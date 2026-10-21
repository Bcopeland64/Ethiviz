# ethiviz/analysis/dignity.py
from __future__ import annotations
from typing import Dict

def calculate_dignity_preservation(
    human_centric_score: float,
    community_harm_score: float,
) -> float:
    """
    Calculate the Dignity Preservation Score (Figure A6).
    Balances human-centric (Islamic Karamah) and community-centric (Ubuntu) harms.
    """
    # Weighted balance of individual and collective dignity
    return (human_centric_score * 0.6) + (community_harm_score * 0.4)
