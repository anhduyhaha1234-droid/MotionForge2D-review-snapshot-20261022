"""Tests for video slicing and on-demand frame extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import config as app_config
from app.schemas import SceneDetail, SceneStatus
from app.workflow.scene_chunking_service import SceneChunkingService


@pytest.fixture
def svc() -> SceneChunkingService:
    return SceneChunkingService(app_config)


@pytest.fixture
def test_video() -> Path:
    """Use fixture_b video if available."""
    p = Path("output_m05/fixture_b/input.mp4")
    if not p.exists():
        pytest.skip("Fixture video not available")
    return p


@pytest.fixture
def sample_scenes() -> list[SceneDetail]:
    """Two short scenes for testing."""
    return [
        SceneDetail(
            scene_id=0, start_frame=0, end_frame=29,
            start_time_sec=0.0, end_time_sec=1.0,
            duration_sec=1.0, frame_count=30,
            status=SceneStatus.PENDING,
        ),
        SceneDetail(
            scene_id=1, start_frame=30, end_frame=59,
            start_time_sec=1.0, end_time_sec=2.0,
            duration_sec=1.0, frame_count=30,
            status=SceneStatus.PENDING,
        ),
    ]


class TestSliceSceneVideos:
    def test_slice_creates_clips(
        self,
        svc: SceneChunkingService,
        test_video: Path,
        sample_scenes: list[SceneDetail],
        tmp_path: Path,
    ) -> None:
        """Slicing creates one clip per scene."""
        output_dir = tmp_path / "scenes"
        clips = svc.slice_scene_videos(test_video, sample_scenes, output_dir)

        assert len(clips) == 2
        assert all(c.exists() for c in clips)
        assert all(c.stat().st_size > 0 for c in clips)

    def test_slice_clip_names(
        self,
        svc: SceneChunkingService,
        test_video: Path,
        sample_scenes: list[SceneDetail],
        tmp_path: Path,
    ) -> None:
        """Clip files follow naming convention."""
        output_dir = tmp_path / "scenes"
        clips = svc.slice_scene_videos(test_video, sample_scenes, output_dir)

        assert clips[0].name == "scene_000.mp4"
        assert clips[1].name == "scene_001.mp4"

    def test_slice_no_reencode(
        self,
        svc: SceneChunkingService,
        test_video: Path,
        sample_scenes: list[SceneDetail],
        tmp_path: Path,
    ) -> None:
        """Stream copy preserves original codec (no re-encode)."""
        import subprocess

        output_dir = tmp_path / "scenes"
        clips = svc.slice_scene_videos(test_video, sample_scenes, output_dir)

        # Check codec matches input
        ffprobe = svc._find_ffprobe()
        for clip in clips:
            cmd = [
                ffprobe, "-v", "quiet",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "csv=p=0",
                str(clip),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert "mpeg4" in result.stdout or "h264" in result.stdout


class TestExtractFramesOnDemand:
    def test_extract_from_clip(
        self,
        svc: SceneChunkingService,
        test_video: Path,
        sample_scenes: list[SceneDetail],
        tmp_path: Path,
    ) -> None:
        """On-demand extraction from scene clip produces frames."""
        # First slice
        scenes_dir = tmp_path / "scenes"
        clips = svc.slice_scene_videos(test_video, sample_scenes, scenes_dir)

        # Then extract frames from first clip
        frames_dir = tmp_path / "frames" / "scene_0"
        frames = svc.extract_frames_on_demand(clips[0], frames_dir, format="jpg")

        assert len(frames) > 0
        assert all(f.exists() for f in frames)
        assert all(f.suffix == ".jpg" for f in frames)

    def test_extract_caches(
        self,
        svc: SceneChunkingService,
        test_video: Path,
        sample_scenes: list[SceneDetail],
        tmp_path: Path,
    ) -> None:
        """Second extraction returns cached frames (no re-extraction)."""
        scenes_dir = tmp_path / "scenes"
        clips = svc.slice_scene_videos(test_video, sample_scenes, scenes_dir)

        frames_dir = tmp_path / "frames" / "scene_0"
        frames1 = svc.extract_frames_on_demand(clips[0], frames_dir, format="jpg")
        frames2 = svc.extract_frames_on_demand(clips[0], frames_dir, format="jpg")

        assert len(frames1) == len(frames2)
        assert frames1 == frames2  # same paths, cached

    def test_extract_png_format(
        self,
        svc: SceneChunkingService,
        test_video: Path,
        sample_scenes: list[SceneDetail],
        tmp_path: Path,
    ) -> None:
        """Extraction supports PNG format."""
        scenes_dir = tmp_path / "scenes"
        clips = svc.slice_scene_videos(test_video, sample_scenes, scenes_dir)

        frames_dir = tmp_path / "frames" / "scene_0_png"
        frames = svc.extract_frames_on_demand(clips[0], frames_dir, format="png")

        assert len(frames) > 0
        assert all(f.suffix == ".png" for f in frames)
