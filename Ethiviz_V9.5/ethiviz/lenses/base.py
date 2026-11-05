# ethiviz/lenses/base.py
from __future__ import annotations
import re
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Cues that a matched stereotype/deficit phrase is being quoted in order to
# refute it, not asserted — "the myth that African cultures are primitive"
# or "challenged the idea that X" must not score the same as asserting X.
# This is a heuristic, not a real negation parser: it only checks for a cue
# word anywhere earlier in the text, so it can still be fooled by a debunking
# clause placed after the stereotype ("African cultures are primitive — a
# claim historians have thoroughly debunked"). It measurably reduces the most
# common false-positive shape (quote-then-refute) without the cost of a full
# NLP negation/scope parser.
_NEGATION_CUES = re.compile(
    r"\b(?:myth|misconception|stereotype|false\s+claim|not\s+true|isn'?t\s+true|"
    r"challenged?\s+the|debunk(?:ed|s|ing)?|no\s+evidence\s+that|"
    r"contrary\s+to\s+the\s+claim|refute[sd]?|disprove[sd]?)\b",
    re.I,
)

def pattern_hit(text: str, patterns: list[re.Pattern]) -> bool:
    """True if any pattern matches text and isn't preceded by a debunking cue."""
    for p in patterns:
        m = p.search(text)
        if m and not _NEGATION_CUES.search(text[: m.start()]):
            return True
    return False

# Blend of the two detection channels when both are available for a language.
SEMANTIC_WEIGHT = 0.70
REGEX_WEIGHT = 0.30

# Every lens's regex pattern set is authored in English. For any other
# language the lexical channel simply cannot fire, so scoring it as 0.0 would
# subtract a fixed 30% from every non-English result — a structural, silent
# penalty that reads as "less biased" rather than "less measurable". Where the
# lexical channel is unavailable the semantic channel is renormalised to full
# weight and the loss of corroboration is reported via CoverageReport instead.
REGEX_LANGUAGES = frozenset({"en"})

# Confidence ceilings, applied multiplicatively against measurement coverage.
SEMANTIC_CONFIDENCE = 0.88
LEXICAL_ONLY_CONFIDENCE = 0.55


@dataclass
class CoverageReport:
    """
    How much of a lens's detection machinery actually applied to this input.

    Both detection channels are language-dependent: prototypes need a
    translation in the input language to be compared meaningfully, and the
    regex channel exists only in English. This records what was genuinely
    available so a degraded analysis is reported as degraded rather than as a
    confident low score.
    """
    language: str
    regex_available: bool
    translated_prototypes: int
    total_prototypes: int
    semantic_enabled: bool = True

    @property
    def translation_ratio(self) -> float:
        if self.total_prototypes <= 0:
            return 0.0
        return self.translated_prototypes / self.total_prototypes

    @property
    def coverage(self) -> float:
        """
        Fraction of the lens's detection capability that applied here, in
        [0, 1], weighted by each channel's contribution to the blended score
        and renormalised over the channels that were actually enabled.
        """
        semantic_w = SEMANTIC_WEIGHT if self.semantic_enabled else 0.0
        lexical_w = REGEX_WEIGHT
        total_w = semantic_w + lexical_w
        if total_w <= 0:
            return 0.0

        achieved = semantic_w * self.translation_ratio
        achieved += lexical_w * (1.0 if self.regex_available else 0.0)
        return achieved / total_w

    def warnings(self) -> list[str]:
        """Human-readable degradation notices, empty when coverage is full."""
        out: list[str] = []
        if not self.regex_available:
            out.append(
                f"Lexical (regex) detection is unavailable for language "
                f"'{self.language}' — patterns are authored in English only. "
                f"Scoring used semantic similarity alone."
            )
        missing = self.total_prototypes - self.translated_prototypes
        if missing > 0 and self.semantic_enabled:
            out.append(
                f"{missing} of {self.total_prototypes} prototypes lack a "
                f"'{self.language}' translation and fell back to their English "
                f"text, which is compared against non-English input and is "
                f"unreliable. Treat this score as a lower bound."
            )
        return out


def blend_scores(semantic: float, regex_hit: float, regex_available: bool) -> float:
    """
    Combine the semantic and lexical channels into one dimension score.
    When the lexical channel is unavailable the semantic channel takes full
    weight, so a non-English input is not silently penalised for the absence
    of English-only patterns.
    """
    if not regex_available:
        return min(1.0, semantic)
    return min(1.0, (SEMANTIC_WEIGHT * semantic) + (REGEX_WEIGHT * regex_hit))


