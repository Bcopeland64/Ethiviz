# ethiviz/vision/face_detector.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import urllib.request
import numpy as np

@dataclass
class DetectedFace:
    bounding_box: tuple[int, int, int, int]    # (x, y, w, h)
    confidence: float
    face_image: np.ndarray                     # cropped face region (H, W, 3)

# mediapipe>=0.10.30 dropped the legacy `mp.solutions` API from its Python 3.13
# wheels in favor of the Tasks API, which requires a local .tflite model file
# rather than bundling weights in the package itself.
_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
_MODEL_PATH = Path.home() / ".ethiviz" / "models" / "blaze_face_short_range.tflite"


def _ensure_model() -> str:
    """Downloads the face detector model on first use, caching it locally."""
    if not _MODEL_PATH.exists():
        _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    return str(_MODEL_PATH)


class MediaPipeFaceDetector:
    """
    CPU-capable face detection using Google MediaPipe's Tasks API.
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
            from mediapipe.tasks.python import vision as mp_vision
            from mediapipe.tasks.python.core.base_options import BaseOptions

            self._mp = mp
            options = mp_vision.FaceDetectorOptions(
                base_options=BaseOptions(model_asset_path=_ensure_model()),
                running_mode=mp_vision.RunningMode.IMAGE,
                min_detection_confidence=min_detection_confidence,
            )
            self._detector = mp_vision.FaceDetector.create_from_options(options)
        except (ImportError, OSError, RuntimeError) as exc:
            # Mock for testing, or if the model couldn't be downloaded
            self._detector = None
            print(f"Warning: mediapipe face detector unavailable ({exc}). Using mock face detector.")

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        """
        Detect faces in an RGB image array (H, W, 3).
        Returns list of DetectedFace with bounding box and cropped region.
        """
        if self._detector is None:
            # Mock return
            return []

        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=image)
        result = self._detector.detect(mp_image)
        faces = []
        if not result.detections:
            return faces
        h, w = image.shape[:2]
        for det in result.detections:
            bb = det.bounding_box
            x = max(0, bb.origin_x)
            y = max(0, bb.origin_y)
            fw = min(bb.width, w - x)
            fh = min(bb.height, h - y)
            faces.append(DetectedFace(
                bounding_box=(x, y, fw, fh),
                confidence=det.categories[0].score if det.categories else 0.0,
                face_image=image[y:y+fh, x:x+fw],
            ))
        return faces
