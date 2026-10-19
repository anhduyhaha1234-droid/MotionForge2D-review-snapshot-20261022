# UX & Navigation Overhaul (M6)

## FastAPI Trailing Slash 405 Fix

**Root cause:** FastAPI `redirect_slashes=True` (default) redirects `DELETE /path/` → `GET /path` (301), changing POST/DELETE to GET → 405.

**Fix:**
1. `app/api/app.py`: `FastAPI(redirect_slashes=False)`
2. Trailing slash aliases on 4 critical endpoints:
   - `DELETE /{project_id}` + `DELETE /{project_id}/`
   - `POST /{project_id}/auto-segment-objects` + trailing slash
   - `POST /{project_id}/cleanup` + trailing slash
   - `POST /{project_id}/objects/{object_id}/auto-match` + trailing slash

**Test file:** `tests/test_trailing_slash.py` — 8 tests (with/without slash × 4 endpoints)

## NavigationHeader Component

Sticky top bar with:
- ⬅️ Quay Lại Trang Chủ (back to start screen)
- Project name + ID badge + scene counter (Cảnh #X / N)
- ◀️ Cảnh Trước / Cảnh Sau ▶️ (scene navigation)

Placed in `page.tsx` before `<ScreenRouter />`. Returns null when `screen === "start"` or no project.

## Button Micro-Descriptions

Pattern for tool/action panels — add gray helper text under each button:
```tsx
<button className="...">Điểm +</button>
<p className="text-[10px] text-gray-500 mt-1">Click 1 điểm màu xanh trên thân nhân vật đối thủ.</p>
```

Applied to ScreenB: Điểm+, Điểm-, BBox, Xem Mask, Chấp Nhận & Tách, Auto-Detect.

## Auto Mask on Click

When user clicks Point+ on canvas, auto-trigger preview-mask API via ref flag pattern:
1. `autoPreviewRef.current = true` in click handler
2. `useEffect` watches points state + ref flag → calls `previewMut.mutate()`
3. No manual "Xem mask" button click needed

Uses ref+useEffect pattern (not setTimeout) for reliability.
