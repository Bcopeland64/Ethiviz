# ethiviz/frameworks/dimension_map.py
"""
Dimension-level cross-cultural reasoning.

Conflict detection (`frameworks/conflict.py`) and synergy amplification
(`scoring/multi_framework.py`) both compare one scalar per lens. That collapses
each tradition's internal structure: two lenses can land on the same overall
score for entirely different reasons, and a lens that uniquely detects a harm
looks identical to one that detected nothing in particular.

This module works one level down. Several traditions independently encode the
same underlying moral construct under different names — Islamic
`dignity_violation` and Hindu `dignity_harm` are both denials of inherent human
worth; Buddhist and Hindu ethics both name `ahimsa_violation` outright. Reading
those dimensions together answers two questions the scalar view cannot:

  * Convergence — do the traditions that actually encode this construct agree
    that it is present? Agreement across independently-authored traditions is
    much stronger evidence than one lens scoring high.
  * Distinctive concern — is a harm visible through only one tradition, while
    the others that measure the same construct see nothing? That asymmetry is
    the most culturally informative signal the platform can produce, and the
    scalar view discards it entirely.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

# Score at or above which a dimension counts as flagging its construct.
FLAG_THRESHOLD = 0.50
# Spread (max - min) below which the traditions are treated as agreeing.
CONSENSUS_SPREAD = 0.25
# Gap a lone flagging lens must open over the next-highest lens for its
# reading to count as a tradition-distinctive concern rather than noise.
DISTINCTIVE_GAP = 0.30


@dataclass(frozen=True)
class MoralConstruct:
    """A concern several ethical traditions encode under different names."""
    construct_id: str
    description: str
    # lens_id -> that lens's dimension expressing this construct
    lens_dimensions: Dict[str, str]


# Each mapping below pairs dimensions that express the same underlying concern.
# Only correspondences with a defensible basis are declared: either the
# traditions use the same term (ahimsa), or the dimensions were authored to
# detect the same harm. Where a concern is genuinely particular to one
# tradition it is declared with a single lens rather than being forced into a
# cross-tradition grouping — a construct only one tradition encodes is a real
# finding, not a gap to paper over.
MORAL_CONSTRUCTS: List[MoralConstruct] = [
    MoralConstruct(
        construct_id="human_dignity",
        description="Denial of inherent, unconditional human worth.",
        lens_dimensions={
            "islamic_v1": "dignity_violation",     # karamah
            "hindu_v1": "dignity_harm",            # manava mahatma
            "ubuntu_v1": "ubuntu_violation",       # communal dignity
        },
    ),
    MoralConstruct(
        construct_id="essentialism",
        description=(
            "Treating a group identity as fixed, innate, and determinative of "
            "worth or capability."
        ),
        lens_dimensions={
            "ubuntu_v1": "african_essentialism",
            "hindu_v1": "caste_essentialism",
            "islamic_v1": "islamic_essentialism",
            "buddhist_v1": "identity_reification",
        },
    ),
    MoralConstruct(
        construct_id="non_harm",
        description=(
            "Condoning, inciting, or normalising violence against a group "
            "(ahimsa in the Buddhist and Hindu traditions)."
        ),
        lens_dimensions={
            "buddhist_v1": "ahimsa_violation",
            "hindu_v1": "ahimsa_violation",
            "islamic_v1": "violent_stereotyping",
        },
    ),
    MoralConstruct(
        construct_id="cultural_delegitimisation",
        description=(
            "Framing another culture's knowledge, practice, or belief as "
            "primitive, invalid, or in need of correction."
        ),
        lens_dimensions={
            "ubuntu_v1": "cultural_erasure",
            "indigenous_v1": "cultural_erasure",
            "hindu_v1": "dharmic_disrespect",
            "islamic_v1": "orientalism",
            "western_v1": "cultural_superiority",
        },
    ),
    MoralConstruct(
        construct_id="group_flattening",
        description="Reducing a diverse group to a single ascribed trait.",
        lens_dimensions={
            "western_v1": "stereotyping",
            "indigenous_v1": "stereotyping",
            "confucian_v2": "relational_bias",
        },
    ),
    MoralConstruct(
        construct_id="relational_obligation",
        description=(
            "Devaluing communal bonds, mutual dependence, or obligation to "
            "others as a source of moral claim."
        ),
        lens_dimensions={
            "ubuntu_v1": "community_devaluation",
            "confucian_v2": "collectivist_harm",
            "buddhist_v1": "interdependence_denial",
        },
    ),
    MoralConstruct(
        construct_id="gender_subordination",
        description="Casting gender as grounds for reduced standing or capability.",
        lens_dimensions={
            "western_v1": "gender_bias",
            "islamic_v1": "gender_essentialism",
        },
    ),
    MoralConstruct(
        construct_id="intergenerational_responsibility",
        description=(
            "Discounting obligation to future generations. Encoded explicitly "
            "only in the Indigenous seven-generations principle; no other lens "
            "in this set measures it."
        ),
        lens_dimensions={
            "indigenous_v1": "seven_generations_violation",
        },
    ),
    MoralConstruct(
        construct_id="knowledge_sovereignty",
        description=(
            "Appropriating a community's knowledge without consent, credit, or "
            "benefit. Encoded only by the Indigenous lens (CARE Principles)."
        ),
        lens_dimensions={
            "indigenous_v1": "knowledge_extraction",
        },
    ),
    MoralConstruct(
        construct_id="truthfulness",
        description=(
            "Asserting falsehoods about a group (satya in the Hindu tradition; "
            "right speech in the Buddhist tradition)."
        ),
        lens_dimensions={
            "hindu_v1": "satya_violation",
            "buddhist_v1": "right_speech_violation",
        },
    ),
]


@dataclass
class ConstructReading:
    """How the traditions that encode one construct read a given input."""
    construct_id: str
    description: str
    scores: Dict[str, float]              # lens_id -> dimension score
    contributing_lenses: List[str]        # lenses that actually reported
    mean_score: float
    spread: float                         # max - min across contributing lenses
    flagged_lenses: List[str]             # lenses at/above FLAG_THRESHOLD
    is_consensus: bool                    # multiple lenses agree it is present
    distinctive_lens: str | None          # sole tradition detecting this harm
    interpretation: str

    @property
    def is_tradition_specific(self) -> bool:
        return self.distinctive_lens is not None


class CrossCulturalDimensionMap:
    """
    Reads a set of LensScores at the dimension level and reports, per shared
    moral construct, whether the traditions converge and whether any harm is
    visible through only one of them.
    """

    def __init__(
        self,
        constructs: List[MoralConstruct] | None = None,
        flag_threshold: float = FLAG_THRESHOLD,
        consensus_spread: float = CONSENSUS_SPREAD,
        distinctive_gap: float = DISTINCTIVE_GAP,
    ) -> None:
        self.constructs = constructs or MORAL_CONSTRUCTS
        self.flag_threshold = flag_threshold
        self.consensus_spread = consensus_spread
        self.distinctive_gap = distinctive_gap

    def analyze(self, lens_dimension_scores: Dict[str, Dict[str, float]]) -> List[ConstructReading]:
        """
        `lens_dimension_scores` maps lens_id -> {dimension: score}, which is
        exactly the shape of LensScore.dimension_scores / FrameworkScore
        .dimension_scores. Lenses absent from the input are skipped, so this
        works on any subset of the seven.
        """
        readings: List[ConstructReading] = []

        for construct in self.constructs:
            scores: Dict[str, float] = {}
            for lens_id, dimension in construct.lens_dimensions.items():
                lens_dims = lens_dimension_scores.get(lens_id)
                if lens_dims is None or dimension not in lens_dims:
                    continue
                scores[lens_id] = float(lens_dims[dimension])

            if not scores:
                continue

            readings.append(self._build_reading(construct, scores))

        readings.sort(key=lambda r: r.mean_score, reverse=True)
        return readings

    def _build_reading(
        self, construct: MoralConstruct, scores: Dict[str, float]
    ) -> ConstructReading:
        values = list(scores.values())
        mean_score = sum(values) / len(values)
        spread = max(values) - min(values)
        flagged = sorted(l for l, s in scores.items() if s >= self.flag_threshold)

        distinctive = self._find_distinctive_lens(scores, flagged)
        is_consensus = len(flagged) > 1 and spread <= self.consensus_spread

        return ConstructReading(
            construct_id=construct.construct_id,
            description=construct.description,
            scores=scores,
            contributing_lenses=sorted(scores),
            mean_score=mean_score,
            spread=spread,
            flagged_lenses=flagged,
            is_consensus=is_consensus,
            distinctive_lens=distinctive,
            interpretation=self._interpret(
                construct, scores, flagged, distinctive, is_consensus
            ),
        )

    def _find_distinctive_lens(
        self, scores: Dict[str, float], flagged: List[str]
    ) -> str | None:
        """
        The sole tradition detecting a harm the others measuring the same
        construct do not. Requires a clear gap over the next-highest lens, so
        a marginal difference near the threshold is not reported as a
        tradition-specific insight.
        """
        if len(flagged) != 1 or len(scores) < 2:
            return None
        lens = flagged[0]
        others = [s for l, s in scores.items() if l != lens]
        if scores[lens] - max(others) >= self.distinctive_gap:
            return lens
        return None

    def _interpret(
        self,
        construct: MoralConstruct,
        scores: Dict[str, float],
        flagged: List[str],
        distinctive: str | None,
        is_consensus: bool,
    ) -> str:
        if distinctive:
            others = ", ".join(sorted(l for l in scores if l != distinctive))
            return (
                f"Detected only through {distinctive}: {construct.description} "
                f"The other traditions encoding this concern ({others}) do not "
                f"flag it, so this harm is visible only through that cultural "
                f"frame — review it there rather than treating the low "
                f"cross-lens average as absence."
            )
        if is_consensus:
            agree = ", ".join(flagged)
            return (
                f"Cross-tradition consensus ({agree}): {construct.description} "
                f"Independently-authored traditions agree, which is stronger "
                f"evidence than any single lens scoring high."
            )
        if flagged:
            return (
                f"Partial signal from {', '.join(flagged)}, but the traditions "
                f"encoding this construct disagree (spread "
                f"{max(scores.values()) - min(scores.values()):.2f}). Treat as "
                f"contested rather than established."
            )
        if len(scores) == 1:
            only = next(iter(scores))
            return (
                f"No signal. Note this construct is encoded only by {only}, so "
                f"absence here reflects one tradition's reading, not consensus."
            )
        return "No tradition encoding this construct flagged it."

    def tradition_specific_findings(
        self, readings: List[ConstructReading]
    ) -> List[ConstructReading]:
        """Readings where exactly one tradition detects the harm."""
        return [r for r in readings if r.is_tradition_specific]

    def consensus_findings(
        self, readings: List[ConstructReading]
    ) -> List[ConstructReading]:
        """Readings where multiple independent traditions agree."""
        return [r for r in readings if r.is_consensus]
