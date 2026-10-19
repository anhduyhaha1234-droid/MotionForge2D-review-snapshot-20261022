# SAM 2.1 Video Predictor API Reference

Verified on SAM-2 v1.0, PyTorch 2.11.0+cu128, RTX 5070.

## Installation

```bash
pip install git+https://github.com/facebookresearch/sam2.git
# Package: SAM-2, import: sam2
# License: Apache 2.0
```

## Checkpoint Download

```bash
# sam2.1_hiera_large (recommended)
URL="https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
curl -L -o models_checkpoints/sam2.1_hiera_large.pt "$URL"
# Size: 898,083,611 bytes (856.5 MB)
# SHA-256: 2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318
```

All checkpoints released under Apache 2.0 by Meta AI. Store in `models_checkpoints/` (gitignored). Script: `scripts/download_models.sh`.

## Model Loading

```python
from sam2.build_sam import build_sam2_video_predictor

predictor = build_sam2_video_predictor(
    config_file="configs/sam2.1/sam2.1_hiera_l.yaml",  # Relative to sam2/configs/
    ckpt_path="models_checkpoints/sam2.1_hiera_large.pt",
    device="cuda",
)
```

**Config path:** Must be relative to the `sam2/configs/` directory. Valid configs:
- `configs/sam2.1/sam2.1_hiera_l.yaml` (large, recommended)
- `configs/sam2.1/sam2.1_hiera_b+.yaml` (base plus)
- `configs/sam2.1/sam2.1_hiera_s.yaml` (small)
- `configs/sam2.1/sam2.1_hiera_t.yaml` (tiny)

Config name without `.yaml` extension also works (Hydra resolves it).

## init_state

```python
inference_state = predictor.init_state(
    video_path="/path/to/frame_directory/",  # Directory of JPEG/PNG frames
    offload_video_to_cpu=False,              # Keep frames in GPU memory
    offload_state_to_cpu=False,
)
```

**CRITICAL:** `video_path` must be a **directory containing numbered frame images** (e.g. `000000.jpg`, `000001.jpg`, ...). NOT a video file. NOT None.

Frames are loaded in sorted filename order. Use zero-padded 6-digit names.

## Adding Prompts

### Point prompt

```python
_, obj_ids, mask_logits = predictor.add_new_points_or_box(
    inference_state=state,
    frame_idx=0,           # Which frame to prompt on
    obj_id=0,              # Object ID (integer)
    points=np.array([[x, y]], dtype=np.float32),  # (N, 2) array
    labels=np.array([1], dtype=np.int32),           # 1=positive, 0=negative
    # box=None,            # Alternative: bounding box [x1, y1, x2, y2]
)
```

### Box prompt

```python
_, obj_ids, mask_logits = predictor.add_new_points_or_box(
    inference_state=state,
    frame_idx=0,
    obj_id=0,
    box=np.array([[x1, y1, x2, y2]], dtype=np.float32),  # (1, 4) array
)
```

### Mask prompt

```python
_, obj_ids, mask_logits = predictor.add_new_mask(
    inference_state=state,
    frame_idx=0,
    obj_id=0,
    mask=mask_tensor,  # MUST be 2D (H, W), float32, values 0.0/1.0
)
```

**CRITICAL:** `add_new_mask` asserts `mask.dim() == 2`. Do NOT unsqueeze to 4D.

```python
# WRONG — causes AssertionError
mask_tensor = torch.from_numpy(mask).unsqueeze(0).unsqueeze(0)  # (1,1,H,W) ← FAILS

# CORRECT
mask_tensor = torch.from_numpy((mask > 127).astype(np.float32))  # (H, W) ← WORKS
```

## Propagation

