from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

class ConflictType(Enum):
    INDIVIDUAL_VS_COMMUNAL    = "individual_vs_communal"
    HIERARCHY_VS_EQUALITY     = "hierarchy_vs_equality"
    SECULAR_VS_SACRED         = "secular_vs_sacred"
    UNIVERSAL_VS_PARTICULAR   = "universal_vs_particular"
    ORIENTALISM_VS_AGENCY     = "orientalism_vs_agency"
    ESSENTIALISM_VS_DIVERSITY = "essentialism_vs_diversity"

class ResolutionStrategy(Enum):
    MAXIMIZE_CONSENSUS         = "maximize_consensus"
    PRIMARY_CONTEXT_DEFERENCE  = "primary_context_deference"
    SAFETY_FIRST               = "safety_first"
    DIVERSITY_WEIGHTING        = "diversity_weighting"

@dataclass
class FrameworkConflict:
    conflict_id: str
    conflict_type: ConflictType
    lenses_involved: List[str]
    lens_a_score: float
    lens_b_score: float
    divergence_score: float
    resolution_strategy: ResolutionStrategy
    rationale: str


CONFLICT_RATIONALE: dict[str, str] = {
    "individual_vs_communal": (
        "Western individualist framing diverges from Ubuntu communal framing. "
        "Western lens may score low because individual rights are upheld; Ubuntu lens "
        "scores high because communal solidarity is being eroded. "
        "Resolution defers to deployment community context."
    ),
    "hierarchy_vs_equality": (
        "Confucian hierarchical order conflicts with Western egalitarian norms. "
        "Content that respects social hierarchy may score low under Confucian lens "
        "but high under Western equality lens. "
        "Resolution balances universal equality with relational propriety."
    ),
    "secular_vs_sacred": (
        "Content that is permissible under secular-liberal norms may be flagged "
        "under Islamic Maqasid principles (e.g. dignity, family, faith). "
        "Resolution requires understanding the deployment's regulatory and cultural context."
    ),
    "universal_vs_particular": (
        "A universal rights framing may be blind to particular community harms. "
        "Resolution weights the lens that reflects the primary affected community."
    ),
    "orientalism_vs_agency": (
        "Islamic lens flags orientalist framing that Western lens may not detect "
        "because the Western frame is the default cultural lens in most training data. "
        "Resolution defers to the Islamic lens for Middle Eastern / Muslim contexts."
    ),
    "essentialism_vs_diversity": (
        "Ubuntu lens flags African essentialism that other lenses may miss. "
        "Resolution amplifies the Ubuntu lens score when African communities are "
        "the primary affected population."
    ),
}

DEFAULT_RESOLUTION = ResolutionStrategy.MAXIMIZE_CONSENSUS

KNOWN_CONFLICTS: list[ConflictType] = [
    ConflictType.INDIVIDUAL_VS_COMMUNAL,
    ConflictType.HIERARCHY_VS_EQUALITY,
    ConflictType.SECULAR_VS_SACRED,
    ConflictType.UNIVERSAL_VS_PARTICULAR,
    ConflictType.ORIENTALISM_VS_AGENCY,
    ConflictType.ESSENTIALISM_VS_DIVERSITY,
]

# Maps (lens_a, lens_b) pair → expected conflict type when they diverge
_PAIR_TO_CONFLICT: dict[tuple[str, str], ConflictType] = {
    ("western_v1", "ubuntu_v1"):     ConflictType.INDIVIDUAL_VS_COMMUNAL,
    ("western_v1", "confucian_v2"):  ConflictType.HIERARCHY_VS_EQUALITY,
    ("western_v1", "islamic_v1"):    ConflictType.SECULAR_VS_SACRED,
    ("ubuntu_v1",  "confucian_v2"):  ConflictType.UNIVERSAL_VS_PARTICULAR,
    ("ubuntu_v1",  "islamic_v1"):    ConflictType.ESSENTIALISM_VS_DIVERSITY,
    ("confucian_v2", "islamic_v1"):  ConflictType.UNIVERSAL_VS_PARTICULAR,
}

_PAIR_TO_STRATEGY: dict[ConflictType, ResolutionStrategy] = {
    ConflictType.INDIVIDUAL_VS_COMMUNAL:    ResolutionStrategy.PRIMARY_CONTEXT_DEFERENCE,
    ConflictType.HIERARCHY_VS_EQUALITY:     ResolutionStrategy.DIVERSITY_WEIGHTING,
    ConflictType.SECULAR_VS_SACRED:         ResolutionStrategy.PRIMARY_CONTEXT_DEFERENCE,
    ConflictType.UNIVERSAL_VS_PARTICULAR:   ResolutionStrategy.DIVERSITY_WEIGHTING,
    ConflictType.ORIENTALISM_VS_AGENCY:     ResolutionStrategy.PRIMARY_CONTEXT_DEFERENCE,
    ConflictType.ESSENTIALISM_VS_DIVERSITY: ResolutionStrategy.PRIMARY_CONTEXT_DEFERENCE,
}


class ConflictResolver:
    """
    Detects framework disagreements and assigns resolution strategies.

    A conflict is raised when two lenses produce scores that diverge by more
    than `threshold` (default 0.40). Each pair has a known ConflictType from
    the thesis taxonomy.
    """

    def __init__(self, threshold: float = 0.40) -> None:
        self.threshold = threshold

    def detect(self, lens_scores: Dict[str, float]) -> List[FrameworkConflict]:
        conflicts: list[FrameworkConflict] = []
        checked: set[tuple[str, str]] = set()

        for (la, lb), conflict_type in _PAIR_TO_CONFLICT.items():
            if la not in lens_scores or lb not in lens_scores:
                continue
            pair_key = (min(la, lb), max(la, lb))
            if pair_key in checked:
                continue
            checked.add(pair_key)

            sa, sb = lens_scores[la], lens_scores[lb]
            diff = abs(sa - sb)
            if diff < self.threshold:
                continue

            cid = f"{la}_vs_{lb}"
            strategy = _PAIR_TO_STRATEGY.get(conflict_type, DEFAULT_RESOLUTION)
            rationale = CONFLICT_RATIONALE.get(conflict_type.value, "")
            conflicts.append(FrameworkConflict(
                conflict_id=cid,
                conflict_type=conflict_type,
                lenses_involved=[la, lb],
                lens_a_score=sa,
                lens_b_score=sb,
                divergence_score=diff,
                resolution_strategy=strategy,
                rationale=rationale,
            ))

        return conflicts

    def resolve(
        self,
        conflicts: List[FrameworkConflict],
        context: Any = None,
    ) -> ResolutionStrategy:
        if not conflicts:
            return DEFAULT_RESOLUTION
        # Prioritise the highest-divergence conflict
        worst = max(conflicts, key=lambda c: c.divergence_score)
        return worst.resolution_strategy
