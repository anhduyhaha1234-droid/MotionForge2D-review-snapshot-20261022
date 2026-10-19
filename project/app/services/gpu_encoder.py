"""GPU encoder detection — NVENC hardware acceleration for FFmpeg."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from app.services.ffmpeg_utils import find_ffmpeg


@dataclass
class EncoderInfo:
    """GPU encoder availability info."""

    has_nvenc: bool = False
    gpu_name: str = ""
    encoder_name: str = "libx264"  # fallback


def detect_nvenc() -> EncoderInfo:
    """Detect if NVENC hardware encoding is available.

    Checks:
    1. nvidia-smi for GPU presence
    2. ffmpeg -encoders for h264_nvenc support

    Returns:
        EncoderInfo with has_nvenc flag and encoder name.
    """
    info = EncoderInfo()

    # Check nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            info.gpu_name = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check ffmpeg nvenc support
    try:
        ffmpeg = find_ffmpeg()
        result = subprocess.run(
            [ffmpeg, "-encoders"],
            capture_output=True, text=True, timeout=10,
        )
        if "h264_nvenc" in result.stdout:
            info.has_nvenc = True
            info.encoder_name = "h264_nvenc"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return info


def get_encode_args() -> list[str]:
    """Get FFmpeg encoding arguments, using NVENC if available.

    Returns:
        List of FFmpeg arguments for encoding.
    """
    info = detect_nvenc()

    if info.has_nvenc:
        return [
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            "-c:v", "h264_nvenc",
            "-preset", "fast",
            "-rc", "vbr",
            "-cq", "23",
        ]
    else:
        return [
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
        ]
