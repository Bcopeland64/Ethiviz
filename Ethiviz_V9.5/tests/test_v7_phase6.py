"""Regression tests for V7 analysis throughput and image detection reporting."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Scripts"))

from ethiviz.api import Analyzer  # noqa: E402
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector  # noqa: E402
import ethiviz_bridge  # noqa: E402


def test_text_embeddings_are_batched_once_and_reused_across_lenses(mock_embedding_model):
    texts = [f"review text number {index}" for index in range(70)]
    analyzer = Analyzer(use_semantic=True, n_bootstrap=10)

    result = analyzer.analyze(texts)

    encoded_text_batches = [
        call.args[0]
        for call in mock_embedding_model.encode.call_args_list
        if isinstance(call.args[0], list)
        and call.args[0]
        and call.args[0][0].startswith("review text number")
    ]
    assert [text for batch in encoded_text_batches for text in batch] == texts
    assert result.metadata["performance"]["text_count"] == len(texts)
    assert result.metadata["performance"]["embedding_seconds"] >= 0
    assert result.metadata["performance"]["texts_per_second"] > 0


def test_semantic_detector_preserves_scores_when_given_precomputed_embedding(mock_embedding_model):
    detector = SemanticBiasDetector(model=mock_embedding_model)
    text = "People from different cultures deserve equal respect."
    expected = detector.detect(text, "western_v1")
    encoded_input = mock_embedding_model.encode(text)
    actual = detector.detect(
        text, "western_v1", input_embedding=encoded_input
    )
    assert actual == expected


def test_cultural_element_count_counts_detected_items_not_categories():
    detections = {
        "religious_symbols": ["cross", "bindi"],
        "cultural_clothing": [],
        "cultural_landmarks": ["pagoda"],
    }
    assert ethiviz_bridge._count_cultural_elements(detections) == 3


def test_cultural_element_count_handles_legacy_list_shape():
    assert ethiviz_bridge._count_cultural_elements(["cross", "pagoda"]) == 2


def test_bridge_exposes_engine_performance_without_changing_return_shape():
    performance = {}
    items, scores, findings = ethiviz_bridge.run_text_analysis(
        "People deserve equal respect.",
        ["western_v1"],
        performance_output=performance,
    )

    assert len((items, scores, findings)) == 3
    assert performance["text_count"] == 1
    assert performance["embedding_seconds"] >= 0
    assert performance["scoring_seconds"] >= 0


def test_image_proxy_includes_only_detected_cultural_labels():
    proxy = ethiviz_bridge._describe_detection({
        "n_faces": 0,
        "skin_tones": [],
        "cultural_elements": {
            "religious_symbols": ["cross"],
            "cultural_clothing": [],
        },
    })
    assert "religious_symbols: cross" in proxy
    assert "cultural_clothing" not in proxy
