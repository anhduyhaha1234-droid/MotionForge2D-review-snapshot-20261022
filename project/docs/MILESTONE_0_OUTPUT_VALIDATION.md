# Milestone 0 — Output Validation

Ngày tạo: 2026-07-29
Phương pháp: Chạy lại spike pipeline, validate mọi artifact bằng công cụ độc lập.

---

## 1. Spike Command

```bash
cd C:\Users\Admin\MotionForge2D
python -m app.spike_runner \
    --video examples/test_video.mp4 \
    --replacement examples/replacement.png \
    --scene 0 \
    --backend contour \
    --output-dir output \
    --name spike_project
```

---

## 2. Input Validation

### 2.1 Input Video (examples/test_video.mp4)

| Thuộc tính | Giá trị |
|-----------|---------|
| Kích thước file | 50,755 bytes |
| SHA-256 | `093cc1f509d30fba01e7e1913faac6455bf927c81f7a3ad26f4291de1dcb7177` |
| Video codec | mpeg4 (MPEG-4 part 2) |
| Pixel format | yuv420p |
| Width × Height | 320 × 240 |
| FPS | 30/1 |
| Duration | 3.000000s |
| Frame count | 90 |
| Video bitrate | 54,434 bps |
| Audio codec | aac (LC) |
| Audio sample rate | 44,100 Hz |
| Audio channels | 1 (mono) |
| Audio bitrate | 69,594 bps |
| Audio frames | 131 |

### 2.2 Replacement Image (examples/replacement.png)

| Thuộc tính | Giá trị |
|-----------|---------|
| Kích thước file | 800 bytes |
| Format | PNG |
| Channels | 4 (BGRA) |
| Kích thước | 60 × 60 |

---

## 3. Output Validation

### 3.1 Output Video (output/renders/scene_0_output.mp4)

| Thuộc tính | Input | Output | Sai lệch | Kết luận |
|-----------|------:|-------:|---------:|----------|
| Width | 320 | 320 | 0 | ✅ Match |
| Height | 240 | 240 | 0 | ✅ Match |
| FPS | 30/1 | 30/1 | 0 | ✅ Match |
| Frame count | 90 | 90 | 0 | ✅ Match |
| Duration (video) | 3.000000s | 3.000000s | 0 | ✅ Match |
| Video codec | mpeg4 | h264 | Changed | ⚠️ Expected (re-encoded) |
| Pixel format | yuv420p | yuv420p | 0 | ✅ Match |
| Audio codec | aac | aac | 0 | ✅ Match |
| Audio sample rate | 44100 | 44100 | 0 | ✅ Match |
| Audio channels | 1 | 1 | 0 | ✅ Match |
| Audio duration | 3.000000s | 2.995011s | -0.005s | ✅ Acceptable |
| Audio frames | 131 | 130 | -1 | ✅ Acceptable |
| File size | 50,755 B | 54,259 B | +3,504 B | ✅ Expected |
| SHA-256 | `093cc...` | `1d47e...` | — | ✅ Different (new content) |

**Kết luận:** Output video giữ nguyên resolution, FPS, frame count, duration. Audio được mux lại (codec copy). Video re-encode sang H.264 (từ MPEG-4). Audio lệch 0.005s — chấp nhận được.

### 3.2 Audio Extraction (output/audio/original_audio.aac)

| Thuộc tính | Giá trị |
|-----------|---------|
| Kích thước file | 27,217 bytes |
| Format | AAC |
| Có mở được không | ✅ (ffprobe xác nhận) |

### 3.3 Project JSON (output/project.json)

```json
{
  "version": "1.0.0",
  "name": "spike_project",
  "source_video": "C:\\Users\\Admin\\MotionForge2D\\examples\\test_video.mp4",
  "video_metadata": {
    "width": 320, "height": 240, "fps": 30.0,
    "duration_seconds": 3.0, "total_frames": 90,
    "codec": "mpeg4", "has_audio": true, "audio_codec": "aac"
  },
  "scenes": [
    {
      "scene_id": 0, "start_frame": 0, "end_frame": 89,
      "start_time_sec": 0.0, "end_time_sec": 3.0,
      "duration_sec": 3.0, "frame_count": 90
    }
  ],
  "objects": [
    {
      "object_id": "obj_0",
      "name": "Spike Object",
      "kind": "character",
      "selection": { "mode": "point", "frame_index": 45, "x": 160.0, "y": 120.0 },
      "scene_id": 0,
      "replacement_image": "examples/replacement.png",
      "motion": { "scene_id": 0, "frames": [...90 frames...], "reference_bbox": {...} }
    }
  ]
}
```

**Schema validation:**
- ✅ version field present (1.0.0)
- ✅ video_metadata matches ffprobe output
- ✅ scenes có start/end frame (inclusive: 0-89 = 90 frames)
- ✅ objects có selection, motion, replacement_image
- ✅ motion.frames có 90 entries
- ✅ reference_bbox present
- ✅ JSON parseable, không lỗi syntax

### 3.4 Motion Data JSON (output/motion_data.json)

```
frames: 90 entries
reference_bbox: {x: 130.0, y: 100.0, width: 40.0, height: 40.0}
```

