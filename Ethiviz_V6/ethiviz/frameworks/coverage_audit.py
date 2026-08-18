# ethiviz/frameworks/coverage_audit.py
"""
Framework self-audit (Upgrade 36).

CrossCulturalEquityDashboard's CREI measures whether the *content being
analyzed* gives balanced signal across the 7 traditions. It says nothing
about whether the traditions themselves are equitably represented inside
EthiViz's own prototype corpus — the underlying detection capability. This
module answers that: it inspects each tradition's prototype YAML directly
(the source of truth already used by ethiviz.embeddings.prototype_store) and
reports prototype counts, category coverage, declared languages, and
translation review status per tradition, plus a Framework Coverage Index
using the same coefficient-of-variation formula as the frontend's CREI.

This closes the open question the V5 improvement plan left unanswered:
"Should CREI also evaluate the EthiViz tool itself?"
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROTOTYPES_DIR = Path(__file__).parent.parent / "embeddings" / "prototypes"

ALL_TRADITIONS: dict[str, str] = {
    "western_v1": "Western",
    "ubuntu_v1": "Ubuntu",
    "confucian_v2": "Confucian",
    "islamic_v1": "Islamic",
    "buddhist_v1": "Buddhist",
    "hindu_v1": "Hindu / Dharmic",
    "indigenous_v1": "Indigenous / First Nations",
}


@dataclass
class TraditionCoverage:
    framework_id: str
    label: str
    prototype_count: int
    category_count: int
    languages_declared: list[str]
    translations_reviewed: int
    translations_machine_generated: int
    translations_undeclared: bool  # has translations but no provenance block at all


def _load_prototype_file(framework_id: str) -> dict:
    path = PROTOTYPES_DIR / f"{framework_id}_prototypes.yaml"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def audit_tradition(framework_id: str) -> TraditionCoverage:
    label = ALL_TRADITIONS.get(framework_id, framework_id)
    data = _load_prototype_file(framework_id)
    prototypes = data.get("prototypes", []) or []

    categories = {p.get("category") for p in prototypes if p.get("category")}
    languages: set[str] = set()
    has_translations = False
    for p in prototypes:
        translations = p.get("translations") or {}
        if translations:
            has_translations = True
        languages.update(translations.keys())

    provenance = data.get("translation_provenance")
    if provenance:
        reviewed = len(provenance.get("reviewed") or [])
        machine_generated = len(provenance.get("machine_generated") or [])
        undeclared = False
    else:
        # Four of the seven builtin lenses (western, ubuntu, confucian,
        # islamic) ship translations with no translation_provenance block at
        # all, so their review status is unknown rather than "reviewed" —
        # that ambiguity is itself worth surfacing, not defaulting away.
        reviewed = 0
        machine_generated = 0
        undeclared = has_translations

    return TraditionCoverage(
        framework_id=framework_id,
        label=label,
        prototype_count=len(prototypes),
        category_count=len(categories),
        languages_declared=sorted(languages),
        translations_reviewed=reviewed,
        translations_machine_generated=machine_generated,
        translations_undeclared=undeclared,
    )


def audit_all() -> list[TraditionCoverage]:
    return [audit_tradition(fid) for fid in ALL_TRADITIONS]


def framework_coverage_index(coverages: list[TraditionCoverage] | None = None) -> float:
    """1 minus the coefficient of variation of prototype_count across
    traditions — the same formula CrossCulturalEquityDashboard.tsx uses for
    CREI, applied to the tool's own corpus instead of per-request content
    scores. 1.0 = every tradition has an equal-sized prototype corpus; lower
    values mean some traditions are structurally under-represented in what
    EthiViz can even detect, independent of any single analysis run.
    """
    coverages = coverages if coverages is not None else audit_all()
    counts = [c.prototype_count for c in coverages]
    if not counts:
        return 1.0
    mean = sum(counts) / len(counts)
    if mean == 0:
        return 1.0
    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    cv = (variance ** 0.5) / (mean + 1e-9)
    return max(0.0, 1 - cv)


def is_language_reviewed(framework_id: str, language: str) -> bool | None:
    """True if `language` is in the reviewed list, False if it's known
    machine-generated, None if the lens has no provenance declaration at all
    (unknown review status) or the language isn't tracked."""
    data = _load_prototype_file(framework_id)
    provenance = data.get("translation_provenance")
    if not provenance:
        return None
    if language in (provenance.get("reviewed") or []):
        return True
    if language in (provenance.get("machine_generated") or []):
        return False
    return None


def coverage_report() -> dict:
    coverages = audit_all()
    return {
        "framework_coverage_index": round(framework_coverage_index(coverages), 4),
        "traditions": [
            {
                "framework_id": c.framework_id,
                "label": c.label,
                "prototype_count": c.prototype_count,
                "category_count": c.category_count,
                "languages_declared": c.languages_declared,
                "translations_reviewed": c.translations_reviewed,
                "translations_machine_generated": c.translations_machine_generated,
                "translations_undeclared": c.translations_undeclared,
            }
            for c in coverages
        ],
    }
