from __future__ import annotations

import logging
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.models.document import Document, DocumentStatus, SourceType
from app.models.job import ProcessingJob, JobStatus
from app.schemas.document import DocumentList, DocumentRead, UrlIngest
from app.services.storage import StorageService
from app.tasks.pipeline import process_document_task

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "audio/x-m4a",
    "audio/mp4",
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "text/plain",
}

SOURCE_TYPE_FROM_MIME: dict[str, SourceType] = {
    "video/": SourceType.video,
    "audio/": SourceType.audio,
    "application/pdf": SourceType.pdf,
    "image/": SourceType.image,
    "text/": SourceType.text,
}


def _detect_source_type(content_type: str) -> SourceType:
    for prefix, stype in SOURCE_TYPE_FROM_MIME.items():
        if content_type.startswith(prefix):
            return stype
    return SourceType.text


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(default=""),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    """Upload a file (video/audio/pdf/image/text) and start processing."""
    content_type = file.content_type or "application/octet-stream"

    if content_type not in ALLOWED_MIME_TYPES and not any(
        content_type.startswith(p) for p in ["video/", "audio/", "image/", "text/"]
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}",
        )

    # Read file into memory for size check
    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb} MB.",
        )

    source_type = _detect_source_type(content_type)
    doc_title = title.strip() or (file.filename or "Untitled")

    # Upload to MinIO
    storage = StorageService()
    doc_id = uuid.uuid4()
    object_name = f"uploads/{doc_id}/{file.filename}"
    await storage.upload_bytes(object_name, file_bytes, content_type)

    # Create document record
    document = Document(
        id=doc_id,
        title=doc_title,
        source_type=source_type,
        file_path=object_name,
        status=DocumentStatus.pending,
    )
    session.add(document)

    # Create job record
    job = ProcessingJob(
        document_id=doc_id,
        status=JobStatus.pending,
        progress=0,
        current_stage="Encolado para procesamiento",
    )
    session.add(job)
    await session.flush()

    # Enqueue Celery task
    task = process_document_task.apply_async(
        args=[str(doc_id), str(job.id)],
        queue=settings.celery_queue_high,
    )
    job.celery_task_id = task.id
    await session.flush()

    logger.info("Document %s enqueued for processing (task %s)", doc_id, task.id)
    return DocumentRead.model_validate(document)


@router.post("/url", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def ingest_url(
    payload: UrlIngest,
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    """Process a URL (YouTube video or web page)."""
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL must not be empty.")

    is_youtube = any(
        host in url for host in ["youtube.com/watch", "youtu.be/", "youtube.com/shorts"]
    )
    source_type = SourceType.youtube if is_youtube else SourceType.url
    doc_title = payload.title or url

    doc_id = uuid.uuid4()
    document = Document(
        id=doc_id,
        title=doc_title,
        source_type=source_type,
        source_url=url,
        status=DocumentStatus.pending,
    )
    session.add(document)

    job = ProcessingJob(
        document_id=doc_id,
        status=JobStatus.pending,
        progress=0,
        current_stage="Encolado para procesamiento",
    )
    session.add(job)
    await session.flush()

    task = process_document_task.apply_async(
        args=[str(doc_id), str(job.id)],
        queue=settings.celery_queue_high,
    )
    job.celery_task_id = task.id
    await session.flush()

    logger.info("URL %s enqueued for processing (task %s)", url, task.id)
    return DocumentRead.model_validate(document)


@router.get("", response_model=List[DocumentList])
async def list_documents(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 50,
) -> List[DocumentList]:
    """List all documents, most recent first."""
    result = await session.execute(
        select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
    )
    docs = result.scalars().all()
    return [DocumentList.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    """Get document details by ID."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a document and all associated files."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete from MinIO if stored
    if document.file_path:
        storage = StorageService()
        try:
            await storage.delete_prefix(f"uploads/{document_id}/")
            await storage.delete_prefix(f"frames/{document_id}/")
            await storage.delete_prefix(f"exports/{document_id}/")
        except Exception as exc:
            logger.warning("Could not fully clean MinIO for doc %s: %s", document_id, exc)

    await session.delete(document)
    logger.info("Document %s deleted", document_id)
