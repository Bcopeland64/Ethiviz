#!/usr/bin/env python3
"""Measure cold and warmed EthiViz text-analysis latency for a local dataset."""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ethiviz import Analyzer  # noqa: E402
from Scripts.ethiviz_bridge import load_text_dataset  # noqa: E402


def _run(analyzer: Analyzer, texts: list[str]) -> tuple[float, dict]:
    started = time.perf_counter()
    result = analyzer.analyze(texts, dataset_source="benchmark")
    return time.perf_counter() - started, result.metadata["performance"]


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile)
    return round(ordered[index], 4)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Text, CSV, JSON, or XLSX input file")
    parser.add_argument("--limit", type=int, default=100, help="Maximum records to analyze (default: 100)")
    parser.add_argument("--iterations", type=int, default=5, help="Number of warm measurements (default: 5)")
    parser.add_argument("--output", help="Optional path for machine-readable JSON output")
    parser.add_argument(
        "--traditions",
        nargs="+",
        choices=("western_v1", "ubuntu_v1", "confucian_v2", "islamic_v1",
                 "buddhist_v1", "hindu_v1", "indigenous_v1"),
        help="Framework ids to include (default: all seven)",
    )
    args = parser.parse_args()
    if args.limit < 1 or args.iterations < 1:
        parser.error("--limit and --iterations must be greater than zero")

    dataset = load_text_dataset(args.input)
    if not dataset:
        parser.error("The input file did not contain any analyzable text")
    texts = dataset[:args.limit]
    analyzer = Analyzer(frameworks=args.traditions, use_semantic=True)

    cold_wall_seconds, cold_metrics = _run(analyzer, texts)
    for lens in analyzer.lenses.values():
        if lens.use_semantic:
            lens.detector.detect("benchmark warm-up", lens.lens_id, language="en")
    warm_runs = [_run(analyzer, texts) for _ in range(args.iterations)]
    warm_wall_times = [duration for duration, _ in warm_runs]
    warm_metrics = warm_runs[-1][1]

    try:
        import resource
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_rss_bytes = peak_rss if platform.system() == "Darwin" else peak_rss * 1024
    except ImportError:
        peak_rss_bytes = None

    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or None,
        "cpu_count": os.cpu_count(),
        "peak_rss_bytes": peak_rss_bytes,
        "input": str(Path(args.input).resolve()),
        "text_count": len(texts),
        "character_count": sum(len(text) for text in texts),
        "frameworks": args.traditions or analyzer.framework_ids,
        "iterations": args.iterations,
        "cold": {
            "wall_seconds": round(cold_wall_seconds, 4),
            "engine_phases": cold_metrics,
        },
        "warm": {
            "wall_seconds": {
                "p50": _percentile(warm_wall_times, 0.50),
                "p95": _percentile(warm_wall_times, 0.95),
                "samples": [round(value, 4) for value in warm_wall_times],
            },
            "engine_phases": warm_metrics,
        },
        "queue_wait_seconds": None,
        "queue_wait_note": "Not measured: this benchmark calls Analyzer directly and bypasses the API queue.",
        "note": "Timing output is not an accuracy or fairness metric.",
    }
    serialized = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
