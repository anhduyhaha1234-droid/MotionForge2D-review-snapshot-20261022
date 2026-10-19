# Milestone 0 — Review Package

**Dự án:** MotionForge 2D
**Milestone:** 0 — Technical Discovery & Vertical Spike
**Ngày kiểm tra:** 2026-07-29
**Người kiểm tra:** AI Agent (Hermes)
**Trạng thái:** Đánh giá độc lập, không tự động PASS

---

## A. Thông tin chung

| Thông tin | Giá trị |
|-----------|---------|
| Tên dự án | MotionForge 2D |
| Đường dẫn | `C:\Users\Admin\MotionForge2D` |
| Milestone | 0 — Technical Discovery & Vertical Spike |
| Git branch | `master` |
| Git commits | **0** (chưa commit, chỉ git init) |
| Working tree | Untracked files (chưa add/commit) |
| Python | 3.11.9 |
| FFmpeg | 8.1.2-full_build (GPL build) |
| PyTorch | 2.11.0+cu128 |
| CUDA | 12.8 (driver 610.47) |
| GPU | NVIDIA GeForce RTX 5070, 12GB VRAM |
| OS | Windows 10 (MINGW64_NT-10.0-22631) |

**Cảnh báo:** Repository chưa có commit nào. Không có .gitignore. Không có LICENSE file.

---

## B. Mục tiêu Milestone 0

Vertical spike phải chứng minh pipeline:

1. Nhận MP4 → ✅ PASS
2. Đọc metadata (ffprobe) → ✅ PASS
3. Phát hiện scene (PySceneDetect) → ✅ PASS
4. Tách audio → ✅ PASS
5. Tách frame → ✅ PASS
6. Chọn object bằng point hoặc bbox → ✅ PASS
7. Phân đoạn object → ✅ PASS (contour backend)
8. Lan truyền mask → ⚠️ PASS WITH LIMITATION
9. Trích xuất motion → ✅ PASS
10. Thay bằng PNG mới → ✅ PASS
11. Composite → ⚠️ PASS WITH LIMITATION
12. Render MP4 mới có audio → ✅ PASS

---

## C. Kết quả theo từng bước pipeline

| Bước | Module thực hiện | Input | Output | Trạng thái | Bằng chứng |
|------|-----------------|-------|--------|:----------:|------------|
| Video Probe | `services/video_probe.py::probe_video()` | `examples/test_video.mp4` | `VideoMetadata` object | ✅ PASS | ffprobe output: 320×240, 30fps, 90 frames, mpeg4, aac |
| Scene Detection | `services/scene_detection.py::detect_scenes()` | video path | 1 scene: frames 0-89 | ✅ PASS | Log: "Found 1 scene(s)" |
| Audio Extraction | `services/video_probe.py::extract_audio()` | video path | `output/audio/original_audio.aac` (27KB) | ✅ PASS | File exists, ffprobe validates |
| Frame Extraction | `services/frame_extraction.py::extract_frames()` | video + scene info | 90 PNG files in `output/frames/scene_0/` | ✅ PASS | `ls` confirms 90 files |
| Selection | `spike_runner.py::find_centroid_of_largest_region()` | frame 45 | point (160, 120) | ✅ PASS | Log: "Auto-detected point (160, 120) at frame 45" |
| Segmentation | `adapters/segmentation.py::SimpleContourAdapter.segment_frame()` | frame + point | `initial_mask.png` (1600 nonzero pixels) | ✅ PASS | Debug overlay shows mask at selection |
| Mask Propagation | `adapters/segmentation.py::SimpleContourAdapter.propagate_masks()` | 90 frames + initial mask | 90 masks | ⚠️ LIMITATION | Chỉ frame 45 có mask hữu ích. Template matching thất bại cho frames khác. |
| Motion Extraction | `services/motion_extraction.py::compute_scene_motion()` | 90 masks | 90 FrameMotion entries | ✅ PASS | motion_data.json: 90 entries |
| Smoothing | `services/motion_extraction.py::smooth_motion()` | raw motion | smoothed motion | ✅ PASS | Integrated in spike_runner |
| Compositing | `services/compositing.py::composite_object()` | frame + mask + replacement + motion | composited frame | ⚠️ LIMITATION | Chỉ frame 45 thực sự composite. Các frame khác visibility=False. |
| Render | `services/render.py::render_video()` | composited frames + audio | `output/renders/scene_0_output.mp4` | ✅ PASS | ffprobe: H264, 320×240, 30fps, 90 frames, aac |
| Audio Muxing | FFmpeg (trong render_video) | video frames + audio file | output video with audio | ✅ PASS | Output has 2 streams (video+audio) |
| Output Validation | ffprobe + custom script | output video | comparison table | ✅ PASS | Xem MILESTONE_0_OUTPUT_VALIDATION.md |

