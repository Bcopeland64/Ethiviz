# ethiviz/analysis/image_analysis.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class ImageAnalysisResult:
    """
    Result of a computer vision bias analysis (Figure A2).
    """
    image_id: str
    detected_faces: int
    skin_tone_distribution: Dict[str, float]
    cultural_elements: List[str]
    essentialism_risk: float
    detected_objects: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
