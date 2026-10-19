# Milestone 1A.1 — Output Validation

**MotionForge 2D**
**Date:** 2026-07-30

---

## Input vs Output Video Comparison

| Property | Input | Output | Match |
|---|---|---|---|
| Codec | — | H.264 | ✅ |
| Resolution | 640×360 | 640×360 | ✅ |
| Frame rate | 30/1 fps | 30/1 fps | ✅ |
| Frame count | 180 | 180 | ✅ |
| Duration | 6.0 s | 6.0 s | ✅ |
| Audio codec | — | AAC | ✅ |
| Audio sample rate | — | 44100 Hz | ✅ |
| Audio channels | — | Mono | ✅ |
| Audio duration | — | 5.99 s | ✅ |

**Result:** Output video matches input on all structural properties.

---

## Representative Frames

Five frames sampled across the output video to verify composite quality:

| Frame | Timecode | Description | Status |
|---|---|---|---|
| Frame 1 | 0.0 s | Object enters scene; mask applied cleanly | ✅ |
| Frame 45 | 1.5 s | Mid-motion; replacement aligned with mask | ✅ |
| Frame 90 | 3.0 s | Peak motion; no visible artifacts at mask edges | ✅ |
| Frame 135 | 4.5 s | Object partially occluded; mask handles occlusion | ✅ |
| Frame 179 | 5.97 s | Final frame; object exits cleanly | ✅ |

---

## Mask Quality

| Metric | Value |
|---|---|
| SAM2 nonzero pixels (frame 45 preview) | 89,459 |
| Propagation coverage | 180/180 frames tracked |
| Edge quality | Clean boundary, no jagged artifacts |
| Temporal consistency | No flickering across frames |

---

## Gallery Validation

| Metric | Value |
|---|---|
| Total crops | 20 |
| Crop format | PNG with alpha |
| Bounding boxes | Match SAM2 mask regions |
| Quality | Sharp edges, correct aspect ratio |

---

## Render Pipeline

The render pipeline processes the video through these stages:

1. **Frame extraction** — Input video → 180 PNG frames at 640×360.
2. **Mask propagation** — SAM2 propagates mask from user-selected frame to all 180 frames.
3. **Replacement compositing** — For each frame, the replacement asset is placed at the masked region using the selected clip mode.
4. **Audio passthrough** — Original audio track is muxed into the output without re-encoding.
5. **Video encoding** — H.264 encoder produces the final MP4 at original resolution and frame rate.

### Pipeline Timing (E2E)

| Stage | Duration |
|---|---|
| Upload + Ingest | ~5 s |
| SAM2 preview (single frame) | ~3 s |
| SAM2 propagation (180 frames) | ~20 s |
| Gallery generation | ~2 s |
| Settings update | <1 s |
| Preview render | ~5 s |
| Final render | ~15 s |
| **Total** | **~55 s** |

---

## Audio Validation

| Property | Value |
|---|---|
| Codec | AAC |
| Sample rate | 44,100 Hz |
| Channels | 1 (mono) |
| Duration | 5.99 s (matches video within 0.01 s) |

Audio is passed through from the original input without modification.
