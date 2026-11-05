#!/usr/bin/env python3
"""Evaluate EthiViz scores against reviewed labels and optionally detect drift."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ethiviz import Analyzer  # noqa: E402
from ethiviz.evaluation.system_evaluation import (  # noqa: E402
    evaluate_labeled_frame,
    load_evaluation_data,
    score_texts,
    write_drift_report,
)

FRAMEWORK_IDS = (
    "western_v1",
    "ubuntu_v1",
    "confucian_v2",
    "islamic_v1",
    "buddhist_v1",
    "hindu_v1",
    "indigenous_v1",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Current evaluation CSV")
    parser.add_argument(
        "--reference",
        help="Optional reference CSV for Evidently distribution-drift analysis",
    )
    parser.add_argument(
        "--frameworks",
        nargs="+",
        choices=FRAMEWORK_IDS,
        default=list(FRAMEWORK_IDS),
        help="Lens IDs to evaluate (default: all seven)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Score cutoff for binary metrics (default: 0.5)",
    )
    parser.add_argument(
        "--output",
        default="system-evaluation.json",
        help="Path for the aggregate JSON report",
    )
    parser.add_argument(
        "--html-output",
        help="Path for the Evidently HTML drift report (requires --reference)",
    )
    parser.add_argument(
        "--lexical-only",
        action="store_true",
        help="Disable semantic embeddings for a lightweight, offline run",
    )
    args = parser.parse_args()
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0 and 1")
    if args.html_output and not args.reference:
        parser.error("--html-output requires --reference")

    current = load_evaluation_data(args.input)
    analyzer = Analyzer(frameworks=args.frameworks, use_semantic=not args.lexical_only)
    current_features = score_texts(analyzer, current["text"].astype(str).tolist())
    labeled = any(
        f"label_{framework_id}" in current.columns for framework_id in args.frameworks
    )
    evaluations = (
        evaluate_labeled_frame(current, current_features, args.threshold) if labeled else {}
    )

    drift_report_path: str | None = None
    reference_count: int | None = None
    if args.reference:
        reference = load_evaluation_data(args.reference)
        reference_features = score_texts(analyzer, reference["text"].astype(str).tolist())
        report_path = Path(args.html_output) if args.html_output else Path(args.output).with_suffix(".html")
        write_drift_report(reference_features, current_features, report_path)
        drift_report_path = str(report_path)
        reference_count = len(reference)

    if not evaluations and not args.reference:
        parser.error(
            "The current CSV needs at least one label_<framework_id> column, "
            "or provide --reference for drift-only analysis."
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": "EthiViz Analyzer",
        "sample_count": len(current),
        "reference_sample_count": reference_count,
        "frameworks": args.frameworks,
        "semantic_embeddings": not args.lexical_only,
        "evaluations": evaluations,
        "drift_report_html": drift_report_path,
        "limitations": [
            "Reference labels should be consented, qualified, and independently reviewed.",
            "Metrics depend on the supplied labels, domain, language, threshold, and sample.",
            "Drift indicates a distribution change, not harm, validity, or model failure.",
            "Results do not establish cultural validity, fairness certification, or "
            "fitness for consequential decisions.",
            "This report contains aggregate metrics only; input text is not copied to it.",
        ],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
