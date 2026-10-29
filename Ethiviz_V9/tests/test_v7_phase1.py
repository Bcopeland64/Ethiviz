"""
Tests for EthiViz V7 Phase 1 — Security Foundation (Upgrades 40-45).
Covers: JobStore schema migration onto a pre-existing DB, the tamper-evident
audit hash chain, job-ownership scoping, and the API-key validation logic
used by Scripts/api_server.py's auth gate.
"""
import hashlib
import sqlite3
import tempfile
import threading
import zipfile
from pathlib import Path

import pytest


# ── Migration onto a pre-Phase-1 database ───────────────────────────────────

class TestSchemaMigration:
    def _make_legacy_db(self, tmp_path: Path) -> Path:
        """Hand-build a DB matching the schema *before* Upgrades 40/45 added
        owner_key_hash/prev_hash/row_hash, to prove JobStore migrates an
        already-deployed jobs.db in place rather than assuming a fresh one."""
        db_path = tmp_path / "legacy_jobs.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                analysis_type TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                error_message TEXT
            );
            CREATE TABLE results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(job_id),
                framework_id TEXT, metric_name TEXT, value REAL,
                confidence_lower REAL, confidence_upper REAL, extra_json TEXT
            );
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL, event_type TEXT, timestamp TEXT, details TEXT
            );
        """)
        conn.execute(
            "INSERT INTO jobs (job_id, status, analysis_type, created_at) VALUES (?,?,?,?)",
            ("legacy-job-1", "completed", "text", "2026-01-01T00:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO audit_log (job_id, event_type, timestamp, details) VALUES (?,?,?,?)",
            ("legacy-job-1", "created", "2026-01-01T00:00:00+00:00", '{"analysis_type": "text"}'),
        )
        conn.commit()
        conn.close()
        return db_path

    def test_new_columns_added_without_data_loss(self, tmp_path):
        from ethiviz.storage.job_store import JobStore
        db_path = self._make_legacy_db(tmp_path)

        store = JobStore(db_path=db_path)

        job = store.get_job("legacy-job-1")
        assert job is not None
        assert job["status"] == "completed"
        assert job["owner_key_hash"] is None  # new column, legacy row -> NULL

        audit = store.get_audit_log("legacy-job-1")
        assert len(audit) == 1
        assert audit[0]["event_type"] == "created"
        assert audit[0]["row_hash"] is None  # legacy row predates the hash chain

    def test_migration_is_idempotent(self, tmp_path):
        """Re-instantiating JobStore against the same file (e.g. server
        restart) must not error or duplicate the ALTER TABLE."""
        from ethiviz.storage.job_store import JobStore
        db_path = self._make_legacy_db(tmp_path)
        JobStore(db_path=db_path)
        store2 = JobStore(db_path=db_path)  # should not raise
        assert store2.get_job("legacy-job-1") is not None


# ── Tamper-evident audit chain (Upgrade 45) ─────────────────────────────────

class TestAuditChain:
    def _make_store(self, tmp_path):
        from ethiviz.storage.job_store import JobStore
        return JobStore(db_path=tmp_path / "jobs.db")

    def test_chain_valid_after_normal_lifecycle(self, tmp_path):
        store = self._make_store(tmp_path)
        job_id = store.create_job("text")
        store.update_status(job_id, "processing")
        store.update_status(job_id, "completed")
        store.log_event(job_id, "exported", {"format": "json"})
        store.delete_job(job_id)

        result = store.verify_audit_chain()
        assert result == {"valid": True, "broken_at_id": None}

    def test_tampering_with_a_row_breaks_the_chain(self, tmp_path):
        store = self._make_store(tmp_path)
        job_id = store.create_job("text")
        store.update_status(job_id, "completed")

        with store._backend._conn() as conn:
            row = conn.execute(
                "SELECT id FROM audit_log WHERE job_id=? AND event_type='created'", (job_id,)
            ).fetchone()
            conn.execute(
                "UPDATE audit_log SET details=? WHERE id=?",
                ('{"tampered": true}', row["id"]),
            )

        result = store.verify_audit_chain()
        assert result["valid"] is False
        assert result["broken_at_id"] == row["id"]

    def test_deleting_a_row_breaks_the_chain(self, tmp_path):
        store = self._make_store(tmp_path)
        job_id = store.create_job("text")
        store.update_status(job_id, "processing")
        store.update_status(job_id, "completed")

        with store._backend._conn() as conn:
            mid_row = conn.execute(
                "SELECT id FROM audit_log WHERE job_id=? AND event_type='status_processing'",
                (job_id,),
            ).fetchone()
            conn.execute("DELETE FROM audit_log WHERE id=?", (mid_row["id"],))

        result = store.verify_audit_chain()
        assert result["valid"] is False

    def test_concurrent_writers_produce_a_single_valid_chain(self, tmp_path):
        """Regression guard for the fork risk described in _write_audit's
        docstring: without the lock, two threads could both read the same
        'last' row_hash and chain off it."""
        store = self._make_store(tmp_path)
        job_id = store.create_job("text")
        errors = []

        def worker():
            try:
                for i in range(10):
                    store.log_event(job_id, f"event_{i}", {"i": i})
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        result = store.verify_audit_chain()
        assert result["valid"] is True


# ── Job ownership scoping (Upgrade 40) ──────────────────────────────────────

class TestJobOwnership:
    def _make_store(self, tmp_path):
        from ethiviz.storage.job_store import JobStore
        return JobStore(db_path=tmp_path / "jobs.db")

    def test_owner_key_hash_round_trips(self, tmp_path):
        store = self._make_store(tmp_path)
        owner = hashlib.sha256(b"caller-key").hexdigest()
        job_id = store.create_job("text", owner_key_hash=owner)

        job = store.get_job(job_id)
        assert job["owner_key_hash"] == owner

    def test_unowned_job_has_null_owner(self, tmp_path):
        store = self._make_store(tmp_path)
        job_id = store.create_job("text")
        assert store.get_job(job_id)["owner_key_hash"] is None

    def test_list_jobs_scopes_to_owner_plus_unowned(self, tmp_path):
        store = self._make_store(tmp_path)
        owner_a = hashlib.sha256(b"key-a").hexdigest()
        owner_b = hashlib.sha256(b"key-b").hexdigest()

        job_a = store.create_job("text", owner_key_hash=owner_a)
        job_b = store.create_job("text", owner_key_hash=owner_b)
        job_legacy = store.create_job("text", owner_key_hash=None)

        listed_ids = {j["job_id"] for j in store.list_jobs(owner_key_hash=owner_a)}
        assert job_a in listed_ids
        assert job_legacy in listed_ids
        assert job_b not in listed_ids

    def test_list_jobs_unscoped_when_owner_not_given(self, tmp_path):
        store = self._make_store(tmp_path)
        store.create_job("text", owner_key_hash=hashlib.sha256(b"key-a").hexdigest())
        store.create_job("text", owner_key_hash=hashlib.sha256(b"key-b").hexdigest())

        assert len(store.list_jobs()) == 2


# ── Upload quota (Upgrade 43) ────────────────────────────────────────────────

class TestUploadQuota:
    def _make_store(self, tmp_path):
        from ethiviz.storage.job_store import JobStore
        return JobStore(db_path=tmp_path / "jobs.db")

    def test_usage_accumulates_same_day(self, tmp_path):
        store = self._make_store(tmp_path)
        total1 = store.record_upload("key-a", 1000)
        total2 = store.record_upload("key-a", 500)
        assert total1 == 1000
        assert total2 == 1500
        assert store.get_upload_usage("key-a") == 1500

    def test_usage_is_isolated_per_key(self, tmp_path):
        store = self._make_store(tmp_path)
        store.record_upload("key-a", 1000)
        assert store.get_upload_usage("key-b") == 0

    def test_usage_zero_before_any_upload(self, tmp_path):
        store = self._make_store(tmp_path)
        assert store.get_upload_usage("never-uploaded") == 0


# ── API-key validation logic (Upgrade 40) ───────────────────────────────────
# Tested as a pure function, independent of Flask app construction — see
# Scripts/api_server.py's _validate_api_key docstring.

class TestApiKeyValidation:
    def _import_validator(self):
        import sys
        import os
        scripts_dir = str(Path(__file__).resolve().parent.parent / "Scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import api_server
        return api_server._validate_api_key

    def test_correct_bearer_token_matches(self):
        validate = self._import_validator()
        key_hash = hashlib.sha256(b"my-secret-key").hexdigest()
        assert validate("Bearer my-secret-key", {key_hash}) == key_hash

    def test_wrong_token_does_not_match(self):
        validate = self._import_validator()
        key_hash = hashlib.sha256(b"my-secret-key").hexdigest()
        assert validate("Bearer wrong-key", {key_hash}) is None

    def test_missing_header_rejected(self):
        validate = self._import_validator()
        key_hash = hashlib.sha256(b"my-secret-key").hexdigest()
        assert validate(None, {key_hash}) is None

    def test_non_bearer_scheme_rejected(self):
        validate = self._import_validator()
        key_hash = hashlib.sha256(b"my-secret-key").hexdigest()
        assert validate("Basic my-secret-key", {key_hash}) is None

    def test_empty_bearer_token_rejected(self):
        validate = self._import_validator()
        key_hash = hashlib.sha256(b"my-secret-key").hexdigest()
        assert validate("Bearer ", {key_hash}) is None

    def test_no_configured_keys_never_matches(self):
        validate = self._import_validator()
        assert validate("Bearer anything", set()) is None


# ── Upload content verification (Upgrade 43) ────────────────────────────────

class TestUploadContentVerification:
    def _import_verifiers(self):
        import sys
        scripts_dir = str(Path(__file__).resolve().parent.parent / "Scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import api_server
        return api_server._verify_image_content, api_server._verify_text_content

    def test_real_png_passes_as_png(self, tmp_path):
        verify_image, _ = self._import_verifiers()
        # The 8-byte PNG signature plus padding is enough for filetype's
        # magic-byte detection without needing a full valid image.
        path = tmp_path / "fake.png"
        path.write_bytes(bytes.fromhex("89504e470d0a1a0a") + b"\x00" * 32)
        assert verify_image(str(path), "png") is True

    def test_text_disguised_as_png_fails(self, tmp_path):
        verify_image, _ = self._import_verifiers()
        path = tmp_path / "not_really.png"
        path.write_text("this is just plain text, not an image")
        assert verify_image(str(path), "png") is False

    def test_plain_csv_passes(self, tmp_path):
        _, verify_text = self._import_verifiers()
        path = tmp_path / "data.csv"
        path.write_text("col1,col2\n1,2\n")
        assert verify_text(str(path), "csv") is True

    def test_binary_disguised_as_csv_fails(self, tmp_path):
        _, verify_text = self._import_verifiers()
        path = tmp_path / "data.csv"
        path.write_bytes(b"\x00\x01\x02\x03binary garbage")
        assert verify_text(str(path), "csv") is False

    def test_xlsx_requires_zip_signature(self, tmp_path):
        _, verify_text = self._import_verifiers()
        real = tmp_path / "real.xlsx"
        with zipfile.ZipFile(real, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("small.txt", "spreadsheet content")
        assert verify_text(str(real), "xlsx") is True

        fake = tmp_path / "fake.xlsx"
        fake.write_text("not a zip file at all")
        assert verify_text(str(fake), "xlsx") is False
