---
name: python-video-processing-pipeline
description: "Build local-first video processing pipelines with Python — FFmpeg, OpenCV, scene detection, AI segmentation, motion extraction, compositing, and render. Covers the full chain from MP4 input to MP4 output with audio preservation."
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: software-development
    tags: [video, ffmpeg, opencv, pytorch, segmentation, motion, compositing, pipeline, fastapi, pydantic, api]
    related_skills: [terminal-engineering-discipline, bom-verified-implementation]
---

# Python Video Processing Pipeline

Build local-first video processing pipelines that extract motion from 2D animation, segment objects, replace assets, and re-render video — all without external APIs.

## When to Use

- Building video analysis or transformation tools
- Extracting motion data (position, scale, rotation) from video
- Object segmentation and tracking in video
- Replacing objects in video with new assets
- Scene detection and video splitting
- Any pipeline that goes MP4 → analysis → MP4
- Standalone video editing operations (crop, speed, flip, audio mix, normalize)
- Watch folder automation for auto-processing dropped videos
- Exposing video operations as FastAPI endpoints
- Building TTS/STT engines with subtitle generation (SRT/ASS)
- Syncing video clips to TTS voice timelines via FFmpeg speed adjustment

## Architecture Pattern

Service-oriented with adapter interfaces for AI models:

```
Input → Probe → Scene Detect → Frame Extract → [Segment → Track → Motion] → Composite → Render → Output
```

Each step is an independent service. The AI segmentation step is behind an abstract adapter interface so models can be swapped (SAM 2, OpenCV fallback, future models) without changing the pipeline.

### Module Layout

```
app/
├── config.py                 # Dataclass config, env vars, path resolution
├── schemas/__init__.py       # Pydantic v2 models (project, motion, selection)
├── adapters/
│   └── segmentation.py       # Abstract base + concrete implementations
├── services/
│   ├── video_probe.py        # ffprobe JSON metadata extraction
│   ├── scene_detection.py    # PySceneDetect ContentDetector
│   ├── frame_extraction.py   # FFmpeg frame extraction (per-scene, single)
│   ├── motion_extraction.py  # Centroid, bbox, scale, rotation from masks
│   ├── compositing.py        # Alpha-blend replacement onto frames
│   ├── render.py             # FFmpeg reassembly with audio mux
│   └── project_service.py    # Project JSON CRUD
└── spike_runner.py           # End-to-end orchestrator
```

## Step-by-Step Implementation Guide

### 1. Video Probe (ffprobe)

```python
cmd = [ffprobe, "-v", "quiet", "-print_format", "json",
       "-show_format", "-show_streams", str(video_path)]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
data = json.loads(result.stdout)
```

Extract from streams: `r_frame_rate` (e.g. "30000/1001"), `nb_frames`, `codec_name`, `width`, `height`. From format: `duration`, `size`. Parse FPS by splitting on `/`.

**Pitfall:** `nb_frames` can be 0 for some containers. Fallback: `int(round(duration * fps))`.

### 2. Scene Detection (PySceneDetect)

```python
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

video = open_video(str(path))
mgr = SceneManager()
mgr.add_detector(ContentDetector(threshold=27.0, min_scene_len=15))
mgr.detect_scenes(video=video)
scene_list = mgr.get_scene_list()  # list of (start, end) FrameTimecode pairs
```

If no scenes detected, treat entire video as one scene. `threshold=27` is a good default; lower = more sensitive.

### 3. Frame Extraction (FFmpeg)

```python
# Per-scene extraction using select filter
cmd = [ffmpeg, "-y", "-i", str(video_path),
       "-vf", f"select=between(n\\\\,{start}\\\\,{end})",
       "-vsync", "vfr", "-start_number", str(start),
       output_pattern]
```

**Pitfall:** The `between` filter is inclusive on both ends. `-vsync vfr` prevents duplicate frames.

### 4. Segmentation Adapter Pattern

Always abstract AI models behind an interface:

```python
class SegmentationAdapter(ABC):
    @abstractmethod
    def segment_frame(self, frame: np.ndarray, selection: SelectionInput) -> np.ndarray: ...
    @abstractmethod
    def propagate_masks(self, frames: list[np.ndarray], initial_mask: np.ndarray, idx: int) -> list[np.ndarray]: ...
    @abstractmethod
    def cleanup(self) -> None: ...
```

Concrete implementations: `SAM2Adapter` (GPU, accurate) and `SimpleContourAdapter` (CPU, GrabCut + template matching fallback).

