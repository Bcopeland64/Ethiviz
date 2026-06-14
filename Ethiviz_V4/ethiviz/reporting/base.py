from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from ethiviz.scoring.base import ScoredResult
from ethiviz.context.regulatory import ComplianceMapping

@dataclass
class BiasReport:
    """Unified report for bias analysis."""
    scored_result: ScoredResult
    compliance_mapping: Optional[ComplianceMapping] = None
    summary_text: str = ""
    
    def summary(self) -> str:
        if self.summary_text:
            return self.summary_text
        
        # Auto-generate summary
        high_lenses = [fs.framework_id for fs in self.scored_result.framework_scores if fs.overall_score > 0.5]
        if not high_lenses:
            return "No significant bias detected across the four ethical frameworks."
        
        return f"Significant bias detected in the following lenses: {', '.join(high_lenses)}. " \
               f"Overall consensus score: {self.scored_result.consensus_score:.3f}."

    def to_json(self) -> str:
        import json
        # Simplified serialization
        return json.dumps({
            "consensus_score": self.scored_result.consensus_score,
            "summary": self.summary()
        })

    def to_html(self) -> str:
        # Will be implemented in html_report.py
        from ethiviz.reporting.html_report import generate_html_report
        return generate_html_report(self)
