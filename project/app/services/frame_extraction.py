"""Frame extraction service — extracts frames from video using FFmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.schemas import SceneInfo
from app.services.ffmpeg_utils import find_ffmpeg


def extract_frames(
    video_path: str | Path,
    output_dir: str | Path,
    scene: SceneInfo,
    format: str = "jpg",
) -> list[Path]:
    """Extract frames for a specific scene from a video.

    Args:
        video_path: Path to source video.
        output_dir: Directory to save frames.
        scene: Scene defining frame range.
        format: Output image format (png or jpg).

    Returns:
        List of extracted frame paths, sorted by frame number.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    ffmpeg = find_ffmpeg()

    # Extract frames using ffmpeg select filter
    output_pattern = str(output_dir / f"frame_%06d.{format}")

    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vf", f"select=between(n\\,{scene.start_frame}\\,{scene.end_frame})",
        "-vsync", "vfr",
        "-start_number", str(scene.start_frame),
        output_pattern,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Frame extraction failed: {result.stderr}")

    # Collect output files
    frames = sorted(output_dir.glob(f"frame_*.{format}"))
    return frames


def extract_single_frame(
    video_path: str | Path,
    output_path: str | Path,
    frame_index: int,
) -> Path:
    """Extract a single frame from a video.

    Args:
        video_path: Path to source video.
        output_path: Where to save the frame.
        frame_index: Zero-based frame index.

    Returns:
        Path to the extracted frame.
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()

    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vf", f"select=eq(n\\,{frame_index})",
        "-vframes", "1",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Single frame extraction failed: {result.stderr}")

    return output_path
