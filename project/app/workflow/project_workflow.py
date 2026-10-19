"""Project workflow service — project creation and lifecycle management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.config import AppConfig
from app.schemas import ProjectData, TrackedObject
from app.services.project_service import ProjectService


class ProjectWorkflowService:
    """High-level project operations wrapping ProjectService."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._projects_dir = config.project_root / "projects"

    @property
    def projects_dir(self) -> Path:
        return self._projects_dir

    def _project_dir(self, project_id: str) -> Path:
        return self._projects_dir / project_id

    def _project_json(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "project.json"

    def create_project(self, name: str) -> tuple[str, ProjectData]:
        """Create a new project.

        Returns:
            (project_id, project_data)
        """
        project_id = uuid.uuid4().hex[:12]
        proj_dir = self._project_dir(project_id)
        proj_dir.mkdir(parents=True, exist_ok=True)

        svc = ProjectService(self._project_json(project_id))
        data = svc.create(name=name, source_video="")
        now = datetime.now(UTC).isoformat()
        data.created_at = now
        data.updated_at = now
        svc.save()
        return project_id, data

    def get_project(self, project_id: str) -> ProjectData:
        """Load project data."""
        svc = ProjectService(self._project_json(project_id))
        return svc.load()

    def get_project_service(self, project_id: str) -> ProjectService:
        """Get a ProjectService instance for the given project."""
        return ProjectService(self._project_json(project_id))

    def set_video(self, project_id: str, video_filename: str) -> ProjectData:
        """Set the source video path on a project."""
        svc = ProjectService(self._project_json(project_id))
        data = svc.load()
        video_dir = self._project_dir(project_id)
        data.source_video = str((video_dir / video_filename).resolve())
        svc.save()
        return data

    def add_tracked_object(self, project_id: str, obj: TrackedObject) -> ProjectData:
        """Add a tracked object to the project."""
        svc = ProjectService(self._project_json(project_id))
        svc.load()
        svc.add_tracked_object(obj)
        return svc.data

    def update_object(self, project_id: str, object_id: str, **kwargs: object) -> TrackedObject:
        """Update fields on a tracked object."""
        svc = ProjectService(self._project_json(project_id))
        data = svc.load()
        for obj in data.objects:
            if obj.object_id == object_id:
                for k, v in kwargs.items():
                    setattr(obj, k, v)
                svc.save()
                return obj
        raise KeyError(f"Object not found: {object_id}")

    def _save_project(self, project_id: str, data: ProjectData) -> None:
        """Save project data directly."""
        data.updated_at = datetime.now(UTC).isoformat()
        svc = ProjectService(self._project_json(project_id))
        svc._data = data
        svc.save()

    def get_tracked_object(self, project_id: str, object_id: str) -> TrackedObject:
        """Get a single tracked object."""
        data = self.get_project(project_id)
        for obj in data.objects:
            if obj.object_id == object_id:
                return obj
        raise KeyError(f"Object not found: {object_id}")
