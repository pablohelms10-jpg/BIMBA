from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    status: JobStatus
    progress: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class TranscriptSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chunk_index: int
    start_time: float
    end_time: float
    transcript: Optional[str] = None
    language: Optional[str] = None


class VisualFrameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: Optional[float] = None
    image_path: Optional[str] = None
    slide_number: Optional[int] = None
    ocr_text: Optional[str] = None
    slide_title: Optional[str] = None
