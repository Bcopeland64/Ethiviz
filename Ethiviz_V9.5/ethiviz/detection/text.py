from __future__ import annotations
from ethiviz.detection.base import DetectionBackend
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

class TextDetectionBackend(DetectionBackend):
    """Backend for text-based bias detection."""
    def __init__(self) -> None:
        self.detector = SemanticBiasDetector()

    def detect(self, input_data: str, lens_id: str, language: str = "en", **kwargs: Any) -> Dict[str, float]:
        return self.detector.detect(input_data, lens_id, language=language)
