import yaml


class TestReviewAndCalibrationWorkflow:
    def test_prototype_store_tracks_review_metadata(self, tmp_path, monkeypatch):
        from ethiviz.embeddings import prototype_store

        monkeypatch.setattr(prototype_store, "PROTOTYPES_DIR", tmp_path)

        payload = {
            "translation_provenance": {
                "reviewed": ["fr"],
                "reviewed_by": {"fr": "analyst-a"},
                "reviewed_at": {"fr": "2026-01-01T00:00:00Z"},
                "community_consent": {
                    "status": "approved",
                    "organization": "Indigenous Language Council",
                },
            },
            "prototypes": [{
                "id": "p1",
                "text": "Original text",
                "translations": {"fr": "Texte original"},
            }],
        }
        (tmp_path / "indigenous_v1_prototypes.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")

        store = prototype_store.PrototypeStore()
        loaded = store.load("indigenous_v1", "fr")

        assert loaded[0]["translation_review_status"] == "reviewed"
        assert loaded[0]["reviewed_by"] == "analyst-a"
        assert loaded[0]["community_consent"]["status"] == "approved"
        assert store.validate_bundle("indigenous_v1", require_community_consent=True)["valid"] is True

    def test_coverage_audit_reports_review_state_and_consent(self, tmp_path, monkeypatch):
        from ethiviz.frameworks import coverage_audit

        monkeypatch.setattr(coverage_audit, "PROTOTYPES_DIR", tmp_path)

        payload = {
            "translation_provenance": {
                "reviewed": ["fr"],
                "machine_generated": ["es"],
                "community_consent": {"status": "approved"},
            },
            "prototypes": [{
                "id": "p1",
                "text": "Original",
                "translations": {"fr": "Français", "es": "Español"},
            }],
        }
        (tmp_path / "buddhist_v1_prototypes.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")

        result = coverage_audit.audit_tradition("buddhist_v1")
        assert result.review_status_by_language["fr"] == "reviewed"
        assert result.review_status_by_language["es"] == "machine_generated"
        assert result.community_consent_present is True

    def test_calibration_validation_reports_brier_and_reliability(self):
        from ethiviz.evaluation.calibration_validation import evaluate_calibration

        result = evaluate_calibration([0.1, 0.8, 0.4, 0.9], [0, 1, 0, 1], lens_id="western_v1")

        assert result.sample_count == 4
        assert 0.0 <= result.brier_score <= 1.0
        assert result.calibration_status in {"reliable", "acceptable", "poor"}
        assert result.to_dict()["lens_id"] == "western_v1"
