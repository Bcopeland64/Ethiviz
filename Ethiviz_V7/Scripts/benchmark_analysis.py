#!/usr/bin/env python3
"""Measure cold and warmed EthiViz text-analysis latency for a local dataset."""
from __future__ import annotations

import argparse
import json
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Text, CSV, JSON, or XLSX input file")
    parser.add_argument("--limit", type=int, default=100, help="Maximum records to analyze (default: 100)")
    parser.add_argument(
        "--traditions",
        nargs="+",
        choices=("western_v1", "ubuntu_v1", "confucian_v2", "islamic_v1",
                 "buddhist_v1", "hindu_v1", "indigenous_v1"),
        help="Framework ids to include (default: all seven)",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be greater than zero")

    dataset = load_text_dataset(args.input)
    if not dataset:
        parser.error("The input file did not contain any analyzable text")
    texts = dataset[:args.limit]
    analyzer = Analyzer(frameworks=args.traditions, use_semantic=True)

    cold_wall_seconds, cold_metrics = _run(analyzer, texts)
    for lens in analyzer.lenses.values():
        if lens.use_semantic:
            lens.detector.detect("benchmark warm-up", lens.lens_id, language="en")
    warm_wall_seconds, warm_metrics = _run(analyzer, texts)

    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "input": str(Path(args.input).resolve()),
        "text_count": len(texts),
        "character_count": sum(len(text) for text in texts),
        "frameworks": args.traditions or analyzer.framework_ids,
        "cold": {
            "wall_seconds": round(cold_wall_seconds, 4),
            "engine_phases": cold_metrics,
        },
        "warm": {
            "wall_seconds": round(warm_wall_seconds, 4),
            "engine_phases": warm_metrics,
        },
        "note": "Timing output is not an accuracy or fairness metric.",
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
