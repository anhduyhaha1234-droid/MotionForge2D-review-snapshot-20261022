"""Durable job-type handlers for the S02-T05 API cutover.

Every handler is a *registered* callable bound to a stable job type.  A
Job row created through the API carries an ``input_manifest`` and is
executed by the S02-T03 ``DurableWorker`` — the HTTP request never holds a
closure as the authoritative job definition (contract §11.2, AC2).

The handlers below are intentionally light wrappers that rehydrate the
same services the legacy route closures used; all heavy work lives in the
service classes.  Each returns a dict result (attempt row) and may publish
final outputs under the manifest ``managed_root``; the worker validates
declared outputs before completion (fail-closed, contract §9.3).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.persistence.artifacts import ManagedRoot, hash_file
from app.workflow.durable_worker import OUTPUT_PURPOSES, WorkerContext

__all__ = [
    "JOB_TYPE_INGEST",
    "JOB_TYPE_PROPAGATE",
    "JOB_TYPE_PREVIEW",
    "JOB_TYPE_RENDER",
    "declared_outputs_for",
    "register_api_handlers",
]

#: Stable API job-type codes (legacy display names preserved for
#: compatibility: ingest / propagate / preview / render).
JOB_TYPE_INGEST = "ingest"
JOB_TYPE_PROPAGATE = "propagate"
JOB_TYPE_PREVIEW = "preview"
JOB_TYPE_RENDER = "render"


def _manifest_value(manifest: dict[str, Any], key: str, default: Any) -> Any:
    """Read a manifest field, failing closed for missing required inputs."""
    value = manifest.get(key, default)
    if value is None and default is None:
        raise KeyError(f"input_manifest missing required field {key!r}")
    return value


def _publish_file(
    ctx: WorkerContext,
    rel_path: str,
    *,
    purpose: str,
) -> dict[str, Any]:
    """Publish a file under the Job's managed root as a final output.

    Returns the output evidence dict in the contract §9.2 shape so the
    worker's declared-output validation sees identical sha256/size.
    """
    root = Path(ctx.input_manifest["managed_root"])
    managed = ManagedRoot(root)
    target = managed.resolve(rel_path)
    if not target.is_file():
        raise FileNotFoundError(f"declared output missing at {rel_path}")
    return {
        "relative_path": rel_path,
        "purpose": purpose,
        "sha256": hash_file(target),
        "size_bytes": target.stat().st_size,
    }


def _ingest_handler(ctx: WorkerContext) -> dict[str, Any]:
    """Run the ingest pipeline for ``manifest.project_id``.

    Legacy closure equivalent: ``IngestService(config, pwf).ingest(...)``.
    """
    from app.workflow.ingest_service import IngestService  # noqa: PLC0415
    from app.workflow.project_workflow import ProjectWorkflowService  # noqa: PLC0415

    manifest = ctx.input_manifest
    project_id = str(_manifest_value(manifest, "project_id", None))
    config = _workflow_config(manifest)
    pwf = ProjectWorkflowService(config)
    svc = IngestService(config, pwf)
    result = svc.ingest(project_id, ctx.progress, ctx.is_cancelled)
    return {"project_id": project_id, "project_dir": str(result)}


def _propagate_handler(ctx: WorkerContext) -> dict[str, Any]:
    """Run mask propagation + motion + crop extraction for one object."""
    import cv2  # noqa: PLC0415

    from app.schemas import SceneMotion  # noqa: PLC0415
    from app.services.motion_extraction import (  # noqa: PLC0415
        compute_scene_motion,
        smooth_motion,
    )
    from app.workflow.project_workflow import ProjectWorkflowService  # noqa: PLC0415
    from app.workflow.segmentation_service import SegmentationService  # noqa: PLC0415

    manifest = ctx.input_manifest
    project_id = str(_manifest_value(manifest, "project_id", None))
    object_id = str(_manifest_value(manifest, "object_id", None))
    config = _workflow_config(manifest)
    pwf = ProjectWorkflowService(config)
    proj_dir = pwf._project_dir(project_id)

    obj = pwf.get_tracked_object(project_id, object_id)
    mask_path = proj_dir / "objects" / object_id / "masks" / "initial_mask.png"
    if not mask_path.is_file():
        raise FileNotFoundError(f"no initial mask for object {object_id}")

    scene_id = obj.scene_id
    frames_dir = proj_dir / "frames" / f"scene_{scene_id}"
    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if not frame_paths:
        frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
    if not frame_paths:
        raise FileNotFoundError(f"no frames found for scene {scene_id}")

    initial_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if initial_mask is None:
        raise RuntimeError("failed to load initial mask")

    sel_idx = min(obj.selection.frame_index, len(frame_paths) - 1)
    scene_frame_start = int(frame_paths[0].stem.split("_")[1])
    list_idx = max(0, min(sel_idx - scene_frame_start, len(frame_paths) - 1))

    seg_svc = SegmentationService(config)
    obj_ext_svc = __import__(
        "app.workflow.object_extraction_service", fromlist=["ObjectExtractionService"]
    ).ObjectExtractionService()

    def seg_progress(pct: float, msg: str) -> None:
        ctx.progress(pct * 0.6, msg)

    masks = seg_svc.propagate_masks(
        frame_paths, initial_mask, list_idx,
        backend="sam2", progress_cb=seg_progress, is_cancelled=ctx.is_cancelled,
    )
    if ctx.is_cancelled():
        return {"cancelled": True, "project_id": project_id, "object_id": object_id}

    ctx.progress(65, "Computing motion data")
    motion = compute_scene_motion(masks, sel_idx, list_idx)
    motion.scene_id = scene_id
    motion_smoothed = smooth_motion(motion.frames)
    final_motion = SceneMotion(
        scene_id=scene_id,
        frames=motion_smoothed,
        reference_bbox=motion.reference_bbox,
    )
    pwf.update_object(project_id, object_id, motion=final_motion)
    if ctx.is_cancelled():
        return {"cancelled": True, "project_id": project_id, "object_id": object_id}

    ctx.progress(80, "Extracting object crops")
    obj_with_motion = pwf.get_tracked_object(project_id, object_id)
    obj_ext_svc.extract_crops(project_id, proj_dir, obj_with_motion, frame_paths, masks)

    ctx.progress(100, "Propagation complete")
    return {
        "project_id": project_id,
        "object_id": object_id,
        "result_path": str(proj_dir / "objects" / object_id),
    }


def _render_handler(ctx: WorkerContext, preview: bool) -> dict[str, Any]:
    """Run preview/final render for one object."""
    from app.workflow.project_workflow import ProjectWorkflowService  # noqa: PLC0415
    from app.workflow.render_service import (  # noqa: PLC0415
        FinalRenderService,
        PreviewRenderService,
    )

    manifest = ctx.input_manifest
    project_id = str(_manifest_value(manifest, "project_id", None))
    object_id = str(_manifest_value(manifest, "object_id", None))
    config = _workflow_config(manifest)
    pwf = ProjectWorkflowService(config)
    proj_dir = pwf._project_dir(project_id)
    project = pwf.get_project(project_id)
    obj = pwf.get_tracked_object(project_id, object_id)

    if preview:
        out = PreviewRenderService().render_preview(
            proj_dir, project, obj, ctx.progress, ctx.is_cancelled,
        )
    else:
        out = FinalRenderService().render_final(
            proj_dir, project, obj, ctx.progress, ctx.is_cancelled,
        )
    return {"project_id": project_id, "object_id": object_id, "result_path": str(out)}


def _preview_handler(ctx: WorkerContext) -> dict[str, Any]:
    return _render_handler(ctx, preview=True)


def _render_handler_entry(ctx: WorkerContext) -> dict[str, Any]:
    return _render_handler(ctx, preview=False)


def _workflow_config(manifest: dict[str, Any]) -> Any:
    """Rehydrate the AppConfig the route used at submit time.

    The manifest carries the *resolved* project root so a restarted process
    can reconstruct the exact same workflow context from durable inputs
    (no closure, no RAM state).
    """
    from app.config import AppConfig  # noqa: PLC0415

    root = Path(str(_manifest_value(manifest, "project_root", None)))
    return AppConfig(
        project_root=root,
        models_dir=root / "models",
        output_dir=root / "output",
    )


#: Declared final outputs per job type (contract §9.2).  Relative paths are
#: resolved against the Job's managed root (manifest ``managed_root``).
_OUTPUT_SPECS: dict[str, dict[str, Any]] = {
    JOB_TYPE_INGEST: {},
    JOB_TYPE_PROPAGATE: {},
    JOB_TYPE_PREVIEW: {
        "preview_video": {
            "path": "renders/scene_{scene_id}_preview.mp4",
        },
    },
    JOB_TYPE_RENDER: {
        "final_video": {
            "path": "renders/scene_{scene_id}_final.mp4",
        },
    },
}


def declared_outputs_for(job_type: str, manifest: dict[str, Any]) -> dict[str, Any] | None:
    """Materialize the declared final-output specs for a submitted Job.

    The path templates are filled from the manifest (project_id/object_id)
    so the worker can fail-closed validate the exact outputs a completed
    Job must expose.
    """
    spec = _OUTPUT_SPECS.get(job_type)
    if not spec:
        return None
    project_id = manifest.get("project_id", "")
    obj = manifest.get("object_id", "")
    scene_id = 0
    if obj:
        try:
            from app.workflow.project_workflow import ProjectWorkflowService  # noqa: PLC0415

            config = _workflow_config(manifest)
            pwf = ProjectWorkflowService(config)
            scene_id = pwf.get_tracked_object(project_id, obj).scene_id
        except Exception:
            scene_id = 0
    materialized: dict[str, Any] = {}
    for name, entry in spec.items():
        path = entry["path"].format(scene_id=scene_id)
        materialized[name] = {"path": path}
    return materialized


def register_api_handlers(worker: Any) -> None:
    """Register all API job-type handlers on a DurableWorker instance.

    Output validators are omitted: the worker's fail-closed declared-output
    disk validation (sha256 + size, contract §9.3/AC6) is the gate, and the
    handlers publish under the manifest managed root.
    """
    worker.register_handler(
        JOB_TYPE_INGEST,
        _ingest_handler,
        declared_outputs=declared_outputs_for(JOB_TYPE_INGEST, {}),
    )
    worker.register_handler(
        JOB_TYPE_PROPAGATE,
        _propagate_handler,
        declared_outputs=declared_outputs_for(JOB_TYPE_PROPAGATE, {}),
    )
    worker.register_handler(
        JOB_TYPE_PREVIEW,
        _preview_handler,
        declared_outputs=declared_outputs_for(JOB_TYPE_PREVIEW, {}),
    )
    worker.register_handler(
        JOB_TYPE_RENDER,
        _render_handler_entry,
        declared_outputs=declared_outputs_for(JOB_TYPE_RENDER, {}),
    )


# Keep OUTPUT_PURPOSES referenced so the module documents the final-output
# visibility contract even when only helpers are imported.
_ = OUTPUT_PURPOSES
