from __future__ import annotations

import logging
import os
import tempfile
from typing import List

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.vision_tasks.detect_and_ocr_slides", max_retries=2)
def detect_and_ocr_slides(self, video_path: str, document_id: str, frames_dir: str) -> List[dict]:
    """
    Celery task: detect slides from video and run OCR on each.

    Returns:
        List of dicts: [{timestamp, image_path, slide_number, ocr_text, slide_title}, ...]
    """
    from app.services.vision import VisionService
    from app.services.ocr import OCRService

    logger.info("Starting slide detection for document %s", document_id)
    try:
        vision_svc = VisionService()
        ocr_svc = OCRService()

        detected = vision_svc.detect_slides_from_video(video_path, frames_dir)
        results = []
        for frame in detected:
            ocr_result = ocr_svc.ocr_image(frame.image_path)
            results.append({
                "timestamp": frame.timestamp,
                "image_path": frame.image_path,
                "slide_number": frame.slide_number,
                "ocr_text": ocr_result.full_text,
                "slide_title": ocr_result.title,
            })
        return results
    except Exception as exc:
        logger.error("Vision/OCR failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="app.tasks.vision_tasks.ocr_pdf", max_retries=2)
def ocr_pdf(self, pdf_path: str, document_id: str) -> List[dict]:
    """
    Celery task: extract text from a PDF (pdfplumber + OCR fallback).

    Returns:
        List of dicts: [{page_number, full_text, title, body}, ...]
    """
    from app.services.ocr import OCRService

    logger.info("Starting PDF OCR for document %s", document_id)
    try:
        svc = OCRService()
        pages = svc.extract_pdf_text(pdf_path)
        return [
            {
                "page_number": p.page_number,
                "full_text": p.full_text,
                "title": p.title,
                "body": p.body,
            }
            for p in pages
        ]
    except Exception as exc:
        logger.error("PDF OCR failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=30)
