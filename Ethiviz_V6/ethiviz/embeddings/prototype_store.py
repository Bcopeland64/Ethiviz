from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

PROTOTYPES_DIR = Path(__file__).parent / "prototypes"

class PrototypeStore:
    """Manages biased prototypes for semantic detection."""

    # Shared across all instances (lenses each construct their own
    # PrototypeStore()) so the YAML for a given lens is only ever read and
    # parsed from disk once per process, instead of on every call to score().
    _cache: Dict[tuple, List[Dict[str, Any]]] = {}

    def __init__(self) -> None:
        PROTOTYPES_DIR.mkdir(parents=True, exist_ok=True)

    def load(self, lens_id: str, language: str = "en") -> List[Dict[str, Any]]:
        """Loads prototypes for a specific lens and language."""
        cache_key = (lens_id, language)
        if cache_key in self._cache:
            return self._cache[cache_key]

        path = PROTOTYPES_DIR / f"{lens_id}_prototypes.yaml"
        if not path.exists():
            self._cache[cache_key] = []
            return []

        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        prototypes = []
        for p in data.get("prototypes", []):
            text = p.get("text", "")
            if language != "en":
                translations = p.get("translations", {})
                if language in translations:
                    text = translations[language]
                # Missing translations fall back to the English text. This is
                # surfaced structurally via each prototype's "language" field,
                # which callers aggregate into a CoverageReport — it used to
                # print() to stdout, where it reached a server log at best and
                # never reached the caller acting on the score.

            prototypes.append({
                "id": p.get("id"),
                "text": text,
                "severity": p.get("severity", 1.0),
                "category": p.get("category", "general"),
                "language": language if language in p.get("translations", {}) else "en",
                "provenance": p.get("provenance", {})
            })
        self._cache[cache_key] = prototypes
        return prototypes
