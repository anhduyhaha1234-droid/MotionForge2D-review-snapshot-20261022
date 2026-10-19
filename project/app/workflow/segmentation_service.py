"""Segmentation service — mask preview and propagation using SAM2 or contour."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from app.adapters.segmentation import create_segmentation_adapter
from app.config import AppConfig
from app.schemas import SelectionInput


class SegmentationService:
    """Mask generation and propagation."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def preview_mask(
        self,
        frame_path: str | Path,
        selection: SelectionInput,
        backend: str = "contour",
    ) -> np.ndarray:
        """Generate a mask preview for a single frame."""
        frame = cv2.imread(str(frame_path))
        if frame is None:
            raise FileNotFoundError(f"Frame not found: {frame_path}")

        kwargs: dict[str, object] = {}
        if backend == "sam2":
            kwargs = {
                "model_cfg": self._config.sam2_model_cfg,
                "checkpoint": self._config.sam2_checkpoint,
            }

        adapter = create_segmentation_adapter(backend=backend, **kwargs)
        try:
            mask = adapter.segment_frame(frame, selection)
        finally:
            adapter.cleanup()
        return mask

    def propagate_masks(
        self,
        frame_paths: list[Path],
        initial_mask: np.ndarray,
        initial_frame_idx: int,
        backend: str = "contour",
        progress_cb: Callable[[float, str], None] | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> list[np.ndarray]:
        """Propagate mask across multiple frames."""
        if not frame_paths:
            return []

        if progress_cb:
            progress_cb(0, "Loading frames")

        frames = []
        for p in frame_paths:
            if is_cancelled and is_cancelled():
                return []
            img = cv2.imread(str(p))
            if img is None:
                raise FileNotFoundError(f"Frame not found: {p}")
            frames.append(img)

        if progress_cb:
            progress_cb(30, "Running propagation")

        kwargs: dict[str, object] = {}
        if backend == "sam2":
            kwargs = {
                "model_cfg": self._config.sam2_model_cfg,
                "checkpoint": self._config.sam2_checkpoint,
            }

        adapter = create_segmentation_adapter(backend=backend, **kwargs)
        try:
            masks = adapter.propagate_masks(frames, initial_mask, initial_frame_idx)
        finally:
            adapter.cleanup()

        if progress_cb:
            progress_cb(100, "Propagation complete")

        return masks
