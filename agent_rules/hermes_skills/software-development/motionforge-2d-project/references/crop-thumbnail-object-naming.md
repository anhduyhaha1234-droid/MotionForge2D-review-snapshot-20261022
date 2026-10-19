# Crop Thumbnails & Distinct Object Naming (M7.1 / M7.2)

Session-specific implementation detail for MotionForge 2D commits `74e1124` and `048550d`.

## Why this exists

User feedback chain:
1. Screen B/D object cards showed empty black boxes — no visual of what was detected.
2. BA/PM requested auto-cropped thumbnails per object (`crop.png`), served by an endpoint, shown in both screens.
3. Then: objects all named the same ("Test Object") — requested distinct names based on size + order.

## Implementation

### Backend (app/api/routes/projects.py)

```python
def _auto_crop_object(proj_dir, object_id, selection, pad=10) -> Path | None:
    # 1. find frame: find_frame_path(scene_dir, selection.frame_index), glob fallback
    # 2. cv2.imread; get h,w
    # 3. bbox mode: x=sel.x-pad, y=sel.y-pad, bw=sel.width+2*pad, bh=sel.height+2*pad
    #    point mode: 160×160 window centered on (sel.x, sel.y)
    # 4. clamp x,y,bw,bh to frame bounds; skip if bw/bh <= 0
    # 5. crop_img = frame[y:y+bh, x:x+bw]; cv2.imwrite(obj_dir/"crop.png")
    # returns Path or None (never raises — wrapped in try/except)
```

- Called in `create_object` before `pwf.add_tracked_object`; sets `obj.crop_path = str(crop_file)`.
- `GET /{project_id}/objects/{object_id}/crop` + `/crop/` alias → `FileResponse(media_type="image/png")`; if crop.png missing, calls `_auto_crop_object` on the fly.
- `GET /{project_id}/objects` (`list_objects`) + alias: each object's `model_dump(by_alias=True)` gets `thumbnail_base64` (data URL) if `objects/{oid}/thumbnail.png` exists.
- `auto_segment_objects` now emits `name`: `Nhân vật #N (W×Hpx)` when `full_area > w*h*0.05` AND `|cx-w/2|+|cy-h/2| < w*0.4`, else `Vật thể #N (W×Hpx)`.
- `create_object` name dedup: if `body.name` empty or in `("test","object","vật thể","nhân vật")`, generate `Vật thể #{len(existing)+1} ({sw}×{sh}px)` from selection (bbox → its size, point → 160×160).

### Schema (app/schemas/__init__.py)

```python
class TrackedObject(BaseModel):
    ...
    crop_path: str | None = None  # Path to cropped thumbnail PNG
```

### Frontend (api.ts, ScreenB.tsx, ScreenD.tsx)

- `getObjectCropUrl(projectId, objectId)` → `${API_BASE}/api/projects/${projectId}/objects/${objectId}/crop`
- `TrackedObject` interface += `thumbnail_base64?: string`
- `autoSegmentObjects` response type objects += `name?: string`
- Object card `<img>`: crop URL primary, `onError` → `thumbnail_base64` data URL → hide. `w-12 h-12 object-contain bg-black/80 rounded border border-purple-500/50`.
- ScreenB left sidebar: section "🎭 Nhân vật đã tách" listing `project.objects` with crop images (above the auto-detected list).
- ScreenD left column: object cards with crop img + name + scene id.

## Tests (tests/test_delete_and_autosegment.py)

- `TestObjectCrop::test_crop_nonexistent_object` → 404
- `TestObjectCrop::test_crop_generates_after_create` — writes synthetic frame, creates object, GET crop → 200 + `image/png` (both URL forms)
- `TestAutoSegment::test_auto_segment_distinct_names` — white-bg synthetic frame with 2 dark rectangles → names unique, contain `×` and `px`, sizes match bbox

## Gotchas

- **White background for synthetic detection tests.** `THRESH_BINARY_INV+THRESH_OTSU` on a black-bg frame produces a single full-frame contour → `len(objs) >= 2` fails. Use `np.full((H,W,3), 255)` bg with dark objects.
- **Use `deps._config.project_root` for test file writes** — the patched tmp root, not the global `config.project_root` singleton (which points at the real projects dir).
- **Don't forget frontend type alignment**: backend adds `name` + `thumbnail_base64`; `api.ts` interfaces must mirror or `tsc --noEmit` fails (TS2339: Property 'name' does not exist).
