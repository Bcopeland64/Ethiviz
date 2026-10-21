"""
Tests for EthiViz V7 Phase 3 — Activate the Dormant Engine (Upgrades 51,
52, 54). Covers: dimension-level findings/conflicts/synergies reaching the
bridge response (Upgrade 51), the opt-in individual-fairness metric
(Upgrade 52), and per-framework severity_thresholds parsing replacing the
proxy-rescaled table (Upgrade 54). Upgrade 53 (mitigation preview) was
deferred — see README.md's "Known limitations" — so there's nothing to
test here for it.

Uses the real Analyzer/bridge (use_semantic=False for speed, matching
tests/test_v5_tier4.py's convention) rather than mocking ScoredResult,
consistent with this suite's existing preference for exercising real
(non-mocked) discrimination.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Scripts"))

from ethiviz.api import Analyzer  # noqa: E402
from ethiviz.frameworks.base import CulturalFramework, FrameworkRegistry  # noqa: E402
from ethiviz.frameworks.loader import FrameworkLoader  # noqa: E402


# ── Upgrade 54: severity_thresholds parsing ─────────────────────────────────

class TestSeverityThresholdsParsing:
    def test_builtin_frameworks_have_severity_thresholds(self):
        registry = FrameworkLoader().load_builtin()
        for fid in registry.registered_ids:
            framework = registry.get(fid)
            assert framework.severity_thresholds, f"{fid} has no severity_thresholds"
            for key in ("low", "moderate", "high", "critical"):
                assert key in framework.severity_thresholds

    def test_thresholds_are_monotonically_increasing(self):
        registry = FrameworkLoader().load_builtin()
        for fid in registry.registered_ids:
            t = registry.get(fid).severity_thresholds
            assert t["low"] < t["moderate"] < t["high"] < t["critical"]

    def test_missing_severity_thresholds_defaults_to_empty(self, tmp_path):
        yaml_path = tmp_path / "custom_v1.yaml"
        yaml_path.write_text(
            "id: custom_v1\nname: Custom\ndescription: test framework\n"
            "ethical_lenses: []\nbias_criteria: {}\n"
        )
        framework = FrameworkLoader().load_file(yaml_path)
        assert framework.severity_thresholds == {}


class TestSeverityForUsesFrameworkRegistry:
    def _bridge(self):
        import ethiviz_bridge
        return ethiviz_bridge

    def test_severity_for_builtin_framework_matches_yaml_scale(self):
        bridge = self._bridge()
        cutoffs = bridge._thresholds_for("western_v1")
        registry = FrameworkLoader().load_builtin()
        assert cutoffs == registry.get("western_v1").severity_thresholds

    def test_severity_for_unknown_framework_falls_back(self):
        bridge = self._bridge()
        cutoffs = bridge._thresholds_for("nonexistent_framework_xyz")
        assert cutoffs == bridge._FALLBACK_THRESHOLDS["western_v1"]

    def test_severity_buckets_are_ordered(self):
        bridge = self._bridge()
        low = bridge._severity_for("western_v1", 0.01)
        high = bridge._severity_for("western_v1", 0.99)
        assert low in ("unknown", "low")
        assert high == "critical"

    def test_registry_thresholds_used_over_hardcoded_fallback(self, monkeypatch):
        """A framework registered with deliberately different thresholds than
        the fallback table must actually change _severity_for's output —
        proves the registry is the real source now, not just present."""
        bridge = self._bridge()
        custom_registry = FrameworkRegistry()
        custom_registry.register(
            CulturalFramework(
                framework_id="western_v1", name="Western", description="",
                ethical_lenses=[], bias_criteria={},
                severity_thresholds={"low": 0.001, "moderate": 0.002, "high": 0.003, "critical": 0.004},
            ),
            "testhash",
        )

        class _FakeAnalyzer:
            registry = custom_registry

        monkeypatch.setattr(bridge, "get_analyzer", lambda: _FakeAnalyzer())
        assert bridge._severity_for("western_v1", 0.5) == "critical"


# ── Upgrade 51: dimension findings reach the bridge response ───────────────

class TestDimensionFindingsWiring:
    @pytest.fixture(scope="class")
    def analyzer(self):
        return Analyzer(use_semantic=False)

    def test_run_text_analysis_returns_three_values(self, monkeypatch, analyzer):
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        dataset_text = (
            "Women are naturally better suited to caregiving roles than leadership. "
            "Men are inherently more rational and should make the final decisions."
        )
        items, scores, dimension_findings = ethiviz_bridge.run_text_analysis(
            text_input=dataset_text,
            selected_fids=ethiviz_bridge.resolve_framework_ids(None),
        )
        assert isinstance(items, list) and len(items) > 0
        assert isinstance(scores, list) and len(scores) > 0
        assert isinstance(dimension_findings, dict)
        for key in (
            "construct_readings", "consensus_findings",
            "tradition_specific_findings", "conflicts", "synergy_amplifications",
        ):
            assert key in dimension_findings

    def test_dimension_findings_shape(self, monkeypatch, analyzer):
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        result = analyzer.analyze(
            dataset=["Women are naturally better suited to caregiving than leadership."] * 3,
            dataset_source="test",
        )
        findings = ethiviz_bridge._serialize_dimension_findings(result)

        # consensus_findings/tradition_specific_findings must each be a
        # filtered subset of construct_readings, keyed by the same flags.
        all_ids = {r["construct_id"] for r in findings["construct_readings"]}
        for r in findings["consensus_findings"]:
            assert r["construct_id"] in all_ids
            assert r["is_consensus"] is True
        for r in findings["tradition_specific_findings"]:
            assert r["construct_id"] in all_ids
            assert r["is_tradition_specific"] is True
            assert r["distinctive_lens"] is not None

        for r in findings["construct_readings"]:
            assert isinstance(r["scores"], dict)
            assert isinstance(r["mean_score"], float)
            assert isinstance(r["contributing_lenses"], list)

        for c in findings["conflicts"]:
            assert isinstance(c["conflict_type"], str)  # enum already .value'd
            assert isinstance(c["resolution_strategy"], str)
            assert isinstance(c["lenses_involved"], list)

        assert isinstance(findings["synergy_amplifications"], list)

    def test_run_analysis_job_adds_dimension_findings_to_final_results(self, monkeypatch, analyzer):
        """Integration check on the actual api_server.py code path, not just
        the bridge function in isolation — this is where a prior version of
        this wiring could plausibly be dropped again (final_results is
        assembled by hand, not generically from whatever the bridge
        returns)."""
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        scripts_dir = str(Path(__file__).resolve().parent.parent / "Scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import api_server

        # Isolate from the real ~/.ethiviz/jobs.db — run_analysis_job's
        # _update_job(..., result=final_results) writes through to
        # JobStore.store_results whenever HAS_JOB_STORE is true, and this
        # test has no reason to touch a real, possibly-shared database file.
        monkeypatch.setattr(api_server, "HAS_JOB_STORE", False)

        job_id = "test-dimension-findings-job"
        api_server._jobs_fallback[job_id] = {}
        try:
            api_server.run_analysis_job(
                job_id=job_id,
                analysis_type="text",
                data_inputs={"text_input": "Women are naturally better suited to caregiving than leadership."},
                selected_traditions=[],
                advanced_options={},
            )
            job = api_server._jobs_fallback[job_id]
            assert job["status"] == "completed"
            assert "dimension_findings" in job["result"]
            assert "construct_readings" in job["result"]["dimension_findings"]
        finally:
            api_server._jobs_fallback.pop(job_id, None)


# ── Upgrade 52: individual fairness ─────────────────────────────────────────

class TestIndividualFairnessWiring:
    @pytest.fixture(scope="class")
    def analyzer(self):
        return Analyzer(use_semantic=False)

    def test_disabled_by_default(self, monkeypatch, analyzer):
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        result = analyzer.analyze(
            dataset=["Text one.", "Text two.", "Text three.", "Text four."],
            dataset_source="test",
        )
        scores = ethiviz_bridge.compute_tradition_scores(
            result, ethiviz_bridge.resolve_framework_ids(None),
        )
        assert all("individual_fairness" not in s for s in scores)

    def test_enabled_produces_individual_fairness_entries(self, monkeypatch, analyzer):
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        result = analyzer.analyze(
            dataset=["Text one.", "Text two.", "Text three.", "Text four."],
            dataset_source="test",
        )
        scores = ethiviz_bridge.compute_tradition_scores(
            result, ethiviz_bridge.resolve_framework_ids(None),
            include_statistical_metrics=True,
        )
        assert len(scores) > 0
        for s in scores:
            assert "individual_fairness" in s
            m = s["individual_fairness"]
            if m is not None:
                assert 0.0 <= m["consistency_score"] <= 1.0
                assert isinstance(m["interpretation"], str)

    def test_too_few_texts_yields_none_not_error(self, monkeypatch, analyzer):
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        result = analyzer.analyze(dataset=["Only one text."], dataset_source="test")
        scores = ethiviz_bridge.compute_tradition_scores(
            result, ethiviz_bridge.resolve_framework_ids(None),
            include_statistical_metrics=True,
        )
        assert all(s["individual_fairness"] is None for s in scores)

    def test_run_text_analysis_passes_flag_through(self, monkeypatch, analyzer):
        import ethiviz_bridge
        monkeypatch.setattr(ethiviz_bridge, "get_analyzer", lambda: analyzer)

        _, scores, _ = ethiviz_bridge.run_text_analysis(
            text_input="Text one. Text two. Text three. Text four.",
            selected_fids=ethiviz_bridge.resolve_framework_ids(None),
            include_statistical_metrics=True,
        )
        assert any("individual_fairness" in s for s in scores)


# ── Upgrade 54: demographic stubs removed ───────────────────────────────────

class TestDemographicStubsRemoved:
    def test_age_and_gender_functions_no_longer_exist(self):
        import ethiviz.analysis.demographics as demographics
        assert not hasattr(demographics, "compute_age_distribution")
        assert not hasattr(demographics, "compute_gender_distribution")

    def test_skin_tone_distribution_still_present(self):
        """The one real (non-stub) function in this module must survive —
        this isn't a test that the whole module got gutted."""
        import ethiviz.analysis.demographics as demographics
        assert hasattr(demographics, "compute_skin_tone_distribution")
