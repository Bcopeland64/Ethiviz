from __future__ import annotations
import re
import numpy as np
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

_ERASURE_PATTERNS = [
    re.compile(r"\bafrican\s+(?:cultures?|societies?|nations?)\s+"
               r"(?:lack|are\s+(?:primitive|backward|inferior|uncivilized|unsophisticated))\b", re.I),
    re.compile(r"\bafrican\s+(?:languages?|knowledge|philosophy|traditions?)\s+"
               r"(?:are\s+)?(?:primitive|superstition|worthless|invalid|not\s+real)\b", re.I),
    re.compile(r"\bno\s+(?:place|role|value)\s+(?:for\s+)?(?:african|ubuntu|traditional)\b", re.I),
]
_COMM_DEVALUE_PATTERNS = [
    re.compile(r"\b(?:community|family|collective)\s+(?:obligations?|ties?|bonds?)\s+"
               r"(?:are\s+)?(?:obstacles?|burdens?|hindrances?|backward)\b", re.I),
    re.compile(r"\b(?:only|just)\s+(?:the\s+)?individual\s+(?:matters?|counts?|succeeds?)\b", re.I),
    re.compile(r"\b(?:self.?made|pull\s+yourself\s+up)\b.*\b(?:alone|by\s+yourself|no\s+help)\b", re.I),
]
_UBUNTU_VIOL_PATTERNS = [
    re.compile(r"\b(?:deserve|deserve\s+their)\s+(?:poverty|suffering|hardship|misery)\b", re.I),
    re.compile(r"\b(?:burdens?|drain|dead\s+weight)\s+(?:on|to)\s+(?:society|the\s+economy|us)\b", re.I),
    re.compile(r"\b(?:homeless?|disabled|elderly|poor)\s+(?:are|were)\s+"
               r"(?:burdens?|problems?|drains?|useless)\b", re.I),
]
_ESSENTIALISM_PATTERNS = [
    re.compile(r"\ball\s+(?:africans?|black\s+people)\s+(?:are|have|do|think|believe)\b", re.I),
    re.compile(r"\bafrica\s+needs?\s+(?:western|foreign|outside)\s+"
               r"(?:intervention|help|saving|leadership)\b", re.I),
    re.compile(r"\btribal\s+(?:mentality|mindset|culture|thinking)\b", re.I),
]

_CATEGORY_PATTERNS = {
    "cultural_erasure": _ERASURE_PATTERNS,
    "community_devaluation": _COMM_DEVALUE_PATTERNS,
    "ubuntu_violation": _UBUNTU_VIOL_PATTERNS,
    "african_essentialism": _ESSENTIALISM_PATTERNS,
}


class UbuntuLens(EthicalLens):
    """Ubuntu Ethical Lens (v1) — communal dignity, relational ethics, anti-essentialism."""

    def __init__(self, use_semantic: bool = True) -> None:
        super().__init__("ubuntu_v1", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        self._dim_weights = {
            "cultural_erasure": 0.30,
            "community_devaluation": 0.25,
            "ubuntu_violation": 0.25,
            "african_essentialism": 0.20,
        }

    def score(self, input_data: str, language: str = "en", **kwargs: Any) -> LensScore:
        all_sim: dict[str, float] = {}
        if self.use_semantic:
            all_sim = self.detector.detect(input_data, self.lens_id, language=language)

        dim_scores = self._compute_dimension_scores(input_data, all_sim)
        overall = min(1.0, sum(dim_scores.get(d, 0.0) * w for d, w in self._dim_weights.items()))
        ci = self._bootstrap_ci(list(dim_scores.values()))

        flagged = [pid for pid, s in all_sim.items() if s > 0.55]
        recs: list[str] = []
        if dim_scores.get("cultural_erasure", 0) > 0.5:
            recs.append("Text may erase or delegitimise African cultural knowledge.")
        if dim_scores.get("ubuntu_violation", 0) > 0.5:
            recs.append("Review for language that denies communal dignity or mutual care.")
        if dim_scores.get("african_essentialism", 0) > 0.5:
            recs.append("Check for essentialism that flattens diverse African identities.")

        return LensScore(
            lens_id=self.lens_id,
            overall_score=overall,
            calibrated_score=None,
            dimension_scores=dim_scores,
            flagged_items=flagged,
            recommendations=recs,
            confidence=0.88 if self.use_semantic else 0.55,
            confidence_interval_95=ci,
            bootstrap_n=200,
            raw_evidence={"input_text": input_data, "semantic_scores": all_sim},
            semantic_similarity_scores=all_sim,
            language_detected=language,
        )

    def _compute_dimension_scores(
        self, text: str, all_sim: dict[str, float]
    ) -> dict[str, float]:
        from ethiviz.embeddings.prototype_store import PrototypeStore
        store = PrototypeStore()
        prototypes = store.load(self.lens_id)
        id_to_category = {p["id"]: p["category"] for p in prototypes}

        dim_semantic: dict[str, list[float]] = {d: [] for d in self._dim_weights}
        for proto_id, sim in all_sim.items():
            cat = id_to_category.get(proto_id, "")
            if cat in dim_semantic:
                dim_semantic[cat].append(sim)

        scores: dict[str, float] = {}
        for dim, patterns in _CATEGORY_PATTERNS.items():
            sem = max(dim_semantic.get(dim, [0.0]))
            regex_hit = 1.0 if any(p.search(text) for p in patterns) else 0.0
            scores[dim] = min(1.0, (0.70 * sem) + (0.30 * regex_hit))
        return scores

    @staticmethod
    def _bootstrap_ci(
        values: list[float], n: int = 200, seed: int = 42
    ) -> tuple[float, float]:
        if not values:
            return (0.0, 0.0)
        arr = np.array(values, dtype=float)
        rng = np.random.default_rng(seed)
        means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n)]
        return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


class SocialGraphUpgrade:
    """Stub for future Social Graph-based upgrade."""
    pass
