from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "bimba",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.pipeline",
        "app.tasks.audio_tasks",
        "app.tasks.vision_tasks",
        "app.tasks.note_tasks",
    ],
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
    task_routes={
        "app.tasks.pipeline.process_document_task": {"queue": settings.celery_queue_high},
        "app.tasks.audio_tasks.*": {"queue": settings.celery_queue_transcription},
        "app.tasks.vision_tasks.*": {"queue": settings.celery_queue_ocr},
        "app.tasks.note_tasks.*": {"queue": settings.celery_queue_llm},
    },
    task_default_queue="celery",
    task_queues={
        settings.celery_queue_high: {"exchange": settings.celery_queue_high},
        settings.celery_queue_transcription: {"exchange": settings.celery_queue_transcription},
        settings.celery_queue_ocr: {"exchange": settings.celery_queue_ocr},
        settings.celery_queue_llm: {"exchange": settings.celery_queue_llm},
        settings.celery_queue_export: {"exchange": settings.celery_queue_export},
    },
    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=30,
)
