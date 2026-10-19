"""Tests for NVENC detection, lip-sync rate, and cleanup service."""

from __future__ import annotations

from pathlib import Path

from app.services.cleanup_service import CleanupService
from app.services.gpu_encoder import detect_nvenc, get_encode_args


class TestNVENC:
    def test_detect_nvenc_returns_info(self) -> None:
        """NVENC detection returns valid EncoderInfo."""
        info = detect_nvenc()
        assert isinstance(info.has_nvenc, bool)
        assert isinstance(info.gpu_name, str)
        assert isinstance(info.encoder_name, str)

    def test_get_encode_args_returns_list(self) -> None:
        """get_encode_args returns valid FFmpeg args."""
        args = get_encode_args()
        assert isinstance(args, list)
        assert len(args) > 0
        assert "-c:v" in args

    def test_encode_args_nvenc_or_fallback(self) -> None:
        """Encode args use nvenc or libx264 fallback."""
        args = get_encode_args()
        joined = " ".join(args)
        assert "h264_nvenc" in joined or "libx264" in joined


class TestCleanupService:
    def test_cleanup_empty_dir(self, tmp_path: Path) -> None:
        """Cleanup on empty directory returns zero stats."""
        svc = CleanupService()
        stats = svc.cleanup_project(tmp_path)
        assert stats["files_removed"] == 0
        assert stats["dirs_removed"] == 0
        assert stats["bytes_freed"] == 0

    def test_cleanup_removes_debug(self, tmp_path: Path) -> None:
        """Cleanup removes debug directory."""
        debug = tmp_path / "debug"
        debug.mkdir()
        (debug / "mask.png").write_bytes(b"\x89PNG" + b"\x00" * 100)

        svc = CleanupService()
        stats = svc.cleanup_project(tmp_path)
        assert not debug.exists()
        assert stats["dirs_removed"] >= 1
        assert stats["bytes_freed"] > 0

    def test_cleanup_removes_frames(self, tmp_path: Path) -> None:
        """Cleanup removes frame directories."""
        frames = tmp_path / "frames" / "scene_0"
        frames.mkdir(parents=True)
        for i in range(5):
            (frames / f"frame_{i:06d}.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

        svc = CleanupService()
        svc.cleanup_project(tmp_path)
        assert not frames.exists()

    def test_cleanup_keeps_renders(self, tmp_path: Path) -> None:
        """Cleanup preserves renders directory."""
        renders = tmp_path / "renders"
        renders.mkdir()
        (renders / "final.mp4").write_bytes(b"\x00" * 100)

        svc = CleanupService()
        svc.cleanup_project(tmp_path)
        assert renders.exists()
        assert (renders / "final.mp4").exists()

    def test_cleanup_removes_temp(self, tmp_path: Path) -> None:
        """Cleanup removes temp files."""
        temp = tmp_path / "temp_stitch"
        temp.mkdir()
        (temp / "merged.mp4").write_bytes(b"\x00" * 50)
        (tmp_path / "temp_concat.txt").write_text("file 'test.mp4'")

        svc = CleanupService()
        svc.cleanup_project(tmp_path)
        assert not temp.exists()
        assert not (tmp_path / "temp_concat.txt").exists()

    def test_cleanup_nonexistent_dir(self, tmp_path: Path) -> None:
        """Cleanup on nonexistent directory returns zero stats."""
        svc = CleanupService()
        stats = svc.cleanup_project(tmp_path / "nonexistent")
        assert stats["files_removed"] == 0
