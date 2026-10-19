# Video Pipeline Python Dependencies — Verified Install Commands

## Core (always needed)

```bash
pip install fastapi uvicorn pydantic sqlalchemy aiosqlite
pip install opencv-python-headless numpy Pillow tqdm
pip install httpx
```

## Video Processing

```bash
pip install scenedetect          # PySceneDetect (v0.7.1+, BSD-3)
# FFmpeg: system dependency, not pip
# Windows: winget install Gyan.FFmpeg
# Ubuntu:  sudo apt install ffmpeg
# macOS:   brew install ffmpeg
```

## AI / ML (for SAM 2.1 segmentation)

```bash
# PyTorch — pick ONE index URL matching your GPU:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128  # RTX 50xx
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124  # RTX 40xx

# SAM 2 from Meta (Apache 2.0)
pip install git+https://github.com/facebookresearch/sam2.git
# Installs as "SAM-2", import as "sam2"
# Dependencies: hydra-core, omegaconf, iopath
```

## SAM 2.1 Model Checkpoint

```bash
# ~856MB, Apache 2.0 license, SHA-256: 2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318
curl -L -o models_checkpoints/sam2.1_hiera_large.pt \
  https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt
# Config path (used in code): configs/sam2.1/sam2.1_hiera_l.yaml
```

## Dev Tools

```bash
pip install pytest pytest-asyncio ruff mypy
```

## Version Matrix (verified 2026-07-29)

| Package | Version | License |
|---|---|---|
| torch | 2.11.0+cu128 | BSD-3 |
| torchvision | 0.26.0+cu128 | BSD-3 |
| SAM-2 | 1.0 | Apache-2.0 |
| fastapi | 0.139.2+ | MIT |
| pydantic | 2.13.4+ | MIT |
| opencv-python-headless | 5.0.0+ | Apache-2.0 |
| scenedetect | 0.7.1+ | BSD-3 |
| SQLAlchemy | 2.0.51+ | MIT |
| numpy | 2.4.4+ | BSD-3 |

## Windows-Specific Notes

- FFmpeg via `winget install Gyan.FFmpeg` installs to `%LOCALAPPDATA%\Microsoft\WinGet\Links\` — NOT in default MSYS PATH. See SKILL.md pitfall #16 for auto-detection pattern.
- `opencv-python-headless` preferred over `opencv-python` to avoid Qt/GUI dependencies on servers.
- PyTorch CUDA init on Windows can take 15-30s on first call; don't use short timeouts.
- `sam2` package's `__init__.py` calls `initialize_config_module("sam2")` — Hydra config search path is `pkg://sam2`, so config files must be referenced relative to `sam2/configs/`.
