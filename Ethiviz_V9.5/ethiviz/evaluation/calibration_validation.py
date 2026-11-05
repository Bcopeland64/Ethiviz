from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CalibrationBucket:
    lower: float
    upper: float
    count: int
    mean_prediction: float
    observed_rate: float
    mean_abs_error: float


@dataclass
class CalibrationValidationResult:
    lens_id: str
    brier_score: float
    mean_abs_error: float
    sample_count: int
    calibration_status: str
    buckets: list[CalibrationBucket] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lens_id": self.lens_id,
            "brier_score": round(self.brier_score, 6),
            "mean_abs_error": round(self.mean_abs_error, 6),
            "sample_count": self.sample_count,
            "calibration_status": self.calibration_status,
            "buckets": [
                {
                    "lower": bucket.lower,
                    "upper": bucket.upper,
                    "count": bucket.count,
                    "mean_prediction": round(bucket.mean_prediction, 6),
                    "observed_rate": round(bucket.observed_rate, 6),
                    "mean_abs_error": round(bucket.mean_abs_error, 6),
                }
                for bucket in self.buckets
            ],
        }


def evaluate_calibration(
    raw_scores: list[float] | np.ndarray,
    labels: list[int] | np.ndarray,
    lens_id: str = "unknown",
    bins: int = 5,
) -> CalibrationValidationResult:
    """Evaluate calibration quality using a Brier score and a reliability table.

    A calibration result is considered reliable when the average bucket gap between
    mean predicted risk and observed outcome rate stays small. This keeps the
    system honest about whether a reported confidence value matches reality.
    """
    scores = np.asarray(raw_scores, dtype=float)
    outcomes = np.asarray(labels, dtype=float)

    if scores.size == 0 or outcomes.size == 0:
        raise ValueError("raw_scores and labels must not be empty.")
    if scores.shape[0] != outcomes.shape[0]:
        raise ValueError("raw_scores and labels must have the same length.")

    clipped = np.clip(scores, 0.0, 1.0)
    brier_score = float(np.mean((clipped - outcomes) ** 2))

    bucket_edges = np.linspace(0.0, 1.0, bins + 1)
    buckets: list[CalibrationBucket] = []
    running_gap = 0.0
    for i in range(bins):
        lo = bucket_edges[i]
        hi = bucket_edges[i + 1]
        in_bucket = (clipped >= lo) & (clipped < hi)
        if i == bins - 1:
            in_bucket = (clipped >= lo) & (clipped <= hi)

        if not np.any(in_bucket):
            buckets.append(
                CalibrationBucket(
                    lower=lo,
                    upper=hi,
                    count=0,
                    mean_prediction=0.0,
                    observed_rate=0.0,
                    mean_abs_error=0.0,
                )
            )
            continue

        bucket_scores = clipped[in_bucket]
        bucket_labels = outcomes[in_bucket]
        mean_prediction = float(np.mean(bucket_scores))
        observed_rate = float(np.mean(bucket_labels))
        abs_gap = abs(mean_prediction - observed_rate)
        running_gap += abs_gap * bucket_scores.size

        buckets.append(
            CalibrationBucket(
                lower=lo,
                upper=hi,
                count=int(bucket_scores.size),
                mean_prediction=mean_prediction,
                observed_rate=observed_rate,
                mean_abs_error=abs_gap,
            )
        )

    mean_abs_error = float(running_gap / max(1, clipped.size))
    if mean_abs_error < 0.05:
        status = "reliable"
    elif mean_abs_error < 0.15:
        status = "acceptable"
    else:
        status = "poor"

    return CalibrationValidationResult(
        lens_id=lens_id,
        brier_score=brier_score,
        mean_abs_error=mean_abs_error,
        sample_count=int(clipped.size),
        calibration_status=status,
        buckets=buckets,
    )
