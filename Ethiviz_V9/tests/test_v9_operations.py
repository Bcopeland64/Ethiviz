from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "Scripts"))


def _store(tmp_path):
    from ethiviz.storage.job_store import JobStore

    return JobStore(db_path=tmp_path / "jobs.db")


def test_job_state_transitions_are_enforced_and_audited(tmp_path):
    from ethiviz.storage.job_store import InvalidJobTransitionError

    store = _store(tmp_path)
    job_id = store.create_job("text")
    store.update_status(job_id, "processing")
    store.update_status(job_id, "completed")
    store.update_status(job_id, "completed")

    with pytest.raises(InvalidJobTransitionError):
        store.update_status(job_id, "processing")

    assert store.get_job(job_id)["status"] == "completed"
    assert store.verify_audit_chain() == {"valid": True, "broken_at_id": None}


def test_idempotent_submission_reuses_job_and_rejects_changed_payload(tmp_path):
    from ethiviz.storage.job_store import IdempotencyConflictError

    store = _store(tmp_path)
    arguments = ("text", "owner", "scope-hash", "key-hash", "request-hash")
    first_id, created = store.create_idempotent_job(*arguments)
    replay_id, replay_created = store.create_idempotent_job(*arguments)

    assert created is True
    assert replay_created is False
    assert replay_id == first_id
    assert store.find_idempotent_job("scope-hash", "key-hash", "request-hash") == first_id
    assert len(store.list_jobs()) == 1

    with pytest.raises(IdempotencyConflictError):
        store.find_idempotent_job("scope-hash", "key-hash", "different-request")


def test_expired_jobs_are_terminal_only_and_database_health_is_reported(tmp_path):
    store = _store(tmp_path)
    completed = store.create_job("text")
    pending = store.create_job("image")
    store.update_status(completed, "completed")

    with store._backend._conn() as conn:
        conn.execute(
            "UPDATE jobs SET completed_at=? WHERE job_id=?",
            ("2000-01-01T00:00:00+00:00", completed),
        )

    assert store.expired_job_ids("2020-01-01T00:00:00+00:00") == [completed]
    assert pending not in store.expired_job_ids("2020-01-01T00:00:00+00:00")
    assert store.healthcheck() is True


class TestLocalQueueCancellation:
    def _queue(self, monkeypatch, workers=1):
        monkeypatch.delenv("ETHIVIZ_REDIS_URL", raising=False)
        monkeypatch.setenv("ETHIVIZ_QUEUE_MAX_DEPTH", "4")
        monkeypatch.setenv("ETHIVIZ_LOCAL_WORKERS", str(workers))
        from analysis_queue import AnalysisQueue

        return AnalysisQueue()

    def test_cancels_waiting_job_without_running_it(self, monkeypatch):
        queue = self._queue(monkeypatch)
        started = threading.Event()
        release = threading.Event()
        ran = threading.Event()

        def blocker():
            started.set()
            release.wait(timeout=5)

        queue.enqueue(blocker, task_id="running")
        assert started.wait(timeout=5)
        queue.enqueue(ran.set, task_id="queued")

        assert queue.cancel("queued") is True
        release.set()
        for _ in range(50):
            if queue.depth == 0:
                break
            time.sleep(0.02)
        assert queue.depth == 0
        assert not ran.is_set()

    def test_running_job_is_not_claimed_cancelled(self, monkeypatch):
        queue = self._queue(monkeypatch)
        started = threading.Event()
        release = threading.Event()

        def blocker():
            started.set()
            release.wait(timeout=5)

        queue.enqueue(blocker, task_id="running")
        assert started.wait(timeout=5)
        assert queue.cancel("running") is False
        release.set()

    def test_local_queue_health_is_explicit(self, monkeypatch):
        queue = self._queue(monkeypatch)
        health = queue.healthcheck()
        assert health["mode"] == "local"
        assert health["available"] is True
        assert health["worker_available"] is True


class _FakeQueue:
    def __init__(self, *, cancel_result=True):
        self.cancel_result = cancel_result
        self.enqueued = []
        self.is_distributed = False

    def enqueue(self, target, *args, task_id=None, **kwargs):
        self.enqueued.append((target, args, task_id, kwargs))
        return task_id or "queue-id"

    def cancel(self, task_id):
        return self.cancel_result

    def healthcheck(self):
        return {
            "mode": "local",
            "available": True,
            "worker_available": True,
            "depth": 0,
        }


class _FailOnceQueue(_FakeQueue):
    def __init__(self):
        super().__init__()
        self.fail_next = True

    def enqueue(self, target, *args, task_id=None, **kwargs):
        if self.fail_next:
            self.fail_next = False
            from Scripts.analysis_queue import QueueFullError

            raise QueueFullError()
        return super().enqueue(target, *args, task_id=task_id, **kwargs)


