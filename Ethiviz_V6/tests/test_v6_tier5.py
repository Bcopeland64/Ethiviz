"""
Tests for EthiViz V6 Tier 5 Upgrades (35-39).
Covers: DriftMonitor thread-safety, framework coverage_audit self-audit,
        translation-review surfacing in Analyzer.analyze(), and the
        JobStore additions backing job/audit-log retention.
"""
import tempfile
import threading
from pathlib import Path

import pytest
import yaml


# ── Upgrade 35: DriftMonitor thread-safety ──────────────────────────────────

class TestDriftMonitorConcurrency:
    def _make_monitor(self):
        from ethiviz.scoring.drift import DriftMonitor
        return DriftMonitor(snapshot_dir=Path(tempfile.mkdtemp()))

    def test_baseline_survives_concurrent_check_drift(self):
        """Regression: unguarded read-then-write of the baseline/snapshot
        files let concurrent analysis jobs race, corrupting the JSON that
        _load_baseline() reads back."""
        monitor = self._make_monitor()
        monitor.record_snapshot("western_v1", [0.1, 0.2, 0.3], "seed", set_as_baseline=True)

        errors = []

        def worker():
            try:
                for _ in range(15):
                    monitor.check_drift("western_v1", [0.2, 0.4, 0.6], "concurrent")
            except Exception as exc:  # pragma: no cover - failure path
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        baseline = monitor._load_baseline("western_v1")
        assert baseline is not None
        assert baseline.mean == pytest.approx(0.2, abs=1e-6)

    def test_atomic_write_helper_produces_valid_json_with_no_leftover_temp_file(self):
        import json
        from ethiviz.scoring.drift import DriftMonitor
        monitor = self._make_monitor()
        path = Path(monitor.SNAPSHOT_DIR) / "sample.json"
        monitor._atomic_write_json(path, {"a": 1})

        assert path.exists()
        assert json.loads(path.read_text()) == {"a": 1}
        assert list(Path(monitor.SNAPSHOT_DIR).glob("*.tmp")) == []


# ── Upgrade 36: Framework coverage self-audit ───────────────────────────────

class TestCoverageAudit:
    def _write_prototype_file(self, tmp_dir: Path, framework_id: str, n_protos: int,
                               provenance: dict | None = None):
        prototypes = [
            {
                "id": f"{framework_id}_{i}",
                "text": f"example {i}",
                "severity": 1.0,
                "category": "cat_a" if i % 2 == 0 else "cat_b",
                "language": "en",
                "translations": {"hi": f"example {i} hi"},
            }
            for i in range(n_protos)
        ]
        data = {"prototypes": prototypes}
        if provenance is not None:
            data["translation_provenance"] = provenance
        path = tmp_dir / f"{framework_id}_prototypes.yaml"
        path.write_text(yaml.safe_dump(data))
        return path

    def test_audit_tradition_counts_prototypes_and_categories(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit
        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)
        self._write_prototype_file(tmp_path, "western_v1", 4)

        result = coverage_audit.audit_tradition("western_v1")
        assert result.prototype_count == 4
        assert result.category_count == 2
        assert "hi" in result.languages_declared

    def test_undeclared_provenance_is_flagged(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit
        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)
        self._write_prototype_file(tmp_path, "western_v1", 3, provenance=None)

        result = coverage_audit.audit_tradition("western_v1")
        assert result.translations_undeclared is True
        assert coverage_audit.is_language_reviewed("western_v1", "hi") is None

    def test_declared_provenance_splits_reviewed_and_machine(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit
        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)
        self._write_prototype_file(
            tmp_path, "buddhist_v1", 3,
            provenance={"reviewed": [], "machine_generated": ["hi"]},
        )

        result = coverage_audit.audit_tradition("buddhist_v1")
        assert result.translations_undeclared is False
        assert result.translations_machine_generated == 1
        assert coverage_audit.is_language_reviewed("buddhist_v1", "hi") is False

    def test_framework_coverage_index_is_one_when_balanced(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit
        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)
        for fid in coverage_audit.ALL_TRADITIONS:
            self._write_prototype_file(tmp_path, fid, 5)

        coverages = coverage_audit.audit_all()
        assert coverage_audit.framework_coverage_index(coverages) == pytest.approx(1.0)

    def test_framework_coverage_index_drops_when_imbalanced(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit
        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)
        fids = list(coverage_audit.ALL_TRADITIONS)
        for i, fid in enumerate(fids):
            self._write_prototype_file(tmp_path, fid, 20 if i == 0 else 5)

        coverages = coverage_audit.audit_all()
        assert coverage_audit.framework_coverage_index(coverages) < 1.0

    def test_coverage_report_shape(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit
        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)
        for fid in coverage_audit.ALL_TRADITIONS:
            self._write_prototype_file(tmp_path, fid, 3)

        report = coverage_audit.coverage_report()
        assert "framework_coverage_index" in report
        assert len(report["traditions"]) == len(coverage_audit.ALL_TRADITIONS)
        assert {"framework_id", "label", "prototype_count"} <= report["traditions"][0].keys()


