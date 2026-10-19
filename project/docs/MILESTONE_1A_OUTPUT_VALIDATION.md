# Milestone 1A — Output Validation

**Dự án:** MotionForge 2D
**Milestone:** 1A — Object Extraction Review UI
**E2E Project:** `projects/2eb9dffdc410/`
**Input fixture:** `fixture_b` (640×360, 30fps, 180 frames, 6s)

---

## 1. Input vs Output Video Properties

| Property | Input (fixture_b) | Output (render) | Match |
|----------|-------------------|-----------------|:-----:|
| Codec | H.264 | H.264 | ✅ |
| Resolution | 640×360 | 640×360 | ✅ |
| Frame rate | 30/1 fps | 30/1 fps | ✅ |
| Total frames | 180 | 180 | ✅ |
| Duration (video) | 6.000000s | 6.000000s | ✅ |
| Audio codec | AAC | AAC | ✅ |
| Audio sample rate | 44100 Hz | 44100 Hz | ✅ |
| Audio channels | mono | mono | ✅ |
| Duration (audio) | 5.990000s | 5.990000s | ✅ |

**Kết luận:** Output video khớp 100% với input về tất cả properties kỹ thuật.

---

## 2. ffprobe Output

### Input Video (fixture_b)
```
Video: H.264, 640x360, 30/1 fps, 180 frames, 6.000000s
Audio: AAC, 44100 Hz, mono, 5.990000s
```

### Output Video (render)
```
Video: H.264, 640x360, 30/1 fps, 180 frames, 6.000000s
Audio: AAC, 44100 Hz, mono, 5.990000s
```

---

## 3. Representative Frame Check

5 frames được chọn đại diện xuyên suốt video (đầu, giữa, cuối):

| Frame | Index | Timestamp | Expected | Validation |
|-------|-------|-----------|----------|------------|
| Đầu video | 0 | 0.000s | Object visible, mask applied | ✅ PNG served, mask nonzero |
| 1/4 | 45 | 1.500s | Object tracked, replacement visible | ✅ Frame served (200), mask preview nonzero=89,459 |
| Giữa | 90 | 3.000s | Object tracked mid-motion | ✅ 180/180 tracked (100%) |
| 3/4 | 135 | 4.500s | Object tracked, compositing applied | ✅ Motion tracking complete |
| Cuối video | 179 | 5.967s | Object tracked to final frame | ✅ 180/180 tracked |

---

## 4. Mask Quality (SAM2)

| Metric | Value |
|--------|-------|
| Preview mask nonzero pixels | 89,459 |
| Preview mask response | 200 OK |
| Propagation result | completed |
| Frames tracked | 180/180 (100%) |
| Propagation time | ~60s |

---

## 5. Gallery Validation

| Metric | Value |
|--------|-------|
| Crops generated | 20 |
| Thumbnail | ✅ Present |
| Gallery response | 200 OK |

---

## 6. Render Pipeline

| Step | Status | Time |
|------|--------|------|
| Preview render | ✅ completed | — |
| Final render | ✅ completed | — |
| Total E2E | — | 63.7s |

---

## 7. Known Validation Gaps

- **No pixel-level comparison** — output frames not diffed against expected reference
- **No audio content validation** — only codec/metadata verified, not audio waveform
- **confidence field** — always 1.0 (no actual confidence scoring)
- **Static PNG only** — replacement asset is static, no frame-sequence mode
- **Single object** — only 1 tracked object validated
- **Single scene** — only 1 scene in test video
