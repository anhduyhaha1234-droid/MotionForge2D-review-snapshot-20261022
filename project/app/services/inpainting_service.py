"""Inpainting service — mask dilation and background reconstruction."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class InpaintingService:
    """Remove objects from frames by dilating masks and inpainting."""

    def dilate_mask(
        self,
        mask: np.ndarray,
        kernel_size: int = 5,
        iterations: int = 2,
    ) -> np.ndarray:
        """Dilate a binary mask to cover object edges.

        Args:
            mask: Binary mask (0/255 uint8).
            kernel_size: Dilation kernel size (3-8px radius).
            iterations: Number of dilation iterations.

        Returns:
            Dilated mask.
        """
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size),
        )
        return cv2.dilate(mask, kernel, iterations=iterations)

    def inpaint_frame(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        method: str = "telea",
        radius: int = 3,
    ) -> np.ndarray:
        """Inpaint masked region of a frame.

        Args:
            frame: BGR image.
            mask: Binary mask (0/255 uint8, white = area to inpaint).
            method: "telea" (Telea) or "ns" (Navier-Stokes).
            radius: Inpainting radius.

        Returns:
            Inpainted frame.
        """
        flag = cv2.INPAINT_NS if method == "ns" else cv2.INPAINT_TELEA
        return cv2.inpaint(frame, mask, radius, flag)

    def process_frame(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        dilate_kernel: int = 5,
        dilate_iterations: int = 2,
        inpaint_method: str = "telea",
        inpaint_radius: int = 3,
    ) -> np.ndarray:
        """Full pipeline: dilate mask then inpaint.

        Args:
            frame: BGR image.
            mask: Binary mask (0/255).
            dilate_kernel: Kernel size for dilation.
            dilate_iterations: Dilation iterations.
            inpaint_method: "telea" or "ns".
            inpaint_radius: Inpainting radius.

        Returns:
            Clean background frame.
        """
        dilated = self.dilate_mask(mask, dilate_kernel, dilate_iterations)
        return self.inpaint_frame(frame, dilated, inpaint_method, inpaint_radius)

    def process_scene_frames(
        self,
        frame_paths: list[Path],
        mask_paths: list[Path],
        output_dir: Path,
        dilate_kernel: int = 5,
        dilate_iterations: int = 2,
    ) -> list[Path]:
        """Batch inpaint all frames in a scene.

        Args:
            frame_paths: Paths to original frames.
            mask_paths: Paths to mask frames (same order).
            output_dir: Directory to write cleaned frames.
            dilate_kernel: Dilation kernel size.
            dilate_iterations: Dilation iterations.

        Returns:
            List of paths to cleaned frames.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[Path] = []

        for frame_path, mask_path in zip(frame_paths, mask_paths):
            frame = cv2.imread(str(frame_path))
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

            if frame is None or mask is None:
                continue

            # Ensure binary mask
            _, mask_bin = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

            cleaned = self.process_frame(
                frame, mask_bin, dilate_kernel, dilate_iterations,
            )

            out_path = output_dir / frame_path.name
            cv2.imwrite(str(out_path), cleaned)
            results.append(out_path)

        return results
