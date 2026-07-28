from __future__ import annotations
import re
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

_LAND_RELATIONAL_PATTERNS = [
    re.compile(r"\bland\s+is\s+just\s+a\s+resource\b.*\b(?:extract|maximum\s+economic\s+value)"
               r"\b", re.I),
    # Requires a reductive "only/no value except" claim, not bare mention of
    # extraction verbs — "sustainably harvest timber from the forest" or
    # "licensed to harvest under environmental review" must not match.
    re.compile(r"\b(?:only|just|merely)\s+(?:a\s+)?(?:resource|commodity)\s+to\s+be\s+"
               r"(?:extracted|exploited|mined)\b", re.I),
    re.compile(r"\b(?:land|forests?|territor(?:y|ies))\b.*\bno\s+value\s+except\s+as\b", re.I),
]
_KNOWLEDGE_EXTRACTION_PATTERNS = [
    re.compile(r"\b(?:use|take)\s+indigenous\s+knowledge\s+without\s+(?:asking\s+)?permission\b",
               re.I),
    # Requires explicit lack of consent/credit — "communities can now patent
    # and own their own traditional knowledge" (a protective outcome) must
    # not match just because "patent"/"own" co-occurs with the phrase.
    re.compile(r"\btraditional\s+knowledge\b.*\bwithout\b.{0,20}\b(?:permission|consent|"
               r"credit|compensation)\b", re.I),
    re.compile(r"\btraditional\s+healing\s+practices?\s+should\s+be\s+patented\b", re.I),
]
_CULTURAL_ERASURE_PATTERNS = [
    # Requires the dismissive claim itself, not bare mention that something
    # is disappearing — "languages are disappearing, so we funded
    # revitalization efforts" must not match.
    re.compile(r"\b(?:dying\s+out|disappearing|extinct)\b.*\bno\s+need\s+to\s+preserve\b|"
               r"\bno\s+need\s+to\s+preserve\b.*\b(?:dying\s+out|disappearing|extinct)\b", re.I),
    re.compile(r"\bno\s+need\s+to\s+preserve\b", re.I),
    re.compile(r"\b(?:ceremonies?|spiritual\s+practices?)\s+are\s+primitive\s+superstitions?\b",
               re.I),
]
_SEVEN_GENERATIONS_PATTERNS = [
    re.compile(r"\bonly\s+consider\s+immediate\s+profits?\b.*\b(?:not|without)\b.*\bfuture\s+"
               r"generations?\b", re.I),
    # Requires a reductive "only/just" claim — "balances profit with
    # protecting the environment for future generations" must not match.
    re.compile(r"\b(?:only|just)\s+(?:immediate|short-?term)\s+profits?\s+matter\b", re.I),
    re.compile(r"\bfuture\s+generations?\s+will\s+find\s+solutions?\b", re.I),
]
_STEREOTYPING_PATTERNS = [
    re.compile(r"\ball\s+indigenous\s+people\s+live\s+in\s+traditional\s+villages?\b", re.I),
    re.compile(r"\b(?:primitive|savage|uncivilized|backward)\b.*\b(?:indigenous|native|tribal|"
               r"aboriginal)\b", re.I),
    re.compile(r"\bnaturally\s+less\s+capable\s+of\s+managing\s+modern\b", re.I),
]

_CATEGORY_PATTERNS = {
    "land_relational_harm": _LAND_RELATIONAL_PATTERNS,
    "knowledge_extraction": _KNOWLEDGE_EXTRACTION_PATTERNS,
    "cultural_erasure": _CULTURAL_ERASURE_PATTERNS,
    "seven_generations_violation": _SEVEN_GENERATIONS_PATTERNS,
    "stereotyping": _STEREOTYPING_PATTERNS,
}


class IndigenousLens(EthicalLens):
    """
    Indigenous / First Nations Ethical Lens (v1) — land-relational ethics, the
    seven-generations principle, CARE Principles, and FNIGC protocols for
    collective data stewardship. Weights knowledge extraction and land-relational
    harm most heavily, reflecting the tradition's central concern with
    unconsented appropriation of land and knowledge.
    """

    def __init__(self, use_semantic: bool = True) -> None:
        super().__init__("indigenous_v1", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        self._dim_weights = {
            "knowledge_extraction": 0.25,
            "land_relational_harm": 0.25,
            "cultural_erasure": 0.20,
            "seven_generations_violation": 0.15,
            "stereotyping": 0.15,
        }

    def score(self, input_data: str, language: str = "en", **kwargs: Any) -> LensScore:
        all_sim: dict[str, float] = {}
        if self.use_semantic:
            all_sim = self.detector.detect(input_data, self.lens_id, language=language)

        dim_scores, coverage = self._score_dimensions(
            input_data, all_sim, _CATEGORY_PATTERNS,
            list(self._dim_weights), language=language,
        )
        overall = min(1.0, sum(dim_scores.get(d, 0.0) * w for d, w in self._dim_weights.items()))
        ci = self._bootstrap_ci(list(dim_scores.values()))

        flagged = [pid for pid, s in all_sim.items() if s > 0.55]
        recs: list[str] = []
        if dim_scores.get("knowledge_extraction", 0) > 0.5:
            recs.append("Text may describe using traditional knowledge without consent or credit; review against CARE Principles.")
        if dim_scores.get("land_relational_harm", 0) > 0.5:
            recs.append("Check for framing that reduces land to a purely extractive resource.")
        if dim_scores.get("seven_generations_violation", 0) > 0.5:
            recs.append("Review for reasoning that discounts impacts on future generations.")

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