# ── Upgrade 37: Translation review surfacing in Analyzer.analyze() ─────────

class TestTranslationReviewSurfacing:
    def test_english_has_no_translation_caveat(self):
        from ethiviz.api import Analyzer
        analyzer = Analyzer(use_semantic=False, frameworks=["western_v1"])
        result = analyzer.analyze(["Immigrants are ruining this country."])
        fs = next(f for f in result.framework_scores if f.framework_id == "western_v1")
        assert fs.raw_evidence["translation_reviewed"] is True
        assert not any("unreviewed" in w for w in fs.raw_evidence["warnings"])

    def test_undeclared_lens_flags_none_for_non_english(self):
        from ethiviz.api import Analyzer
        analyzer = Analyzer(use_semantic=False, frameworks=["western_v1"])
        result = analyzer.analyze(["Les immigrants détruisent ce pays."])
        fs = next(f for f in result.framework_scores if f.framework_id == "western_v1")
        assert fs.raw_evidence["translation_reviewed"] is None
        assert any("undeclared" in w for w in fs.raw_evidence["warnings"])

    def test_machine_generated_lens_flags_false_for_non_english(self):
        from ethiviz.api import Analyzer
        analyzer = Analyzer(use_semantic=False, frameworks=["buddhist_v1"])
        result = analyzer.analyze(["這些人本質上是暴力的。"])
        fs = next(f for f in result.framework_scores if f.framework_id == "buddhist_v1")
        assert fs.raw_evidence["translation_reviewed"] is False
        assert any("unreviewed" in w for w in fs.raw_evidence["warnings"])


# ── Upgrade 38 & 39: JobStore retention + audit-log ─────────────────────────

class TestJobStoreRetentionAndAuditLog:
    def _make_store(self):
        from ethiviz.storage.job_store import JobStore
        tmp = tempfile.mkdtemp()
        return JobStore(db_path=Path(tmp) / "test_jobs.db")

    def test_delete_job_removes_job_and_results(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.store_results(job_id, {"western_v1": {"overall_score": 0.4}})

        store.delete_job(job_id)

        assert store.get_job(job_id) is None
        assert store.get_results(job_id) == []

    def test_delete_job_leaves_a_deleted_audit_entry(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.delete_job(job_id)

        audit = store.get_audit_log(job_id)
        event_types = [row["event_type"] for row in audit]
        assert "deleted" in event_types

    def test_log_event_appends_custom_event(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.log_event(job_id, "exported", {"format": "html"})

        audit = store.get_audit_log(job_id)
        exported = [row for row in audit if row["event_type"] == "exported"]
        assert len(exported) == 1
        assert "html" in exported[0]["details"]

    def test_audit_log_accumulates_lifecycle_events(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.update_status(job_id, "processing")
        store.update_status(job_id, "completed")
        store.store_results(job_id, {"western_v1": {"overall_score": 0.1}})

        events = [row["event_type"] for row in store.get_audit_log(job_id)]
        assert events == [
            "created", "status_processing", "status_completed", "results_stored",
        ]