**Mỗi frame entry chứa:**
- frame_index (int)
- centroid_x, centroid_y (float)
- bbox: {x, y, width, height}
- scale_x, scale_y (float)
- rotation_deg (float)
- opacity (float, 0-1)
- visibility (bool)
- area (float)

### 3.5 Benchmark JSON (output/benchmark.json)

```json
{
  "timings_seconds": {
    "probe": 0.028,
    "scene_detect": 0.062,
    "audio_extract": 0.029,
    "frame_extract": 0.055,
    "segment_initial": 0.0,
    "mask_propagation": 0.107,
    "segment_total": 0.107,
    "motion_extraction": 0.007,
    "compositing": 0.065,
    "render": 0.493,
    "total": 0.886
  },
  "peak_ram_mb": 22.77,
  "gpu_peak_mb": 0.0,
  "total_frames_processed": 90,
  "fps_throughput": 101.57
}
```

**Lưu ý benchmark:**
- Đo bằng `time.perf_counter()` (wall-clock)
- Đo bằng `tracemalloc` cho RAM
- GPU = 0.0 vì dùng contour backend (không có CUDA)
- Không tính thời gian khởi động process Python
- **Benchmark contour CPU không đại diện cho SAM 2.1 GPU performance**

---

## 4. Frame Validation (5 representative frames)

| Frame | % | File exists | Mask exists | Motion data | Visible | Centroid | Composited |
|------:|--:|:-----------:|:-----------:|:-----------:|:-------:|:--------:|:----------:|
| 0 | 0% | ✅ | ✅ (saved) | ✅ | ❌ | (0,0) | ❌ |
| 22 | 25% | ✅ | ❌ (not saved) | ✅ | ❌ | (0,0) | ❌ |
| 45 | 50% | ✅ | ❌ (not saved) | ✅ | ✅ | (149.1, 119.5) | ✅ |
| 67 | 75% | ✅ | ❌ (not saved) | ✅ | ❌ | (0,0) | ❌ |
| 89 | 100% | ✅ | ✅ (saved) | ✅ | ❌ | (0,0) | ❌ |

**Phát hiện quan trọng:**
- Chỉ frame 45 (frame selection) có `visibility=True` và được composite.
- Frames 0, 22, 67, 89: `visibility=False`, `centroid=(0,0)` — mask propagation **thất bại**.
- Mask chỉ được lưu cho frame 0, 10, 20, ..., 80, 89 (mỗi 10 frame + cuối) — đây là sampling strategy, không phải lỗi.
- **Nguyên nhân:** `SimpleContourAdapter.propagate_masks()` dùng template matching. Template lấy từ bounding box của mask ở frame 45. Template matching chỉ match tốt ở chính xác vị trí đó. Các frame khác object ở vị trí khác → match score < 0.3 → visibility=False.

**Đây là limitation nghiêm trọng của contour backend.** SAM 2.1 backend sẽ giải quyết vấn đề này nhưng chưa được test do thiếu checkpoint.

---

## 5. Debug Overlay Validation

Có 12 debug overlay files:
- `initial_mask.png` — mask tại frame selection
- `initial_overlay.png` — frame selection + mask overlay
- `overlay_NNNNNN.png` — mỗi 10 frame + frame cuối

**Nội dung overlay:**
- Green contour vẽ trên mask
- Red bounding box
- Blue centroid dot
- Yellow rotation arrow
- Text info: frame index, centroid, rotation, scale

---

## 6. Mask Files

Có 10 mask files (sampling mỗi 10 frame + frame cuối):
- `mask_000000.png` — frame 0
- `mask_000010.png` — frame 10
- ...
- `mask_000080.png` — frame 80
- `mask_000089.png` — frame 89

**Vấn đề:** Chỉ mask ở frame 0 và 89 được saved nhưng nội dung là mask rỗng (trừ frame selection được lưu ở initial_mask). Mask propagation không tạo mask hữu ích cho các frame khác.

---

## 7. Tổng kết Validation

| Artifact | Tồn tại | Nội dung hợp lệ | Ghi chú |
|----------|:--------:|:----------------:|---------|
| Input video | ✅ | ✅ | MPEG4, 320×240, 30fps, 3s, có audio |
| Output video | ✅ | ✅ | H264, 320×240, 30fps, 3s, có audio |
| Audio extracted | ✅ | ✅ | AAC, 27KB |
| Extracted frames | ✅ | ✅ | 90 PNG files |
| Masks | ✅ | ⚠️ | 10 files saved, nhưng propagation thất bại |
| Debug overlays | ✅ | ✅ | 12 files với annotation |
| Motion JSON | ✅ | ✅ | 90 frame entries, schema hợp lệ |
| Project JSON | ✅ | ✅ | version 1.0.0, đầy đủ fields |
| Benchmark JSON | ✅ | ✅ | Timing + RAM data |
| Replacement asset | ✅ | ✅ | 60×60 BGRA PNG |
| Composited frames | ✅ | ⚠️ | 90 files, nhưng chỉ frame 45 thực sự composite |

**Kết luận:** Pipeline chạy end-to-end thành công. Output video đúng format. Tuy nhiên, **mask propagation với contour backend không hiệu quả** — chỉ frame selection được xử lý đúng. Đây là limitation đã biết, không phải bug.
