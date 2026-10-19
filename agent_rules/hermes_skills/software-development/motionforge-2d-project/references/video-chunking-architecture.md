# On-Demand Video Chunking — Implementation Reference

## Problem Statement
Original ingest extracted ALL frames from full video at upload time. For 10-min video (18K frames):
- 2-5 minute ingest time
- ~2GB disk usage
- Frontend timeout (90s → 300s still insufficient)
- Wasted resources if user only works on 1-2 scenes

## Solution Architecture

### Ingest Pipeline (new, fast)
```
1. probe_video() → metadata (~0.5s)
2. detect_scenes() → scene boundaries (~1-3s)
3. slice_scene_videos() → scene clip MP4s via FFmpeg -c copy (~1-2s)
4. extract_audio() per scene → AAC clips (~1s)
5. DONE — no frame extraction
```

### On-Demand Frame Extraction
```
User selects scene → POST /scenes/{id}/extract-frames
→ extract_frames_on_demand(clip_path, output_dir, format="jpg")
→ Returns cached frames if already extracted
→ New extraction: FFmpeg extracts from small clip (~0.2-1s)
```

## Key Implementation Details

### slice_scene_videos()
```python
def slice_scene_videos(self, video_path, scene_details, output_dir):
    """FFmpeg -c copy: stream copy, no re-encode, near-instant."""
    for sd in scene_details:
        clip_path = output_dir / f"scene_{sd.scene_id:03d}.mp4"
        duration = sd.end_time_sec - sd.start_time_sec
        cmd = [
            ffmpeg, "-y",
            "-ss", str(sd.start_time_sec),
            "-i", str(video_path),
            "-t", str(duration),
            "-c", "copy",  # KEY: no re-encode
            "-avoid_negative_ts", "make_zero",
            str(clip_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
```

### extract_frames_on_demand()
```python
def extract_frames_on_demand(self, scene_clip_path, output_dir, format="jpg"):
    """Extract from small clip, with caching."""
    output_dir.mkdir(parents=True, exist_ok=True)
    # Check cache first
    existing = sorted(output_dir.glob(f"frame_*.{format}"))
    if existing:
        return existing
    # Extract from scene clip (not full video!)
    cmd = [ffmpeg, "-y", "-i", str(scene_clip_path),
           "-vsync", "vfr", "-start_number", "0",
           str(output_dir / f"frame_%06d.{format}")]
    subprocess.run(cmd, capture_output=True, check=True, timeout=60)
    return sorted(output_dir.glob(f"frame_*.{format}"))
```

### IngestService changes
- Remove: frame extraction loop (`extract_frames` for each scene)
- Add: `chunk_svc.slice_scene_videos()` call
- Add: `svc.set_scene_details(scene_details)` to persist scene info
- Result: ingest completes in 3-5 seconds regardless of video length

### set_scene_details() in ProjectService
```python
def set_scene_details(self, scene_details):
    self.data.scene_details = scene_details
    # Backward compat: also populate scenes list
    self.data.scenes = [SceneInfo(...) for sd in scene_details]
    self.save()
```

## Performance Comparison

| Metric | Old (full extract) | New (on-demand) |
|--------|-------------------|-----------------|
| Ingest (10min video) | 2-5 minutes | 3-5 seconds |
| Disk usage | ~2GB (18K JPGs) | ~50MB (scene clips) |
| Frame extraction | All at once | Per-scene when needed |
| Frontend timeout | 90s → still fails | Never times out |

## BA/PM Validation
"Việc cố trích xuất hàng chục nghìn file hình ảnh của toàn bộ video ngay lúc mới upload vẫn sẽ tốn hàng gigabyte ổ đĩa, làm máy bị chậm và nguy cơ tràn VRAM/RAM rất cao."
— BA/PM architectural review, confirming on-demand is the correct architecture.
