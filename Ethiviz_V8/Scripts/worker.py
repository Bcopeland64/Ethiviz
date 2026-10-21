"""RQ worker entry point for production analysis processing."""
from __future__ import annotations

import os

from redis import Redis
from rq import Queue, Worker


def main() -> None:
    redis_url = os.environ.get("ETHIVIZ_REDIS_URL", "redis://127.0.0.1:6379/0")
    queue_name = os.environ.get("ETHIVIZ_QUEUE_NAME", "ethiviz-analysis")
    connection = Redis.from_url(redis_url)
    connection.ping()
    Worker([Queue(queue_name, connection=connection)]).work()


if __name__ == "__main__":
    main()
