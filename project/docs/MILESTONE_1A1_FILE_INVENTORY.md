# Milestone 1A.1 — File Inventory

**MotionForge 2D**
**Date:** 2026-07-30
**Commit:** df476e9

---

## Backend — `app/`

| File | Role |
|---|---|
| `app/__init__.py` | Package init |
| `app/main.py` | FastAPI application entry point |
| `app/api/__init__.py` | API package init |
| `app/api/routes.py` | API route handlers (projects, objects, frames, render, jobs) |
| `app/models/__init__.py` | Models package init |
| `app/models/schemas.py` | Pydantic v2 schemas: `ClipMode` enum, `ReplacementConfig`, `Project`, `Object`, etc. |
| `app/core/__init__.py` | Core package init |
| `app/core/config.py` | Application configuration |
| `app/core/project_manager.py` | Project CRUD, persistence to JSON |
| `app/core/job_manager.py` | Job queue, cancel flag (`threading.Event`), state machine |
| `app/core/video_processor.py` | Video ingest, frame extraction, FFmpeg wrapper |
| `app/core/mask_engine.py` | SAM2 mask generation and propagation |
| `app/core/render_engine.py` | Composite render pipeline (frame + mask + replacement) |
| `app/core/gallery.py` | Gallery crop generation from mask regions |

---

## Frontend — `frontend/src/`

| File | Role |
|---|---|
| `frontend/src/app/layout.tsx` | Next.js root layout |
| `frontend/src/app/page.tsx` | Root page (router entry) |
| `frontend/src/components/ScreenA.tsx` | Project start / create screen |
| `frontend/src/components/ScreenB.tsx` | Video upload & ingest screen |
| `frontend/src/components/ScreenC.tsx` | Object selection & SAM2 masking screen |
| `frontend/src/components/ScreenD.tsx` | Replacement upload, settings, preview (rewritten in M1A.1) |
| `frontend/src/components/ScreenE.tsx` | Render & export screen |
| `frontend/src/components/CompositeCanvas.tsx` | Konva-based real-time composite canvas preview (new in M1A.1) |
| `frontend/src/stores/project.ts` | Zustand store: project state, `previewMode`, `frameMotion` |
| `frontend/src/lib/api.ts` | API client: `getMaskImageUrl`, `getCropImageUrl`, `getReplacementImageUrl` |

---

## Tests

| File | Role |
|---|---|
| `app/tests/__init__.py` | Test package init |
| `app/tests/conftest.py` | pytest fixtures (TestClient, temp dirs, sample video) |
| `app/tests/test_api.py` | API endpoint tests (25 tests) |
| `app/tests/test_schemas.py` | Pydantic schema validation tests (14 tests) |
| `app/tests/test_motion.py` | Motion / transform unit tests (7 tests) |
| `app/tests/test_integration.py` | Integration tests (7 tests) |
| `app/tests/test_clip_cancel_persist.py` | Clip modes, cancel, persistence tests (14 tests, new in M1A.1) |
| `frontend/tests/happy-path.spec.ts` | Playwright E2E: happy path workflow (new in M1A.1) |
| `frontend/tests/gpu-workflow.spec.ts` | Playwright E2E: GPU-accelerated workflow (new in M1A.1) |
| `frontend/tests/coordinate-validation.spec.ts` | Playwright E2E: coordinate accuracy (9/9 pass, new in M1A.1) |

---

## Documentation

| File | Role |
|---|---|
| `docs/MILESTONES.md` | Roadmap: M0→M4, M1A.1 marked CURRENT (updated in M1A.1) |
| `docs/TRANSFORM_SPEC.md` | Transform specification, clip mode section added (updated in M1A.1) |
| `docs/MILESTONE_1A1_REVIEW_PACKAGE.md` | This review package |
| `docs/MILESTONE_1A1_TEST_EVIDENCE.md` | Test output evidence |
| `docs/MILESTONE_1A1_UI_VALIDATION.md` | UI screen and component validation |
| `docs/MILESTONE_1A1_OUTPUT_VALIDATION.md` | Output video quality validation |
| `docs/MILESTONE_1A1_PERSISTENCE_VALIDATION.md` | Persistence verification |
| `docs/MILESTONE_1A1_CANCEL_VALIDATION.md` | Cancel mechanism verification |
| `docs/MILESTONE_1A1_FILE_INVENTORY.md` | This file |
| `docs/screenshots/milestone_1a/01_project_start.png` | Screenshot of Screen A |

---

## Configuration & Build

| File | Role |
|---|---|
| `pyproject.toml` | Python project config, dependencies |
| `requirements.txt` | Python pinned dependencies |
| `frontend/package.json` | Node.js dependencies and scripts |
| `frontend/tsconfig.json` | TypeScript configuration |
| `frontend/next.config.js` | Next.js configuration |
| `frontend/playwright.config.ts` | Playwright test configuration (new in M1A.1) |
| `.gitignore` | Git ignore rules |
| `README.md` | Project README |

---

## Summary

| Category | Count |
|---|---|
| Backend source files | 14 |
| Frontend source files | 10 |
| Test files | 10 |
| Documentation files | 10 |
| Config / build files | 8 |
| **Total** | **52** |
