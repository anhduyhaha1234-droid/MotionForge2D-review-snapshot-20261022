"""Scene stitching — combine approved scenes into final video."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.config import AppConfig
from app.schemas import SceneDetail
from app.services.ffmpeg_utils import find_ffmpeg


class SceneStitchService:
    """Stitch approved scenes into a single video."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def stitch_scenes(
        self,
        project_dir: Path,
        scene_details: list[SceneDetail],
        output_path: Path,
    ) -> Path:
        """Combine rendered scene videos into final output.

        Looks for rendered videos at: project_dir/renders/scene_{id}_final.mp4
        And audio at: project_dir/audio/scene_{id:03d}.aac

        Args:
            project_dir: Root project directory.
            scene_details: List of scenes (only APPROVED ones used).
            output_path: Where to write final video.

        Returns:
            Path to output video.
        """
        ffmpeg = self._find_ffmpeg()

        # Build concat file
        concat_file = project_dir / "temp_concat.txt"
        video_parts: list[str] = []

        for scene in sorted(scene_details, key=lambda s: s.scene_id):
            scene_video = project_dir / "renders" / f"scene_{scene.scene_id}_final.mp4"
            if not scene_video.exists():
                # Fall back to preview
                scene_video = project_dir / "renders" / f"scene_{scene.scene_id}_preview.mp4"
            if scene_video.exists():
                video_parts.append(str(scene_video))

        if not video_parts:
            raise FileNotFoundError("No rendered scene videos found")

        # Write concat file
        with open(concat_file, "w") as f:
            for vp in video_parts:
                f.write(f"file '{vp}'\n")

        # Concat videos
        cmd = [
            ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        # Cleanup temp
        concat_file.unlink(missing_ok=True)

        return output_path

    def stitch_with_audio(
        self,
        project_dir: Path,
        scene_details: list[SceneDetail],
        output_path: Path,
    ) -> Path:
        """Stitch scenes with per-scene audio re-muxed.

        For each scene: merge rendered video with scene audio.
        Then concat all merged scenes.
        """
        ffmpeg = self._find_ffmpeg()
        temp_dir = project_dir / "temp_stitch"
        temp_dir.mkdir(exist_ok=True)

        merged_parts: list[str] = []

        for scene in sorted(scene_details, key=lambda s: s.scene_id):
            scene_video = (
                project_dir / "renders" / f"scene_{scene.scene_id}_final.mp4"
            )
            if not scene_video.exists():
                scene_video = (
                    project_dir / "renders"
                    / f"scene_{scene.scene_id}_preview.mp4"
                )
            if not scene_video.exists():
                continue

            # Check for scene audio
            audio_file = project_dir / "audio" / f"scene_{scene.scene_id:03d}.aac"

            if audio_file.exists():
                # Merge video + audio
                merged = temp_dir / f"scene_{scene.scene_id:03d}_merged.mp4"
                cmd = [
                    ffmpeg, "-y",
                    "-i", str(scene_video),
                    "-i", str(audio_file),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(merged),
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                merged_parts.append(str(merged))
            else:
                merged_parts.append(str(scene_video))

        if not merged_parts:
            raise FileNotFoundError("No scene videos to stitch")

        # Concat all merged parts
        concat_file = temp_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for mp in merged_parts:
                f.write(f"file '{mp}'\n")

        cmd = [
            ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

        return output_path

    def _find_ffmpeg(self) -> str:
        """Find FFmpeg binary via the shared discovery authority."""
        return find_ffmpeg()
