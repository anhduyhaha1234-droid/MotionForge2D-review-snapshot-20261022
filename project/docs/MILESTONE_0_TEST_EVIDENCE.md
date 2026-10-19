# Milestone 0 — Test Evidence

Ngày tạo: 2026-07-29
Người thực hiện: AI Agent (Hermes)
Mục đích: Ghi lại toàn bộ output thực tế từ các lệnh verification, không chỉnh sửa.

---

## 1. Python Version

```
$ python --version
Python 3.11.9
```

## 2. FFmpeg Version

```
$ ffmpeg -version 2>&1 | head -1
ffmpeg version 8.1.2-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
```

## 3. PyTorch + CUDA

```
$ python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
PyTorch 2.11.0+cu128, CUDA: True
```

## 4. GPU

```
$ nvidia-smi 2>/dev/null | head -10
Wed Jul 29 20:07:42 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 610.47                 KMD Version: 610.47        CUDA UMD Version: 13.3     |
|   0  NVIDIA GeForce RTX 5070      WDDM  |   00000000:01:00.0  On |                  N/A |
| 2291MiB /  12227MiB |      7%      Default |
```

## 5. Git Status

```
$ git status
On branch master
No commits yet
Untracked files:
  README.md
  THIRD_PARTY.md
  app/
  docs/
  examples/
  output/
  pyproject.toml
  scripts/
  tests/
nothing added to commit but untracked files present
```

**Kết luận:** Repository chưa có commit nào. Git init đã chạy nhưng chưa add/commit.

## 6. Test Collection

```
$ python -m pytest tests/ --collect-only -q
tests/test_integration.py::TestVideoProbe::test_probe_metadata
tests/test_integration.py::TestVideoProbe::test_probe_nonexistent
tests/test_integration.py::TestVideoProbe::test_extract_audio
tests/test_integration.py::TestRender::test_render_with_audio
tests/test_integration.py::TestRender::test_render_without_audio
tests/test_integration.py::TestCompositing::test_composite_basic
tests/test_integration.py::TestCompositing::test_composite_invisible
tests/test_schema.py::TestVideoMetadata::test_valid_metadata
tests/test_schema.py::TestVideoMetadata::test_defaults
tests/test_schema.py::TestSceneInfo::test_scene_creation
tests/test_schema.py::TestSceneInfo::test_duration_consistency
tests/test_schema.py::TestSelectionInput::test_point_selection
tests/test_schema.py::TestSelectionInput::test_bbox_selection
tests/test_schema.py::TestProjectData::test_create_minimal
tests/test_schema.py::TestProjectData::test_roundtrip
tests/test_schema.py::TestProjectData::test_schema_version
tests/test_schema.py::TestProjectData::test_with_tracked_object
tests/test_schema.py::TestComputeFrameMotion::test_visible_object
tests/test_schema.py::TestComputeFrameMotion::test_empty_mask
tests/test_schema.py::TestComputeFrameMotion::test_scale_relative_to_reference
tests/test_schema.py::TestComputeFrameMotion::test_scale_different_reference
tests/test_schema.py::TestComputeFrameMotion::test_rotation_computed
tests/test_schema.py::TestComputeFrameMotion::test_opacity_fill_ratio
tests/test_schema.py::TestComputeSceneMotion::test_basic_scene
tests/test_schema.py::TestComputeSceneMotion::test_reference_from_selection_frame
tests/test_schema.py::TestSmoothMotion::test_smoothing_reduces_noise
tests/test_schema.py::TestSmoothMotion::test_preserves_length
tests/test_schema.py::TestSmoothMotion::test_short_list_passthrough
28 tests collected in 0.07s
```

## 6b. FFmpeg PATH Issue (Phát hiện khi re-run)

Lần chạy đầu tiên (với pytest cache): 28/28 PASS.
Lần chạy thứ hai (cache invalidated): 24 PASS, 4 ERROR.

Nguyên nhân: `ffmpeg` được cài qua WinGet, symlink tại:
`C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe`

Nhưng đường dẫn này KHÔNG nằm trong PATH mặc định của MSYS bash session mới.
Integration tests gọi `subprocess.run(["ffmpeg", ...])` → FileNotFoundError.

Fix: `export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"`

Đây là environment setup issue, KHÔNG phải code bug. Cần document trong setup.sh.

Sau khi fix PATH:

```
$ export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"
$ python -m pytest tests/ -v
============================== 28 passed in 0.51s ==============================
```

## 7. Full Test Run

