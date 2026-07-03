from __future__ import annotations
import re
import numpy as np
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

# Regex patterns that signal Western-framework bias categories.
# These detect deficit framing, slurs, and supremacist language —
# NOT the neutral philosophical vocabulary.
_RACIAL_PATTERNS = [
    re.compile(r"\b(?:blacks?|hispanics?|latinos?|asians?|arabs?|jews?)\s+"
               r"(?:are|were|will be)\s+(?:inferior|primitive|criminal|lazy|violent|dangerous)", re.I),
    re.compile(r"\b(?:all|every|most)\s+(?:black|hispanic|asian|arab|immigrant|minority)"
               r"\s+(?:people|men|women|persons)\b.*\b(?:crime|theft|violence|fraud|drugs?)\b", re.I),
    re.compile(r"\bgenetically\s+(?:inferior|predisposed|incapable)\b", re.I),
    re.compile(r"\b(?:replace|replacement|invasion)\b.*\b(?:whites?|western|civilization)\b", re.I),
]
_GENDER_PATTERNS = [
    re.compile(r"\bwomen\s+are\s+(?:too|naturally|inherently)\s+"
               r"(?:emotional|weak|irrational|unfit|unsuited)\b", re.I),
    re.compile(r"\b(?:women|females?)\s+(?:belong|should stay|should be)\s+"
               r"(?:in the kitchen|at home|barefoot)\b", re.I),
    re.compile(r"\b(?:men|males?)\s+are\s+(?:naturally|inherently|always)\s+better\s+at\b", re.I),
    re.compile(r"\b(?:primary|only|true)\s+role\s+of\s+(?:a\s+)?women?\b", re.I),
]
_STEREO_PATTERNS = [
    re.compile(r"\ball\s+(?:asians?|blacks?|arabs?|muslims?|latinos?|immigrants?)\s+"
               r"(?:are|do|have|can'?t|cannot|don'?t)\b", re.I),
    re.compile(r"\bmodel\s+minority\b", re.I),
    re.compile(r"\b(?:they|those people)\s+all\s+(?:look|act|think|behave)\s+the same\b", re.I),
]
_RIGHTS_PATTERNS = [
    re.compile(r"\b(?:minorities|immigrants|refugees|foreigners)\s+do\s+not\s+deserve\b", re.I),
    re.compile(r"\b(?:survey|monitor|track|surveil)\s+(?:all\s+)?(?:muslims?|arabs?|immigrants?)"
               r"\b", re.I),
    re.compile(r"\bwithout\s+(?:warrant|due\s+process|trial)\b", re.I),
]
_CULTSUP_PATTERNS = [
    re.compile(r"\b(?:western|christian|european)\s+(?:civilization|culture|values)\s+is\s+"
               r"(?:the\s+)?(?:pinnacle|superior|greatest|best)\b", re.I),
    re.compile(r"\b(?:backward|primitive|uncivilized)\s+(?:cultures?|nations?|people)\b", re.I),
    re.compile(r"\bneeds?\s+(?:western|civilized)\s+(?:intervention|help|saving)\b", re.I),
]

_CATEGORY_PATTERNS = {
    "racial_bias": _RACIAL_PATTERNS,
    "gender_bias": _GENDER_PATTERNS,
    "stereotyping": _STEREO_PATTERNS,
    "individual_rights_violation": _RIGHTS_PATTERNS,
    "cultural_superiority": _CULTSUP_PATTERNS,
}


