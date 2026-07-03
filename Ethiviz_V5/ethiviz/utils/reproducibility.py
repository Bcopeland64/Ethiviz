# ethiviz/utils/reproducibility.py
from __future__ import annotations
import hashlib
import importlib.metadata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass
class ReproducibilityRecord:
    """
    Captures all state needed to reproduce an analysis result exactly.
    Automatically populated by Analyzer for every ScoredResult.

    Example:
        >>> record = ReproducibilityRecord.capture(
        ...     framework_ids=["western_v1", "ubuntu_v1"],
        ...     random_seed=42
        ... )
        >>> record.library_version
        '0.4.0'
    """
    analysis_id: str
    library_version: str
    embedding_model_id: str
    framework_ids: list[str]
    prototype_yaml_hashes: dict[str, str]   # lens_id → SHA-256 of YAML file
    framework_yaml_hashes: dict[str, str]   # framework_id → SHA-256 of YAML file
    random_seed: int
    n_bootstrap_samples: int
    recorded_at: str
    python_version: str

    @classmethod
    def capture(
        cls,
        framework_ids: list[str],
        random_seed: int = 42,
        n_bootstrap: int = 1000,
    ) -> ReproducibilityRecord:
        import sys
        from ethiviz.embeddings.model import MODEL_ID
        from ethiviz.embeddings.prototype_store import PROTOTYPES_DIR
        # from ethiviz.frameworks.loader import FrameworkLoader  # Not needed for capture yet

        proto_hashes = {}
        for lens_id in framework_ids:
            path = PROTOTYPES_DIR / f"{lens_id}_prototypes.yaml"
            if path.exists():
                proto_hashes[lens_id] = _file_hash(path)

        fw_hashes = {}
        fw_dir = Path(__file__).parent.parent / "frameworks" / "builtin"
        for fw_id in framework_ids:
            path = fw_dir / f"{fw_id}.yaml"
            if path.exists():
                fw_hashes[fw_id] = _file_hash(path)

        try:
            version = importlib.metadata.version("ethiviz")
        except importlib.metadata.PackageNotFoundError:
            version = "dev"

        analysis_id = hashlib.sha256(
            f"{version}:{framework_ids}:{random_seed}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        return cls(
            analysis_id=analysis_id,
            library_version=version,
            embedding_model_id=MODEL_ID,
            framework_ids=framework_ids,
            prototype_yaml_hashes=proto_hashes,
            framework_yaml_hashes=fw_hashes,
            random_seed=random_seed,
            n_bootstrap_samples=n_bootstrap,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
