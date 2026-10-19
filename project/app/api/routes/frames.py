"""Frame serving endpoints — with auto on-demand frame extraction fallback."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import get_project_workflow
from app.config import AppConfig
from app.workflow.scene_chunking_service import SceneChunkingService

router = APIRouter(prefix="/api/projects", tags=["frames"])


def find_frame_path(scene_dir: Path, frame_index: int) -> Path | None:
    """Find frame file matching index supporting jpg, jpeg, and png formats."""
    for ext in ("jpg", "jpeg", "png"):
        candidate = scene_dir / f"frame_{frame_index:06d}.{ext}"
        if candidate.exists():
            return candidate
    return None


@router.get("/{project_id}/frames/{frame_index}")
def serve_frame(project_id: str, frame_index: int, scene_id: int = 0) -> FileResponse:
    """Serve a frame image file. Automatically extracts scene frames on-demand if needed."""
    pwf = get_project_workflow()
    try:
        proj_dir = pwf._project_dir(project_id)
        pwf.get_project(project_id)  # validate project exists
    except FileNotFoundError as err:
        raise HTTPException(404, f"Project {project_id} not found") from err

    frames_dir = proj_dir / "frames" / f"scene_{scene_id}"

    # Check if frames already exist
    frame_path = find_frame_path(frames_dir, frame_index)

    # If missing, attempt auto on-demand extraction for scene
    if not frame_path:
        scene_clip = proj_dir / "scenes" / f"scene_{scene_id:03d}.mp4"
        if not scene_clip.exists():
            # Try unpadded fallback
            scene_clip = proj_dir / "scenes" / f"scene_{scene_id}.mp4"

        if scene_clip.exists():
            chunking_svc = SceneChunkingService(AppConfig())
            chunking_svc.extract_frames_on_demand(scene_clip, frames_dir, format="jpg")
            frame_path = find_frame_path(frames_dir, frame_index)

    if not frame_path or not frame_path.exists():
        # Fallback search across any scene directory
        for scene_dir in sorted((proj_dir / "frames").glob("scene_*")):
            candidate = find_frame_path(scene_dir, frame_index)
            if candidate:
                frame_path = candidate
                break

    if not frame_path or not frame_path.exists():
        raise HTTPException(404, f"Frame {frame_index} not found for scene {scene_id}")

    media_type = "image/png" if frame_path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(str(frame_path), media_type=media_type)
