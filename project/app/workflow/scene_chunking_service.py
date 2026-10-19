"""Scene chunking — detect scenes and extract per-scene audio."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.config import AppConfig
from app.schemas import SceneDetail, SceneStatus
from app.services.ffmpeg_utils import find_ffmpeg, find_ffprobe
from app.services.scene_detection import detect_scenes


class SceneChunkingService:
    """Detect scenes and extract synced audio per scene."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def chunk_video(
        self,
        video_path: Path,
        output_dir: Path,
        threshold: float = 27.0,
    ) -> list[SceneDetail]:
        """Detect scenes and extract audio for each scene.

        Args:
            video_path: Path to input video.
            output_dir: Directory to write scene audio files.
            threshold: Scene detection sensitivity.

        Returns:
            List of SceneDetail with status=PENDING and audio_path set.
        """
        scenes = detect_scenes(video_path, threshold=threshold)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if video has audio
        has_audio = self._check_audio(video_path)

        scene_details: list[SceneDetail] = []
        for scene in scenes:
            audio_path = ""
            if has_audio:
                audio_filename = f"scene_{scene.scene_id:03d}.aac"
                audio_file = output_dir / audio_filename
                self._extract_audio(
                    video_path, audio_file,
                    scene.start_time_sec, scene.end_time_sec,
                )
                audio_path = str(audio_file.relative_to(output_dir.parent.parent))

            scene_details.append(SceneDetail(
                scene_id=scene.scene_id,
                start_frame=scene.start_frame,
                end_frame=scene.end_frame,
                start_time_sec=scene.start_time_sec,
                end_time_sec=scene.end_time_sec,
                duration_sec=scene.duration_sec,
                frame_count=scene.frame_count,
                status=SceneStatus.PENDING,
                audio_path=audio_path,
            ))

        return scene_details

    def slice_scene_videos(
        self,
        video_path: Path,
        scene_details: list[SceneDetail],
        output_dir: Path,
    ) -> list[Path]:
        """Slice video into scene clips using FFmpeg stream copy.

        Uses -c copy (no re-encode) for near-instant slicing.

        Args:
            video_path: Path to source video.
            scene_details: Scene boundary info.
            output_dir: Directory to write scene clips.

        Returns:
            List of paths to scene clip files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = self._find_ffmpeg()
        results: list[Path] = []

        for sd in scene_details:
            clip_path = output_dir / f"scene_{sd.scene_id:03d}.mp4"
            duration = sd.end_time_sec - sd.start_time_sec

            cmd = [
                ffmpeg, "-y",
                "-ss", str(sd.start_time_sec),
                "-i", str(video_path),
                "-t", str(duration),
                "-c", "copy",  # stream copy — no re-encode, instant
                "-avoid_negative_ts", "make_zero",
                str(clip_path),
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            results.append(clip_path)

        return results

    def extract_frames_on_demand(
        self,
        scene_clip_path: Path,
        output_dir: Path,
        format: str = "jpg",
    ) -> list[Path]:
        """Extract frames from a single scene clip (on-demand).

        Called only when user opens/selects a scene in the UI.
        Much faster than extracting from full video.

        Args:
            scene_clip_path: Path to scene clip MP4.
            output_dir: Directory to write frame images.
            format: Output format (jpg or png).

        Returns:
            List of extracted frame paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = self._find_ffmpeg()

        # Check if already extracted
        existing = sorted(output_dir.glob(f"frame_*.{format}"))
        if existing:
            return existing

        output_pattern = str(output_dir / f"frame_%06d.{format}")

        cmd = [
            ffmpeg, "-y",
            "-i", str(scene_clip_path),
            "-vsync", "vfr",
            "-start_number", "0",
            output_pattern,
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=60)

        return sorted(output_dir.glob(f"frame_*.{format}"))

    def _extract_audio(
        self,
        video_path: Path,
        output_path: Path,
        start_sec: float,
        end_sec: float,
    ) -> None:
        """Extract audio segment using FFmpeg."""
        ffmpeg = self._find_ffmpeg()
        duration = end_sec - start_sec
        cmd = [
            ffmpeg, "-y",
            "-i", str(video_path),
            "-ss", str(start_sec),
            "-t", str(duration),
            "-vn",           # no video
            "-acodec", "copy",  # copy audio codec (no re-encode)
            "-avoid_negative_ts", "make_zero",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _check_audio(self, video_path: Path) -> bool:
        """Check if video has audio stream."""
        ffprobe = self._find_ffprobe()
        cmd = [
            ffprobe, "-v", "quiet",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "audio" in result.stdout

    def _find_ffmpeg(self) -> str:
        """Find FFmpeg binary via the shared discovery authority."""
        return find_ffmpeg()

    def _find_ffprobe(self) -> str:
        """Find FFprobe binary via the shared discovery authority."""
        return find_ffprobe()
