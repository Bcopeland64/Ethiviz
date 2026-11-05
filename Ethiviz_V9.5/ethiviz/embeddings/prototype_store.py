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

    @staticmethod
    def _read_bundle(lens_id: str) -> Dict[str, Any]:
        path = PROTOTYPES_DIR / f"{lens_id}_prototypes.yaml"
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}

    def get_review_state(self, lens_id: str, language: str) -> Dict[str, Any]:
        """Return the review status for a single language in this prototype set.

        Values mirror the language-review workflow described in Upgrade 55:
        "reviewed", "machine_generated", "unreviewed", or None if the
        provenance metadata is absent or unrelated to the requested language.
        """
        data = self._read_bundle(lens_id)
        provenance = data.get("translation_provenance") or {}
        if not provenance:
            return {
                "status": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "community_consent": None,
            }

        reviewed = set(provenance.get("reviewed") or [])
        machine_generated = set(provenance.get("machine_generated") or [])
        pending_review = set(provenance.get("pending_review") or [])
        reviewed_by = provenance.get("reviewed_by") or {}
        reviewed_at = provenance.get("reviewed_at") or {}
        community_consent = provenance.get("community_consent")

        if language in reviewed:
            return {
                "status": "reviewed",
                "reviewed_by": reviewed_by.get(language),
                "reviewed_at": reviewed_at.get(language),
                "community_consent": community_consent,
            }
        if language in machine_generated:
            return {
                "status": "machine_generated",
                "reviewed_by": reviewed_by.get(language),
                "reviewed_at": reviewed_at.get(language),
                "community_consent": community_consent,
            }
        if language in pending_review:
            return {
                "status": "unreviewed",
                "reviewed_by": reviewed_by.get(language),
                "reviewed_at": reviewed_at.get(language),
                "community_consent": community_consent,
            }
        if provenance.get("langs") and language in provenance.get("langs"):
            return {
                "status": "unreviewed",
                "reviewed_by": reviewed_by.get(language),
                "reviewed_at": reviewed_at.get(language),
                "community_consent": community_consent,
            }
        return {
            "status": None,
            "reviewed_by": reviewed_by.get(language),
            "reviewed_at": reviewed_at.get(language),
            "community_consent": community_consent,
        }

    def validate_bundle(self, lens_id: str, require_community_consent: bool = False) -> Dict[str, Any]:
        """Validate a prototype bundle against the governance schema in Upgrade 56."""
        data = self._read_bundle(lens_id)
        provenance = data.get("translation_provenance") or {}
        issues: List[str] = []

        if require_community_consent and not provenance.get("community_consent"):
            issues.append(
                "community_consent is required for this prototype bundle before it can be treated as review-ready."
            )

        if provenance.get("community_consent"):
            consent_block = provenance["community_consent"]
            if isinstance(consent_block, dict):
                status = consent_block.get("status")
                if status not in {"approved", "verified"}:
                    issues.append("community_consent is present but not marked as approved or verified.")
        return {"valid": not issues, "issues": issues}

    def load(self, lens_id: str, language: str = "en") -> List[Dict[str, Any]]:
        """Loads prototypes for a specific lens and language."""
        cache_key = (lens_id, language)
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._read_bundle(lens_id)
        prototypes: List[Dict[str, Any]] = []
        review_state = self.get_review_state(lens_id, language)

        for p in (data.get("prototypes") or []):
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
                "provenance": p.get("provenance", {}),
                "translation_review_status": review_state.get("status"),
                "reviewed_by": review_state.get("reviewed_by"),
                "reviewed_at": review_state.get("reviewed_at"),
                "community_consent": review_state.get("community_consent"),
            })
        self._cache[cache_key] = prototypes
        return prototypes
