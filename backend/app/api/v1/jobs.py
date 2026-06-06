from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.job import ProcessingJob
from app.models.segment import AudioSegment, VisualFrame
from app.schemas.job import JobRead, TranscriptSegmentRead, VisualFrameRead

router = APIRouter()


@router.get("/{document_id}", response_model=JobRead)
async def get_job_status(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    """Get the latest processing job status for a document."""
    result = await session.execute(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document_id)
        .order_by(ProcessingJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No job found for this document.")
    return JobRead.model_validate(job)


@router.get("/{document_id}/transcript", response_model=List[TranscriptSegmentRead])
async def get_transcript(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> List[TranscriptSegmentRead]:
    """Get all audio/transcript segments for a document, ordered by chunk index."""
    result = await session.execute(
        select(AudioSegment)
        .where(AudioSegment.document_id == document_id)
        .order_by(AudioSegment.chunk_index)
    )
    segments = result.scalars().all()
    return [TranscriptSegmentRead.model_validate(s) for s in segments]


@router.get("/{document_id}/frames", response_model=List[VisualFrameRead])
async def get_frames(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> List[VisualFrameRead]:
    """Get all detected visual frames/slides for a document."""
    result = await session.execute(
        select(VisualFrame)
        .where(VisualFrame.document_id == document_id)
        .order_by(VisualFrame.slide_number)
    )
    frames = result.scalars().all()
    return [VisualFrameRead.model_validate(f) for f in frames]
