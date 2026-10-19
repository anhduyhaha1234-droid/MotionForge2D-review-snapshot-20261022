# 📋 MotionForge 2D — Milestone 1A.1 Report

**Từ:** Development Team  
**Đến:** Business Analyst (BA)  
**Ngày:** 30/07/2026  
**Chủ đề:** Milestone 1A.1 — UI Integration & Acceptance  
**Đề xuất:** `PARTIALLY ACCEPTED`

---

## 1. Tóm tắt điều khoản

Milestone 1A.1 yêu cầu biến frontend từ trạng thái compile/build thành một UI hoạt động thực tế trên trình duyệt, với các yêu cầu chính:

- Screen D phải hiển thị preview composite thật (không placeholder)
- Transform specification phải hỗ trợ 3 clip modes
- Playwright E2E test phải chạy được
- Canvas coordinate validation roundtrip ≤1px
- Job cancellation phải test được
- Restart persistence phải test được
- 9 screenshots từ ứng dụng thật
- 7 review documents

---

## 2. Kết quả nghiệm thu

### 2.1. Backend (Python)

| Tiêu chí | Kết quả | Evidence |
|----------|---------|----------|
| Tests | **67 passed** | `pytest tests/ -q` → 8.11s |
| Linting | **All checks passed** | `ruff check app/ tests/` |
| ClipMode schema | **3 modes hoạt động** | 4 schema tests + 2 API tests |
| Job cancellation | **running→cancelling→cancelled** | 4 cancel tests |
| Persistence | **project/object/gallery/config** | 4 persistence tests |
| API response format | **`status` key** (không phải `state`) | Verified via TestClient |

**Breakdown 67 tests:**
- 25 API endpoint tests
- 14 schema validation tests
- 7 motion calculation tests
- 7 integration tests
- 14 clip/cancel/persist tests (M1A.1 mới)

### 2.2. Frontend (TypeScript/React)

| Tiêu chí | Kết quả | Evidence |
|----------|---------|----------|
| Next.js build | ✅ Pass | `npx next build` |
| TypeScript strict | ✅ Pass | `npx tsc --noEmit` |
| Coordinate validation | **9/9 pass** | Playwright test, 338ms |
| Screen D preview | ✅ CompositeCanvas.tsx | Konva real preview |
| Preview modes | ✅ 4 modes | Ảnh gốc, Mask, Kết quả, So sánh |
| Vietnamese labels | ✅ | All UI labels tiếng Việt |

### 2.3. E2E API Workflow (TestClient)

Toàn bộ workflow đã chạy thành công qua API:

| Bước | Endpoint | Kết quả |
|------|----------|---------|
| 1. Tạo project | `POST /api/projects` | 201 Created |
| 2. Upload video | `POST /api/projects/{id}/video` | 200 OK |
| 3. Ingest | `POST /api/projects/{id}/ingest` | completed |
| 4. Lấy metadata | `GET /api/projects/{id}` | 640×360, 30fps, 180 frames |
| 5. Lấy frame | `GET /api/projects/{id}/frames/45` | 200 PNG |
| 6. Preview mask | `POST /api/projects/{id}/objects/preview-mask` | nonzero=89459 |
| 7. Tạo object | `POST /api/projects/{id}/objects` | 201 Created |
| 8. Propagate (SAM2) | `POST /api/projects/{id}/objects/{oid}/propagate` | 180/180 tracked |
| 9. Gallery | `GET /api/projects/{id}/objects/{oid}/gallery` | 20 crops |
| 10. Upload replacement | `POST /api/projects/{id}/objects/{oid}/replacement` | 200 OK |
| 11. Update settings | `PATCH /api/projects/{id}/objects/{oid}/replacement-settings` | clip_mode=intersection |
| 12. Preview render | `POST /api/projects/{id}/preview` | completed |
| 13. Final render | `POST /api/projects/{id}/render` | completed |

**Tổng thời gian E2E:** ~55 giây (bao gồm SAM2 propagation trên RTX 5070)

### 2.4. Output Video Validation

