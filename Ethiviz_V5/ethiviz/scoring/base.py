from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from ethiviz.lenses.base import LensScore
from ethiviz.frameworks.conflict import FrameworkConflict
from ethiviz.context.deployment import DeploymentContext
from ethiviz.utils.reproducibility import ReproducibilityRecord
from ethiviz.analysis.weat import WEATTestSuite, iWEATResult

@dataclass
class BiasCandidate:
    text: str
    score: float
    lens_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FrameworkScore:
    framework_id: str
    framework_name: str
    overall_score: float
    dimension_scores: Dict[str, float]
    confidence: float
    flagged_candidates: List[str]
    confidence_interval_95: tuple[float, float]
    bootstrap_n: int
    raw_evidence: Dict[str, Any]
    calibrated_score: float | None = None    # Upgrade 9

@dataclass
class ScoredResult:
    candidates: list[BiasCandidate]
    framework_scores: list[FrameworkScore]
    consensus_score: float | None
    conflicts: list[FrameworkConflict]       # Upgrade 4
    synergy_amplifications: list[str]        # Upgrade 14
    weat_results: dict[str, WEATTestSuite] | None
    iweat_results: dict[str, iWEATResult] | None  # Upgrade 16
    deployment_context: DeploymentContext | None   # Upgrade 13
    reproducibility: ReproducibilityRecord         # Upgrade 18
    metadata: dict[str, Any]

    def generate_report(self) -> Any: ... # Will be defined in reporting
    def top_biases(self, n: int = 5) -> list[BiasCandidate]:
        return sorted(self.candidates, key=lambda c: c.score, reverse=True)[:n]
