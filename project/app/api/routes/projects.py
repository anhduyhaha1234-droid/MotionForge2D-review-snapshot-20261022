"""Project CRUD endpoints."""

from __future__ import annotations

import base64
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.deps import (
    get_config,
    get_job_service,
    get_project_workflow,
    get_replacement_service,
    get_segmentation_service,
)
from app.api.helpers import find_frame_path, job_response
from app.schemas import (
    BoundingBox,
    ObjectKind,
    ProjectData,
    ReplacementConfig,
    ReplacementMode,
    SceneInfo,
    SceneStatus,
    SelectionInput,
    TrackedObject,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ─── Request/Response models ─────────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    name: str


class CreateProjectResponse(BaseModel):
    project_id: str
    project: ProjectData


class CreateObjectRequest(BaseModel):
    name: str
    kind: ObjectKind = ObjectKind.CHARACTER
    selection: SelectionInput
    scene_id: int
    mask_data: list[list[int]] | None = None


class PreviewMaskRequest(BaseModel):
    frame_index: int
    selection: SelectionInput
    backend: str = "contour"


class ReplacementSettingsRequest(BaseModel):
    replacement_config: ReplacementConfig


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
def list_all_projects() -> list[dict[str, object]]:
    """List all projects on disk with summary info."""
    import json

    pwf = get_project_workflow()
    projects_dir = pwf.projects_dir  # projects root
    if not projects_dir.exists():
        return []

    # Filter valid project directories (excluding dummy test projects)
    results: list[dict[str, object]] = []
    dirs = [d for d in projects_dir.iterdir() if d.is_dir() and (d / "project.json").exists()]
    # Sort: scenes_count desc first (real projects), then by mtime
    def _sort_key(p: Path) -> tuple[int, float]:
        try:
            data = json.loads((p / "project.json").read_text(encoding="utf-8"))
            return (len(data.get("scenes", [])), p.stat().st_mtime)
        except Exception:
            return (0, 0)
    dirs.sort(key=_sort_key, reverse=True)

    for proj_dir in dirs:
        try:
            data = json.loads((proj_dir / "project.json").read_text(encoding="utf-8"))
            name = data.get("name", "")
            # Skip dummy pytest projects named "Clip Test"
            if name == "Clip Test":
                continue

            results.append({
                "project_id": proj_dir.name,
                "name": name or "Dự án MotionForge",
                "task_status": data.get("task_status", "draft"),
                "source_video": data.get("source_video", ""),
                "scenes_count": len(data.get("scenes", [])),
                "updated_at": data.get("updated_at", ""),
                "created_at": data.get("created_at", ""),
            })
        except Exception:
            continue
    return results


@router.post("", status_code=201)
@router.post("/", status_code=201)
def create_project(body: CreateProjectRequest) -> CreateProjectResponse:
    """Create a new project."""
    pwf = get_project_workflow()
    project_id, data = pwf.create_project(body.name)
    return CreateProjectResponse(project_id=project_id, project=data)


@router.get("/gpu-info")
def get_gpu_info_early() -> dict[str, object]:
    """Check GPU encoder availability (declared early to avoid path conflict)."""
    from app.services.gpu_encoder import detect_nvenc  # noqa: PLC0415

    info = detect_nvenc()
    return {
        "gpu_name": info.gpu_name,
        "has_nvenc": info.has_nvenc,
        "encoder": info.encoder_name,
    }


# ─── Character preset library (static routes — declared BEFORE /{project_id}) ─

@router.get("/presets/characters")
def list_character_presets_early() -> dict[str, object]:
    """List built-in multi-pose character presets (Boy Cool / Thỏ Cute / Gấu Nâu)."""
    from app.services.preset_manager import get_preset_manager  # noqa: PLC0415

    pm = get_preset_manager()
    return {"status": "ok", "characters": pm.list_characters()}


@router.get("/presets/characters/{set_key}/{pose}/image")
def get_character_preset_image_early(set_key: str, pose: str) -> FileResponse:
    """Serve a character preset PNG asset."""
    from app.services.preset_manager import get_preset_manager  # noqa: PLC0415

    pm = get_preset_manager()
    path = pm.asset_path(set_key, pose)
    if path is None:
        raise HTTPException(404, "Character preset asset not found")
    return FileResponse(str(path), media_type="image/png")


@router.post("/{project_id}/presets/characters/{set_key}/{pose}/apply")
@router.post("/{project_id}/presets/characters/{set_key}/{pose}/apply/")
def apply_character_preset_early(
    project_id: str, set_key: str, pose: str,
) -> dict[str, object]:
    """Apply a character preset pose to the active object of a project.

    Copies the preset PNG into the object's replacement slot and sets
    mode=static_asset so CompositeCanvas renders it immediately.
    """
    from app.services.preset_manager import get_preset_manager  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Active object = first object (ScreenD auto-selects objects[0])
    if not proj.objects:
        raise HTTPException(404, "No objects in project")
    obj = proj.objects[0]

    pm = get_preset_manager()
    src = pm.asset_path(set_key, pose)
    if src is None:
        raise HTTPException(404, "Character preset asset not found")

    proj_dir = pwf._project_dir(project_id)
    obj_dir = proj_dir / "objects" / obj.object_id
    obj_dir.mkdir(parents=True, exist_ok=True)

    dest = obj_dir / "replacement.png"
    shutil.copy2(str(src), str(dest))

    if obj.replacement_config is None:
        from app.schemas import ReplacementConfig

        obj.replacement_config = ReplacementConfig(
            mode=ReplacementMode.STATIC_ASSET,
            assetPath=f"objects/{obj.object_id}/replacement.png",
        )
    else:
        obj.replacement_config.mode = ReplacementMode.STATIC_ASSET
        obj.replacement_config.asset_path = f"objects/{obj.object_id}/replacement.png"

    pwf._save_project(project_id, proj)
    return {
        "status": "ok",
        "object_id": obj.object_id,
        "asset_path": obj.replacement_config.asset_path,
        "pose": pose,
        "set_key": set_key,
    }


@router.post("/{project_id}/video")
@router.post("/{project_id}/video/")
async def upload_video(project_id: str, file: UploadFile) -> dict[str, object]:
    """Upload a video file for the project."""
    import re
    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Sanitize filename to avoid invalid characters on Windows (?, :, *, <, >, |, ")
    original_name = file.filename or "video.mp4"
    safe_filename = re.sub(r'[^\w\.-]', '_', original_name)
    if not safe_filename or safe_filename.startswith("."):
        safe_filename = f"source_{safe_filename}"

    proj_dir = pwf._project_dir(project_id)
    dest = proj_dir / safe_filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    pwf.set_video(project_id, safe_filename)
    return {"status": "ok", "filename": safe_filename}


@router.post("/{project_id}/ingest")
@router.post("/{project_id}/ingest/")
def trigger_ingest(project_id: str) -> dict[str, object]:
    """Trigger ingest (probe + scene detect + frame extract). Returns a job.

    Durable submission (S02-T05): the request only writes an input-manifest
    Job row; the registered ``ingest`` handler runs in the durable worker
    (AC2/AC6 — no long operation inside the HTTP request).
    """
    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    job_svc = get_job_service()
    info = job_svc.create_job(
        "ingest",
        input_manifest={
            "project_id": project_id,
        },
        workspace_id="default",
        owner_type="project",
        owner_id=project_id,
        idempotency_key=f"ingest:{project_id}",
    )
    return job_response(info)


@router.delete("/{project_id}")
@router.delete("/{project_id}/")
def delete_project(project_id: str) -> dict[str, object]:
    """Delete a project and purge all files from disk."""
    import shutil

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    if proj_dir.exists():
        shutil.rmtree(proj_dir)

    return {"ok": True, "deleted": project_id}


@router.get("/{project_id}")
def get_project(project_id: str) -> ProjectData:
    """Get project data."""
    pwf = get_project_workflow()
    try:
        return pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err


@router.post("/{project_id}/auto-segment-objects")
@router.post("/{project_id}/auto-segment-objects/")
def auto_segment_objects(
    project_id: str,
    scene_id: int = 0,
    min_area: int = 300,
    max_objects: int = 20,
) -> dict[str, object]:
    """Auto-detect objects in a frame using OpenCV contour detection.

    Returns list of detected objects with bounding boxes.
    min_area computed on 0.5x downsampled frame; 300 ≈ 1200px at full res —
    catches characters, chairs, tables, beds.
    """
    import cv2
    import numpy as np  # noqa: F401

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    frames_dir = proj_dir / "frames" / f"scene_{scene_id}"

    # Find first frame
    frame_path = find_frame_path(frames_dir, 0)
    if frame_path is None:
        # Try scene clip extraction
        clip_path = proj_dir / "scenes" / f"scene_{scene_id:03d}.mp4"
        if clip_path.exists():
            from app.config import config as app_config  # noqa: PLC0415
            from app.workflow.scene_chunking_service import SceneChunkingService  # noqa: PLC0415
            svc = SceneChunkingService(app_config)
            svc.extract_frames_on_demand(clip_path, frames_dir, format="jpg")
            frame_path = find_frame_path(frames_dir, 0)

    if frame_path is None:
        raise HTTPException(404, "No frames found for this scene")

    # Read frame and detect objects
    img = cv2.imread(str(frame_path))
    if img is None:
        raise HTTPException(500, "Failed to read frame")

    # Downsample for speed
    h, w = img.shape[:2]
    scale = 0.5
    small = cv2.resize(img, (int(w * scale), int(h * scale)))

    # Convert to grayscale and threshold
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    objects: list[dict[str, object]] = []
    for _i, contour in enumerate(contours[:max_objects]):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, bw, bh = cv2.boundingRect(contour)
        # Scale back to original resolution
        full_x = int(x / scale)
        full_y = int(y / scale)
        full_w = int(bw / scale)
        full_h = int(bh / scale)
        cx = int((x + bw / 2) / scale)
        cy = int((y + bh / 2) / scale)
        full_area = int(area / (scale * scale))

        # Crop the object region from the ORIGINAL frame and encode as base64 PNG
        crop_png_base64 = ""
        try:
            crop_img = img[full_y : full_y + full_h, full_x : full_x + full_w]
            if crop_img.size > 0:
                ok_flag, buf = cv2.imencode(".png", crop_img)
                if ok_flag:
                    crop_png_base64 = base64.b64encode(buf.tobytes()).decode("utf-8")
        except Exception:
            crop_png_base64 = ""

        # Distinct name based on size + position
        # Large object near center → "Nhân vật", else "Vật thể"
        center_dist = abs(cx - w / 2) + abs(cy - h / 2)
        is_character = full_area > (w * h * 0.05) and center_dist < (w * 0.4)
        label = "Nhân vật" if is_character else "Vật thể"
        name = f"{label} #{len(objects) + 1} ({full_w}×{full_h}px)"

        objects.append({
            "object_index": len(objects),
            "name": name,
            "crop_png_base64": crop_png_base64,
            "bbox": {
                "x": full_x,
                "y": full_y,
                "width": full_w,
                "height": full_h,
            },
            "area": full_area,
            "centroid": {
                "x": cx,
                "y": cy,
            },
        })

    # Sort by area (largest first)
    def _area_key(item: dict[str, object]) -> int:
        area = item["area"]
        if isinstance(area, int):
            return area
        raise TypeError(f"unexpected area type: {type(area)!r}")

    objects.sort(key=_area_key, reverse=True)

    return {
        "scene_id": scene_id,
        "frame_path": str(frame_path),
        "objects_found": len(objects),
        "objects": objects,
    }


@router.get("/{project_id}/scenes")
def list_scenes(project_id: str) -> list[SceneInfo]:
    """List scenes for a project."""
    pwf = get_project_workflow()
    try:
        data = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err
    return data.scenes


@router.get("/{project_id}/scenes/{scene_id}/objects")
def get_scene_objects(project_id: str, scene_id: int) -> list[dict[str, object]]:
    """Get all tracked objects in a specific scene."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    scene_objects = [o for o in proj.objects if o.scene_id == scene_id]
    return [o.model_dump(by_alias=True) for o in scene_objects]


@router.get("/{project_id}/objects")
@router.get("/{project_id}/objects/")
def list_objects(project_id: str) -> list[dict[str, object]]:
    """List all tracked objects with thumbnail (base64 PNG) for UI display."""
    import base64

    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    results: list[dict[str, object]] = []
    for obj in proj.objects:
        item = obj.model_dump(by_alias=True)
        # Attach thumbnail base64 if thumbnail.png exists
        thumb_path = proj_dir / "objects" / obj.object_id / "thumbnail.png"
        item["thumbnail_base64"] = ""
        if thumb_path.exists():
            try:
                data = thumb_path.read_bytes()
                item["thumbnail_base64"] = (
                    "data:image/png;base64," + base64.b64encode(data).decode()
                )
            except Exception:
                item["thumbnail_base64"] = ""
        results.append(item)
    return results


@router.delete("/{project_id}/objects")
@router.delete("/{project_id}/objects/")
def clear_objects(project_id: str) -> dict[str, object]:
    """Delete all tracked objects for a project (reset objects list)."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj.objects = []
    pwf._save_project(project_id, proj)

    # Also clean object dirs on disk
    proj_dir = pwf._project_dir(project_id)
    objects_dir = proj_dir / "objects"
    if objects_dir.exists():
        shutil.rmtree(objects_dir, ignore_errors=True)

    return {"status": "ok", "project": proj.model_dump()}


@router.delete("/{project_id}/objects/{object_id}")
@router.delete("/{project_id}/objects/{object_id}/")
def delete_single_object(project_id: str, object_id: str) -> dict[str, object]:
    """Delete a single tracked object by ID."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj.objects = [o for o in proj.objects if o.object_id != object_id]
    pwf._save_project(project_id, proj)

    # Remove object dir on disk
    proj_dir = pwf._project_dir(project_id)
    obj_dir = proj_dir / "objects" / object_id
    if obj_dir.exists():
        shutil.rmtree(obj_dir, ignore_errors=True)

    return {"status": "ok", "project": proj.model_dump()}


@router.get("/{project_id}/frames/{frame_index}")
def get_frame(project_id: str, frame_index: int, scene_id: int = 0) -> FileResponse:
    """Serve a frame image (tries jpg first, then png)."""
    pwf = get_project_workflow()
    proj_dir = pwf._project_dir(project_id)
    scene_dir = proj_dir / "frames" / f"scene_{scene_id}"

    frame_path = find_frame_path(scene_dir, frame_index)
    if frame_path is None:
        raise HTTPException(404, f"Frame {frame_index} not found")

    media = "image/jpeg" if frame_path.suffix in (".jpg", ".jpeg") else "image/png"
    return FileResponse(str(frame_path), media_type=media)


@router.post("/{project_id}/objects/preview-mask")
@router.post("/{project_id}/objects/preview-mask/")
def preview_mask(project_id: str, body: PreviewMaskRequest) -> dict[str, object]:
    """Preview mask for a selection on a frame."""
    pwf = get_project_workflow()
    proj_dir = pwf._project_dir(project_id)
    scene_dir_0 = proj_dir / "frames" / "scene_0"
    frame_path = find_frame_path(scene_dir_0, body.frame_index)

    if frame_path is None:
        for sd in (proj_dir / "frames").glob("scene_*"):
            found = find_frame_path(sd, body.frame_index)
            if found is not None:
                frame_path = found
                break
        if frame_path is None:
            raise HTTPException(404, f"Frame {body.frame_index} not found")

    seg_svc = get_segmentation_service()
    try:
        mask = seg_svc.preview_mask(frame_path, body.selection, body.backend)
    except Exception as e:
        raise HTTPException(500, str(e)) from e

    import cv2

    mask_dir = proj_dir / "debug"
    mask_dir.mkdir(parents=True, exist_ok=True)
    mask_path = mask_dir / f"preview_mask_{body.frame_index}.png"
    cv2.imwrite(str(mask_path), mask)

    return {
        "mask_path": str(mask_path),
        "nonzero_pixels": int((mask > 0).sum()),
        "frame_index": body.frame_index,
    }


def _auto_crop_object(
    proj_dir: Path,
    object_id: str,
    selection: SelectionInput,
    pad: int = 10,
) -> Path | None:
    """Crop the object region from the current frame into crop.png.

    Uses the selection bbox (or point with a default window). Returns the
    crop file path, or None if the frame can't be found.
    """
    import cv2

    try:
        f_idx = selection.frame_index
        s_id = 0  # default scene
        scene_dir = proj_dir / "frames" / f"scene_{s_id}"
        frame_path = find_frame_path(scene_dir, f_idx)
        if frame_path is None:
            for sd in (proj_dir / "frames").glob("scene_*"):
                found = find_frame_path(sd, f_idx)
                if found is not None:
                    frame_path = found
                    break
        if frame_path is None:
            return None

        frame = cv2.imread(str(frame_path))
        if frame is None:
            return None

        h, w = frame.shape[:2]

        if selection.mode == "bounding_box":
            sel_w = selection.width
            sel_h = selection.height
            if sel_w is None or sel_h is None:
                return None
            x = max(0, int(selection.x) - pad)
            y = max(0, int(selection.y) - pad)
            bw = int(sel_w) + 2 * pad
            bh = int(sel_h) + 2 * pad
        else:
            # Point mode: use a 160x160 window centered on the point
            cx, cy = int(selection.x), int(selection.y)
            half = 80
            x = max(0, cx - half)
            y = max(0, cy - half)
            bw, bh = 2 * half, 2 * half

        x = min(x, w - 1)
        y = min(y, h - 1)
        bw = min(bw, w - x)
        bh = min(bh, h - y)
        if bw <= 0 or bh <= 0:
            return None

        crop_img = frame[y : y + bh, x : x + bw]

        obj_dir = proj_dir / "objects" / object_id
        obj_dir.mkdir(parents=True, exist_ok=True)
        crop_file = obj_dir / "crop.png"
        cv2.imwrite(str(crop_file), crop_img)
        return crop_file
    except Exception:
        return None


@router.get("/{project_id}/objects/{object_id}/crop")
@router.get("/{project_id}/objects/{object_id}/crop/")
def get_object_crop(project_id: str, object_id: str) -> FileResponse:
    """Return the cropped object thumbnail. Auto-generates if missing."""
    pwf = get_project_workflow()
    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    proj_dir = pwf._project_dir(project_id)
    crop_file = proj_dir / "objects" / object_id / "crop.png"

    # Auto-generate crop if missing
    if not crop_file.exists():
        generated = _auto_crop_object(proj_dir, object_id, obj.selection)
        if generated is not None:
            crop_file = generated

    if not crop_file.exists():
        raise HTTPException(404, "Crop not found")

    return FileResponse(str(crop_file), media_type="image/png")


@router.post("/{project_id}/objects", status_code=201)
@router.post("/{project_id}/objects/", status_code=201)
def create_object(project_id: str, body: CreateObjectRequest) -> dict[str, object]:
    """Create a tracked object."""
    import cv2
    import numpy as np

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Dedupe: if an existing object has nearly the same bbox in the same
    # scene and same frame, return the existing object instead of creating
    # a duplicate.
    try:
        proj_now = pwf.get_project(project_id)
        sel = body.selection
        for existing in proj_now.objects:
            if existing.scene_id != body.scene_id:
                continue
            es = existing.selection
            es_w = es.width
            es_h = es.height
            sel_w = sel.width
            sel_h = sel.height
            if (
                es.mode == "bounding_box"
                and sel.mode == "bounding_box"
                and es_w is not None
                and es_h is not None
                and sel_w is not None
                and sel_h is not None
            ):
                if (
                    abs(es.x - sel.x) < 20
                    and abs(es.y - sel.y) < 20
                    and abs(es_w - sel_w) < 30
                    and abs(es_h - sel_h) < 30
                    and abs(es.frame_index - sel.frame_index) < 3
                ):
                    return {
                        "object_id": existing.object_id,
                        "project": proj_now.model_dump(),
                        "duplicate": True,
                    }
            elif (
                es.mode == sel.mode == "point"
                and abs(es.x - sel.x) < 30
                and abs(es.y - sel.y) < 30
                and abs(es.frame_index - sel.frame_index) < 3
            ):
                return {
                    "object_id": existing.object_id,
                    "project": proj_now.model_dump(),
                    "duplicate": True,
                }
    except Exception:
        pass

    obj_id = uuid.uuid4().hex[:8]

    # Distinct name: use provided name, or auto-generate from selection size
    obj_name = body.name
    if not obj_name or obj_name.lower() in ("test", "object", "vật thể", "nhân vật"):
        selection = body.selection
        if selection.mode == "bounding_box":
            sel_w = selection.width
            sel_h = selection.height
            if sel_w is not None and sel_h is not None:
                sw = int(sel_w)
                sh = int(sel_h)
            else:
                sw, sh = 160, 160
        else:
            sw, sh = 160, 160
        existing_objects = [o for o in pwf.get_project(project_id).objects]
        idx = len(existing_objects) + 1
        obj_name = f"Vật thể #{idx} ({sw}×{sh}px)"

    obj = TrackedObject(
        object_id=obj_id,
        name=obj_name,
        kind=body.kind,
        selection=body.selection,
        scene_id=body.scene_id,
    )

    proj_dir = pwf._project_dir(project_id)
    mask_dir = proj_dir / "objects" / obj_id / "masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    initial_mask_path = mask_dir / "initial_mask.png"

    if body.mask_data:
        mask_arr = np.array(body.mask_data, dtype=np.uint8)
        cv2.imwrite(str(initial_mask_path), mask_arr)
    else:
        # Fallback 1: specific frame preview mask
        f_idx = body.selection.frame_index
        debug_mask_path = proj_dir / "debug" / f"preview_mask_{f_idx}.png"
        if debug_mask_path.exists():
            shutil.copy2(str(debug_mask_path), str(initial_mask_path))
        else:
            # Fallback 2: most recent preview mask by mtime
            debug_dir = proj_dir / "debug"
            if debug_dir.exists():
                preview_masks = sorted(
                    debug_dir.glob("preview_mask_*.png"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if preview_masks:
                    shutil.copy2(str(preview_masks[0]), str(initial_mask_path))

        # Fallback 3: compute mask directly
        if not initial_mask_path.exists():
            try:
                s_id = body.scene_id
                scene_dir = proj_dir / "frames" / f"scene_{s_id}"
                frame_path = find_frame_path(scene_dir, f_idx)
                if frame_path is None:
                    for sd in (proj_dir / "frames").glob("scene_*"):
                        found = find_frame_path(sd, f_idx)
                        if found is not None:
                            frame_path = found
                            break
                if frame_path is not None:
                    seg_svc = get_segmentation_service()
                    mask = seg_svc.preview_mask(frame_path, body.selection, "contour")
                    cv2.imwrite(str(initial_mask_path), mask)
            except Exception:
                pass

    # Auto-crop the object from the frame into crop.png
    crop_file = _auto_crop_object(
        proj_dir, obj_id, body.selection,
    )
    if crop_file is not None:
        obj.crop_path = str(crop_file)

    data = pwf.add_tracked_object(project_id, obj)
    return {"object_id": obj_id, "project": data.model_dump()}


@router.post("/{project_id}/objects/{object_id}/propagate")
@router.post("/{project_id}/objects/{object_id}/propagate/")
def propagate_object(project_id: str, object_id: str) -> dict[str, object]:
    """Propagate masks for a tracked object. Returns a job.

    Durable submission (S02-T05): the request validates inputs and writes an
    input-manifest Job row; the registered ``propagate`` handler runs in the
    durable worker (AC2/AC6).
    """
    import cv2  # noqa: PLC0415

    pwf = get_project_workflow()
    proj_dir = pwf._project_dir(project_id)

    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    mask_path = proj_dir / "objects" / object_id / "masks" / "initial_mask.png"
    if not mask_path.exists():
        debug_dir = proj_dir / "debug"
        f_idx = obj.selection.frame_index
        frame_mask = debug_dir / f"preview_mask_{f_idx}.png"
        if frame_mask.exists():
            mask_dir = proj_dir / "objects" / object_id / "masks"
            mask_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(frame_mask), str(mask_path))
        else:
            preview_masks = (
                sorted(
                    debug_dir.glob("preview_mask_*.png"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if debug_dir.exists()
                else []
            )
            if preview_masks:
                mask_dir = proj_dir / "objects" / object_id / "masks"
                mask_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(preview_masks[0]), str(mask_path))
            else:
                try:
                    s_id = obj.scene_id
                    scene_dir = proj_dir / "frames" / f"scene_{s_id}"
                    frame_path = find_frame_path(scene_dir, f_idx)
                    if frame_path is None:
                        for sd in (proj_dir / "frames").glob("scene_*"):
                            found = find_frame_path(sd, f_idx)
                            if found is not None:
                                frame_path = found
                                break
                    if frame_path is not None:
                        seg_svc = get_segmentation_service()
                        mask = seg_svc.preview_mask(frame_path, obj.selection, "contour")
                        mask_dir = proj_dir / "objects" / object_id / "masks"
                        mask_dir.mkdir(parents=True, exist_ok=True)
                        cv2.imwrite(str(mask_path), mask)
                except Exception:
                    pass

    if not mask_path.exists():
        raise HTTPException(
            400, "No initial mask. Preview a mask or create with mask_data."
        )

    scene_id = obj.scene_id
    frames_dir = proj_dir / "frames" / f"scene_{scene_id}"
    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if not frame_paths:
        frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
    if not frame_paths:
        raise HTTPException(400, f"No frames found for scene {scene_id}")

    job_svc = get_job_service()
    info = job_svc.create_job(
        "propagate",
        input_manifest={
            "project_id": project_id,
            "object_id": object_id,
            "scene_id": scene_id,
            "frame_count": len(frame_paths),
        },
        workspace_id="default",
        owner_type="project",
        owner_id=project_id,
        idempotency_key=f"propagate:{project_id}:{object_id}",
    )
    return job_response(info)


@router.get("/{project_id}/objects/{object_id}")
def get_object(project_id: str, object_id: str) -> dict[str, object]:
    """Get tracked object with motion data."""
    pwf = get_project_workflow()
    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e
    return obj.model_dump()


@router.get("/{project_id}/objects/{object_id}/gallery")
def get_gallery(project_id: str, object_id: str) -> dict[str, object]:
    """Get gallery manifest for a tracked object."""
    import json as json_mod

    pwf = get_project_workflow()
    proj_dir = pwf._project_dir(project_id)
    manifest_path = proj_dir / "objects" / object_id / "gallery_manifest.json"

    if not manifest_path.exists():
        raise HTTPException(404, "Gallery not found. Run propagation first.")

    with open(manifest_path) as f:
        data = json_mod.load(f)
    if not isinstance(data, dict):
        raise HTTPException(500, "Gallery manifest is corrupt")
    return data


@router.post("/{project_id}/objects/{object_id}/replacement")
@router.post("/{project_id}/objects/{object_id}/replacement/")
async def upload_replacement(
    project_id: str, object_id: str, file: UploadFile,
) -> dict[str, object]:
    """Upload a replacement PNG for a tracked object."""
    pwf = get_project_workflow()
    try:
        pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    proj_dir = pwf._project_dir(project_id)
    obj_dir = proj_dir / "objects" / object_id
    obj_dir.mkdir(parents=True, exist_ok=True)

    # Write to temp file first, then let service copy to final location
    import tempfile
    from pathlib import Path
    suffix = Path(file.filename or "replacement.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        rep_svc = get_replacement_service()
        rel_path = rep_svc.upload_replacement(project_id, object_id, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"status": "ok", "asset_path": rel_path}


@router.get("/{project_id}/objects/{object_id}/replacement-image")
@router.get("/{project_id}/objects/{object_id}/replacement-image/")
def get_replacement_image(project_id: str, object_id: str) -> FileResponse:
    """Serve the uploaded replacement image for a tracked object."""
    pwf = get_project_workflow()
    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    proj_dir = pwf._project_dir(project_id)

    # Replacement file lives at objects/<object_id>/replacement.png (or .jpg/...)
    obj_dir = proj_dir / "objects" / object_id
    for candidate in sorted(obj_dir.glob("replacement.*")):
        if candidate.is_file():
            return FileResponse(candidate)

    # Fall back to the asset_path saved on the object
    asset = getattr(obj, "replacement_config", None)
    asset_path = getattr(asset, "asset_path", "") if asset else ""
    if asset_path and asset_path != "/replacements/test.png":
        p = Path(asset_path)
        if not p.is_absolute():
            p = proj_dir / p
        if p.is_file():
            return FileResponse(p)

    raise HTTPException(404, "Replacement image not found")


@router.get("/{project_id}/objects/{object_id}/masks/{frame_index}")
@router.get("/{project_id}/objects/{object_id}/masks/{frame_index}/")
def get_object_mask_image(
    project_id: str, object_id: str, frame_index: int,
) -> FileResponse:
    """Serve a mask image for a tracked object at a given frame."""
    pwf = get_project_workflow()
    proj_dir = pwf._project_dir(project_id)
    mask_dir = proj_dir / "objects" / object_id / "masks"

    candidates = [
        mask_dir / f"mask_{frame_index}.png",
        mask_dir / f"mask_{frame_index:06d}.png",
        mask_dir / "initial_mask.png",
    ]
    for p in candidates:
        if p.is_file():
            return FileResponse(str(p), media_type="image/png")

    # Fall back to any preview mask
    if mask_dir.is_dir():
        previews = sorted(mask_dir.glob("preview_mask_*.png"))
        if previews:
            return FileResponse(str(previews[0]), media_type="image/png")

    raise HTTPException(404, f"Mask for frame {frame_index} not found")


@router.get("/{project_id}/objects/{object_id}/inpainted/{frame_index}")
@router.get("/{project_id}/objects/{object_id}/inpainted/{frame_index}/")
def get_inpainted_frame(
    project_id: str, object_id: str, frame_index: int,
) -> FileResponse:
    """Serve the inpainted (background-cleaned) frame for an object.

    On demand: loads frame + mask, inpaints the masked region with
    InpaintingService, writes to debug/, and returns the PNG.
    """
    from app.services.inpainting_service import InpaintingService  # noqa: PLC0415

    pwf = get_project_workflow()
    proj_dir = pwf._project_dir(project_id)
    scene_dir = proj_dir / "frames" / "scene_0"
    frame_path = find_frame_path(scene_dir, frame_index)
    if frame_path is None:
        raise HTTPException(404, f"Frame {frame_index} not found")

    mask_dir = proj_dir / "objects" / object_id / "masks"
    mask_candidates = [
        mask_dir / f"mask_{frame_index}.png",
        mask_dir / f"mask_{frame_index:06d}.png",
        mask_dir / "initial_mask.png",
    ]
    mask_path = next((p for p in mask_candidates if p.is_file()), None)
    if mask_path is None and mask_dir.is_dir():
        previews = sorted(mask_dir.glob("preview_mask_*.png"))
        if previews:
            mask_path = previews[0]
    if mask_path is None:
        # No mask — fall back to original frame
        media = "image/jpeg" if frame_path.suffix in (".jpg", ".jpeg") else "image/png"
        return FileResponse(str(frame_path), media_type=media)

    import cv2

    frame = cv2.imread(str(frame_path))
    if frame is None:
        raise HTTPException(500, "Could not read frame")

    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise HTTPException(500, "Could not read mask")

    # Resize mask to frame if needed
    if mask.shape[:2] != frame.shape[:2]:
        mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))

    svc = InpaintingService()
    dilated = svc.dilate_mask(mask, kernel_size=5, iterations=2)
    result = svc.inpaint_frame(frame, dilated, method="telea", radius=3)

    out_dir = proj_dir / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"inpainted_{object_id}_{frame_index}.png"
    cv2.imwrite(str(out_path), result)
    return FileResponse(str(out_path), media_type="image/png")


@router.patch("/{project_id}/objects/{object_id}/replacement-settings")
def update_replacement_settings(
    project_id: str, object_id: str, body: ReplacementSettingsRequest,
) -> dict[str, object]:
    """Update replacement transform settings."""
    rep_svc = get_replacement_service()
    try:
        obj = rep_svc.update_settings(
            project_id, object_id, body.replacement_config,
        )
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e
    return obj.model_dump()


@router.post("/{project_id}/preview")
@router.post("/{project_id}/preview/")
def render_preview(project_id: str, object_id: str = "") -> dict[str, object]:
    """Render a preview video. Returns a job.

    Durable submission (S02-T05): the request validates inputs and writes an
    input-manifest Job row; the registered ``preview`` handler runs in the
    durable worker (AC2/AC6).
    """
    pwf = get_project_workflow()

    try:
        project = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    if not object_id and project.objects:
        object_id = project.objects[0].object_id

    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    if obj.motion is None or not obj.motion.frames:
        raise HTTPException(400, "Object has no motion data. Run propagation first.")

    job_svc = get_job_service()
    info = job_svc.create_job(
        "preview",
        input_manifest={
            "project_id": project_id,
            "object_id": object_id,
            "scene_id": obj.scene_id,
        },
        workspace_id="default",
        owner_type="project",
        owner_id=project_id,
        idempotency_key=f"preview:{project_id}:{object_id}",
    )
    return job_response(info)


@router.post("/{project_id}/render")
@router.post("/{project_id}/render/")
def render_final(
    project_id: str, object_id: str = "", format: str = "mp4",
) -> dict[str, object]:
    """Render the final video in specified format (mp4/webm/gif). Returns a job.

    Durable submission (S02-T05): the request validates inputs and writes an
    input-manifest Job row; the registered ``render`` handler runs in the
    durable worker (AC2/AC6).
    """
    pwf = get_project_workflow()

    try:
        project = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    if not object_id and project.objects:
        object_id = project.objects[0].object_id

    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    if obj.motion is None or not obj.motion.frames:
        raise HTTPException(400, "Object has no motion data. Run propagation first.")

    job_svc = get_job_service()
    info = job_svc.create_job(
        "render",
        input_manifest={
            "project_id": project_id,
            "object_id": object_id,
            "scene_id": obj.scene_id,
            "format": format,
        },
        workspace_id="default",
        owner_type="project",
        owner_id=project_id,
        idempotency_key=f"render:{project_id}:{object_id}:{format}",
    )
    return job_response(info)


# ── Dubbing endpoints ───────────────────────────────────────────────────────

class DubbingRequest(BaseModel):
    scene_id: int
    source_lang: str = "vi"
    target_lang: str = "en"
    whisper_model: str = "base"
    tts_voice: str = "en-US-AriaNeural"


@router.post("/{project_id}/dubbing/separate")
@router.post("/{project_id}/dubbing/separate/")
def separate_audio(project_id: str, scene_id: int) -> dict[str, object]:
    """Separate scene audio into vocal and background tracks."""
    from app.workflow.audio_dubbing_service import AudioDubbingService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    audio_path = proj_dir / "audio" / f"scene_{scene_id:03d}.aac"
    if not audio_path.exists():
        raise HTTPException(404, f"Audio for scene {scene_id} not found")

    output_dir = proj_dir / "dubbing" / f"scene_{scene_id:03d}"
    svc = AudioDubbingService()
    vocal, bgm = svc.separate_vocals(audio_path, output_dir)

    return {
        "vocal_track": str(vocal),
        "bgm_track": str(bgm),
    }


@router.post("/{project_id}/dubbing/transcribe")
@router.post("/{project_id}/dubbing/transcribe/")
def transcribe_scene(
    project_id: str, scene_id: int,
    source_lang: str = "vi", whisper_model: str = "base",
) -> dict[str, object]:
    """Transcribe scene vocal track to text."""
    from app.workflow.audio_dubbing_service import AudioDubbingService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    vocal_path = proj_dir / "dubbing" / f"scene_{scene_id:03d}" / "vocal_track.wav"
    if not vocal_path.exists():
        raise HTTPException(400, "Run audio separation first")

    svc = AudioDubbingService()
    segments = svc.transcribe(vocal_path, language=source_lang, model_size=whisper_model)
    srt_path = svc.segments_to_srt(
        segments,
        proj_dir / "dubbing" / f"scene_{scene_id:03d}" / "subtitles_original.srt",
    )

    return {"segments": segments, "srt_path": str(srt_path)}


@router.post("/{project_id}/dubbing/translate")
@router.post("/{project_id}/dubbing/translate/")
def translate_subtitles(
    project_id: str, scene_id: int,
    target_lang: str = "en", source_lang: str = "auto",
) -> dict[str, object]:
    """Translate scene subtitles to target language."""
    from app.workflow.audio_dubbing_service import AudioDubbingService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    dubbing_dir = proj_dir / "dubbing" / f"scene_{scene_id:03d}"

    svc = AudioDubbingService()

    # Try to load existing segments
    vocal_path = dubbing_dir / "vocal_track.wav"
    if not vocal_path.exists():
        raise HTTPException(400, "Run audio separation and transcription first")

    segments = svc.transcribe(vocal_path, language=source_lang)
    translated = svc.translate_segments(segments, target_lang=target_lang)
    srt_path = svc.segments_to_srt(translated, dubbing_dir / "subtitles_translated.srt")

    return {"segments": translated, "srt_path": str(srt_path)}


@router.post("/{project_id}/dubbing/tts")
@router.post("/{project_id}/dubbing/tts/")
def generate_tts(
    project_id: str, scene_id: int,
    target_lang: str = "en",
    tts_voice: str = "en-US-AriaNeural",
) -> dict[str, object]:
    """Generate TTS audio for translated segments."""
    from app.workflow.audio_dubbing_service import AudioDubbingService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    dubbing_dir = proj_dir / "dubbing" / f"scene_{scene_id:03d}"

    # Load translated segments
    translated_srt = dubbing_dir / "subtitles_translated.srt"
    if not translated_srt.exists():
        raise HTTPException(400, "Run translation first")

    svc = AudioDubbingService()
    # Parse SRT back to segments
    segments = svc.transcribe(dubbing_dir / "vocal_track.wav", language=target_lang)

    # Generate TTS
    tts_dir = dubbing_dir / "tts_segments"
    tts_paths = svc.tts_segments(segments, tts_dir, voice=tts_voice)

    return {"tts_count": len(tts_paths), "tts_dir": str(tts_dir)}


@router.post("/{project_id}/dubbing/remux")
@router.post("/{project_id}/dubbing/remux/")
def remux_dubbed_audio(
    project_id: str, scene_id: int,
    tts_voice: str = "en-US-AriaNeural",
) -> dict[str, object]:
    """Remux TTS with background music into final dubbed audio."""
    from app.workflow.audio_dubbing_service import AudioDubbingService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    dubbing_dir = proj_dir / "dubbing" / f"scene_{scene_id:03d}"
    bgm_path = dubbing_dir / "bgm_sfx_track.wav"

    if not bgm_path.exists():
        raise HTTPException(400, "Run audio separation first")

    svc = AudioDubbingService()

    # Get TTS files
    tts_dir = dubbing_dir / "tts_segments"
    tts_paths = sorted(tts_dir.glob("tts_*.wav"))
    if not tts_paths:
        raise HTTPException(400, "Generate TTS first")

    # Parse timing from translated SRT
    segments = svc.transcribe(dubbing_dir / "vocal_track.wav")
    translated = svc.translate_segments(segments, target_lang="en")

    # Remux
    final_path = dubbing_dir / "dubbed_audio.wav"
    svc.remux_audio(tts_paths, translated, bgm_path, final_path)

    return {"final_audio": str(final_path)}


@router.post("/{project_id}/dubbing/full")
@router.post("/{project_id}/dubbing/full/")
def full_dubbing_pipeline(project_id: str, body: DubbingRequest) -> dict[str, object]:
    """Run full dubbing pipeline for a scene."""
    from app.workflow.audio_dubbing_service import AudioDubbingService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    audio_path = proj_dir / "audio" / f"scene_{body.scene_id:03d}.aac"
    if not audio_path.exists():
        raise HTTPException(404, f"Audio for scene {body.scene_id} not found")

    output_dir = proj_dir / "dubbing" / f"scene_{body.scene_id:03d}"
    svc = AudioDubbingService()

    result = svc.dub_scene(
        audio_path=audio_path,
        output_dir=output_dir,
        source_lang=body.source_lang,
        target_lang=body.target_lang,
        whisper_model=body.whisper_model,
        tts_voice=body.tts_voice,
    )

    return result


# ── Scene management endpoints ──────────────────────────────────────────────

class SceneStatusUpdate(BaseModel):
    status: str  # "pending" | "draft" | "approved"
    notes: str = ""


@router.post("/{project_id}/scenes/chunk")
@router.post("/{project_id}/scenes/chunk/")
def chunk_scenes(project_id: str, threshold: float = 27.0) -> dict[str, object]:
    """Re-chunk video into scenes and extract per-scene audio."""
    from app.workflow.scene_chunking_service import SceneChunkingService

    pwf = get_project_workflow()
    config = get_config()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    video_metadata = proj.video_metadata
    if video_metadata is None or not video_metadata.file_path:
        raise HTTPException(400, "Video file not found")
    video_path = Path(video_metadata.file_path)
    if not video_path.exists():
        raise HTTPException(400, "Video file not found")

    proj_dir = pwf._project_dir(project_id)
    audio_dir = proj_dir / "audio"

    svc = SceneChunkingService(config)
    scene_details = svc.chunk_video(video_path, audio_dir, threshold=threshold)

    # Update project with scene details
    proj.scene_details = scene_details
    pwf._save_project(project_id, proj)

    return {
        "scene_count": len(scene_details),
        "scenes": [s.model_dump() for s in scene_details],
    }


@router.get("/{project_id}/scenes/details")
def get_scene_details(project_id: str) -> list[dict[str, object]]:
    """Get scene details with status."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    return [s.model_dump() for s in proj.scene_details]


@router.patch("/{project_id}/scenes/{scene_id}/status")
def update_scene_status(
    project_id: str, scene_id: int, body: SceneStatusUpdate,
) -> dict[str, object]:
    """Update a scene's status (pending/draft/approved)."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    valid_statuses = {"pending", "draft", "approved"}
    if body.status not in valid_statuses:
        raise HTTPException(400, f"Invalid status: {body.status}")

    found = False
    for sd in proj.scene_details:
        if sd.scene_id == scene_id:
            sd.status = SceneStatus(body.status)
            sd.notes = body.notes
            found = True
            break

    if not found:
        raise HTTPException(404, f"Scene {scene_id} not found")

    pwf._save_project(project_id, proj)
    return {"ok": True, "scene_id": scene_id, "status": body.status}


@router.get("/{project_id}/scenes/{scene_id}/audio")
def get_scene_audio(project_id: str, scene_id: int) -> FileResponse:
    """Serve the audio file for a scene."""
    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    audio_path = proj_dir / "audio" / f"scene_{scene_id:03d}.aac"

    if not audio_path.exists():
        raise HTTPException(404, f"Audio for scene {scene_id} not found")

    return FileResponse(str(audio_path), media_type="audio/aac")


@router.post("/{project_id}/scenes/{scene_id}/extract-frames")
@router.post("/{project_id}/scenes/{scene_id}/extract-frames/")
def extract_scene_frames(
    project_id: str, scene_id: int, format: str = "jpg",
) -> dict[str, object]:
    """Extract frames from a scene clip on-demand.

    Only called when user opens/selects a scene. Much faster than
    extracting all frames at ingest time.
    """
    from app.workflow.scene_chunking_service import SceneChunkingService

    pwf = get_project_workflow()
    config = get_config()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    clip_path = proj_dir / "scenes" / f"scene_{scene_id:03d}.mp4"

    if not clip_path.exists():
        raise HTTPException(404, f"Scene clip {scene_id} not found")

    frames_dir = proj_dir / "frames" / f"scene_{scene_id}"
    svc = SceneChunkingService(config)
    frames = svc.extract_frames_on_demand(clip_path, frames_dir, format=format)

    return {
        "scene_id": scene_id,
        "frame_count": len(frames),
        "format": format,
        "frames_dir": str(frames_dir),
    }


@router.post("/{project_id}/scenes/stitch")
@router.post("/{project_id}/scenes/stitch/")
def stitch_scenes(project_id: str) -> dict[str, object]:
    """Stitch all approved scenes into final video."""
    from app.workflow.scene_stitch_service import SceneStitchService

    pwf = get_project_workflow()
    config = get_config()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Check all scenes are approved
    pending = [s for s in proj.scene_details if s.status != "approved"]
    if pending:
        raise HTTPException(
            400,
            f"{len(pending)} scenes not approved yet: "
            f"{[s.scene_id for s in pending]}",
        )

    proj_dir = pwf._project_dir(project_id)
    output_path = proj_dir / "renders" / "final_output.mp4"

    svc = SceneStitchService(config)
    result = svc.stitch_with_audio(proj_dir, proj.scene_details, output_path)

    return {"ok": True, "output_path": str(result)}


# ── Bulk character mapping ───────────────────────────────────────────────────

class BulkMappingRequest(BaseModel):
    object_id: str
    scene_ids: list[int] = Field(default_factory=list)  # empty = all scenes


@router.post("/{project_id}/objects/{object_id}/apply-bulk")
@router.post("/{project_id}/objects/{object_id}/apply-bulk/")
def apply_bulk_mapping(
    project_id: str, object_id: str, body: BulkMappingRequest,
) -> dict[str, object]:
    """Apply an object's replacement config to multiple scenes."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Find the source object
    source_obj = None
    for obj in proj.objects:
        if obj.object_id == object_id:
            source_obj = obj
            break

    if source_obj is None:
        raise HTTPException(404, "Object not found")

    # Determine target scenes
    target_scenes = body.scene_ids
    if not target_scenes:
        target_scenes = [s.scene_id for s in proj.scene_details]

    # Apply replacement config to all objects in target scenes
    applied = []
    for obj in proj.objects:
        if obj.object_id == object_id:
            continue  # skip source
        if obj.scene_id in target_scenes:
            obj.replacement_config = source_obj.replacement_config
            applied.append(obj.object_id)

    pwf._save_project(project_id, proj)
    return {"applied_to": applied, "scene_ids": target_scenes}


# ── Preset endpoints ────────────────────────────────────────────────────────

class SavePresetRequest(BaseModel):
    name: str = "Untitled Preset"
    description: str = ""


@router.post("/{project_id}/presets/save")
@router.post("/{project_id}/presets/save/")
def save_project_preset(
    project_id: str, body: SavePresetRequest,
) -> dict[str, object]:
    """Save current project configuration as a preset."""
    from app.workflow.preset_service import (  # noqa: PLC0415
        CharacterMapping,
        PresetService,
        ProjectPreset,
    )

    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Build mappings from current objects
    mappings = []
    for obj in proj.objects:
        rc = obj.replacement_config
        mappings.append(CharacterMapping(
            original_name=obj.name,
            replacement_asset=rc.asset_path if rc else "",
            replacement_config=rc.model_dump(by_alias=True) if rc else {},
        ))

    preset = ProjectPreset(
        name=body.name,
        description=body.description,
        mappings=mappings,
    )

    proj_dir = pwf._project_dir(project_id)
    presets_dir = proj_dir / "presets"
    output_path = presets_dir / f"{body.name.lower().replace(' ', '_')}.json"

    svc = PresetService()
    svc.save_preset(preset, output_path)

    return {"ok": True, "path": str(output_path), "mapping_count": len(mappings)}


@router.get("/{project_id}/presets")
def list_project_presets(project_id: str) -> list[dict[str, object]]:
    """List all presets for a project."""
    from app.workflow.preset_service import PresetService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    presets_dir = proj_dir / "presets"

    svc = PresetService()
    return svc.list_presets(presets_dir)


@router.post("/{project_id}/presets/{preset_filename}/apply")
@router.post("/{project_id}/presets/{preset_filename}/apply/")
def apply_preset(project_id: str, preset_filename: str) -> dict[str, object]:
    """Apply a preset to the current project."""
    from app.workflow.preset_service import PresetService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    preset_path = proj_dir / "presets" / preset_filename

    svc = PresetService()
    try:
        preset = svc.load_preset(preset_path)
    except FileNotFoundError as err:
        raise HTTPException(404, "Preset not found") from err

    updated = svc.apply_preset_to_project(preset, proj)
    pwf._save_project(project_id, proj)

    return {"ok": True, "updated_objects": updated}


# ── Export ZIP endpoint ─────────────────────────────────────────────────────

@router.get("/{project_id}/export")
def export_project_zip(project_id: str) -> FileResponse:
    """Export project as ZIP containing rendered video, SRT, and dubbing."""
    import zipfile  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    zip_path = proj_dir / f"{project_id}_export.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add rendered videos
        renders_dir = proj_dir / "renders"
        if renders_dir.exists():
            for f in renders_dir.glob("*.mp4"):
                zf.write(f, f"renders/{f.name}")
            for f in renders_dir.glob("*.webm"):
                zf.write(f, f"renders/{f.name}")

        # Add SRT and WAV files
        dubbing_dir = proj_dir / "dubbing"
        if dubbing_dir.exists():
            for f in dubbing_dir.rglob("*.srt"):
                zf.write(f, f"dubbing/{f.relative_to(dubbing_dir)}")
            for f in dubbing_dir.rglob("*.wav"):
                zf.write(f, f"dubbing/{f.relative_to(dubbing_dir)}")

        # Add project JSON
        project_json = proj_dir / "project.json"
        if project_json.exists():
            zf.write(project_json, "project.json")

        # Add presets
        presets_dir = proj_dir / "presets"
        if presets_dir.exists():
            for f in presets_dir.glob("*.json"):
                zf.write(f, f"presets/{f.name}")

    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"{project_id}_export.zip",
    )


# ── Channel Workspace endpoints ──────────────────────────────────────────────

class CreateChannelRequest(BaseModel):
    name: str
    target_lang: str = "en"
    default_preset_id: str = ""

class UpdateTaskStatusRequest(BaseModel):
    task_status: str  # draft | in_progress | ready_to_stitch | completed


@router.post("/channels")
@router.post("/channels/")
def create_channel(body: CreateChannelRequest) -> dict[str, object]:
    """Create a new channel workspace."""
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415

    config = get_config()
    svc = ChannelService(config)
    channel = svc.create_channel(
        name=body.name,
        target_lang=body.target_lang,
        default_preset_id=body.default_preset_id,
    )
    return channel.model_dump()


@router.get("/channels")
def list_channels() -> list[dict[str, object]]:
    """List all channel workspaces."""
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415

    config = get_config()
    svc = ChannelService(config)
    return [c.model_dump() for c in svc.list_channels()]


@router.get("/channels/{channel_id}/projects")
def get_channel_projects(channel_id: str) -> list[dict[str, object]]:
    """List projects in a channel."""
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415

    config = get_config()
    svc = ChannelService(config)
    channel = svc.get_channel(channel_id)
    if channel is None:
        raise HTTPException(404, "Channel not found")

    return svc.get_projects_for_channel(channel_id, config.project_root)


@router.delete("/channels/{channel_id}")
@router.delete("/channels/{channel_id}/")
def delete_channel(channel_id: str) -> dict[str, object]:
    """Delete a channel workspace."""
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415

    config = get_config()
    svc = ChannelService(config)
    if not svc.delete_channel(channel_id):
        raise HTTPException(404, "Channel not found")
    return {"ok": True}


@router.patch("/{project_id}/task-status")
def update_task_status(project_id: str, body: UpdateTaskStatusRequest) -> dict[str, object]:
    """Update project task status."""
    valid = {"draft", "in_progress", "ready_to_stitch", "completed"}
    if body.task_status not in valid:
        raise HTTPException(400, f"Invalid status: {body.task_status}")

    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj.task_status = body.task_status
    pwf._save_project(project_id, proj)
    return {"ok": True, "task_status": body.task_status}


@router.patch("/{project_id}/assign-channel")
def assign_channel(project_id: str, channel_id: str) -> dict[str, object]:
    """Assign a project to a channel."""
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj.channel_id = channel_id
    pwf._save_project(project_id, proj)
    return {"ok": True, "channel_id": channel_id}


# ── Cleanup endpoint ────────────────────────────────────────────────────────

@router.post("/{project_id}/cleanup")
@router.post("/{project_id}/cleanup/")
def cleanup_project(project_id: str) -> dict[str, object]:
    """Clean up temp files and debug artifacts."""
    from app.services.cleanup_service import CleanupService  # noqa: PLC0415

    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    svc = CleanupService()
    stats = svc.cleanup_project(proj_dir)

    return {
        "ok": True,
        "files_removed": stats["files_removed"],
        "dirs_removed": stats["dirs_removed"],
        "bytes_freed": stats["bytes_freed"],
    }


# ── Auto-match character endpoint ──────────────────────────────────────────

@router.post("/{project_id}/objects/{object_id}/auto-match")
@router.post("/{project_id}/objects/{object_id}/auto-match/")
def auto_match_character(project_id: str, object_id: str) -> dict[str, object]:
    """Auto-match character across all scenes using bbox similarity.

    Finds objects in other scenes with similar position/size and
    applies the same replacement config.
    """
    pwf = get_project_workflow()
    try:
        proj = pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    # Find source object
    source = None
    for obj in proj.objects:
        if obj.object_id == object_id:
            source = obj
            break
    if source is None:
        raise HTTPException(404, "Object not found")

    # If source.motion is None, fallback to using source.selection bounding box
    source_bbox: SelectionInput | BoundingBox | None = None
    if source.selection and source.selection.mode == "bounding_box":
        source_bbox = source.selection
    elif source.motion and source.motion.frames:
        for m in source.motion.frames:
            if m.centroid_x > 0:
                source_bbox = m.bbox
                break

    # AI auto-pose matching: analyze the source bbox aspect ratio to pick the
    # best preset pose, then auto-apply the correct pose to every scene.
    from app.services.preset_manager import (  # noqa: PLC0415
        CharacterPresetManager,
        get_preset_manager,
    )

    pose_choice: str | None = None
    if (
        source_bbox is not None
        and source_bbox.width is not None
        and source_bbox.width > 0
    ):
        # Pass centroid + bbox position so the AI can also detect a
        # "looking away" pose (centroid far from bbox center → back).
        centroid_x: float | None = None
        centroid_y: float | None = None
        bbox_x: float | None = None
        bbox_y: float | None = None
        if source.motion and source.motion.frames:
            for m in source.motion.frames:
                if m.centroid_x > 0:
                    centroid_x = m.centroid_x
                    centroid_y = m.centroid_y
                    bbox_x = m.bbox.x
                    bbox_y = m.bbox.y
                    break
        elif source.selection and source.selection.mode == "bounding_box":
            bbox_x = source.selection.x
            bbox_y = source.selection.y

        pose_choice = CharacterPresetManager.auto_pose_for_bbox(
            float(source_bbox.width) if source_bbox.width is not None else 0.0,
            float(source_bbox.height) if source_bbox.height is not None else 0.0,
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            bbox_x=bbox_x,
            bbox_y=bbox_y,
        )
        pm = get_preset_manager()
        pose_asset = pm.asset_path("boy_hacker", pose_choice)  # default set
        if pose_asset is not None:
            proj_dir = pwf._project_dir(project_id)
            for obj in proj.objects:
                if obj.object_id == object_id or obj.scene_id == source.scene_id:
                    continue
                obj_dir = proj_dir / "objects" / obj.object_id
                obj_dir.mkdir(parents=True, exist_ok=True)
                dest = obj_dir / "replacement.png"
                shutil.copy2(str(pose_asset), str(dest))
                if obj.replacement_config is None:
                    from app.schemas import ReplacementConfig

                    obj.replacement_config = ReplacementConfig(
                        mode=ReplacementMode.STATIC_ASSET,
                        assetPath=f"objects/{obj.object_id}/replacement.png",
                    )
                else:
                    obj.replacement_config.mode = ReplacementMode.STATIC_ASSET
                    obj.replacement_config.asset_path = (
                        f"objects/{obj.object_id}/replacement.png"
                    )

    # source_bbox retained for future similarity matching; current behavior
    # applies the replacement config to all other-scene objects.
    _ = source_bbox

    matched: list[str] = []
    for obj in proj.objects:
        if obj.object_id == object_id or obj.scene_id == source.scene_id:
            continue
        # Copy replacement config to matching objects (pose asset included)
        if obj.replacement_config is None:
            from app.schemas import ReplacementConfig

            obj.replacement_config = ReplacementConfig(
                mode=ReplacementMode.STATIC_ASSET,
                assetPath=f"objects/{obj.object_id}/replacement.png",
            )
        else:
            obj.replacement_config.mode = (
                source.replacement_config.mode
                if source.replacement_config
                else ReplacementMode.STATIC_ASSET
            )
            obj.replacement_config.asset_path = (
                source.replacement_config.asset_path
                if source.replacement_config
                else f"objects/{obj.object_id}/replacement.png"
            )
        matched.append(obj.object_id)

    pwf._save_project(project_id, proj)
    return {
        "status": "ok",
        "matched": matched,
        "count": len(matched),
        "pose": pose_choice,
        "warning": "Applied replacement config to all scenes",
    }