**Factory pattern:** `create_segmentation_adapter(backend="sam2"|"contour", **kwargs)` — kwargs are backend-specific, so the factory must filter them before passing to constructors.

### 5. Motion Extraction from Masks

For each frame's binary mask:
1. `cv2.findContours` → largest contour
2. `cv2.moments` → centroid (m10/m00, m01/m00)
3. `cv2.boundingRect` → axis-aligned bbox
4. `cv2.minAreaRect` → rotation angle (normalize to [-90, 90])
5. Scale = current bbox / reference bbox dimensions
6. Opacity = contour area / bbox area (fill ratio)
7. Visibility = area > threshold

**Smoothing:** Moving average on centroid and scale; use sin/cos decomposition for rotation (avoids wrap-around artifacts at ±180°).

### 6. Compositing with Alpha Blending

```python
# Alpha blend with mask constraint
alpha = replacement[:, :, 3:4].astype(np.float32) / 255.0
mask_alpha = (mask_roi > 127).astype(np.float32)[:, :, np.newaxis]
combined_alpha = alpha * mask_alpha
blended = bg * (1 - combined_alpha) + fg * combined_alpha
```

**Pitfall:** Handle edge clipping when replacement extends beyond frame bounds. Calculate src/dst ROI intersections before blending.

**Rotation:** Apply `cv2.warpAffine` to replacement before compositing. Recalculate output size after rotation to avoid clipping.

### 7. Render with Audio Preservation

```python
cmd = [ffmpeg, "-y",
       "-framerate", str(fps),
       "-i", frame_pattern,    # composited frames
       "-i", str(audio_path),  # original audio
       "-c:v", "libx264", "-preset", "medium", "-crf", "18",
       "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k",
       "-shortest", "-movflags", "+faststart",
       str(output_path)]
```

**Pitfall:** `-shortest` ensures audio/video match length. `-pix_fmt yuv420p` required for broad player compatibility. `-movflags +faststart` for web streaming.

### 8. Project JSON Schema

Version-controlled, Pydantic-validated:

```json
{
  "version": "1.0.0",
  "name": "project_name",
  "source_video": "/absolute/path",
  "video_metadata": { "width", "height", "fps", "duration_seconds", "total_frames", "codec", "has_audio" },
  "scenes": [{ "scene_id", "start_frame", "end_frame", "start_time_sec", "end_time_sec" }],
  "objects": [{
    "object_id", "name", "kind",
    "selection": { "mode": "point"|"bounding_box", "frame_index", "x", "y", "width?", "height?" },
    "motion": { "frames": [{ "frame_index", "centroid_x", "centroid_y", "bbox", "scale_x", "scale_y", "rotation_deg", "opacity", "visibility" }] }
  }]
}
```

### 9. SAM 2.1 Video Predictor — Correct API Usage

SAM2's video predictor has specific API requirements that differ from naive assumptions. See `references/sam2-video-predictor-api.md` for full details.

