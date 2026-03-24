"""
ARQ WorkerSettings — the entrypoint for ``python -m arq backend.worker.worker_settings.WorkerSettings``.
"""

from __future__ import annotations

from arq.connections import RedisSettings
from arq.cron import cron

from backend.config import settings
from backend.worker.tasks.generate_page import run_generation_pipeline
from backend.worker.tasks.publish_page import publish_page
from backend.worker.tasks.scheduled_publish import scheduled_publish


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [
        run_generation_pipeline,
        publish_page,
    ]
    cron_jobs = [
        # Run scheduled_publish every hour at minute 0
        cron(scheduled_publish, minute=0),
    ]
    max_jobs = 5
    job_timeout = 300  # seconds
