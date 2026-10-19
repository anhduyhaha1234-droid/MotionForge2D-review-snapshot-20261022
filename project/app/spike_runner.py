"""Vertical spike runner — end-to-end pipeline for Milestone 0.

This script demonstrates the full MotionForge pipeline:
1. Probe video metadata
2. Detect scenes
3. Extract frames from a scene
4. Segment an object (SAM2 or fallback)
5. Propagate mask across scene
6. Extract motion data
7. Composite replacement image
8. Render output video with audio

Usage:
    python -m app.spike_runner --video input.mp4 --replacement sprite.png --scene 0
"""

from __future__ import annotations

import argparse
import json
import logging
import time
import tracemalloc
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.adapters.segmentation import create_segmentation_adapter
from app.config import config
from app.schemas import (
    ObjectKind,
    ProjectData,
    SceneMotion,
    SelectionInput,
    SelectionMode,
    TrackedObject,
)
from app.services.compositing import (
    composite_object,
    create_debug_overlay,
    load_replacement_image,
)
from app.services.frame_extraction import extract_frames
from app.services.motion_extraction import compute_scene_motion, smooth_motion
from app.services.render import render_video
from app.services.scene_detection import detect_scenes
from app.services.video_probe import extract_audio, probe_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("motionforge.spike")