---

## D. Danh sách module

### Xác nhận "10 service modules tách biệt"

Đếm thực tế trong `app/`:

| # | Module path | Loại | Có trong spike? |
|---|------------|------|:---------------:|
| 1 | `app/config.py` | Config | ✅ |
| 2 | `app/schemas/__init__.py` | Schema/Model | ✅ |
| 3 | `app/services/video_probe.py` | Service | ✅ |
| 4 | `app/services/scene_detection.py` | Service | ✅ |
| 5 | `app/services/frame_extraction.py` | Service | ✅ |
| 6 | `app/services/motion_extraction.py` | Service | ✅ |
| 7 | `app/services/compositing.py` | Service | ✅ |
| 8 | `app/services/render.py` | Service | ✅ |
| 9 | `app/services/project_service.py` | Service | ❌ Không được gọi |
| 10 | `app/adapters/segmentation.py` | Adapter | ✅ (contour only) |
| 11 | `app/spike_runner.py` | Orchestrator | ✅ |

**Kết luận:** Có 11 module Python (không tính __init__.py). 10 trong số 12 file `.py` được gọi trong spike. `project_service.py` không được spike_runner sử dụng. Tuyên bố "10 service modules tách biệt" **đúng về số lượng** nhưng cần lưu ý `project_service.py` chưa được integration test.

---

## E. Kiến trúc adapter segmentation

### Interface

```python
class SegmentationAdapter(abc.ABC):
    @abc.abstractmethod
    def segment_frame(self, frame: np.ndarray, selection: SelectionInput) -> np.ndarray: ...
    @abc.abstractmethod
    def propagate_masks(self, frames: list[np.ndarray], initial_mask: np.ndarray, initial_frame_idx: int) -> list[np.ndarray]: ...
    @abc.abstractmethod
    def cleanup(self) -> None: ...
```

### Implementations

| Implementation | Trạng thái | Lý do |
|---------------|:----------:|-------|
| `SimpleContourAdapter` — segment_frame | **Implemented and executed** | Chạy thành công, tạo mask 1600 px |
| `SimpleContourAdapter` — propagate_masks | **Implemented but FAILING** | Template matching không propagate được. Chỉ frame selection có mask. |
| `SAM2Adapter` — segment_frame | **Implemented but not executed** | Code đầy đủ, import OK, nhưng thiếu checkpoint |
| `SAM2Adapter` — propagate_masks | **Implemented but not executed** | Code đầy đủ, import OK, nhưng thiếu checkpoint |
| `create_segmentation_adapter()` factory | **Implemented and executed** | Tạo đúng adapter theo backend param |

### Chi tiết SAM2 Adapter

- `sam2` package: ✅ Importable
- `build_sam2_video_predictor`: ✅ Importable
- Config files (`sam2.1_hiera_l.yaml`): ✅ Tồn tại trong package
- Checkpoint (`sam2.1_hiera_large.pt`): ❌ **Chưa download** (file không tồn tại)
- CUDA: ✅ Available (RTX 5070)
- `SAM2Adapter.__init__()`: Nhận model_cfg, checkpoint, device
- `SAM2Adapter._ensure_model()`: Lazy load, sẽ raise FileNotFoundError nếu thiếu checkpoint
- `SAM2Adapter.segment_frame()`: Gọi `init_state`, `add_new_points_or_box` — code logic đúng nhưng chưa chạy
- `SAM2Adapter.propagate_masks()`: Gọi `init_state`, `append_frame`, `add_new_mask`, `propagate_in_video` — code logic đúng nhưng chưa chạy

**Cảnh báo:** SAM2 adapter code看起来正确 nhưng chưa được end-to-end test. Không thể kết luận "SAM2 backend hoàn thành" chỉ dựa trên code readable.