| Thuộc tính | Input | Output | Khớp |
|------------|------:|-------:|:----:|
| Resolution | 640×360 | 640×360 | ✅ |
| FPS | 30 | 30 | ✅ |
| Frames | 180 | 180 | ✅ |
| Duration | 6.0s | 6.0s | ✅ |
| Video codec | — | H.264 | ✅ |
| Audio codec | AAC 44100Hz | AAC 44100Hz | ✅ |

### 2.5. Playwright Tests

| Suite | Tests | Kết quả | Ghi chú |
|-------|:-----:|:-------:|---------|
| coordinate-validation | 9 | ✅ 9/9 pass | Roundtrip ≤1px tại mọi viewport |
| happy-path | 1 | ❌ Fail | Propagate 400 — mask file race condition |
| gpu-workflow | 1 | ⏭️ Not run | Cần GPU + live servers |

---

## 3. Những gì đã hoàn thành

### 3.1. Screen D — Real Composite Preview

**Trước:** Placeholder text "Preview sẽ hiển thị ở đây"  
**Sau:** Konva canvas composite thật với:

- Frame gốc làm background
- Mask overlay (xanh lá bán trong suốt)
- Replacement PNG positioned theo transform params
- Bounding box rectangle
- Centroid dot
- Anchor point marker
- Frame selector slider
- Controls: anchor X/Y, offset X/Y, scale, rotation, opacity, fit mode, clip mode
- 4 preview modes: Ảnh gốc, Mask, Kết quả, So sánh

**File:** `frontend/src/components/CompositeCanvas.tsx` + `ScreenD.tsx`

### 3.2. Transform Specification — Clip Modes

Cập nhật `docs/TRANSFORM_SPEC.md` với 3 clip modes mới:

| Clip Mode | Ý nghĩa | Use case |
|-----------|---------|----------|
| `asset_alpha` | Dùng alpha của PNG replacement | Mặc định, replacement khác shape |
| `original_mask` | Clip theo mask object cũ | Giữ đúng silhouette |
| `intersection` | Giao PNG alpha AND original mask | Conform partially |

Frontend và backend phải dùng cùng một computation.

### 3.3. Backend ClipMode Schema

```python
class ClipMode(str, Enum):
    ASSET_ALPHA = "asset_alpha"
    ORIGINAL_MASK = "original_mask"
    INTERSECTION = "intersection"

class ReplacementConfig(BaseModel):
    ...
    clip_mode: ClipMode = Field(default=ClipMode.ASSET_ALPHA, alias="clipMode")
```

API accepts `clip_mode` in request body, returns in response.

### 3.4. Job Cancellation Tests

4 tests xác minh:
1. Cancel running job → state: running → cancelling → cancelled
2. Cancel completed job → returns False
3. Cancel nonexistent job → 404
4. State transitions tracked correctly

**Mechanism:** `threading.Event` → worker checks `is_cancelled()` → returns early → job state updated to CANCELLED.

### 3.5. Restart Persistence Tests

4 tests xác minh:
1. Project JSON persists on disk
2. Object data in project JSON
3. Gallery manifest persists
4. Replacement config persists with clip_mode

### 3.6. API Response Fix

**Bug:** Backend trả `state` nhưng frontend expect `status`.  
**Fix:** Tạo `app/api/helpers.py` với `job_response()` helper, update tất cả routes.

### 3.7. Playwright Setup

- `playwright.config.ts` — Chromium, baseURL localhost:3000
- `e2e/coordinate-validation.spec.ts` — 9 tests, 9/9 pass
- `e2e/happy-path.spec.ts` — Full workflow test
- `e2e/gpu-workflow.spec.ts` — SAM2 GPU test (marker @slow)
- `e2e/fixtures/test-2s.mp4` — 2s 320×240 test video

### 3.8. Review Documents (7 files)

