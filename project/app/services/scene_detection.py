"""Scene detection service using PySceneDetect."""

from __future__ import annotations

from pathlib import Path

from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector

from app.schemas import SceneInfo


def detect_scenes(
    video_path: str | Path,
    threshold: float = 27.0,
    min_scene_len_frames: int = 15,
) -> list[SceneInfo]:
    """Detect scene changes in a video using content-aware detection.

    Args:
        video_path: Path to the video file.
        threshold: Detection sensitivity (lower = more scenes).
        min_scene_len_frames: Minimum scene length in frames.

    Returns:
        List of SceneInfo objects sorted by start time.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len_frames)
    )

    scene_manager.detect_scenes(video=video)
    scene_list = scene_manager.get_scene_list()

    fps = video.frame_rate
    total_video_frames = int(video.duration.get_frames() or 0)

    scenes: list[SceneInfo] = []
    for i, (start, end) in enumerate(scene_list):
        start_frame = start.get_frames()
        end_frame = end.get_frames() - 1  # end is exclusive in PySceneDetect
        start_time = start_frame / fps
        end_time = end_frame / fps

        scenes.append(SceneInfo(
            scene_id=i,
            start_frame=start_frame,
            end_frame=end_frame,
            start_time_sec=round(start_time, 3),
            end_time_sec=round(end_time, 3),
            duration_sec=round(end_time - start_time, 3),
            frame_count=end_frame - start_frame + 1,
        ))

    # If no scenes detected, treat entire video as one scene
    if not scenes and total_video_frames > 0:
        duration = total_video_frames / fps
        scenes.append(SceneInfo(
            scene_id=0,
            start_frame=0,
            end_frame=total_video_frames - 1,
            start_time_sec=0.0,
            end_time_sec=round(duration, 3),
            duration_sec=round(duration, 3),
            frame_count=total_video_frames,
        ))

    return scenes