**Critical API facts:**
- `init_state(video_path=dir)` — requires a **directory of frame images** (JPEG/PNG), not `None` or a video file. Write frames to a temp directory first.
- `add_new_mask(inference_state, frame_idx, obj_id, mask)` — mask must be a **2D tensor (H, W)**, NOT 4D (1, 1, H, W). Use `torch.from_numpy((mask > 127).astype(np.float32))` without unsqueeze.
- `propagate_in_video(inference_state, start_frame_idx=N)` — yields `(frame_idx, obj_ids, mask_logits)` tuples. Use `start_frame_idx` to propagate from the selection frame. Use `reverse=True` for backward propagation.
- Config path: `configs/sam2.1/sam2.1_hiera_l.yaml` (relative to sam2 package's configs dir, resolved by Hydra).
- `_C` post-processing warning is cosmetic — SAM2 works fine without the compiled C extension.

**Bidirectional propagation pattern:**
```python
# Forward from selection to end
for frame_idx, _, logits in predictor.propagate_in_video(state, start_frame_idx=sel_idx):
    masks[frame_idx] = (logits[0] > 0.0).cpu().numpy().squeeze()
# Backward from selection to start
if sel_idx > 0:
    for frame_idx, _, logits in predictor.propagate_in_video(state, start_frame_idx=sel_idx, reverse=True):
        if masks[frame_idx] is None:
            masks[frame_idx] = (logits[0] > 0.0).cpu().numpy().squeeze()
```

### 10. FFmpeg PATH Auto-Detection (Windows)

When FFmpeg is installed via WinGet on Windows, `shutil.which("ffmpeg")` returns `None` in MSYS/Git Bash sessions. Auto-detect in conftest.py:

```python
_ffmpeg = shutil.which("ffmpeg")
if _ffmpeg is None:
    _winget_links = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links"
    if _winget_links.is_dir():
        os.environ["PATH"] = str(_winget_links) + os.pathsep + os.environ.get("PATH", "")
```

Or create a shared `ffmpeg_utils.py` with `find_ffmpeg()` / `find_ffprobe()` that all services import.

### 11. Tracking Validation Methodology

When validating object tracking, measure:
- **Tracked ratio** = frames with non-empty mask / total frames
- **Composited ratio** = frames where composited differs from original / total frames
- **Largest centroid jump** = max frame-to-frame centroid distance (detects tracking loss)
- **Occlusion behavior** — SAM2 propagates onto the occluder, not the hidden object. This is expected.

Acceptance targets: ≥90% for simple motion, ≥80% for complex/animation content.

### 12. Schema Versioning with Migration

When evolving project JSON schema:
- Bump version in `ProjectData.version` default
- Add new fields with defaults (backward compatible — old JSON loads without errors)
- Provide explicit `migrate_v1_to_v2(data: dict) -> dict` function
- Test: load old data → verify new fields have defaults → verify round-trip

## Pitfalls

1. **PyTorch + new GPU architectures:** RTX 50-series (Blackwell, sm_120) requires PyTorch 2.11+ with cu128. PyTorch 2.6 cu124 silently fails at runtime with "no kernel image is available" — no import-time error, just a RuntimeError when you try to create a CUDA tensor. Verified install: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128`. Older cu124 index does NOT have sm_120 wheels. Always verify with `torch.cuda.get_device_capability()` after install. See `references/pytorch-cuda-compat.md`.

2. **SAM 2 not on PyPI:** Use `pip install git+https://github.com/facebookresearch/sam2.git`. Package installs as `SAM-2` (import as `sam2`). Apache 2.0 license. Config files are relative paths within the package (e.g. `configs/sam2.1/sam2.1_hiera_l.yaml`), not absolute filesystem paths.

3. **FFmpeg path on Windows (WinGet + MSYS):** After `winget install Gyan.FFmpeg`, the symlink lands in `%LOCALAPPDATA%\Microsoft\WinGet\Links\` but this path is NOT in the default MSYS/Git Bash PATH. `shutil.which("ffmpeg")` inside a Python process launched from MSYS will return None, causing `subprocess.run(["ffmpeg", ...])` to raise FileNotFoundError. Fix: `export PATH="$PATH:/c/Users/$USER/AppData/Local/Microsoft/WinGet/Links"` in the shell session, or use the full absolute path in the code. Integration tests that shell out to FFmpeg will fail silently in fresh MSYS sessions if this isn't set.

4. **OpenCV GrabCut needs minimum iterations:** `cv2.grabCut(frame, mask, rect, bgd, fgd, 5, mode)` — use 5+ iterations. Wrap in try/except for cv2.error on degenerate inputs.

5. **Template matching propagation is lossy:** OpenCV fallback propagation using `cv2.matchTemplate` loses accuracy with scale/rotation changes. Good enough for spike/MVP; real product needs optical flow or learned tracker.

6. **cv2.imread returns None silently:** Always check `if img is None: raise FileNotFoundError(...)` after imread.

7. **Factory functions with mixed kwargs:** When a factory dispatches to different constructors that accept different args, filter kwargs per backend. Don't pass SAM2-specific args to the OpenCV fallback.

8. **Mask list identity trap:** `masks = [np.zeros(...)] * n` creates N references to the SAME array. Use `[np.zeros(...) for _ in range(n)]` instead.

9. **Audio codec copy vs re-encode:** Use `-acodec copy` for extraction (no quality loss). Use `-c:a aac -b:a 192k` for final render (broad compatibility).

10. **Frame numbering:** FFmpeg `-start_number` affects output filenames only, not the select filter. The `between(n,start,end)` filter uses 0-based frame indices regardless.

11. **Default to JPG for frame extraction (10x speedup):** PNG frame extraction is ~10x slower than JPG. For a 10-minute video at 30fps (18,000 frames), PNG can take 30+ min while JPG takes ~3 min. Change default `format` parameter from `"png"` to `"jpg"`. Only use PNG when lossless quality is required. **Critical:** When changing format, update ALL frame-serving endpoints — use a `find_frame_path` helper that tries `jpg/jpeg/png` in order, instead of hardcoding `.png` in every lookup:

```python
def find_frame_path(scene_dir: Path, frame_index: int) -> Path | None:
    for ext in ("jpg", "jpeg", "png"):
        p = scene_dir / f"frame_{frame_index:06d}.{ext}"
        if p.exists():
            return p
    return None
```

Update ALL references: `get_frame`, `preview_mask`, `propagate`, `object_extraction`. Leaving even one `.png` hardcode causes 404s for newly extracted frames.

12. **Pytest cache masking integration test failures:** When integration tests generate fixtures (e.g. test videos via FFmpeg subprocess), pytest caches the fixture on first successful run. A subsequent run with a broken environment (e.g. FFmpeg not in PATH) will PASS from cache, hiding the real failure. Always run `pytest --cache-clear` or delete `.pytest_cache/` when verifying environment correctness. The symptom: `pytest -v` passes, but `pytest --cache-clear -v` shows ERRORs.

12. **SAM2 `add_new_mask` expects 2D tensor:** `add_new_mask(inference_state, frame_idx, obj_id, mask)` asserts `mask.dim() == 2`. Passing a 4D tensor (1, 1, H, W) via `unsqueeze(0).unsqueeze(0)` causes `AssertionError`. Use `torch.from_numpy((mask > 127).astype(np.float32))` — shape (H, W), no unsqueeze.

13. **SAM2 `init_state` requires frame directory, not None:** `init_state(video_path=dir)` expects a directory of numbered JPEG/PNG images. Passing `None` or a video file path causes errors. Write frames to a temp directory first with `cv2.imwrite(f"{tmpdir}/{i:06d}.jpg", frame)`.

14. **SAM2 VRAM scales with frame count, not resolution:** Video state is stored in GPU memory. ~20 MB/frame at 640×360. 210 frames → 4.2 GB VRAM. For very long videos (>500 frames), implement chunked processing or use `offload_video_to_cpu=True`.

15. **SAM2 doesn't detect occlusion:** During occlusion, SAM2 propagates the mask onto the occluder (the object in front), not the hidden object behind it. This is expected behavior — SAM2 does visual appearance propagation, not semantic object reasoning. Document as "PASS WITH LIMITATION" in tracking validation.

16. **FFmpeg PATH auto-detection for Windows tests:** Create a shared `ffmpeg_utils.py` with `find_ffmpeg()`/`find_ffprobe()` that checks `shutil.which()` first, then falls back to WinGet Links path (`%LOCALAPPDATA%\Microsoft\WinGet\Links`). All services should import from this utility instead of calling `shutil.which("ffmpeg")` directly. In `conftest.py`, auto-detect and add to `os.environ["PATH"]` before any test runs.

17. **Edge-TTS SubMaker API changed (≥ v6.x):** `SubMaker.create_sub()` and `SubMaker.generate_subs()` are **removed**. Use `SubMaker.feed(chunk)` (accepts raw chunk dict from `communicate.stream()`, NOT a tuple) and `SubMaker.get_srt()` (returns SRT string). Also: Vietnamese and some other voices emit `SentenceBoundary` events only, NOT `WordBoundary`. Always filter with `chunk["type"] in ("WordBoundary", "SentenceBoundary")` — checking only `WordBoundary` produces empty SRT files. See `references/edge-tts-whisper-stt.md` for the full pattern.

18. **FFmpeg rawvideo stdout pipe drops frames on Windows under scale-heavy filter graphs.** Reading raw frames via `-f rawvideo -pix_fmt rgb24 -` from a subprocess pipe silently loses frames (observed 7/30) when the decode graph includes a large `scale`/`pad` filter — the producer stalls the pipe and the reader gets a truncated stream. The same decode with NO filter (same-raster passthrough) delivers 30/30. Symptoms look like content mismatch (low PSNR, missing frames) — always check the FRAME COUNT first, not the quality metric. Fix: for any filtered/cross-raster decode, write the filtered output to a temp raw file (mkstemp in the OS temp dir, validate `file_size % (w*h*channels) == 0`, delete in `finally`) and read frame-by-frame from disk; keep the pipe only for filter-free decode. If you move only ONE side (e.g. the reference) to a file and leave the other (candidate) on the pipe, the same drop reappears — decode BOTH sides to files whenever either path has a filter. Assert the full expected frame count in tests (`len(frames) == frame_count`) so truncation fails as a count mismatch, never as low-quality noise. (Verified 2026-09-10 on Windows in the MotionForge2D S12-C2 cross-raster PSNR probe; full chain in `motionforge-sprint-manager` → `references/s12c2-finding-loop-reencode-validation.md`.)

19. **`ffprobe -show_packets` reports DECODE order, not presentation order — reading it as "the PTS is broken" is a classic false finding.** With B-frames the packet list is non-monotonic (`pts_time` 0, 0.133, 0.066, … with negative deltas like `-1024, -512`) while the *presentation* timeline is clean CFR. Always separate the two reads: `-select_streams v:0 -show_entries frame=pts_time` (presentation) vs `packet=pts_time` (decode order, plus `-count_packets` for the packet count). Verified 2026-09-22: a raw render declared "PTS impossible to satisfy / not CFR" was in fact already **CFR 30 fps with presentation PTS `0…61440` step 512**, and the earlier claim had been made from the decode-order packet list. Corollary: if you need a presentation-order view of packets, sort them — never conclude a timeline is broken from a raw packet dump.

20. **Trimming "the padding frame" must be verified by DECODED-frame identity, not by packet counts.** Counting encoded packets and adjusting PTS is not equivalent to dropping a decoded index. Recipe: decode both files to per-frame PNGs, hash each frame, and build an explicit `output_frame → matching_raw_frame` map; store it as an artifact. Verified failure: a claimed "padding dropped" export actually mapped **output 119 → raw 120** — it had dropped raw 119 and kept the padding frame — which only the decoded-frame hashes could show. When you trim N padded frames, assert the map (`output i ↔ raw i` for `i ∈ [0, 119)`) and keep a **lossless intermediate** (FFV1/NUT or a PNG sequence) so index selection is separated from encode loss. Also: `-c:v copy` cannot remove a decoded frame from the middle of a stream, and a single re-encode is usually the honest fix when the requirement is "keep the source audio/timeline untouched" rather than "keep the video bitstream".

21. **Container audio duration ≠ decoded sample count — measure both and label them separately.** AAC frames are 1024 samples/channel, so whole-packet copies cannot end on a video frame edge. Verified on one 4 s export, three different numbers that must never be conflated:
   - container `duration = 4.001995 s` (216 AAC packets)
   - decoded `176,484` samples/channel = `4.001905 s` (+84 samples ≈ 1.905 ms over nominal)
   - source window `176,400` samples = `4.000000 s`
   Decisive proof that the source audio was remuxed untouched (cheap, and much stronger than "the duration looks right"):
   ```bash
   ffmpeg -v error -y -i candidate.mp4 -map 0:a:0 -f s16le -acodec pcm_s16le cand.pcm
   ffmpeg -v error -y -ss 55.000 -t 4.001995 -i film.mp4 -map 0:a:0 -f s16le -acodec pcm_s16le src.pcm
   ```
   then compare sample-by-sample (MAE, max abs diff, mismatch count) **and** the PCM file sha256. Verified: 352,968 samples, **0 mismatches, MAE 0.0, identical PCM sha256**. Also watch the window arithmetic — a request that says "film `[55.000, 60.001995)`" is a 5.001995 s window and can never match a 4.001995 s candidate; measure both readings rather than reporting a false mismatch.

22. **A model's input-size requirement (e.g. "must be a multiple of 16") does not authorize changing the aspect ratio.** Pad with a mapped offset and crop back after generation, applying the **same transform to source, reference and control**: `640×360 → 640×368` by +4 px top / +4 px bottom, then crop the output back to exactly `640×360` with content at identical coordinates. Verified failure: the code stretched 360→368 to satisfy divisibility, the final clip came out `640×368`, and the downstream gate "passed" it only because 368 had been declared as the expectation. Prove the round-trip on a synthetic grid before spending GPU time, and never let the expected value be whatever the code happened to emit.

## Speech Engine Integration (TTS/STT/Subtitles)

For Edge-TTS (free TTS with SRT generation), Faster-Whisper (STT transcription), SRT/ASS subtitle generation, FFmpeg speed-sync for clip-to-TTS timeline matching, and audio mixing — see `references/edge-tts-whisper-stt.md`.

## FFmpeg Video Editing Operations

For crop, speed, flip, audio replace/mix, loudness normalization, frame extraction modes, and video joining via concat demuxer — see `references/ffmpeg-video-editing-ops.md`. Covers `imageio_ffmpeg.get_ffmpeg_exe()` as the preferred cross-platform FFmpeg binary resolver (simpler than WinGet path detection).

## Watch Folder Automation

For auto-processing video files dropped into a monitored directory (polling loop, preset config, start/stop lifecycle) — see `references/watch-folder-pattern.md`.

## OpenCV Thread Optimization

Set OpenCV thread count at app startup for better multi-core utilization:

```python
# app/main.py — at the VERY TOP, before any other imports
import cv2
cv2.setNumThreads(8)  # Use 8 CPU cores for OpenCV operations
```

**Why at the top:** OpenCV's thread pool is initialized on first use. Setting it after importing heavy modules (SAM2, numpy) may have no effect.

**When to use:** Backend servers processing multiple frames concurrently (inpainting, contour detection, frame extraction). Default OpenCV thread count is often 1-2 on Windows.

**Pitfall:** Don't set this in test files — it can cause thread contention with pytest-xdist parallel execution.

## GPU Hardware Acceleration (NVENC)

When the machine has an NVIDIA GPU, FFmpeg can use hardware encoding for 3-5x speedup on render.

### Detection Pattern

```python
import subprocess
import shutil
from dataclasses import dataclass

@dataclass
class EncoderInfo:
    has_nvenc: bool = False
    gpu_name: str = ""
    encoder_name: str = "libx264"  # fallback

def detect_nvenc() -> EncoderInfo:
    info = EncoderInfo()
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            info.gpu_name = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        ffmpeg = shutil.which("ffmpeg")
        result = subprocess.run([ffmpeg, "-encoders"], capture_output=True, text=True, timeout=10)
        if "h264_nvenc" in result.stdout:
            info.has_nvenc = True
            info.encoder_name = "h264_nvenc"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return info
```

### Encoding Args

```python
def get_encode_args() -> list[str]:
    info = detect_nvenc()
    if info.has_nvenc:
        return ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
                "-c:v", "h264_nvenc", "-preset", "fast", "-rc", "vbr", "-cq", "23"]
    return ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p"]
