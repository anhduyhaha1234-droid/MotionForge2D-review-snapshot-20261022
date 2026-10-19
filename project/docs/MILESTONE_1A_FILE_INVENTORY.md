# Milestone 1A — File Inventory

**Dự án:** MotionForge 2D
**Milestone:** 1A — Object Extraction Review UI

---

## Backend (`app/`)

| File | Vai trò |
|------|---------|
| `app/__init__.py` | Package init |
| `app/main.py` | Entry point — tạo FastAPI app, mount routes |
| `app/config.py` | Cấu hình (paths, SAM2 model, FFmpeg settings) |
| `app/spike_runner.py` | Spike test runner (M0.5) |
| **API Layer** | |
| `app/api/__init__.py` | Package init |
| `app/api/app.py` | FastAPI app factory, CORS, router mount |
| `app/api/deps.py` | Dependency injection (project service, job service) |
| `app/api/routes/__init__.py` | Package init |
| `app/api/routes/projects.py` | Project endpoints (CRUD, video, ingest, scenes, frames, objects, render) |
| `app/api/routes/jobs.py` | Job endpoints (status, cancel) |
| `app/api/routes/frames.py` | Frame serving endpoint |
| **Schemas** | |
| `app/schemas/__init__.py` | Pydantic models — Project, TrackedObject, ReplacementConfig, JobInfo, etc. |
| **Services** | |
| `app/services/__init__.py` | Package init |
| `app/services/video_probe.py` | FFprobe wrapper — trích metadata video (resolution, fps, duration, frames) |
| `app/services/ffmpeg_utils.py` | FFmpeg utility functions (frame extraction, video encoding) |
| `app/services/frame_extraction.py` | Trích xuất frame từ video theo index |
| `app/services/scene_detection.py` | Phát hiện scene boundary (PySceneDetect) |
| `app/services/motion_extraction.py` | Optical flow / motion tracking |
| `app/services/compositing.py` | Compositing — overlay replacement lên frame gốc |
| `app/services/render.py` | Render pipeline — encode frame sequence thành video |
| `app/services/project_service.py` | Project CRUD operations trên disk |
| **Adapters** | |
| `app/adapters/__init__.py` | Package init |
| `app/adapters/segmentation.py` | SAM2 adapter — mask prediction, propagation |
| **Workflow** | |
| `app/workflow/__init__.py` | Package init |
| `app/workflow/job_service.py` | Job queue manager — tạo, poll, cancel async jobs |
| `app/workflow/project_workflow.py` | Project lifecycle orchestration |
| `app/workflow/ingest_service.py` | Ingest pipeline — probe + extract frames + detect scenes |
| `app/workflow/segmentation_service.py` | Segmentation pipeline — SAM2 mask generation |
| `app/workflow/object_extraction_service.py` | Object extraction — crop gallery, tracking |
| `app/workflow/replacement_service.py` | Replacement asset management |
| `app/workflow/render_service.py` | Render workflow — preview + final render |

---

## Frontend (`frontend/src/`)

| File | Vai trò |
|------|---------|
| **App** | |
| `src/app/layout.tsx` | Root layout — metadata, font, providers |
| `src/app/page.tsx` | Main page — screen routing theo Zustand state |
| `src/app/providers.tsx` | React providers (Zustand store) |
| `src/app/globals.css` | Global styles (Tailwind CSS) |
| `src/app/favicon.ico` | Favicon |
| **Components** | |
| `src/components/ScreenA.tsx` | Project Start — upload video + ingest |
| `src/components/ScreenB.tsx` | Object Selection — canvas point/negative/bbox + SAM2 preview |
| `src/components/ScreenC.tsx` | Extraction Review — gallery crops + tracking status |
| `src/components/ScreenD.tsx` | Replacement Controls — anchor, offset, scale, rotation, opacity, fit |
| `src/components/ScreenE.tsx` | Preview & Render — video player + render controls |
| **Lib** | |
| `src/lib/api.ts` | API client — typed fetch wrappers cho tất cả 18 endpoints |
| `src/lib/coordinates.ts` | Coordinate transform — canvas ↔ video frame mapping |
| **Stores** | |
| `src/stores/project.ts` | Zustand store — project state, screen navigation, object data |

---

## Thống kê

| | Files |
|---|------:|
| Backend Python | 22 |
| Frontend TypeScript | 13 |
| **Tổng** | **35** |
