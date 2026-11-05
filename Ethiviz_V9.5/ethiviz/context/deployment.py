# ethiviz/context/deployment.py
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class DeploymentContext:
    """
    Encodes the cultural and regulatory context of a deployment.
    Used by MultiFrameworkScorer to apply context-weighted aggregation
    and by RegulatoryMapper to determine applicable regulations.
    """
    region: str                  # ISO 3166-1 alpha-2 country code
    domain: str                  # "hiring" | "healthcare" | "content_moderation"
                                 # | "education" | "finance" | "general"
    primary_community: str       # "african" | "east_asian" | "muslim_majority"
                                 # | "western" | "south_asian" | "global"
    regulatory_framework: str    # "gdpr" | "ccpa" | "eu_ai_act" | "none"
    additional_regulations: list[str] = field(default_factory=list)
    notes: str = ""
