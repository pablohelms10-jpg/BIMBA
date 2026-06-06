from __future__ import annotations

import logging
import os
import subprocess
from typing import List, Tuple

logger = logging.getLogger(__name__)


def get_audio_duration(audio_path: str) -> float:
    """Return duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            audio_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    import json
    data = json.loads(result.stdout)
    for stream in data.get("streams", []):
        duration = stream.get("duration")
        if duration:
            return float(duration)
    raise ValueError(f"Could not determine duration of {audio_path}")


def extract_audio_from_video(video_path: str, output_path: str) -> None:
    """
    Extract audio track from video using FFmpeg.
    Output is WAV 16kHz mono — optimal for Whisper.
    """
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",                   # no video
        "-acodec", "pcm_s16le",  # PCM 16-bit
        "-ar", "16000",          # 16 kHz sample rate
        "-ac", "1",              # mono
        "-y",                    # overwrite output
        output_path,
    ]
    logger.debug("Running ffmpeg: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed:\n{result.stderr}")
    logger.info("Audio extracted to %s", output_path)


def extract_frames_1fps(video_path: str, output_dir: str) -> List[Tuple[float, str]]:
    """
    Extract one frame per second from a video.

    Returns:
        List of (timestamp_seconds, frame_file_path) sorted by timestamp.
    """
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", "fps=1",
        "-frame_pts", "1",
        "-q:v", "2",             # high quality JPEG
        os.path.join(output_dir, "frame_%06d.jpg"),
        "-y",
    ]
    logger.debug("Extracting frames: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed:\n{result.stderr}")

    # Collect extracted frames sorted by frame number → timestamp
    frames: List[Tuple[float, str]] = []
    for fname in sorted(os.listdir(output_dir)):
        if fname.startswith("frame_") and fname.endswith(".jpg"):
            # frame number corresponds to 1-based second
            frame_num = int(fname.replace("frame_", "").replace(".jpg", ""))
            timestamp = float(frame_num - 1)  # 0-based seconds
            frames.append((timestamp, os.path.join(output_dir, fname)))

    logger.info("Extracted %d frames from %s", len(frames), video_path)
    return frames


def extract_audio_chunk(
    audio_path: str,
    start_sec: float,
    duration_sec: float,
    output_path: str,
) -> None:
    """Extract a time segment from an audio file."""
    cmd = [
        "ffmpeg",
        "-i", audio_path,
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg chunk extraction failed:\n{result.stderr}")
