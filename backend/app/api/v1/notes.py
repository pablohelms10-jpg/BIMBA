from __future__ import annotations

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.note import Note
from app.models.segment import AudioSegment, SemanticLink, VisualFrame
from app.schemas.note import NoteRead, SemanticLinkPatch
from app.utils.exporters import export_note

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_FORMATS = {"pdf", "docx", "md", "txt"}


@router.get("/{document_id}", response_model=NoteRead)
async def get_notes(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> NoteRead:
    """Get the generated notes for a document (JSON structure)."""
    result = await session.execute(
        select(Note).where(Note.document_id == document_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Notes not found for this document. Processing may not be complete.")
    return NoteRead.model_validate(note)


@router.get("/{document_id}/export/{format}")
async def export_notes(
    document_id: uuid.UUID,
    format: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export notes in the requested format: pdf, docx, md, or txt."""
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{format}'. Supported: {', '.join(SUPPORTED_FORMATS)}",
        )

    result = await session.execute(
        select(Note).where(Note.document_id == document_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Notes not found for this document.")
    if not note.content:
        raise HTTPException(status_code=422, detail="Note content is empty.")

    content_bytes, media_type, filename = await export_note(note.content, format, str(document_id))

    # Persist the exported path
    exported_paths = note.exported_paths or {}
    exported_paths[format] = filename
    note.exported_paths = exported_paths
    await session.flush()

    return Response(
        content=content_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{document_id}/links", status_code=204)
async def patch_semantic_links(
    document_id: uuid.UUID,
    patches: List[SemanticLinkPatch],
    session: AsyncSession = Depends(get_session),
) -> None:
    """Manually add or remove semantic links between audio segments and visual frames."""
    for patch in patches:
        if patch.action == "add":
            # Verify both segment and frame belong to this document
            seg_result = await session.execute(
                select(AudioSegment).where(
                    AudioSegment.id == patch.audio_segment_id,
                    AudioSegment.document_id == document_id,
                )
            )
            segment = seg_result.scalar_one_or_none()
            if not segment:
                raise HTTPException(
                    status_code=404,
                    detail=f"AudioSegment {patch.audio_segment_id} not found for this document.",
                )

            frame_result = await session.execute(
                select(VisualFrame).where(
                    VisualFrame.id == patch.visual_frame_id,
                    VisualFrame.document_id == document_id,
                )
            )
            frame = frame_result.scalar_one_or_none()
            if not frame:
                raise HTTPException(
                    status_code=404,
                    detail=f"VisualFrame {patch.visual_frame_id} not found for this document.",
                )

            # Check if link already exists
            existing = await session.execute(
                select(SemanticLink).where(
                    SemanticLink.audio_segment_id == patch.audio_segment_id,
                    SemanticLink.visual_frame_id == patch.visual_frame_id,
                )
            )
            link = existing.scalar_one_or_none()
            if not link:
                link = SemanticLink(
                    audio_segment_id=patch.audio_segment_id,
                    visual_frame_id=patch.visual_frame_id,
                    similarity_score=patch.similarity_score,
                )
                session.add(link)
            else:
                link.similarity_score = patch.similarity_score

        elif patch.action == "remove":
            existing = await session.execute(
                select(SemanticLink).where(
                    SemanticLink.audio_segment_id == patch.audio_segment_id,
                    SemanticLink.visual_frame_id == patch.visual_frame_id,
                )
            )
            link = existing.scalar_one_or_none()
            if link:
                await session.delete(link)

    await session.flush()
    logger.info("Applied %d semantic link patches for document %s", len(patches), document_id)
