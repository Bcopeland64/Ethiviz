from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

PROTOTYPES_DIR = Path(__file__).parent / "prototypes"

class PrototypeStore:
    """Manages biased prototypes for semantic detection."""
    def __init__(self) -> None:
        PROTOTYPES_DIR.mkdir(parents=True, exist_ok=True)

    def load(self, lens_id: str, language: str = "en") -> List[Dict[str, Any]]:
        """Loads prototypes for a specific lens and language."""
        path = PROTOTYPES_DIR / f"{lens_id}_prototypes.yaml"
        if not path.exists():
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
                else:
                    print(f"Warning: No '{language}' translation for prototype '{p.get('id')}' in '{lens_id}'. Falling back to English.")
            
            prototypes.append({
                "id": p.get("id"),
                "text": text,
                "severity": p.get("severity", 1.0),
                "category": p.get("category", "general"),
                "language": language if language in p.get("translations", {}) else "en",
                "provenance": p.get("provenance", {})
            })
        return prototypes
