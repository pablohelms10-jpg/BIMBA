from __future__ import annotations

import logging
import os
import tempfile
import uuid
from typing import List

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.audio_tasks.transcribe_audio", max_retries=2)
def transcribe_audio(self, audio_path: str, document_id: str) -> List[dict]:
    """
    Celery task: transcribe an audio file and return segment dicts.

    Returns:
        List of dicts: [{chunk_index, start_time, end_time, transcript, language}, ...]
    """
    from app.services.transcription import TranscriptionService

    logger.info("Starting transcription for document %s", document_id)
    try:
        svc = TranscriptionService()
        chunks = svc.transcribe_file(audio_path)
        return [
            {
                "chunk_index": c.chunk_index,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "transcript": c.transcript,
                "language": c.language,
            }
            for c in chunks
        ]
    except Exception as exc:
        logger.error("Transcription failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=30)
