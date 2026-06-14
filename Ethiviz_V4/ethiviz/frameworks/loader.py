from __future__ import annotations
import yaml
from pathlib import Path
import hashlib
from ethiviz.frameworks.base import CulturalFramework, FrameworkRegistry

BUILTIN_DIR = Path(__file__).parent / "builtin"

class FrameworkLoader:
    """Loads cultural frameworks from YAML files."""
    def __init__(self, registry: FrameworkRegistry | None = None) -> None:
        self.registry = registry or FrameworkRegistry()

    def load_builtin(self) -> FrameworkRegistry:
        """Loads all builtin frameworks from the builtin directory."""
        if not BUILTIN_DIR.exists():
            return self.registry

        for yaml_path in BUILTIN_DIR.glob("*.yaml"):
            self.load_file(yaml_path)
        return self.registry

    def load_file(self, path: Path) -> CulturalFramework:
        """Loads a single framework from a YAML file."""
        content = path.read_bytes()
        yaml_hash = hashlib.sha256(content).hexdigest()[:16]
        
        data = yaml.safe_load(content)
        framework = CulturalFramework(
            framework_id=data["id"],
            name=data["name"],
            description=data["description"],
            ethical_lenses=data.get("ethical_lenses", []),
            bias_criteria=data.get("bias_criteria", {}),
            validation=data.get("validation", {})
        )
        self.registry.register(framework, yaml_hash)
        return framework
