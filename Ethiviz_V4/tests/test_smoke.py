import pytest
import numpy as np
from ethiviz import Analyzer, DeploymentContext
from ethiviz.analysis.weat import WEATAnalyzer, iWEATAnalyzer
from ethiviz.vision.skin_tone import ITASkinToneEstimator
from ethiviz.context.regulatory import RegulatoryMapper

def test_smoke_1_analyzer_init():
    """Smoke Test 1: Verify Analyzer initializes with all four lenses."""
    analyzer = Analyzer()
    assert len(analyzer.lenses) == 4
    assert "western_v1" in analyzer.lenses
    assert "ubuntu_v1" in analyzer.lenses

def test_smoke_2_semantic_detection():
    """Smoke Test 2: Verify semantic bias detection on a known biased string."""
    analyzer = Analyzer(use_semantic=True)
    report = analyzer.quick_scan(["Individual rights are more important than communal stability."])
    # The string matches western_individualism_001 prototype
    western_score = next(fs.overall_score for fs in report.scored_result.framework_scores if fs.framework_id == "western_v1")
    assert western_score > 0.5

def test_smoke_3_multilingual_ar():
    """Smoke Test 3: Verify Arabic language detection and prototype mapping."""
    analyzer = Analyzer()
    # "All Muslims are terrorists" in Arabic
    report = analyzer.quick_scan(["جميع المسلمين إرهابيون"])
    islamic_score = next(fs.overall_score for fs in report.scored_result.framework_scores if fs.framework_id == "islamic_v1")
    assert islamic_score > 0.5

def test_smoke_4_ita_skin_tone():
    """Smoke Test 4: Verify ITA skin tone estimation logic (CPU)."""
    estimator = ITASkinToneEstimator()
    # Light pixel (L=200, a=128, b=140) -> High ITA -> Type I/II
    light_img = np.full((10, 10, 3), 200, dtype=np.uint8)
    res = estimator.estimate(light_img)
    assert "Type" in res.fitzpatrick_type

def test_smoke_5_regulatory_mapping():
    """Smoke Test 5: Verify EU AI Act mapping for high-bias findings."""
    ctx = DeploymentContext(region="DE", domain="hiring", primary_community="western", regulatory_framework="eu-ai-act")
    analyzer = Analyzer(deployment_context=ctx)
    report = analyzer.quick_scan(["Individual rights are more important than communal stability. Autonomy is everything."])
    assert report.compliance_mapping is not None
    assert any(ob.regulation == "EU_AI_Act" for ob in report.compliance_mapping.obligations)

def test_smoke_6_weat_benchmarks():
    """Smoke Test 6: Verify WEAT benchmark validation suite runs."""
    weat = WEATAnalyzer(n_permutations=100)
    results = weat.run_benchmark_validation()
    assert "male_vs_female_career_family" in results

def test_smoke_7_iweat_intersectional():
    """Smoke Test 7: Verify intersectional WEAT (iWEAT) compound effect calculation."""
    iweat = iWEATAnalyzer(n_permutations=100)
    # Mock identity combinations
    combos = {
        "Black_woman": ["Black woman", "African woman"],
        "Black_man": ["Black man", "African man"],
        "white_woman": ["white woman", "European woman"],
        "white_man": ["white man", "European man"],
    }
    res = iweat.run("test", "western", combos, ["pleasant"], ["unpleasant"])
    assert hasattr(res, "compound_effect")

def test_smoke_8_reproducibility():
    """Smoke Test 8: Verify ReproducibilityRecord capture."""
    analyzer = Analyzer()
    report = analyzer.quick_scan(["test"])
    rec = report.scored_result.reproducibility
    assert len(rec.analysis_id) == 16
    assert rec.library_version == "0.4.0"
