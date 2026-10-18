"""Bounded analysis queue with an RQ/Redis production backend.

The local executor keeps the development server usable without Redis, while
production deployments set ETHIVIZ_REDIS_URL and run Scripts/worker.py.
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore, Lock
from typing import Any, Callable

logger = logging.getLogger(__name__)


class QueueFullError(RuntimeError):
    """Raised when the configured queue cannot accept another job."""


class AnalysisQueue:
    def __init__(self) -> None:
        self.name = os.environ.get("ETHIVIZ_QUEUE_NAME", "ethiviz-analysis")
        self.max_depth = int(os.environ.get("ETHIVIZ_QUEUE_MAX_DEPTH", "100"))
        self.redis_url = os.environ.get("ETHIVIZ_REDIS_URL")
        self._rq_queue = None
        self._executor = None
        self._slots = None
        self._local_pending = 0
        self._lock = Lock()

        if self.redis_url:
            try:
                from redis import Redis
                from rq import Queue

                connection = Redis.from_url(self.redis_url)
                connection.ping()
                self._rq_queue = Queue(self.name, connection=connection)
            except Exception:
                self._rq_queue = None

        if self._rq_queue is None:
            workers = int(os.environ.get("ETHIVIZ_LOCAL_WORKERS", "2"))
            self._executor = ThreadPoolExecutor(max_workers=workers)
            self._slots = BoundedSemaphore(self.max_depth)

    @property
    def is_distributed(self) -> bool:
        return self._rq_queue is not None

    @property
    def depth(self) -> int:
        if self._rq_queue is not None:
            return int(self._rq_queue.count)
        with self._lock:
            return self._local_pending

    def enqueue(self, target: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        if self._rq_queue is not None:
            if self._rq_queue.count >= self.max_depth:
                raise QueueFullError("Analysis queue is full.")
            from rq import Retry

            job = self._rq_queue.enqueue(
                target, *args, kwargs=kwargs,
                retry=Retry(max=1, interval=[5]),
                job_timeout=int(os.environ.get("ETHIVIZ_JOB_TIMEOUT", "3600")),
            )
            return str(job.id)

        assert self._executor is not None and self._slots is not None
        if not self._slots.acquire(blocking=False):
            raise QueueFullError("Analysis queue is full.")
        with self._lock:
            self._local_pending += 1

        def run_and_release() -> Any:
            try:
                return target(*args, **kwargs)
            except Exception:
                # ThreadPoolExecutor swallows an exception raised here until
                # something calls future.result() — nothing does, since
                # api_server.py submits this fire-and-forget. Without this,
                # a bug that somehow escapes run_analysis_job's own broad
                # except Exception (the caller here) would vanish with no
                # trace, undermining the observability this queue is meant
                # to support. threading.Thread's default excepthook used to
                # print this same traceback before Upgrade 46 replaced it.
                logger.exception("Unhandled exception in queued job target %r", target)
                raise
            finally:
                with self._lock:
                    self._local_pending -= 1
                self._slots.release()

        future = self._executor.submit(run_and_release)
        return str(id(future))
