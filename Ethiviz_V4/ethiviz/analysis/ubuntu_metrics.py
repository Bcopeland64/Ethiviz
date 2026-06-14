from __future__ import annotations
import numpy as np
from typing import List, Dict

def shannon_diversity(counts: List[int]) -> float:
    """Computes Shannon-Wiener Diversity Index."""
    if not counts or sum(counts) == 0:
        return 0.0
    arr = np.array(counts, dtype=float)
    p = arr / arr.sum()
    return -float(np.sum(p * np.log(p + 1e-8)))

def intersectional_diversity(demographics: List[Dict[str, str]]) -> float:
    """Measures diversity across identity intersections."""
    if not demographics:
        return 0.0
    # Create unique keys for each intersection
    intersections = ["|".join(sorted(d.values())) for d in demographics]
    unique_intersections, counts = np.unique(intersections, return_counts=True)
    return shannon_diversity(counts.tolist())

def representational_specificity(scores: List[float]) -> float:
    """Measures how specific/targeted the bias detections are."""
    if not scores:
        return 0.0
    # High specificity = low variance in high scores
    return 1.0 - float(np.std(scores))

def ubuntu_composite_score(
    diversity: float,
    specificity: float,
    harmony_impact: float
) -> float:
    """
    Computes a composite Ubuntu metric balancing diversity,
    specificity, and communal harmony.
    """
    return (0.4 * diversity) + (0.3 * specificity) + (0.3 * harmony_impact)
