# ethiviz/storage/job_store.py
"""SQLite-backed job storage replacing the in-memory dict in api_server.py."""
from __future__ import annotations
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path.home() / ".ethiviz" / "jobs.db"

class JobStore:
    """Persistent SQLite job storage with schema: jobs, results, audit_log."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'pending',
        analysis_type TEXT,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        error_message TEXT
    );
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(job_id),
        framework_id TEXT,
        metric_name TEXT,
        value REAL,
        confidence_lower REAL,
        confidence_upper REAL,
        extra_json TEXT
    );
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        event_type TEXT,
        timestamp TEXT,
        details TEXT
    );
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            for stmt in self.SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(s)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_job(self, analysis_type: str = "text") -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, status, analysis_type, created_at) VALUES (?,?,?,?)",
                (job_id, "pending", analysis_type, now),
            )
            conn.execute(
                "INSERT INTO audit_log (job_id, event_type, timestamp, details) VALUES (?,?,?,?)",
                (job_id, "created", now, json.dumps({"analysis_type": analysis_type})),
            )
        return job_id

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status in ("completed", "failed") else None
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status=?, completed_at=?, error_message=? WHERE job_id=?",
                (status, completed_at, error, job_id),
            )
            conn.execute(
                "INSERT INTO audit_log (job_id, event_type, timestamp, details) VALUES (?,?,?,?)",
                (job_id, f"status_{status}", now, json.dumps({"error": error})),
            )

    def store_results(self, job_id: str, results_data: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            for framework_id, metrics in results_data.items():
                if isinstance(metrics, dict):
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            conn.execute(
                                "INSERT INTO results (job_id, framework_id, metric_name, value) VALUES (?,?,?,?)",
                                (job_id, framework_id, metric_name, float(value)),
                            )
                        else:
                            conn.execute(
                                "INSERT INTO results (job_id, framework_id, metric_name, extra_json) VALUES (?,?,?,?)",
                                (job_id, framework_id, metric_name, json.dumps(value)),
                            )
            conn.execute(
                "INSERT INTO audit_log (job_id, event_type, timestamp, details) VALUES (?,?,?,?)",
                (job_id, "results_stored", now, "{}"),
            )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def get_results(self, job_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM results WHERE job_id=?", (job_id,)).fetchall()
        return [dict(r) for r in rows]

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_audit_log(self, job_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE job_id=? ORDER BY id", (job_id,)
            ).fetchall()
        return [dict(r) for r in rows]
