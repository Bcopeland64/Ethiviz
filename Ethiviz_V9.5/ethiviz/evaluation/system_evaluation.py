from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)

from ethiviz.evaluation.calibration_validation import evaluate_calibration


def evaluate_predictions(
    labels: list[int] | np.ndarray,
    scores: list[float] | np.ndarray,
    lens_id: str,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Compare one lens's scores with binary, human-reviewed reference labels."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1.")

    raw_labels = np.asarray(labels, dtype=float)
    y_score = np.asarray(scores, dtype=float)
    if raw_labels.size == 0:
        raise ValueError(f"No non-missing reference labels for {lens_id}.")
    if raw_labels.shape != y_score.shape:
        raise ValueError("labels and scores must have the same length.")
    if not np.isfinite(raw_labels).all() or not np.isin(raw_labels, [0, 1]).all():
        raise ValueError("Reference labels must be binary values 0 or 1.")
    y_true = raw_labels.astype(int)
    if not np.isfinite(y_score).all() or ((y_score < 0) | (y_score > 1)).any():
        raise ValueError("Prediction scores must be finite values between 0 and 1.")

    y_pred = (y_score >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    calibration = evaluate_calibration(y_score, y_true, lens_id=lens_id)
    return {
        "status": "evaluated",
        "sample_count": int(y_true.size),
        "threshold": threshold,
        "metrics": {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "roc_auc": (
                float(roc_auc_score(y_true, y_score))
                if np.unique(y_true).size == 2
                else None
            ),
            "brier_score": calibration.brier_score,
            "mean_abs_calibration_error": calibration.mean_abs_error,
            "calibration_status": calibration.calibration_status,
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        },
        "interpretation": (
            "Exploratory comparison to the supplied labels; not evidence of "
            "cultural validity or suitability for consequential decisions."
        ),
    }


def load_evaluation_data(path: str | Path) -> pd.DataFrame:
    """Load a CSV requiring one non-empty text field per row."""
    frame = pd.read_csv(path)
    if "text" not in frame.columns:
        raise ValueError("Evaluation CSV must contain a 'text' column.")
    if frame.empty:
        raise ValueError("Evaluation CSV must contain at least one row.")
    if frame["text"].isna().any() or frame["text"].astype(str).str.strip().eq("").any():
        raise ValueError("Evaluation CSV contains an empty or missing text value.")
    return frame


def score_texts(analyzer: Any, texts: list[str]) -> pd.DataFrame:
    """Run the EthiViz analyzer and return privacy-minimized numeric features."""
    result = analyzer.analyze(texts, dataset_source="evaluation")
    features: dict[str, Any] = {"text_length": [len(text) for text in texts]}
    for framework_score in result.framework_scores:
        values = framework_score.raw_evidence.get("per_text_scores")
        if values is None or len(values) != len(texts):
            raise ValueError(
                f"Analyzer did not return one score per text for "
                f"{framework_score.framework_id}."
            )
        features[f"score_{framework_score.framework_id}"] = values
    if len(features) == 1:
        raise ValueError("Analyzer returned no framework scores.")
    return pd.DataFrame(features)


def evaluate_labeled_frame(
    frame: pd.DataFrame,
    score_frame: pd.DataFrame,
    threshold: float = 0.5,
) -> dict[str, dict[str, Any]]:
    """Evaluate every lens with a matching ``label_<framework_id>`` column."""
    evaluations: dict[str, dict[str, Any]] = {}
    for score_column in score_frame.columns:
        if not score_column.startswith("score_"):
            continue
        lens_id = score_column.removeprefix("score_")
        label_column = f"label_{lens_id}"
        if label_column not in frame.columns:
            continue

        raw_labels = frame[label_column]
        numeric_labels = pd.to_numeric(raw_labels, errors="coerce")
        invalid_values = numeric_labels.isna() & raw_labels.notna()
        if invalid_values.any():
            raise ValueError(f"{label_column} must contain only 0, 1, or blank values.")
        observed = numeric_labels.notna()
        if not observed.any():
            continue
        labels = numeric_labels.loc[observed].to_numpy(dtype=float)
        scores = score_frame.loc[observed, score_column].to_numpy(dtype=float)
        evaluations[lens_id] = evaluate_predictions(labels, scores, lens_id, threshold)
        evaluations[lens_id]["label_column"] = label_column

    if not evaluations:
        raise ValueError(
            "Provide at least one binary label column named "
            "'label_<framework_id>' for the selected frameworks."
        )
    return evaluations


def write_drift_report(
    reference_features: pd.DataFrame,
    current_features: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Write an Evidently data-drift report for numeric analysis features."""
    try:
        from evidently import DataDefinition, Dataset, Report
        from evidently.presets import DataDriftPreset
    except ImportError as exc:
        raise RuntimeError(
            "Evidently is required for drift reports. Install with "
            "`pip install -e '.[evaluation]'`."
        ) from exc

    columns = sorted(set(reference_features.columns) & set(current_features.columns))
    if not columns:
        raise ValueError("Reference and current datasets have no comparable features.")
    data_definition = DataDefinition(numerical_columns=columns)
    reference = Dataset.from_pandas(
        reference_features[columns], data_definition=data_definition
    )
    current = Dataset.from_pandas(current_features[columns], data_definition=data_definition)
    evaluation = Report([DataDriftPreset()]).run(current, reference)
    evaluation.save_html(str(output_path))
