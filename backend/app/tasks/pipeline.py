from __future__ import annotations

import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _make_sync_session():
    """Create a synchronous SQLAlchemy session for use inside Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings

    # Convert asyncpg URL to psycopg2 for sync Celery use
    sync_url = settings.database_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


def _update_job(session, job_id: str, **kwargs) -> None:
    """Update a ProcessingJob record within a sync session."""
    from app.models.job import ProcessingJob

    job = session.get(ProcessingJob, uuid.UUID(job_id))
    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        session.commit()


@celery_app.task(
    bind=True,
    name="app.tasks.pipeline.process_document_task",
    max_retries=2,
    soft_time_limit=7200,  # 2 hours
    time_limit=7500,
)
def process_document_task(self, document_id: str, job_id: str) -> None:
    """
    Main orchestration task for processing a BIMBA document.

    Pipeline stages:
    1. Fetch document metadata and download file from MinIO.
    2. Route based on source_type:
       - video:   extract audio → transcribe → detect slides → OCR
       - audio:   transcribe chunks
       - pdf:     pdfplumber text + convert pages to images + OCR
       - image:   OCR
       - youtube: yt-dlp download → treat as video
       - url:     beautifulsoup text extraction
    3. Compute embeddings for all segments and frames.
    4. Semantic linking.
    5. Generate notes with Claude.
    6. Persist all results to the database.
    7. Mark job as completed.
    """
    from app.config import settings
    from app.models.document import Document, DocumentStatus, SourceType
    from app.models.job import JobStatus
    from app.models.segment import AudioSegment, SemanticLink, VisualFrame
    from app.models.note import Note
    from app.services.storage import StorageService
    from app.services.transcription import TranscriptionService
    from app.services.vision import VisionService
    from app.services.ocr import OCRService
    from app.services.embeddings import EmbeddingService
    from app.services.vector_store import VectorStoreService
    from app.services.semantic_linker import SemanticLinker
    from app.services.note_generator import NoteGeneratorService
    from app.utils.ffmpeg import extract_audio_from_video

    session = _make_sync_session()
    storage = StorageService()
    doc_uuid = uuid.UUID(document_id)

    try:
        # ------------------------------------------------------------------ #
        # Stage 0: Initialise
        # ------------------------------------------------------------------ #
        document = session.get(Document, doc_uuid)
        if not document:
            logger.error("Document %s not found", document_id)
            return

        _update_job(
            session, job_id,
            status=JobStatus.processing,
            started_at=datetime.now(timezone.utc),
            progress=2,
            current_stage="Iniciando procesamiento",
        )
        document.status = DocumentStatus.processing
        session.commit()

        source_type = document.source_type
        logger.info("Processing document %s (type=%s)", document_id, source_type)

        workdir = tempfile.mkdtemp(prefix=f"bimba_{document_id}_")
        audio_segments_data: List[Dict] = []
        visual_frames_data: List[Dict] = []

        # ------------------------------------------------------------------ #
        # Stage 1: Download source file
        # ------------------------------------------------------------------ #
        _update_job(session, job_id, progress=5, current_stage="Descargando archivo")

        local_source_path: Optional[str] = None

        if source_type in (SourceType.video, SourceType.audio, SourceType.pdf, SourceType.image, SourceType.text):
            if document.file_path:
                ext = os.path.splitext(document.file_path)[1] or ""
                local_source_path = os.path.join(workdir, f"source{ext}")
                storage.download_to_file.__func__ if False else None  # type: ignore
                # Use sync boto3 client directly
                import boto3
                from botocore.client import Config as BotoConfig
                client = boto3.client(
                    "s3",
                    endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
                    aws_access_key_id=settings.minio_access_key,
                    aws_secret_access_key=settings.minio_secret_key,
                    config=BotoConfig(signature_version="s3v4"),
                    region_name="us-east-1",
                )
                client.download_file(settings.minio_bucket, document.file_path, local_source_path)
                logger.info("Downloaded source file to %s", local_source_path)

        elif source_type == SourceType.youtube:
            _update_job(session, job_id, progress=5, current_stage="Descargando video de YouTube")
            local_source_path = _download_youtube(document.source_url, workdir)
            source_type = SourceType.video  # treat as video after download

        elif source_type == SourceType.url:
            _update_job(session, job_id, progress=5, current_stage="Descargando página web")
            text_content = _fetch_url_text(document.source_url)
            txt_path = os.path.join(workdir, "page.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            local_source_path = txt_path
            source_type = SourceType.text

        # ------------------------------------------------------------------ #
        # Stage 2: Type-specific processing
        # ------------------------------------------------------------------ #

        if source_type == SourceType.video:
            _update_job(session, job_id, progress=10, current_stage="Extrayendo audio del video")
            audio_path = os.path.join(workdir, "audio.wav")
            extract_audio_from_video(local_source_path, audio_path)

            _update_job(session, job_id, progress=20, current_stage="Transcribiendo audio")
            svc = TranscriptionService()
            chunks = svc.transcribe_file(audio_path)
            audio_segments_data = [
                {
                    "chunk_index": c.chunk_index,
                    "start_time": c.start_time,
                    "end_time": c.end_time,
                    "transcript": c.transcript,
                    "language": c.language,
                }
                for c in chunks
            ]

            _update_job(session, job_id, progress=50, current_stage="Detectando slides y OCR")
            frames_dir = os.path.join(workdir, "frames")
            vision_svc = VisionService()
            ocr_svc = OCRService()
            detected = vision_svc.detect_slides_from_video(local_source_path, frames_dir)
            visual_frames_data = _ocr_detected_frames(detected, ocr_svc, document_id, storage)

        elif source_type == SourceType.audio:
            _update_job(session, job_id, progress=15, current_stage="Transcribiendo audio")
            svc = TranscriptionService()
            chunks = svc.transcribe_file(local_source_path)
            audio_segments_data = [
                {
                    "chunk_index": c.chunk_index,
                    "start_time": c.start_time,
                    "end_time": c.end_time,
                    "transcript": c.transcript,
                    "language": c.language,
                }
                for c in chunks
            ]

        elif source_type == SourceType.pdf:
            _update_job(session, job_id, progress=10, current_stage="Extrayendo texto del PDF")
            ocr_svc = OCRService()
            pages = ocr_svc.extract_pdf_text(local_source_path)

            # Convert pages to images for visual frames
            images_dir = os.path.join(workdir, "pdf_images")
            image_paths = ocr_svc.convert_pdf_to_images(local_source_path, images_dir)

            for idx, page in enumerate(pages):
                img_path = image_paths[idx] if idx < len(image_paths) else None
                minio_key = None
                if img_path:
                    minio_key = f"frames/{document_id}/page_{idx + 1:04d}.jpg"
                    with open(img_path, "rb") as f:
                        import boto3
                        from botocore.client import Config as BotoConfig
                        client = boto3.client(
                            "s3",
                            endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
                            aws_access_key_id=settings.minio_access_key,
                            aws_secret_access_key=settings.minio_secret_key,
                            config=BotoConfig(signature_version="s3v4"),
                            region_name="us-east-1",
                        )
                        client.put_object(
                            Bucket=settings.minio_bucket,
                            Key=minio_key,
                            Body=f.read(),
                            ContentType="image/jpeg",
                        )

                visual_frames_data.append({
                    "timestamp": float(idx + 1),
                    "image_path": minio_key,
                    "slide_number": idx + 1,
                    "ocr_text": page.full_text,
                    "slide_title": page.title,
                })

            # No audio for PDFs
            audio_segments_data = []

        elif source_type == SourceType.image:
            _update_job(session, job_id, progress=10, current_stage="Aplicando OCR a imagen")
            ocr_svc = OCRService()
            ocr_result = ocr_svc.ocr_image(local_source_path)
            minio_key = f"frames/{document_id}/slide_0001.jpg"
            with open(local_source_path, "rb") as f:
                import boto3
                from botocore.client import Config as BotoConfig
                client = boto3.client(
                    "s3",
                    endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
                    aws_access_key_id=settings.minio_access_key,
                    aws_secret_access_key=settings.minio_secret_key,
                    config=BotoConfig(signature_version="s3v4"),
                    region_name="us-east-1",
                )
                client.put_object(
                    Bucket=settings.minio_bucket,
                    Key=minio_key,
                    Body=f.read(),
                    ContentType="image/jpeg",
                )
            visual_frames_data = [{
                "timestamp": 0.0,
                "image_path": minio_key,
                "slide_number": 1,
                "ocr_text": ocr_result.full_text,
                "slide_title": ocr_result.title,
            }]
            audio_segments_data = []

        elif source_type == SourceType.text:
            with open(local_source_path, "r", encoding="utf-8", errors="replace") as f:
                text_body = f.read()
            # Treat entire text as a single audio segment (no real audio)
            audio_segments_data = [{
                "chunk_index": 0,
                "start_time": 0.0,
                "end_time": 0.0,
                "transcript": text_body,
                "language": "es",
            }]

        # ------------------------------------------------------------------ #
        # Stage 3: Persist segments and frames to DB
        # ------------------------------------------------------------------ #
        _update_job(session, job_id, progress=60, current_stage="Guardando segmentos en base de datos")

        segment_ids: List[str] = []
        for seg_data in audio_segments_data:
            seg = AudioSegment(
                document_id=doc_uuid,
                chunk_index=seg_data["chunk_index"],
                start_time=seg_data["start_time"],
                end_time=seg_data["end_time"],
                transcript=seg_data["transcript"],
                language=seg_data["language"],
            )
            session.add(seg)
            session.flush()
            segment_ids.append(str(seg.id))
            seg_data["db_id"] = str(seg.id)

        frame_ids: List[str] = []
        for frame_data in visual_frames_data:
            frame = VisualFrame(
                document_id=doc_uuid,
                timestamp=frame_data.get("timestamp"),
                image_path=frame_data.get("image_path"),
                slide_number=frame_data.get("slide_number"),
                ocr_text=frame_data.get("ocr_text"),
                slide_title=frame_data.get("slide_title"),
            )
            session.add(frame)
            session.flush()
            frame_ids.append(str(frame.id))
            frame_data["db_id"] = str(frame.id)

        session.commit()

        # ------------------------------------------------------------------ #
        # Stage 4: Embeddings + Qdrant
        # ------------------------------------------------------------------ #
        _update_job(session, job_id, progress=70, current_stage="Generando embeddings semánticos")

        embed_svc = EmbeddingService()
        vector_store = VectorStoreService()

        if audio_segments_data:
            seg_texts = [s.get("transcript") or "" for s in audio_segments_data]
            seg_vectors = embed_svc.embed_batch(seg_texts)
            for seg_data, vec in zip(audio_segments_data, seg_vectors):
                vector_store.upsert_segment_embedding(
                    segment_id=seg_data["db_id"],
                    document_id=document_id,
                    vector=vec,
                    payload={"chunk_index": seg_data["chunk_index"]},
                )

        if visual_frames_data:
            frame_texts = [f.get("ocr_text") or "" for f in visual_frames_data]
            frame_vectors = embed_svc.embed_batch(frame_texts)
            for frame_data, vec in zip(visual_frames_data, frame_vectors):
                vector_store.upsert_frame_embedding(
                    frame_id=frame_data["db_id"],
                    document_id=document_id,
                    vector=vec,
                    payload={"slide_number": frame_data.get("slide_number")},
                )

        # ------------------------------------------------------------------ #
        # Stage 5: Semantic linking
        # ------------------------------------------------------------------ #
        _update_job(session, job_id, progress=78, current_stage="Enlazando semánticamente audio y slides")

        link_candidates = []
        if audio_segments_data and visual_frames_data:
            linker = SemanticLinker()
            segments_for_linking = [
                {"id": s["db_id"], "transcript": s.get("transcript") or ""}
                for s in audio_segments_data
            ]
            frames_for_linking = [
                {"id": f["db_id"], "ocr_text": f.get("ocr_text") or ""}
                for f in visual_frames_data
            ]
            link_candidates = linker.compute_links(segments_for_linking, frames_for_linking)

            for lc in link_candidates:
                sl = SemanticLink(
                    audio_segment_id=uuid.UUID(lc.audio_segment_id),
                    visual_frame_id=uuid.UUID(lc.visual_frame_id),
                    similarity_score=lc.similarity_score,
                )
                session.add(sl)
            session.commit()

        # ------------------------------------------------------------------ #
        # Stage 6: Build note sections input
        # ------------------------------------------------------------------ #
        _update_job(session, job_id, progress=82, current_stage="Preparando generación de notas")

        # Group linked segments by frame
        frame_to_segments: Dict[str, List[Dict]] = {}
        seg_map = {s["db_id"]: s for s in audio_segments_data}

        for lc in link_candidates:
            frame_to_segments.setdefault(lc.visual_frame_id, []).append(
                seg_map.get(lc.audio_segment_id, {})
            )

        sections_input = []

        # One section per visual frame (or per audio segment if no frames)
        if visual_frames_data:
            for frame_data in visual_frames_data:
                fid = frame_data["db_id"]
                linked_segs = frame_to_segments.get(fid, [])
                transcripts = [s.get("transcript") or "" for s in linked_segs]
                timestamps = [(s.get("start_time", 0.0), s.get("end_time", 0.0)) for s in linked_segs]

                sections_input.append({
                    "slide_title": frame_data.get("slide_title"),
                    "slide_ocr": frame_data.get("ocr_text"),
                    "transcripts": transcripts,
                    "timestamps": timestamps,
                    "slide_number": frame_data.get("slide_number"),
                    "timestamp_start": timestamps[0][0] if timestamps else None,
                    "timestamp_end": timestamps[-1][1] if timestamps else None,
                    "source_segments": [s.get("db_id", "") for s in linked_segs],
                    "source_frames": [fid],
                })
        elif audio_segments_data:
            # Pure audio: one section per chunk
            for seg_data in audio_segments_data:
                sections_input.append({
                    "slide_title": None,
                    "slide_ocr": None,
                    "transcripts": [seg_data.get("transcript") or ""],
                    "timestamps": [(seg_data.get("start_time", 0.0), seg_data.get("end_time", 0.0))],
                    "slide_number": None,
                    "timestamp_start": seg_data.get("start_time"),
                    "timestamp_end": seg_data.get("end_time"),
                    "source_segments": [seg_data.get("db_id", "")],
                    "source_frames": [],
                })

        # ------------------------------------------------------------------ #
        # Stage 7: Generate notes with Claude
        # ------------------------------------------------------------------ #
        _update_job(session, job_id, progress=85, current_stage="Generando notas con IA")

        note_svc = NoteGeneratorService()
        sections_data = []
        total = len(sections_input)

        for idx, sec in enumerate(sections_input):
            progress_val = 85 + int((idx / max(total, 1)) * 12)
            _update_job(
                session, job_id,
                progress=progress_val,
                current_stage=f"Generando notas (sección {idx + 1}/{total})",
            )
            try:
                section_note = note_svc.generate_section_note(
                    slide_title=sec.get("slide_title"),
                    slide_ocr=sec.get("slide_ocr"),
                    transcripts=sec.get("transcripts", []),
                    timestamps=sec.get("timestamps", []),
                )
            except Exception as exc:
                logger.error("Section %d note generation failed: %s", idx, exc)
                section_note = {
                    "title": sec.get("slide_title") or f"Sección {idx + 1}",
                    "content": "[Error al generar esta sección]",
                    "key_concepts": [],
                    "summary": "",
                }
            section_note.update({
                "slide_number": sec.get("slide_number"),
                "timestamp_start": sec.get("timestamp_start"),
                "timestamp_end": sec.get("timestamp_end"),
                "source_segments": sec.get("source_segments", []),
                "source_frames": sec.get("source_frames", []),
            })
            sections_data.append(section_note)

        note_content = note_svc.build_full_note(document.title, sections_data)

        # Persist note
        note = Note(
            document_id=doc_uuid,
            content=note_content,
            format_version=1,
            exported_paths={},
        )
        session.add(note)

        # ------------------------------------------------------------------ #
        # Stage 8: Finalise
        # ------------------------------------------------------------------ #
        document.status = DocumentStatus.completed
        session.commit()

        _update_job(
            session, job_id,
            status=JobStatus.completed,
            progress=100,
            current_stage="Procesamiento completado",
            completed_at=datetime.now(timezone.utc),
        )
        logger.info("Document %s processed successfully", document_id)

    except Exception as exc:
        logger.exception("Pipeline failed for document %s: %s", document_id, exc)
        try:
            from app.models.document import DocumentStatus
            from app.models.job import JobStatus
            document = session.get(Document, doc_uuid)
            if document:
                document.status = DocumentStatus.failed
            session.commit()
        except Exception:
            pass
        _update_job(
            session, job_id,
            status=JobStatus.failed,
            error_message=str(exc),
            completed_at=datetime.now(timezone.utc),
        )
        raise self.retry(exc=exc, countdown=60)
    finally:
        session.close()
        # Clean up workdir
        try:
            import shutil
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass


# ---- Helper functions -------------------------------------------------------

def _download_youtube(url: str, workdir: str) -> str:
    """Download a YouTube video using yt-dlp. Returns path to downloaded file."""
    import yt_dlp  # type: ignore

    output_template = os.path.join(workdir, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename


def _fetch_url_text(url: str) -> str:
    """Fetch a web page and extract clean text using BeautifulSoup."""
    import httpx
    from bs4 import BeautifulSoup  # type: ignore

    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove scripts and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _ocr_detected_frames(
    detected: list,
    ocr_svc,
    document_id: str,
    storage,
) -> List[Dict]:
    """Run OCR on detected video frames and upload to MinIO. Returns frame data dicts."""
    from app.config import settings
    import boto3
    from botocore.client import Config as BotoConfig

    client = boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )

    results = []
    for frame in detected:
        ocr_result = ocr_svc.ocr_image(frame.image_path)
        minio_key = f"frames/{document_id}/slide_{frame.slide_number:04d}.jpg"
        try:
            with open(frame.image_path, "rb") as f:
                client.put_object(
                    Bucket=settings.minio_bucket,
                    Key=minio_key,
                    Body=f.read(),
                    ContentType="image/jpeg",
                )
        except Exception as exc:
            logger.warning("Could not upload frame %s to MinIO: %s", minio_key, exc)
            minio_key = frame.image_path  # fall back to local path

        results.append({
            "timestamp": frame.timestamp,
            "image_path": minio_key,
            "slide_number": frame.slide_number,
            "ocr_text": ocr_result.full_text,
            "slide_title": ocr_result.title,
        })
    return results
