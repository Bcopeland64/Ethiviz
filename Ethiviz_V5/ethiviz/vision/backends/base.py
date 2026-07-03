# ethiviz/vision/backends/base.py
from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict
import numpy as np

@runtime_checkable
class FaceAttributeBackend(Protocol):
    """Protocol for face attribute detection backends."""
    def predict_gender(self, face_image: np.ndarray) -> Dict[str, float]:
        """Returns {"male": p, "female": p} probabilities."""
        ...
    def predict_age_group(self, face_image: np.ndarray) -> Dict[str, float]:
        """Returns {"child": p, "young_adult": p, "adult": p, ...} probabilities."""
        ...
