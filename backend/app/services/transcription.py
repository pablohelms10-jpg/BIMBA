from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

MEDICAL_INITIAL_PROMPT = (
    "Transcripción de clase de medicina. Vocabulario médico especializado: "
    "farmacocinética, farmacodinámica, patología, fisiopatología, diagnóstico diferencial, "
    "tratamiento, pronóstico, anatomía, fisiología, bioquímica, microbiología, "
    "inmunología, histología, embriología, neurología, cardiología, neumología, "
    "gastroenterología, nefrología, endocrinología, hematología, oncología."
)


@dataclass
class TranscriptChunk:
    chunk_index: int
    start_time: float
    end_time: float
    transcript: str
    language: str


class TranscriptionService:
    """Chunked audio transcription using faster-whisper."""

    def __init__(self) -> None:
        self._model = None  # Lazy load to avoid import at module level

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # type: ignore

            device = "cpu"
            compute_type = "int8"
            try:
                import torch  # type: ignore
                if torch.cuda.is_available():
                    device = "cuda"
                    compute_type = "float16"
                    logger.info("Using CUDA for Whisper inference")
            except ImportError:
                pass

            logger.info("Loading Whisper model: %s on %s", settings.whisper_model, device)
            self._model = WhisperModel(
                settings.whisper_model,
                device=device,
                compute_type=compute_type,
            )
        return self._model

    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> List[TranscriptChunk]:
        """
        Transcribe an audio file by splitting it into CHUNK_DURATION_SECONDS chunks.
        Returns a list of TranscriptChunk with absolute timestamps.
        """
        from app.utils.chunker import split_audio_into_chunks
        from app.utils.ffmpeg import get_audio_duration

        total_duration = get_audio_duration(audio_path)
        logger.info("Total audio duration: %.1f seconds", total_duration)

        chunk_paths = split_audio_into_chunks(
            audio_path,
            chunk_duration=settings.chunk_duration_seconds,
            overlap=settings.chunk_overlap_seconds,
        )

        model = self._get_model()
        results: List[TranscriptChunk] = []

        for idx, (chunk_path, chunk_start) in enumerate(chunk_paths):
            logger.info("Transcribing chunk %d/%d (start=%.1f)", idx + 1, len(chunk_paths), chunk_start)
            try:
                segments, info = model.transcribe(
                    chunk_path,
                    language=language or settings.whisper_language or None,
                    initial_prompt=MEDICAL_INITIAL_PROMPT,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 500},
                )
                segment_list = list(segments)
                full_text = " ".join(s.text.strip() for s in segment_list).strip()

                # Calculate actual end time from last segment or chunk duration
                if segment_list:
                    chunk_end = chunk_start + segment_list[-1].end
                else:
                    chunk_end = chunk_start + settings.chunk_duration_seconds

                results.append(
                    TranscriptChunk(
                        chunk_index=idx,
                        start_time=chunk_start,
                        end_time=min(chunk_end, total_duration),
                        transcript=full_text,
                        language=info.language or "es",
                    )
                )
            except Exception as exc:
                logger.error("Failed to transcribe chunk %d: %s", idx, exc)
                results.append(
                    TranscriptChunk(
                        chunk_index=idx,
                        start_time=chunk_start,
                        end_time=chunk_start + settings.chunk_duration_seconds,
                        transcript="",
                        language="es",
                    )
                )
            finally:
                try:
                    os.unlink(chunk_path)
                except OSError:
                    pass

        return results
