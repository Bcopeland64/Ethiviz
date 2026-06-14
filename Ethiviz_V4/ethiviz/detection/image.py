from __future__ import annotations
import numpy as np
from ethiviz.detection.base import DetectionBackend
from ethiviz.vision.face_detector import MediaPipeFaceDetector
from ethiviz.vision.skin_tone import ITASkinToneEstimator
from ethiviz.vision.cultural_element_detector import CLIPCulturalDetector

class ImageDetectionBackend(DetectionBackend):
    """Backend for image-based bias detection."""
    def __init__(self) -> None:
        self.face_detector = MediaPipeFaceDetector()
        self.skin_tone_estimator = ITASkinToneEstimator()
        self.cultural_detector = CLIPCulturalDetector()

    def detect(self, input_data: np.ndarray, **kwargs: Any) -> Dict[str, Any]:
        faces = self.face_detector.detect(input_data)
        skin_tones = [self.skin_tone_estimator.estimate(f.face_image) for f in faces]
        cultural_elements = self.cultural_detector.detect(input_data)
        
        return {
            "n_faces": len(faces),
            "skin_tones": [st.fitzpatrick_type for st in skin_tones],
            "cultural_elements": cultural_elements.found_elements
        }
