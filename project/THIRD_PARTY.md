# MotionForge 2D — Third-Party Dependencies

## Python Packages

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| **PyTorch** | 2.11.0+cu128 | BSD-3-Clause | Deep learning framework for SAM 2.1 |
| **torchvision** | 0.26.0+cu128 | BSD-3-Clause | Vision utilities for PyTorch |
| **SAM-2** | 1.0 | Apache-2.0 | Segment Anything Model 2 by Meta AI |
| **FastAPI** | 0.139.2+ | MIT | Web API framework |
| **Pydantic** | 2.13.4+ | MIT | Data validation and serialization |
| **SQLAlchemy** | 2.0.51+ | MIT | Database ORM |
| **aiosqlite** | 0.22.1+ | MIT | Async SQLite driver |
| **OpenCV** (opencv-python-headless) | 5.0.0+ | Apache-2.0 | Image processing, contour detection |
| **NumPy** | 2.4.4+ | BSD-3-Clause | Numerical computing |
| **Pillow** | 12.2.0+ | MIT-CMU | Image I/O |
| **PySceneDetect** | 0.7.1+ | BSD-3-Clause | Video scene boundary detection |
| **hydra-core** | 1.3.4+ | MIT | Configuration management (SAM2 dep) |
| **omegaconf** | 2.3.1+ | BSD-3-Clause | YAML config (SAM2 dep) |
| **iopath** | 0.1.10+ | MIT | File I/O abstraction (SAM2 dep) |
| **uvicorn** | 0.51.0+ | BSD-3-Clause | ASGI server |
| **httpx** | 0.28.1+ | BSD-3-Clause | HTTP client |
| **tqdm** | 4.69.0+ | MIT | Progress bars |

### Dev Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| **pytest** | 9.1.1+ | MIT | Testing framework |
| **pytest-asyncio** | 1.4.0+ | Apache-2.0 | Async test support |
| **ruff** | 0.3.0+ | MIT | Python linter |
| **mypy** | 1.8.0+ | MIT | Static type checker |

## System Dependencies

| Tool | Version | License | Purpose |
|------|---------|---------|---------|
| **FFmpeg** | 8.1.2 | LGPL-2.1+ (GPL build) | Video encoding/decoding |
| **Python** | 3.11 | PSF | Runtime |
| **Node.js** | 26.x | MIT | Frontend build |

## AI Model Checkpoints

| Model | Size | License | Source |
|-------|------|---------|--------|
| **sam2.1_hiera_large.pt** | ~890MB | Apache-2.0 | [Meta AI SAM2](https://github.com/facebookresearch/sam2) |

## License Notes

- **SAM 2.1** is released under Apache 2.0 by Meta AI, permitting commercial use.
- **PyTorch** uses BSD-3-Clause, permitting commercial use.
- **FFmpeg** is built with `--enable-gpl` flags. If distributing binaries, ensure
  compliance with GPL-2.0+ or use an LGPL-only build.
- All Python packages are permissively licensed (MIT, BSD, Apache).
- No proprietary or paywalled APIs are used.
- No user data is sent to external services.

## Compliance Checklist

- [x] All dependencies checked for compatible licenses
- [x] SAM 2.1 checkpoint license verified (Apache 2.0)
- [x] FFmpeg GPL flags noted for distribution awareness
- [x] No commercial API keys required
- [x] Fully offline-capable after model download