@dataclass
class LensScore:
    lens_id: str
    overall_score: float
    calibrated_score: float | None          # Upgrade 9 — None until calibrator fitted
    dimension_scores: dict[str, float]
    flagged_items: list[str]
    recommendations: list[str]
    confidence: float
    confidence_interval_95: tuple[float, float]
    bootstrap_n: int
    raw_evidence: dict[str, Any]
    token_attributions: list[tuple[str, float]] = field(default_factory=list)
    semantic_similarity_scores: dict[str, float] = field(default_factory=dict)
    language_detected: str = "en"           # Upgrade 11 — ISO 639-1 code
    prototype_version_hash: str = ""        # Upgrade 19 — hash of prototype YAML used
    analysis_coverage: float = 1.0          # Phase 2 — fraction of machinery that applied
    warnings: list[str] = field(default_factory=list)   # Phase 2 — degradation notices

class EthicalLens(ABC):
    """Base class for all ethical lenses (Western, Ubuntu, etc.)."""

    def __init__(self, lens_id: str, use_semantic: bool = True) -> None:
        self.lens_id = lens_id
        self.use_semantic = use_semantic

    @abstractmethod
    def score(self, input_data: Any, **kwargs: Any) -> LensScore:
        """Score input data through this ethical lens."""
        pass

    # ------------------------------------------------------------------
    # Shared scoring machinery
    # ------------------------------------------------------------------

    def _load_prototype_index(
        self, language: str
    ) -> tuple[dict[str, str], dict[str, float], CoverageReport]:
        """
        Load this lens's prototypes for `language` and return
        (id->category, id->severity, coverage). Coverage records how many
        prototypes had a real translation versus falling back to English.
        """
        from ethiviz.embeddings.prototype_store import PrototypeStore

        prototypes = PrototypeStore().load(self.lens_id, language=language)
        id_to_category = {p["id"]: p["category"] for p in prototypes}
        id_to_severity = {p["id"]: p["severity"] for p in prototypes}

        translated = sum(1 for p in prototypes if p.get("language") == language)
        coverage = CoverageReport(
            language=language,
            regex_available=language in REGEX_LANGUAGES,
            translated_prototypes=translated,
            total_prototypes=len(prototypes),
            semantic_enabled=self.use_semantic,
        )
        return id_to_category, id_to_severity, coverage

    def _score_dimensions(
        self,
        text: str,
        all_sim: dict[str, float],
        category_patterns: dict[str, list[re.Pattern]],
        dim_keys: list[str],
        language: str = "en",
    ) -> tuple[dict[str, float], CoverageReport]:
        """
        Compute per-dimension scores by blending severity-weighted semantic
        similarity with the lexical (regex) channel.

        Shared by every lens: each supplies its own category->patterns map and
        dimension list, so the blending, severity weighting, negation guarding
        and language-coverage logic live in exactly one place.
        """
        id_to_category, id_to_severity, coverage = self._load_prototype_index(language)

        dim_semantic: dict[str, list[float]] = {d: [] for d in dim_keys}
        for proto_id, sim in all_sim.items():
            cat = id_to_category.get(proto_id, "")
            if cat in dim_semantic:
                dim_semantic[cat].append(sim * id_to_severity.get(proto_id, 1.0))

        scores: dict[str, float] = {}
        for dim in dim_keys:
            sem = max(dim_semantic.get(dim) or [0.0])
            patterns = category_patterns.get(dim, [])
            regex_hit = 1.0 if (patterns and pattern_hit(text, patterns)) else 0.0
            scores[dim] = blend_scores(sem, regex_hit, coverage.regex_available)

        return scores, coverage

    @staticmethod
    def _bootstrap_ci(
        values: list[float], n: int = 200, seed: int = 42
    ) -> tuple[float, float]:
        """Percentile bootstrap 95% CI over the dimension scores."""
        if not values:
            return (0.0, 0.0)
        arr = np.array(values, dtype=float)
        rng = np.random.default_rng(seed)
        means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n)]
        return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))

    def _confidence_for(self, coverage: CoverageReport) -> float:
        """
        Base confidence for this lens, attenuated by how much of its detection
        machinery actually applied. A semantic-enabled English run keeps the
        full ceiling; a run where prototypes are untranslated and the regex
        channel is unavailable scales down toward zero rather than reporting a
        confident-looking score built on nothing.
        """
        base = SEMANTIC_CONFIDENCE if self.use_semantic else LEXICAL_ONLY_CONFIDENCE
        return round(base * coverage.coverage, 4)
