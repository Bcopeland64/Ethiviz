# ethiviz/analysis/recommendations.py
from __future__ import annotations
from typing import List, Dict

def generate_recommendations(
    lens_scores: Dict[str, float],
    regulatory_obligations: List[str],
) -> List[str]:
    """
    Generate priority-sorted mitigation recommendations (Figure A5).
    """
    recommendations = []
    
    if any(s > 0.8 for s in lens_scores.values()):
        recommendations.append("CRITICAL: Bias exceeds acceptable threshold. Immediate human review required.")
        
    if "Article 10(2)" in regulatory_obligations:
        recommendations.append("Conduct a data governance review to address representative data set requirements.")
        
    if lens_scores.get("ubuntu_v1", 0) > 0.5:
        recommendations.append("Address communal essentialism through targeted adversarial de-biasing.")
        
    return recommendations