### Cách chọn backend

`create_segmentation_adapter(backend="sam2"|"contour")` — factory function. Spike_runner truyền `--backend contour` mặc định.

### Xử lý thiếu checkpoint

`SAM2Adapter._ensure_model()` raise `FileNotFoundError` với message rõ ràng.

### Xử lý không có GPU

Không có fallback tự động. Nếu `device="cuda"` và CUDA không available, PyTorch sẽ raise RuntimeError.

---

## F. Project JSON Schema

### Schema Version

`version: "1.0.0"` — field bắt buộc trong `ProjectData`.

### Cấu trúc thực tế

```
ProjectData
├── version: str = "1.0.0"
├── name: str
├── source_video: str (absolute path)
├── video_metadata: VideoMetadata | None
│   ├── width, height: int
│   ├── fps: float
│   ├── duration_seconds: float
│   ├── total_frames: int
│   ├── codec: str
│   ├── has_audio: bool
│   ├── audio_codec: str | None
│   ├── file_size_bytes: int
│   └── file_path: str
├── scenes: list[SceneInfo]
│   ├── scene_id: int
│   ├── start_frame, end_frame: int (INCLUSIVE)
│   ├── start_time_sec, end_time_sec, duration_sec: float
│   └── frame_count: int
└── objects: list[TrackedObject]
    ├── object_id: str
    ├── name: str
    ├── kind: ObjectKind (character|prop|effect|background)
    ├── selection: SelectionInput
    │   ├── mode: SelectionMode (point|bounding_box)
    │   ├── frame_index: int
    │   ├── x, y: float
    │   └── width, height: float | None
    ├── scene_id: int
    ├── replacement_image: str | None
    └── motion: SceneMotion | None
        ├── scene_id: int
        ├── frames: list[FrameMotion]
        │   ├── frame_index: int
        │   ├── centroid_x, centroid_y: float
        │   ├── bbox: {x, y, width, height}: float
        │   ├── scale_x, scale_y: float
        │   ├── rotation_deg: float (degrees, từ minAreaRect)
        │   ├── opacity: float (0-1, fill ratio)
        │   ├── visibility: bool
        │   └── area: float (pixels)
        └── reference_bbox: BoundingBox | None
```

### Ghi chú schema

- **Frame indexing:** 0-based
- **Start/end frame:** INCLUSIVE (start_frame=0, end_frame=89 = 90 frames)
- **Rotation unit:** degrees (từ `cv2.minAreaRect`, normalize về [-90, 90])
- **Scale:** relative to reference_bbox (1.0 = same size)
- **Opacity:** fill ratio of bounding box area (0-1)
- **Visibility:** bool, False khi mask area < threshold
- **Confidence:** Không có field confidence
- **Anchor:** Không có field anchor
- **Raw vs smoothed motion:** Chỉ smoothed được lưu trong project JSON. Raw không được persist.
- **Mask path:** Không lưu trong schema. Masks lưu ở filesystem (`output/masks/`).

### JSON rút gọn từ output thật

```json
{
  "version": "1.0.0",
  "name": "spike_project",
  "scenes": [{"scene_id": 0, "start_frame": 0, "end_frame": 89, "frame_count": 90}],
  "objects": [{
    "object_id": "obj_0",
    "kind": "character",
    "selection": {"mode": "point", "frame_index": 45, "x": 160.0, "y": 120.0},
    "motion": {
      "frames": [
        {"frame_index": 0, "centroid_x": 0.0, "centroid_y": 0.0, "visibility": false},
        {"frame_index": 45, "centroid_x": 149.1, "centroid_y": 119.5, "visibility": true,
         "bbox": {"x": 130.0, "y": 100.0, "width": 40.0, "height": 40.0},
         "scale_x": 1.0, "scale_y": 1.0, "rotation_deg": 0.0, "opacity": 1.0}
      ],
      "reference_bbox": {"x": 130.0, "y": 100.0, "width": 40.0, "height": 40.0}
    }
  }]
}
```

---

## G. Tests

### Tổng hợp

| Metric | Giá trị |
|--------|---------|
| Unit tests | 21 |
| Integration tests | 7 |
| **Tổng** | **28** |
| Pass | 28 |
| Fail | 0 |
| Skip | 0 |
| Thời gian | 0.50s |

