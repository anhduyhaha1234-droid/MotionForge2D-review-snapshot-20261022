# UX & Navigation Overhaul

**Date:** 2026-08-02  
**Status:** ✅ Complete  
**Commit:** f7cc37e

---

## Task 1: Fix 405 Method Not Allowed ✅

**Root cause:** FastAPI default `redirect_slashes=True` converts POST/DELETE → GET on redirect, causing 405.

**Fix:** 
- `redirect_slashes=False` in `app/api/app.py`
- Trailing slash aliases for 4 critical endpoints
- 8 new tests verify both `/path` and `/path/` return correct status

| Endpoint | Without `/` | With `/` |
|----------|-------------|----------|
| DELETE /{project_id} | 200 ✅ | 200 ✅ |
| POST /auto-segment-objects | 404 ✅ | 404 ✅ |
| POST /cleanup | 200 ✅ | 200 ✅ |
| POST /auto-match | 404 ✅ | 404 ✅ |

## Task 2: Navigation Header ✅

- `NavigationHeader.tsx`: sticky top bar
- ⬅️ Quay Lại Trang Chủ button
- Project name + ID badge
- Cảnh #X / N counter
- ◀️ Cảnh Trước / Cảnh Sau ▶️

## Task 3: Button Micro-Descriptions ✅

ScreenB buttons now have gray helper text:
- 🪄 Auto-Detect: "AI tự động quét & bóc tách toàn bộ nhân vật..."
- Điểm+: "Click 1 điểm màu xanh trên thân nhân vật đối thủ."
- Điểm-: "Click điểm đỏ trên phông nền xung quanh để loại trừ."
- BBox: "Kéo ô hình chữ nhật bao trùm toàn thân nhân vật."
- Xem Mask: "Xem trước đường khoanh màu tím bao quanh nhân vật."
- Chấp Nhận: "Xác nhận chọn & AI tự động theo vết (tracking) qua các frame."

## Task 4: Auto Mask on Click ✅

- Point+ click → auto-trigger preview-mask API
- No need to manually click "Xem mask" button

## Verification

| Check | Result |
|-------|--------|
| pytest | 123 passed ✅ |
| ruff | ✅ Clean |
| tsc --noEmit | ✅ 0 errors |
| next build | ✅ OK |
