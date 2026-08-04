from celery import Celery
from celery.schedules import crontab
import structlog

from app.core.settings import settings

logger = structlog.get_logger(__name__)

# Initialize Celery Application
celery_app = Celery(
    "ai_codeguardian_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minute hard time limit
    task_soft_time_limit=1500,  # 25 minute soft time limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Periodic Celery Beat Schedules
    beat_schedule={
        "daily_periodic_cleanup_task": {
            "task": "app.workers.tasks.periodic_cleanup_task",
            "schedule": crontab(hour=2, minute=0),  # Run daily at 02:00 UTC
            "args": (),
        },
    },
)

# Auto-discover tasks from app.workers module
celery_app.autodiscover_tasks(["app.workers"])
