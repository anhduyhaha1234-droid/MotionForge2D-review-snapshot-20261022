# Milestone 0 — File Inventory

Ngày tạo: 2026-07-29

---

## 1. Repository Tree (filtered)

```
MotionForge2D/
├── app/
│   ├── __init__.py                    (83 B)
│   ├── config.py                      (1,642 B)
│   ├── spike_runner.py                (17,245 B)
│   ├── adapters/
│   │   ├── __init__.py                (24 B)
│   │   └── segmentation.py            (11,170 B)
│   ├── schemas/
│   │   └── __init__.py                (4,817 B)
│   └── services/
│       ├── __init__.py                (24 B)
│       ├── compositing.py             (6,508 B)
│       ├── frame_extraction.py        (2,518 B)
│       ├── motion_extraction.py       (6,483 B)
│       ├── project_service.py         (2,838 B)
│       ├── render.py                  (4,058 B)
│       ├── scene_detection.py         (2,324 B)
│       └── video_probe.py            (3,895 B)
├── tests/
│   ├── conftest.py                    (2,031 B)
│   ├── test_schema.py                 (9,953 B)
│   └── test_integration.py            (7,629 B)
├── scripts/
│   ├── setup.sh                       (2,317 B)
│   ├── download_models.sh             (1,628 B)
│   └── run_spike.sh                   (2,844 B)
├── docs/
│   ├── ARCHITECTURE.md                (6,980 B)
│   ├── MILESTONES.md                  (4,065 B)
│   ├── SPIKE_REPORT.md                (8,446 B)
│   ├── MILESTONE_0_REVIEW_PACKAGE.md  (sẽ tạo)
│   ├── MILESTONE_0_FILE_INVENTORY.md  (file này)
│   ├── MILESTONE_0_TEST_EVIDENCE.md   (đã tạo)
│   └── MILESTONE_0_OUTPUT_VALIDATION.md (sẽ tạo)
├── examples/
│   ├── example_project.json           (2,128 B)
│   ├── replacement.png                (800 B)
│   ├── test_video.mp4                 (50,755 B)
│   └── test_video_noaudio.mp4         (21,681 B) ← STRAY
├── output/                            (~12 MB tổng)
│   ├── project.json                   (42,018 B)
│   ├── motion_data.json               (31,707 B)
│   ├── benchmark.json                 (442 B)
│   ├── audio/original_audio.aac       (27,217 B)
│   ├── frames/scene_0/               (90 PNG files)
│   ├── masks/scene_0/                (10 PNG files, sampled)
│   ├── debug/                         (12 PNG overlay files)
│   └── renders/
│       ├── scene_0_composited/       (90 PNG files)
│       └── scene_0_output.mp4        (54,259 B)
├── pyproject.toml                     (1,370 B)
├── README.md                          (5,032 B)
├── THIRD_PARTY.md                     (2,778 B)
├── models_checkpoints/                (empty)
├── .mypy_cache/                       ← cache, không commit
├── .ruff_cache/                       ← cache, không commit
└── .pytest_cache/                     ← cache, không commit
```

**Không có .gitignore** — rủi ro commit nhầm cache/output.

---

## 2. Module Inventory

