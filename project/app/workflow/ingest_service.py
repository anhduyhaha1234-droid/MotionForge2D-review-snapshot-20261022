"""Ingest service — probe video, detect scenes, slice scene clips."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.config import AppConfig
from app.services.video_probe import probe_video
from app.workflow.project_workflow import ProjectWorkflowService
from app.workflow.scene_chunking_service import SceneChunkingService


class IngestService:
    """Orchestrates video ingest: probe + scene detect + slice clips.

    Architecture: On-Demand Video Chunking
    - Ingest only: probe metadata, detect scene boundaries, slice scene MP4s
    - Frame extraction happens on-demand when user opens a scene
    - This keeps ingest fast (~3-5s) regardless of video length
    """

    def __init__(self, config: AppConfig, project_wf: ProjectWorkflowService) -> None:
        self._config = config
        self._project_wf = project_wf

    def ingest(
        self,
        project_id: str,
        progress_cb: Callable[[float, str], None] | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> str:
        """Run fast ingest pipeline for a project.

        Pipeline:
        1. Probe video metadata (~0.5s)
        2. Detect scene boundaries with PySceneDetect (~1-3s)
        3. Slice video into scene clips with FFmpeg stream copy (~1-2s)
        4. Extract per-scene audio (~1s)
        5. Done! No frame extraction at this stage.

        Args:
            project_id: Target project ID.
            progress_cb: Optional callback(progress_pct, message).
            is_cancelled: Optional callback returning True if cancelled.

        Returns:
            Project directory path on success.

        Raises:
            FileNotFoundError: If video file not found.
        """
        proj_dir = self._project_wf._project_dir(project_id)
        project = self._project_wf.get_project(project_id)
        video_path = Path(project.source_video)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        def _pct(pct: float, msg: str) -> None:
            if progress_cb:
                progress_cb(pct, msg)

        def _cancelled() -> bool:
            return is_cancelled() if is_cancelled else False

        # Step 1: Probe video
        _pct(10, "Probing video metadata")
        metadata = probe_video(video_path)

        svc = self._project_wf.get_project_service(project_id)
        svc.load()
        svc.set_video_metadata(metadata)

        if _cancelled():
            return str(proj_dir)

        # Step 2: Detect scenes
        _pct(30, "Detecting scenes")
        chunk_svc = SceneChunkingService(self._config)
        scene_details = chunk_svc.chunk_video(
            video_path, proj_dir / "audio", threshold=27.0,
        )
        svc.set_scene_details(scene_details)

        if _cancelled():
            return str(proj_dir)

        # Step 3: Slice video into scene clips (stream copy, no re-encode)
        _pct(60, "Slicing scene videos")
        scenes_dir = proj_dir / "scenes"
        chunk_svc.slice_scene_videos(video_path, scene_details, scenes_dir)

        if _cancelled():
            return str(proj_dir)

        # Step 4: Done — no frame extraction at ingest time
        _pct(100, "Ingest complete")
        return str(proj_dir)
