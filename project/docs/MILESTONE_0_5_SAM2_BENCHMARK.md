# Milestone 0.5 — SAM 2.1 Benchmark

Ngày tạo: 2026-07-29
GPU: NVIDIA GeForce RTX 5070 (12GB VRAM, sm_120, CUDA 12.8)
Model: sam2.1_hiera_large

---

## Model Information

| Attribute | Value |
|-----------|-------|
| Model | SAM 2.1 Hiera Large |
| Checkpoint | `models_checkpoints/sam2.1_hiera_large.pt` |
| Size | 898,083,611 bytes (856.5 MB) |
| SHA-256 | `2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318` |
| Source | https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt |
| License | Apache 2.0 (Meta AI) |
| Download date | 2026-07-29 |
| Config | `configs/sam2.1/sam2.1_hiera_l.yaml` |

---

## GPU Validation

| Test | Result |
|------|--------|
| CUDA available | ✅ True |
| Model load | ✅ 1.622s |
| VRAM after load | 1000.9 MB |
| init_state (10 frames) | ✅ 0.625s |
| Point prompt | ✅ 0.106s |
| Mask logits shape | [1, 1, 240, 320] |
| Propagation (10 frames) | ✅ 1.927s (5.2 fps) |
| Peak VRAM total | 1670.4 MB |
| Cleanup (cuda.empty_cache) | ✅ |
| `_C` warning | Present (cosmetic, no functional impact) |

---

## Benchmark — Per Fixture

### Fixture A (Synthetic Motion)

| Metric | Value |
|--------|-------|
| Resolution | 640×360 |
| FPS | 30 |
| Frame count | 210 |
| Duration | 7.0s |
| Selection | Point (320, 180) at frame 105 |
| Model load time | ~3s (included in total) |
| Propagation time | ~62s (forward105 frames + backward105 frames) |
| Total time | 67.16s |
| Throughput | 3.1 fps |
| Peak VRAM | 4225.9 MB |
| Peak RAM | 200.2 MB |

### Fixture B (Simulated 2D Animation)

| Metric | Value |
|--------|-------|
| Resolution | 640×360 |
| FPS | 30 |
| Frame count | 180 |
| Duration | 6.0s |
| Selection | Point (50, 230) at frame 90 |
| Total time | 57.66s |
| Throughput | 3.1 fps |
| Peak VRAM | 3843.3 MB |
| Peak RAM | 173.9 MB |

### Fixture C (Occlusion)

| Metric | Value |
|--------|-------|
| Resolution | 640×360 |
| FPS | 30 |
| Frame count | 150 |
| Duration | 5.0s |
| Selection | Point (325, 180) at frame 75 |
| Total time | 48.91s |
| Throughput | 3.1 fps |
| Peak VRAM | 3460.8 MB |
| Peak RAM | 147.4 MB |

---

## VRAM Scaling

| Resolution | Frames | Peak VRAM |
|-----------|--------|-----------|
| 320×240 | 10 | 1670 MB |
| 640×360 | 150 | 3461 MB |
| 640×360 | 180 | 3843 MB |
| 640×360 | 210 | 4226 MB |

VRAM scales with frame count (video state stored in GPU memory).

---

## Known Issues

1. `_C` module not compiled: `cannot import name '_C' from 'sam2'`. This disables the `fill_holes_in_mask_scores` post-processing step. Impact: minor (masks may have small holes). Fix: build SAM2 from source with CUDA extensions.

2. Throughput is ~3.1 fps for 640×360 on RTX 5070. This is acceptable for offline processing but not real-time.

3. VRAM usage scales with total frame count. For very long videos (>1000 frames), may need to implement chunked processing.
