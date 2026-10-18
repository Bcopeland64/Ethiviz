# ethiviz/storage/job_store.py
"""Job storage backing api_server.py: SQLite by default, Postgres opt-in.

JobStore is a thin dispatcher (Upgrade 48): with no DATABASE_URL set (the
default), it delegates to _SQLiteBackend, the original single-file
implementation, completely unchanged in behavior. Setting DATABASE_URL to a
postgres(ql):// URL switches to _PostgresBackend (SQLAlchemy Core, not the
ORM, to keep the same explicit-SQL style as the SQLite path) so the API and
Scripts/worker.py processes from Upgrade 46 can share one database instead
of each opening its own SQLite file.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path.home() / ".ethiviz" / "jobs.db"

# A fixed, arbitrary 63-bit key for Postgres's session/xact advisory lock
# namespace (Upgrade 48's _PostgresBackend._write_audit uses this to
# serialize the audit hash chain's read-last-hash-then-insert sequence
# across every process talking to the same database — the SQLite path's
# threading.Lock only ever protected a single process, which was sufficient
# when SQLite meant "one process owns this file," but is not sufficient once
# Postgres lets the API and worker processes from Upgrade 46 share one DB).
_AUDIT_CHAIN_LOCK_KEY = 0x45746869_56697A31  # "EthiViz1" as hex, arbitrary

# Separate advisory lock key for _PostgresBackend.__init__'s schema creation
# (see the comment there) — a distinct key from _AUDIT_CHAIN_LOCK_KEY so
# schema init and audit writes never contend with each other, even though
# in practice schema init always finishes long before any audit write.
_SCHEMA_LOCK_KEY = 0x45746869_56697A32  # "EthiViz2" as hex, arbitrary


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, coltype: str) -> None:
    """Add `column` to `table` if it isn't already there. This codebase has
    no migration/versioning system — CREATE TABLE IF NOT EXISTS is a no-op
    against an already-deployed DB file with an older schema, so new columns
    on existing tables need an explicit ALTER TABLE, run here."""
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


class _SQLiteBackend:
    """Persistent SQLite job storage with schema: jobs, results, audit_log,
    upload_usage. This is JobStore's original implementation, unchanged by
    Upgrade 48 — verbatim except for the class rename, so a deployment that
    never sets DATABASE_URL sees no behavior change."""

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
    CREATE TABLE IF NOT EXISTS upload_usage (
        key_hash TEXT NOT NULL,
        usage_date TEXT NOT NULL,
        bytes_used INTEGER NOT NULL DEFAULT 0,
        UNIQUE(key_hash, usage_date)
    );
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Guards the audit_log hash-chain's read-last-hash-then-insert
        # sequence (Upgrade 45). Without this, two threads writing audit
        # events concurrently could both read the same "last" row_hash and
        # chain off it, forking the chain instead of extending it.
        self._audit_lock = threading.Lock()
        with self._conn() as conn:
            for stmt in self.SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(s)
            # SCHEMA above is CREATE TABLE IF NOT EXISTS, which is a no-op
            # against an already-deployed jobs.db that predates these
            # columns — this codebase has no other migration mechanism, so
            # ALTER TABLE here is it. Safe to run on every startup: it's a
            # no-op once the column exists.
            _ensure_column(conn, "jobs", "owner_key_hash", "TEXT")
            _ensure_column(conn, "audit_log", "prev_hash", "TEXT")
            _ensure_column(conn, "audit_log", "row_hash", "TEXT")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _write_audit(
        self,
        conn: sqlite3.Connection,
        job_id: str,
        event_type: str,
        details: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> str:
        """Single write path for every audit_log row (Upgrade 45), used by
        create_job/update_status/store_results/delete_job/log_event — these
        previously each ran their own ad hoc INSERT, which meant a hash
        chain added to only one of them would leave the others unprotected.
        Must be called with `conn` already inside an open transaction (i.e.
        from within a `with self._conn() as conn:` block in the caller)."""
        now = timestamp or datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details or {})
        with self._audit_lock:
            last = conn.execute(
                "SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            prev_hash = (last["row_hash"] if last else None) or ""
            row_hash = hashlib.sha256(
                f"{prev_hash}|{job_id}|{event_type}|{now}|{details_json}".encode("utf-8")
            ).hexdigest()
            conn.execute(
                "INSERT INTO audit_log (job_id, event_type, timestamp, details, prev_hash, row_hash) "
                "VALUES (?,?,?,?,?,?)",
                (job_id, event_type, now, details_json, prev_hash, row_hash),
            )
        return now

    def verify_audit_chain(self) -> dict[str, Any]:
        """Recompute the hash chain across the whole audit_log table.
        Rows written before Upgrade 45 have no row_hash — verification
        starts from the first hashed row rather than failing immediately on
        that legacy data (documented limitation, not silently ignored)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, job_id, event_type, timestamp, details, prev_hash, row_hash "
                "FROM audit_log ORDER BY id"
            ).fetchall()
        prev_hash = ""
        started = False
        for row in rows:
            if row["row_hash"] is None:
                continue
            if not started:
                prev_hash = row["prev_hash"] or ""
                started = True
            expected = hashlib.sha256(
                f"{prev_hash}|{row['job_id']}|{row['event_type']}|{row['timestamp']}|{row['details']}".encode("utf-8")
            ).hexdigest()
            if expected != row["row_hash"] or (row["prev_hash"] or "") != prev_hash:
                return {"valid": False, "broken_at_id": row["id"]}
            prev_hash = row["row_hash"]
        return {"valid": True, "broken_at_id": None}

    def create_job(self, analysis_type: str = "text", owner_key_hash: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, status, analysis_type, created_at, owner_key_hash) VALUES (?,?,?,?,?)",
                (job_id, "pending", analysis_type, now, owner_key_hash),
            )
            self._write_audit(conn, job_id, "created", {"analysis_type": analysis_type}, timestamp=now)
        return job_id

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status in ("completed", "failed") else None
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status=?, completed_at=?, error_message=? WHERE job_id=?",
                (status, completed_at, error, job_id),
            )
            self._write_audit(conn, job_id, f"status_{status}", {"error": error}, timestamp=now)

    def store_results(self, job_id: str, results_data: dict[str, Any]) -> None:
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
            self._write_audit(conn, job_id, "results_stored", {})

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def get_results(self, job_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM results WHERE job_id=?", (job_id,)).fetchall()
        return [dict(r) for r in rows]

    def list_jobs(self, limit: int = 50, owner_key_hash: str | None = None) -> list[dict[str, Any]]:
        """owner_key_hash, when given, scopes the listing to jobs owned by
        that key plus unowned/legacy jobs (owner_key_hash IS NULL) — jobs
        created before Upgrade 40 or while auth was disabled. Passing None
        (the default, and always the case when auth is disabled) preserves
        the original unscoped behavior."""
        with self._conn() as conn:
            if owner_key_hash is None:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE owner_key_hash=? OR owner_key_hash IS NULL "
                    "ORDER BY created_at DESC LIMIT ?",
                    (owner_key_hash, limit),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_audit_log(self, job_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE job_id=? ORDER BY id", (job_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def log_event(self, job_id: str, event_type: str, details: dict[str, Any] | None = None) -> None:
        """Record an arbitrary audit_log event (e.g. 'exported') for a job.
        Previously the audit_log table only ever received the three events
        create_job/update_status/store_results wrote automatically — nothing
        outside JobStore could add to the compliance trail."""
        with self._conn() as conn:
            self._write_audit(conn, job_id, event_type, details)

    def delete_job(self, job_id: str) -> None:
        """Purge a job's rows and results (Upgrade 38 retention). The
        audit_log keeps a 'deleted' row rather than being wiped too, so the
        deletion itself remains part of the compliance trail."""
        with self._conn() as conn:
            conn.execute("DELETE FROM results WHERE job_id=?", (job_id,))
            self._write_audit(conn, job_id, "deleted", {})
            conn.execute("DELETE FROM jobs WHERE job_id=?", (job_id,))

    def record_upload(self, key: str, num_bytes: int) -> int:
        """Add num_bytes to today's (UTC) running total for `key` (an API-key
        hash, or a caller IP when auth is disabled) and return the new total
        for the day (Upgrade 43 — per-key daily upload quota)."""
        today = datetime.now(timezone.utc).date().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO upload_usage (key_hash, usage_date, bytes_used) VALUES (?,?,?) "
                "ON CONFLICT(key_hash, usage_date) DO UPDATE SET bytes_used = bytes_used + excluded.bytes_used",
                (key, today, num_bytes),
            )
            row = conn.execute(
                "SELECT bytes_used FROM upload_usage WHERE key_hash=? AND usage_date=?",
                (key, today),
            ).fetchone()
        return row["bytes_used"] if row else num_bytes

    def get_upload_usage(self, key: str) -> int:
        """Bytes uploaded today (UTC) by `key`, or 0 if none yet."""
        today = datetime.now(timezone.utc).date().isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT bytes_used FROM upload_usage WHERE key_hash=? AND usage_date=?",
                (key, today),
            ).fetchone()
        return row["bytes_used"] if row else 0


