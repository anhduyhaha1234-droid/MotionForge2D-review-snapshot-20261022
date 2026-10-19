# MotionForge 2D — Milestone 0 Spike Report

## 1. What Was Completed

Full end-to-end vertical spike demonstrating:
- Video metadata extraction via FFmpeg/ffprobe
- Scene boundary detection via PySceneDetect
- Audio extraction from source video
- Frame extraction per scene
- Object selection (auto-detect centroid)
- Object segmentation using OpenCV GrabCut (contour backend)
- Mask propagation across frames using template matching
- Motion extraction: centroid, bounding box, scale, rotation, opacity, visibility
- Object replacement with PNG sprite via alpha compositing
- Video rendering with original audio preserved
- Project JSON serialization (version 1.0.0)
- Benchmark logging (time, RAM, VRAM)

## 2. Files Created

```
MotionForge2D/
├── pyproject.toml                    # Python project config
├── README.md                         # Full setup and usage guide
├── THIRD_PARTY.md                    # License audit for all dependencies
├── app/
│   ├── __init__.py
│   ├── config.py                     # Global config (paths, SAM2 settings)
│   ├── spike_runner.py               # End-to-end pipeline orchestrator
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── segmentation.py           # SAM2 + OpenCV contour adapters
│   ├── schemas/
│   │   └── __init__.py               # Pydantic data models
│   └── services/
│       ├── __init__.py
│       ├── video_probe.py            # FFmpeg metadata extraction
│       ├── scene_detection.py        # PySceneDetect wrapper
│       ├── frame_extraction.py       # Frame extraction via FFmpeg
│       ├── motion_extraction.py      # Motion vectors from masks
│       ├── compositing.py            # Object replacement + debug overlays
│       ├── render.py                 # FFmpeg reassembly with audio
│       └── project_service.py        # Project persistence
├── tests/
│   ├── conftest.py                   # Fixtures
│   ├── test_schema.py                # 21 unit tests
│   └── test_integration.py           # 7 integration tests
├── scripts/
│   ├── setup.sh                      # Full environment setup
│   ├── download_models.sh            # SAM 2.1 checkpoint download
│   └── run_spike.sh                  # Run the spike
├── docs/
│   ├── ARCHITECTURE.md               # System architecture
│   ├── MILESTONES.md                 # Development milestones
│   └── SPIKE_REPORT.md               # This report
├── examples/
│   ├── example_project.json          # Sample project file
│   ├── test_video.mp4                # Test video (3s, 320x240, with audio)
│   └── replacement.png               # Test replacement sprite
├── output/
│   ├── project.json                  # Generated project (v1.0.0)
│   ├── motion_data.json              # Per-frame motion vectors
│   ├── benchmark.json                # Performance metrics
│   ├── audio/original_audio.aac      # Extracted audio
│   ├── frames/scene_0/               # 90 extracted frames
│   ├── masks/scene_0/                # Binary masks
│   ├── debug/                        # Mask overlay visualizations
│   └── renders/
│       └── scene_0_output.mp4        # Final composited video
└── models_checkpoints/               # (empty, SAM2 checkpoint not downloaded)
```

## 3. How to Run

```bash
cd MotionForge2D

# Run unit tests
python -m pytest tests/test_schema.py -v

# Run integration tests
python -m pytest tests/test_integration.py -v -m integration

# Run the spike
python -m app.spike_runner \
    --video examples/test_video.mp4 \
    --replacement examples/replacement.png \
    --scene 0 \
    --backend contour \
    --output-dir output
```

## 4. Tests Run and Results

### Unit Tests (21/21 passed)
| Test | Result |
|------|--------|
| TestVideoMetadata::test_valid_metadata | ✅ |
| TestVideoMetadata::test_defaults | ✅ |
| TestSceneInfo::test_scene_creation | ✅ |
| TestSceneInfo::test_duration_consistency | ✅ |
| TestSelectionInput::test_point_selection | ✅ |
| TestSelectionInput::test_bbox_selection | ✅ |
| TestProjectData::test_create_minimal | ✅ |
| TestProjectData::test_roundtrip | ✅ |
| TestProjectData::test_schema_version | ✅ |
| TestProjectData::test_with_tracked_object | ✅ |
| TestComputeFrameMotion::test_visible_object | ✅ |
| TestComputeFrameMotion::test_empty_mask | ✅ |
| TestComputeFrameMotion::test_scale_relative_to_reference | ✅ |
| TestComputeFrameMotion::test_scale_different_reference | ✅ |
| TestComputeFrameMotion::test_rotation_computed | ✅ |
| TestComputeFrameMotion::test_opacity_fill_ratio | ✅ |
| TestComputeSceneMotion::test_basic_scene | ✅ |
| TestComputeSceneMotion::test_reference_from_selection_frame | ✅ |
| TestSmoothMotion::test_smoothing_reduces_noise | ✅ |
| TestSmoothMotion::test_preserves_length | ✅ |
| TestSmoothMotion::test_short_list_passthrough | ✅ |

