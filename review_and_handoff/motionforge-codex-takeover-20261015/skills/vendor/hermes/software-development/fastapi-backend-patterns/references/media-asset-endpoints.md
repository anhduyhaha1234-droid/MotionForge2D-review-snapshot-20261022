# Auto-Generated Media Asset Endpoints — MotionForge2D Crop Implementation

Full working example from MotionForge 2D (object crop thumbnails). This is the concrete
realization of the pattern in SKILL.md; adapt paths/names per project.

## Schema addition

```python
class TrackedObject(BaseModel):
    object_id: str
    name: str
    ...
    crop_path: str | None = None  # Path to cropped thumbnail PNG
```

## Crop helper (module-level function in the routes file)

```python
def _auto_crop_object(
    proj_dir: Path,
    object_id: str,
    selection: SelectionInput,
    pad: int = 10,
) -> Path | None:
    """Crop the object region from the current frame into crop.png.

    Bbox selection → crop the box (+pad). Point selection → 160x160 window
    centered on the click. Returns the crop file path, or None if the frame
    can't be found.
    """
    import cv2

    try:
        f_idx = selection.frame_index
        # find_frame_path tries jpg → jpeg → png (frame format varies)
        frame_path = find_frame_path(scene_dir, f_idx)
        if frame_path is None:
            # fallback: search every scene dir
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
            x = max(0, int(selection.x) - pad)
            y = max(0, int(selection.y) - pad)
            bw = int(selection.width) + 2 * pad
            bh = int(selection.height) + 2 * pad
        else:
            cx, cy = int(selection.x), int(selection.y)
            half = 80
            x, y = max(0, cx - half), max(0, cy - half)
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
```

## Serve endpoint (with lazy regeneration + trailing-slash aliases)

```python
@router.get("/{project_id}/objects/{object_id}/crop")
@router.get("/{project_id}/objects/{object_id}/crop/")
def get_object_crop(project_id: str, object_id: str) -> FileResponse:
    pwf = get_project_workflow()
    try:
        obj = pwf.get_tracked_object(project_id, object_id)
    except (FileNotFoundError, KeyError) as e:
        raise HTTPException(404, str(e)) from e

    proj_dir = pwf._project_dir(project_id)
    crop_file = proj_dir / "objects" / object_id / "crop.png"

    # Lazy regeneration: objects created before this feature (or whose frames
    # were wiped by test isolation) still render.
    if not crop_file.exists():
        generated = _auto_crop_object(proj_dir, object_id, obj.selection)
        if generated is not None:
            crop_file = generated

    if not crop_file.exists():
        raise HTTPException(404, "Crop not found")
    return FileResponse(str(crop_file), media_type="image/png")
```

## Wire into creation (so crop exists from the moment the object is made)

```python
    # ... after mask fallback logic in create_object ...
    crop_file = _auto_crop_object(proj_dir, obj_id, body.selection)
    if crop_file is not None:
        obj.crop_path = str(crop_file)
    data = pwf.add_tracked_object(project_id, obj)
```

## List endpoint with base64 thumbnails (one request, N images)

```python
@router.get("/{project_id}/objects")
@router.get("/{project_id}/objects/")
def list_objects(project_id: str) -> list[dict]:
    import base64
    ...
    for obj in proj.objects:
        item = obj.model_dump(by_alias=True)
        thumb_path = proj_dir / "objects" / obj.object_id / "thumbnail.png"
        item["thumbnail_base64"] = ""
        if thumb_path.exists():
            item["thumbnail_base64"] = (
                "data:image/png;base64," + base64.b64encode(thumb_path.read_bytes()).decode()
            )
        results.append(item)
```

## Frontend consumption

```ts
getObjectCropUrl: (projectId: string, objectId: string) =>
  `${API_BASE}/api/projects/${projectId}/objects/${objectId}/crop`,
```

```tsx
<img
  src={api.getObjectCropUrl(projectId, obj.object_id)}
  alt={obj.name}
  className="w-12 h-12 object-contain bg-black/60 rounded border border-purple-500/50"
  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
/>
```

## Test pattern (synthetic frame → create object → fetch crop)

```python
def test_crop_generates_after_create(self, client) -> None:
    create_resp = client.post("/api/projects", json={"name": "CropProj2"})
    pid = create_resp.json()["project_id"]

    # Synthetic frame directly in the test project's frames dir
    from app.api import deps
    proj_root = deps._config.project_root   # patched to tmp in conftest
    frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[50:150, 50:150] = (0, 0, 255)
    cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

    r = client.post(f"/api/projects/{pid}/objects", json={
        "name": "CropObj",
        "selection": {"mode": "point", "frame_index": 0, "x": 100, "y": 100},
        "scene_id": 0,
    })
    oid = r.json()["object_id"]

    resp = client.get(f"/api/projects/{pid}/objects/{oid}/crop")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")

    resp2 = client.get(f"/api/projects/{pid}/objects/{oid}/crop/")
    assert resp2.status_code == 200  # trailing slash variant, no 405
```

## Why this pattern matters

- **No client upload / no manual step** — the user's core requirement (100% API automation).
- **Lazy regeneration** keeps old records rendering after schema/feature evolution.
- **base64 in list** avoids N+1 image requests in card grids.
- **find_frame_path (jpg→jpeg→png)** handles the frame-format migration (PNG→JPG for ingest speed) without breaking lookups.
