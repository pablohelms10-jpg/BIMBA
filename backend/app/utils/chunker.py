from __future__ import annotations

import logging
import os
import tempfile
from typing import List, Tuple

from app.config import settings
from app.utils.ffmpeg import extract_audio_chunk, get_audio_duration

logger = logging.getLogger(__name__)


def split_audio_into_chunks(
    audio_path: str,
    chunk_duration: int = 300,
    overlap: int = 10,
) -> List[Tuple[str, float]]:
    """
    Split an audio file into overlapping chunks using FFmpeg.

    Each chunk is CHUNK_DURATION seconds long with OVERLAP seconds of context
    from the previous chunk.

    Args:
        audio_path: Path to the source audio file (WAV, MP3, etc.).
        chunk_duration: Duration of each chunk in seconds.
        overlap: Overlap in seconds between consecutive chunks.

    Returns:
        List of (chunk_file_path, start_time_absolute) tuples.
        The caller is responsible for deleting temporary files.
    """
    total_duration = get_audio_duration(audio_path)
    logger.info(
        "Splitting audio (%.1f s) into chunks of %d s with %d s overlap",
        total_duration,
        chunk_duration,
        overlap,
    )

    chunks: List[Tuple[str, float]] = []
    start = 0.0
    step = max(chunk_duration - overlap, 1)  # advance by this many seconds each iteration

    while start < total_duration:
        actual_duration = min(chunk_duration, total_duration - start)
        if actual_duration < 1.0:
            break  # skip tiny trailing chunks

        tmp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            prefix=f"bimba_chunk_{len(chunks)}_",
            delete=False,
        )
        tmp_path = tmp_file.name
        tmp_file.close()

        try:
            extract_audio_chunk(audio_path, start, actual_duration, tmp_path)
            chunks.append((tmp_path, start))
            logger.debug("Created chunk %d: %.1f–%.1f s → %s", len(chunks), start, start + actual_duration, tmp_path)
        except Exception as exc:
            logger.error("Failed to extract chunk at %.1f s: %s", start, exc)
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        start += step

    logger.info("Created %d audio chunks", len(chunks))
    return chunks
