# ScreenD Replacement Canvas Fixes (M7.6–M7.8)

Session detail for the replacement-character display flow: auto-match 400,
modal hang, stale-image cache, inpainted background, split comparison.

## auto_match_character — fallback when motion is None (M7.6)

The endpoint must NEVER 400 on missing motion. Old code raised two
`HTTPException(400, ...)` ("Object has no motion data" / "No valid motion
data"). Correct behavior: compute `source_bbox` from selection when motion is
None (or first motion frame with centroid), then copy `source.replacement_config`
to every object in a different scene and save:

```python
source_bbox = None
if source.selection and source.selection.mode == "bounding_box":
    source_bbox = source.selection
elif source.motion and source.motion.frames:
    for m in source.motion.frames:
        if m.centroid_x > 0:
            source_bbox = m.bbox
            break

matched = []
for obj in proj.objects:
    if obj.object_id == object_id or obj.scene_id == source.scene_id:
        continue
    obj.replacement_config = source.replacement_config
    matched.append(obj.object_id)

pwf._save_project(project_id, proj)
return {"status": "ok", "matched": matched, "count": len(matched),
        "warning": "Applied replacement config to all scenes"}
```

Ruff note: if you compute `source_bbox` but never use it, ruff F841 fires. Keep
the variable (spec requires it) or prefix `_source_bbox`.

## confirm-replace must close the modal IMMEDIATELY (M7.7)

Old code only closed the compare modal in `uploadMut.onSuccess` → modal hangs
while the upload is in flight. Fix:

```tsx
const handleConfirmReplace = () => {
  if (!pendingFile) return;
  setPendingPreview(null);        // close modal NOW (revoke happens in onSuccess/cleanup)
  setPreviewMode("result");       // canvas switches to result mode
  uploadMut.mutate(pendingFile);  // async upload; onSuccess sets replacement + banner
};
```

## CompositeCanvas draws replacement even when frameMotion is null (M7.7)

Bbox-created objects have `motion = null` → the old `if (activeRepImg &&
frameMotion)` guard silently skipped drawing → canvas showed only background.
Fix: compute an `effMotion` fallback placement when frameMotion is null:
- centroid = video center `(videoWidth/2, videoHeight/2)`
- size = replacement natural aspect × 30% of frame height
- apply `replacement.anchor/offset/scale/rotation/opacity` as usual
- bbox, centroid dot, anchor marker all use the fallback coords

TypeScript gotcha: after introducing `effMotion`, replace EVERY `frameMotion.*`
reference in the single-object branch with `(effMotion ? effMotion.* : fallback)`
or tsc errors TS18047 (possibly null) at each line.

## Browser image cache — always cache-bust replacementUrl (M7.8)

After re-upload, the browser serves the OLD replacement PNG from cache → user
sees stale character. Append a timestamp + asset version:

```tsx
const replacementUrl =
  projectId && objectId && replacement.asset_path
    ? `${api.getReplacementImageUrl(projectId, objectId)}?t=${Date.now()}&v=${encodeURIComponent(replacement.asset_path)}`
    : null;
```

When `asset_path` changes, the URL changes → the CompositeCanvas `repImg`
loading effect re-runs → redraw. Same pattern for any served image that can be
replaced at the same path.

## Inpainted background endpoints (M7.8)

`InpaintingService` existed but had NO API route; the frontend's `maskUrl`
(`/objects/{id}/masks/{frame}`) also pointed at a nonexistent route (404).
Added two endpoints after `get_replacement_image`:

- `GET /{project_id}/objects/{object_id}/masks/{frame_index}` (+ `/`) — serves
  `mask_{frame}.png` / `mask_{frame:06d}.png` / `initial_mask.png`, falls back
  to any `preview_mask_*.png`
- `GET /{project_id}/objects/{object_id}/inpainted/{frame_index}` (+ `/`) —
  on-demand inpaint: find frame via `find_frame_path(scene_dir, frame_index)`,
  find mask, resize mask to frame shape, `InpaintingService.dilate_mask(5, 2)`
  + `inpaint_frame(telea, radius=3)`, write to `debug/inpainted_{oid}_{frame}.png`,
  return FileResponse. If NO mask exists → fall back to the original frame
  (media type from extension) so the endpoint never 404s on unmasked objects.

Frontend: `getInpaintedFrameUrl(projectId, objectId, frameIndex)` in api.ts;
CompositeCanvas takes `inpaintedUrl?: string | null`, loads it, and uses
`inpaintedImg ?? frameImg` as the base layer in `drawComposite`.

## Auto bottom-anchor (M7.8)

To seat the new character's feet/hips on the original surface, lift the default
center anchor (0.5, 0.5) to bottom-center (0.5, 1.0) inside
`computeReplacementTransform`:

```ts
const autoBottom = rep.anchor.x === 0.5 && (rep.anchor.y === 0.5 || rep.anchor.y === 1.0);
const anchorY = autoBottom ? 1.0 : rep.anchor.y;
const anchorPxY = finalH * anchorY;
```

Do the same in the no-motion fallback branch.

## Split comparison 50/50

Comparison mode draws: left half = original frame (crop to videoWidth/2),
divider line, right half = `drawComposite(halfW)` (full composite with
replacement). Label bars `rgba(0,0,0,0.45)` + `📷 Ảnh Gốc (Gốc ban đầu)` /
`🎨 Kết Quả Thay Thế (Sau khi đổi)`. Text must be added AFTER the rect so it
renders on top.

## Test recipes

- Synthetic mask test: write `mask_000000.png` into the isolated test root
  (`deps._config.project_root / "projects" / pid / "objects" / oid / "masks"`)
  then GET both endpoints; assert `content-type` starts `image/png`; test both
  trailing-slash variants.
- Fallback-without-mask test: create frame + object but NO mask → inpainted
  endpoint returns 200 with `image/` content type (original frame).
- Test helper `_make_object_with_mask(client, pid)` — creates frame, object via
  POST, writes mask file. NOTE: the class has NO `_make_project` helper — create
  projects inline with `client.post("/api/projects", json={"name": ...})`.
- When adding tests to `TestDeleteSingleAndClear`, the helper must be inserted
  with its full `def` line AND the next test's def line in the same patch —
  the patch tool's fuzzy matching can detach the next docstring from its
  function (seen twice: docstring left dangling, and two lines of a test body
  deleted). Always re-read the region after patching.

## Verification pattern (repeatable)

1. `export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"`
2. Restart backend AFTER every backend commit: kill old session, start
   `python -m uvicorn app.main:app --host 127.0.0.1 --port 8002` background
3. Live-verify new endpoints with curl BEFORE telling the user to F5:
   `curl -s -o /dev/null -w "%{http_code} %{content_type}\n" <url>`
   (exit code 23 = write-error on `-w`, harmless — re-run with `-o /dev/null`)
4. Gates: `python -m ruff check app/ tests/` → `python -m pytest tests/ -v` →
   `npx tsc --noEmit` → `npm run build`
5. Stale-backend tell: backend log shows the NEW frontend URL (with `?t=...`
   cache-buster) hitting 404 — frontend is new, backend is old. Restart backend.