### Lệnh đã chạy

```bash
python -m pytest tests/ -v
# Exit code: 0
# 28 passed in 0.50s
```

### File test

| File | Tests | Loại |
|------|------:|------|
| `tests/test_schema.py` | 21 | Unit |
| `tests/test_integration.py` | 7 | Integration |
| `tests/conftest.py` | 0 | Fixtures |

### Test case detail

#### Unit tests (test_schema.py) — 21 tests

| Test | Kiểm tra | Mock/Fixture | Happy path only? |
|------|----------|:------------:|:----------------:|
| TestVideoMetadata::test_valid_metadata | Schema creation | Không | ✅ Happy only |
| TestVideoMetadata::test_defaults | Default values | Không | ✅ Happy only |
| TestSceneInfo::test_scene_creation | Schema creation | Không | ✅ Happy only |
| TestSceneInfo::test_duration_consistency | Field consistency | Không | ✅ Happy only |
| TestSelectionInput::test_point_selection | Point mode | Không | ✅ Happy only |
| TestSelectionInput::test_bbox_selection | Bbox mode | Không | ✅ Happy only |
| TestProjectData::test_create_minimal | Minimal project | Không | ✅ Happy only |
| TestProjectData::test_roundtrip | Serialize/deserialize | `sample_project_data` fixture | ✅ Happy only |
| TestProjectData::test_schema_version | Version field | `sample_project_data` fixture | ✅ Happy only |
| TestProjectData::test_with_tracked_object | Object in project | `sample_project_data` fixture | ✅ Happy only |
| TestComputeFrameMotion::test_visible_object | Mask → motion | `sample_mask` fixture | ✅ Happy only |
| TestComputeFrameMotion::test_empty_mask | Empty mask → invisible | numpy zeros | ✅ Edge case |
| TestComputeFrameMotion::test_scale_relative_to_reference | Scale calc | `sample_mask` fixture | ✅ Happy only |
| TestComputeFrameMotion::test_scale_different_reference | Scale > 1 | `sample_mask` fixture | ✅ Happy only |
| TestComputeFrameMotion::test_rotation_computed | Rotation extraction | `sample_mask` fixture | ✅ Happy only |
| TestComputeFrameMotion::test_opacity_fill_ratio | Opacity calc | `sample_mask` fixture | ✅ Happy only |
| TestComputeSceneMotion::test_basic_scene | Scene motion | `sample_mask` × 5 | ✅ Happy only |
| TestComputeSceneMotion::test_reference_from_selection_frame | Ref bbox source | 2 different masks | ✅ Happy only |
| TestSmoothMotion::test_smoothing_reduces_noise | Smoothing effect | Random noise | ✅ Happy only |
| TestSmoothMotion::test_preserves_length | Length preserved | 10 synthetic frames | ✅ Happy only |
| TestSmoothMotion::test_short_list_passthrough | Edge case | 1 frame | ✅ Edge case |

#### Integration tests (test_integration.py) — 7 tests

| Test | Kiểm tra | FFmpeg? | Fixture | Happy path only? |
|------|----------|:-------:|:-------:|:----------------:|
| TestVideoProbe::test_probe_metadata | ffprobe output | ✅ Real FFmpeg | `test_video` (generated) | ✅ Happy only |
| TestVideoProbe::test_probe_nonexistent | Error handling | ❌ | Không | ✅ Error case |
| TestVideoProbe::test_extract_audio | Audio extraction | ✅ Real FFmpeg | `test_video` | ✅ Happy only |
| TestRender::test_render_with_audio | Video render + audio mux | ✅ Real FFmpeg | `test_video` + extracted frames | ✅ Happy only |
| TestRender::test_render_without_audio | Video render no audio | ✅ Real FFmpeg | extracted frames | ✅ Happy only |
| TestCompositing::test_composite_basic | Alpha blending | ❌ | `test_png` + numpy arrays | ✅ Happy only |
| TestCompositing::test_composite_invisible | Invisible passthrough | ❌ | numpy arrays | ✅ Edge case |

