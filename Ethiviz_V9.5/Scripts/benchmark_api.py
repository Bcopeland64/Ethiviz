"""Measure API submission, queue delay when observable, execution, and results retrieval."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return round(ordered[index], 4)


def _multipart_body(path: Path, boundary: str) -> bytes:
    fields = [
        ("analysis_type", "text"),
        ("data_source_type", "upload"),
        ("selected_traditions", "western"),
        ("selected_traditions", "ubuntu"),
        ("selected_traditions", "confucian"),
        ("selected_traditions", "islamic"),
        ("advanced_options", "{}"),
    ]
    marker = f"--{boundary}\r\n".encode("ascii")
    pieces: list[bytes] = []
    for name, value in fields:
        pieces.extend((
            marker,
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8"),
        ))
    safe_name = path.name.replace('"', "_").replace("\r", "_").replace("\n", "_")
    pieces.extend((
        marker,
        (
            f'Content-Disposition: form-data; name="text_file"; filename="{safe_name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8"),
        path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode("ascii"),
    ))
    return b"".join(pieces)


def _json_request(url: str, headers: dict[str, str], body: bytes | None = None):
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def run_benchmark(
    api_url: str,
    input_path: Path,
    iterations: int,
    poll_interval: float,
    timeout_seconds: float,
) -> dict:
    api_url = api_url.rstrip("/") + "/"
    api_key = os.environ.get("ETHIVIZ_API_KEY")
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    runs = []
    for _ in range(iterations):
        boundary = f"ethiviz-{uuid.uuid4().hex}"
        body = _multipart_body(input_path, boundary)
        request_headers = {
            **headers,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "Idempotency-Key": str(uuid.uuid4()),
        }
        started = time.monotonic()
        try:
            submitted = _json_request(
                urljoin(api_url, "api/analyze"), request_headers, body
            )
        except (HTTPError, URLError, TimeoutError) as error:
            runs.append({"outcome": "submission_failed", "error_type": type(error).__name__})
            continue

        job_id = submitted.get("job_id")
        if not job_id:
            runs.append({"outcome": "submission_rejected"})
            continue
        status_url = urljoin(api_url, f"api/analyze/status/{quote(job_id, safe='')}")
        deadline = time.monotonic() + timeout_seconds
        queue_wait = None
        final_status = None
        while time.monotonic() < deadline:
            try:
                status = _json_request(status_url, headers)
            except (HTTPError, URLError, TimeoutError) as error:
                final_status = "status_request_failed"
                runs.append({"outcome": final_status, "error_type": type(error).__name__})
                break
            if status.get("start_time") is not None and status.get("submission_time") is not None:
                queue_wait = max(0.0, status["start_time"] - status["submission_time"])
            final_status = status.get("status")
            if final_status in {"completed", "failed", "cancelled"}:
                break
            time.sleep(poll_interval)
        else:
            final_status = "timed_out"

        run = {
            "outcome": final_status,
            "wall_seconds": round(time.monotonic() - started, 4),
            "queue_wait_seconds": round(queue_wait, 4) if queue_wait is not None else None,
            "execution_seconds": None,
            "results_retrieval_seconds": None,
        }
        if final_status == "completed":
            retrieval_started = time.monotonic()
            try:
                result = _json_request(
                    urljoin(api_url, f"api/analyze/results/{quote(job_id, safe='')}"),
                    headers,
                )
                run["results_retrieval_seconds"] = round(
                    time.monotonic() - retrieval_started, 4
                )
                run["execution_seconds"] = (
                    result.get("results", {}).get("performance", {}).get("total_seconds")
                )
            except (HTTPError, URLError, TimeoutError) as error:
                run["outcome"] = "results_request_failed"
                run["error_type"] = type(error).__name__
        runs.append(run)

    def measured(field: str) -> list[float]:
        return [
            run[field]
            for run in runs
            if isinstance(run.get(field), (int, float))
        ]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None

    return {
        "benchmark": "ethiviz-api-text-v1",
        "revision": revision,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "queue_mode": "redis" if os.environ.get("ETHIVIZ_REDIS_URL") else "local",
            "database_mode": (
                "postgres"
                if os.environ.get("DATABASE_URL", "").startswith(("postgres://", "postgresql"))
                else "sqlite"
            ),
        },
        "workload": {
            "analysis_type": "text",
            "input_bytes": input_path.stat().st_size,
            "iterations": iterations,
            "input_content_included": False,
        },
        "sample_count": len(runs),
        "completed_count": sum(run.get("outcome") == "completed" for run in runs),
        "measurements": {
            "queue_wait_seconds": {
                "p50": _percentile(measured("queue_wait_seconds"), 0.50),
                "p95": _percentile(measured("queue_wait_seconds"), 0.95),
                "sample_count": len(measured("queue_wait_seconds")),
            },
            "execution_seconds": {
                "p50": _percentile(measured("execution_seconds"), 0.50),
                "p95": _percentile(measured("execution_seconds"), 0.95),
                "sample_count": len(measured("execution_seconds")),
            },
            "results_retrieval_seconds": {
                "p50": _percentile(measured("results_retrieval_seconds"), 0.50),
                "p95": _percentile(measured("results_retrieval_seconds"), 0.95),
                "sample_count": len(measured("results_retrieval_seconds")),
            },
            "user_visible_wall_seconds": {
                "p50": _percentile(measured("wall_seconds"), 0.50),
                "p95": _percentile(measured("wall_seconds"), 0.95),
                "sample_count": len(measured("wall_seconds")),
            },
            "peak_memory_mb": None,
            "cpu_utilization": None,
            "gpu_utilization": None,
        },
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:5001/")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error("--input must name an existing file.")
    if args.iterations < 1 or args.poll_interval <= 0 or args.timeout <= 0:
        parser.error("--iterations, --poll-interval, and --timeout must be positive.")
    report = run_benchmark(
        args.api_url, args.input, args.iterations, args.poll_interval, args.timeout
    )
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
