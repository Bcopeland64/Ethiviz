from __future__ import annotations
import re
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

_AHIMSA_PATTERNS = [
    re.compile(r"\bviolence\b.*\b(?:minority|community|religious|dalit)\b.*\b(?:justified|"
               r"warranted|necessary)\b", re.I),
    re.compile(r"\b(?:aggressive\s+tactics?|force)\s+to\s+drive\s+out\b", re.I),
    # Requires an incitement framing — "police vowed to prevent any attack on
    # religious minorities" or "punish those who harm minorities" (protective
    # statements) must not match a bare "attack/harm ... minority" co-occurrence.
    re.compile(r"\b(?:should|must|need\s+to|let'?s)\s+(?:attack|harm)\b.*\b(?:religious\s+"
               r"minorit(?:y|ies)|neighbou?rhood)\b", re.I),
]
_SATYA_PATTERNS = [
    re.compile(r"\ball\s+(?:people|members?)\s+(?:from|of)\s+this\s+(?:religious\s+)?community\s+"
               r"are\s+(?:terrorists?|criminals?)\b", re.I),
    re.compile(r"\b(?:every|all)\b.*\b(?:muslim|hindu|christian|sikh)s?\b.*\b(?:terrorist|"
               r"criminal|corrupt)\b", re.I),
    re.compile(r"\bwomen\s+from\s+this\s+community\s+are\s+all\s+submissive\b", re.I),
]
_DHARMIC_DISRESPECT_PATTERNS = [
    re.compile(r"\b(?:superstition|nonsense|primitive|wasteful)\b.*\b(?:ritual|prayer|worship|"
               r"dharma|performances?)\b", re.I),
    re.compile(r"\breligious\s+practices?\s+(?:are|is)\s+superstitious\s+nonsense\b", re.I),
    re.compile(r"\bno\s+(?:moral|spiritual)\s+(?:value|significance)\b.*\bpractices?\b", re.I),
]
_DIGNITY_HARM_PATTERNS = [
    re.compile(r"\b(?:low\s+social\s+status|dalits?)\b.*\b(?:less\s+than\s+human|polluted|"
               r"impure)\b", re.I),
    re.compile(r"\bshould\s+not\s+mix\s+with\s+upper\s+castes?\b", re.I),
    re.compile(r"\bdeserve(?:s)?\s+to\s+be\s+treated\s+as\s+less\s+than\s+human\b", re.I),
]
_CASTE_ESSENTIALISM_PATTERNS = [
    re.compile(r"\bcaste\b.*\b(?:determines|decides|fixes)\b.*\b(?:intelligence|ability|"
               r"capability|destiny)\b", re.I),
    re.compile(r"\b(?:certain\s+)?castes?\s+are\s+genetically\s+inferior\b", re.I),
    re.compile(r"\bcannot\s+be\s+overcome\b.*\bcaste\b", re.I),
]

_CATEGORY_PATTERNS = {
    "ahimsa_violation": _AHIMSA_PATTERNS,
    "satya_violation": _SATYA_PATTERNS,
    "dharmic_disrespect": _DHARMIC_DISRESPECT_PATTERNS,
    "dignity_harm": _DIGNITY_HARM_PATTERNS,
    "caste_essentialism": _CASTE_ESSENTIALISM_PATTERNS,
}


class HinduLens(EthicalLens):
    """
    Hindu / Dharmic Ethical Lens (v1) — dharmic duty, ahimsa, satya (truthfulness),
    and manava mahatma (human dignity), drawing on dharmashastra tradition and
    contemporary Hindu ethics scholarship. Weights caste-based essentialism and
    dignity harm most heavily, reflecting caste discrimination as a distinct and
    especially severe axis within this tradition.
    """

    def __init__(self, use_semantic: bool = True) -> None:
        super().__init__("hindu_v1", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        self._dim_weights = {
            "caste_essentialism": 0.25,
            "dignity_harm": 0.25,
            "ahimsa_violation": 0.20,
            "satya_violation": 0.20,
            "dharmic_disrespect": 0.10,
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
        if dim_scores.get("caste_essentialism", 0) > 0.5:
            recs.append("Text may treat caste as determining ability or worth; review for caste essentialism.")
        if dim_scores.get("dignity_harm", 0) > 0.5:
            recs.append("Check for language denying manava mahatma (inherent human dignity) to a group.")
        if dim_scores.get("ahimsa_violation", 0) > 0.5:
            recs.append("Text may condone violence toward a religious or communal minority; review against ahimsa.")

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


