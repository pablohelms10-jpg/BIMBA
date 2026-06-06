from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class NoteSection(BaseModel):
    id: str
    title: str
    slide_number: Optional[int] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    content: str
    key_concepts: List[str] = []
    source_segments: List[str] = []
    source_frames: List[str] = []


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    content: Optional[Dict[str, Any]] = None
    format_version: int
    exported_paths: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class SemanticLinkPatch(BaseModel):
    """Manual correction of a semantic link between an audio segment and a visual frame."""

    audio_segment_id: uuid.UUID
    visual_frame_id: uuid.UUID
    similarity_score: float = 1.0
    action: str = "add"  # "add" | "remove"
