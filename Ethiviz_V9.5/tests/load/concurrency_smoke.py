"""A minimal concurrency smoke test documenting the V7 load-testing target.
This is intentionally lightweight: it proves the queue can accept concurrent jobs
and is meant to be extended with a real benchmark harness in a production setup.
"""

from __future__ import annotations

from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Scripts"))

from analysis_queue import AnalysisQueue


def run_smoke_test() -> None:
    import os
    os.environ['ETHIVIZ_QUEUE_MAX_DEPTH'] = '8'
    os.environ['ETHIVIZ_LOCAL_WORKERS'] = '2'
    queue = AnalysisQueue()
    started = []
    lock = threading.Lock()

    def worker(value: int):
        with lock:
            started.append(value)
        time.sleep(0.05)

    for value in range(4):
        queue.enqueue(worker, value)

    deadline = time.time() + 5
    while len(started) < 4 and time.time() < deadline:
        time.sleep(0.05)

    if len(started) != 4:
        raise AssertionError(f"Expected 4 queued jobs to run, saw {len(started)}")


if __name__ == "__main__":
    run_smoke_test()
    print("queue concurrency smoke test passed")
