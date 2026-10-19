"""Shared helpers for API routes."""

from __future__ import annotations

from pathlib import Path

from app.schemas import JobInfo


def find_frame_path(scene_dir: Path, frame_index: int) -> Path | None:
    """Find a frame file trying jpg/jpeg/png in order.

    Args:
        scene_dir: Directory containing frame files.
        frame_index: Zero-based frame index.

    Returns:
        Path to frame file, or None if not found.
    """
    for ext in ("jpg", "jpeg", "png"):
        p = scene_dir / f"frame_{frame_index:06d}.{ext}"
        if p.exists():
            return p
    return None


def job_response(info: JobInfo) -> dict[str, object]:
    """Serialize JobInfo with 'status' key for frontend compatibility.

    Frontend expects 'status', backend model uses 'state'.  The response
    shape is preserved from the legacy service; additive durable fields
    (``steps``, ``attempts``, ``outputs``) may appear but never change the
    meaning of the legacy fields.  Internal ``fenced`` state is hidden by
    the service (the reconciler resolves it before any poll observes it).
    """
    data: dict[str, object] = info.model_dump()
    data["status"] = data.pop("state")
    return data
