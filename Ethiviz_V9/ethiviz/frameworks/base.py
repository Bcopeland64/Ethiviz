from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class CulturalFramework:
    framework_id: str
    name: str
    description: str
    ethical_lenses: List[str]
    bias_criteria: Dict[str, float]
    validation: Dict[str, Any] = field(default_factory=dict)
    # Upgrade 54 (V7 Phase 3): each builtin YAML declares its own
    # low/moderate/high/critical cutoffs, previously parsed by FrameworkLoader
    # into nothing — see Scripts/ethiviz_bridge.py's _severity_for for how
    # this is actually used (the raw YAML values share their scale with
    # ethiviz/metrics/group_fairness.py's TRADITION_THRESHOLDS, not this
    # engine's own 0-1 lens score, so they're rescaled there, not applied
    # literally).
    severity_thresholds: Dict[str, float] = field(default_factory=dict)

class FrameworkRegistry:
    """Registry to manage and track framework versions."""
    def __init__(self) -> None:
        self._frameworks: Dict[str, CulturalFramework] = {}
        self._hashes: Dict[str, str] = {}

    def register(self, framework: CulturalFramework, yaml_hash: str) -> None:
        self._frameworks[framework.framework_id] = framework
        self._hashes[framework.framework_id] = yaml_hash

    def get(self, framework_id: str) -> Optional[CulturalFramework]:
        return self._frameworks.get(framework_id)

    def get_hash(self, framework_id: str) -> Optional[str]:
        return self._hashes.get(framework_id)

    @property
    def registered_ids(self) -> List[str]:
        return list(self._frameworks.keys())