```

**Pitfall:** `h264_nvenc` requires FFmpeg built with NVENC support. Verify with `ffmpeg -encoders | grep nvenc`.

**Pitfall:** NVENC quality differs from libx264 at same CRF/CQ. Test visually before switching default.

## Auto Lip-Sync Speech-Rate Adjustment

When generating TTS to replace original speech, auto-adjust rate to match original duration:

```python
def calculate_speech_rate(original_duration: float, tts_duration: float) -> str:
    if tts_duration <= 0 or original_duration <= 0:
        return "+0%"
    ratio = max(0.85, min(1.15, tts_duration / original_duration))
    pct = max(-15, min(15, round((1.0 / ratio - 1.0) * 100)))
    return f"{'+' if pct >= 0 else ''}{pct}%"
```

Pipeline: Generate TTS → measure → if off >15%, regenerate with adjusted rate → final fallback: FFmpeg `atempo` filter.

**Pitfall:** Edge-TTS rate clamped to ±15%. FFmpeg `atempo` clamped to [0.5, 2.0]. Chain for extreme: `atempo=0.5,atempo=0.5` = 0.25x.

## Adding an API Layer (FastAPI)

After the service layer works via spike_runner.py, the next step is exposing it as an HTTP API. This adds three layers:

### Workflow Services (`app/workflow/`)

Application-level orchestration that wraps the lower-level services. Each workflow service owns a coherent user-facing operation:

```
app/workflow/
├── __init__.py
├── project_workflow.py        # Project CRUD, object management
├── ingest_service.py          # Probe + scene detect + frame extract (orchestrates 3 services)
├── segmentation_service.py    # Mask preview + propagation (wraps adapter)
├── object_extraction_service.py  # Crop PNGs, thumbnails, gallery manifest
├── replacement_service.py     # Upload replacement PNG, manage transform settings
├── render_service.py          # PreviewRenderService + FinalRenderService
└── job_service.py             # In-process background worker with progress/cancel
```

**Key principle:** Workflow services import and call service modules. They never duplicate logic. They add orchestration, progress reporting, and cancellation checks.

### Job Service Pattern

Background jobs run in daemon threads, not subprocesses. The caller provides a `func(progress_cb, is_cancelled_cb)`:

```python
class JobService:
    def create_job(self, job_type, func) -> JobInfo:
        # Creates threading.Event for cancel flag
        # Spawns daemon thread
        # Returns JobInfo immediately (state=queued)
        # Thread updates state: queued → running → completed/failed/cancelled

    def cancel_job(self, job_id) -> bool:
        # Sets cancel event, sets state=cancelling
        # Worker must check is_cancelled() between frames
