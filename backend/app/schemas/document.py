from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.document import DocumentStatus, SourceType


class DocumentCreate(BaseModel):
    title: str
    source_type: SourceType


class UrlIngest(BaseModel):
    url: str
    title: Optional[str] = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_type: SourceType
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_type: SourceType
    status: DocumentStatus
    created_at: datetime
