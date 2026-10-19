"""Cleanup service — remove temp files and debug artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


class CleanupService:
    """Remove temporary files after project completion."""

    def cleanup_project(
        self,
        project_dir: Path,
        keep_renders: bool = True,
        keep_audio: bool = True,
        keep_presets: bool = True,
    ) -> dict[str, Any]:
        """Clean up temp files in a project directory.

        Removes:
        - debug/ directory (mask previews, debug frames)
        - temp_stitch/ directory
        - temp_concat.txt
        - Individual frame files (if renders exist)
        - __pycache__ directories

        Keeps:
        - renders/ (final videos)
        - audio/ (scene audio)
        - presets/ (project presets)
        - project.json
        - scenes/ (scene clips)

        Args:
            project_dir: Root project directory.
            keep_renders: Whether to keep rendered videos.
            keep_audio: Whether to keep audio files.
            keep_presets: Whether to keep preset files.

        Returns:
            Dict with cleanup stats.
        """
        stats = {
            "files_removed": 0,
            "dirs_removed": 0,
            "bytes_freed": 0,
        }

        if not project_dir.exists():
            return stats

        # Remove debug directory
        debug_dir = project_dir / "debug"
        if debug_dir.exists():
            size = self._dir_size(debug_dir)
            shutil.rmtree(debug_dir)
            stats["dirs_removed"] += 1
            stats["bytes_freed"] += size

        # Remove temp stitch directory
        temp_dir = project_dir / "temp_stitch"
        if temp_dir.exists():
            size = self._dir_size(temp_dir)
            shutil.rmtree(temp_dir)
            stats["dirs_removed"] += 1
            stats["bytes_freed"] += size

        # Remove temp concat file
        temp_concat = project_dir / "temp_concat.txt"
        if temp_concat.exists():
            stats["bytes_freed"] += temp_concat.stat().st_size
            temp_concat.unlink()
            stats["files_removed"] += 1

        # Remove frame directories (keep scene clips)
        frames_dir = project_dir / "frames"
        if frames_dir.exists():
            for scene_dir in frames_dir.iterdir():
                if scene_dir.is_dir():
                    size = self._dir_size(scene_dir)
                    shutil.rmtree(scene_dir)
                    stats["dirs_removed"] += 1
                    stats["bytes_freed"] += size

        # Remove dubbing TTS segments (keep final audio)
        dubbing_dir = project_dir / "dubbing"
        if dubbing_dir.exists():
            for scene_dir in dubbing_dir.iterdir():
                if scene_dir.is_dir():
                    tts_dir = scene_dir / "tts_segments"
                    if tts_dir.exists():
                        size = self._dir_size(tts_dir)
                        shutil.rmtree(tts_dir)
                        stats["dirs_removed"] += 1
                        stats["bytes_freed"] += size

        # Remove __pycache__
        for pycache in project_dir.rglob("__pycache__"):
            if pycache.is_dir():
                size = self._dir_size(pycache)
                shutil.rmtree(pycache)
                stats["dirs_removed"] += 1
                stats["bytes_freed"] += size

        # Remove export zips
        for zf in project_dir.glob("*_export.zip"):
            stats["bytes_freed"] += zf.stat().st_size
            zf.unlink()
            stats["files_removed"] += 1

        return stats

    def _dir_size(self, path: Path) -> int:
        """Calculate total size of a directory."""
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total
