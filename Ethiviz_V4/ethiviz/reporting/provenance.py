# ethiviz/reporting/provenance.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class EvidenceItem:
    """One piece of evidence supporting a bias finding."""
    evidence_type: str       # "prototype_match" | "weat_test" | "co_occurrence"
                             # | "demographic_imbalance" | "dignity_violation"
    evidence_id: str         # prototype_id, weat_test_name, or description
    evidence_text: str       # Human-readable description
    similarity_or_score: float
    lens_id: str
    language: str

@dataclass
class ProvenanceRecord:
    """
    Full provenance chain for one bias finding, linking the high-level
    score back to specific evidence items.
    """
    finding_summary: str
    lens_scores: dict[str, float]          # lens_id → overall_score
    evidence_items: list[EvidenceItem]
    prototype_versions: dict[str, str]     # lens_id → YAML hash at analysis time
    weat_results_summary: list[str]        # interpretations of significant WEAT tests
    conflict_summary: list[str]            # descriptions of framework conflicts
    calibration_applied: bool
    confidence_intervals: dict[str, tuple[float, float]]  # lens_id → (lower, upper)
    reproducibility_id: str               # links to ReproducibilityRecord
