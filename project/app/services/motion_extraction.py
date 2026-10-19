"""Motion extraction service — computes motion data from mask sequences."""

from __future__ import annotations

import math

import cv2
import numpy as np

from app.schemas import BoundingBox, FrameMotion, SceneMotion


def compute_frame_motion(
    mask: np.ndarray,
    frame_index: int,
    reference_bbox: BoundingBox | None = None,
) -> FrameMotion | None:
    """Extract motion data from a single binary mask.

    Computes centroid, bounding box, scale (relative to reference), rotation,
    opacity (fill ratio), and visibility.

    Args:
        mask: Binary mask (H, W), uint8, 0 or 255.
        frame_index: Frame index in the scene.
        reference_bbox: Reference bounding box for scale calculation.
            If None, scale is 1.0.

    Returns:
        FrameMotion or None if the mask is empty (object not visible).
    """
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return FrameMotion(
            frame_index=frame_index,
            centroid_x=0.0,
            centroid_y=0.0,
            bbox=BoundingBox(x=0, y=0, width=0, height=0),
            scale_x=0.0,
            scale_y=0.0,
            rotation_deg=0.0,
            opacity=0.0,
            visibility=False,
            area=0.0,
        )

    # Use largest contour
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    if area < 1.0:
        return FrameMotion(
            frame_index=frame_index,
            centroid_x=0.0,
            centroid_y=0.0,
            bbox=BoundingBox(x=0, y=0, width=0, height=0),
            scale_x=0.0,
            scale_y=0.0,
            rotation_deg=0.0,
            opacity=0.0,
            visibility=False,
            area=0.0,
        )

    # Centroid from moments
    moments = cv2.moments(largest)
    cx = float(moments["m10"] / moments["m00"]) if moments["m00"] != 0 else 0.0
    cy = float(moments["m01"] / moments["m00"]) if moments["m00"] != 0 else 0.0

    # Bounding box
    x, y, w, h = cv2.boundingRect(largest)
    bbox = BoundingBox(x=float(x), y=float(y), width=float(w), height=float(h))

    # Rotation from minimum area rectangle
    if len(largest) >= 5:
        rect = cv2.minAreaRect(largest)
        rotation_deg = float(rect[2])
        # Normalize rotation to [-90, 90]
        if rotation_deg > 90:
            rotation_deg -= 180
        if rotation_deg < -90:
            rotation_deg += 180
    else:
        rotation_deg = 0.0

    # Scale relative to reference
    scale_x = 1.0
    scale_y = 1.0
    if reference_bbox is not None and reference_bbox.width > 0 and reference_bbox.height > 0:
        scale_x = w / reference_bbox.width
        scale_y = h / reference_bbox.height

    # Opacity: ratio of mask pixels to bounding box area
    bbox_area = w * h
    opacity = area / bbox_area if bbox_area > 0 else 0.0

    return FrameMotion(
        frame_index=frame_index,
        centroid_x=round(cx, 2),
        centroid_y=round(cy, 2),
        bbox=bbox,
        scale_x=round(scale_x, 4),
        scale_y=round(scale_y, 4),
        rotation_deg=round(rotation_deg, 2),
        opacity=round(min(opacity, 1.0), 4),
        visibility=True,
        area=round(area, 2),
    )


def compute_scene_motion(
    masks: list[np.ndarray],
    selection_frame: int,
    selection_frame_in_list: int,
) -> SceneMotion:
    """Compute motion data for an entire scene from a sequence of masks.

    Args:
        masks: List of binary masks, one per frame in the scene.
        selection_frame: Absolute frame index of the user's selection.
        selection_frame_in_list: Index of the selection frame within the masks list.

    Returns:
        SceneMotion with per-frame motion data.
    """
    # First pass: get reference bbox from the selection frame
    ref_mask = masks[selection_frame_in_list]
    ref_contours, _ = cv2.findContours(ref_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    reference_bbox = None
    if ref_contours:
        largest = max(ref_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        reference_bbox = BoundingBox(x=float(x), y=float(y), width=float(w), height=float(h))

    # Second pass: compute motion for each frame
    frames: list[FrameMotion] = []
    for i, mask in enumerate(masks):
        motion = compute_frame_motion(mask, i, reference_bbox)
        if motion is not None:
            frames.append(motion)

    return SceneMotion(
        scene_id=0,  # Will be set by caller
        frames=frames,
        reference_bbox=reference_bbox,
    )


def smooth_motion(frames: list[FrameMotion], window: int = 5) -> list[FrameMotion]:
    """Apply moving-average smoothing to motion data.

    Args:
        frames: Raw per-frame motion data.
        window: Smoothing window size (odd number recommended).

    Returns:
        Smoothed motion data with same length.
    """
    if len(frames) <= 2:
        return frames

    n = len(frames)
    half_w = window // 2

    # Extract arrays
    cx = [f.centroid_x for f in frames]
    cy = [f.centroid_y for f in frames]
    sx = [f.scale_x for f in frames]
    sy = [f.scale_y for f in frames]
    rot = [f.rotation_deg for f in frames]

    # Handle rotation wrap-around by converting to sin/cos
    rot_sin = [math.sin(math.radians(r)) for r in rot]
    rot_cos = [math.cos(math.radians(r)) for r in rot]

    def smooth(arr: list[float], w: int) -> list[float]:
        result = []
        for i in range(len(arr)):
            start = max(0, i - w)
            end = min(len(arr), i + w + 1)
            result.append(sum(arr[start:end]) / (end - start))
        return result

    cx_s = smooth(cx, half_w)
    cy_s = smooth(cy, half_w)
    sx_s = smooth(sx, half_w)
    sy_s = smooth(sy, half_w)
    sin_s = smooth(rot_sin, half_w)
    cos_s = smooth(rot_cos, half_w)

    smoothed: list[FrameMotion] = []
    for i in range(n):
        angle = math.degrees(math.atan2(sin_s[i], cos_s[i]))
        smoothed.append(FrameMotion(
            frame_index=frames[i].frame_index,
            centroid_x=round(cx_s[i], 2),
            centroid_y=round(cy_s[i], 2),
            bbox=frames[i].bbox,
            scale_x=round(sx_s[i], 4),
            scale_y=round(sy_s[i], 4),
            rotation_deg=round(angle, 2),
            opacity=frames[i].opacity,
            visibility=frames[i].visibility,
            area=frames[i].area,
        ))

    return smoothed