### Integration Tests (7/7 passed)
| Test | Result |
|------|--------|
| TestVideoProbe::test_probe_metadata | ✅ |
| TestVideoProbe::test_probe_nonexistent | ✅ |
| TestVideoProbe::test_extract_audio | ✅ |
| TestRender::test_render_with_audio | ✅ |
| TestRender::test_render_without_audio | ✅ |
| TestCompositing::test_composite_basic | ✅ |
| TestCompositing::test_composite_invisible | ✅ |

### Lint
- Ruff: 15 remaining warnings (all TC001/TC002/TC003 = move imports to type-checking blocks, non-blocking)
- 0 errors

## 5. Output Artifacts

| Artifact | Path | Size |
|----------|------|------|
| Output video | output/renders/scene_0_output.mp4 | 54 KB |
| Project JSON | output/project.json | 42 KB |
| Motion data | output/motion_data.json | 32 KB |
| Benchmark | output/benchmark.json | 442 B |
| Debug overlays | output/debug/ | 12 files |
| Mask images | output/masks/scene_0/ | 10 files |

**Output video properties:**
- Codec: H.264
- FPS: 30 (matches original)
- Duration: 3.0s (matches original)
- Frames: 90 (matches original)
- Audio: AAC preserved

## 6. Benchmark

| Metric | Value |
|--------|-------|
| Total time | 0.89s |
| Peak RAM | 22.8 MB |
| GPU peak | 0.0 MB (CPU-only contour backend) |
| Throughput | 101.6 fps |
| Frames processed | 90 |

### Timing Breakdown
| Step | Time |
|------|------|
| Video probe | 0.028s |
| Scene detection | 0.062s |
| Audio extraction | 0.029s |
| Frame extraction | 0.055s |
| Mask propagation | 0.107s |
| Motion extraction | 0.007s |
| Compositing | 0.065s |
| Render | 0.493s |

## 7. Licenses Checked

| Dependency | License | Commercial OK |
|------------|---------|---------------|
| SAM 2.1 | Apache 2.0 | ✅ |
| PyTorch 2.11.0 | BSD-3-Clause | ✅ |
| OpenCV 5.0 | Apache 2.0 | ✅ |
| FastAPI | MIT | ✅ |
| Pydantic v2 | MIT | ✅ |
| PySceneDetect | BSD-3-Clause | ✅ |
| FFmpeg 8.1.2 | LGPL-2.1+ (GPL build) | ✅ (with GPL compliance) |
| NumPy | BSD-3-Clause | ✅ |

## 8. Limitations

1. **Segmentation backend:** Only OpenCV contour/GrabCut tested in spike. SAM 2.1 adapter code is complete but requires model checkpoint download (~890MB) and GPU.
2. **Template matching propagation:** The contour fallback uses simple template matching, which loses accuracy for scale/rotation changes.
3. **No frontend yet:** Spike is CLI-only. UI comes in Milestone 2.
4. **Single object:** Only one tracked object per scene in spike. Multi-object in Milestone 3.
5. **No undo/redo:** State management comes in Milestone 5.
6. **FFmpeg frame extraction uses `select` filter:** Works but not optimal for very long videos (should use segment-based extraction).

## 9. Blockers

**None.** The spike completed successfully end-to-end.

**Note:** RTX 5070 (sm_120) requires PyTorch 2.11+ with cu128. PyTorch 2.6 and earlier do NOT support this GPU. SAM 2.1 model checkpoint not downloaded in this spike (890MB); download script is ready in `scripts/download_models.sh`.

## 10. Next Milestone Proposal

**Milestone 1: Backend API & Project Management**
- FastAPI REST endpoints for all services
- Background job queue with progress tracking
- SQLite database for project persistence
- Video upload endpoint
- Full API documentation (OpenAPI)

Estimated effort: 2-3 days. No blockers identified.
