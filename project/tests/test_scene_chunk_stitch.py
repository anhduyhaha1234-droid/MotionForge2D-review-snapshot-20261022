"""Tests for scene chunking and stitching services."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import config as app_config
from app.schemas import SceneDetail, SceneStatus
from app.workflow.scene_chunking_service import SceneChunkingService
from app.workflow.scene_stitch_service import SceneStitchService


@pytest.fixture
def svc() -> SceneChunkingService:
    return SceneChunkingService(app_config)


@pytest.fixture
def stitch_svc() -> SceneStitchService:
    return SceneStitchService(app_config)


@pytest.fixture
def test_video() -> Path:
    """Use fixture_b video if available."""
    p = Path("output_m05/fixture_b/input.mp4")
    if not p.exists():
        pytest.skip("Fixture video not available")
    return p


class TestSceneChunking:
    def test_chunk_returns_scenes(
        self, svc: SceneChunkingService, test_video: Path, tmp_path: Path,
    ) -> None:
        """Chunking a video returns at least one scene."""
        audio_dir = tmp_path / "audio"
        scenes = svc.chunk_video(test_video, audio_dir)
        assert len(scenes) >= 1
        assert all(isinstance(s, SceneDetail) for s in scenes)

    def test_chunk_scene_ids_sequential(
        self, svc: SceneChunkingService, test_video: Path, tmp_path: Path,
    ) -> None:
        """Scene IDs are 0-based sequential."""
        audio_dir = tmp_path / "audio"
        scenes = svc.chunk_video(test_video, audio_dir)
        ids = [s.scene_id for s in scenes]
        assert ids == list(range(len(scenes)))

    def test_chunk_status_pending(
        self, svc: SceneChunkingService, test_video: Path, tmp_path: Path,
    ) -> None:
        """All scenes start as PENDING."""
        audio_dir = tmp_path / "audio"
        scenes = svc.chunk_video(test_video, audio_dir)
        assert all(s.status == SceneStatus.PENDING for s in scenes)

    def test_chunk_audio_extracted(
        self, svc: SceneChunkingService, test_video: Path, tmp_path: Path,
    ) -> None:
        """Audio files are extracted for each scene."""
        audio_dir = tmp_path / "audio"
        scenes = svc.chunk_video(test_video, audio_dir)
        for scene in scenes:
            if scene.audio_path:
                audio_file = audio_dir / f"scene_{scene.scene_id:03d}.aac"
                assert audio_file.exists(), f"Missing audio for scene {scene.scene_id}"

    def test_chunk_duration_positive(
        self, svc: SceneChunkingService, test_video: Path, tmp_path: Path,
    ) -> None:
        """All scenes have positive duration."""
        audio_dir = tmp_path / "audio"
        scenes = svc.chunk_video(test_video, audio_dir)
        assert all(s.duration_sec > 0 for s in scenes)
        assert all(s.frame_count > 0 for s in scenes)


class TestSceneStitching:
    def test_stitch_no_videos_raises(
        self, stitch_svc: SceneStitchService, tmp_path: Path,
    ) -> None:
        """Stitching with no rendered videos raises error."""
        scenes = [
            SceneDetail(
                scene_id=0, start_frame=0, end_frame=29,
                start_time_sec=0.0, end_time_sec=1.0,
                duration_sec=1.0, frame_count=30,
                status=SceneStatus.APPROVED,
            ),
        ]
        with pytest.raises(FileNotFoundError):
            stitch_svc.stitch_scenes(tmp_path, scenes, tmp_path / "out.mp4")

    def test_stitch_requires_approved(
        self, stitch_svc: SceneStitchService, tmp_path: Path,
    ) -> None:
        """Stitching checks scene list is provided."""
        scenes: list[SceneDetail] = []
        with pytest.raises(FileNotFoundError):
            stitch_svc.stitch_scenes(tmp_path, scenes, tmp_path / "out.mp4")