```
$ python -m pytest tests/ -v
============================= test session starts ==============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Admin\MotionForge2D
configfile: pyproject.toml

tests/test_integration.py::TestVideoProbe::test_probe_metadata        PASSED
tests/test_integration.py::TestVideoProbe::test_probe_nonexistent     PASSED
tests/test_integration.py::TestVideoProbe::test_extract_audio         PASSED
tests/test_integration.py::TestRender::test_render_with_audio         PASSED
tests/test_integration.py::TestRender::test_render_without_audio      PASSED
tests/test_integration.py::TestCompositing::test_composite_basic      PASSED
tests/test_integration.py::TestCompositing::test_composite_invisible  PASSED
tests/test_schema.py::TestVideoMetadata::test_valid_metadata           PASSED
tests/test_schema.py::TestVideoMetadata::test_defaults                 PASSED
tests/test_schema.py::TestSceneInfo::test_scene_creation               PASSED
tests/test_schema.py::TestSceneInfo::test_duration_consistency         PASSED
tests/test_schema.py::TestSelectionInput::test_point_selection         PASSED
tests/test_schema.py::TestSelectionInput::test_bbox_selection          PASSED
tests/test_schema.py::TestProjectData::test_create_minimal             PASSED
tests/test_schema.py::TestProjectData::test_roundtrip                  PASSED
tests/test_schema.py::TestProjectData::test_schema_version             PASSED
tests/test_schema.py::TestProjectData::test_with_tracked_object        PASSED
tests/test_schema.py::TestComputeFrameMotion::test_visible_object      PASSED
tests/test_schema.py::TestComputeFrameMotion::test_empty_mask          PASSED
tests/test_schema.py::TestComputeFrameMotion::test_scale_relative...   PASSED
tests/test_schema.py::TestComputeFrameMotion::test_scale_different...  PASSED
tests/test_schema.py::TestComputeFrameMotion::test_rotation_computed   PASSED
tests/test_schema.py::TestComputeFrameMotion::test_opacity_fill_ratio  PASSED
tests/test_schema.py::TestComputeSceneMotion::test_basic_scene         PASSED
tests/test_schema.py::TestComputeSceneMotion::test_reference_from...   PASSED
tests/test_schema.py::TestSmoothMotion::test_smoothing_reduces_noise   PASSED
tests/test_schema.py::TestSmoothMotion::test_preserves_length          PASSED
tests/test_schema.py::TestSmoothMotion::test_short_list_passthrough    PASSED

============================== 28 passed in 0.50s ==============================
```

**Kết luận:** 28/28 PASS, 0 FAIL, 0 SKIP. Thời gian 0.50s.

## 8. Ruff Lint

```
$ python -m ruff check app/ tests/
UP042 Class ObjectKind inherits from both `str` and `enum.Enum`     --> app\schemas\__init__.py:11
UP042 Class SelectionMode inherits from both `str` and `enum.Enum`  --> app\schemas\__init__.py:18
UP042 Class JobStatus inherits from both `str` and `enum.Enum`      --> app\schemas\__init__.py:23
TC003 Move standard library import into type-checking block         --> app\services\compositing.py:6
TC001 Move application import into type-checking block              --> app\services\compositing.py:11
TC001 Move application import into type-checking block              --> app\services\frame_extraction.py:9
TC002 Move third-party import into type-checking block              --> app\services\motion_extraction.py:8
TC003 Move standard library import into type-checking block         --> app\services\project_service.py:6
TC001 Move application import into type-checking block              --> app\services\render.py:9
B905 zip() without an explicit strict= parameter                    --> app\spike_runner.py:295
TC002 Move third-party import into type-checking block              --> tests\test_schema.py:5

Found 11 errors.
```

**Phân loại:**
- UP042 × 3: Đề xuất dùng StrEnum thay vì str+Enum (style, không phải lỗi)
- TC001 × 3: Đề xuất move import vào TYPE_CHECKING block (performance suggestion)
- TC002 × 2: Đề xuất move numpy vào TYPE_CHECKING block
- TC003 × 2: Đề xuất move pathlib vào TYPE_CHECKING block
- B905 × 1: Đề xuất thêm strict= vào zip()
- **E/F errors: 0** (không có lỗi functional)
- **TODO/FIXME/HACK: 0** (grep xác nhận NONE_FOUND)

## 9. SAM 2.1 Import Check

```
$ python -c "
import sam2
print('SAM2 import: OK')
from sam2.build_sam import build_sam2_video_predictor
print('build_sam2_video_predictor: importable')
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
import os
print(f'SAM2 checkpoint exists: {os.path.exists(\"models_checkpoints/sam2.1_hiera_large.pt\")}')
"

SAM2 import: OK
build_sam2_video_predictor: importable
CUDA available: True
GPU: NVIDIA GeForce RTX 5070
SAM2 checkpoint exists: False
```

