"""Integration tests for video probe and render services.

These tests require FFmpeg to be installed and a test video fixture.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.schemas import BoundingBox, FrameMotion
from app.services.compositing import composite_object, load_replacement_image
from app.services.render import render_video
from app.services.video_probe import extract_audio, probe_video

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
TEST_VIDEO = FIXTURES_DIR / "test_video.mp4"


def create_test_video(output_path: Path, fps: float = 30.0, duration: float = 2.0) -> Path:
    """Generate a simple test video using FFmpeg.

    Creates a 2-second video with color bars and a moving rectangle.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

    # Generate test video with testsrc (color bars + moving pattern)
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size=320x240:rate={fps}",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test video: {result.stderr}")

    return output_path


def create_test_png(output_path: Path, width: int = 50, height: int = 50) -> Path:
    """Create a simple test PNG with alpha channel."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create BGRA image
    img = np.zeros((height, width, 4), dtype=np.uint8)
    img[:, :, 2] = 255  # Red
    img[:, :, 3] = 200  # Semi-transparent

    cv2.imwrite(str(output_path), img)
    return output_path


@pytest.fixture(scope="module")
def test_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test video for integration tests."""
    tmp = tmp_path_factory.mktemp("video")
    return create_test_video(tmp / "test_video.mp4")


@pytest.fixture(scope="module")
def test_png(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test PNG for compositing tests."""
    tmp = tmp_path_factory.mktemp("png")
    return create_test_png(tmp / "replacement.png")


# ─── Video Probe Integration ─────────────────────────────────────────────────

@pytest.mark.integration
class TestVideoProbe:
    def test_probe_metadata(self, test_video: Path) -> None:
        """Probe should return valid metadata."""
        metadata = probe_video(test_video)
        assert metadata.width == 320
        assert metadata.height == 240
        assert metadata.fps > 0
        assert metadata.duration_seconds > 0
        assert metadata.total_frames > 0
        assert metadata.has_audio is True
        assert metadata.codec in ("h264", "mpeg4")

    def test_probe_nonexistent(self) -> None:
        """Probe should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            probe_video("/nonexistent/video.mp4")

    def test_extract_audio(self, test_video: Path, tmp_path: Path) -> None:
        """Audio extraction should produce a valid audio file."""
        audio_path = tmp_path / "audio.aac"
        result = extract_audio(test_video, audio_path)
        assert result.exists()
        assert result.stat().st_size > 0


# ─── Render Integration ──────────────────────────────────────────────────────

@pytest.mark.integration
class TestRender:
    def test_render_with_audio(self, test_video: Path, tmp_path: Path) -> None:
        """Render should produce a valid MP4 with audio."""
        # Extract frames first
        metadata = probe_video(test_video)
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()

        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg, "-y",
            "-i", str(test_video),
            "-vf", "select=between(n\\,0\\,29)",
            "-vsync", "vfr",
            str(frames_dir / "frame_%06d.png"),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Extract audio
        audio_path = tmp_path / "audio.aac"
        extract_audio(test_video, audio_path)

        # Render
        output = tmp_path / "output.mp4"
        result = render_video(frames_dir, output, metadata, audio_path)
        assert result.exists()
        assert result.stat().st_size > 0

        # Verify output has correct properties
        out_meta = probe_video(result)
        assert abs(out_meta.fps - metadata.fps) < 1.0
        assert out_meta.has_audio is True

    def test_render_without_audio(self, test_video: Path, tmp_path: Path) -> None:
        """Render should work without audio."""
        metadata = probe_video(test_video)
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()

        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg, "-y",
            "-i", str(test_video),
            "-vf", "select=between(n\\,0\\,14)",
            "-vsync", "vfr",
            str(frames_dir / "frame_%06d.png"),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        output = tmp_path / "output_noaudio.mp4"
        result = render_video(frames_dir, output, metadata)
        assert result.exists()


# ─── Compositing Integration ─────────────────────────────────────────────────

@pytest.mark.integration
class TestCompositing:
    def test_composite_basic(self, test_png: Path) -> None:
        """Compositing should blend replacement onto frame."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:] = (50, 50, 50)

        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:80, 20:80] = 255

        replacement = load_replacement_image(test_png, 60, 60)

        motion = FrameMotion(
            frame_index=0,
            centroid_x=50.0,
            centroid_y=50.0,
            bbox=BoundingBox(x=20, y=20, width=60, height=60),
            scale_x=1.0,
            scale_y=1.0,
            rotation_deg=0.0,
            opacity=1.0,
            visibility=True,
            area=3600.0,
        )

        result = composite_object(frame, mask, replacement, motion)
        assert result.shape == frame.shape
        # The composited region should differ from the original
        assert not np.array_equal(result[30:70, 30:70], frame[30:70, 30:70])

    def test_composite_invisible(self) -> None:
        """Invisible object should not modify frame."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        replacement = np.zeros((50, 50, 4), dtype=np.uint8)

        motion = FrameMotion(
            frame_index=0,
            centroid_x=50.0,
            centroid_y=50.0,
            bbox=BoundingBox(x=0, y=0, width=0, height=0),
            visibility=False,
        )

        result = composite_object(frame, mask, replacement, motion)
        assert np.array_equal(result, frame)
