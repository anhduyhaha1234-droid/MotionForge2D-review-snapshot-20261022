# Milestone 1C — Progress Report

**Ngày:** 31/07/2026  
**Trạng thái:** ✅ Complete  
**Commit:** *(pending)*

---

## 1. Feature 1: Background Inpainting & Mask Dilation ✅

### 1.1 Inpainting Service
- ✅ `app/services/inpainting_service.py`
- ✅ `dilate_mask()` — morphological dilation (kernel 3-8px, configurable iterations)
- ✅ `inpaint_frame()` — Telea + Navier-Stokes algorithms
- ✅ `process_frame()` — full pipeline: dilate → inpaint
- ✅ `process_scene_frames()` — batch processing with file I/O

### 1.2 Tests (6 new)
- ✅ `tests/test_inpainting.py`
- ✅ Test dilation increases mask area
- ✅ Test kernel size effect (3 vs 7)
- ✅ Test Telea inpainting output shape/dtype
- ✅ Test Navier-Stokes inpainting output shape
- ✅ Test full pipeline (dilate + inpaint)
- ✅ Test frame sequence cycling concept

---

## 2. Feature 2: Animated PNG Sequence Replacement ✅

### 2.1 Schema
- ✅ `ReplacementConfig.frame_sequence_dir` field (alias: frameSequenceDir)
- ✅ `ReplacementConfig.frame_sequence_fps` field (alias: frameSequenceFps)

### 2.2 Render Engine
- ✅ FRAME_SEQUENCE mode in `app/workflow/render_service.py`
- ✅ `_get_sequence_frame()` helper — loads PNG from sequence dir, cycles by frame_index
- ✅ Frame cycling (index % total_frames)

### 2.3 Frontend
- ✅ API types updated: `mode: "none" | "static_asset" | "frame_sequence"`
- ✅ `frameSequenceDir` and `frameSequenceFps` fields added
- ✅ `CompositeCanvas.tsx` — `sequenceFrameUrl` prop + image loading
- ✅ `ScreenD.tsx` — mode selector with frame_sequence option
- ✅ Sequence directory + FPS override controls

---

## 3. Feature 3: Bulk Character Mapping UI ✅

### 3.1 Backend
- ✅ `POST /api/projects/{id}/objects/{oid}/apply-bulk` endpoint
- ✅ `BulkMappingRequest` model (object_id, scene_ids)
- ✅ Applies replacement config to all objects in target scenes

### 3.2 Frontend
- ✅ `applyBulkMapping()` API method in api.ts
- ✅ `ScreenD.tsx` — "Áp dụng hàng loạt" section
- ✅ Purple button: "Áp dụng cho tất cả cảnh"
- ✅ Success feedback with applied count

---

## 4. Testing & Verification ✅

| Check | Result |
|-------|--------|
| `pytest tests/ -q` | **80 passed** (74 + 6 new) |
| `ruff check app/ tests/` | ✅ All checks passed |
| `npx tsc --noEmit` | ✅ 0 errors |
| `npx next build` | ✅ compiled 1334ms |

---

## 5. Files Created/Modified

### New Files (2)
| File | Description |
|------|-------------|
| `app/services/inpainting_service.py` | InpaintingService with dilate + inpaint + batch |
| `tests/test_inpainting.py` | 6 tests for inpainting and frame sequence |

### Modified Files (6)
| File | Changes |
|------|---------|
| `app/schemas/__init__.py` | frame_sequence_dir, frame_sequence_fps fields |
| `app/api/routes/projects.py` | BulkMappingRequest + apply-bulk endpoint |
| `app/workflow/render_service.py` | FRAME_SEQUENCE support + _get_sequence_frame() |
| `frontend/src/lib/api.ts` | frame_sequence mode + bulk/inpaint methods |
| `frontend/src/components/CompositeCanvas.tsx` | sequenceFrameUrl prop |
| `frontend/src/components/ScreenD.tsx` | Mode selector + bulk mapping UI |

---

## 6. Benchmark

| Metric | Value |
|--------|-------|
| Backend test suite | 8.75s (80 tests) |
| Frontend build | ~1.3s |
| TypeScript check | ~1.8s |

---

## 7. Verification Commands

```bash
python -m pytest tests/ -q           # 80 passed
python -m ruff check app/ tests/     # All checks passed
cd frontend && npx tsc --noEmit      # OK
cd frontend && npx next build        # OK
```
