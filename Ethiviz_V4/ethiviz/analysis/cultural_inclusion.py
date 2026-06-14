# ethiviz/analysis/cultural_inclusion.py
from __future__ import annotations
from typing import List, Dict

def cultural_inclusion_index(
    detected_elements: List[str],
    reference_distribution: Dict[str, float],
) -> float:
    """
    Calculate the Cultural Inclusion Index (Figure A4).
    Measures how well the detected cultural elements match a target distribution.
    """
    if not detected_elements:
        return 0.0
        
    # Simplified implementation
    found_types = set(detected_elements)
    reference_types = set(reference_distribution.keys())
    
    overlap = found_types.intersection(reference_types)
    return len(overlap) / len(reference_types) if reference_types else 0.0
