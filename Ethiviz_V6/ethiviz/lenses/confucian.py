from __future__ import annotations
import re
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

_HIER_PATTERNS = [
    re.compile(r"\b(?:elders?|seniors?|older\s+workers?)\s+(?:should|must|ought\s+to)\s+"
               r"(?:defer|step\s+aside|give\s+way|be\s+replaced)\b", re.I),
    re.compile(r"\b(?:challenging|questioning|defying)\s+(?:authority|superiors?|management)\s+"
               r"(?:is\s+)?(?:disrespectful|wrong|unacceptable|immoral)\b", re.I),
    re.compile(r"\b(?:troublemakers?|agitators?|rabble-rousers?)\s+who\s+"
               r"(?:question|challenge|undermine)\b", re.I),
]
_COLL_HARM_PATTERNS = [
    re.compile(r"\b(?:individual\s+(?:conscience|rights?|opinion))\s+must\s+"
               r"(?:be\s+)?(?:suppressed?|silenced?|overridden?|subordinated?)\b", re.I),
    re.compile(r"\bwhistleblowers?\s+(?:destroy|undermine|harm|damage)\s+"
               r"(?:harmony|stability|order)\b", re.I),
    re.compile(r"\bconformity\s+(?:at\s+all\s+costs?|over\s+truth|over\s+ethics?)\b", re.I),
]
_FACE_PATTERNS = [
    re.compile(r"\b(?:publicly\s+(?:shame|humiliate|embarrass)|shame\s+(?:asian|chinese|japanese"
               r"|korean))\b", re.I),
    re.compile(r"\basian\s+(?:workers?|employees?|people)\s+(?:are\s+)?(?:too\s+)?(?:submissive|passive"
               r"|obedient|docile)\b", re.I),
    re.compile(r"\b(?:can'?t|cannot|unable\s+to)\s+(?:lead|make\s+decisions?|speak\s+up)\s+"
               r"because\s+(?:they\s+are\s+)?(?:asian|chinese|japanese|korean)\b", re.I),
]
_REL_PATTERNS = [
    re.compile(r"\b(?:east\s+asian|chinese|japanese|korean)\s+(?:cultures?|people|societies?)\s+"
               r"(?:are\s+)?(?:incapable|unable|cannot)\s+(?:of\s+)?(?:innovation|creativity|"
               r"original\s+thought)\b", re.I),
    re.compile(r"\b(?:confucian|asian)\s+(?:cultures?|societies?)\s+(?:suppress|oppress|trap)"
               r"\s+women\b", re.I),
    re.compile(r"\bmonolithic\b.*\b(?:asian|chinese|confucian)\b", re.I),
]

_CATEGORY_PATTERNS = {
    "hierarchical_disrespect": _HIER_PATTERNS,
    "collectivist_harm": _COLL_HARM_PATTERNS,
    "face_violation": _FACE_PATTERNS,
    "relational_bias": _REL_PATTERNS,
}


class ConfucianLens(EthicalLens):
    """Confucian Ethical Lens (v2) — ren, li, yi, face, relational propriety."""

    def __init__(self, use_semantic: bool = True) -> None:
        super().__init__("confucian_v2", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        self._dim_weights = {
            "hierarchical_disrespect": 0.25,
            "collectivist_harm": 0.25,
            "face_violation": 0.30,
            "relational_bias": 0.20,
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
        if dim_scores.get("face_violation", 0) > 0.5:
            recs.append("Text may violate face (mianzi); review for public shaming language.")
        if dim_scores.get("relational_bias", 0) > 0.5:
            recs.append("Check for stereotyping of East Asian cultures as monolithic.")
        if dim_scores.get("collectivist_harm", 0) > 0.5:
            recs.append("Review for language that weaponises harmony to silence dissent.")

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




class OntologyUpgrade:
    """Stub for future Ontology-based upgrade."""
    pass
