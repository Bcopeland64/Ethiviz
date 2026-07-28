from __future__ import annotations
from ethiviz.detection.base import DetectionBackend
from ethiviz.detection.text import TextDetectionBackend
from ethiviz.detection.image import ImageDetectionBackend

class MultimodalDetectionBackend(DetectionBackend):
    """Backend for multimodal (text + image) bias detection."""
    def __init__(self) -> None:
        self.text_backend = TextDetectionBackend()
        self.image_backend = ImageDetectionBackend()

    def detect(self, input_data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        text_res = {}
        if "text" in input_data:
            text_res = self.text_backend.detect(input_data["text"], **kwargs)
        
        image_res = {}
        if "image" in input_data:
            image_res = self.image_backend.detect(input_data["image"], **kwargs)
            
        return {
            "text_analysis": text_res,
            "image_analysis": image_res
        }
