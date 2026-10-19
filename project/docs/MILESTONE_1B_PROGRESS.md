# Milestone 1B — Progress Report

**Ngày:** 31/07/2026  
**Trạng thái:** ✅ Complete  
**Commit:** *(pending)*

---

## 1. Feature 1: Backend Scene Chunking & Synced Audio Engine ✅

### 1.1 Scene Chunking Service
- ✅ `app/workflow/scene_chunking_service.py` — PySceneDetect + FFmpeg audio extraction
- ✅ Mỗi scene có file audio riêng `scene_000.aac`, `scene_001.aac`...
- ✅ Audio được cắt chính xác theo timestamp video gốc (100% sync)
- ✅ `_check_audio()` — kiểm tra video có audio stream
- ✅ `_extract_audio()` — FFmpeg copy codec (no re-encode)

### 1.2 Scene Stitching Service
- ✅ `app/workflow/scene_stitch_service.py` — concat rendered scenes + re-mux audio
- ✅ `stitch_scenes()` — FFmpeg concat demuxer
- ✅ `stitch_with_audio()` — merge video + per-scene audio trước khi concat

### 1.3 Schema Extensions
- ✅ `SceneStatus` enum: PENDING / DRAFT / APPROVED
- ✅ `SceneDetail` model với status, audio_path, notes
- ✅ `ProjectData.scene_details` field
- ✅ `_save_project()` method trong ProjectWorkflowService

### 1.4 API Endpoints (6 mới)
- ✅ `POST /api/projects/{id}/scenes/chunk` — cắt video + extract audio
- ✅ `GET /api/projects/{id}/scenes/details` — danh sách scenes + status
- ✅ `PATCH /api/projects/{id}/scenes/{id}/status` — cập nhật trạng thái
- ✅ `GET /api/projects/{id}/scenes/{id}/audio` — file audio scene
- ✅ `POST /api/projects/{id}/scenes/stitch` — ghép video hoàn chỉnh

---

## 2. Feature 2: Frontend Step-by-Step Approval UI ✅

### 2.1 SceneSelector Component
- ✅ `frontend/src/components/SceneSelector.tsx`
- ✅ Hiển thị danh sách cảnh với badge màu sắc
- ✅ 🟢 Đã duyệt | 🟡 Đang sửa | ⚪ Chưa làm
- ✅ Nút "🔄 Cắt cảnh" để trigger chunk
- ✅ Nút "✅ Duyệt" trên mỗi scene
- ✅ Auto-advance sang cảnh tiếp theo sau khi duyệt
- ✅ Counter: "{approved}/{total} đã duyệt"

### 2.2 ScenePreview Component
- ✅ `frontend/src/components/ScenePreview.tsx`
- ✅ Audio player nghe thử giọng nói gốc
- ✅ Hiển thị tên cảnh đang preview
- ✅ Auto-load audio khi chuyển cảnh

### 2.3 Screen D Updates
- ✅ Thêm scene sidebar bên trái (SceneSelector + ScenePreview)
- ✅ Nút "✅ Duyệt phân cảnh này"
- ✅ Layout: Scene Panel | Canvas | Controls

### 2.4 AssemblyModal
- ✅ `frontend/src/components/AssemblyModal.tsx`
- ✅ Modal tổng hợp với danh sách cảnh + status
- ✅ Nút "🎬 Đồng ý ghép Video hoàn chỉnh"
- ✅ Chỉ enabled khi tất cả cảnh đã APPROVED
- ✅ Hiển thị kết quả sau khi ghép

### 2.5 API Client & Store
- ✅ `SceneDetail` interface trong api.ts
- ✅ 5 API methods: chunkScenes, getSceneDetails, updateSceneStatus, getSceneAudioUrl, stitchScenes
- ✅ Zustand store: scenes, activeSceneId, setScenes, setActiveSceneId

---

## 3. Testing ✅

### 3.1 Backend Tests
- ✅ `tests/test_scene_chunk_stitch.py` — 7 tests
- ✅ Test chunk trả về scenes đúng
- ✅ Test scene IDs sequential
- ✅ Test status = PENDING
- ✅ Test audio extracted
- ✅ Test duration positive
- ✅ Test stitch no videos raises
- ✅ Test stitch empty list raises
- ✅ **74 tests pass** (67 existing + 7 new)

### 3.2 Frontend Checks
- ✅ `npx tsc --noEmit` — 0 errors
- ✅ `npx next build` — compiled in ~1.3s

---

## 4. Files Created/Modified

### Backend (6 files)
| File | Action |
|------|--------|
| `app/schemas/__init__.py` | MODIFIED — SceneStatus, SceneDetail, ProjectData.scene_details |
| `app/workflow/scene_chunking_service.py` | NEW |
| `app/workflow/scene_stitch_service.py` | NEW |
| `app/workflow/project_workflow.py` | MODIFIED — _save_project() |
| `app/api/routes/projects.py` | MODIFIED — 5 new endpoints |
| `tests/test_scene_chunk_stitch.py` | NEW — 7 tests |

### Frontend (6 files)
| File | Action |
|------|--------|
| `frontend/src/lib/api.ts` | MODIFIED — SceneDetail + 5 API methods |
| `frontend/src/stores/project.ts` | MODIFIED — scenes, activeSceneId |
| `frontend/src/components/SceneSelector.tsx` | NEW |
| `frontend/src/components/ScenePreview.tsx` | NEW |
| `frontend/src/components/AssemblyModal.tsx` | NEW |
| `frontend/src/components/ScreenD.tsx` | MODIFIED — scene sidebar |
| `frontend/src/app/page.tsx` | MODIFIED — assembly button |

### Docs (1 file)
| File | Action |
|------|--------|
| `docs/MILESTONE_1B_PROGRESS.md` | NEW — this report |

---

## 5. Benchmark

| Metric | Giá trị |
|--------|---------|
| Backend test suite | 8.87s (74 tests) |
| Frontend build | ~1.3s |
| TypeScript check | ~1.8s |

---

## 6. Verification Commands

```bash
# Backend
python -m ruff check app/ tests/     # All checks passed
python -m pytest tests/ -q           # 74 passed

# Frontend
cd frontend && npx tsc --noEmit      # OK
cd frontend && npx next build        # OK
```