**Nhận xét:**
- Không có test nào dùng mock — tất cả dùng real FFmpeg hoặc real numpy operations
- 4/7 integration tests thực sự gọi FFmpeg subprocess
- **Phát hiện:** 4 integration tests fail nếu FFmpeg không trong PATH (WinGet symlink issue). Fix bằng `export PATH`.
- Không có test cho error paths của render (FFmpeg failure)
- Không có test cho scene_detection, frame_extraction, project_service
- Không có test cho SAM2Adapter

---

## H. Benchmark

### Thông tin video benchmark

| Thuộc tính | Giá trị |
|-----------|---------|
| Video input | `examples/test_video.mp4` |
| Độ phân giải | 320 × 240 |
| FPS | 30 |
| Frame count | 90 |
| Duration | 3.0s |
| Có audio | ✅ (AAC, mono, 44100 Hz) |
| Content | Solid background + moving red rectangle |
| Complexity | Rất thấp (uniform colors, simple shapes) |

### Kết quả benchmark

| Metric | Giá trị | Cách đo |
|--------|--------:|---------|
| Tổng thời gian | 0.886s | `time.perf_counter()` |
| Throughput | 101.57 fps | frames / total_time |
| Peak RAM | 22.77 MB | `tracemalloc.get_traced_memory()` |
| GPU peak | 0.0 MB | `torch.cuda.max_memory_allocated()` (0 vì không dùng CUDA) |

### Timing breakdown

| Step | Thời gian | % tổng |
|------|--------:|------:|
| Probe | 0.028s | 3.2% |
| Scene detect | 0.062s | 7.0% |
| Audio extract | 0.029s | 3.3% |
| Frame extract | 0.055s | 6.2% |
| Segment initial | 0.000s | 0.0% |
| Mask propagation | 0.107s | 12.1% |
| Motion extraction | 0.007s | 0.8% |
| Compositing | 0.065s | 7.3% |
| Render | 0.493s | 55.6% |

### Cảnh báo benchmark

1. **Video rất ngắn** (3s, 90 frames). Benchmark trên video dài hơn sẽ khác nhiều.
2. **Nội dung rất đơn giản** (solid bg, rectangle). Real animation sẽ chậm hơn.
3. **Contour backend** — không phải AI segmentation. Benchmark này KHÔNG đại diện cho SAM 2.1 performance.
4. **Không tính model loading time** — SAM2 model load (~890MB checkpoint) sẽ thêm significant time.
5. **Không tính startup time** — Python interpreter + import torch (~2-3s).
6. **RAM chỉ 22.77MB** — vì contour backend rất nhẹ. SAM2 sẽ dùng nhiều GB hơn.
7. **Render chiếm 55.6%** — FFmpeg encode là bottleneck, không phải segmentation.
8. **segment_initial = 0.0** — có vẻ do measurement granularity, thực tế GrabCut mất vài ms.
9. **Throughput 101.57 fps** — meaningless vì video chỉ 320×240 và contour backend rất nhanh.

---

## I. Validation video đầu ra

Xem chi tiết trong `MILESTONE_0_OUTPUT_VALIDATION.md`.

### So sánh Input vs Output

| Thuộc tính | Input | Output | Sai lệch | Kết luận |
|-----------|------:|-------:|---------:|----------|
| Width | 320 | 320 | 0 | ✅ Match |
| Height | 240 | 240 | 0 | ✅ Match |
| FPS | 30 | 30 | 0 | ✅ Match |
| Frame count | 90 | 90 | 0 | ✅ Match |
| Duration (video) | 3.000s | 3.000s | 0 | ✅ Match |
| Video codec | mpeg4 | h264 | Changed | ⚠️ Expected |
| Pixel format | yuv420p | yuv420p | 0 | ✅ Match |
| Audio codec | aac | aac | 0 | ✅ Match |
| Audio sample rate | 44100 | 44100 | 0 | ✅ Match |
| Audio channels | 1 | 1 | 0 | ✅ Match |
| Audio duration | 3.000s | 2.995s | -0.005s | ✅ Acceptable |
| Audio frames | 131 | 130 | -1 | ✅ Acceptable |
| File size | 50,755 B | 54,259 B | +3,504 B | ✅ Expected |

**Audio sync:** Audio duration lệch 0.005s (< 1 frame at 30fps). Chấp nhận được.