```python
# Forward propagation (from start_frame_idx to end)
for frame_idx, obj_ids, mask_logits in predictor.propagate_in_video(
    inference_state=state,
    start_frame_idx=45,       # Start from this frame
    max_frame_num_to_track=None,  # Track to end
    reverse=False,
):
    # mask_logits shape: (num_objects, 1, H, W) or similar
    mask = (mask_logits[0] > 0.0).cpu().numpy().squeeze()
    masks[frame_idx] = (mask * 255).astype(np.uint8)

# Backward propagation (from start_frame_idx to beginning)
for frame_idx, obj_ids, mask_logits in predictor.propagate_in_video(
    inference_state=state,
    start_frame_idx=45,
    reverse=True,
):
    mask = (mask_logits[0] > 0.0).cpu().numpy().squeeze()
    masks[frame_idx] = (mask * 255).astype(np.uint8)
```

**Key behaviors:**
- `propagate_in_video` yields tuples: `(frame_idx, obj_ids, mask_logits)`
- Frame indices are absolute (matching the frame directory ordering)
- With `start_frame_idx=45, reverse=False`: frames 45, 46, 47, ...
- With `start_frame_idx=45, reverse=True`: frames 45, 44, 43, ...
- Frame 45 appears in BOTH calls (the prompt frame)

## Cleanup

```python
predictor.reset_state(inference_state)
# Also clean temp frame directory
import shutil
shutil.rmtree(temp_dir, ignore_errors=True)
# Release GPU memory
torch.cuda.empty_cache()
```

## Benchmark (RTX 5070, 12GB VRAM)

| Operation | Time | VRAM |
|-----------|------|------|
| Model load | 1.6s | 1001 MB |
| init_state (10 frames, 320×240) | 0.6s | — |
| init_state (210 frames, 640×360) | 2.5s | — |
| Point prompt | 0.1s | — |
| Propagation (90 frames, 320×240) | 23s | 2694 MB |
| Propagation (210 frames, 640×360) | 62s | 4226 MB |
| Throughput | ~3.1 fps | — |

VRAM scales with frame count (video state stored in GPU). For >500 frames, consider chunked processing.

## Known Issues

1. **`_C` import warning:** `cannot import name '_C' from 'sam2'` — post-processing step (`fill_holes_in_mask_scores`) is skipped. Impact: minor (masks may have small holes). Fix: build SAM2 from source with CUDA extensions.

2. **Occlusion:** SAM2 does not detect occlusion. During hidden frames, the mask propagates onto the occluder. This is expected — SAM2 does visual propagation, not semantic reasoning.

3. **No confidence score:** `mask_logits` values can be thresholded at different levels for pseudo-confidence, but SAM2 doesn't provide a per-frame confidence metric.

## Adapter Pattern

```python
class SAM2Adapter(SegmentationAdapter):
    def __init__(self, model_cfg, checkpoint, device="cuda"):
        self._predictor = None
        self._tmp_dir = None

    def _ensure_model(self):
        if self._predictor is None:
            self._predictor = build_sam2_video_predictor(...)

    def _frames_to_dir(self, frames):
        """Write frames to temp directory for init_state."""
        self._tmp_dir = tempfile.mkdtemp(prefix="sam2_")
        for i, frame in enumerate(frames):
            cv2.imwrite(f"{self._tmp_dir}/{i:06d}.jpg", frame)
        return self._tmp_dir

    def propagate_masks(self, frames, initial_mask, sel_idx):
        frame_dir = self._frames_to_dir(frames)
        state = self._predictor.init_state(video_path=frame_dir)
        # Add mask prompt (2D tensor!)
        mask_tensor = torch.from_numpy((initial_mask > 127).astype(np.float32))
        self._predictor.add_new_mask(state, sel_idx, 0, mask_tensor)
        # Forward
        for idx, _, logits in self._predictor.propagate_in_video(state, start_frame_idx=sel_idx):
            masks[idx] = (logits[0] > 0.0).cpu().numpy().squeeze()
        # Backward
        if sel_idx > 0:
            for idx, _, logits in self._predictor.propagate_in_video(state, start_frame_idx=sel_idx, reverse=True):
                if masks[idx] is None:
                    masks[idx] = (logits[0] > 0.0).cpu().numpy().squeeze()
        self._predictor.reset_state(state)
        return masks
```
