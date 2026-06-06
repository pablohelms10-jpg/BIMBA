from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import imagehash  # type: ignore
from PIL import Image

from app.config import settings
from app.utils.ffmpeg import extract_frames_1fps

logger = logging.getLogger(__name__)


@dataclass
class DetectedFrame:
    timestamp: float          # seconds from start of video
    image_path: str           # local temp path to the frame image
    slide_number: int         # sequential slide index (1-based)


class VisionService:
    """Slide-change detection from video frames using perceptual hashing."""

    def detect_slides_from_video(
        self,
        video_path: str,
        output_dir: str,
    ) -> List[DetectedFrame]:
        """
        Extract 1fps frames, detect slide changes via pHash, return unique slides.

        Args:
            video_path: Path to the input video file.
            output_dir: Directory where unique slide images are stored.

        Returns:
            List of DetectedFrame for each detected unique slide.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Extract all frames at 1fps
        frames_dir = os.path.join(output_dir, "_raw_frames")
        os.makedirs(frames_dir, exist_ok=True)

        logger.info("Extracting frames from video: %s", video_path)
        frame_paths: List[Tuple[float, str]] = extract_frames_1fps(video_path, frames_dir)
        logger.info("Extracted %d raw frames", len(frame_paths))

        if not frame_paths:
            return []

        detected: List[DetectedFrame] = []
        prev_hash: imagehash.ImageHash | None = None
        slide_number = 0

        for timestamp, frame_path in frame_paths:
            try:
                img = Image.open(frame_path)
                current_hash = imagehash.phash(img)
                img.close()
            except Exception as exc:
                logger.warning("Could not hash frame at %.1f: %s", timestamp, exc)
                try:
                    os.unlink(frame_path)
                except OSError:
                    pass
                continue

            is_new_slide = (
                prev_hash is None
                or (current_hash - prev_hash) > settings.slide_change_threshold
            )

            if is_new_slide:
                slide_number += 1
                dest_path = os.path.join(output_dir, f"slide_{slide_number:04d}.jpg")
                try:
                    os.rename(frame_path, dest_path)
                except OSError:
                    import shutil
                    shutil.copy2(frame_path, dest_path)
                    os.unlink(frame_path)

                detected.append(
                    DetectedFrame(
                        timestamp=timestamp,
                        image_path=dest_path,
                        slide_number=slide_number,
                    )
                )
                prev_hash = current_hash
                logger.debug("New slide %d at %.1f seconds", slide_number, timestamp)
            else:
                try:
                    os.unlink(frame_path)
                except OSError:
                    pass

        # Clean up raw frames dir
        try:
            os.rmdir(frames_dir)
        except OSError:
            pass

        logger.info("Detected %d unique slides", len(detected))
        return detected

    def detect_slides_from_pdf_images(
        self,
        image_paths: List[str],
    ) -> List[DetectedFrame]:
        """
        Treat each PDF page image as a slide. Returns DetectedFrame list.
        For PDFs, timestamp is None (no time dimension).
        """
        detected: List[DetectedFrame] = []
        for idx, img_path in enumerate(image_paths, start=1):
            detected.append(
                DetectedFrame(
                    timestamp=float(idx),  # Use page number as pseudo-timestamp
                    image_path=img_path,
                    slide_number=idx,
                )
            )
        return detected
