# ethiviz/analysis/demographics.py
from __future__ import annotations
import numpy as np
from ethiviz.vision.face_detector import MediaPipeFaceDetector
from ethiviz.vision.skin_tone import ITASkinToneEstimator

def compute_skin_tone_distribution(image: np.ndarray) -> dict[str, float]:
    """
    Detect faces, estimate Fitzpatrick type per face, and return 
    the normalized distribution of skin tones (Figure A7).
    """
    faces = MediaPipeFaceDetector().detect(image)
    if not faces:
        return {}
        
    counts: dict[str, int] = {}
    estimator = ITASkinToneEstimator()
    
    for face in faces:
        est = estimator.estimate(face.face_image)
        counts[est.description] = counts.get(est.description, 0) + 1
        
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}

def compute_age_distribution(image: np.ndarray) -> dict[str, float]:
    """Placeholder for Figure A8: Age distribution analysis."""
    return {}

def compute_gender_distribution(image: np.ndarray) -> dict[str, float]:
    """Placeholder for Figure A9: Gender distribution analysis."""
    return {}
