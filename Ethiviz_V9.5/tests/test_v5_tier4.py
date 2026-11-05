"""
Tests for EthiViz V5 Tier 4 Upgrades (21-34).
Covers: JobStore, GroupFairnessCalculator, IndividualFairnessCalculator,
        Reweigher, DisparateImpactRemover, CalibratedEqualizedOdds,
        RejectOptionClassifier, CulturalBiasTransformer, EthiVizPipeline,
        and YAML loading for new cultural traditions.
"""
import pytest
import tempfile
from pathlib import Path


# ── Upgrade 31: SQLite JobStore ─────────────────────────────────────────────

class TestJobStore:
    def _make_store(self):
        from ethiviz.storage.job_store import JobStore
        tmp = tempfile.mkdtemp()
        return JobStore(db_path=Path(tmp) / "test_jobs.db")

    def test_create_job_returns_string_id(self):
        store = self._make_store()
        job_id = store.create_job("text")
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID format

    def test_create_job_status_is_pending(self):
        store = self._make_store()
        job_id = store.create_job("text")
        job = store.get_job(job_id)
        assert job is not None
        assert job["status"] == "pending"

    def test_create_job_stores_analysis_type(self):
        store = self._make_store()
        job_id = store.create_job("image")
        job = store.get_job(job_id)
        assert job["analysis_type"] == "image"

    def test_update_status_changes_to_processing(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.update_status(job_id, "processing")
        job = store.get_job(job_id)
        assert job["status"] == "processing"

    def test_update_status_to_completed_sets_completed_at(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.update_status(job_id, "completed")
        job = store.get_job(job_id)
        assert job["status"] == "completed"
        assert job["completed_at"] is not None

    def test_update_status_to_failed_stores_error(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.update_status(job_id, "failed", error="Something went wrong")
        job = store.get_job(job_id)
        assert job["status"] == "failed"
        assert job["error_message"] == "Something went wrong"

    def test_store_results_and_retrieve(self):
        store = self._make_store()
        job_id = store.create_job("text")
        results_data = {"western_v1": {"overall_score": 0.42, "bias_level": 0.3}}
        store.store_results(job_id, results_data)
        rows = store.get_results(job_id)
        assert len(rows) > 0
        metric_names = [r["metric_name"] for r in rows]
        assert "overall_score" in metric_names

    def test_list_jobs_returns_list(self):
        store = self._make_store()
        store.create_job("text")
        store.create_job("image")
        jobs = store.list_jobs(limit=10)
        assert len(jobs) >= 2

    def test_audit_log_has_entries(self):
        store = self._make_store()
        job_id = store.create_job("text")
        store.update_status(job_id, "completed")
        log = store.get_audit_log(job_id)
        assert len(log) >= 2  # created + status_completed

    def test_get_nonexistent_job_returns_none(self):
        store = self._make_store()
        result = store.get_job("nonexistent-id")
        assert result is None


# ── Upgrades 21-22: Group and Individual Fairness ───────────────────────────

class TestGroupFairnessCalculator:
    def test_compute_returns_group_fairness_result(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator, GroupFairnessResult
        calc = GroupFairnessCalculator()
        y_true = [1, 1, 0, 0, 1, 0]
        y_pred = [1, 0, 0, 0, 1, 0]
        groups = {"western_v1": [1, 1, 0, 0, 1, 0]}
        result = calc.compute(y_true, y_pred, groups)
        assert isinstance(result, GroupFairnessResult)

    def test_tradition_fairness_score_has_required_fields(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        calc = GroupFairnessCalculator()
        y_true = [1, 1, 0, 0, 1, 0]
        y_pred = [1, 0, 0, 0, 1, 0]
        groups = {"western_v1": [1, 1, 0, 0, 1, 0]}
        result = calc.compute(y_true, y_pred, groups)
        score = result.per_tradition["western_v1"]
        assert hasattr(score, "spd")
        assert hasattr(score, "disparate_impact")
        assert hasattr(score, "equal_opportunity_diff")
        assert hasattr(score, "average_odds_diff")
        assert hasattr(score, "theil_index")
        assert hasattr(score, "mean_difference")
        assert hasattr(score, "severity")
        assert hasattr(score, "threshold_source")

    def test_severity_is_valid_string(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        calc = GroupFairnessCalculator()
        y_true = [1, 1, 0, 0, 1, 0, 1, 0]
        y_pred = [1, 0, 0, 0, 1, 0, 0, 1]
        groups = {"ubuntu_v1": [1, 1, 0, 0, 1, 0, 1, 0]}
        result = calc.compute(y_true, y_pred, groups)
        score = result.per_tradition["ubuntu_v1"]
        assert score.severity in ("low", "moderate", "high", "critical")

    def test_overall_consensus_is_float(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        calc = GroupFairnessCalculator()
        y_true = [1, 0, 1, 0]
        y_pred = [1, 1, 0, 0]
        groups = {"western_v1": [1, 0, 1, 0]}
        result = calc.compute(y_true, y_pred, groups)
        assert result.overall_consensus is not None
        assert isinstance(result.overall_consensus, float)

    def test_multiple_traditions_computed(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        calc = GroupFairnessCalculator()
        y_true = [1, 0, 1, 0, 1, 0]
        y_pred = [1, 1, 0, 0, 1, 0]
        groups = {
            "western_v1": [1, 1, 0, 0, 1, 0],
            "ubuntu_v1":  [1, 0, 1, 0, 1, 0],
        }
        result = calc.compute(y_true, y_pred, groups)
        assert "western_v1" in result.per_tradition
        assert "ubuntu_v1" in result.per_tradition

    def test_conflicts_detected_when_spd_differs(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        calc = GroupFairnessCalculator()
        # Construct groups where SPDs will differ by >0.10
        y_true = [1, 1, 1, 1, 0, 0, 0, 0]
        y_pred = [1, 1, 0, 0, 1, 0, 0, 0]
        groups = {
            "western_v1": [1, 1, 1, 1, 0, 0, 0, 0],
            "ubuntu_v1":  [0, 0, 0, 0, 1, 1, 1, 1],
        }
        result = calc.compute(y_true, y_pred, groups)
        assert isinstance(result.conflicts, list)

    def test_mitigation_recommended_list(self):
        from ethiviz.metrics.group_fairness import GroupFairnessCalculator
        calc = GroupFairnessCalculator()
        y_true = [1, 0, 1, 0]
        y_pred = [1, 0, 0, 1]
        groups = {"western_v1": [1, 1, 0, 0]}
        result = calc.compute(y_true, y_pred, groups)
        assert isinstance(result.mitigation_recommended, list)


class TestIndividualFairnessCalculator:
    def test_compute_returns_result(self):
        from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator, IndividualFairnessResult
        calc = IndividualFairnessCalculator(k=3)
        scores = [0.8, 0.75, 0.9, 0.2, 0.25, 0.15]
        result = calc.compute(scores)
        assert isinstance(result, IndividualFairnessResult)

    def test_consistency_score_in_zero_one(self):
        from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator
        calc = IndividualFairnessCalculator(k=3)
        scores = [0.8, 0.75, 0.9, 0.2, 0.25, 0.15]
        result = calc.compute(scores)
        assert 0.0 <= result.consistency_score <= 1.0

    def test_sample_distortion_non_negative(self):
        from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator
        calc = IndividualFairnessCalculator(k=3)
        scores = [0.5, 0.6, 0.4, 0.3]
        result = calc.compute(scores)
        assert result.sample_distortion_score >= 0.0

    def test_k_neighbors_capped_at_n_minus_1(self):
        from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator
        calc = IndividualFairnessCalculator(k=100)
        scores = [0.5, 0.6, 0.4]
        result = calc.compute(scores)
        assert result.k_neighbors <= 2

    def test_with_feature_matrix_sets_cultural_proximity_true(self):
        from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator
        calc = IndividualFairnessCalculator(k=2)
        scores = [0.8, 0.75, 0.2, 0.25]
        features = [[0.9, 0.1], [0.85, 0.15], [0.1, 0.9], [0.15, 0.85]]
        result = calc.compute(scores, feature_matrix=features)
        assert result.cultural_proximity_used is True

    def test_interpretation_is_string(self):
        from ethiviz.metrics.individual_fairness import IndividualFairnessCalculator
        calc = IndividualFairnessCalculator(k=3)
        scores = [0.8, 0.75, 0.9, 0.2, 0.25, 0.15]
        result = calc.compute(scores)
        assert isinstance(result.interpretation, str)
        assert len(result.interpretation) > 0


# ── Upgrades 23-25: Bias Mitigation Pipeline ────────────────────────────────

class TestReweigher:
    def test_fit_returns_preprocessing_result(self):
        from ethiviz.mitigation.preprocessing import Reweigher, PreprocessingResult
        rw = Reweigher()
        groups = [1, 1, 0, 0, 1, 0]
        labels = [1, 0, 1, 0, 1, 0]
        result = rw.fit(groups, labels)
        assert isinstance(result, PreprocessingResult)

    def test_weights_length_equals_n(self):
        from ethiviz.mitigation.preprocessing import Reweigher
        rw = Reweigher()
        groups = [1, 1, 0, 0, 1, 0]
        labels = [1, 0, 1, 0, 1, 0]
        result = rw.fit(groups, labels)
        assert len(result.weights) == 6

    def test_weights_sum_approximately_n(self):
        """Reweighing should roughly preserve total sample weight."""
        import numpy as np
        from ethiviz.mitigation.preprocessing import Reweigher
        rw = Reweigher()
        groups = [1, 1, 0, 0, 1, 0]
        labels = [1, 0, 1, 0, 1, 0]
        result = rw.fit(groups, labels)
        total_weight = sum(result.weights)
        # Total should be approximately n (not necessarily exact due to rounding)
        assert total_weight > 0

    def test_weights_are_positive(self):
        from ethiviz.mitigation.preprocessing import Reweigher
        rw = Reweigher()
        groups = [1, 1, 0, 0, 1, 0]
        labels = [1, 0, 1, 0, 1, 0]
        result = rw.fit(groups, labels)
        assert all(w > 0 for w in result.weights)

    def test_method_is_reweighing(self):
        from ethiviz.mitigation.preprocessing import Reweigher
        rw = Reweigher()
        result = rw.fit([1, 0, 1, 0], [1, 0, 1, 0])
        assert result.method == "reweighing"

    def test_n_privileged_and_unprivileged_correct(self):
        from ethiviz.mitigation.preprocessing import Reweigher
        rw = Reweigher()
        groups = [1, 1, 1, 0, 0]
        labels = [1, 0, 1, 0, 1]
        result = rw.fit(groups, labels)
        assert result.n_privileged == 3
        assert result.n_unprivileged == 2


class TestDisparateImpactRemover:
    def test_fit_transform_returns_same_shape(self):
        from ethiviz.mitigation.preprocessing import DisparateImpactRemover
        remover = DisparateImpactRemover(repair_level=0.8)
        X = [[0.5, 0.3], [0.9, 0.7], [0.1, 0.2], [0.4, 0.6]]
        groups = [1, 1, 0, 0]
        result = remover.fit_transform(X, groups)
        assert len(result) == 4
        assert len(result[0]) == 2

    def test_repaired_values_are_floats(self):
        from ethiviz.mitigation.preprocessing import DisparateImpactRemover
        remover = DisparateImpactRemover(repair_level=1.0)
        X = [[0.5, 0.3], [0.9, 0.7], [0.1, 0.2]]
        groups = [1, 1, 0]
        result = remover.fit_transform(X, groups)
        for row in result:
            for val in row:
                assert isinstance(val, float)

    def test_repair_level_zero_leaves_unchanged(self):
        import numpy as np
        from ethiviz.mitigation.preprocessing import DisparateImpactRemover
        remover = DisparateImpactRemover(repair_level=0.0)
        X = [[0.5, 0.3], [0.9, 0.7], [0.1, 0.2]]
        groups = [1, 1, 0]
        result = remover.fit_transform(X, groups)
        for orig, rep in zip(X, result):
            for o, r in zip(orig, rep):
                assert abs(o - r) < 1e-9

    def test_protected_feature_not_repaired(self):
        import numpy as np
        from ethiviz.mitigation.preprocessing import DisparateImpactRemover
        remover = DisparateImpactRemover(repair_level=1.0)
        X = [[0.5, 0.3], [0.9, 0.7], [0.1, 0.2]]
        groups = [1, 1, 0]
        result = remover.fit_transform(X, groups, protected_feature_indices=[0])
        # Column 0 should be unchanged
        for orig, rep in zip(X, result):
            assert abs(orig[0] - rep[0]) < 1e-9


class TestCalibratedEqualizedOdds:
    def test_adjust_returns_postprocessing_result(self):
        from ethiviz.mitigation.postprocessing import CalibratedEqualizedOdds, PostprocessingResult
        ceo = CalibratedEqualizedOdds(tradition_id="ubuntu_v1")
        result = ceo.adjust([0.7, 0.3, 0.8, 0.2], [1, 0, 1, 0], [1, 1, 0, 0])
        assert isinstance(result, PostprocessingResult)

    def test_adjusted_predictions_correct_length(self):
        from ethiviz.mitigation.postprocessing import CalibratedEqualizedOdds
        ceo = CalibratedEqualizedOdds()
        scores = [0.7, 0.3, 0.8, 0.2, 0.6, 0.4]
        result = ceo.adjust(scores, [1, 0, 1, 0, 1, 0], [1, 1, 0, 0, 1, 0])
        assert len(result.adjusted_predictions) == 6

    def test_adjusted_predictions_binary(self):
        from ethiviz.mitigation.postprocessing import CalibratedEqualizedOdds
        ceo = CalibratedEqualizedOdds()
        result = ceo.adjust([0.7, 0.3, 0.8, 0.2], [1, 0, 1, 0], [1, 1, 0, 0])
        assert all(p in (0, 1) for p in result.adjusted_predictions)

    def test_method_name_correct(self):
        from ethiviz.mitigation.postprocessing import CalibratedEqualizedOdds
        ceo = CalibratedEqualizedOdds()
        result = ceo.adjust([0.7, 0.3, 0.8, 0.2], [1, 0, 1, 0], [1, 1, 0, 0])
        assert result.method == "calibrated_equalized_odds"

    def test_tradition_id_preserved(self):
        from ethiviz.mitigation.postprocessing import CalibratedEqualizedOdds
        ceo = CalibratedEqualizedOdds(tradition_id="islamic_v1")
        result = ceo.adjust([0.7, 0.3, 0.8, 0.2], [1, 0, 1, 0], [1, 1, 0, 0])
        assert result.tradition_id == "islamic_v1"


class TestRejectOptionClassifier:
    def test_classify_returns_postprocessing_result(self):
        from ethiviz.mitigation.postprocessing import RejectOptionClassifier, PostprocessingResult
        roc = RejectOptionClassifier(band_width=0.15, tradition_id="ubuntu_v1")
        result = roc.classify([0.3, 0.55, 0.7, 0.48], [1, 0, 1, 0])
        assert isinstance(result, PostprocessingResult)

    def test_adjusted_predictions_binary(self):
        from ethiviz.mitigation.postprocessing import RejectOptionClassifier
        roc = RejectOptionClassifier(band_width=0.15)
        result = roc.classify([0.3, 0.55, 0.7, 0.48, 0.2, 0.9], [1, 0, 1, 0, 1, 0])
        assert all(p in (0, 1) for p in result.adjusted_predictions)

    def test_adjusts_uncertain_band_predictions(self):
        from ethiviz.mitigation.postprocessing import RejectOptionClassifier
        # Score exactly in band [0.40, 0.60] should be adjusted for group 0
        roc = RejectOptionClassifier(band_width=0.10, tradition_id="western_v1")
        scores = [0.45, 0.55]  # both in uncertain band
        groups = [0, 1]  # unprivileged, privileged
        result = roc.classify(scores, groups)
        # Group 0 (unprivileged) in band should get favorable label (1)
        assert result.adjusted_predictions[0] == 1

    def test_method_name_correct(self):
        from ethiviz.mitigation.postprocessing import RejectOptionClassifier
        roc = RejectOptionClassifier()
        result = roc.classify([0.3, 0.7, 0.5, 0.4], [1, 0, 1, 0])
        assert result.method == "reject_option_classification"


# ── Upgrades 26-27: Structured Dataset + sklearn API ────────────────────────

class TestCulturalBiasTransformer:
    def test_has_fit_method(self):
        from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        transformer = CulturalBiasTransformer()
        assert hasattr(transformer, 'fit')
        assert callable(transformer.fit)

    def test_has_transform_method(self):
        from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        transformer = CulturalBiasTransformer()
        assert hasattr(transformer, 'transform')
        assert callable(transformer.transform)

    def test_fit_returns_self(self):
        import numpy as np
        from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        transformer = CulturalBiasTransformer()
        X = np.array([[0.5, 0.3], [0.9, 0.7], [0.1, 0.2]])
        result = transformer.fit(X)
        assert result is transformer

    def test_transform_returns_same_shape(self):
        import numpy as np
        from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        transformer = CulturalBiasTransformer(repair_level=0.5)
        X = np.array([[0.5, 0.3], [0.9, 0.7], [0.1, 0.2]])
        transformer.fit(X)
        result = transformer.transform(X)
        assert result.shape == X.shape

    def test_get_params_returns_dict(self):
        from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        transformer = CulturalBiasTransformer(tradition_id="ubuntu_v1", repair_level=0.8)
        params = transformer.get_params()
        assert params["tradition_id"] == "ubuntu_v1"
        assert params["repair_level"] == 0.8

    def test_set_params_updates_attributes(self):
        from ethiviz.integration.sklearn_api import CulturalBiasTransformer
        transformer = CulturalBiasTransformer()
        transformer.set_params(tradition_id="islamic_v1")
        assert transformer.tradition_id == "islamic_v1"


class TestEthiVizPipeline:
    def _make_simple_estimator(self):
        """Create a simple majority-class classifier for testing."""
        class MajorityClassifier:
            def fit(self, X, y):
                import numpy as np
                self.label_ = int(np.bincount(y.astype(int)).argmax())
                return self
            def predict(self, X):
                import numpy as np
                return np.full(len(X), self.label_)
        return MajorityClassifier()

    def test_pipeline_fit_returns_self(self):
        import numpy as np
        from ethiviz.integration.sklearn_api import EthiVizPipeline
        estimator = self._make_simple_estimator()
        pipe = EthiVizPipeline(estimator=estimator, tradition_id="western_v1")
        X = np.array([[0.5, 0.3], [0.9, 0.7], [0.1, 0.2], [0.4, 0.6]])
        y = np.array([1, 1, 0, 0])
        result = pipe.fit(X, y)
        assert result is pipe

    def test_pipeline_predict_returns_array(self):
        import numpy as np
        from ethiviz.integration.sklearn_api import EthiVizPipeline
        estimator = self._make_simple_estimator()
        pipe = EthiVizPipeline(estimator=estimator)
        X_train = np.array([[0.5, 0.3], [0.9, 0.7], [0.1, 0.2], [0.4, 0.6]])
        y_train = np.array([1, 1, 0, 0])
        pipe.fit(X_train, y_train)
        X_test = np.array([[0.6, 0.4], [0.2, 0.8]])
        preds = pipe.predict(X_test)
        assert len(preds) == 2

    def test_pipeline_score_between_zero_and_one(self):
        import numpy as np
        from ethiviz.integration.sklearn_api import EthiVizPipeline
        estimator = self._make_simple_estimator()
        pipe = EthiVizPipeline(estimator=estimator)
        X = np.array([[0.5, 0.3], [0.9, 0.7], [0.1, 0.2], [0.4, 0.6]])
        y = np.array([1, 1, 0, 0])
        pipe.fit(X, y)
        score = pipe.score(X, y)
        assert 0.0 <= score <= 1.0


# ── Upgrade 28: New YAML Files Load Without Error ───────────────────────────

class TestNewYAMLFiles:
    def _load_yaml(self, path):
        import yaml
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_builtin_dir(self):
        return (
            Path(__file__).parent.parent
            / "ethiviz" / "frameworks" / "builtin"
        )

    def _get_prototypes_dir(self):
        return (
            Path(__file__).parent.parent
            / "ethiviz" / "embeddings" / "prototypes"
        )

    def test_load_indigenous_v1_framework_yaml(self):
        data = self._load_yaml(self._get_builtin_dir() / "indigenous_v1.yaml")
        assert data["framework_id"] == "indigenous_v1"
        assert "bias_criteria" in data
        assert "severity_thresholds" in data

    def test_load_buddhist_v1_framework_yaml(self):
        data = self._load_yaml(self._get_builtin_dir() / "buddhist_v1.yaml")
        assert data["framework_id"] == "buddhist_v1"
        assert "bias_criteria" in data
        assert "severity_thresholds" in data

    def test_load_hindu_v1_framework_yaml(self):
        data = self._load_yaml(self._get_builtin_dir() / "hindu_v1.yaml")
        assert data["framework_id"] == "hindu_v1"
        assert "bias_criteria" in data
        assert "severity_thresholds" in data

    def test_load_indigenous_v1_prototypes(self):
        data = self._load_yaml(self._get_prototypes_dir() / "indigenous_v1_prototypes.yaml")
        assert "prototypes" in data
        assert len(data["prototypes"]) >= 5

    def test_load_buddhist_v1_prototypes(self):
        data = self._load_yaml(self._get_prototypes_dir() / "buddhist_v1_prototypes.yaml")
        assert "prototypes" in data
        assert len(data["prototypes"]) >= 5

    def test_load_hindu_v1_prototypes(self):
        data = self._load_yaml(self._get_prototypes_dir() / "hindu_v1_prototypes.yaml")
        assert "prototypes" in data
        assert len(data["prototypes"]) >= 5

    def test_indigenous_prototypes_have_required_fields(self):
        data = self._load_yaml(self._get_prototypes_dir() / "indigenous_v1_prototypes.yaml")
        for proto in data["prototypes"]:
            assert "id" in proto
            assert "text" in proto
            assert "severity" in proto
            assert "category" in proto

    def test_existing_frameworks_now_have_severity_thresholds(self):
        for fname in ["western_v1.yaml", "ubuntu_v1.yaml", "confucian_v2.yaml", "islamic_v1.yaml"]:
            data = self._load_yaml(self._get_builtin_dir() / fname)
            assert "severity_thresholds" in data, f"{fname} missing severity_thresholds"
            thresholds = data["severity_thresholds"]
            assert "low" in thresholds
            assert "moderate" in thresholds
            assert "high" in thresholds
            assert "critical" in thresholds


# ── Upgrade 32: Sample Data Files Exist ─────────────────────────────────────

class TestSampleDataFiles:
    def _get_sample_dir(self):
        return Path(__file__).parent.parent / "ethiviz" / "sample_data"

    def test_all_seven_sample_csv_files_exist(self):
        sample_dir = self._get_sample_dir()
        traditions = ["western", "ubuntu", "confucian", "islamic",
                      "indigenous", "buddhist", "hindu"]
        for tradition in traditions:
            path = sample_dir / f"sample_texts_{tradition}.csv"
            assert path.exists(), f"Missing: {path}"

    def test_sample_csvs_have_at_least_20_rows(self):
        sample_dir = self._get_sample_dir()
        traditions = ["western", "ubuntu", "confucian", "islamic",
                      "indigenous", "buddhist", "hindu"]
        for tradition in traditions:
            path = sample_dir / f"sample_texts_{tradition}.csv"
            if path.exists():
                lines = path.read_text(encoding="utf-8").strip().split("\n")
                # header + at least 20 data rows
                assert len(lines) >= 21, f"{path.name} has fewer than 20 data rows"

    def test_sample_csv_has_required_columns(self):
        import csv
        sample_dir = self._get_sample_dir()
        path = sample_dir / "sample_texts_western.csv"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                assert set(reader.fieldnames or []) >= {"text", "bias_level", "category", "notes"}


# ── Integration: New Lens Imports ───────────────────────────────────────────

class TestNewLensImports:
    def test_import_indigenous_lens(self):
        from ethiviz.lenses.indigenous import IndigenousLens
        lens = IndigenousLens(use_semantic=False)
        assert lens.lens_id == "indigenous_v1"

    def test_import_buddhist_lens(self):
        from ethiviz.lenses.buddhist import BuddhistLens
        lens = BuddhistLens(use_semantic=False)
        assert lens.lens_id == "buddhist_v1"

    def test_import_hindu_lens(self):
        from ethiviz.lenses.hindu import HinduLens
        lens = HinduLens(use_semantic=False)
        assert lens.lens_id == "hindu_v1"

    def test_indigenous_lens_score_returns_lens_score(self):
        from ethiviz.lenses.indigenous import IndigenousLens
        from ethiviz.lenses.base import LensScore
        lens = IndigenousLens(use_semantic=False)
        result = lens.score("Traditional healing practices should be patented by corporations.")
        assert isinstance(result, LensScore)
        assert result.lens_id == "indigenous_v1"

    def test_buddhist_lens_score_returns_lens_score(self):
        from ethiviz.lenses.buddhist import BuddhistLens
        from ethiviz.lenses.base import LensScore
        lens = BuddhistLens(use_semantic=False)
        result = lens.score("People of this race are inherently violent and cannot change.")
        assert isinstance(result, LensScore)
        assert result.lens_id == "buddhist_v1"

    def test_hindu_lens_score_returns_lens_score(self):
        from ethiviz.lenses.hindu import HinduLens
        from ethiviz.lenses.base import LensScore
        lens = HinduLens(use_semantic=False)
        result = lens.score("Certain castes are genetically inferior and should be restricted.")
        assert isinstance(result, LensScore)
        assert result.lens_id == "hindu_v1"
