# FFmpeg Video Editing Operations (Async Subprocess)

Use `asyncio.create_subprocess_exec` for non-blocking FFmpeg execution in FastAPI apps.

## Cross-Platform FFmpeg Resolution

**Preferred:** `imageio_ffmpeg.get_ffmpeg_exe()` — returns the absolute path to a bundled FFmpeg binary on Windows, macOS, and Linux. No PATH setup, no WinGet detection, no `shutil.which()` fallbacks needed.

```python
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()  # e.g. C:\...\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe
```

Install: `pip install imageio-ffmpeg`

**When to use each approach:**
- `imageio_ffmpeg` — best for standalone scripts, CI, and any environment where you control `pip install`. Bundles its own FFmpeg binary.
- `shutil.which("ffmpeg")` — when the system has FFmpeg installed globally (e.g. dev machines, Docker images with ffmpeg pre-installed)
- WinGet path detection — last resort for Windows-only dev environments where ffmpeg was installed via `winget install Gyan.FFmpeg`

## Async FFmpeg Execution Pattern

```python
import asyncio
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

async def run_ffmpeg(*args) -> tuple[int, str, str]:
    cmd = [FFMPEG, "-y", *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace")
```

**Pitfall:** Always pass `-y` (overwrite output) — FFmpeg prompts for confirmation on stdout which hangs async subprocess.

**Pitfall:** FFmpeg writes progress/metadata to stderr, not stdout. Parse stderr for duration, errors, etc.

## Video Filter Operations

### Crop by Aspect Ratio

```python
# 9:16 portrait — crop width to match height
vf = "crop=ih*9/16:ih"

# 1:1 square — crop to smaller dimension
vf = "crop=min(iw\\,ih):min(iw\\,ih)"

# 16:9 landscape — crop height to match width
vf = "crop=iw:iw*9/16"
```

### Speed Change

```python
# Both video and audio must be adjusted
speed = 1.5
vf = f"setpts=PTS/{speed}"     # video: speeds up by reducing presentation timestamps
af = f"atempo={speed}"          # audio: tempo adjustment (0.5–2.0 range per filter)
```

**Pitfall:** `atempo` only supports 0.5–2.0. For 4x speed, chain: `atempo=2.0,atempo=2.0`.

### Flip

```python
vf = "hflip"   # horizontal mirror
vf = "vflip"   # vertical mirror
```

### Loudness Normalization (EBU R128)

```python
af = "loudnorm=I=-16:TP=-1.5:LRA=11"
# I = integrated loudness target (-16 LUFS for streaming)
# TP = true peak limit (-1.5 dBTP)
# LRA = loudness range target (11 LU)
```

### Combining Filters

Chain multiple video filters with commas in a single `-vf` string:

```python
vf_parts = []
vf_parts.append("crop=ih*9/16:ih")   # crop
vf_parts.append(f"setpts=PTS/1.5")   # speed
vf_parts.append("hflip")              # flip
cmd.extend(["-vf", ",".join(vf_parts)])
```

**Pitfall:** When combining with audio filters AND replacing audio, use `-filter_complex` with stream labels instead of `-vf`/`-af`.

## Audio Replacement / Mixing

```python
# Replace audio entirely
cmd = [FFMPEG, "-y", "-i", video, "-i", audio, "-c:v", "copy", "-map", "0:v", "-map", "1:a", output]

# Mix audio (overlay new audio on original, keep video duration)
cmd = [FFMPEG, "-y", "-i", video, "-i", audio,
       "-filter_complex", "[1:a][0:a]amix=inputs=2:duration=first[outa]",
       "-map", "0:v", "-map", "[outa]", output]
```

## Frame Extraction Modes

### Interval (every N seconds)
```python
vf = f"fps=1/{interval_seconds}"
```

### Even distribution (N frames total)
```python
duration = get_duration(input)  # via FFmpeg probe
fps = target_count / duration
vf = f"fps={fps}"
```

### Specific FPS
```python
vf = f"fps={target_fps}"
```

## Video Joining (Concat Demuxer)

Fast, lossless joining when all clips share resolution/codec:

```python
# 1. Write concat list file
with open("concat.txt", "w") as f:
    for clip in clip_paths:
        safe = clip.replace("'", "'\\''")
        f.write(f"file '{safe}'\n")

# 2. Concat
cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", output]
```

**Pitfall:** All clips must have the same resolution, codec, and frame rate. If not, re-encode mismatched clips first:

```python
cmd = [FFMPEG, "-y", "-i", clip,
       "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
       "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k",
       normalized_output]
```

## Extracting Video Metadata

```python
import re

async def get_duration(path: str) -> float:
    """Get duration in seconds by parsing FFmpeg stderr."""
    cmd = [FFMPEG, "-i", path]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr.decode(errors="replace"))
    if m:
        h, mi, s = float(m.group(1)), float(m.group(2)), float(m.group(3))
        return h * 3600 + mi * 60 + s
    return 0.0

async def get_resolution(path: str) -> tuple[int, int]:
    """Get (width, height) by parsing FFmpeg stderr."""
    cmd = [FFMPEG, "-i", path]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    m = re.search(r"(\d{2,5})x(\d{2,5})", stderr.decode(errors="replace"))
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0
```

**Pitfall:** `ffmpeg -i file.mp4` (no output) exits with code 1 but prints all metadata to stderr. This is normal — don't treat rc=1 as an error for this probe command.
