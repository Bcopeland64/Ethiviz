# ethiviz/context/regulatory.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class RegulatoryObligation:
    regulation: str              # "EU_AI_Act" | "GDPR" | "CCPA"
    article: str                 # e.g. "Article 10(2)"
    obligation_text: str         # Plain-language description of the obligation
    triggered_by: list[str]      # which lens findings triggered this obligation
    severity: str                # "critical" | "high" | "medium" | "informational"
    recommended_action: str
    evidence_chain: list[str]    # prototype IDs or WEAT test names that support this

@dataclass
class ComplianceMapping:
    deployment_context: Any      # DeploymentContext
    obligations: list[RegulatoryObligation]
    overall_compliance_risk: str    # "critical" | "high" | "medium" | "low"
    disclaimer: str = (
        "This mapping is informational only and does not constitute legal advice. "
        "Consult a qualified legal professional for compliance decisions."
    )

# Regulatory rule table: maps (regulation, finding_type) → obligation text
REGULATORY_RULES: list[dict[str, Any]] = [
    {
        "regulation": "EU_AI_Act",
        "article": "Article 10(2)",
        "trigger_conditions": ["racial_profiling_score > 0.5", "demographic_imbalance"],
        "obligation": (
            "High-risk AI systems must use training, validation, and testing data sets "
            "that are relevant, sufficiently representative, and free of errors. "
            "Detected demographic imbalances may indicate non-compliance."
        ),
        "severity": "critical",
        "action": (
            "Conduct a data governance review. Document demographic distribution of "
            "training data. Apply re-weighting or re-sampling to address imbalances."
        ),
    },
    {
        "regulation": "EU_AI_Act",
        "article": "Article 13",
        "trigger_conditions": ["overall_bias_score > 0.3"],
        "obligation": (
            "High-risk AI systems shall be designed and developed in such a way "
            "to ensure that their operation is sufficiently transparent to enable "
            "deployers to interpret the system's output and use it appropriately."
        ),
        "severity": "high",
        "action": (
            "Ensure bias detection results and their basis are documented. "
            "Use EthiViz provenance chains to satisfy transparency requirements."
        ),
    },
    {
        "regulation": "GDPR",
        "article": "Article 22",
        "trigger_conditions": ["automated_decision_making", "demographic_bias_detected"],
        "obligation": (
            "Data subjects have the right not to be subject to a decision based "
            "solely on automated processing which produces legal or similarly "
            "significant effects. Biased automated decisions may violate this right."
        ),
        "severity": "critical",
        "action": (
            "Implement human oversight for automated decisions affecting individuals "
            "from demographic groups where bias has been detected."
        ),
    },
    {
        "regulation": "GDPR",
        "article": "Article 5(1)(f)",
        "trigger_conditions": ["dignity_violation_score > 0.5"],
        "obligation": (
            "Personal data shall be processed in a manner that ensures appropriate "
            "security and integrity. Dignity violations in AI outputs may indicate "
            "inadequate safeguards for sensitive personal data."
        ),
        "severity": "high",
        "action": (
            "Review data processing agreements and implement additional safeguards "
            "for sensitive categories of personal data (religious, ethnic origin)."
        ),
    },
    {
        "regulation": "CCPA",
        "article": "Section 1798.100",
        "trigger_conditions": ["demographic_bias_detected", "region_in_california"],
        "obligation": (
            "Consumers have the right to know about personal information collected "
            "and how it is used. Biased outcomes based on demographic data may "
            "require disclosure of how demographic information affects decisions."
        ),
        "severity": "medium",
        "action": (
            "Update privacy policy to disclose how demographic data affects AI "
            "system outputs. Provide opt-out mechanism for data sale."
        ),
    },
    {
        "regulation": "EU_AI_Act",
        "article": "Article 9",
        "trigger_conditions": ["weat_effect_size > 0.8"],
        "obligation": (
            "Providers of high-risk AI systems shall implement a risk management "
            "system throughout the entire lifecycle. High WEAT effect sizes indicate "
            "systemic bias requiring formal risk documentation."
        ),
        "severity": "high",
        "action": (
            "Document WEAT findings in the AI system's risk management file. "
            "Implement bias mitigation measures and re-test before deployment."
        ),
    },
]

