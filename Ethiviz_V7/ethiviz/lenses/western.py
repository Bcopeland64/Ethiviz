from __future__ import annotations
import re
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

        # procedural_bias has no regex patterns of its own; _score_dimensions
        # scores it from the semantic channel alone via the empty pattern list.
        dim_scores, coverage = self._score_dimensions(
            input_data, all_sim, _CATEGORY_PATTERNS,
            list(self._dim_weights), language=language,
        )

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
            confidence=self._confidence_for(coverage),
            confidence_interval_95=ci,
            bootstrap_n=200,
            raw_evidence={"input_text": input_data, "semantic_scores": all_sim},
            semantic_similarity_scores=all_sim,
            language_detected=language,
            analysis_coverage=coverage.coverage,
            warnings=coverage.warnings(),
        )


class TransformerUpgrade:
    """Stub for future Transformer-based upgrade."""
    pass