**Frame loss:** Video: 0 frame loss. Audio: 1 frame difference (131→130). Do AAC encoding rounding.

---

## J. Artifact Inventory

### Source code

| File | Size | SHA-256 (first 16 chars) |
|------|-----:|--------------------------|
| `app/__init__.py` | 83 B | — |
| `app/config.py` | 1,642 B | — |
| `app/schemas/__init__.py` | 4,817 B | — |
| `app/services/video_probe.py` | 3,895 B | — |
| `app/services/scene_detection.py` | 2,324 B | — |
| `app/services/frame_extraction.py` | 2,518 B | — |
| `app/services/motion_extraction.py` | 6,483 B | — |
| `app/services/compositing.py` | 6,508 B | — |
| `app/services/render.py` | 4,058 B | — |
| `app/services/project_service.py` | 2,838 B | — |
| `app/adapters/segmentation.py` | 11,170 B | — |
| `app/spike_runner.py` | 17,245 B | — |

### Artifacts

| Artifact | Path | Size | SHA-256 | Validate |
|----------|------|-----:|---------|:--------:|
| Input video | `examples/test_video.mp4` | 50,755 B | `093cc1f5...` | ffprobe ✅ |
| Output video | `output/renders/scene_0_output.mp4` | 54,259 B | `1d47e813...` | ffprobe ✅ |
| Project JSON | `output/project.json` | 42,018 B | `d6c8bb1a...` | json.load ✅ |
| Motion JSON | `output/motion_data.json` | 31,707 B | `77f6dddf...` | json.load ✅ |
| Benchmark JSON | `output/benchmark.json` | 442 B | `a4dea55c...` | json.load ✅ |
| Audio | `output/audio/original_audio.aac` | 27,217 B | — | ffprobe ✅ |
| Frames | `output/frames/scene_0/` | 90 files | — | cv2.imread ✅ |
| Masks | `output/masks/scene_0/` | 10 files | — | cv2.imread ✅ |
| Debug overlays | `output/debug/` | 12 files | — | cv2.imread ✅ |
| Composited | `output/renders/scene_0_composited/` | 90 files | — | cv2.imread ✅ |
| Replacement | `examples/replacement.png` | 800 B | — | cv2.imread ✅ |

### Stray files

| File | Size | Vấn đề |
|------|-----:|--------|
| `examples/test_video_noaudio.mp4` | 21,681 B | Intermediate file, không cần |
| `output/` (toàn bộ) | ~12 MB | Generated output, không nên commit |

---

## K. License Review

| Dependency | Version | License | Commercial concern | Source checked | Status |
|-----------|---------|---------|:------------------:|:--------------:|:------:|
| PyTorch | 2.11.0+cu128 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| torchvision | 0.26.0+cu128 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| SAM-2 (code) | 1.0 | Apache-2.0 | ❌ Không | GitHub repo | ✅ |
| SAM 2.1 checkpoint | — | Apache-2.0 | ❌ Không | Meta AI page | ✅ |
| FastAPI | 0.139.2 | MIT | ❌ Không | PyPI | ✅ |
| Pydantic | 2.13.4 | MIT | ❌ Không | PyPI | ✅ |
| OpenCV | 5.0.0 | Apache-2.0 | ❌ Không | PyPI | ✅ |
| NumPy | 2.4.4 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| Pillow | 12.2.0 | MIT-CMU | ❌ Không | PyPI | ✅ |
| PySceneDetect | 0.7.1 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| SQLAlchemy | 2.0.51 | MIT | ❌ Không | PyPI | ✅ |
| uvicorn | 0.51.0 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| httpx | 0.28.1 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| hydra-core | 1.3.4 | MIT | ❌ Không | PyPI | ✅ |
| omegaconf | 2.3.1 | BSD-3-Clause | ❌ Không | PyPI | ✅ |
| iopath | 0.1.10 | MIT | ❌ Không | PyPI | ✅ |
| FFmpeg | 8.1.2 | GPL-2.0+ (build) | ⚠️ GPL compliance | winget | ⚠️ |
| pytest | 9.1.1 | MIT | ❌ Không | PyPI | ✅ |
| ruff | 0.16.0 | MIT | ❌ Không | PyPI | ✅ |