def find_centroid_of_largest_region(frame: np.ndarray) -> tuple[float, float]:
    """Auto-detect the largest object in a frame by color variance.

    Used for automatic point selection in the spike when no manual input.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (21, 21), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        h, w = frame.shape[:2]
        return float(w) / 2, float(h) / 2

    largest = max(contours, key=cv2.contourArea)
    moments = cv2.moments(largest)
    if moments["m00"] == 0:
        h, w = frame.shape[:2]
        return float(w) / 2, float(h) / 2

    cx = float(moments["m10"] / moments["m00"])
    cy = float(moments["m01"] / moments["m00"])
    return cx, cy


def run_spike(
    video_path: str,
    replacement_path: str | None = None,
    scene_index: int = 0,
    point_x: float | None = None,
    point_y: float | None = None,
    bbox_x: float | None = None,
    bbox_y: float | None = None,
    bbox_w: float | None = None,
    bbox_h: float | None = None,
    backend: str = "contour",
    output_dir: str | None = None,
    project_name: str = "spike_project",
) -> dict[str, Any]:
    """Run the full vertical spike pipeline.

    Returns:
        Dict with paths to all outputs and benchmark data.
    """
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    out_dir = Path(output_dir) if output_dir else config.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {"steps": {}}
    timings: dict[str, float] = {}

    # ─── Start tracking ───────────────────────────────────────────────────
    tracemalloc.start()
    t_total_start = time.perf_counter()

    # ─── Step 1: Video Probe ──────────────────────────────────────────────
    logger.info("Step 1: Probing video metadata...")
    t0 = time.perf_counter()
    metadata = probe_video(video_path)
    timings["probe"] = time.perf_counter() - t0
    logger.info(f"  Video: {metadata.width}x{metadata.height}, {metadata.fps} fps, "
                f"{metadata.duration_seconds}s, {metadata.total_frames} frames, "
                f"codec={metadata.codec}, audio={metadata.has_audio}")
    results["metadata"] = metadata.model_dump()

    # ─── Step 2: Scene Detection ──────────────────────────────────────────
    logger.info("Step 2: Detecting scenes...")
    t0 = time.perf_counter()
    scenes = detect_scenes(video_path)
    timings["scene_detect"] = time.perf_counter() - t0
    logger.info(f"  Found {len(scenes)} scene(s)")
    for s in scenes:
        logger.info(f"    Scene {s.scene_id}: frames {s.start_frame}-{s.end_frame} "
                    f"({s.duration_sec:.2f}s)")
    results["scenes"] = [s.model_dump() for s in scenes]

    if scene_index >= len(scenes):
        raise ValueError(f"Scene {scene_index} not found (only {len(scenes)} scenes)")

    scene = scenes[scene_index]

    # ─── Step 3: Audio Extraction ─────────────────────────────────────────
    audio_path = None
    if metadata.has_audio:
        logger.info("Step 3: Extracting audio...")
        t0 = time.perf_counter()
        audio_path = out_dir / "audio" / "original_audio.aac"
        try:
            extract_audio(video_path, audio_path)
            timings["audio_extract"] = time.perf_counter() - t0
            logger.info(f"  Audio extracted to: {audio_path}")
        except Exception as e:
            logger.warning(f"  Audio extraction failed: {e}")
            audio_path = None
    else:
        logger.info("Step 3: No audio track found, skipping.")

    # ─── Step 4: Frame Extraction ─────────────────────────────────────────
    logger.info(f"Step 4: Extracting frames for scene {scene_index}...")
    t0 = time.perf_counter()
    frames_dir = out_dir / "frames" / f"scene_{scene_index}"
    frame_paths = extract_frames(video_path, frames_dir, scene)
    timings["frame_extract"] = time.perf_counter() - t0
    logger.info(f"  Extracted {len(frame_paths)} frames")
    results["frame_count"] = len(frame_paths)

    if not frame_paths:
        raise RuntimeError("No frames extracted")

    # ─── Step 5: Selection ────────────────────────────────────────────────
    logger.info("Step 5: Setting up selection...")
    # Use middle frame for selection
    sel_idx = len(frame_paths) // 2
    sel_frame = cv2.imread(str(frame_paths[sel_idx]))

    if point_x is not None and point_y is not None:
        selection = SelectionInput(
            mode=SelectionMode.POINT,
            frame_index=sel_idx,
            x=point_x,
            y=point_y,
        )
        logger.info(f"  Using point ({point_x}, {point_y}) at frame {sel_idx}")
    elif bbox_x is not None and bbox_y is not None and bbox_w is not None and bbox_h is not None:
        selection = SelectionInput(
            mode=SelectionMode.BBOX,
            frame_index=sel_idx,
            x=bbox_x,
            y=bbox_y,
            width=bbox_w,
            height=bbox_h,
        )
        logger.info(f"  Using bbox ({bbox_x},{bbox_y},{bbox_w},{bbox_h}) at frame {sel_idx}")
    else:
        # Auto-detect: find centroid of largest region
        if sel_frame is None:
            raise RuntimeError(f"Could not read selection frame: {frame_paths[sel_idx]}")
        cx, cy = find_centroid_of_largest_region(sel_frame)
        selection = SelectionInput(
            mode=SelectionMode.POINT,
            frame_index=sel_idx,
            x=cx,
            y=cy,
        )
        logger.info(f"  Auto-detected point ({cx:.0f}, {cy:.0f}) at frame {sel_idx}")

    results["selection"] = selection.model_dump()

    # ─── Step 6: Segmentation ─────────────────────────────────────────────
    logger.info(f"Step 6: Segmenting with {backend} backend...")
    t0 = time.perf_counter()

    seg_kwargs: dict[str, object] = {}
    if backend == "sam2":
        seg_kwargs = {
            "model_cfg": config.sam2_model_cfg,
            "checkpoint": config.sam2_checkpoint,
        }
    seg_adapter = create_segmentation_adapter(backend=backend, **seg_kwargs)

    # Generate initial mask
    if sel_frame is None:
        raise RuntimeError(f"Could not read selection frame: {frame_paths[sel_idx]}")
    initial_mask = seg_adapter.segment_frame(sel_frame, selection)
    timings["segment_initial"] = time.perf_counter() - t0
    logger.info(f"  Initial mask generated: {np.count_nonzero(initial_mask)} nonzero pixels")

    # Save initial mask debug
    debug_dir = out_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(debug_dir / "initial_mask.png"), initial_mask)
    init_debug = create_debug_overlay(sel_frame, initial_mask)
    cv2.imwrite(str(debug_dir / "initial_overlay.png"), init_debug)

    # ─── Step 7: Mask Propagation ─────────────────────────────────────────
    logger.info("Step 7: Propagating masks across scene...")
    t0 = time.perf_counter()

    # Load all frames
    all_frames: list[np.ndarray] = []
    for p in frame_paths:
        img = cv2.imread(str(p))
        if img is None:
            raise RuntimeError(f"Could not read frame: {p}")
        all_frames.append(img)

    # Propagate masks
    masks = seg_adapter.propagate_masks(all_frames, initial_mask, sel_idx)
    timings["mask_propagation"] = time.perf_counter() - t0
    logger.info(f"  Propagated {len(masks)} masks")

    # Save mask overlays
    mask_dir = out_dir / "masks" / f"scene_{scene_index}"
    mask_dir.mkdir(parents=True, exist_ok=True)

    for i, mask in enumerate(masks):
        if i % 10 == 0 or i == len(masks) - 1:  # Save every 10th + last
            cv2.imwrite(str(mask_dir / f"mask_{i:06d}.png"), mask)
            debug_img = create_debug_overlay(all_frames[i], mask)
            cv2.imwrite(str(debug_dir / f"overlay_{i:06d}.png"), debug_img)

    seg_adapter.cleanup()
    timings["segment_total"] = timings["segment_initial"] + timings["mask_propagation"]

    # ─── Step 8: Motion Extraction ────────────────────────────────────────
    logger.info("Step 8: Extracting motion data...")
    t0 = time.perf_counter()
    motion = compute_scene_motion(masks, sel_idx, sel_idx)
    motion.scene_id = scene_index
    motion_smoothed = SceneMotion(
        scene_id=scene_index,
        frames=smooth_motion(motion.frames),
        reference_bbox=motion.reference_bbox,
    )
    timings["motion_extraction"] = time.perf_counter() - t0
    logger.info(f"  Motion extracted: {len(motion_smoothed.frames)} frames, "
                f"ref bbox={motion_smoothed.reference_bbox}")

    # Save motion data as JSON
    motion_json_path = out_dir / "motion_data.json"
    with open(motion_json_path, "w") as f:
        json.dump(motion_smoothed.model_dump(), f, indent=2)
    results["motion_data_path"] = str(motion_json_path)

    # ─── Step 9: Compositing + Render ─────────────────────────────────────
    if replacement_path and Path(replacement_path).exists():
        logger.info("Step 9: Compositing replacement image...")
        t0 = time.perf_counter()

        # Load replacement
        ref_bbox = motion_smoothed.reference_bbox
        if ref_bbox:
            rep_w = max(1, int(ref_bbox.width))
            rep_h = max(1, int(ref_bbox.height))
        else:
            rep_w, rep_h = 100, 100

        replacement = load_replacement_image(replacement_path, rep_w, rep_h)

        # Composite each frame
        composited_dir = out_dir / "renders" / f"scene_{scene_index}_composited"
        composited_dir.mkdir(parents=True, exist_ok=True)

        composited_paths: list[Path] = []
        for i, (frame, mask) in enumerate(zip(all_frames, masks)):
            frame_motion = motion_smoothed.frames[i] if i < len(motion_smoothed.frames) else None
            if frame_motion and frame_motion.visibility:
                result = composite_object(frame, mask, replacement, frame_motion)
            else:
                result = frame

            out_frame_path = composited_dir / f"frame_{i:06d}.png"
            cv2.imwrite(str(out_frame_path), result)
            composited_paths.append(out_frame_path)

        timings["compositing"] = time.perf_counter() - t0
        logger.info(f"  Composited {len(composited_paths)} frames")

        # Render video
        logger.info("Step 10: Rendering output video...")
        t0 = time.perf_counter()
        output_video = out_dir / "renders" / f"scene_{scene_index}_output.mp4"
        render_video(composited_dir, output_video, metadata, audio_path)
        timings["render"] = time.perf_counter() - t0
        logger.info(f"  Rendered to: {output_video}")
        results["output_video"] = str(output_video)
    else:
        logger.info("Step 9: No replacement image, rendering original frames...")
        t0 = time.perf_counter()
        output_video = out_dir / "renders" / f"scene_{scene_index}_original.mp4"
        render_video(frames_dir, output_video, metadata, audio_path)
        timings["render"] = time.perf_counter() - t0
        results["output_video"] = str(output_video)

    # ─── Project JSON ─────────────────────────────────────────────────────
    logger.info("Saving project JSON...")
    project_path = out_dir / "project.json"
    project = ProjectData(
        name=project_name,
        source_video=str(video_path_obj.resolve()),
        video_metadata=metadata,
        scenes=scenes,
        objects=[
            TrackedObject(
                object_id="obj_0",
                name="Spike Object",
                kind=ObjectKind.CHARACTER,
                selection=selection,
                scene_id=scene_index,
                replacement_image=replacement_path,
                motion=motion_smoothed,
            )
        ],
    )
    with open(project_path, "w") as f:
        json.dump(project.model_dump(), f, indent=2, default=str)
    results["project_json"] = str(project_path)
    logger.info(f"  Project saved to: {project_path}")

    # ─── Benchmarks ───────────────────────────────────────────────────────
    t_total = time.perf_counter() - t_total_start
    timings["total"] = t_total

    _, peak_ram = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # GPU memory (if available)
    gpu_peak_mb = 0.0
    try:
        import torch
        if torch.cuda.is_available():
            gpu_peak_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        pass

    benchmark = {
        "timings_seconds": {k: round(v, 3) for k, v in timings.items()},
        "peak_ram_mb": round(peak_ram / (1024 * 1024), 2),
        "gpu_peak_mb": round(gpu_peak_mb, 2),
        "total_frames_processed": len(frame_paths),
        "fps_throughput": round(len(frame_paths) / t_total, 2) if t_total > 0 else 0,
    }
    results["benchmark"] = benchmark

    # Save benchmark
    bench_path = out_dir / "benchmark.json"
    with open(bench_path, "w") as f:
        json.dump(benchmark, f, indent=2)
    results["benchmark_path"] = str(bench_path)

    logger.info("=" * 60)
    logger.info("SPIKE COMPLETE")
    logger.info(f"  Total time: {t_total:.2f}s")
    logger.info(f"  Peak RAM: {benchmark['peak_ram_mb']:.1f} MB")
    logger.info(f"  GPU peak: {benchmark['gpu_peak_mb']:.1f} MB")
    logger.info(f"  Throughput: {benchmark['fps_throughput']:.1f} fps")
    logger.info("=" * 60)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="MotionForge 2D Vertical Spike")
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--replacement", help="Replacement PNG image path")
    parser.add_argument("--scene", type=int, default=0, help="Scene index to process")
    parser.add_argument("--point-x", type=float, help="Selection point X")
    parser.add_argument("--point-y", type=float, help="Selection point Y")
    parser.add_argument("--bbox-x", type=float, help="Bounding box X")
    parser.add_argument("--bbox-y", type=float, help="Bounding box Y")
    parser.add_argument("--bbox-w", type=float, help="Bounding box width")
    parser.add_argument("--bbox-h", type=float, help="Bounding box height")
    parser.add_argument("--backend", choices=["sam2", "contour"], default="contour",
                        help="Segmentation backend")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--name", default="spike_project", help="Project name")

    args = parser.parse_args()

    run_spike(
        video_path=args.video,
        replacement_path=args.replacement,
        scene_index=args.scene,
        point_x=args.point_x,
        point_y=args.point_y,
        bbox_x=args.bbox_x,
        bbox_y=args.bbox_y,
        bbox_w=args.bbox_w,
        bbox_h=args.bbox_h,
        backend=args.backend,
        output_dir=args.output_dir,
        project_name=args.name,
    )


if __name__ == "__main__":
    main()
