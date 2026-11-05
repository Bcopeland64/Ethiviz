from __future__ import annotations
import numpy as np
from typing import Any

def validate_score(score: Any, name: str = "score") -> float:
    """Ensure score is a float between 0.0 and 1.0."""
    try:
        val = float(score)
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")
        return val
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} must be a valid float, got {score}") from e

def validate_image(image: Any) -> np.ndarray:
    """Ensure image is a valid RGB numpy array."""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Image must be a numpy array, got {type(image)}")
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(f"Image must have shape (H, W, 3), got {image.shape}")
    return image
