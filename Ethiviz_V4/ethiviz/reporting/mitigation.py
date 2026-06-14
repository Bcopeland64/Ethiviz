from __future__ import annotations
from typing import List, Dict, Any

@dataclass
class MitigationRecommendation:
    title: str
    description: str
    priority: str # "high" | "medium" | "low"
    citation: str

class MitigationAdvisor:
    """Provides recommendations for mitigating detected biases."""
    
    def advise(self, lens_scores: Dict[str, float]) -> List[MitigationRecommendation]:
        recommendations = []
        
        if lens_scores.get("western_v1", 0) > 0.5:
            recommendations.append(MitigationRecommendation(
                "Enhance Procedural Fairness",
                "Ensure that the automated process includes human-in-the-loop review for high-impact decisions.",
                "high",
                "Copeland (2025), Section 4.1"
            ))
            
        if lens_scores.get("ubuntu_v1", 0) > 0.5:
            recommendations.append(MitigationRecommendation(
                "Communal Impact Assessment",
                "Perform a stakeholder analysis to understand how this system affects the target community as a whole.",
                "high",
                "Copeland (2025), Section 4.2"
            ))
            
        return recommendations
