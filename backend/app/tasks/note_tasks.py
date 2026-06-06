from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.note_tasks.generate_notes", max_retries=2)
def generate_notes(
    self,
    document_id: str,
    document_title: str,
    sections_input: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Celery task: generate full structured notes via Claude for all sections.

    Args:
        document_id: Document UUID string.
        document_title: Human-readable title for the note document.
        sections_input: List of section dicts, each containing:
            - slide_title, slide_ocr, transcripts, timestamps,
              slide_number, source_segments, source_frames

    Returns:
        Complete note content dict (matches Note.content JSONB schema).
    """
    from app.services.note_generator import NoteGeneratorService

    logger.info("Generating notes for document %s (%d sections)", document_id, len(sections_input))
    svc = NoteGeneratorService()
    sections_data = []

    for idx, sec in enumerate(sections_input):
        logger.debug("Generating section %d/%d", idx + 1, len(sections_input))
        try:
            section_note = svc.generate_section_note(
                slide_title=sec.get("slide_title"),
                slide_ocr=sec.get("slide_ocr"),
                transcripts=sec.get("transcripts", []),
                timestamps=sec.get("timestamps", []),
            )
        except Exception as exc:
            logger.error("Failed to generate section %d: %s", idx, exc)
            section_note = {
                "title": sec.get("slide_title") or f"Sección {idx + 1}",
                "content": "[Error al generar esta sección]",
                "key_concepts": [],
                "summary": "",
            }

        section_note["slide_number"] = sec.get("slide_number")
        section_note["timestamp_start"] = sec.get("timestamp_start")
        section_note["timestamp_end"] = sec.get("timestamp_end")
        section_note["source_segments"] = sec.get("source_segments", [])
        section_note["source_frames"] = sec.get("source_frames", [])
        sections_data.append(section_note)

    return svc.build_full_note(document_title, sections_data)