class RegulatoryMapper:
    """
    Maps EthiViz findings to regulatory obligations.
    """
    def map(
        self,
        scored_result: Any,        # ScoredResult
        context: Any,              # DeploymentContext
    ) -> ComplianceMapping:
        applicable_regulations = {r.upper() for r in self._get_applicable_regulations(context)}
        findings = self._extract_findings(scored_result)
        obligations = []

        for rule in REGULATORY_RULES:
            if rule["regulation"].upper() not in applicable_regulations:
                continue
            if self._conditions_met(rule["trigger_conditions"], findings):
                triggered_by = self._identify_triggers(
                    rule["trigger_conditions"], findings, scored_result
                )
                evidence = self._build_evidence_chain(triggered_by, scored_result)
                obligations.append(RegulatoryObligation(
                    regulation=rule["regulation"],
                    article=rule["article"],
                    obligation_text=rule["obligation"],
                    triggered_by=triggered_by,
                    severity=rule["severity"],
                    recommended_action=rule["action"],
                    evidence_chain=evidence,
                ))

        risk = self._overall_risk(obligations)
        return ComplianceMapping(
            deployment_context=context,
            obligations=obligations,
            overall_compliance_risk=risk,
        )

    def _get_applicable_regulations(self, context: Any) -> set[str]:
        regs = {context.regulatory_framework.upper().replace("-", "_")}
        regs.update(r.upper() for r in context.additional_regulations)
        if context.region in ("US", "CA") or context.regulatory_framework == "ccpa":
            regs.add("CCPA")
        return regs

    def _extract_findings(self, result: Any) -> dict[str, Any]:
        scores = {fs.framework_id: fs.overall_score for fs in result.framework_scores}
        return {
            "overall_bias_score": max(scores.values()) if scores else 0.0,
            "demographic_bias_detected": scores.get("western_v1", 0) > 0.3,
            "dignity_violation_score": (
                result.framework_scores[3].dimension_scores.get("karamah_preservation", 1.0)
                if len(result.framework_scores) > 3 else 0.0
            ),
            "weat_effect_size": max(
                (abs(r.effect_size) for suite in (result.weat_results or {}).values()
                 for r in suite.results), default=0.0
            ),
            "racial_profiling_score": scores.get("western_v1", 0),
            "demographic_imbalance": any(
                fs.dimension_scores.get("group_harmony_score", 1.0) < 0.6
                for fs in result.framework_scores
            ),
        }

    def _conditions_met(
        self, conditions: list[str], findings: dict[str, Any]
    ) -> bool:
        for cond in conditions:
            if ">" in cond:
                key, val = cond.split(">")
                if findings.get(key.strip(), 0) <= float(val.strip()):
                    return False
            elif cond.startswith("region_in_"):
                # "region_in_US,CA" -> check context.region in {"US", "CA"}
                allowed = set(cond[len("region_in_"):].split(","))
                if context is None or context.region not in allowed:
                    return False
            elif not findings.get(cond, False):
                return False
        return True

    def _identify_triggers(
        self, conditions: list[str], findings: dict, result: Any
    ) -> list[str]:
        return [c for c in conditions if findings.get(c.split(">")[0].strip(), False)]

    def _build_evidence_chain(self, triggers: list[str], result: Any) -> list[str]:
        chain = []
        for fs in result.framework_scores:
            for item in fs.flagged_candidates[:3]:
                chain.append(f"{fs.framework_id}:{item}")
        if result.weat_results:
            for suite in result.weat_results.values():
                for r in suite.results[:2]: # tests_flagged was mentioned in prompt but results is in dataclass
                    chain.append(f"WEAT:{r.test_name}")
        return chain[:10]

    def _overall_risk(self, obligations: list[RegulatoryObligation]) -> str:
        if any(o.severity == "critical" for o in obligations):
            return "critical"
        if any(o.severity == "high" for o in obligations):
            return "high"
        if any(o.severity == "medium" for o in obligations):
            return "medium"
        return "low"
