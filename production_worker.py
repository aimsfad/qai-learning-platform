"""Run an RQ worker for the 3alimnIA production queue.

Usage:
    REDIS_URL=redis://localhost:6379/0 python production_worker.py
"""
import os
from redis import Redis
from rq import Worker, Queue

if __name__ == "__main__":
    if not os.getenv("REDIS_URL"):
        raise SystemExit("REDIS_URL is required")
    connection = Redis.from_url(os.environ["REDIS_URL"])
    queue_name = os.getenv("PRODUCTION_QUEUE_NAME", "3alimnia-production")
    Worker([Queue(queue_name, connection=connection)], connection=connection).work(with_scheduler=True)
