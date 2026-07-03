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
