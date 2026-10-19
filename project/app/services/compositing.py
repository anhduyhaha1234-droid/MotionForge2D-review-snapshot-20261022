"""Compositing service — replaces objects in frames using masks and motion data."""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from app.schemas import FrameMotion


def load_replacement_image(path: str | Path, target_width: int, target_height: int) -> np.ndarray:
    """Load and resize a replacement PNG image.

    Args:
        path: Path to the PNG file (with alpha channel).
        target_width: Desired width.
        target_height: Desired height.

    Returns:
        BGRA image (H, W, 4) resized to target dimensions.
    """
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Replacement image not found: {path}")

    # Ensure alpha channel exists
    if img.shape[2] == 3:
        alpha = np.full(img.shape[:2] + (1,), 255, dtype=np.uint8)
        img = np.concatenate([img, alpha], axis=2)

    # Resize
    img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
    return img


def composite_object(
    frame: np.ndarray,
    mask: np.ndarray,
    replacement: np.ndarray,
    motion: FrameMotion,
    anchor_x: float = 0.5,
    anchor_y: float = 0.5,
) -> np.ndarray:
    """Composite a replacement image onto a frame at the tracked position.

    Args:
        frame: Background frame BGR (H, W, 3).
        mask: Object mask (H, W), uint8 0/255.
        replacement: Replacement image BGRA (H, W, 4).
        motion: Motion data for this frame.
        anchor_x: Horizontal anchor point (0=left, 1=right).
        anchor_y: Vertical anchor point (0=top, 1=bottom).

    Returns:
        Composited frame BGR (H, W, 3).
    """
    result = frame.copy()
    h, w = frame.shape[:2]

    if not motion.visibility or motion.area < 1:
        return result

    # Get the target bounding box from motion data
    bw = int(motion.bbox.width)
    bh = int(motion.bbox.height)

    if bw < 1 or bh < 1:
        return result

    # Scale replacement to match the bounding box
    scale_x = motion.scale_x if motion.scale_x > 0 else 1.0
    scale_y = motion.scale_y if motion.scale_y > 0 else 1.0
    new_w = max(1, int(bw * scale_x))
    new_h = max(1, int(bh * scale_y))

    # Rotate replacement
    scaled = cv2.resize(replacement, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    if abs(motion.rotation_deg) > 0.5:
        center = (new_w // 2, new_h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, motion.rotation_deg, 1.0)
        # Calculate rotated image size
        cos_val = abs(rot_mat[0, 0])
        sin_val = abs(rot_mat[0, 1])
        rot_w = int(new_h * sin_val + new_w * cos_val)
        rot_h = int(new_h * cos_val + new_w * sin_val)
        rot_mat[0, 2] += (rot_w - new_w) / 2
        rot_mat[1, 2] += (rot_h - new_h) / 2

        rotated = cv2.warpAffine(
            scaled, rot_mat, (rot_w, rot_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )
        scaled = rotated
        new_w, new_h = rot_w, rot_h

    # Position: center replacement at the centroid
    paste_x = int(motion.centroid_x - new_w * anchor_x)
    paste_y = int(motion.centroid_y - new_h * anchor_y)

    # Alpha blend
    # Create the region of interest on the output frame
    # Handle edge clipping
    src_x1 = max(0, -paste_x)
    src_y1 = max(0, -paste_y)
    dst_x1 = max(0, paste_x)
    dst_y1 = max(0, paste_y)
    src_x2 = min(new_w, w - paste_x)
    src_y2 = min(new_h, h - paste_y)
    dst_x2 = min(w, paste_x + new_w)
    dst_y2 = min(h, paste_y + new_h)

    if dst_x1 >= dst_x2 or dst_y1 >= dst_y2:
        return result

    roi = scaled[src_y1:src_y2, src_x1:src_x2]
    if roi.shape[2] < 4:
        return result

    # Use mask from the original to determine where to place
    # Blend using alpha channel of replacement
    alpha = roi[:, :, 3:4].astype(np.float32) / 255.0

    # Optionally use the original mask to constrain placement
    mask_roi = mask[dst_y1:dst_y2, dst_x1:dst_x2]
    if mask_roi.shape != alpha.shape[:2]:
        mask_resized = cv2.resize(mask_roi, (alpha.shape[1], alpha.shape[0]))
    else:
        mask_resized = mask_roi
    mask_alpha = (mask_resized > 127).astype(np.float32)
    if len(mask_alpha.shape) == 2:
        mask_alpha = mask_alpha[:, :, np.newaxis]

    combined_alpha = alpha * mask_alpha

    bg = result[dst_y1:dst_y2, dst_x1:dst_x2].astype(np.float32)
    fg = roi[:, :, :3].astype(np.float32)
    blended = bg * (1 - combined_alpha) + fg * combined_alpha
    result[dst_y1:dst_y2, dst_x1:dst_x2] = blended.astype(np.uint8)

    return result


def create_debug_overlay(
    frame: np.ndarray,
    mask: np.ndarray,
    motion: FrameMotion | None = None,
) -> np.ndarray:
    """Create a debug visualization with mask overlay and motion data.

    Args:
        frame: Original BGR frame.
        mask: Binary mask.
        motion: Optional motion data to draw.

    Returns:
        Annotated frame with mask overlay (green), bbox, and centroid.
    """
    overlay = frame.copy()

    # Green mask overlay
    colored_mask = np.zeros_like(overlay)
    colored_mask[:, :, 1] = mask  # Green channel
    overlay = cv2.addWeighted(overlay, 0.7, colored_mask, 0.3, 0)

    # Draw contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)

    if motion and motion.visibility:
        # Draw bounding box
        bx, by = int(motion.bbox.x), int(motion.bbox.y)
        bw, bh = int(motion.bbox.width), int(motion.bbox.height)
        cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (0, 0, 255), 2)

        # Draw centroid
        cx, cy = int(motion.centroid_x), int(motion.centroid_y)
        cv2.circle(overlay, (cx, cy), 5, (255, 0, 0), -1)
        cv2.circle(overlay, (cx, cy), 8, (255, 0, 0), 2)

        # Draw rotation direction
        angle_rad = math.radians(motion.rotation_deg)
        line_len = 30
        ex = int(cx + line_len * math.cos(angle_rad))
        ey = int(cy + line_len * math.sin(angle_rad))
        cv2.arrowedLine(overlay, (cx, cy), (ex, ey), (0, 255, 255), 2)

        # Text info
        rot = motion.rotation_deg
        scl = motion.scale_x
        info = f"F{motion.frame_index} C({cx},{cy}) R{rot:.1f} S{scl:.2f}"
        cv2.putText(overlay, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return overlay
