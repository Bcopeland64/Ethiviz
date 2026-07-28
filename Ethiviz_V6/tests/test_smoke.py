import pytest
import numpy as np
from ethiviz import Analyzer, DeploymentContext
from ethiviz.analysis.weat import WEATAnalyzer, iWEATAnalyzer
from ethiviz.vision.skin_tone import ITASkinToneEstimator
from ethiviz.context.regulatory import RegulatoryMapper

def test_smoke_1_analyzer_init():
    """Smoke Test 1: Verify Analyzer initializes with all seven lenses."""
    analyzer = Analyzer()
    assert len(analyzer.lenses) == 7
    assert "western_v1" in analyzer.lenses
    assert "ubuntu_v1" in analyzer.lenses

def test_smoke_2_semantic_detection():
    """Smoke Test 2: Verify semantic bias detection routes to the right dimension.

    Asserts a structural property (the correct prototype and dimension win)
    rather than an absolute score threshold. Absolute thresholds are a
    function of the embedding model's similarity scale, so under a mocked
    model they test the mock, not the detector.
    """
    analyzer = Analyzer(use_semantic=True)
    report = analyzer.quick_scan(
        ["Individual rights are more important than communal stability."]
    )
    western = next(
        fs for fs in report.scored_result.framework_scores
        if fs.framework_id == "western_v1"
    )
    # The string is a paraphrase of western_proc_001 (procedural_bias).
    top_dimension = max(western.dimension_scores.items(), key=lambda kv: kv[1])[0]
    assert top_dimension == "procedural_bias"
    assert western.overall_score > 0.0

def test_smoke_3_multilingual_ar():
    """Smoke Test 3: Verify Arabic input routes to the culturally-relevant lens."""
    analyzer = Analyzer()
    # "All Muslims are terrorists" in Arabic
    report = analyzer.quick_scan(["جميع المسلمين إرهابيون"])
    scores = {
        fs.framework_id: fs.overall_score
        for fs in report.scored_result.framework_scores
    }
    assert report.scored_result.metadata["language_detected"] == "ar"
    # The Islamic lens must lead by a clear margin, not merely be non-zero.
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    assert ranked[0][0] == "islamic_v1"
    assert ranked[0][1] > 2 * ranked[1][1]

def test_smoke_3b_non_english_reports_degraded_coverage():
    """Non-English analysis must declare its own degradation rather than
    returning a confident-looking score built on a partial pipeline."""
    analyzer = Analyzer()
    report = analyzer.quick_scan(["جميع المسلمين إرهابيون"])
    islamic = next(
        fs for fs in report.scored_result.framework_scores
        if fs.framework_id == "islamic_v1"
    )
    assert islamic.raw_evidence["analysis_coverage"] < 1.0
    assert islamic.raw_evidence["warnings"]

def test_smoke_4_ita_skin_tone():
    """Smoke Test 4: Verify ITA skin tone estimation logic (CPU)."""
    estimator = ITASkinToneEstimator()
    # Light pixel (L=200, a=128, b=140) -> High ITA -> Type I/II
    light_img = np.full((10, 10, 3), 200, dtype=np.uint8)
    res = estimator.estimate(light_img)
    assert "Type" in res.fitzpatrick_type

def _high_bias_result(score: float = 0.75):
    """Minimal ScoredResult carrying a known peak bias score, for exercising
    the regulatory mapper independently of the embedding model's scale."""
    from ethiviz.scoring.base import FrameworkScore, ScoredResult
    from ethiviz.utils.reproducibility import ReproducibilityRecord

    fs = FrameworkScore(
        framework_id="western_v1",
        framework_name="Western V1",
        overall_score=score,
        dimension_scores={"racial_bias": score},
        confidence=0.88,
        flagged_candidates=[],
        confidence_interval_95=(score, score),
        bootstrap_n=100,
        raw_evidence={"peak_score": score},
    )
    return ScoredResult(
        candidates=[], framework_scores=[fs], consensus_score=score,
        conflicts=[], synergy_amplifications=[], weat_results=None,
        iweat_results=None, deployment_context=None,
        reproducibility=ReproducibilityRecord.capture(["western_v1"]),
        metadata={},
    )

def test_smoke_5_regulatory_mapping():
    """Smoke Test 5: Verify EU AI Act mapping fires for high-bias findings."""
    ctx = DeploymentContext(region="DE", domain="hiring", primary_community="western", regulatory_framework="eu-ai-act")
    mapping = RegulatoryMapper().map(_high_bias_result(0.75), ctx)
    assert mapping is not None
    assert any(ob.regulation == "EU_AI_Act" for ob in mapping.obligations)

def test_smoke_5b_regulatory_uses_worst_case_not_mean():
    """A single egregious document must trigger obligations even when the
    dataset mean is low — regulatory exposure follows the worst case."""
    ctx = DeploymentContext(region="DE", domain="hiring", primary_community="western", regulatory_framework="eu-ai-act")
    result = _high_bias_result(0.75)
    # Mean well below the 0.3 trigger, peak well above it.
    result.framework_scores[0].overall_score = 0.05
    result.framework_scores[0].raw_evidence["peak_score"] = 0.75

    mapping = RegulatoryMapper().map(result, ctx)
    assert any(ob.regulation == "EU_AI_Act" for ob in mapping.obligations)

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
    assert rec.library_version == "0.6.0"