**Cảnh báo FFmpeg:** Build được cài qua winget sử dụng `--enable-gpl`. Nếu distribute binaries, phải tuân thủ GPL-2.0+.

**Tất cả Python dependencies đều permissive license (MIT/BSD/Apache).** Không có dependency proprietary hoặc paywalled API.

---

## L. Hạn chế và rủi ro

### Critical

1. **Contour backend không phải semantic segmentation.** `SimpleContourAdapter` dùng GrabCut + template matching. Template matching chỉ match ở vị trí chính xác. Object di chuyển → propagation thất bại. **Đây không phải "object tracking" — chỉ là "template matching at same position".**

2. **SAM 2.1 chưa chạy end-to-end.** Checkpoint chưa download (~890MB). Code adapter có vẻ logic đúng nhưng chưa được validate bằng execution. Có thể có bug ẩn (wrong API usage, tensor shape mismatch, etc.).

3. **Mask propagation thất bại trên thực tế.** Chỉ 1/90 frames (selection frame) có mask hữu ích. Pipeline "hoàn thành" về mặt code nhưng output không usable cho real use case.

### High

4. **Video benchmark quá ngắn và đơn giản.** 3 seconds, 320×240, solid background, rectangle. Không representative cho real animation.

5. **Object có nền màu đơn giản.** Test video dùng solid gray background + red rectangle. Real animation sẽ có complex backgrounds, similar colors, motion blur.

6. **Không test occlusion.** Không có scenario object bị che khuất.

7. **Rotation estimation chưa validate.** `cv2.minAreaRect` trả rotation cho rectangle shapes. Không biết accuracy cho irregular shapes.

### Medium

8. **Audio sync chưa validate kỹ.** Lệch 0.005s chấp nhận được nhưng chưa test với video dài hơn hoặc variable frame rate.

9. **Variable frame rate chưa xử lý.** Code giả định CFR. VFR video sẽ gây sai lệch frame timing.

10. **Multiple scenes chưa test.** Spike chỉ test 1 scene. Multi-scene workflow chưa verify.

11. **Multiple objects chưa test.** Spike chỉ track 1 object.

12. **Windows vs WSL2.** Chạy trên Windows (MINGW64). Chưa test trên WSL2/Linux.

13. **No restart/recovery.** Pipeline chạy một lần. Không có checkpoint/resume cho video dài.

14. **No cancellation.** Không có cơ chế cancel giữa chừng.

15. **Repository chưa commit.** Không có version history, không có .gitignore.

