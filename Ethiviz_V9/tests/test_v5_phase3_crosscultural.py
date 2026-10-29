"""
Phase 3 — dimension-level cross-cultural reasoning, WEAT parity, real iWEAT.

Before this phase, cross-lens reasoning compared one scalar per lens, so a
harm visible through only one tradition was indistinguishable from no finding;
WEAT word lists existed for only 4 of 7 lenses (the other 3 were silently
skipped); and the iWEAT compound effect was zero by algebraic identity.
"""
from __future__ import annotations
import pathlib

import pytest
import yaml

from ethiviz.frameworks.dimension_map import (
    CrossCulturalDimensionMap,
    MORAL_CONSTRUCTS,
)
from ethiviz.analysis.weat import _interaction_2x2, load_weat_tests, load_iweat_tests

WEAT_DIR = pathlib.Path(__file__).parent.parent / "ethiviz/analysis/weat_lists"
ALL_LENSES = [
    "western_v1", "ubuntu_v1", "confucian_v2", "islamic_v1",
    "buddhist_v1", "hindu_v1", "indigenous_v1",
]


class TestMoralConstructDefinitions:
    def test_every_construct_has_at_least_one_lens(self):
        for c in MORAL_CONSTRUCTS:
            assert c.lens_dimensions, f"{c.construct_id} maps to no lens"

    def test_construct_ids_are_unique(self):
        ids = [c.construct_id for c in MORAL_CONSTRUCTS]
        assert len(ids) == len(set(ids))

    def test_constructs_only_reference_known_lenses(self):
        for c in MORAL_CONSTRUCTS:
            for lens_id in c.lens_dimensions:
                assert lens_id in ALL_LENSES, f"{c.construct_id} -> unknown {lens_id}"

    def test_dimensions_referenced_actually_exist_on_their_lens(self):
        """A construct pointing at a dimension a lens does not produce would
        silently never contribute."""
        from ethiviz.api import Analyzer

        analyzer = Analyzer(use_semantic=False)
        real_dims = {
            lens_id: set(lens.score("neutral text").dimension_scores)
            for lens_id, lens in analyzer.lenses.items()
        }
        for c in MORAL_CONSTRUCTS:
            for lens_id, dim in c.lens_dimensions.items():
                assert dim in real_dims[lens_id], (
                    f"{c.construct_id}: {lens_id} has no dimension {dim!r}"
                )


class TestCrossCulturalDimensionMap:
    def test_consensus_detected_when_traditions_agree(self):
        readings = CrossCulturalDimensionMap().analyze({
            "islamic_v1": {"dignity_violation": 0.80},
            "hindu_v1": {"dignity_harm": 0.85},
            "ubuntu_v1": {"ubuntu_violation": 0.78},
        })
        dignity = next(r for r in readings if r.construct_id == "human_dignity")
        assert dignity.is_consensus is True
        assert len(dignity.flagged_lenses) == 3
        assert "consensus" in dignity.interpretation.lower()

    def test_tradition_specific_harm_is_surfaced(self):
        """The key Phase 3 payoff: a harm only one tradition detects must be
        reported, not averaged into invisibility."""
        readings = CrossCulturalDimensionMap().analyze({
            "islamic_v1": {"dignity_violation": 0.05},
            "hindu_v1": {"dignity_harm": 0.90},
            "ubuntu_v1": {"ubuntu_violation": 0.10},
        })
        dignity = next(r for r in readings if r.construct_id == "human_dignity")
        assert dignity.distinctive_lens == "hindu_v1"
        assert dignity.is_tradition_specific is True
        assert "only" in dignity.interpretation.lower()

    def test_marginal_difference_is_not_called_distinctive(self):
        """A lens barely over the threshold while others sit just under is not
        a tradition-specific insight."""
        readings = CrossCulturalDimensionMap().analyze({
            "islamic_v1": {"dignity_violation": 0.52},
            "hindu_v1": {"dignity_harm": 0.48},
            "ubuntu_v1": {"ubuntu_violation": 0.47},
        })
        dignity = next(r for r in readings if r.construct_id == "human_dignity")
        assert dignity.distinctive_lens is None

    def test_disagreement_is_reported_as_contested(self):
        readings = CrossCulturalDimensionMap().analyze({
            "islamic_v1": {"dignity_violation": 0.90},
            "hindu_v1": {"dignity_harm": 0.55},
            "ubuntu_v1": {"ubuntu_violation": 0.10},
        })
        dignity = next(r for r in readings if r.construct_id == "human_dignity")
        assert dignity.is_consensus is False
        assert "contested" in dignity.interpretation.lower()

    def test_missing_lenses_are_skipped_not_scored_as_zero(self):
        """Analysing a subset of lenses must not make absent traditions look
        like they actively found nothing."""
        readings = CrossCulturalDimensionMap().analyze(
            {"hindu_v1": {"dignity_harm": 0.9}}
        )
        dignity = next(r for r in readings if r.construct_id == "human_dignity")
        assert dignity.contributing_lenses == ["hindu_v1"]
        assert "islamic_v1" not in dignity.scores

    def test_single_lens_construct_notes_lack_of_corroboration(self):
        readings = CrossCulturalDimensionMap().analyze({
            "indigenous_v1": {"seven_generations_violation": 0.0},
        })
        r = next(r for r in readings
                 if r.construct_id == "intergenerational_responsibility")
        assert "only" in r.interpretation.lower()

    def test_readings_sorted_by_severity(self):
        readings = CrossCulturalDimensionMap().analyze({
            "islamic_v1": {"dignity_violation": 0.9, "orientalism": 0.1},
            "hindu_v1": {"dignity_harm": 0.9, "dharmic_disrespect": 0.1},
            "ubuntu_v1": {"ubuntu_violation": 0.9, "cultural_erasure": 0.1},
        })
        means = [r.mean_score for r in readings]
        assert means == sorted(means, reverse=True)

    def test_helper_filters(self):
        m = CrossCulturalDimensionMap()
        readings = m.analyze({
            "islamic_v1": {"dignity_violation": 0.8},
            "hindu_v1": {"dignity_harm": 0.85},
            "ubuntu_v1": {"ubuntu_violation": 0.05, "african_essentialism": 0.9},
            "buddhist_v1": {"identity_reification": 0.05},
        })
        assert all(r.is_consensus for r in m.consensus_findings(readings))
        assert all(r.is_tradition_specific for r in m.tradition_specific_findings(readings))