class _PostgresBackend:
    """SQLAlchemy-Core-backed job storage (Upgrade 48), same public method
    set and semantics as _SQLiteBackend, for multi-instance deployments that
    set DATABASE_URL to a postgres(ql):// URL and share one database across
    the API and Scripts/worker.py (Upgrade 46) processes.

    Import of sqlalchemy is deferred to __init__ (not module level) so that
    installing ethiviz[api] alone — no DATABASE_URL, no Postgres extra —
    never requires sqlalchemy to be present, matching every other optional
    dependency in this codebase (vision, semantic, etc.)."""

    SCHEMA_STATEMENTS = [
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            analysis_type TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            error_message TEXT,
            owner_key_hash TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS results (
            id BIGSERIAL PRIMARY KEY,
            job_id TEXT NOT NULL REFERENCES jobs(job_id),
            framework_id TEXT,
            metric_name TEXT,
            value DOUBLE PRECISION,
            confidence_lower DOUBLE PRECISION,
            confidence_upper DOUBLE PRECISION,
            extra_json TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            job_id TEXT NOT NULL,
            event_type TEXT,
            timestamp TEXT,
            details TEXT,
            prev_hash TEXT,
            row_hash TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS upload_usage (
            key_hash TEXT NOT NULL,
            usage_date TEXT NOT NULL,
            bytes_used BIGINT NOT NULL DEFAULT 0,
            UNIQUE(key_hash, usage_date)
        )
        """,
        # jobs/audit_log both predate owner_key_hash/prev_hash/row_hash in
        # the SQLite schema history this mirrors; IF NOT EXISTS makes these
        # safe to (re-)run against an already-migrated database, unlike the
        # SQLite path, which needs the PRAGMA-based _ensure_column check
        # because SQLite's ADD COLUMN has no IF NOT EXISTS of its own.
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS owner_key_hash TEXT",
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS prev_hash TEXT",
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS row_hash TEXT",
    ]

    def __init__(self, database_url: str) -> None:
        from sqlalchemy import create_engine, text

        self._text = text
        self.database_url = database_url
        self.engine = create_engine(database_url, pool_pre_ping=True, future=True)
        with self.engine.begin() as conn:
            # Multiple gunicorn workers (or API + worker processes) each
            # construct their own JobStore on startup and race this exact
            # block — reproduced directly under docker-compose's default
            # 2-worker gunicorn config: two concurrent
            # `CREATE TABLE IF NOT EXISTS jobs (...)` statements both pass
            # Postgres's existence check before either commits, and the
            # second's catalog insert then fails with
            # `duplicate key value violates unique constraint
            # "pg_type_typname_nsp_index"` — IF NOT EXISTS guards against a
            # table that already existed when the statement started, not
            # against another transaction creating it concurrently. The
            # SQLite path never hit this because a single file/process was
            # always the only writer during schema init; Postgres exists
            # specifically to remove that assumption, so this needs its own
            # guard. pg_advisory_xact_lock serializes every process's schema
            # init against this same key, released automatically at commit.
            conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _SCHEMA_LOCK_KEY})
            for stmt in self.SCHEMA_STATEMENTS:
                conn.execute(text(stmt))

    def _write_audit(
        self,
        conn,
        job_id: str,
        event_type: str,
        details: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> str:
        """Same hash-chain shape as _SQLiteBackend._write_audit, but
        serialized with a Postgres transaction-scoped advisory lock instead
        of a threading.Lock — the API and worker processes from Upgrade 46
        are separate OS processes (potentially on separate hosts) sharing
        this one database, so a lock inside this Python process alone would
        not stop two of them from reading the same "last" row_hash and
        forking the chain. pg_advisory_xact_lock is released automatically
        at COMMIT/ROLLBACK, matching the `with self.engine.begin() as conn`
        transaction boundary each caller already uses."""
        text = self._text
        now = timestamp or datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details or {})
        conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _AUDIT_CHAIN_LOCK_KEY})
        last = conn.execute(
            text("SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1")
        ).mappings().first()
        prev_hash = (last["row_hash"] if last else None) or ""
        row_hash = hashlib.sha256(
            f"{prev_hash}|{job_id}|{event_type}|{now}|{details_json}".encode("utf-8")
        ).hexdigest()
        conn.execute(
            text(
                "INSERT INTO audit_log (job_id, event_type, timestamp, details, prev_hash, row_hash) "
                "VALUES (:job_id, :event_type, :timestamp, :details, :prev_hash, :row_hash)"
            ),
            {
                "job_id": job_id, "event_type": event_type, "timestamp": now,
                "details": details_json, "prev_hash": prev_hash, "row_hash": row_hash,
            },
        )
        return now

    def verify_audit_chain(self) -> dict[str, Any]:
        text = self._text
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, job_id, event_type, timestamp, details, prev_hash, row_hash "
                    "FROM audit_log ORDER BY id"
                )
            ).mappings().all()
        prev_hash = ""
        started = False
        for row in rows:
            if row["row_hash"] is None:
                continue
            if not started:
                prev_hash = row["prev_hash"] or ""
                started = True
            expected = hashlib.sha256(
                f"{prev_hash}|{row['job_id']}|{row['event_type']}|{row['timestamp']}|{row['details']}".encode("utf-8")
            ).hexdigest()
            if expected != row["row_hash"] or (row["prev_hash"] or "") != prev_hash:
                return {"valid": False, "broken_at_id": row["id"]}
            prev_hash = row["row_hash"]
        return {"valid": True, "broken_at_id": None}

    def create_job(self, analysis_type: str = "text", owner_key_hash: str | None = None) -> str:
        text = self._text
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO jobs (job_id, status, analysis_type, created_at, owner_key_hash) "
                    "VALUES (:job_id, 'pending', :analysis_type, :created_at, :owner_key_hash)"
                ),
                {"job_id": job_id, "analysis_type": analysis_type, "created_at": now, "owner_key_hash": owner_key_hash},
            )
            self._write_audit(conn, job_id, "created", {"analysis_type": analysis_type}, timestamp=now)
        return job_id

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        text = self._text
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status in ("completed", "failed") else None
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE jobs SET status=:status, completed_at=:completed_at, error_message=:error "
                    "WHERE job_id=:job_id"
                ),
                {"status": status, "completed_at": completed_at, "error": error, "job_id": job_id},
            )
            self._write_audit(conn, job_id, f"status_{status}", {"error": error}, timestamp=now)

    def store_results(self, job_id: str, results_data: dict[str, Any]) -> None:
        text = self._text
        with self.engine.begin() as conn:
            for framework_id, metrics in results_data.items():
                if isinstance(metrics, dict):
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            conn.execute(
                                text(
                                    "INSERT INTO results (job_id, framework_id, metric_name, value) "
                                    "VALUES (:job_id, :framework_id, :metric_name, :value)"
                                ),
                                {"job_id": job_id, "framework_id": framework_id, "metric_name": metric_name, "value": float(value)},
                            )
                        else:
                            conn.execute(
                                text(
                                    "INSERT INTO results (job_id, framework_id, metric_name, extra_json) "
                                    "VALUES (:job_id, :framework_id, :metric_name, :extra_json)"
                                ),
                                {"job_id": job_id, "framework_id": framework_id, "metric_name": metric_name, "extra_json": json.dumps(value)},
                            )
            self._write_audit(conn, job_id, "results_stored", {})

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        text = self._text
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM jobs WHERE job_id=:job_id"), {"job_id": job_id}).mappings().first()
        return dict(row) if row else None

    def get_results(self, job_id: str) -> list[dict[str, Any]]:
        text = self._text
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM results WHERE job_id=:job_id"), {"job_id": job_id}).mappings().all()
        return [dict(r) for r in rows]

    def list_jobs(self, limit: int = 50, owner_key_hash: str | None = None) -> list[dict[str, Any]]:
        text = self._text
        with self.engine.connect() as conn:
            if owner_key_hash is None:
                rows = conn.execute(
                    text("SELECT * FROM jobs ORDER BY created_at DESC LIMIT :limit"), {"limit": limit}
                ).mappings().all()
            else:
                rows = conn.execute(
                    text(
                        "SELECT * FROM jobs WHERE owner_key_hash=:owner OR owner_key_hash IS NULL "
                        "ORDER BY created_at DESC LIMIT :limit"
                    ),
                    {"owner": owner_key_hash, "limit": limit},
                ).mappings().all()
        return [dict(r) for r in rows]

    def get_audit_log(self, job_id: str) -> list[dict[str, Any]]:
        text = self._text
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM audit_log WHERE job_id=:job_id ORDER BY id"), {"job_id": job_id}
            ).mappings().all()
        return [dict(r) for r in rows]

    def log_event(self, job_id: str, event_type: str, details: dict[str, Any] | None = None) -> None:
        with self.engine.begin() as conn:
            self._write_audit(conn, job_id, event_type, details)

    def delete_job(self, job_id: str) -> None:
        text = self._text
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM results WHERE job_id=:job_id"), {"job_id": job_id})
            self._write_audit(conn, job_id, "deleted", {})
            conn.execute(text("DELETE FROM jobs WHERE job_id=:job_id"), {"job_id": job_id})

    def record_upload(self, key: str, num_bytes: int) -> int:
        text = self._text
        today = datetime.now(timezone.utc).date().isoformat()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO upload_usage (key_hash, usage_date, bytes_used) "
                    "VALUES (:key, :today, :num_bytes) "
                    "ON CONFLICT (key_hash, usage_date) DO UPDATE "
                    "SET bytes_used = upload_usage.bytes_used + EXCLUDED.bytes_used"
                ),
                {"key": key, "today": today, "num_bytes": num_bytes},
            )
            row = conn.execute(
                text("SELECT bytes_used FROM upload_usage WHERE key_hash=:key AND usage_date=:today"),
                {"key": key, "today": today},
            ).mappings().first()
        return row["bytes_used"] if row else num_bytes

    def get_upload_usage(self, key: str) -> int:
        text = self._text
        today = datetime.now(timezone.utc).date().isoformat()
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT bytes_used FROM upload_usage WHERE key_hash=:key AND usage_date=:today"),
                {"key": key, "today": today},
            ).mappings().first()
        return row["bytes_used"] if row else 0


class JobStore:
    """Public entry point used by api_server.py and Scripts/worker.py.
    Dispatches to _SQLiteBackend (default) or _PostgresBackend (Upgrade 48,
    opt-in via DATABASE_URL) — every public method here is a one-line
    delegation, so this class carries no logic of its own to drift out of
    sync with either backend."""

    def __init__(self, db_path: Path | None = None, database_url: str | None = None) -> None:
        import os

        self.database_url = database_url or os.environ.get("DATABASE_URL")
        # DATABASE_URL is also how some deployments point at a SQLite file by
        # URL rather than a Path (e.g. sqlite:///path/to/jobs.db) — treat
        # that the same as db_path/unset, since _SQLiteBackend already knows
        # how to open a SQLite file and gains nothing from going through
        # SQLAlchemy for it.
        if self.database_url and not self.database_url.startswith("sqlite"):
            self.backend_name = "postgres"
            self._backend = _PostgresBackend(self.database_url)
            self.db_path = None
        else:
            self.backend_name = "sqlite"
            self._backend = _SQLiteBackend(db_path)
            self.db_path = self._backend.db_path

    def verify_audit_chain(self) -> dict[str, Any]:
        return self._backend.verify_audit_chain()

    def create_job(self, analysis_type: str = "text", owner_key_hash: str | None = None) -> str:
        return self._backend.create_job(analysis_type, owner_key_hash)

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        return self._backend.update_status(job_id, status, error)

    def store_results(self, job_id: str, results_data: dict[str, Any]) -> None:
        return self._backend.store_results(job_id, results_data)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._backend.get_job(job_id)

    def get_results(self, job_id: str) -> list[dict[str, Any]]:
        return self._backend.get_results(job_id)

    def list_jobs(self, limit: int = 50, owner_key_hash: str | None = None) -> list[dict[str, Any]]:
        return self._backend.list_jobs(limit, owner_key_hash)

    def get_audit_log(self, job_id: str) -> list[dict[str, Any]]:
        return self._backend.get_audit_log(job_id)

    def log_event(self, job_id: str, event_type: str, details: dict[str, Any] | None = None) -> None:
        return self._backend.log_event(job_id, event_type, details)

    def delete_job(self, job_id: str) -> None:
        return self._backend.delete_job(job_id)

    def record_upload(self, key: str, num_bytes: int) -> int:
        return self._backend.record_upload(key, num_bytes)

    def get_upload_usage(self, key: str) -> int:
        return self._backend.get_upload_usage(key)
