"""
Phase 1 — regression tests for the repaired cultural metrics.

Each test class here covers a function that was previously either crashing or
computing something structurally different from what it documented, with no
test coverage to catch it. The "regression" tests below pin the specific
defect so it cannot silently return.
"""
from __future__ import annotations
import pytest

from ethiviz.analysis.dual_framework import DualEthicsFramework
from ethiviz.analysis.intersectional import (
    calculate_intersectional_analysis,
    IntersectionResult,
    SUPERADDITIVE_THRESHOLD,
)
from ethiviz.analysis.cultural_inclusion import cultural_inclusion_index


class TestDualEthicsFramework:
    def test_resolve_conflict_does_not_raise(self):
        """Regression: resolve_conflict referenced bare names, not self.*,
        and raised NameError on every call."""
        f = DualEthicsFramework(western_bias_score=0.8, non_western_bias_score=0.2)
        assert isinstance(f.resolve_conflict(), str)

    def test_western_dominant_reports_individualistic(self):
        f = DualEthicsFramework(western_bias_score=0.8, non_western_bias_score=0.2)
        assert "Individualistic" in f.resolve_conflict()

    def test_non_western_dominant_reports_communal(self):
        f = DualEthicsFramework(western_bias_score=0.2, non_western_bias_score=0.8)
        assert "Communal" in f.resolve_conflict()

    def test_close_scores_report_consensus(self):
        f = DualEthicsFramework(western_bias_score=0.50, non_western_bias_score=0.55)
        assert "Consensus" in f.resolve_conflict()


class TestIntersectionalAnalysis:
    def test_returns_intersection_result_objects(self):
        res = calculate_intersectional_analysis({"black": 0.8}, {"woman": 0.7})
        assert isinstance(res["black_woman"], IntersectionResult)

    def test_superadditive_intersection_is_detected(self):
        """The Crenshaw case: compound disadvantage exceeding the independent
        baseline must be representable and flagged."""
        res = calculate_intersectional_analysis(
            {"black": 0.5}, {"woman": 0.5}, {"black_woman": 0.9}
        )
        r = res["black_woman"]
        assert r.expected_independent == pytest.approx(0.75)
        assert r.amplification == pytest.approx(1.2)
        assert r.is_superadditive is True

    def test_regression_compound_can_exceed_both_parts(self):
        """Regression: the old implementation returned score_a * score_b, which
        is always <= min(a, b), making compound disadvantage inexpressible."""
        res = calculate_intersectional_analysis(
            {"black": 0.8}, {"woman": 0.7}, {"black_woman": 0.99}
        )
        r = res["black_woman"]
        assert r.observed > r.score_a
        assert r.observed > r.score_b

    def test_buffered_intersection_is_not_superadditive(self):
        res = calculate_intersectional_analysis(
            {"black": 0.8}, {"woman": 0.7}, {"black_woman": 0.60}
        )
        r = res["black_woman"]
        assert r.amplification < 1.0
        assert r.is_superadditive is False
        assert "Buffered" in r.interpretation

    def test_missing_observed_defaults_to_independence(self):
        """With no measured intersection data we must report 'no interaction',
        not invent one."""
        res = calculate_intersectional_analysis({"black": 0.8}, {"woman": 0.7})
        r = res["black_woman"]
        assert r.amplification == pytest.approx(1.0)
        assert r.is_superadditive is False

    def test_zero_scores_do_not_divide_by_zero(self):
        res = calculate_intersectional_analysis({"a": 0.0}, {"b": 0.0})
        assert res["a_b"].amplification == 1.0

    def test_all_pairs_are_enumerated(self):
        res = calculate_intersectional_analysis(
            {"black": 0.5, "asian": 0.4}, {"woman": 0.6, "man": 0.3}
        )
        assert set(res) == {"black_woman", "black_man", "asian_woman", "asian_man"}

    def test_threshold_boundary_is_superadditive(self):
        """A ratio exactly at the threshold counts as superadditive."""
        # noisy_or(0.5, 0.5) = 0.75; observed = 0.75 * SUPERADDITIVE_THRESHOLD
        observed = 0.75 * SUPERADDITIVE_THRESHOLD
        res = calculate_intersectional_analysis(
            {"a": 0.5}, {"b": 0.5}, {"a_b": observed}
        )
        assert res["a_b"].is_superadditive is True


class TestCulturalInclusionIndex:
    def test_perfect_match_scores_one(self):
        ref = {"hijab": 0.5, "sari": 0.5}
        assert cultural_inclusion_index(["hijab", "sari"], ref) == pytest.approx(1.0)

    def test_regression_reference_values_are_actually_used(self):
        """Regression: the old implementation only checked key overlap, so a
        balanced target and a 98/1/1 target both returned 1.0."""
        detected = ["hijab", "kente", "sari"]
        balanced = cultural_inclusion_index(
            detected, {"hijab": 0.33, "kente": 0.33, "sari": 0.34}
        )
        skewed = cultural_inclusion_index(
            detected, {"hijab": 0.98, "kente": 0.01, "sari": 0.01}
        )
        assert balanced != pytest.approx(skewed)
        assert balanced > skewed

    def test_regression_proportions_matter_not_just_presence(self):
        """One token of each category must not score the same as a balanced
        sample when the target is balanced."""
        ref = {"hijab": 0.5, "sari": 0.5}
        balanced = cultural_inclusion_index(["hijab", "sari"], ref)
        lopsided = cultural_inclusion_index(["hijab"] * 99 + ["sari"], ref)
        assert lopsided < balanced

    def test_entirely_off_target_scores_zero(self):
        ref = {"hijab": 0.5, "sari": 0.5}
        assert cultural_inclusion_index(["kimono", "kimono"], ref) == pytest.approx(0.0)

    def test_off_target_detections_reduce_score(self):
        """Off-target elements are real representation and must register as
        divergence rather than being dropped."""
        ref = {"hijab": 0.5, "sari": 0.5}
        clean = cultural_inclusion_index(["hijab", "sari"], ref)
        polluted = cultural_inclusion_index(["hijab", "sari", "kimono", "kimono"], ref)
        assert polluted < clean

    def test_empty_inputs_return_zero(self):
        assert cultural_inclusion_index([], {"hijab": 1.0}) == 0.0
        assert cultural_inclusion_index(["hijab"], {}) == 0.0

    def test_result_is_bounded_unit_interval(self):
        ref = {"a": 0.7, "b": 0.3}
        for detected in (["a"], ["b"], ["a", "b"], ["a"] * 50 + ["b"], ["z"]):
            score = cultural_inclusion_index(detected, ref)
            assert 0.0 <= score <= 1.0

    def test_unnormalised_reference_is_handled(self):
        """Reference distributions given as counts/weights rather than
        probabilities must still work."""
        assert cultural_inclusion_index(
            ["hijab", "sari"], {"hijab": 50, "sari": 50}
        ) == pytest.approx(1.0)
