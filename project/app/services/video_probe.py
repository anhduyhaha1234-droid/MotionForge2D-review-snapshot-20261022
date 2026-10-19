"""Video probe service — extracts metadata from video files using ffprobe."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.schemas import VideoMetadata
from app.services.ffmpeg_utils import find_ffprobe


def probe_video(video_path: str | Path) -> VideoMetadata:
    """Extract video metadata using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        VideoMetadata with all fields populated.

    Raises:
        FileNotFoundError: If video or ffprobe not found.
        RuntimeError: If ffprobe fails.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    ffprobe = find_ffprobe()

    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)

    # Extract video stream
    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    if video_stream is None:
        raise RuntimeError("No video stream found in file")

    # Parse FPS from r_frame_rate (e.g. "30000/1001")
    fps_str = video_stream.get("r_frame_rate", "30/1")
    num, den = fps_str.split("/")
    fps = float(num) / float(den)

    # Duration
    duration = float(data.get("format", {}).get("duration", 0))
    total_frames = int(video_stream.get("nb_frames", 0))
    if total_frames == 0:
        total_frames = int(round(duration * fps))

    # File size
    file_size = int(data.get("format", {}).get("size", 0))

    return VideoMetadata(
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        fps=round(fps, 3),
        duration_seconds=round(duration, 3),
        total_frames=total_frames,
        codec=video_stream.get("codec_name", "unknown"),
        has_audio=audio_stream is not None,
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        file_size_bytes=file_size,
        file_path=str(video_path.resolve()),
    )


def extract_audio(video_path: str | Path, output_path: str | Path) -> Path:
    """Extract audio track from video to a separate file.

    Args:
        video_path: Source video.
        output_path: Where to save the audio (e.g. .aac or .wav).

    Returns:
        Path to the extracted audio file.
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from app.services.ffmpeg_utils import find_ffmpeg
    ffmpeg = find_ffmpeg()

    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vn",           # No video
        "-acodec", "copy",  # Copy codec (no re-encode)
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr}")

    return output_path
