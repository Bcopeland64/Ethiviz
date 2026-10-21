# ethiviz/frameworks/versioning.py
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class FrameworkVersion:
    framework_id: str
    yaml_hash: str              # SHA-256 of YAML content (first 16 chars)
    version_string: str         # from YAML last_updated field
    recorded_at: str

class FrameworkVersionTracker:
    """
    Tracks which version of each framework YAML was used for an analysis.

    If confucian_v2.yaml changes between two analyses, their scores are not
    directly comparable. This tracker records the YAML hash at analysis time
    so comparisons can be qualified with "using the same framework version."

    Integrated into ReproducibilityRecord automatically.

    Example:
        >>> tracker = FrameworkVersionTracker()
        >>> versions = tracker.snapshot(["western_v1", "ubuntu_v1"])
        >>> versions["western_v1"].yaml_hash
        'a3f9b21c'
        >>> # After YAML update:
        >>> new_versions = tracker.snapshot(["western_v1", "ubuntu_v1"])
        >>> tracker.changed_since(versions, new_versions)
        ['western_v1']  # only western changed
    """
    BUILTIN_DIR = Path(__file__).parent / "builtin"

    def snapshot(self, framework_ids: list[str]) -> dict[str, FrameworkVersion]:
        from datetime import datetime, timezone
        import yaml as _yaml
        versions = {}
        for fw_id in framework_ids:
            path = self.BUILTIN_DIR / f"{fw_id}.yaml"
            if not path.exists():
                continue
            content = path.read_bytes()
            h = hashlib.sha256(content).hexdigest()[:16]
            data = _yaml.safe_load(content)
            versions[fw_id] = FrameworkVersion(
                framework_id=fw_id,
                yaml_hash=h,
                version_string=str(data.get("validation", {}).get("last_updated", "unknown")),
                recorded_at=datetime.now(timezone.utc).isoformat(),
            )
        return versions

    def changed_since(
        self,
        baseline: dict[str, FrameworkVersion],
        current: dict[str, FrameworkVersion],
    ) -> list[str]:
        """Returns list of framework IDs whose YAML hashes changed."""
        changed = []
        for fw_id in set(list(baseline.keys()) + list(current.keys())):
            b_hash = baseline.get(fw_id, FrameworkVersion(fw_id, "", "", "")).yaml_hash
            c_hash = current.get(fw_id, FrameworkVersion(fw_id, "", "", "")).yaml_hash
            if b_hash != c_hash:
                changed.append(fw_id)
        return changed
