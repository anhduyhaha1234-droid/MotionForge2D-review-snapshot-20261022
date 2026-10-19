"""Render service — reassembles composited frames into MP4 with original audio."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.schemas import VideoMetadata
from app.services.ffmpeg_utils import find_ffmpeg


def render_video(
    frames_dir: str | Path,
    output_path: str | Path,
    metadata: VideoMetadata,
    audio_path: str | Path | None = None,
    frame_pattern: str = "frame_%06d.png",
) -> Path:
    """Render frames into an MP4 video, optionally muxing with audio.

    Args:
        frames_dir: Directory containing composited frames.
        output_path: Where to save the final MP4.
        metadata: Original video metadata (for FPS matching).
        audio_path: Optional audio file to mux.
        frame_pattern: Printf pattern for frame filenames.

    Returns:
        Path to the rendered video.
    """
    frames_dir = Path(frames_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()

    frame_input = str(frames_dir / frame_pattern)

    if audio_path and Path(audio_path).exists():
        # Render with audio
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(metadata.fps),
            "-i", frame_input,
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        # Render without audio
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(metadata.fps),
            "-i", frame_input,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Video render failed: {result.stderr}")

    return output_path


def render_scene_video(
    frames: list[Path],
    output_path: str | Path,
    fps: float,
    audio_path: str | Path | None = None,
) -> Path:
    """Render a list of frame files into a video.

    Uses a concat demuxer for non-sequential filenames.

    Args:
        frames: List of frame file paths in order.
        output_path: Where to save the MP4.
        fps: Frames per second.
        audio_path: Optional audio to mux.

    Returns:
        Path to rendered video.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()

    # Create concat list file
    concat_file = output_path.parent / "_concat_list.txt"
    with open(concat_file, "w") as f:
        for frame in frames:
            # FFmpeg concat demuxer needs forward slashes
            f.write(f"file '{frame.as_posix()}'\n")
            f.write(f"duration {1.0/fps:.6f}\n")

    cmd_base = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
    ]

    if audio_path and Path(audio_path).exists():
        cmd = cmd_base + [
            "-i", str(audio_path),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        cmd = cmd_base + [
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-movflags", "+faststart",
            str(output_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Clean up concat file
    concat_file.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(f"Scene video render failed: {result.stderr}")

    return output_path
