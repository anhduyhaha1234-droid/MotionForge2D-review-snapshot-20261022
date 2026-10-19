# MotionForge 2D

Local-first 2D animation motion extraction and replacement tool.

## Overview

MotionForge 2D lets you:
1. Import a 2D animation video (MP4)
2. Automatically detect scene changes
3. Select characters/objects by clicking or drawing a bounding box
4. Track objects across frames using AI segmentation (SAM 2.1)
5. Extract motion data (position, scale, rotation, opacity)
6. Replace objects with new PNG assets
7. Render the result as MP4 preserving original FPS, duration, and audio

## Requirements

- **Python 3.11+**
- **FFmpeg** (with ffprobe)
- **CUDA-capable GPU** (optional, for SAM 2.1; CPU fallback available)
- **8GB+ RAM** recommended

### Installing FFmpeg

MotionForge locates `ffmpeg` and `ffprobe` at runtime — no hard-coded
install path is assumed. Install FFmpeg any way you like, then make sure
MotionForge can find it (see [FFmpeg configuration](#ffmpeg-configuration)):

- **Windows**: `winget install Gyan.FFmpeg` (adds both `ffmpeg.exe` and
  `ffprobe.exe` to `%LOCALAPPDATA%\Microsoft\WinGet\Links`)
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Any OS**: download a build from <https://ffmpeg.org/download.html> and
  put it in a directory on your `PATH`

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd MotionForge2D

# Run setup (installs deps, downloads models)
bash scripts/setup.sh

# Or manually:
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
pip install -e ".[dubbing]"  # optional: audio dubbing (edge-tts, Whisper, translation)
pip install git+https://github.com/facebookresearch/sam2.git  # optional: SAM 2 segmentation
bash scripts/download_models.sh  # optional: SAM 2 model checkpoints
```

## Running the Spike

The vertical spike demonstrates the full pipeline end-to-end:

```bash
# With a custom video and replacement image:
bash scripts/run_spike.sh /path/to/video.mp4 /path/to/sprite.png 0

# Or run directly:
python -m app.spike_runner \
    --video input.mp4 \
    --replacement sprite.png \
    --scene 0 \
    --backend contour \
    --output-dir output
```

### Command Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `--video` | Input MP4 video (required) | — |
| `--replacement` | PNG replacement image | None (renders original) |
| `--scene` | Scene index to process | 0 |
| `--point-x`, `--point-y` | Selection point coordinates | Auto-detect |
| `--bbox-x/y/w/h` | Bounding box selection | — |
| `--backend` | `sam2` or `contour` | `contour` |
| `--output-dir` | Output directory | `output/` |
| `--name` | Project name | `spike_project` |

### Using SAM 2.1 (GPU)

```bash
python -m app.spike_runner \
    --video input.mp4 \
    --replacement sprite.png \
    --backend sam2
```

Requires:
- CUDA-capable GPU with 8GB+ VRAM
- SAM 2.1 checkpoint downloaded via `scripts/download_models.sh`

## Project Structure

```
MotionForge2D/
├── app/
│   ├── __init__.py
│   ├── config.py              # Global configuration
│   ├── spike_runner.py        # End-to-end spike pipeline
│   ├── adapters/
│   │   └── segmentation.py    # SAM2 + OpenCV adapters
│   ├── schemas/
│   │   └── __init__.py        # Pydantic data models
│   └── services/
│       ├── video_probe.py     # FFmpeg metadata extraction
│       ├── scene_detection.py # PySceneDetect integration
│       ├── frame_extraction.py # Frame extraction
│       ├── motion_extraction.py # Motion from masks
│       ├── compositing.py     # Object replacement
│       ├── render.py          # Video reassembly
│       └── project_service.py # Project persistence
├── tests/
│   ├── conftest.py
│   ├── test_schema.py         # Unit tests
│   └── test_integration.py    # Integration tests
├── scripts/
│   ├── setup.sh               # Full environment setup
│   ├── download_models.sh     # Download SAM 2.1 checkpoints
│   └── run_spike.sh           # Run the vertical spike
├── docs/
│   ├── ARCHITECTURE.md        # System architecture
│   ├── MILESTONES.md          # Development milestones
│   └── SPIKE_REPORT.md        # Spike results report
├── examples/
│   └── example_project.json   # Sample project file
├── output/                    # Generated outputs
├── models_checkpoints/        # AI model weights
├── pyproject.toml             # Python project config
├── README.md
└── THIRD_PARTY.md
```

## Running Tests

```bash
# Unit tests only (no GPU/FFmpeg required):
pytest tests/test_schema.py -v

# All tests including integration:
pytest -v -m integration

# With coverage:
pytest --cov=app --cov-report=html
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MOTIONFORGE_ROOT` | Project root directory | `~/MotionForge2D` |
| `MOTIONFORGE_MODELS` | Model checkpoints directory | `~/MotionForge2D/models_checkpoints` |
| `MOTIONFORGE_OUTPUT` | Output directory | `~/MotionForge2D/output` |
| `MOTIONFORGE_FFMPEG` | Full path to the `ffmpeg` executable | auto-discovered |
| `MOTIONFORGE_FFPROBE` | Full path to the `ffprobe` executable | auto-discovered |

## FFmpeg configuration

MotionForge discovers `ffmpeg` and `ffprobe` once through a shared
resolution order in `app/services/ffmpeg_utils.py`. Every service imports
this authority; there are no per-service hard-coded paths.

Resolution order (first match wins):

1. **Environment override** — `MOTIONFORGE_FFMPEG` / `MOTIONFORGE_FFPROBE`
   must point to an executable-suitable file (Windows: a `.exe` file;
   POSIX: a regular file with execute permission). A set-but-invalid
   override (missing file, non-executable text file, unsupported suffix)
   raises an actionable error; it never silently falls back.
2. **`PATH`** — the executables are found via the system `PATH`.
3. **WinGet Links (Windows)** — `%LOCALAPPDATA%\Microsoft\WinGet\Links`,
   where `winget install Gyan.FFmpeg` places `ffmpeg.exe`/`ffprobe.exe`.
4. **Portable app-managed location** — reserved; no such contract exists in
   the repo yet. When a portable bundle is added, it is resolved here and
   documented in this section.
5. **Actionable error** — install guidance, no guessed machine paths.

Example — point MotionForge at a specific FFmpeg build:

```bash
export MOTIONFORGE_FFMPEG=/opt/ffmpeg/bin/ffmpeg
export MOTIONFORGE_FFPROBE=/opt/ffmpeg/bin/ffprobe
```

## Dubbing dependencies (Phase 2, optional)

Audio dubbing (vocal separation, speech-to-text, translation, TTS) is a
Phase 2 feature. Its runtime dependencies are declared in the optional
`dubbing` group and are NOT installed by default:

```bash
pip install -e ".[dubbing]"
```

- `edge-tts` — text-to-speech (imported at module load; importing
  `AudioDubbingService` without it raises an actionable error)
- `openai-whisper` — speech-to-text (lazy-imported inside `transcribe()`)
- `deep-translator` — segment translation (lazy-imported inside
  `translate_segments()`)

Core (Phase 1) installs do not require any of these packages.

## Project JSON Format

Version 1.0.0 schema includes:
- Video metadata (resolution, fps, duration, codec)
- Scene list (start/end frames, timestamps)
- Tracked objects with selections (point or bbox)
- Per-frame motion data (centroid, bbox, scale, rotation, opacity, visibility)
- Replacement image paths

See `examples/example_project.json` for a complete example.

## License

MIT License. See LICENSE file.

## Third-Party Dependencies

See [THIRD_PARTY.md](THIRD_PARTY.md) for a complete list of dependencies,
their versions, licenses, and purposes.