```

**State machine:** `queued → running → completed|failed` or `queued|running → cancelling → cancelled`

**Progress callback:** `progress_cb(pct: float, msg: str)` where pct is 0-100. Worker calls this periodically; the JobInfo object is updated in-place (shared reference).

**Cancel check:** Worker calls `is_cancelled()` between expensive operations (frame processing, mask propagation). Must return early and cleanly when cancelled.

**JobInfo fields:** job_id, state (JobState enum), progress (0-100), message (user-safe), current_step, started_at, completed_at, error_code, result (dict for output paths). `error_detail` goes to internal logs only, not exposed to client.

**Pitfall:** Don't block the FastAPI request thread. `create_job` starts the thread and returns immediately. The endpoint returns the JobInfo dict; the client polls `GET /api/jobs/{id}` for progress.

**Pitfall — SameFileError on file upload:** When an endpoint writes an uploaded file to its final destination, then calls a service that also copies to that same path, `shutil.copy2` raises `SameFileError`. Fix: write to a `tempfile.NamedTemporaryFile` first, call the service with the temp path, then `unlink` the temp in a `finally` block. The service owns the final copy.

### FastAPI Routes (`app/api/`)

```
app/api/
├── __init__.py
├── app.py           # FastAPI app with CORS, health check, router includes
├── deps.py          # Module-level singletons + getter functions
└── routes/
    ├── __init__.py
    ├── projects.py   # Project CRUD, objects, replacement, render endpoints
    ├── jobs.py       # Job status/cancel endpoints
    └── frames.py     # Frame serving via FileResponse
