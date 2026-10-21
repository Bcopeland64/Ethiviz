"""Tests for EthiViz V7 Phase 2 — Scalable Production Architecture
(Upgrades 46-50). Covers: the bounded local analysis queue (Upgrade 46),
request/job metrics and structured logging (Upgrade 50), and the Postgres
JobStore backend (Upgrade 48).

Upgrade 47 (thread-safe calibrator/drift state) is covered separately in
tests/test_concurrency.py, per the plan's module list.

The Postgres tests are skipped unless ETHIVIZ_TEST_DATABASE_URL is set to a
reachable postgres(ql):// URL — there is no live Postgres in every dev/CI
environment, and job_store.py's SQLite path (the default, zero-config
backend) already has full coverage without it. CI's workflow brings up a
postgres service container and sets this variable (see
.github/workflows/ci.yml).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Scripts"))


# ── AnalysisQueue (Upgrade 46) ───────────────────────────────────────────────

class TestAnalysisQueueLocalExecutor:
    def _make_queue(self, monkeypatch, max_depth: int = 2, workers: int = 1):
        monkeypatch.delenv("ETHIVIZ_REDIS_URL", raising=False)
        monkeypatch.setenv("ETHIVIZ_QUEUE_MAX_DEPTH", str(max_depth))
        monkeypatch.setenv("ETHIVIZ_LOCAL_WORKERS", str(workers))
        from analysis_queue import AnalysisQueue
        return AnalysisQueue()

    def test_falls_back_to_local_executor_without_redis_url(self, monkeypatch):
        queue = self._make_queue(monkeypatch)
        assert queue.is_distributed is False

    def test_enqueued_job_actually_runs(self, monkeypatch):
        queue = self._make_queue(monkeypatch, workers=2)
        done = threading.Event()
        result = {}

        def job(x):
            result["value"] = x * 2
            done.set()

        queue.enqueue(job, 21)
        assert done.wait(timeout=5), "queued job never ran"
        assert result["value"] == 42

    def test_depth_reflects_pending_work(self, monkeypatch):
        # A single worker plus a job that blocks until released lets us
        # observe the queue's depth accounting while work is in flight,
        # without racing a fast-finishing job.
        queue = self._make_queue(monkeypatch, max_depth=5, workers=1)
        release = threading.Event()
        started = threading.Event()

        def blocking_job():
            started.set()
            release.wait(timeout=5)

        queue.enqueue(blocking_job)
        assert started.wait(timeout=5)
        assert queue.depth >= 1
        release.set()
        for _ in range(50):
            if queue.depth == 0:
                break
            time.sleep(0.05)
        assert queue.depth == 0

    def test_queue_full_raises(self, monkeypatch):
        from analysis_queue import QueueFullError
        queue = self._make_queue(monkeypatch, max_depth=1, workers=1)
        release = threading.Event()
        started = threading.Event()

        def blocking_job():
            started.set()
            release.wait(timeout=5)

        def noop_job():
            pass

        queue.enqueue(blocking_job)
        assert started.wait(timeout=5)
        # max_depth=1: the semaphore has no room for a second job while the
        # first is still occupying its slot.
        with pytest.raises(QueueFullError):
            queue.enqueue(noop_job)
        release.set()

    def test_failed_job_does_not_wedge_the_slot(self, monkeypatch):
        """A job that raises must still release its queue slot — mirrors
        run_analysis_job's own try/except/finally never letting an
        exception escape, but proves the queue's bookkeeping is correct
        even if some future job target does raise."""
        queue = self._make_queue(monkeypatch, max_depth=1, workers=1)

        def failing_job():
            raise RuntimeError("boom")

        queue.enqueue(failing_job)
        for _ in range(50):
            if queue.depth == 0:
                break
            time.sleep(0.05)
        assert queue.depth == 0
        # The slot must be free again for a subsequent job.
        done = threading.Event()
        queue.enqueue(lambda: done.set())
        assert done.wait(timeout=5)


class TestAnalysisQueueDistributedSelection:
    def test_unreachable_redis_falls_back_to_local(self, monkeypatch):
        """AnalysisQueue.__init__ pings Redis and silently falls back to the
        local executor on any failure — a misconfigured/unreachable
        ETHIVIZ_REDIS_URL must degrade to "dev mode" rather than making the
        whole app fail to start."""
        monkeypatch.setenv("ETHIVIZ_REDIS_URL", "redis://127.0.0.1:1/0")  # port 1: nothing listens
        monkeypatch.setenv("ETHIVIZ_QUEUE_MAX_DEPTH", "10")
        from analysis_queue import AnalysisQueue
        queue = AnalysisQueue()
        assert queue.is_distributed is False


# ── Observability (Upgrade 50) ───────────────────────────────────────────────

class TestObservability:
    def setup_method(self):
        import observability
        with observability._lock:
            observability._http_requests.clear()
            observability._http_duration_sum.clear()
            observability._job_count.clear()
            observability._job_duration_sum.clear()
            observability._lens_jobs.clear()
            observability._lens_warnings.clear()
        observability._queue_depth_provider.clear()

    def test_record_job_updates_counters(self):
        import observability
        observability.record_job(
            "text", "completed", 2.5,
            tradition_scores=[
                {"tradition": "western_v1", "score": 0.4},
                {"tradition": "ubuntu_v1", "score": 0.6, "warnings": ["low sample size"]},
            ],
        )
        assert observability._job_count[("text", "completed")] == 1
        assert observability._job_duration_sum[("text", "completed")] == 2.5
        assert observability._lens_jobs["western_v1"] == 1
        assert observability._lens_jobs["ubuntu_v1"] == 1
        assert observability._lens_warnings["ubuntu_v1"] == 1
        assert observability._lens_warnings["western_v1"] == 0

    def test_metrics_endpoint_reports_job_and_lens_data(self):
        import observability
        from flask import Flask

        app = Flask(__name__)
        observability.install(app)
        observability.record_job(
            "text", "completed", 1.0,
            tradition_scores=[{"tradition": "islamic_v1", "score": 0.3, "warnings": ["x"]}],
        )
        observability.register_queue_depth_provider(lambda: 3)

        client = app.test_client()
        resp = client.get("/metrics")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'ethiviz_job_total{analysis_type="text",status="completed"} 1' in body
        assert 'ethiviz_lens_warnings_total{lens="islamic_v1"} 1' in body
        assert 'ethiviz_lens_warning_rate{lens="islamic_v1"} 1.0000' in body
        assert "ethiviz_queue_depth 3" in body

    def test_request_gets_correlation_id_header(self):
        import observability
        from flask import Flask

        app = Flask(__name__)
        observability.install(app)

        @app.get("/ping")
        def ping():
            return "pong"

        client = app.test_client()
        resp = client.get("/ping")
        assert resp.headers.get("X-Request-ID")

    def test_client_supplied_request_id_is_echoed(self):
        import observability
        from flask import Flask

        app = Flask(__name__)
        observability.install(app)

        @app.get("/ping")
        def ping():
            return "pong"

        client = app.test_client()
        resp = client.get("/ping", headers={"X-Request-ID": "caller-supplied-id"})
        assert resp.headers["X-Request-ID"] == "caller-supplied-id"

    def test_queue_depth_provider_exception_is_swallowed(self):
        """A broken provider must not take GET /metrics down with it —
        metrics scraping should degrade (omit the gauge), not 500."""
        import observability
        from flask import Flask

        app = Flask(__name__)
        observability.install(app)

        def broken():
            raise RuntimeError("queue backend unreachable")

        observability.register_queue_depth_provider(broken)
        client = app.test_client()
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "ethiviz_queue_depth" not in resp.get_data(as_text=True)


class TestJsonLogging:
    def test_json_formatter_produces_valid_json_with_expected_fields(self, capsys):
        import logging
        import observability

        observability.configure_json_logging()
        logger = logging.getLogger("test.v7.phase2")
        logger.info("hello world")

        captured = capsys.readouterr()
        line = [l for l in captured.err.split("\n") if l.strip()][-1]
        payload = json.loads(line)
        assert payload["message"] == "hello world"
        assert payload["level"] == "INFO"
        assert "timestamp" in payload
        assert payload["request_id"] == "-"


# ── Postgres JobStore backend (Upgrade 48) ──────────────────────────────────

_PG_URL = os.environ.get("ETHIVIZ_TEST_DATABASE_URL")

pytestmark_pg = pytest.mark.skipif(
    not _PG_URL,
    reason="Set ETHIVIZ_TEST_DATABASE_URL to a reachable postgres:// URL to run these.",
)


@pytestmark_pg
class TestPostgresJobStore:
    """Exercises _PostgresBackend against a real Postgres instance — the
    SQLAlchemy Core queries here diverge from _SQLiteBackend's raw sqlite3
    ones enough (named params, BIGSERIAL, pg_advisory_xact_lock) that a
    mocked connection wouldn't catch a real syntax error."""

    @pytest.fixture
    def store(self):
        from ethiviz.storage.job_store import JobStore
        js = JobStore(database_url=_PG_URL)
        yield js
        # Best-effort cleanup so repeated runs don't accumulate rows.
        with js._backend.engine.begin() as conn:
            from sqlalchemy import text
            conn.execute(text("DELETE FROM results"))
            conn.execute(text("DELETE FROM audit_log"))
            conn.execute(text("DELETE FROM jobs"))
            conn.execute(text("DELETE FROM upload_usage"))

    def test_backend_selected_is_postgres(self, store):
        assert store.backend_name == "postgres"

    def test_create_and_fetch_job(self, store):
        job_id = store.create_job("text", owner_key_hash="abc123")
        job = store.get_job(job_id)
        assert job["status"] == "pending"
        assert job["owner_key_hash"] == "abc123"

    def test_full_lifecycle_and_audit_chain(self, store):
        job_id = store.create_job("text")
        store.update_status(job_id, "processing")
        store.store_results(job_id, {"western_v1": {"score": 0.42}})
        store.update_status(job_id, "completed")

        assert store.get_job(job_id)["status"] == "completed"
        assert store.get_results(job_id)[0]["value"] == 0.42
        assert store.verify_audit_chain()["valid"] is True

        store.delete_job(job_id)
        assert store.get_job(job_id) is None

    def test_upload_quota_accumulates(self, store):
        first = store.record_upload("key-x", 1000)
        second = store.record_upload("key-x", 500)
        assert first == 1000
        assert second == 1500
        assert store.get_upload_usage("key-x") == 1500

    def test_owner_scoped_listing(self, store):
        owned = store.create_job("text", owner_key_hash="owner-a")
        store.create_job("text", owner_key_hash="owner-b")
        jobs = store.list_jobs(owner_key_hash="owner-a")
        assert {j["job_id"] for j in jobs} == {owned}

    def test_concurrent_audit_writes_stay_chained(self, store):
        job_id = store.create_job("text")
        errors = []

        def hammer(n):
            try:
                for i in range(10):
                    store.log_event(job_id, "concurrent_test", {"i": i})
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=hammer, args=(10,)) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert store.verify_audit_chain()["valid"] is True

    def test_concurrent_schema_init_does_not_race(self):
        """Regression test: multiple gunicorn workers (or API + worker
        processes) each construct their own JobStore on startup, all
        hitting `_PostgresBackend.__init__`'s `CREATE TABLE IF NOT EXISTS`
        block against a table that doesn't exist yet — reproduced directly
        under docker-compose's default 2-worker gunicorn config, where the
        second worker to reach the CREATE TABLE failed with
        `duplicate key value violates unique constraint
        "pg_type_typname_nsp_index"`. IF NOT EXISTS guards against a table
        that already existed when the statement started, not against
        another concurrent transaction creating it. Requires a genuinely
        empty schema, so this drops the tables first rather than reusing
        the `store` fixture (which assumes a stack already up)."""
        from sqlalchemy import create_engine, text

        engine = create_engine(_PG_URL)
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS results, audit_log, upload_usage, jobs CASCADE"))
        engine.dispose()

        from ethiviz.storage.job_store import JobStore

        errors: list[BaseException] = []

        def make_store() -> None:
            try:
                JobStore(database_url=_PG_URL)
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=make_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent schema init raised: {errors}"
