"""Structured logging, request/job metrics, and GET /metrics (Upgrade 50).

Dependency-free by design — no prometheus_client or structlog, matching this
codebase's existing preference (Upgrades 41/45/47) for a guarded dict/Counter
over adding infrastructure dependencies where the metric surface is small.
The /metrics output is plain Prometheus text exposition format even though
nothing here links against the prometheus_client library.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import Counter, defaultdict
from typing import Callable

from flask import Flask, Response, g, has_request_context, request

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_http_requests: Counter = Counter()                 # (method, route, status) -> count
_http_duration_sum: dict = defaultdict(float)        # (method, route, status) -> seconds
_job_count: Counter = Counter()                       # (analysis_type, status) -> count
_job_duration_sum: dict = defaultdict(float)          # (analysis_type, status) -> seconds
_lens_jobs: Counter = Counter()                        # lens_id -> times scored
_lens_warnings: Counter = Counter()                     # lens_id -> times a warning was attached

_queue_depth_provider: list[Callable[[], int]] = []


class _RequestIdFilter(logging.Filter):
    """Attaches the current request's correlation ID to every log record
    emitted during that request, so existing app.logger.info/.warning/...
    call sites throughout api_server.py get request_id in their structured
    output without editing each call site individually."""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
        elif not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        job_id = getattr(record, "job_id", None)
        if job_id is not None:
            payload["job_id"] = job_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_json_logging(level: int = logging.INFO) -> None:
    """Installs the JSON formatter + request-id filter on the root logger.
    Called once at import time by api_server.py (before the Flask app or
    JobStore are constructed, so their own startup log lines are structured
    too) — every existing logger.info/warning/error call in this codebase
    becomes structured JSON with no per-call-site changes required."""
    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_RequestIdFilter())
    root.handlers = [handler]
    root.setLevel(level)


def register_queue_depth_provider(fn: Callable[[], int]) -> None:
    """Lets api_server.py register a zero-arg callable returning the current
    AnalysisQueue depth for GET /metrics, without this module importing
    Scripts.analysis_queue (which would make redis/rq a hard dependency of
    observability.py even for deployments that never enable the queue)."""
    _queue_depth_provider[:] = [fn]


def record_job(analysis_type: str, status: str, duration_seconds: float,
                tradition_scores: list[dict] | None = None) -> None:
    """Call once per finished analysis job (from run_analysis_job's finally
    block) to update the per-analysis-type duration/count metrics and the
    per-lens warning rate — the latter counts how often a lens attached a
    `warnings` entry (see ethiviz_bridge.compute_tradition_scores) out of
    how many jobs scored that lens, exposed as ethiviz_lens_warning_rate."""
    with _lock:
        _job_count[(analysis_type, status)] += 1
        _job_duration_sum[(analysis_type, status)] += duration_seconds
        for entry in (tradition_scores or []):
            lens_id = entry.get("tradition")
            if not lens_id:
                continue
            _lens_jobs[lens_id] += 1
            if entry.get("warnings"):
                _lens_warnings[lens_id] += 1


def install(app: Flask) -> None:
    """Wires a correlation ID + latency timer onto every request and adds
    GET /metrics. Call once, after the Flask app is constructed."""

    @app.before_request
    def _start_request() -> None:
        g.observability_started = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

    @app.after_request
    def _finish_request(response):
        route = request.url_rule.rule if request.url_rule else request.path
        started = getattr(g, "observability_started", None)
        elapsed = time.perf_counter() - started if started is not None else 0.0
        key = (request.method, route, str(response.status_code))
        with _lock:
            _http_requests[key] += 1
            _http_duration_sum[key] += elapsed
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response

    @app.get("/metrics")
    def metrics():
        with _lock:
            http_rows = list(_http_requests.items())
            http_durations = dict(_http_duration_sum)
            job_rows = list(_job_count.items())
            job_durations = dict(_job_duration_sum)
            lens_warning_rows = list(_lens_warnings.items())
            lens_job_totals = dict(_lens_jobs)

        lines = [
            "# HELP ethiviz_http_requests_total Total HTTP requests handled.",
            "# TYPE ethiviz_http_requests_total counter",
        ]
        for (method, route, status), count in http_rows:
            labels = f'method="{method}",route="{route}",status="{status}"'
            lines.append(f"ethiviz_http_requests_total{{{labels}}} {count}")
            lines.append(
                f"ethiviz_http_request_duration_seconds_sum{{{labels}}} "
                f"{http_durations[(method, route, status)]}"
            )

        lines += [
            "# HELP ethiviz_job_total Analysis jobs finished, by type and outcome.",
            "# TYPE ethiviz_job_total counter",
            "# HELP ethiviz_job_duration_seconds_sum Cumulative analysis job duration, by type and outcome.",
            "# TYPE ethiviz_job_duration_seconds_sum counter",
        ]
        for (analysis_type, status), count in job_rows:
            labels = f'analysis_type="{analysis_type}",status="{status}"'
            lines.append(f"ethiviz_job_total{{{labels}}} {count}")
            lines.append(
                f"ethiviz_job_duration_seconds_sum{{{labels}}} "
                f"{job_durations[(analysis_type, status)]}"
            )

        lines += [
            "# HELP ethiviz_lens_warning_rate Fraction of scored jobs where a lens attached a warning.",
            "# TYPE ethiviz_lens_warning_rate gauge",
        ]
        for lens_id, warning_count in lens_warning_rows:
            total = lens_job_totals.get(lens_id, 0)
            rate = (warning_count / total) if total else 0.0
            labels = f'lens="{lens_id}"'
            lines.append(f"ethiviz_lens_warnings_total{{{labels}}} {warning_count}")
            lines.append(f"ethiviz_lens_warning_rate{{{labels}}} {rate:.4f}")

        if _queue_depth_provider:
            try:
                depth = _queue_depth_provider[0]()
            except Exception:
                depth = None
            if depth is not None:
                lines += [
                    "# HELP ethiviz_queue_depth Current analysis queue depth.",
                    "# TYPE ethiviz_queue_depth gauge",
                    f"ethiviz_queue_depth {depth}",
                ]

        return Response("\n".join(lines) + "\n", mimetype="text/plain")
