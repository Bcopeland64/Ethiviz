# examples/text_analysis.py
from ethiviz.api import Analyzer
from ethiviz.context.deployment import DeploymentContext

def main():
    # 1. Define context
    ctx = DeploymentContext(
        region="DE",
        domain="hiring",
        primary_community="western",
        regulatory_framework="eu_ai_act"
    )
    
    # 2. Initialize
    analyzer = Analyzer(deployment_context=ctx)
    
    # 3. Analyze
    dataset = [
        "The software engineer is highly skilled.",
        "Women are generally more emotional and less suited for leadership roles.",
        "Applicants from African backgrounds should be evaluated with stricter criteria."
    ]
    
    print("Starting EthiViz Analysis...")
    result = analyzer.analyze(dataset)
    
    # 4. Results
    print(f"\nConsensus Score: {result.consensus_score:.3f}")
    for fs in result.framework_scores:
        print(f"{fs.framework_name}: {fs.overall_score:.3f}")
        
    # 5. Report
    report = result.generate_report()
    print(f"\nOverall Compliance Risk: {report.compliance_mapping.overall_compliance_risk.upper()}")

if __name__ == "__main__":
    main()
