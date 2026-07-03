# ethiviz/analysis/dual_framework.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DualEthicsFramework:
    """
    Implements the Dual-Ethics Framework logic (Figure A1).
    Handles synthesis and conflict resolution between Western and Non-Western lenses.
    """
    western_bias_score: float
    non_western_bias_score: float
    
    def resolve_conflict(self) -> str:
        """Resolve conflicts between individualistic and communal ethical perspectives."""
        diff = abs(western_bias_score - non_western_bias_score)
        if diff < 0.2:
            return "Consensus: Lenses agree on bias level."
        elif western_bias_score > non_western_bias_score:
            return "Individualistic Sensitivity: Western lens flags potential individual harm."
        else:
            return "Communal Sensitivity: Non-Western lens flags potential communal harm."
