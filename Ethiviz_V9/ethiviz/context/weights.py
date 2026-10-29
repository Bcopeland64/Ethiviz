# ethiviz/context/weights.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ethiviz.context.deployment import DeploymentContext

# Context-derived lens weight tables.
# Each entry maps (primary_community, domain) → framework weights.
CONTEXT_WEIGHTS: dict[tuple[str, str], dict[str, float]] = {
    ("african", "hiring"): {
        "ubuntu_v1": 0.40, "western_v1": 0.25,
        "confucian_v2": 0.10, "islamic_v1": 0.25,
    },
    ("african", "healthcare"): {
        "ubuntu_v1": 0.45, "western_v1": 0.25,
        "confucian_v2": 0.05, "islamic_v1": 0.25,
    },
    ("east_asian", "education"): {
        "confucian_v2": 0.40, "western_v1": 0.25,
        "ubuntu_v1": 0.15, "islamic_v1": 0.20,
    },
    ("east_asian", "hiring"): {
        "confucian_v2": 0.40, "western_v1": 0.30,
        "ubuntu_v1": 0.15, "islamic_v1": 0.15,
    },
    ("muslim_majority", "hiring"): {
        "islamic_v1": 0.40, "western_v1": 0.25,
        "ubuntu_v1": 0.20, "confucian_v2": 0.15,
    },
    ("muslim_majority", "content_moderation"): {
        "islamic_v1": 0.45, "western_v1": 0.25,
        "ubuntu_v1": 0.20, "confucian_v2": 0.10,
    },
    ("western", "hiring"): {
        "western_v1": 0.45, "ubuntu_v1": 0.25,
        "confucian_v2": 0.15, "islamic_v1": 0.15,
    },
    ("global", "general"): {
        "western_v1": 0.25, "ubuntu_v1": 0.25,
        "confucian_v2": 0.25, "islamic_v1": 0.25,
    },
}

def get_weights(context: DeploymentContext) -> dict[str, float]:
    """
    Look up context-specific framework weights.
    Falls back to equal weighting if no match found.
    """
    key = (context.primary_community, context.domain)
    if key in CONTEXT_WEIGHTS:
        return CONTEXT_WEIGHTS[key]
    community_key = (context.primary_community, "general")
    if community_key in CONTEXT_WEIGHTS:
        return CONTEXT_WEIGHTS[community_key]
    # Equal weights fallback
    return {"western_v1": 0.25, "ubuntu_v1": 0.25,
            "confucian_v2": 0.25, "islamic_v1": 0.25}
