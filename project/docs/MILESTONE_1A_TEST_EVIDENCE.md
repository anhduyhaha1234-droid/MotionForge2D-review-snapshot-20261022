# Milestone 1A — Test Evidence

**Dự án:** MotionForge 2D
**Milestone:** 1A — Object Extraction Review UI
**Ngày:** 2026-07-30
**Commit:** `7e9faf8` M1A: Bug fixes

---

## 1. Git Status

```
8 commits on master
Latest: 7e9faf8 M1A: Bug fixes
Working tree: clean
```

---

## 2. Backend Tests

```bash
$ python -m pytest -q
53 passed in 2.66s
```

| Category | Count |
|----------|------:|
| API tests | 25 |
| Schema tests | 14 |
| Motion tests | 7 |
| Integration tests | 7 |
| **Total** | **53** |

---

## 3. Linting (Ruff)

```bash
$ ruff check .
All checks passed!
```

---

## 4. Frontend Build

```bash
$ cd frontend && npm run build
Next.js production build success
```

No TypeScript errors. No build warnings.

---

## 5. E2E API Workflow (TestClient)

Full end-to-end workflow verified with Python `TestClient` against the FastAPI app. All 15 steps completed successfully.

```
[1]  Create project:         POST /api/projects               → 201  id=2eb9dffdc410
[2]  Upload video:           POST /api/projects/{id}/video    → 200
[3]  Ingest:                 POST /api/projects/{id}/ingest   → 200  completed
                             fixture_b, 640×360, 30fps, 180 frames
[4]  Metadata:               GET  /api/projects/{id}          → 200  640×360 30fps 180frames
[5]  Scenes:                 GET  /api/projects/{id}/scenes   → 200  1 scene
[6]  Frame 45:               GET  /api/projects/{id}/frames/45 → 200 image/png
[7]  Preview mask (SAM2):    POST /api/.../preview-mask       → 200  nonzero=89,459
[8]  Create object:          POST /api/.../objects            → 201  oid=c38bbad8
[9]  Propagate (SAM2):       POST /api/.../propagate          → 200  completed, ~60s
[10] Motion tracking:        GET  /api/.../objects/{oid}      → 200  180/180 tracked (100%)
[11] Gallery:                GET  /api/.../gallery            → 200  20 crops + thumbnail
[12] Upload replacement:     POST /api/.../replacement        → 200
[13] Settings update:        PATCH /api/.../replacement-settings → 200
[14] Preview render:         POST /api/.../preview            → 200  completed
[15] Final render:           POST /api/.../render             → 200  completed
```

**Total E2E time: 63.7 seconds**

---

## 6. Environment

| Component | Version |
|-----------|---------|
| Python | 3.11.9 |
| Node.js | 26.4.0 |
| npm | 11.17.0 |
| PyTorch | 2.11.0+cu128 |
| CUDA | 12.8 |
| GPU | RTX 5070 12GB |
| FFmpeg | 8.1.2 |
| SAM2 | sam2.1_hiera_large (Apache 2.0) |
| OS | Windows 10 MINGW64 |

---

## 7. Output Artifacts

- `projects/2eb9dffdc410/` — E2E project with all outputs (video, frames, masks, crops, render)
- `artifacts/milestone_1a/openapi.json` — OpenAPI spec export (18 endpoints)
- `docs/screenshots/milestone_1a/01_project_start.png` — UI screenshot
- `docs/TRANSFORM_SPEC.md` — Replacement transform specification
