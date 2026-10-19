"""Segmentation adapter — wraps SAM 2.1 for mask generation and propagation.

This module provides an adapter interface so the AI model can be swapped
without changing the rest of the pipeline.
"""

from __future__ import annotations

import abc
import os
import shutil
import tempfile
from pathlib import Path

import cv2
import numpy as np
import torch

from app.schemas import SelectionInput, SelectionMode


class SegmentationAdapter(abc.ABC):
    """Abstract interface for video object segmentation."""

    @abc.abstractmethod
    def segment_frame(
        self,
        frame: np.ndarray,
        selection: SelectionInput,
    ) -> np.ndarray:
        """Generate a binary mask for a single frame.

        Args:
            frame: BGR image (H, W, 3), uint8.
            selection: User's point or bbox selection.

        Returns:
            Binary mask (H, W), uint8 with values 0 or 255.
        """
        ...

    @abc.abstractmethod
    def propagate_masks(
        self,
        frames: list[np.ndarray],
        initial_mask: np.ndarray,
        initial_frame_idx: int,
    ) -> list[np.ndarray]:
        """Propagate a mask across multiple frames.

        Args:
            frames: List of BGR images (H, W, 3), uint8.
            initial_mask: Binary mask at the initial frame.
            initial_frame_idx: Index of the initial frame in the list.

        Returns:
            List of binary masks, one per frame. Same length as frames.
        """
        ...

    @abc.abstractmethod
    def cleanup(self) -> None:
        """Release GPU memory and resources."""
        ...