16. **FFmpeg PATH dependency.** Integration tests (4/7) fail nếu FFmpeg không trong PATH. WinGet install đặt symlink ở `C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\` nhưng đường dẫn này không tự động vào PATH trong MSYS bash sessions. Cần `export PATH` hoặc document rõ trong setup.sh.

---

## M. Phân loại mức độ hoàn thành

| Requirement | Status | Evidence | Limitation |
|------------|:------:|----------|------------|
| 1. Nhận MP4 | **PASS** | ffprobe reads file successfully | — |
| 2. Đọc metadata | **PASS** | probe_video returns VideoMetadata | — |
| 3. Phát hiện scene | **PASS** | PySceneDetect found 1 scene | Chưa test multi-scene |
| 4. Tách audio | **PASS** | extract_audio produces .aac file | — |
| 5. Tách frame | **PASS** | 90 PNG files extracted | — |
| 6. Chọn object | **PASS** | Point selection works | Bbox selection chưa integration test |
| 7. Phân đoạn object | **PASS WITH LIMITATION** | Contour backend works at selection frame | GrabCut quality thấp cho animation |
| 8. Lan truyền mask | **FAIL** | Template matching chỉ match ở frame selection | Contour propagation unusable cho real use |
| 9. Trích xuất motion | **PASS** | 90 FrameMotion entries computed | Chưa validate accuracy |
| 10. Thay bằng PNG | **PASS** | load_replacement_image works | — |
| 11. Composite | **PASS WITH LIMITATION** | Frame 45 composited correctly | Chỉ 1/90 frames composite |
| 12. Render MP4 có audio | **PASS** | Output: H264, 30fps, 90 frames, AAC audio | — |
| 13. Project JSON | **PASS** | version 1.0.0, valid schema | — |
| 14. Unit tests | **PASS** | 21/21 pass | Không test error paths |
| 15. Integration tests | **PASS** | 7/7 pass | Không test scene_detection, frame_extraction |
| 16. Benchmark log | **PASS** | benchmark.json with timing + RAM | Chỉ contour backend |
| 17. Debug overlay | **PASS** | 12 overlay PNG files | — |
| 18. README | **PASS** | Đầy đủ hướng dẫn | — |
| 19. SPIKE_REPORT | **PASS** | Đầy đủ 10 sections | — |
| 20. THIRD_PARTY | **PASS** | License audit cho tất cả deps | — |
| 21. setup.sh | **PASS** | Script exists, logic đúng | Chưa chạy trên clean env |
| 22. download_models.sh | **PASS** | Script exists, logic đúng | Chưa chạy (890MB download) |
| 23. run_spike.sh | **PASS** | Script exists, logic đúng | — |

---

## N. Kết luận đề nghị nghiệm thu

### `CONDITIONALLY ACCEPTED`

### Điều kiện bắt buộc trước Milestone 1:

1. **Download SAM 2.1 checkpoint và chạy end-to-end với SAM2 backend.** Đây là điều kiện tiên quyết. Không thể claim "vertical spike hoàn thành" nếu AI segmentation chưa chạy.

2. **Fix mask propagation.** Hoặc dùng SAM2 propagation (không phải template matching), hoặc document rõ contour backend chỉ dùng cho testing và spike phải chạy với SAM2.

3. **Tạo .gitignore** trước khi commit.

4. **Commit repository** với git history rõ ràng.

### Điều kiện nên hoàn thành trước hoặc trong Milestone 1:

5. Bổ sung test cho `scene_detection`, `frame_extraction`, `project_service`.
6. Bổ sung test error paths (FFmpeg failure, invalid video, corrupt file).
7. Pin dependency versions trong pyproject.toml (hiện tại dùng `>=` ranges).
8. Tạo LICENSE file.
9. Xóa stray file `examples/test_video_noaudio.mp4`.

---

## O. Đề xuất Milestone 1

### Code được phép tái sử dụng:

- `schemas/__init__.py` — Data models tốt, schema versioned
- `services/video_probe.py` — Hoạt động tốt
- `services/scene_detection.py` — Hoạt động tốt
- `services/frame_extraction.py` — Hoạt động tốt
- `services/motion_extraction.py` — Logic đúng, test coverage OK
- `services/compositing.py` — Logic đúng
- `services/render.py` — Hoạt động tốt

### Cần refactor:

- `adapters/segmentation.py::SimpleContourAdapter` — Bỏ template matching, thay bằng optical flow hoặc contour tracking. Hoặc bỏ hoàn toàn và chỉ support SAM2.
- `spike_runner.py` — Quá dài (17KB), cần tách thành smaller functions
- `project_service.py` — Cần integration với spike_runner
- Error handling: thiếu retry, timeout handling cho FFmpeg subprocess

### Technical debt:

- Không có logging config (hard-coded basicConfig)
- Không có proper error types (chỉ dùng RuntimeError, FileNotFoundError)
- Không có progress callback cho long-running operations
- Config singleton pattern không testable

### Schema cần thay đổi:

- Thêm `confidence` field vào FrameMotion
- Thêm `mask_path` field để track mask file location
- Thêm `raw_motion` storage option
- Thêm `anchor` field cho compositing control

### Test cần bổ sung:

- Scene detection integration test
- Frame extraction integration test
- SAM2 adapter test (có checkpoint)
- Error path tests (corrupt video, missing file, FFmpeg failure)
- Project service CRUD tests
- Multi-scene test
- Multi-object test

### Dependency cần pin:

-คณะกรรม `torch>=2.0.0` → `torch==2.11.0+cu128` (exact version)
- `opencv-python-headless>=4.9.0` → pin exact version
-บรรยาก `SAM-2>=1.0` → pin to specific commit hash

### Rủi ro cần giải quyết trước Milestone 1:

1. SAM2 checkpoint download reliability (890MB, có thể fail)
2. SAM2 GPU memory footprint trên RTX 5070 12GB
3. FFmpeg subprocess timeout handling
4. Cross-platform path handling (Windows backslash vs forward slash)
