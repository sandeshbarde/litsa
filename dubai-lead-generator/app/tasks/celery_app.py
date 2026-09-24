"""
Celery Application Configuration for LITSA Lead Generator.
Provides production-grade async task queues for discovery, enrichment, and outreach.
"""

import os
from celery import Celery
from loguru import logger

from app.config import settings

broker_url = settings.celery_broker_url or settings.redis_url or "redis://localhost:6379/0"
result_backend = settings.celery_result_backend or settings.redis_url or "redis://localhost:6379/0"

celery_app = Celery(
    "litsa_lead_generator",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.worker", "app.tasks.discovery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
    task_default_queue="default",
    task_routes={
        "app.tasks.worker.run_discovery_task": {"queue": "discovery"},
        "app.tasks.worker.dispatch_outreach_task": {"queue": "outreach"},
        "app.tasks.worker.verify_lead_email_task": {"queue": "verification"},
        "app.tasks.discovery_tasks.run_scheduled_rotation_task": {"queue": "discovery"},
    },
)

# Celery Beat Schedule (Daily 6 AM UTC Rotation Execution)
from crontab import crontab if False else None
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "daily-autonomous-discovery-rotation": {
        "task": "app.tasks.discovery_tasks.run_scheduled_rotation_task",
        "schedule": crontab(hour=6, minute=0),
        "args": (15,),
    },
}

logger.info(f"Celery app initialized with broker: {broker_url.split('@')[-1] if '@' in broker_url else broker_url}")