```

**Entry point:** `app/main.py` imports `app` from `app/api/app.py`. Run with `uvicorn app.main:app`.

### Dependency Injection Pattern

Use module-level singletons in `deps.py`. Each singleton is a workflow service instance. Getter functions provide access:

```python
# deps.py
_config = AppConfig()
_job_service = JobService()
_project_wf = ProjectWorkflowService(_config)
_seg_service = SegmentationService(_config)

def get_job_service() -> JobService:
    return _job_service
```

Endpoints call `get_job_service()` etc. This is simple, testable (monkeypatch the module attributes), and avoids FastAPI's `Depends()` boilerplate for singletons.

### Testing with Singleton Deps

Override singletons via `monkeypatch.setattr` on the deps module in an autouse fixture:

```python
@pytest.fixture(autouse=True)
def _patch_project_root(tmp_path, monkeypatch):
    from app.api import deps
    test_config = AppConfig(project_root=tmp_path / "test", ...)
    monkeypatch.setattr(deps, "_config", test_config)
    monkeypatch.setattr(deps, "_project_wf", ProjectWorkflowService(test_config))
    monkeypatch.setattr(deps, "_job_service", JobService())
    # ... etc for each singleton
```

**Pitfall:** The `monkeypatch` fixture is function-scoped by default. Each test gets fresh singletons. This is correct — don't use session scope or tests will share state.

### E2E Workflow Testing with TestClient

Use FastAPI's `TestClient` (from `starlette.testclient`) to run full workflow E2E tests without starting a real server or browser:

```python
from fastapi.testclient import TestClient
from app.api.app import app

