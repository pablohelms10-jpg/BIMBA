from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, Text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AudioSegment(Base):
    __tablename__ = "audio_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(  # type: ignore[name-defined]
        "Document", back_populates="audio_segments"
    )
    semantic_links: Mapped[list["SemanticLink"]] = relationship(
        "SemanticLink", back_populates="audio_segment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AudioSegment id={self.id} chunk={self.chunk_index} [{self.start_time:.1f}-{self.end_time:.1f}]>"


class VisualFrame(Base):
    __tablename__ = "visual_frames"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    slide_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    slide_title: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(  # type: ignore[name-defined]
        "Document", back_populates="visual_frames"
    )
    semantic_links: Mapped[list["SemanticLink"]] = relationship(
        "SemanticLink", back_populates="visual_frame", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VisualFrame id={self.id} slide={self.slide_number} ts={self.timestamp}>"


class SemanticLink(Base):
    __tablename__ = "semantic_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audio_segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audio_segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visual_frame_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visual_frames.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    audio_segment: Mapped["AudioSegment"] = relationship(
        "AudioSegment", back_populates="semantic_links"
    )
    visual_frame: Mapped["VisualFrame"] = relationship(
        "VisualFrame", back_populates="semantic_links"
    )

    def __repr__(self) -> str:
        return f"<SemanticLink audio={self.audio_segment_id} frame={self.visual_frame_id} score={self.similarity_score:.3f}>"
