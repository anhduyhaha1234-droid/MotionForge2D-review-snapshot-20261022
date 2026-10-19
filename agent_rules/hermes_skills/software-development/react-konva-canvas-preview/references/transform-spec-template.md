# Transform Specification Template

This is a reusable template for defining the compositing transform pipeline between frontend (Konva) and backend (OpenCV/FFmpeg). Both sides must produce identical positioning.

## Coordinate Systems

| System | Origin | Units | Range |
|--------|--------|-------|-------|
| Source Video | top-left | pixels | [0, width) × [0, height) |
| Normalized | top-left | ratio | [0.0, 1.0] × [0.0, 1.0] |
| Canvas | top-left | pixels | viewport-scaled |

Conversion: `canvas_x = source_x * scale + offset_x`

## Replacement Config Schema

```typescript
interface ReplacementConfig {
  mode: "none" | "static_asset" | "frame_sequence" | "keyframe_assets";
  asset_path: string | null;
  anchor: { x: number; y: number };     // 0-1, relative within asset bbox
  offset: { x: number; y: number };      // normalized, 0.5 = half frame
  scale: number;                          // 0.01-10.0, multiplier
  rotation_offset_deg: number;            // -180 to 180
  opacity: number;                        // 0.0-1.0
  fit_mode: "contain" | "cover" | "stretch";
  clip_mode: "asset_alpha" | "original_mask" | "intersection";
}
```

## Transform Pipeline (ORDER MATTERS)

```
1. Resolve asset natural size: (rw, rh) = replacement_image.dimensions
2. Target size from fit mode:
   - contain: ratio = min(bboxW/rw, bboxH/rh), target = (rw*ratio, rh*ratio)
   - cover:   ratio = max(bboxW/rw, bboxH/rh), target = (rw*ratio, rh*ratio)
   - stretch: target = (bboxW, bboxH)
3. Apply scale: final = target * scale
4. Anchor offset: anchor_px = final * anchor
5. Position: pos = centroid - anchor_px + offset * frame_size
6. Rotation: total = tracked_rotation + rotation_offset
7. Clip mode: determines alpha composition
```

## Clip Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `asset_alpha` | Use PNG's own alpha channel | Replacement has different shape |
| `original_mask` | Clip to tracked object's mask | Preserve original silhouette |
| `intersection` | Both must agree on visibility | Partial conformance |

### Frontend implementation
- `asset_alpha`: normal draw (`source-over`)
- `original_mask`: `destination-in` composite
- `intersection`: `source-in` composite

### Backend implementation (NumPy)
```python
if clip_mode == "asset_alpha":
    alpha = replacement_alpha * opacity
elif clip_mode == "original_mask":
    alpha = original_mask * opacity
elif clip_mode == "intersection":
    alpha = np.minimum(replacement_alpha, original_mask) * opacity
```

## Agreement Contract

Both frontend and backend must:
1. Store clip_mode in the replacement config
2. Use identical transform math
3. Validate clip_mode before processing
4. Pass tolerance test: ≤2% per-pixel MSE between frontend canvas export and backend render

## Extension Points

- **frame_sequence**: Per-frame replacement assets. Schema: `{"mode": "frame_sequence", "frames": {"0": "path.png"}}`
- **keyframe_assets**: Keyframes with interpolation. Schema: `{"mode": "keyframe_assets", "keyframes": [{"frame": 0, "asset": "a.png"}]}`
- **background cleaning**: clean_plate, user_background, or inpainting modes
