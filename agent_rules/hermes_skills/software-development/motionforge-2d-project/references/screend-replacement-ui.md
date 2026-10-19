# ScreenD — Replacement Screen (3-Column UI)

Refactored to a simple 3-column layout. Use as the canonical shape for the
replacement/composite preview screen.

## Layout
```
Top bar: title + preview mode selector (Ảnh gốc/Mask/Kết quả/So sánh) + back
┌ w-64 (left)  ┌ flex-1 min-w-0 (center)  ┌ w-72 (right)
│ Objects list │ CompositeCanvas          │ 4 transform sliders
│ Upload       │                          │ 🚀 Apply-all (purple)
│ Library btn  │                          │ Áp dụng / Đặt lại / Tiếp: Render
│ Frame slider │                          │ SceneSelector + ScenePreview
└──────────────┴──────────────────────────┴ DubbingPanel (<details>)
```
- All panels `flex-shrink-0` with explicit width; center is `flex-1 min-w-0`
  so it absorbs remaining space.
- Old 4th scene panel (w-52) was folded into the right column below Actions.

## Task 1 — Auto-select first object
```tsx
useEffect(() => {
  if (!activeObject && project?.objects?.length) {
    setActiveObject(project.objects[0]);
  }
}, [activeObject, project, setActiveObject]);
```
Place this effect early (it only references store setters, so the
"useEffect before variable declaration" pitfall does not apply).

## Task 2 — Left column: object cards + upload
- Card per `project.objects`: thumbnail via
  `api.getReplacementImageUrl(projectId, obj.object_id)` with
  `onError` fallback to the generic thumbnail URL
  `` `http://localhost:8000/api/projects/${projectId}/objects/${objectId}/thumbnail` ``
  (set `el.onerror = null` after fallback to avoid loops).
- Active card styling: `bg-purple-900/40 border-purple-500/50`.
- Upload: `<label>` wrapping a hidden `<input type="file" accept=".png,image/png">`
  → `uploadMut` → `setReplacement({ mode: "static_asset", asset_path })`.
- Keep the frame slider at the bottom of the left column.

## Task 4 — Prominent purple apply-all button
Save settings FIRST, then auto-match. `mutateAsync()` (not `mutate()`) so the
alert only fires after both complete:
```tsx
<button
  onClick={async () => {
    if (!projectId || !objectId) return;
    try {
      await settingsMut.mutateAsync();          // persist current transform
      const result = await api.autoMatchCharacter(projectId, objectId);
      alert(`Đã áp dụng nhân vật mới cho ${result.count} cảnh!`);
    } catch (err) {
      alert(`Lỗi: ${(err as Error).message}`);
    }
  }}
  className="w-full py-3 text-sm bg-purple-600 hover:bg-purple-500 text-white
    font-bold rounded-xl shadow-lg shadow-purple-900/40 transition-all"
>
  🚀 Áp Dụng Nhân Vật Mới Cho Tất Cả {sceneCount} Cảnh
</button>
```
- Scene count comes from the project, never hardcoded:
  `const sceneCount = project?.scene_details?.length ?? project?.scenes?.length ?? 0;`

## Right column — 4 sliders only (removed controls)
Removed: Anchor X/Y, Opacity, Fit mode, Clip mode, Mesh transform, Bulk mapping.
Kept 4 sliders with emoji labels + Vietnamese captions:
1. 🔍 Kích thước — `replacement.scale` (0.1–3, step 0.05, unit "x")
2. 🔄 Góc xoay — `replacement.rotation_offset_deg` (−180–180, step 1, unit "°")
3. ↔️ Vị trí Ngang — `replacement.offset.x` (−0.5–0.5, step 0.01)
4. ↕️ Vị trí Dọc — `replacement.offset.y` (−0.5–0.5, step 0.01)

Each slider gets a short caption (`<p className="text-[10px] text-gray-600">`),
e.g. "Phóng to / Thu nhỏ nhân vật mới", "Dịch chuyển nhân vật lên / xuống".

## Keep
- Áp dụng (green, `settingsMut`), Đặt lại (`resetReplacement`),
  Tiếp: Render → (`setScreen("render")`) with their description `<p>`s.
- `SceneSelector` + `ScenePreview` + ✅ Duyệt phân cảnh này moved into the
  right column; `DubbingPanel` stays inside a `<details>` as-is.
- Retained testids: `frame-slider`, `apply-settings`, `next-render`; new
  `apply-all-scenes`. `replacement-upload`/`replacement-preview` testids were
  removed (nothing referenced them in e2e/).

## Verification
1. `cd frontend && npx tsc --noEmit` (strict, no `any`)
2. `cd frontend && npx next build`
3. `cd .. && python -m pytest tests/ -q` — 127 passed, 6 skipped (pre-existing skips)
