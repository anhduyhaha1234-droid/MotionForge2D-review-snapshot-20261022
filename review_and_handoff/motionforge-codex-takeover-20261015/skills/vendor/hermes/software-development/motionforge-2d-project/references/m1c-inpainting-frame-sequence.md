# M1C: Inpainting, Frame Sequence, Bulk Mapping

## Inpainting Service (`app/services/inpainting_service.py`)
- Uses OpenCV `cv2.inpaint()` with Telea (`INPAINT_TELEA`) or Navier-Stokes (`INPAINT_NS`) methods
- Mask dilation via `cv2.dilate()` with elliptical kernel (`cv2.MORPH_ELLIPSE`)
- Binary mask: `cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)` before processing
- Batch method `process_scene_frames()` takes parallel lists of frame_paths + mask_paths

## ReplacementConfig schema additions
- `frame_sequence_dir: str` (alias `frameSequenceDir`) — path to directory of PNG sequence files
- `frame_sequence_fps: float` (alias `frameSequenceFps`) — override FPS (0 = use scene FPS)
- Mode enum: `ReplacementMode.FRAME_SEQUENCE = "frame_sequence"`

## FRAME_SEQUENCE in render service (`app/workflow/render_service.py`)
- Helper `_get_sequence_frame(sequence_dir, frame_index, total_frames)` loads PNGs sorted alphabetically, cycled by `frame_index % len(png_files)`
- Uses `cv2.IMREAD_UNCHANGED` to preserve alpha channel
- In `_do_render()`, check `rc.mode == ReplacementMode.FRAME_SEQUENCE` before falling back to static asset
- Sequence frames composited same way as static replacement (via `composite_object()`)

## Bulk character mapping endpoint
- `POST /{project_id}/objects/{object_id}/apply-bulk`
- Request body: `BulkMappingRequest(object_id, scene_ids: list[int])`
- Empty `scene_ids` = apply to all scenes (from `proj.scene_details`)
- Copies `replacement_config` from source object to all other objects in target scenes
- Skips the source object itself
- Persists via `pwf._save_project(project_id, proj)`

---

## Frontend Implementation (Milestone 1C)

### ReplacementConfig type update (`frontend/src/lib/api.ts`)
- Union extended: `mode: "none" | "static_asset" | "frame_sequence"`
- Optional fields added: `frameSequenceDir?: string`, `frameSequenceFps?: number`
- New API methods:
  - `applyBulkMapping(projectId, objectId, sceneIds)` → `POST /objects/{oid}/apply-bulk`
  - `inpaintScene(projectId, sceneId)` → `POST /scenes/{sid}/inpaint`
  - `getSequenceFrameUrl(projectId, objectId, index)` → URL string for sequence frame image

### CompositeCanvas FRAME_SEQUENCE support (`CompositeCanvas.tsx`)
- New prop: `sequenceFrameUrl: string | null`
- New state: `sequenceFrameImg` (HTMLImageElement | null)
- Loading effect follows same pattern as frame/mask/replacement image loading:
  ```tsx
  useEffect(() => {
    if (!sequenceFrameUrl) { setSequenceFrameImg(null); return; }
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setSequenceFrameImg(img);
    img.onerror = () => setSequenceFrameImg(null);
    img.src = sequenceFrameUrl;
  }, [sequenceFrameUrl]);
  ```
- Active image selection in render effect:
  ```tsx
  const activeRepImg = replacement.mode === "frame_sequence" ? sequenceFrameImg : repImg;
  ```
- All uses of `repImg` in composite drawing replaced with `activeRepImg`
- `sequenceFrameImg` added to render effect dependency array

### ScreenD mode selector + bulk mapping UI (`ScreenD.tsx`)
- `REPLACEMENT_MODES` constant: `none`, `static_asset`, `frame_sequence` with Vietnamese labels
- Mode `<select>` above the file upload area; file upload only shown when `mode === "static_asset"`
- Frame sequence controls (shown when `mode === "frame_sequence"`):
  - Text input for `frameSequenceDir` (directory path)
  - Number input for `frameSequenceFps` (optional, min=1 max=120)
- `sequenceFrameUrl` computed: `api.getSequenceFrameUrl(projectId, objectId, currentFrame)` when mode matches
- Passed to `<CompositeCanvas sequenceFrameUrl={sequenceFrameUrl} />`
- Bulk mapping section at bottom of right panel:
  - "Áp dụng hàng loạt" heading with purple button
  - `bulkMut` mutation calling `api.applyBulkMapping`
  - Success alert with count of applied objects and scenes
- `settingsMut` updated to include `frameSequenceDir` and `frameSequenceFps` in PATCH payload

### Pattern: Extending a union type + adding optional config fields
When adding a new mode to an existing config type:
1. Extend the union literal type
2. Add optional fields (with `?`) — they don't require changes to `DEFAULT_REPLACEMENT`
3. Update `settingsMut.mutationFn` to pass new fields in the PATCH body
4. Conditionally render mode-specific UI controls
5. Compute mode-specific URLs/data and pass as props to canvas components
