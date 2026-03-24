"""
Worker package.

Re-exports WorkerSettings for backwards compatibility so that
``python -m arq backend.worker.WorkerSettings`` keeps working.
"""

from backend.worker.worker_settings import WorkerSettings  # noqa: F401
