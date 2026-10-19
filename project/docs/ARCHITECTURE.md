# MotionForge 2D — Architecture

## Overview

MotionForge 2D is a local-first application for extracting motion from 2D animation
videos and replacing tracked objects with new assets. The architecture follows a
service-oriented design with clear separation of concerns.

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Video     │  │  Canvas   │  │ Timeline │  │ Property Panel│  │
│  │  Player    │  │  (Konva)  │  │          │  │               │  │
│  └───────────┘  └───────────┘  └──────────┘  └───────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                    API Layer (FastAPI REST)                       │
├──────────────────────────────────────────────────────────────────┤
│                    Backend Services (Python)                      │
│  ┌────────────┐  ┌───────────┐  ┌───────────┐  ┌────────────┐  │
│  │  Project   │  │  Video    │  │  Scene    │  │  Frame     │  │
│  │  Service   │  │  Probe    │  │  Detect   │  │  Extract   │  │
│  └────────────┘  └───────────┘  └───────────┘  └────────────┘  │
│  ┌────────────┐  ┌───────────┐  ┌───────────┐  ┌────────────┐  │
│  │  Segment   │  │  Motion   │  │ Composite │  │  Render    │  │
│  │  Adapter   │  │  Extract  │  │  Service  │  │  Service   │  │
│  └────────────┘  └───────────┘  └───────────┘  └────────────┘  │
│  ┌────────────┐  ┌───────────┐                                 │
│  │  Job       │  │  Tracking │                                 │
│  │  Service   │  │  Service  │                                 │
│  └────────────┘  └───────────┘                                 │
├──────────────────────────────────────────────────────────────────┤
│                    Storage (SQLite + Filesystem)                 │
│  ┌────────────┐  ┌───────────┐  ┌───────────┐                  │
│  │  Project   │  │  Frames   │  │  Renders  │                  │
│  │  JSON      │  │  (FS)     │  │  (FS)     │                  │
│  └────────────┘  └───────────┘  └───────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

| Module | Responsibility | Authority |
|--------|---------------|-----------|
| **Project Service** | CRUD for project state, serialization | Project data |
| **Video Probe** | FFmpeg metadata extraction | Video info |
| **Scene Detection** | PySceneDetect scene boundaries | Scene list |
| **Frame Extraction** | FFmpeg frame extraction per scene | Frame files |
| **Segmentation Adapter** | Abstract interface for mask generation | Masks |
| **Tracking Service** | Multi-frame object propagation | Tracks |
| **Motion Extraction** | Compute motion vectors from masks | Motion data |
| **Compositing** | Overlay replacement images | Composited frames |
| **Render Service** | FFmpeg reassembly with audio | Final video |
| **Job Service** | Background task management | Job status |

## Key Design Decisions

### Adapter Pattern for AI Models

The `SegmentationAdapter` abstract class decouples the pipeline from any
specific AI model. Current implementations:
- `SAM2Adapter` — Meta's SAM 2.1 (GPU required)
- `SimpleContourAdapter` — OpenCV-based fallback (CPU only)

### Motion Data Pipeline

```
Mask Sequence → Centroid/BBox → Scale/Rotation → Smoothing → JSON Export
```

Each frame's mask is analyzed for:
1. **Centroid** — center of mass from moments
2. **Bounding Box** — axis-aligned bounding rect
3. **Scale** — relative to reference frame
4. **Rotation** — from minimum area rect angle
5. **Opacity** — fill ratio of bbox area
6. **Visibility** — based on mask area threshold

### Project JSON Format

Version-controlled, human-readable project file containing:
- Video metadata and scene boundaries
- All tracked objects with selections
- Per-frame motion data
- Replacement image paths

### File System Layout

```
output/
├── scenes/          # Scene-split video segments
├── frames/          # Extracted frame images per scene
├── masks/           # Binary masks per scene
├── renders/         # Composited frames and final videos
├── debug/           # Mask overlays and debug visualizations
├── audio/           # Extracted audio tracks
├── project.json     # Full project state
├── motion_data.json # Motion vectors
└── benchmark.json   # Performance metrics
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.11 | Core runtime |
| API | FastAPI + Pydantic v2 | REST API + validation |
| DB | SQLAlchemy + SQLite | Persistent storage |
| Video | FFmpeg + ffprobe | Video processing |
| Vision | OpenCV | Image processing |
| AI | SAM 2.1 (PyTorch) | Object segmentation |
| Scenes | PySceneDetect | Scene boundary detection |
| Frontend | Next.js + TypeScript | Web UI |
| Canvas | Konva.js | Video annotation |
| State | Zustand | Client state |
| Style | Tailwind CSS | UI styling |