| File | Class / Function chính | Trách nhiệm | Dependency chính | Được gọi bởi spike? | Test coverage |
|------|----------------------|-------------|-----------------|---------------------|---------------|
| `app/config.py` | `AppConfig` dataclass | Cấu hình global (paths, SAM2 settings) | os, pathlib, dataclasses | ✅ spike_runner | ❌ Không có test riêng |
| `app/schemas/__init__.py` | `VideoMetadata`, `SceneInfo`, `SelectionInput`, `FrameMotion`, `SceneMotion`, `ProjectData`, `TrackedObject`, `JobInfo` | Data model definitions | pydantic | ✅ toàn bộ | ✅ test_schema.py (14 tests) |
| `app/services/video_probe.py` | `probe_video()`, `extract_audio()` | FFmpeg metadata + audio extraction | subprocess, shutil, json | ✅ spike_runner | ✅ test_integration.py (3 tests) |
| `app/services/scene_detection.py` | `detect_scenes()` | PySceneDetect wrapper | scenedetect | ✅ spike_runner | ❌ Không có test riêng |
| `app/services/frame_extraction.py` | `extract_frames()`, `extract_single_frame()` | FFmpeg frame extraction | subprocess, shutil | ✅ spike_runner | ❌ Không có test riêng |
| `app/adapters/segmentation.py` | `SegmentationAdapter` (ABC), `SAM2Adapter`, `SimpleContourAdapter`, `create_segmentation_adapter()` | AI segmentation interface | cv2, torch, sam2 | ✅ spike_runner (contour only) | ❌ Không có test riêng |
| `app/services/motion_extraction.py` | `compute_frame_motion()`, `compute_scene_motion()`, `smooth_motion()` | Motion vectors from masks | cv2, numpy | ✅ spike_runner | ✅ test_schema.py (9 tests) |
| `app/services/compositing.py` | `load_replacement_image()`, `composite_object()`, `create_debug_overlay()` | Object replacement + debug viz | cv2, numpy | ✅ spike_runner | ✅ test_integration.py (2 tests) |
| `app/services/render.py` | `render_video()`, `render_scene_video()` | FFmpeg video reassembly | subprocess, shutil | ✅ spike_runner | ✅ test_integration.py (2 tests) |
| `app/services/project_service.py` | `ProjectService` class | Project CRUD + persistence | json, pathlib | ❌ Không được gọi | ❌ Không có test |
| `app/spike_runner.py` | `run_spike()`, `main()`, `find_centroid_of_largest_region()` | Pipeline orchestrator | tất cả services | ✅ Entry point | ❌ Không có test riêng |

---

## 3. Dependency Usage Analysis

### Module được gọi trong spike (9/12):
1. `config.py` — AppConfig singleton
2. `schemas/__init__.py` — tất cả data models
3. `services/video_probe.py` — probe_video, extract_audio
4. `services/scene_detection.py` — detect_scenes
5. `services/frame_extraction.py` — extract_frames
6. `adapters/segmentation.py` — create_segmentation_adapter (contour only)
7. `services/motion_extraction.py` — compute_scene_motion, smooth_motion
8. `services/compositing.py` — composite_object, create_debug_overlay, load_replacement_image
9. `services/render.py` — render_video

### Module KHÔNG được gọi (3/12):
1. **`services/project_service.py`** — ProjectService class hoàn chỉnh nhưng không được spike_runner sử dụng. Spike tạo project JSON trực tiếp bằng Pydantic model_dump().
2. **`adapters/segmentation.py::SAM2Adapter`** — Code đầy đủ nhưng không chạy được (thiếu checkpoint).
3. **`services/render.py::render_scene_video()`** — Function tồn tại nhưng không được gọi. Chỉ `render_video()` được dùng.

---

## 4. Code Quality Scan

### TODO/FIXME/HACK
```
$ grep -rn "TODO\|FIXME\|HACK\|XXX\|STUB" app/ tests/
NONE_FOUND
```

### Hard-coded values
- `app/config.py`: Default paths hard-coded (`~/MotionForge2D`, `models_checkpoints/`)
- `app/adapters/segmentation.py`: Template matching threshold `0.3` hard-coded
- `app/services/motion_extraction.py`: Smoothing default window `5`

### Magic constants
- `compositing.py`: Border value `(0, 0, 0, 0)` for warpAffine
- `segmentation.py`: GrabCut `iterCount=5`
- `motion_extraction.py`: Flood fill `loDiff=(20,20,20)`

### Binary files trong repository
- `examples/test_video.mp4` (50 KB) — test fixture
- `examples/test_video_noaudio.mp4` (21 KB) — stray, không cần
- `examples/replacement.png` (800 B) — test fixture
- `output/` (~12 MB) — generated output, không nên commit

### Missing files
- `.gitignore` — không tồn tại
- `LICENSE` — không tồn tại
- `CONTRIBUTING.md` — không tồn tại (không bắt buộc cho spike)