class SAM2Adapter(SegmentationAdapter):
    """SAM 2.1 based segmentation adapter.

    Uses SAM2's video predictor for temporal mask propagation.
    Frames are written to a temp directory since SAM2 expects a video_path.
    """

    def __init__(
        self,
        model_cfg: str = "configs/sam2.1/sam2.1_hiera_l.yaml",
        checkpoint: str = "",
        device: str = "cuda",
    ) -> None:
        self.model_cfg = model_cfg
        self.checkpoint = checkpoint
        self.device = device
        self._predictor = None
        self._tmp_dir: str | None = None

    def _ensure_model(self) -> None:
        """Lazy-load the SAM 2 model."""
        if self._predictor is not None:
            return

        from sam2.build_sam import build_sam2_video_predictor

        if not self.checkpoint or not Path(self.checkpoint).exists():
            raise FileNotFoundError(
                f"SAM 2 checkpoint not found: {self.checkpoint}. "
                "Run scripts/download_models.sh first."
            )

        self._predictor = build_sam2_video_predictor(
            config_file=self.model_cfg,
            ckpt_path=self.checkpoint,
            device=self.device,
        )

    def _frames_to_dir(self, frames: list[np.ndarray]) -> str:
        """Write frames to a temp directory for SAM2 init_state."""
        if self._tmp_dir:
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
        self._tmp_dir = tempfile.mkdtemp(prefix="motionforge_sam2_")
        for i, frame in enumerate(frames):
            path = os.path.join(self._tmp_dir, f"{i:06d}.jpg")
            cv2.imwrite(path, frame)
        return self._tmp_dir

    def segment_frame(
        self,
        frame: np.ndarray,
        selection: SelectionInput,
    ) -> np.ndarray:
        """Generate mask for a single frame using SAM 2 video predictor."""
        self._ensure_model()
        assert self._predictor is not None

        h, w = frame.shape[:2]

        # Write single frame to temp dir
        frame_dir = self._frames_to_dir([frame])

        # Initialize with single frame
        inference_state = self._predictor.init_state(video_path=frame_dir)

        # Prepare prompt
        if selection.mode == SelectionMode.POINT:
            points = np.array([[selection.x, selection.y]], dtype=np.float32)
            labels = np.array([1], dtype=np.int32)
            box = None
        elif selection.mode == SelectionMode.BBOX:
            assert selection.width is not None and selection.height is not None
            box = np.array([[
                selection.x,
                selection.y,
                selection.x + selection.width,
                selection.y + selection.height,
            ]], dtype=np.float32)
            points = None
            labels = None
        else:
            raise ValueError(f"Unknown selection mode: {selection.mode}")

        # Run inference
        _, out_obj_ids, out_mask_logits = self._predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=0,
            obj_id=0,
            points=points,
            labels=labels,
            box=box,
        )

        # Extract mask
        mask_logits = out_mask_logits[0]
        mask = (mask_logits > 0.0).cpu().numpy().squeeze()
        mask_uint8 = (mask * 255).astype(np.uint8)

        # Resize to original if needed
        if mask_uint8.shape[:2] != (h, w):
            mask_uint8 = cv2.resize(mask_uint8, (w, h), interpolation=cv2.INTER_NEAREST)

        self._predictor.reset_state(inference_state)
        return mask_uint8

    def propagate_masks(
        self,
        frames: list[np.ndarray],
        initial_mask: np.ndarray,
        initial_frame_idx: int,
    ) -> list[np.ndarray]:
        """Propagate mask across frames using SAM 2 video predictor.

        SAM2 propagates forward from the prompt frame. For backward propagation
        (when selection is in the middle), we run two passes: forward and reverse.
        """
        self._ensure_model()
        assert self._predictor is not None

        if not frames:
            return []

        h, w = frames[0].shape[:2]
        n_frames = len(frames)

        # Write frames to temp directory
        frame_dir = self._frames_to_dir(frames)

        # Initialize video state
        inference_state = self._predictor.init_state(video_path=frame_dir)

        # Add mask prompt at the initial frame — SAM2 expects 2D tensor (H, W)
        mask_resized = initial_mask
        if initial_mask.shape[:2] != (h, w):
            mask_resized = cv2.resize(initial_mask, (w, h), interpolation=cv2.INTER_NEAREST)

        mask_tensor = torch.from_numpy(
            (mask_resized > 127).astype(np.float32)
        )  # (H, W) — SAM2 requires 2D

        _, out_obj_ids, out_mask_logits = self._predictor.add_new_mask(
            inference_state=inference_state,
            frame_idx=initial_frame_idx,
            obj_id=0,
            mask=mask_tensor,
        )

        # Forward propagation from selection frame to end
        masks: list[np.ndarray | None] = [None] * n_frames

        for frame_idx, _obj_ids, mask_logits in self._predictor.propagate_in_video(
            inference_state,
            start_frame_idx=initial_frame_idx,
        ):
            if 0 <= frame_idx < n_frames and len(mask_logits) > 0:
                mask = (mask_logits[0] > 0.0).cpu().numpy().squeeze()
                masks[frame_idx] = (mask * 255).astype(np.uint8)

        # Backward propagation from selection frame to start
        if initial_frame_idx > 0:
            for frame_idx, _obj_ids, mask_logits in self._predictor.propagate_in_video(
                inference_state,
                start_frame_idx=initial_frame_idx,
                reverse=True,
            ):
                if 0 <= frame_idx < n_frames and len(mask_logits) > 0 and masks[frame_idx] is None:
                    mask = (mask_logits[0] > 0.0).cpu().numpy().squeeze()
                    masks[frame_idx] = (mask * 255).astype(np.uint8)

        self._predictor.reset_state(inference_state)

        # Fill any remaining None masks with zeros
        result: list[np.ndarray] = []
        for _i, m in enumerate(masks):
            if m is None:
                result.append(np.zeros((h, w), dtype=np.uint8))
            else:
                # Resize if SAM2 returned different resolution
                if m.shape[:2] != (h, w):
                    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
                result.append(m)

        return result

    def cleanup(self) -> None:
        """Release GPU resources and clean temp files."""
        self._predictor = None
        if self._tmp_dir:
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
            self._tmp_dir = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class SimpleContourAdapter(SegmentationAdapter):
    """Fallback adapter using OpenCV contour detection (no GPU required).

    Used for testing or when SAM 2 is not available.
    NOTE: Template matching propagation is unreliable for moving objects.
    """

    def segment_frame(
        self,
        frame: np.ndarray,
        selection: SelectionInput,
    ) -> np.ndarray:
        """Generate mask using GrabCut with the selection as init."""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        if selection.mode == SelectionMode.POINT:
            x, y = int(selection.x), int(selection.y)
            flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
            cv2.floodFill(
                frame, flood_mask, (x, y), 255,
                loDiff=(20, 20, 20), upDiff=(20, 20, 20),
                flags=cv2.FLOODFILL_MASK_ONLY | (255 << 8),
            )
            mask = flood_mask[1:-1, 1:-1]

        elif selection.mode == SelectionMode.BBOX:
            assert selection.width is not None and selection.height is not None
            x1 = max(0, int(selection.x))
            y1 = max(0, int(selection.y))
            x2 = min(w, int(selection.x + selection.width))
            y2 = min(h, int(selection.y + selection.height))

            bgd_model = np.zeros((1, 65), dtype=np.float64)
            fgd_model = np.zeros((1, 65), dtype=np.float64)
            rect = (x1, y1, x2 - x1, y2 - y1)

            grab_mask = np.zeros((h, w), dtype=np.uint8)
            try:
                cv2.grabCut(frame, grab_mask, rect, bgd_model, fgd_model,
                            iterCount=5, mode=cv2.GC_INIT_WITH_RECT)
                mask = np.where(
                    (grab_mask == cv2.GC_FGD) | (grab_mask == cv2.GC_PR_FGD),
                    255, 0
                ).astype(np.uint8)
            except cv2.error:
                mask[y1:y2, x1:x2] = 255

        return mask

    def propagate_masks(
        self,
        frames: list[np.ndarray],
        initial_mask: np.ndarray,
        initial_frame_idx: int,
    ) -> list[np.ndarray]:
        """Propagate mask using template matching (unreliable for moving objects)."""
        if not frames:
            return []

        h, w = frames[0].shape[:2]
        masks: list[np.ndarray] = [np.zeros((h, w), dtype=np.uint8)] * len(frames)
        masks[initial_frame_idx] = initial_mask.copy()

        contours, _ = cv2.findContours(
            initial_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return masks

        moments = cv2.moments(initial_mask)
        if moments["m00"] == 0:
            return masks

        x, y, tw, th = cv2.boundingRect(max(contours, key=cv2.contourArea))
        template = frames[initial_frame_idx][y:y+th, x:x+tw]

        if template.size == 0:
            return masks

        # Forward propagation
        for i in range(initial_frame_idx + 1, len(frames)):
            frame_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            tmpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            result = cv2.matchTemplate(frame_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > 0.3:
                new_mask = np.zeros((h, w), dtype=np.uint8)
                new_mask[max_loc[1]:max_loc[1]+th, max_loc[0]:max_loc[0]+tw] = 255
                masks[i] = new_mask

        # Backward propagation
        for i in range(initial_frame_idx - 1, -1, -1):
            frame_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            tmpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            result = cv2.matchTemplate(frame_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > 0.3:
                new_mask = np.zeros((h, w), dtype=np.uint8)
                new_mask[max_loc[1]:max_loc[1]+th, max_loc[0]:max_loc[0]+tw] = 255
                masks[i] = new_mask

        return masks

    def cleanup(self) -> None:
        """No resources to release."""
        pass


def create_segmentation_adapter(
    backend: str = "sam2",
    **kwargs: object,
) -> SegmentationAdapter:
    """Factory function to create a segmentation adapter.

    Args:
        backend: "sam2" for SAM 2.1, "contour" for OpenCV fallback.
        **kwargs: Additional arguments passed to the adapter constructor.

    Returns:
        A SegmentationAdapter instance.
    """
    if backend == "sam2":
        adapter_cls: type[SegmentationAdapter] = SAM2Adapter
    elif backend == "contour":
        adapter_cls = SimpleContourAdapter
    else:
        raise ValueError(f"Unknown segmentation backend: {backend}")
    return adapter_cls(**kwargs)