class TestScoredResultIntegration:
    def test_analyze_populates_construct_readings(self):
        from ethiviz.api import Analyzer

        result = Analyzer(use_semantic=False).analyze(
            ["Dalits are polluted by nature and should not mix with upper castes."]
        )
        assert result.construct_readings
        assert hasattr(result, "tradition_specific_findings")
        assert hasattr(result, "consensus_findings")


class TestWEATParity:
    @pytest.mark.parametrize("lens_id", ALL_LENSES)
    def test_every_lens_has_weat_word_lists(self, lens_id):
        """Regression: buddhist/hindu/indigenous had no word lists, so
        run_weat=True silently skipped them via `if not tests: continue`."""
        assert (WEAT_DIR / f"{lens_id}.yaml").exists()
        assert load_weat_tests(lens_id), f"{lens_id} defines no WEAT tests"

    @pytest.mark.parametrize("lens_id", ALL_LENSES)
    def test_weat_word_lists_are_well_formed(self, lens_id):
        for test in load_weat_tests(lens_id):
            for field in ("target_a", "target_b", "attribute_x", "attribute_y"):
                assert test[field], f"{lens_id}/{test['test_name']}: {field} empty"


class TestIWEATInteractionTerm:
    def test_additive_model_yields_zero_interaction(self):
        base, r, g = 0.1, 0.3, 0.2
        assert _interaction_2x2(base + r + g, base + r, base + g, base) == pytest.approx(0.0)

    def test_superadditive_interaction_is_positive(self):
        base, r, g = 0.1, 0.3, 0.2
        val = _interaction_2x2(base + r + g + 0.25, base + r, base + g, base)
        assert val == pytest.approx(0.25)

    def test_subadditive_interaction_is_negative(self):
        base, r, g = 0.1, 0.3, 0.2
        val = _interaction_2x2(base + r + g - 0.25, base + r, base + g, base)
        assert val == pytest.approx(-0.25)

    def test_regression_interaction_is_not_identically_zero(self):
        """Regression: the previous formula was
            actual - (axis1_effect + axis2_effect)
        which expands to zero for every possible input, so the compound effect
        could never report intersectional amplification."""
        assert _interaction_2x2(0.9, 0.4, 0.3, 0.1) != pytest.approx(0.0)

    def test_iweat_tests_load_with_four_ordered_cells(self):
        tests = load_iweat_tests("western_v1")
        assert tests
        for t in tests:
            assert len(t["identity_combinations"]) == 4
            assert t["attribute_x"] and t["attribute_y"]

    def test_run_iweat_produces_results_through_api(self):
        """Regression: run_iweat=True assigned an empty dict, so the public
        parameter silently did nothing."""
        from ethiviz.api import Analyzer

        result = Analyzer(use_semantic=False).analyze(["neutral text"], run_iweat=True)
        assert result.iweat_results
        key = "western_v1:race_gender_competence_intersection"
        assert key in result.iweat_results
        assert hasattr(result.iweat_results[key], "compound_effect")
