"""Project service — manages project lifecycle and persistence."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import (
    ProjectData,
    SceneDetail,
    SceneInfo,
    SceneMotion,
    TrackedObject,
    VideoMetadata,
)


class ProjectService:
    """Handles project creation, loading, saving, and updates."""

    def __init__(self, project_path: Path) -> None:
        self.path = project_path
        self._data: ProjectData | None = None

    @property
    def data(self) -> ProjectData:
        if self._data is None:
            raise RuntimeError("Project not loaded. Call load() or create() first.")
        return self._data

    def create(self, name: str, source_video: str) -> ProjectData:
        """Create a new project."""
        self._data = ProjectData(name=name, source_video=source_video)
        self.save()
        return self._data

    def load(self) -> ProjectData:
        """Load project from JSON file."""
        if not self.path.exists():
            raise FileNotFoundError(f"Project file not found: {self.path}")

        with open(self.path) as f:
            raw = json.load(f)

        self._data = ProjectData.model_validate(raw)
        return self._data

    def save(self) -> None:
        """Save current project state to JSON."""
        if self._data is None:
            raise RuntimeError("No project data to save")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data.model_dump(), f, indent=2, default=str)

    def set_video_metadata(self, metadata: VideoMetadata) -> None:
        """Update video metadata in the project."""
        self.data.video_metadata = metadata
        self.save()

    def set_scenes(self, scenes: list[SceneInfo]) -> None:
        """Update scene list in the project."""
        self.data.scenes = scenes
        self.save()

    def set_scene_details(self, scene_details: list[SceneDetail]) -> None:
        """Update scene details list in the project."""
        self.data.scene_details = scene_details
        # Also update scenes list for backward compatibility
        self.data.scenes = [
            SceneInfo(
                scene_id=sd.scene_id,
                start_frame=sd.start_frame,
                end_frame=sd.end_frame,
                start_time_sec=sd.start_time_sec,
                end_time_sec=sd.end_time_sec,
                duration_sec=sd.duration_sec,
                frame_count=sd.frame_count,
            )
            for sd in scene_details
        ]
        self.save()

    def add_tracked_object(self, obj: TrackedObject) -> None:
        """Add a tracked object to the project."""
        self.data.objects.append(obj)
        self.save()

    def update_object_motion(self, object_id: str, motion: SceneMotion) -> None:
        """Attach motion data to a tracked object."""
        for obj in self.data.objects:
            if obj.object_id == object_id:
                obj.motion = motion
                self.save()
                return
        raise KeyError(f"Object not found: {object_id}")

    def set_replacement_image(self, object_id: str, image_path: str) -> None:
        """Set the replacement image for a tracked object."""
        for obj in self.data.objects:
            if obj.object_id == object_id:
                obj.replacement_image = image_path
                self.save()
                return
        raise KeyError(f"Object not found: {object_id}")
