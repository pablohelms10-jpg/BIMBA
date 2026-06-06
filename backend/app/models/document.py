from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SourceType(str, PyEnum):
    video = "video"
    audio = "audio"
    pdf = "pdf"
    image = "image"
    text = "text"
    url = "url"
    youtube = "youtube"


class DocumentStatus(str, PyEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="sourcetype"), nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="documentstatus"),
        nullable=False,
        default=DocumentStatus.pending,
        server_default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    jobs: Mapped[list["ProcessingJob"]] = relationship(  # type: ignore[name-defined]
        "ProcessingJob", back_populates="document", cascade="all, delete-orphan"
    )
    audio_segments: Mapped[list["AudioSegment"]] = relationship(  # type: ignore[name-defined]
        "AudioSegment", back_populates="document", cascade="all, delete-orphan"
    )
    visual_frames: Mapped[list["VisualFrame"]] = relationship(  # type: ignore[name-defined]
        "VisualFrame", back_populates="document", cascade="all, delete-orphan"
    )
    note: Mapped["Note | None"] = relationship(  # type: ignore[name-defined]
        "Note", back_populates="document", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title!r} status={self.status}>"
