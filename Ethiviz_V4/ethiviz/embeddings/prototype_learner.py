# ethiviz/embeddings/prototype_learner.py
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml
from ethiviz.embeddings.prototype_store import PrototypeStore, PROTOTYPES_DIR

@dataclass
class UncertainCase:
    """A detection result in the ambiguous similarity range requiring expert review."""
    case_id: str
    lens_id: str
    input_text: str
    bias_score: float
    top_prototype_id: str
    top_prototype_similarity: float
    language: str
    dataset_source: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

@dataclass
class ConfirmedPrototype:
    """An expert-confirmed bias case ready for write-back to prototype store."""
    case_id: str
    lens_id: str
    prototype_id: str         # assigned by expert
    text: str
    severity: float           # 0.0–1.0, assigned by expert
    category: str             # bias category, assigned by expert
    language: str
    confirmed_by: str         # reviewer identifier
    confirmed_at: str
    source_case_id: str       # links back to UncertainCase
    provenance: dict[str, Any] = field(default_factory=dict)

class PrototypeLearner:
    """
    Active learning loop for prototype store maintenance.

    Collects uncertain detections (similarity 0.55–0.75), queues them for
    expert review, and writes confirmed cases back to the prototype YAML
    with full provenance tracking.

    Every write-back records: who confirmed it, when, what similarity score
    triggered the review, which dataset it came from, and the library version.
    This provenance chain makes the prototype evolution auditable.

    Example:
        >>> learner = PrototypeLearner()
        >>> # After running analysis on a dataset:
        >>> uncertain = learner.collect_uncertain(lens_scores, dataset_source="news_corpus")
        >>> print(f"{len(uncertain)} cases queued for review")
        12 cases queued for review
        >>> # After expert review:
        >>> confirmed = ConfirmedPrototype(
        ...     case_id=uncertain[0].case_id,
        ...     lens_id="islamic_v1",
        ...     prototype_id="islamic_essentialism_011",
        ...     text=uncertain[0].input_text,
        ...     severity=0.80,
        ...     category="islamic_essentialism",
        ...     language="en",
        ...     confirmed_by="expert_001",
        ...     confirmed_at=datetime.now(timezone.utc).isoformat(),
        ...     source_case_id=uncertain[0].case_id,
        ... )
        >>> learner.write_back([confirmed])
        >>> # Prototype YAML now contains the new entry with provenance
    """
    UNCERTAINTY_LOWER = 0.55
    UNCERTAINTY_UPPER = 0.75
    QUEUE_DIR = PROTOTYPES_DIR / "review_queue"

    def __init__(self) -> None:
        self.QUEUE_DIR.mkdir(exist_ok=True)

    def collect_uncertain(
        self,
        lens_scores: list[Any],       # list[LensScore]
        dataset_source: str,
        texts: list[str] | None = None,
    ) -> list[UncertainCase]:
        """
        Scan LensScore objects for detections in the uncertainty band.
        Returns UncertainCase objects and persists them to the review queue.
        """
        uncertain = []
        for score in lens_scores:
            for proto_id, sim in score.semantic_similarity_scores.items():
                if self.UNCERTAINTY_LOWER <= sim <= self.UNCERTAINTY_UPPER:
                    case_id = hashlib.sha256(
                        f"{score.lens_id}:{proto_id}:{sim}:{dataset_source}".encode()
                    ).hexdigest()[:16]
                    case = UncertainCase(
                        case_id=case_id,
                        lens_id=score.lens_id,
                        input_text=score.raw_evidence.get("input_text", ""),
                        bias_score=score.overall_score,
                        top_prototype_id=proto_id,
                        top_prototype_similarity=sim,
                        language=score.language_detected,
                        dataset_source=dataset_source,
                    )
                    uncertain.append(case)
        self._persist_queue(uncertain)
        return uncertain

    def get_review_queue(self, lens_id: str | None = None) -> list[UncertainCase]:
        """Load all pending review cases, optionally filtered by lens."""
        cases = []
        for path in self.QUEUE_DIR.glob("*.json"):
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            case = UncertainCase(**data)
            if lens_id is None or case.lens_id == lens_id:
                cases.append(case)
        return cases

    def write_back(self, confirmed: list[ConfirmedPrototype]) -> dict[str, int]:
        """
        Write confirmed prototypes back to the appropriate prototype YAML file.
        Returns {lens_id: n_written} summary.

        The write-back format appends to the existing prototype list and records
        full provenance in each new entry so the prototype's origin is traceable.
        Raises ValueError if a prototype_id already exists in the YAML (prevents
        duplicate entries from repeated review sessions).
        """
        written: dict[str, int] = {}
        by_lens: dict[str, list[ConfirmedPrototype]] = {}
        for c in confirmed:
            by_lens.setdefault(c.lens_id, []).append(c)

        for lens_id, cases in by_lens.items():
            path = PROTOTYPES_DIR / f"{lens_id}_prototypes.yaml"
            with path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            existing_ids = {p["id"] for p in data["prototypes"]}
            new_entries = []
            for c in cases:
                if c.prototype_id in existing_ids:
                    raise ValueError(
                        f"Prototype ID '{c.prototype_id}' already exists in "
                        f"{lens_id}_prototypes.yaml. Use a unique ID."
                    )
                entry = {
                    "id": c.prototype_id,
                    "text": c.text,
                    "severity": c.severity,
                    "category": c.category,
                    "language": c.language,
                    "provenance": {
                        "confirmed_by": c.confirmed_by,
                        "confirmed_at": c.confirmed_at,
                        "source_case_id": c.source_case_id,
                        "active_learning": True,
                        **c.provenance,
                    },
                }
                new_entries.append(entry)
                existing_ids.add(c.prototype_id)

            data["prototypes"].extend(new_entries)
            with path.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)

            # Remove confirmed cases from review queue
            for c in cases:
                queue_path = self.QUEUE_DIR / f"{c.source_case_id}.json"
                if queue_path.exists():
                    queue_path.unlink()

            written[lens_id] = len(new_entries)
        return written

    def _persist_queue(self, cases: list[UncertainCase]) -> None:
        for case in cases:
            path = self.QUEUE_DIR / f"{case.case_id}.json"
            if not path.exists():
                with path.open("w", encoding="utf-8") as f:
                    json.dump(case.__dict__, f, indent=2, ensure_ascii=False)
