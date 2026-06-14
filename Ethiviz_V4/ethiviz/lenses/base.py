# ethiviz/lenses/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class LensScore:
    lens_id: str
    overall_score: float
    calibrated_score: float | None          # Upgrade 9 — None until calibrator fitted
    dimension_scores: dict[str, float]
    flagged_items: list[str]
    recommendations: list[str]
    confidence: float
    confidence_interval_95: tuple[float, float]
    bootstrap_n: int
    raw_evidence: dict[str, Any]
    token_attributions: list[tuple[str, float]] = field(default_factory=list)
    semantic_similarity_scores: dict[str, float] = field(default_factory=dict)
    language_detected: str = "en"           # Upgrade 11 — ISO 639-1 code
    prototype_version_hash: str = ""        # Upgrade 19 — hash of prototype YAML used

class EthicalLens(ABC):
    """Base class for all ethical lenses (Western, Ubuntu, etc.)."""
    
    def __init__(self, lens_id: str, use_semantic: bool = True) -> None:
        self.lens_id = lens_id
        self.use_semantic = use_semantic

    @abstractmethod
    def score(self, input_data: Any, **kwargs: Any) -> LensScore:
        """Score input data through this ethical lens."""
        pass