def _configure_api(monkeypatch, tmp_path):
    import api_server

    store = _store(tmp_path)
    monkeypatch.setattr(api_server, "_job_store", store)
    monkeypatch.setattr(api_server, "HAS_JOB_STORE", True)
    monkeypatch.setattr(api_server, "_analysis_queue", _FakeQueue())
    monkeypatch.setattr(api_server, "AUTH_ENABLED", False)
    monkeypatch.setattr(api_server, "_VALID_KEY_HASHES", set())
    monkeypatch.setattr(api_server, "_JOBS_FALLBACK", {}, raising=False)
    monkeypatch.setattr(api_server, "_jobs_fallback", {})
    monkeypatch.setattr(api_server, "_concurrent_jobs", {})
    return api_server, store


def test_api_health_and_readiness_distinguish_dependencies(monkeypatch, tmp_path):
    api_server, _ = _configure_api(monkeypatch, tmp_path)
    client = api_server.app.test_client()

    assert client.get("/health/live").json == {"status": "alive"}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json["components"] == {
        "database": True,
        "queue": True,
        "worker": True,
    }


def test_api_cancels_queued_jobs_but_does_not_claim_to_stop_running_jobs(
    monkeypatch, tmp_path
):
    api_server, store = _configure_api(monkeypatch, tmp_path)
    client = api_server.app.test_client()
    queued_id = store.create_job("text")
    api_server._jobs_fallback[queued_id] = {"job_id": queued_id, "status": "pending"}

    response = client.post(f"/api/jobs/{queued_id}/cancel")
    assert response.status_code == 200
    assert response.json["status"] == "cancelled"
    assert store.get_job(queued_id)["status"] == "cancelled"

    running_id = store.create_job("text")
    store.update_status(running_id, "processing")
    api_server._jobs_fallback[running_id] = {
        "job_id": running_id,
        "status": "processing",
    }
    response = client.post(f"/api/jobs/{running_id}/cancel")
    assert response.status_code == 409
    assert store.get_job(running_id)["status"] == "processing"


def test_api_idempotency_reuses_submission_without_enqueueing_twice(
    monkeypatch, tmp_path
):
    api_server, store = _configure_api(monkeypatch, tmp_path)
    queue = api_server._analysis_queue
    client = api_server.app.test_client()
    form = {
        "analysis_type": "text",
        "data_source_type": "sample",
        "sample_text_id": "sample_text_1",
        "selected_traditions": ["western"],
        "advanced_options": "{}",
    }

    first = client.post(
        "/api/analyze", data=form, headers={"Idempotency-Key": "safe-retry-key"}
    )
    second = client.post(
        "/api/analyze", data=form, headers={"Idempotency-Key": "safe-retry-key"}
    )

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json["idempotent_replay"] is True
    assert first.json["job_id"] == second.json["job_id"]
    assert len(queue.enqueued) == 1
    assert len(store.list_jobs()) == 1


def test_invalid_submission_does_not_consume_idempotency_key(monkeypatch, tmp_path):
    api_server, store = _configure_api(monkeypatch, tmp_path)
    client = api_server.app.test_client()
    headers = {"Idempotency-Key": "retry-after-validation"}
    form = {
        "analysis_type": "text",
        "data_source_type": "sample",
        "sample_text_id": "not-a-sample",
    }

    rejected = client.post("/api/analyze", data=form, headers=headers)
    assert rejected.status_code == 404
    assert store.list_jobs() == []

    form["sample_text_id"] = "sample_text_1"
    accepted = client.post("/api/analyze", data=form, headers=headers)
    assert accepted.status_code == 202
    assert len(store.list_jobs()) == 1


def test_queue_rejection_does_not_consume_idempotency_key(monkeypatch, tmp_path):
    api_server, store = _configure_api(monkeypatch, tmp_path)
    queue = _FailOnceQueue()
    monkeypatch.setattr(api_server, "_analysis_queue", queue)
    client = api_server.app.test_client()
    form = {
        "analysis_type": "text",
        "data_source_type": "sample",
        "sample_text_id": "sample_text_1",
    }
    headers = {"Idempotency-Key": "retry-after-queue-capacity"}

    rejected = client.post("/api/analyze", data=form, headers=headers)
    assert rejected.status_code == 503
    assert store.list_jobs() == []

    accepted = client.post("/api/analyze", data=form, headers=headers)
    assert accepted.status_code == 202
    assert len(queue.enqueued) == 1
    assert len(store.list_jobs()) == 1
