from __future__ import annotations
from typing import List, Dict
import numpy as np

class BiasQuantifier:
    """Quantifies bias levels based on lens scores."""
    def quantify(self, scores: List[float]) -> str:
        avg = np.mean(scores) if scores else 0.0
        if avg > 0.8: return "Critical"
        if avg > 0.6: return "High"
        if avg > 0.4: return "Medium"
        if avg > 0.2: return "Low"
        return "Negligible"