def test_full_e2e():
    c = TestClient(app)
    # 1. Create project
    r = c.post("/api/projects", json={"name": "Test"})
    pid = r.json()["project_id"]
    # 2. Upload video
    with open("fixture.mp4", "rb") as f:
        c.post(f"/api/projects/{pid}/video", files={"file": ("test.mp4", f, "video/mp4")})
    # 3. Ingest (triggers background job)
    r = c.post(f"/api/projects/{pid}/ingest")
    jid = r.json()["job_id"]
    # 4. Poll job to completion
    for _ in range(60):
        time.sleep(1)
        r = c.get(f"/api/jobs/{jid}")
        if r.json()["state"] in ("completed", "failed"):
            break
    assert r.json()["state"] == "completed"
    # ... continue with subsequent steps
```

**Advantages over browser E2E:** Runs in-process (no server startup), deterministic, fast, works in CI without display. Covers the full API contract.

**Limitations:** Doesn't test frontend routing, canvas rendering, or browser-specific behavior. Use Playwright for those.

**Polling pattern:** Background jobs return immediately with a job_id. The test polls `GET /api/jobs/{id}` until state is terminal. Set a reasonable timeout (e.g. 300s for SAM2 propagation on GPU). If the job service uses daemon threads, they complete even when the test ends — no cleanup needed.

### Frame Serving

Use `FileResponse` for frame images. Don't read the file into memory:

```python
@router.get("/{project_id}/frames/{frame_index}")
def serve_frame(project_id, frame_index, scene_id=0):
    frame_path = proj_dir / "frames" / f"scene_{scene_id}" / f"frame_{frame_index:06d}.png"
    if not frame_path.exists():
        raise HTTPException(404, ...)
    return FileResponse(str(frame_path), media_type="image/png")
