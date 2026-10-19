"""Replacement service — upload replacement PNG and manage transform settings."""

from __future__ import annotations

import shutil
from pathlib import Path

from app.schemas import ReplacementConfig, TrackedObject
from app.workflow.project_workflow import ProjectWorkflowService


class ReplacementService:
    """Handles replacement image upload and config management."""

    def __init__(self, project_wf: ProjectWorkflowService) -> None:
        self._project_wf = project_wf

    def upload_replacement(
        self,
        project_id: str,
        object_id: str,
        source_path: str | Path,
        filename: str = "replacement.png",
    ) -> str:
        """Upload a replacement PNG for a tracked object.

        Args:
            project_id: Target project ID.
            object_id: Target object ID.
            source_path: Path to the uploaded replacement PNG.
            filename: Destination filename.

        Returns:
            Relative path to the stored replacement image.
        """
        project = self._project_wf.get_project(project_id)
        obj = None
        for o in project.objects:
            if o.object_id == object_id:
                obj = o
                break
        if obj is None:
            raise KeyError(f"Object not found: {object_id}")

        proj_dir = self._project_wf._project_dir(project_id)
        obj_dir = proj_dir / "objects" / object_id
        obj_dir.mkdir(parents=True, exist_ok=True)
        dest = obj_dir / filename
        shutil.copy2(str(source_path), str(dest))

        rel_path = f"objects/{object_id}/{filename}"
        self._project_wf.update_object(
            project_id, object_id, replacement_image=rel_path
        )
        return rel_path

    def update_settings(
        self,
        project_id: str,
        object_id: str,
        settings: ReplacementConfig,
    ) -> TrackedObject:
        """Update replacement transform settings for an object."""
        return self._project_wf.update_object(
            project_id, object_id, replacement_config=settings
        )
