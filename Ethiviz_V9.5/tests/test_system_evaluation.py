from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ethiviz.evaluation.system_evaluation import (
    evaluate_labeled_frame,
    evaluate_predictions,
    score_texts,
)


def test_evaluate_predictions_reports_binary_and_calibration_metrics():
    result = evaluate_predictions(
        labels=[0, 0, 1, 1],
        scores=[0.1, 0.6, 0.8, 0.9],
        lens_id="western_v1",
    )

    assert result["sample_count"] == 4
    assert result["metrics"]["accuracy"] == 0.75
    assert result["metrics"]["precision"] == pytest.approx(2 / 3)
    assert result["metrics"]["recall"] == 1.0
    assert result["metrics"]["roc_auc"] == 1.0
    assert result["metrics"]["confusion_matrix"] == [[1, 1], [0, 2]]
    assert "not evidence" in result["interpretation"]


def test_evaluate_predictions_omits_auc_when_labels_have_one_class():
    result = evaluate_predictions(
        labels=[0, 0],
        scores=[0.1, 0.2],
        lens_id="western_v1",
    )

    assert result["metrics"]["roc_auc"] is None


@pytest.mark.parametrize(
    ("labels", "scores", "threshold"),
    [
        ([0, 2], [0.1, 0.9], 0.5),
        ([0, 0.5], [0.1, 0.9], 0.5),
        ([0, 1], [0.1, np.nan], 0.5),
        ([0, 1], [0.1, 0.9], 1.1),
        ([0], [0.1, 0.2], 0.5),
    ],
)
def test_evaluate_predictions_rejects_invalid_inputs(labels, scores, threshold):
    with pytest.raises(ValueError):
        evaluate_predictions(labels, scores, "western_v1", threshold)


def test_evaluate_labeled_frame_ignores_blank_labels_and_skips_unlabeled_lenses():
    frame = pd.DataFrame(
        {
            "label_western_v1": [0, 1, None],
            "label_ubuntu_v1": [None, None, None],
        }
    )
    scores = pd.DataFrame(
        {
            "score_western_v1": [0.1, 0.9, 0.7],
            "score_ubuntu_v1": [0.2, 0.3, 0.4],
        }
    )

    results = evaluate_labeled_frame(frame, scores)

    assert list(results) == ["western_v1"]
    assert results["western_v1"]["sample_count"] == 2
    assert results["western_v1"]["label_column"] == "label_western_v1"


def test_evaluate_labeled_frame_rejects_non_binary_annotations():
    frame = pd.DataFrame({"label_western_v1": [0, 3]})
    scores = pd.DataFrame({"score_western_v1": [0.1, 0.9]})

    with pytest.raises(ValueError, match="binary"):
        evaluate_labeled_frame(frame, scores)


def test_score_texts_exports_only_numeric_scores_and_lengths():
    class FakeResult:
        framework_scores = [
            type(
                "FrameworkScore",
                (),
                {
                    "framework_id": "western_v1",
                    "raw_evidence": {"per_text_scores": [0.2, 0.8]},
                },
            )()
        ]

    class FakeAnalyzer:
        def analyze(self, texts, dataset_source):
            assert dataset_source == "evaluation"
            return FakeResult()

    scores = score_texts(FakeAnalyzer(), ["a", "longer text"])

    assert scores.to_dict(orient="list") == {
        "text_length": [1, 11],
        "score_western_v1": [0.2, 0.8],
    }
