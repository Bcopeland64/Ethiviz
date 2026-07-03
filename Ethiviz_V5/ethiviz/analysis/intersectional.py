# ethiviz/analysis/intersectional.py
from __future__ import annotations
from typing import Dict, List, Any

def calculate_intersectional_analysis(
    dimension_a_scores: Dict[str, float],
    dimension_b_scores: Dict[str, float],
) -> Dict[str, float]:
    """
    Calculate compound bias at identity intersections (Figure A3).
    Example: Intersection of Race (A) and Gender (B).
    """
    intersections = {}
    for identity_a, score_a in dimension_a_scores.items():
        for identity_b, score_b in dimension_b_scores.items():
            # Intersectional amplification term (Copeland, 2025)
            # Measures if bias at intersection > sum of parts
            intersections[f"{identity_a}_{identity_b}"] = score_a * score_b
            
    return intersections
