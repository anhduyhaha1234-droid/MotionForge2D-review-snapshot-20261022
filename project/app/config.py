"""Global configuration for MotionForge 2D backend."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application configuration loaded from environment or defaults."""

    # Paths
    project_root: Path = field(default_factory=lambda: Path(os.environ.get(
        "MOTIONFORGE_ROOT", str(Path.home() / "MotionForge2D")
    )))
    models_dir: Path = field(default_factory=lambda: Path(os.environ.get(
        "MOTIONFORGE_MODELS", str(Path.home() / "MotionForge2D" / "models_checkpoints")
    )))
    output_dir: Path = field(default_factory=lambda: Path(os.environ.get(
        "MOTIONFORGE_OUTPUT", str(Path.home() / "MotionForge2D" / "output")
    )))

    # SAM 2.1
    sam2_model_cfg: str = "configs/sam2.1/sam2.1_hiera_l.yaml"
    sam2_checkpoint: str = ""  # Set after download

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Processing
    max_frames_per_scene: int = 1000
    mask_propagation_batch: int = 8

    def __post_init__(self) -> None:
        if not self.sam2_checkpoint:
            object.__setattr__(
                self,
                "sam2_checkpoint",
                str(self.models_dir / "sam2.1_hiera_large.pt"),
            )

    def ensure_dirs(self) -> None:
        """Create output and model directories if they don't exist."""
        for subdir in ["scenes", "frames", "masks", "renders", "debug", "audio"]:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)


# Singleton config
config = AppConfig()
