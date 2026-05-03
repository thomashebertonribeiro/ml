"""
Celery application instance and configuration.

This module defines the Celery app used by both the worker process and
the beat scheduler. Import ``celery_app`` wherever you need to enqueue
tasks or reference the shared task registry.
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "ml_category_web",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.import_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "import-categories-daily": {
            "task": "app.workers.import_task.import_categories",
            "schedule": 86400.0,  # 24h em segundos
            "kwargs": {"triggered_by": "scheduler"},
        }
    },
)
