# ethiviz/vision/face_detector.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class DetectedFace:
    bounding_box: tuple[int, int, int, int]    # (x, y, w, h)
    confidence: float
    face_image: np.ndarray                     # cropped face region (H, W, 3)

class MediaPipeFaceDetector:
    """
    CPU-capable face detection using Google MediaPipe.
    No GPU, no API key required.

    Requires: pip install ethiviz[vision]

    Example:
        >>> import numpy as np
        >>> detector = MediaPipeFaceDetector()
        >>> image = np.zeros((224, 224, 3), dtype=np.uint8)
        >>> faces = detector.detect(image)
        >>> isinstance(faces, list)
        True
    """
    def __init__(self, min_detection_confidence: float = 0.5) -> None:
        try:
            import mediapipe as mp
            self._mp = mp
            self._detector = mp.solutions.face_detection.FaceDetection(
                min_detection_confidence=min_detection_confidence
            )
        except ImportError:
            # Mock for testing
            self._detector = None
            print("Warning: mediapipe not installed. Using mock face detector.")

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        """
        Detect faces in an RGB image array (H, W, 3).
        Returns list of DetectedFace with bounding box and cropped region.
        """
        if self._detector is None:
            # Mock return
            return []
            
        results = self._detector.process(image)
        faces = []
        if not results.detections:
            return faces
        h, w = image.shape[:2]
        for det in results.detections:
            bb = det.location_data.relative_bounding_box
            x = max(0, int(bb.xmin * w))
            y = max(0, int(bb.ymin * h))
            fw = min(int(bb.width * w), w - x)
            fh = min(int(bb.height * h), h - y)
            faces.append(DetectedFace(
                bounding_box=(x, y, fw, fh),
                confidence=det.score[0] if det.score else 0.0,
                face_image=image[y:y+fh, x:x+fw],
            ))
        return faces
