# Master Performance & Auto-Segment Upgrade

**Date:** 2026-08-02  
**Status:** 🔄 In Progress

---

## Task 1: Delete Project & Hard Drive Purger ✅

- `DELETE /api/projects/{project_id}` — xóa project + shutil.rmtree
- Frontend: 🗑️ button on recent projects + ChannelDashboard
- Confirmation dialog before delete

## Task 2: Auto-Detect All Objects Engine ✅

- `POST /api/projects/{id}/auto-segment-objects` — OpenCV contour detection
- Downsample 0.5x for speed
- Returns bounding boxes sorted by area
- Frontend: "🪄 Tự Động Bắt Tất Cả Nhân Vật" button on ScreenB

## Task 3: Mask Preview Acceleration ✅

- Downsample 1/2 resolution for preview-mask
- Auto-trigger mask preview on point click (no manual button)
- Loading spinner on "Chấp nhận & Tách" button

## Task 4: System-Wide Performance ✅

- cv2.setNumThreads(8) in main.py
- Poll interval: 1000ms → 300ms
- maxAttempts: 300 → 1000

## Tests

- test_delete_and_autosegment.py — 3 tests

## Verification

| Check | Result |
|-------|--------|
| pytest | ✅ |
| ruff | ✅ |
| tsc --noEmit | ✅ |
| next build | ✅ |
