from __future__ import annotations
import re
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

_AHIMSA_PATTERNS = [
    re.compile(r"\b(?:eliminate|destroy|exterminate|wipe\s+out)\b.*\b(?:people|group|community|"
               r"culture|population)\b", re.I),
    re.compile(r"\bit'?s?\s+(?:fine|acceptable|okay)\s+to\s+harm\s+(?:animals?|the\s+weak)\b", re.I),
    re.compile(r"\b(?:violence|cruelty)\s+(?:is\s+)?(?:justified|warranted|necessary)\s+"
               r"(?:against|to\s+control)\b", re.I),
]
_RIGHT_SPEECH_PATTERNS = [
    re.compile(r"\b(?:inferior|worthless|subhuman)\b.*\b(?:race|ethnicity|religion|group|culture)"
               r"\b", re.I),
    re.compile(r"\b(?:their|this)\s+culture\s+contributes?\s+nothing\b", re.I),
    re.compile(r"\bwomen\s+are\s+(?:naturally\s+)?(?:deceitful|untrustworthy|unfit)\s+"
               r"(?:in|for)\s+leadership\b", re.I),
]
_INTERDEPENDENCE_PATTERNS = [
    re.compile(r"\bindividual\s+success\s+has\s+nothing\s+to\s+do\s+with\s+(?:social\s+conditions?"
               r"|other\s+people|community)\b", re.I),
    re.compile(r"\b(?:not\s+our\s+concern|none\s+of\s+our\s+business)\b.*\b(?:distant|other\s+"
               r"places?|elsewhere)\b", re.I),
    re.compile(r"\bself.?made\b.*\b(?:alone|by\s+yourself|no\s+one\s+helped)\b", re.I),
]
_IDENTITY_REIFICATION_PATTERNS = [
    re.compile(r"\b(?:inherently|naturally|genetically)\b.*\b(?:violent|criminal|lazy|inferior)"
               r"\b", re.I),
    re.compile(r"\b(?:always|will\s+always)\s+be\s+(?:criminal|violent|lesser)\b.*\bblood\b", re.I),
    re.compile(r"\bcannot\s+change\s+(?:their|its)\s+(?:nature|essence)\b", re.I),
]
_COMPASSION_DEFICIT_PATTERNS = [
    re.compile(r"\btheir\s+own\s+fault\b|\bdeserve(?:s)?\s+to\s+suffer\b|\bno\s+sympathy\b", re.I),
    re.compile(r"\b(?:homeless|refugees?|poor|disabled)\s+(?:are|were)\s+(?:lazy\s+)?failures?\b",
               re.I),
    re.compile(r"\bchose\s+(?:their\s+own\s+)?suffering\b", re.I),
]

_CATEGORY_PATTERNS = {
    "ahimsa_violation": _AHIMSA_PATTERNS,
    "right_speech_violation": _RIGHT_SPEECH_PATTERNS,
    "interdependence_denial": _INTERDEPENDENCE_PATTERNS,
    "identity_reification": _IDENTITY_REIFICATION_PATTERNS,
    "compassion_deficit": _COMPASSION_DEFICIT_PATTERNS,
}


class BuddhistLens(EthicalLens):
    """
    Buddhist Ethical Lens (v1) — ahimsa (non-harm), right speech, interdependence
    (pratītyasamutpāda), and non-attachment to fixed identity categories.
    """

    def __init__(self, use_semantic: bool = True) -> None:
        super().__init__("buddhist_v1", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        self._dim_weights = {
            "ahimsa_violation": 0.30,
            "identity_reification": 0.25,
            "right_speech_violation": 0.20,
            "compassion_deficit": 0.15,
            "interdependence_denial": 0.10,
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
        if dim_scores.get("ahimsa_violation", 0) > 0.5:
            recs.append("Text may condone harm; review against the ahimsa (non-harm) principle.")
        if dim_scores.get("identity_reification", 0) > 0.5:
            recs.append("Check for language that treats identity categories as fixed, essential traits.")
        if dim_scores.get("compassion_deficit", 0) > 0.5:
            recs.append("Review for language that denies compassion to those who suffer.")

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


