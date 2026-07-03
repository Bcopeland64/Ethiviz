from __future__ import annotations
import re
import numpy as np
from typing import Any
from ethiviz.lenses.base import EthicalLens, LensScore
from ethiviz.embeddings.semantic_detector import SemanticBiasDetector

_VIOLENT_STEREO_PATTERNS = [
    re.compile(r"\b(?:all|every|most)\s+muslims?\s+(?:are|support|endorse|believe\s+in)\s+"
               r"(?:terrorism|violence|extremism|jihad)\b", re.I),
    re.compile(r"\bislam\s+(?:is\s+a\s+)?(?:religion\s+of\s+)?(?:violence|terror|hatred|war)\b",
               re.I),
    re.compile(r"\bmuslims?\s+(?:should\s+be\s+banned|are\s+a\s+(?:security\s+)?threat|"
               r"can'?t\s+be\s+trusted)\b", re.I),
    re.compile(r"\b(?:islamic|muslim)\s+(?:terrorism|extremism|fundamentalism)\s+"
               r"(?:is\s+)?(?:inherent|inevitable|natural|normal)\b", re.I),
]
_ESSEN_PATTERNS = [
    re.compile(r"\b(?:islamic\s+world|muslim\s+countries?|arab\s+world)\s+"
               r"(?:is\s+)?(?:incompatible|opposed|hostile)\s+(?:with|to)\s+"
               r"(?:democracy|modernity|freedom|human\s+rights?)\b", re.I),
    re.compile(r"\bmuslims?\s+(?:can'?t|cannot|will\s+never)\s+be\s+(?:truly\s+)?loyal\b", re.I),
    re.compile(r"\ball\s+(?:islamic|muslim)\s+(?:societies?|cultures?|nations?)\s+are\s+"
               r"(?:the\s+same|monolithic|identical)\b", re.I),
]
_GENDER_ESSEN_PATTERNS = [
    re.compile(r"\bmuslim\s+women?\s+who\s+(?:don'?t|do\s+not)\s+wear\s+(?:the\s+)?(?:hijab|"
               r"veil|niqab)\s+(?:are\s+)?(?:immoral|sinful|bad)\b", re.I),
    re.compile(r"\bislam\s+(?:inherently|always|fundamentally)\s+(?:oppresses?|subjugates?|"
               r"enslaves?)\s+women\b", re.I),
    re.compile(r"\bmuslim\s+women?\s+(?:can'?t|cannot|are\s+not\s+allowed\s+to)\s+"
               r"(?:be\s+liberated|have\s+freedom|make\s+choices?)\b", re.I),
]
_ORIENT_PATTERNS = [
    re.compile(r"\b(?:middle\s+eastern|arab|muslim)\s+(?:people|men|women|societies?)\s+"
               r"(?:are\s+)?(?:irrational|emotional|barbaric|backwards?|uncivilized)\b", re.I),
    re.compile(r"\b(?:arab|muslim|islamic)\s+(?:culture|world|society)\s+(?:is\s+)?"
               r"(?:exotic|mysterious|backward|primitive|needs?\s+(?:to\s+be\s+)?saved?)\b", re.I),
    re.compile(r"\bneeds?\s+western\s+(?:civilization|values?|intervention)\s+to\s+"
               r"(?:modernize|civilize|fix|help)\b", re.I),
]
_DIGNITY_PATTERNS = [
    re.compile(r"\b(?:certain\s+)?(?:groups?|people|individuals?)\s+(?:are\s+)?(?:inherently|"
               r"naturally|by\s+(?:nature|design))\s+less\s+(?:dignified|worthy|human)\b", re.I),
    re.compile(r"\b(?:non-muslims?|infidels?|kuffar)\s+(?:are\s+)?(?:inferior|subhuman|unworthy"
               r"|filthy)\b", re.I),
]

_CATEGORY_PATTERNS = {
    "violent_stereotyping": _VIOLENT_STEREO_PATTERNS,
    "islamic_essentialism": _ESSEN_PATTERNS,
    "gender_essentialism": _GENDER_ESSEN_PATTERNS,
    "orientalism": _ORIENT_PATTERNS,
    "dignity_violation": _DIGNITY_PATTERNS,
}


class IslamicLens(EthicalLens):
    """Islamic Ethical Lens (v1) — maqasid al-shari'ah, karamah, anti-orientalism."""

    def __init__(self, use_semantic: bool = True) -> None:
        super().__init__("islamic_v1", use_semantic=use_semantic)
        self.detector = SemanticBiasDetector()
        self._dim_weights = {
            "violent_stereotyping": 0.30,
            "islamic_essentialism": 0.25,
            "gender_essentialism": 0.20,
            "orientalism": 0.15,
            "dignity_violation": 0.10,
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
        if dim_scores.get("violent_stereotyping", 0) > 0.5:
            recs.append("Text may contain violent stereotyping of Muslim communities.")
        if dim_scores.get("orientalism", 0) > 0.5:
            recs.append("Review for Orientalist framing that exoticises or infantilises Middle Eastern cultures.")
        if dim_scores.get("dignity_violation", 0) > 0.5:
            recs.append("Check for language that violates karamah (innate human dignity).")

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


class ClassifierUpgrade:
    """Stub for future Classifier-based upgrade."""
    pass