| File | Nội dung |
|------|----------|
| `MILESTONE_1A1_REVIEW_PACKAGE.md` | Sections A–J đầy đủ |
| `MILESTONE_1A1_TEST_EVIDENCE.md` | Git log, pytest, ruff, build output |
| `MILESTONE_1A1_UI_VALIDATION.md` | 5 screens, CompositeCanvas, preview modes |
| `MILESTONE_1A1_OUTPUT_VALIDATION.md` | Input vs output video comparison |
| `MILESTONE_1A1_PERSISTENCE_VALIDATION.md` | Project/object/gallery/config |
| `MILESTONE_1A1_CANCEL_VALIDATION.md` | State transitions, worker checks |
| `MILESTONE_1A1_FILE_INVENTORY.md` | 52 files with role descriptions |

---

## 4. Những gì CHƯA hoàn thành

### 4.1. Playwright Happy-Path E2E ❌

**Vấn đề:** Test chạy đến bước "Chấp nhận & Tách" nhưng propagate trả 400.

**Nguyên nhân gốc:** Frontend tạo object không gửi `mask_data`. Backend propagate endpoint cần `initial_mask.png`. Fallback tìm trong `debug/preview_mask_*.png` nhưng có race condition — preview mask được lưu cho frame 45 nhưng test dùng frame 0.

**Cách fix:** Frontend cần gửi `mask_data` (base64 mask PNG) khi gọi `createObject`, hoặc propagate endpoint cần accept mask preview response trực tiếp.

**Effort ước tính:** 2-4 giờ

### 4.2. Screenshots (1/9) ❌

Đã chụp: `01_project_start.png`  
Chưa chụp: 8 screenshots còn lại (cần chạy full workflow trên browser)

**Blocker:** Cần fix happy-path E2E trước để có thể navigate qua các screens.

### 4.3. GPU E2E Browser Test ⏭️

Chưa chạy test `gpu-workflow.spec.ts` với SAM2 thật trên browser.

### 4.4. Multi-Viewport UI Acceptance ⏭️

Chưa test tại 1440×900, 1366×768, 1024×768.

---

## 5. Benchmark

| Metric | Giá trị |
|--------|---------|
| SAM2 model load | ~3s |
| Mask preview (contour) | <1s |
| SAM2 propagation (180 frames) | ~60s |
| E2E API workflow | ~55s |
| Backend test suite | 8.11s |
| Frontend build | ~1.2s |
| Coordinate validation | 338ms |

---

## 6. License

| Dependency | Version | License | Purpose |
|-----------|---------|---------|---------|
| SAM 2.1 | sam2.1_hiera_large | Apache 2.0 | Segmentation |
| PyTorch | 2.11.0+cu128 | BSD-3 | Deep learning |
| FastAPI | latest | MIT | Backend API |
| Next.js | 16.2.12 | MIT | Frontend |
| Konva.js | latest | MIT | Canvas rendering |
| Playwright | latest | Apache 2.0 | E2E testing |

---

## 7. Hạn chế

1. **Single object only** — chưa hỗ trợ multi-object
2. **Single scene only** — chưa hỗ trợ multi-scene
3. **Static PNG only** — chưa có frame_sequence
4. **No background cleanup** — chỉ overlay, không xóa object gốc
5. **confidence luôn 1.0** — chưa có confidence metric thật
6. **SAM2 _C warning** — cosmetic, không ảnh hưởng chức năng
7. **Playwright happy-path fail** — cần fix frontend flow

---

## 8. Blocker

| # | Blocker | Impact | Fix |
|---|---------|--------|-----|
| 1 | Propagate mask race condition | Happy-path E2E fail | Frontend gửi mask_data khi createObject |

---

## 9. Files đã tạo/sửa

### Backend (app/)
| File | Action |
|------|--------|
| `app/api/helpers.py` | NEW — job_response() |
| `app/api/routes/jobs.py` | MODIFIED — use job_response() |
| `app/api/routes/projects.py` | MODIFIED — job_response(), mask fallback |
| `app/schemas/__init__.py` | MODIFIED — ClipMode enum |
| `tests/test_clip_cancel_persist.py` | NEW — 14 tests |

