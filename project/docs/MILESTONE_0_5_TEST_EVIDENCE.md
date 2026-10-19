# Milestone 0.5 — Test Evidence

Ngày tạo: 2026-07-29

---

## 1. Environment

```
Python 3.11.9
FFmpeg 8.1.2-full_build (WinGet)
PyTorch 2.11.0+cu128
CUDA 12.8 (driver 610.47)
GPU: NVIDIA GeForce RTX 5070 (12GB VRAM)
OS: Windows 10 (MINGW64)
```

## 2. Git Status

```
$ git log --oneline
f7094a5 M0.5 Phase 4-6: Fixtures, validation, schema v2.0.0
555f13e M0.5 Phase 2+3: SAM2 GPU validation + adapter rewrite
1ff3850 M0.5 Phase 1: Repository stabilization

$ git status
nothing to commit, working tree clean
```

## 3. Test Run

```
$ python -m pytest tests/ -v
28 passed in 0.53s
```

### Test List

| # | Test | Result |
|---|------|--------|
| 1 | TestVideoProbe::test_probe_metadata | ✅ |
| 2 | TestVideoProbe::test_probe_nonexistent | ✅ |
| 3 | TestVideoProbe::test_extract_audio | ✅ |
| 4 | TestRender::test_render_with_audio | ✅ |
| 5 | TestRender::test_render_without_audio | ✅ |
| 6 | TestCompositing::test_composite_basic | ✅ |
| 7 | TestCompositing::test_composite_invisible | ✅ |
| 8 | TestVideoMetadata::test_valid_metadata | ✅ |
| 9 | TestVideoMetadata::test_defaults | ✅ |
| 10 | TestSceneInfo::test_scene_creation | ✅ |
| 11 | TestSceneInfo::test_duration_consistency | ✅ |
| 12 | TestSelectionInput::test_point_selection | ✅ |
| 13 | TestSelectionInput::test_bbox_selection | ✅ |
| 14 | TestProjectData::test_create_minimal | ✅ |
| 15 | TestProjectData::test_roundtrip | ✅ |
| 16 | TestProjectData::test_schema_version | ✅ |
| 17 | TestProjectData::test_with_tracked_object | ✅ |
| 18 | TestComputeFrameMotion::test_visible_object | ✅ |
| 19 | TestComputeFrameMotion::test_empty_mask | ✅ |
| 20 | TestComputeFrameMotion::test_scale_relative_to_reference | ✅ |
| 21 | TestComputeFrameMotion::test_scale_different_reference | ✅ |
| 22 | TestComputeFrameMotion::test_rotation_computed | ✅ |
| 23 | TestComputeFrameMotion::test_opacity_fill_ratio | ✅ |
| 24 | TestComputeSceneMotion::test_basic_scene | ✅ |
| 25 | TestComputeSceneMotion::test_reference_from_selection_frame | ✅ |
| 26 | TestSmoothMotion::test_smoothing_reduces_noise | ✅ |
| 27 | TestSmoothMotion::test_preserves_length | ✅ |
| 28 | TestSmoothMotion::test_short_list_passthrough | ✅ |

## 4. Ruff Check

```
$ python -m ruff check app/ tests/
All checks passed!
```

## 5. SAM2 GPU Validation

```
$ python -c "from sam2.build_sam import build_sam2_video_predictor; ..."
Model loaded OK
CUDA: True, GPU: NVIDIA GeForce RTX 5070
init_state (10 frames): 0.625s
Point prompt: 0.106s
Propagation (10 frames): 1.927s
Peak VRAM: 1670.4 MB
```

## 6. Fixture Validation Commands

```bash
# Fixture A
python -m app.spike_runner --video output_m05/fixture_a/input.mp4 \
    --replacement examples/replacement.png --backend sam2 \
    --output-dir output_m05/fixture_a --point-x 320 --point-y 180

# Fixture B
python -m app.spike_runner --video output_m05/fixture_b/input.mp4 \
    --replacement examples/replacement.png --backend sam2 \
    --output-dir output_m05/fixture_b --point-x 50 --point-y 230

# Fixture C
python -m app.spike_runner --video output_m05/fixture_c/input.mp4 \
    --replacement examples/replacement.png --backend sam2 \
    --output-dir output_m05/fixture_c --point-x 325 --point-y 180
```

## 7. Tracking Metrics Summary

| Fixture | Frames | Tracked | Ratio | Target | Result |
|---------|-------:|--------:|------:|-------:|:------:|
| A (synthetic) | 210 | 210 | 100% | ≥90% | PASS |
| B (animation) | 180 | 180 | 100% | ≥80% | PASS |
| C (occlusion) | 150 | 150 | 100% | ≥80% | PASS WITH LIMITATION |

## 8. Schema Migration Test

```
$ python -c "
from app.schemas import migrate_v1_to_v2, ProjectData
v1 = {'version': '1.0.0', 'name': 'Test', 'source_video': '/tmp/test.mp4',
      'objects': [{'motion': {'frames': [{'frame_index': 0}]}}]}
v2 = migrate_v1_to_v2(v1)
assert v2['version'] == '2.0.0'
assert v2['objects'][0]['motion']['tracking_backend'] == 'unknown'
assert v2['objects'][0]['motion']['frames'][0]['confidence'] == 1.0
print('Migration OK')
"
Migration OK
```
