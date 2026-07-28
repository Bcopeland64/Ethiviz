from __future__ import annotations
from typing import List, Dict
import numpy as np

def weighted_mean(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """Computes weighted mean of scores."""
    total_weight = sum(weights.values())
    if total_weight == 0:
        return float(np.mean(list(scores.values()))) if scores else 0.0
    
    weighted_sum = sum(scores.get(k, 0.0) * w for k, w in weights.items())
    return weighted_sum / total_weight

def max_score(scores: Dict[str, float]) -> float:
    """Returns the maximum score across all lenses."""
    return max(scores.values()) if scores else 0.0

def median_score(scores: Dict[str, float]) -> float:
    """Returns the median score across all lenses."""
    return float(np.median(list(scores.values()))) if scores else 0.0