### Frontend (frontend/src/)
| File | Action |
|------|--------|
| `components/CompositeCanvas.tsx` | NEW — Konva composite preview |
| `components/ScreenD.tsx` | REWRITTEN — real preview |
| `stores/project.ts` | MODIFIED — previewMode, frameMotion |
| `lib/api.ts` | MODIFIED — mask/crop/replacement URLs |

### E2E (frontend/e2e/)
| File | Action |
|------|--------|
| `playwright.config.ts` | NEW |
| `coordinate-validation.spec.ts` | NEW — 9 tests |
| `happy-path.spec.ts` | NEW — full workflow |
| `gpu-workflow.spec.ts` | NEW — SAM2 GPU |
| `fixtures/test-2s.mp4` | NEW — test video |

### Docs (docs/)
| File | Action |
|------|--------|
| `TRANSFORM_SPEC.md` | MODIFIED — clip mode section |
| `MILESTONES.md` | MODIFIED — roadmap M0→M4 |
| `MILESTONE_1A1_REVIEW_PACKAGE.md` | NEW |
| `MILESTONE_1A1_TEST_EVIDENCE.md` | NEW |
| `MILESTONE_1A1_UI_VALIDATION.md` | NEW |
| `MILESTONE_1A1_OUTPUT_VALIDATION.md` | NEW |
| `MILESTONE_1A1_PERSISTENCE_VALIDATION.md` | NEW |
| `MILESTONE_1A1_CANCEL_VALIDATION.md` | NEW |
| `MILESTONE_1A1_FILE_INVENTORY.md` | NEW |

---

## 10. Cách chạy

```bash
# Backend
cd C:\Users\Admin\MotionForge2D
python -m pytest tests/ -v          # 67 tests
python -m ruff check app/ tests/    # lint
python -m uvicorn app.main:app      # start API

# Frontend
cd frontend
npm run dev                          # start dev server
npx next build                       # production build
npx tsc --noEmit                     # type check

# Playwright
npx playwright test coordinate-validation   # 9 tests, 338ms
npx playwright test happy-path              # full E2E (needs backend)
npx playwright test gpu-workflow --grep @slow  # GPU test
```

---

## 11. Đề xuất cho Milestone tiếp theo

### Ưu tiên 1: Fix Playwright Happy-Path (1A.1 completion)

**Vấn đề:** Frontend tạo object không gửi mask_data → propagate 400  
**Fix:** 
- Option A: Frontend gửi `mask_data` (base64 từ preview response) khi gọi `createObject`
- Option B: Backend propagate accept mask preview response trực tiếp qua request body

**Effort:** 2-4 giờ

### Ưu tiên 2: Milestone 1B — Frame Sequence & Keyframe Replacement

**Scope:**
- `frame_sequence` replacement mode
- `keyframe_assets` replacement mode  
- Timeline với keyframe markers
- Interpolation giữa keyframes
- Per-frame asset assignment UI

**Effort ước tính:** 2-3 tuần

### Ưu tiên 3: Milestone 1C — Background Cleaning

**Scope:**
- Clean plate từ frame khác
- User-uploaded clean background
- Local inpainting model
- Preview vs final quality controls

### Lộ trình đề xuất

```
M1A.1 (hiện tại) ──fix──→ M1A.1 COMPLETE
                              │
                              ▼
M1B: Frame Sequence (2-3 tuần)
                              │
                              ▼
M1C: Background Cleaning (2 tuần)
                              │
                              ▼
M2: Multi-Object & Multi-Scene (3 tuần)
```

---

## 12. Quyết định cần BA

1. **Duyệt PARTIALLY ACCEPTED** cho M1A.1 với điều kiện fix happy-path trong sprint tiếp?
2. **Ưu tiên M1B hay M1C** cho milestone tiếp theo?
3. **Có cần thêm screenshots** trước khi duyệt, hay chấp nhận với evidence API-level?

---

**Commit hashes:**
```
2d3fbae M1A.1: API status fix, 7 review docs, Playwright improvements
df476e9 M1A.1: Backend — clip modes, cancel tests, persistence tests, roadmap
```

**Repository:** `C:\Users\Admin\MotionForge2D`  
**Branch:** main  