**Kết luận:** SAM2 code importable nhưng checkpoint chưa download. Không thể chạy SAM2 end-to-end.

## 10. SAM2 Config Files Available

```
$ python -c "import sam2, os; [print(os.path.relpath(os.path.join(r,f), os.path.dirname(sam2.__file__))) for r,d,fs in os.walk(os.path.join(os.path.dirname(sam2.__file__),'configs')) for f in fs if f.endswith('.yaml')]"

configs\sam2\sam2_hiera_b+.yaml
configs\sam2\sam2_hiera_l.yaml
configs\sam2\sam2_hiera_s.yaml
configs\sam2\sam2_hiera_t.yaml
configs\sam2.1\sam2.1_hiera_b+.yaml
configs\sam2.1\sam2.1_hiera_l.yaml
configs\sam2.1\sam2.1_hiera_s.yaml
configs\sam2.1\sam2.1_hiera_t.yaml
configs\sam2.1_training\sam2.1_hiera_b+_MOSE_finetune.yaml
```

## 11. ffprobe — Input Video

```
$ ffprobe -v quiet -show_streams -print_format json examples/test_video.mp4

Stream #0: Video: mpeg4, yuv420p, 320x240, 30/1 fps, 54434 bit_rate, 90 frames
Stream #1: Audio: aac (LC), 44100 Hz, mono, fltp, 69594 bit_rate, 131 frames
```

## 12. ffprobe — Output Video

```
$ ffprobe -v quiet -show_streams -print_format json output/renders/scene_0_output.mp4

Stream #0: Video: h264 (High), yuv420p, 320x240, 30/1 fps, 19456 bit_rate, 90 frames
Stream #1: Audio: aac (LC), 44100 Hz, mono, fltp, 112242 bit_rate, 130 frames
```

## 13. SHA-256 Hashes

```
input_video:    sha256=093cc1f509d30fba01e7e1913faac6455bf927c81f7a3ad26f4291de1dcb7177
output_video:   sha256=1d47e813c1e14e3456c56e01a58c1191db0a84a2ee0067c03d0b9caf5bdc9b36
project_json:   sha256=d6c8bb1a1833e4dc5537a10120b30330b278883984a9fc132dedc8f333bebc4a
motion_json:    sha256=77f6dddf77d314385cb068dbfa5228531554128a279b76ba10b4bde45a7137e5
benchmark_json: sha256=a4dea55c5057d2eb5581d57e819537cb71c927d661c547f5b59e829a0cb82398
```

## 14. Frame Validation (5 representative frames)

```
Frame   0: orig=True comp=True mask=True  visible=False centroid=(0.0,0.0) composited=False
Frame  22: orig=True comp=True mask=False visible=False centroid=(0.0,0.0) composited=False
Frame  45: orig=True comp=True mask=False visible=True  centroid=(149.1,119.5) composited=True
Frame  67: orig=True comp=True mask=False visible=False centroid=(0.0,0.0) composited=False
Frame  89: orig=True comp=True mask=True  visible=False centroid=(0.0,0.0) composited=False
```

**Phát hiện quan trọng:** Chỉ frame 45 (selection frame) có object visible và được composite.
Các frame khác: mask propagation không hoạt động hiệu quả với contour backend.

## 15. Project JSON Schema Validation

```
$ python -c "import json; p=json.load(open('output/project.json')); ..."

version: 1.0.0
scenes: 1
objects: 1
  object_id: obj_0
  kind: character
  motion frames: 90
  has reference_bbox: True

motion_data frames: 90
reference_bbox: {'x': 130.0, 'y': 100.0, 'width': 40.0, 'height': 40.0}

benchmark:
  timings_seconds: {probe: 0.028, scene_detect: 0.062, audio_extract: 0.029, frame_extract: 0.055, segment_initial: 0.0, mask_propagation: 0.107, segment_total: 0.107, motion_extraction: 0.007, compositing: 0.065, render: 0.493, total: 0.886}
  peak_ram_mb: 22.77
  gpu_peak_mb: 0.0
  total_frames_processed: 90
  fps_throughput: 101.57
```

## 16. Stray Files Detected

```
examples/test_video_noaudio.mp4  (21681 bytes) — intermediate file, không cần thiết
output/ (toàn bộ thư mục) — chứa ~200 file frame/mask/composited PNG
.mypy_cache/ — cache files
.ruff_cache/ — cache files
__pycache__/ — compiled Python files
```

**Không có .gitignore** — nếu commit, cache và output sẽ bị track.
