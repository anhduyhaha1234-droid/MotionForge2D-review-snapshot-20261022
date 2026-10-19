# Video Chunking Architecture

**Date:** 2026-07-31  
**Status:** Implemented

---

## Problem

The original ingest pipeline extracted ALL frames from the entire video at upload time. For a 10-minute video at 30fps (18,000 frames), this:
- Takes 2-5 minutes
- Uses gigabytes of disk space
- Causes frontend timeout (was 90s, then 300s)
- Wastes resources if user only works on 1-2 scenes

## Solution: On-Demand Video Chunking

### Architecture

```
[Upload Video] 
       │
       ▼
[Fast Ingest (~3-5s)]
  1. Probe metadata (ffprobe)
  2. Detect scene boundaries (PySceneDetect)
  3. Slice video into scene clips (FFmpeg -c copy, instant)
  4. Extract per-scene audio (FFmpeg -acodec copy)
  5. DONE — no frame extraction
       │
       ▼
[User selects scene → On-Demand Frame Extraction]
  - Only extracts frames from that scene's clip (~0.2-1s)
  - Caches extracted frames (won't re-extract)
       │
       ▼
[User works on scene: mask, replace, dub]
       │
       ▼
[Approve → Stitch → Final Video]
```

### Key Changes

1. **`ingest_service.py`**: Removed frame extraction loop. Now calls `SceneChunkingService.chunk_video()` + `slice_scene_videos()`.

2. **`scene_chunking_service.py`**: Added two new methods:
   - `slice_scene_videos()` — FFmpeg stream copy (`-c copy`) to cut video into scene clips
   - `extract_frames_on_demand()` — Extract frames from a single scene clip

3. **`project_service.py`**: Added `set_scene_details()` method.

4. **API endpoint**: `POST /projects/{id}/scenes/{scene_id}/extract-frames`

5. **Frontend**: Added `extractSceneFrames()` API method.

### Performance

| Metric | Old (full extract) | New (on-demand) |
|--------|-------------------|-----------------|
| Ingest time (10min video) | 2-5 minutes | **3-5 seconds** |
| Disk usage | ~2GB (18K JPGs) | ~50MB (scene clips) |
| Frame extraction | All at once | Per-scene when needed |
| Frontend timeout | 90s → 300s | Never times out |

### File Structure

```
projects/{id}/
├── project.json
├── scenes/
│   ├── scene_000.mp4    ← scene clip (stream copy)
│   ├── scene_001.mp4
│   └── ...
├── audio/
│   ├── scene_000.aac    ← per-scene audio
│   ├── scene_001.aac
│   └── original_audio.aac
├── frames/
│   ├── scene_0/         ← extracted on-demand
│   │   ├── frame_000000.jpg
│   │   └── ...
│   └── scene_1/
│       └── ...
└── renders/
    └── scene_0_final.mp4
```

### Backward Compatibility

- `scenes` list in project.json still populated (from `set_scene_details`)
- Existing frame-based endpoints still work (try jpg/jpeg/png)
- `find_frame_path()` helper handles format detection