```

### Video Upload

Use `UploadFile` (FastAPI's async file upload). Write with `shutil.copyfileobj(file.file, dest)` — don't use `await file.read()` for large files.

### Pydantic v2 Aliases for External Specs

When a field name must match an external spec (e.g. JavaScript camelCase from a transform spec) but Python conventions use snake_case:

```python
class ReplacementConfig(BaseModel):
    asset_path: str = Field(default="", alias="assetPath")
    rotation_offset_deg: float = Field(default=0.0, alias="rotationOffsetDeg")
    fit_mode: FitMode = Field(default=FitMode.CONTAIN, alias="fitMode")

    model_config = {"populate_by_name": True}
```

`populate_by_name=True` allows both `assetPath` (from JSON/API) and `asset_path` (from Python code) to work. Without it, only the alias works for deserialization.

**Ruff N815 suppression:** The aliases avoid the mixedCase variable name warning. Don't use `# noqa: N815` — use Field aliases instead.

## Fixture-Based Tracking Validation

When validating object tracking, create 3 purpose-built fixtures:

### Fixture A — Synthetic Motion
- 5-10s, 640×360+, 30fps
- Object moves in non-trivial path (figure-8, arc)
- Include scale oscillation and rotation
- Not just a rectangle moving linearly on solid background

### Fixture B — Real/Realistic Animation
- 5s+, character or object with clear motion
- Background not uniform color
- Light silhouette changes (walking, arm swing)

### Fixture C — Occlusion
- Object hidden behind obstacle for 3-10 frames
- Reappears after occlusion zone
- Tests SAM2's recovery behavior

### Metrics to collect per fixture

```python
metrics = {
    "totalFrames": total,
    "trackedFrames": sum(1 for f in frames if f["visibility"] and f["area"] > 0),
    "trackedRatio": tracked / total,
    "compositedFrames": composited,  # pixel-diff from original
    "compositedRatio": composited / total,
    "emptyMaskFrames": total - tracked,
    "largestCentroidJumpPx": max_centroid_jump,
    "peakVramMb": gpu_peak_mb,
    "propagationSeconds": propagation_time,
}
```

Acceptance targets: Fixture A ≥90%, Fixture B ≥80%, composited ratio ≈ tracked ratio.

**Occlusion caveat:** SAM2 propagates onto the occluder during hidden frames. Centroid stays at obstacle center. This is expected — document as "PASS WITH LIMITATION". After reappearance, tracking resumes correctly.

## Verification

After building a spike, verify ALL of these:
- [ ] Output video plays correctly (check with ffprobe: duration, fps, codec, audio)
- [ ] Audio is preserved and synced
- [ ] Frame count matches original
- [ ] Project JSON validates against schema (round-trip: create → serialize → deserialize → compare)
- [ ] Unit tests pass for schema and motion calculation
- [ ] Integration tests pass for probe and render
- [ ] Debug overlays show correct mask positions
- [ ] Benchmark logged (time, RAM, VRAM)
- [ ] **Run `pytest --cache-clear`** to confirm tests pass without cached fixtures — pytest caches module-scoped fixtures (e.g. generated test videos), so a broken environment can appear green from cache

## Dependencies Reference

See `references/dependencies.md` for version-pinned install commands.
See `references/ruff-fix-patterns.md` for common ruff linting fixes in FastAPI + Pydantic v2 code.
See `references/ffmpeg-video-editing-ops.md` for video editing operations, frame extraction modes, concat joining, and `imageio_ffmpeg` setup.
See `references/watch-folder-pattern.md` for auto-processing watch folder automation.
See `references/edge-tts-whisper-stt.md` for Edge-TTS, Faster-Whisper, SRT/ASS generation, and FFmpeg speed-sync patterns.
See `references/manager-side-pixel-verification.md` for manager-side independent visual verification: ROI step measurement for event frames, channel-order-aware overlay-mask measurement, vision-prose-vs-file-truth grep rule, and canonical RULES_LOADED path check.
See `templates/fastapi-deps.py` for the dependency injection singleton pattern.

## Frontend Preview (Konva Canvas)

For the frontend canvas preview side (Konva.js compositing, coordinate transforms, Zustand store, Playwright E2E testing), see the companion skill `react-konva-canvas-preview`. It covers the React/TypeScript implementation that pairs with this Python backend.