class WesternLens(EthicalLens):
    """Western Ethical Lens (v1) — rights, equality, anti-discrimination."""

    def __init__(self, registry=None, use_semantic: bool = True) -> None:
        super().__init__("western_v1", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        # bias_criteria weights from framework YAML (duplicated here for speed)
        self._dim_weights = {
            "racial_bias": 0.25,
            "gender_bias": 0.20,
            "stereotyping": 0.20,
            "individual_rights_violation": 0.20,
            "cultural_superiority": 0.10,
            "procedural_bias": 0.05,
        }

    def score(self, input_data: str, language: str = "en", **kwargs: Any) -> LensScore:
        # ── Semantic scoring: group prototypes by category ──────────────────
        all_sim: dict[str, float] = {}
        if self.use_semantic:
            all_sim = self.detector.detect(input_data, self.lens_id, language=language)

        dim_scores = self._compute_dimension_scores(input_data, all_sim)

        # Weighted overall score
        overall = sum(
            dim_scores.get(dim, 0.0) * w for dim, w in self._dim_weights.items()
        )
        overall = min(1.0, overall)

        # Bootstrap CI over dimension scores
        ci = self._bootstrap_ci(list(dim_scores.values()))

        flagged = [proto_id for proto_id, s in all_sim.items() if s > 0.55]
        recs: list[str] = []
        if dim_scores.get("racial_bias", 0) > 0.5:
            recs.append("Review racial/ethnic framing for deficit narratives.")
        if dim_scores.get("gender_bias", 0) > 0.5:
            recs.append("Audit language for gender essentialism.")
        if dim_scores.get("cultural_superiority", 0) > 0.5:
            recs.append("Check for cultural hierarchisation or supremacist framing.")

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
        """
        For each bias_criteria dimension, combine:
          70% — max semantic similarity among prototypes tagged with that category
          30% — binary regex hit (1.0 if any pattern fires, 0.0 otherwise)
        """
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

        # procedural_bias has no regex; semantic only
        pb_sims = dim_semantic.get("procedural_bias", [0.0])
        scores["procedural_bias"] = min(1.0, 0.70 * max(pb_sims))
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


    def _score_with_patterns(
        self,
        text: str,
        lens_id: str,
        regex_patterns: list[str],
        language: str,
        dimension_keys: list[str],
    ) -> LensScore:
        """
        Generic scoring helper for lenses that follow the same structure:
        - Run compiled regex patterns on the text
        - Call PrototypeStore for semantic scoring if use_semantic=True
        - Return a LensScore with appropriate fields

        Used by IndigenousLens, BuddhistLens, HinduLens.
        """
        import re
        from ethiviz.embeddings.prototype_store import PrototypeStore

        # Semantic detection
        all_sim: dict[str, float] = {}
        if self.use_semantic:
            all_sim = self.detector.detect(text, lens_id, language=language)

        # Map prototype IDs to categories
        store = PrototypeStore()
        prototypes = store.load(lens_id)
        id_to_category = {p["id"]: p["category"] for p in prototypes}

        # Build dimension semantic scores
        dim_semantic: dict[str, list[float]] = {d: [] for d in dimension_keys}
        for proto_id, sim in all_sim.items():
            cat = id_to_category.get(proto_id, "")
            if cat in dim_semantic:
                dim_semantic[cat].append(sim)

        # Compile regex patterns
        compiled_patterns = [re.compile(pat, re.I) for pat in regex_patterns]

        # Compute dimension scores (70% semantic, 30% regex)
        scores: dict[str, float] = {}
        # Distribute regex hits evenly across dimensions
        regex_hit = 1.0 if any(p.search(text) for p in compiled_patterns) else 0.0
        for dim in dimension_keys:
            sem_list = dim_semantic.get(dim, [])
            sem = max(sem_list) if sem_list else 0.0
            scores[dim] = min(1.0, (0.70 * sem) + (0.30 * regex_hit))

        # Equal weights across dimensions if not otherwise specified
        n_dims = len(dimension_keys)
        dim_weight = 1.0 / n_dims if n_dims > 0 else 1.0
        overall = min(1.0, sum(scores.get(d, 0.0) * dim_weight for d in dimension_keys))

        # Bootstrap CI
        ci = self._bootstrap_ci(list(scores.values()))

        flagged = [proto_id for proto_id, s in all_sim.items() if s > 0.55]
        recs: list[str] = []
        if overall > 0.5:
            recs.append(f"High bias detected under {lens_id} lens. Review flagged dimensions.")
        elif overall > 0.3:
            recs.append(f"Moderate bias detected under {lens_id} lens.")

        return LensScore(
            lens_id=lens_id,
            overall_score=overall,
            calibrated_score=None,
            dimension_scores=scores,
            flagged_items=flagged,
            recommendations=recs,
            confidence=0.88 if self.use_semantic else 0.55,
            confidence_interval_95=ci,
            bootstrap_n=200,
            raw_evidence={"input_text": text, "semantic_scores": all_sim},
            semantic_similarity_scores=all_sim,
            language_detected=language,
        )


class TransformerUpgrade:
    """Stub for future Transformer-based upgrade."""
    pass
