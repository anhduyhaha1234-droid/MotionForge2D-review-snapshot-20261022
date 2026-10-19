"""Tests for project schema validation and motion calculation."""

from __future__ import annotations

import numpy as np

from app.schemas import (
    BoundingBox,
    FrameMotion,
    ObjectKind,
    ProjectData,
    SceneInfo,
    SelectionInput,
    SelectionMode,
    VideoMetadata,
)
from app.services.motion_extraction import (
    compute_frame_motion,
    compute_scene_motion,
    smooth_motion,
)

# ─── Schema Tests ─────────────────────────────────────────────────────────────

class TestVideoMetadata:
    def test_valid_metadata(self) -> None:
        meta = VideoMetadata(
            width=1920, height=1080, fps=30.0,
            duration_seconds=10.0, total_frames=300,
            codec="h264", has_audio=True,
        )
        assert meta.width == 1920
        assert meta.fps == 30.0
        assert meta.has_audio is True

    def test_defaults(self) -> None:
        meta = VideoMetadata(
            width=640, height=480, fps=24.0,
            duration_seconds=5.0, total_frames=120,
            codec="vp9", has_audio=False,
        )
        assert meta.audio_codec is None
        assert meta.file_size_bytes == 0


class TestSceneInfo:
    def test_scene_creation(self) -> None:
        scene = SceneInfo(
            scene_id=0,
            start_frame=0, end_frame=29,
            start_time_sec=0.0, end_time_sec=1.0,
            duration_sec=1.0, frame_count=30,
        )
        assert scene.frame_count == 30

    def test_duration_consistency(self) -> None:
        scene = SceneInfo(
            scene_id=1,
            start_frame=30, end_frame=59,
            start_time_sec=1.0, end_time_sec=2.0,
            duration_sec=1.0, frame_count=30,
        )
        assert scene.end_frame - scene.start_frame + 1 == scene.frame_count


class TestSelectionInput:
    def test_point_selection(self) -> None:
        sel = SelectionInput(
            mode=SelectionMode.POINT,
            frame_index=0, x=100.0, y=200.0,
        )
        assert sel.mode == SelectionMode.POINT
        assert sel.width is None
        assert sel.height is None

    def test_bbox_selection(self) -> None:
        sel = SelectionInput(
            mode=SelectionMode.BBOX,
            frame_index=5, x=10.0, y=20.0,
            width=50.0, height=60.0,
        )
        assert sel.mode == SelectionMode.BBOX
        assert sel.width == 50.0
        assert sel.height == 60.0


class TestProjectData:
    def test_create_minimal(self) -> None:
        project = ProjectData(name="Test", source_video="/tmp/test.mp4")
        assert project.version == "2.0.0"
        assert project.scenes == []
        assert project.objects == []

    def test_roundtrip(self, sample_project_data: dict) -> None:
        """Serialize and deserialize preserves all data."""
        project = ProjectData.model_validate(sample_project_data)
        serialized = project.model_dump()
        restored = ProjectData.model_validate(serialized)
        assert restored.name == sample_project_data["name"]
        assert len(restored.scenes) == 2
        assert restored.video_metadata is not None
        assert restored.video_metadata.width == 1920

    def test_schema_version(self, sample_project_data: dict) -> None:
        # v1.0.0 data loads fine — version is a string field, not validated
        project = ProjectData.model_validate(sample_project_data)
        assert project.version == "1.0.0"
        # New projects default to v2.0.0
        new_project = ProjectData(name="New", source_video="/tmp/test.mp4")
        assert new_project.version == "2.0.0"

    def test_with_tracked_object(self, sample_project_data: dict) -> None:
        data = sample_project_data.copy()
        data["objects"] = [
            {
                "object_id": "obj_0",
                "name": "Character A",
                "kind": "character",
                "selection": {
                    "mode": "point",
                    "frame_index": 10,
                    "x": 100.0,
                    "y": 200.0,
                },
                "scene_id": 0,
                "replacement_image": None,
                "motion": None,
            }
        ]
        project = ProjectData.model_validate(data)
        assert len(project.objects) == 1
        assert project.objects[0].kind == ObjectKind.CHARACTER


# ─── Motion Calculation Tests ─────────────────────────────────────────────────

class TestComputeFrameMotion:
    def test_visible_object(self, sample_mask: np.ndarray) -> None:
        """Mask with visible object should produce valid motion."""
        motion = compute_frame_motion(sample_mask, frame_index=0)
        assert motion is not None
        assert motion.visibility is True
        assert motion.area > 0
        # Centroid should be roughly at (50, 50) for a 20-80 rect
        assert 40 <= motion.centroid_x <= 60
        assert 40 <= motion.centroid_y <= 60
        # Bbox should be ~60x60
        assert abs(motion.bbox.width - 60) <= 2
        assert abs(motion.bbox.height - 60) <= 2

    def test_empty_mask(self) -> None:
        """Empty mask should return invisible motion."""
        import numpy as np
        empty = np.zeros((100, 100), dtype=np.uint8)
        motion = compute_frame_motion(empty, frame_index=0)
        assert motion is not None
        assert motion.visibility is False
        assert motion.area == 0.0

    def test_scale_relative_to_reference(self, sample_mask: np.ndarray) -> None:
        """Scale should be 1.0 when reference matches."""
        ref = BoundingBox(x=20, y=20, width=60, height=60)
        motion = compute_frame_motion(sample_mask, frame_index=0, reference_bbox=ref)
        assert motion is not None
        assert abs(motion.scale_x - 1.0) < 0.1
        assert abs(motion.scale_y - 1.0) < 0.1

    def test_scale_different_reference(self, sample_mask: np.ndarray) -> None:
        """Scale should be > 1.0 when object is larger than reference."""
        ref = BoundingBox(x=20, y=20, width=30, height=30)
        motion = compute_frame_motion(sample_mask, frame_index=0, reference_bbox=ref)
        assert motion is not None
        assert motion.scale_x > 1.5  # Object is ~60 wide, ref is 30

    def test_rotation_computed(self, sample_mask: np.ndarray) -> None:
        """Rotation should be a finite number."""
        motion = compute_frame_motion(sample_mask, frame_index=0)
        assert motion is not None
        assert isinstance(motion.rotation_deg, float)
        assert -90 <= motion.rotation_deg <= 90

    def test_opacity_fill_ratio(self, sample_mask: np.ndarray) -> None:
        """Opacity should represent the fill ratio of the bounding box."""
        motion = compute_frame_motion(sample_mask, frame_index=0)
        assert motion is not None
        # For a filled square, opacity should be close to 1.0
        assert 0.8 <= motion.opacity <= 1.0


class TestComputeSceneMotion:
    def test_basic_scene(self, sample_mask: np.ndarray) -> None:
        """Scene motion should have one frame per mask."""
        masks = [sample_mask] * 5
        motion = compute_scene_motion(masks, selection_frame=2, selection_frame_in_list=2)
        assert len(motion.frames) == 5
        assert motion.reference_bbox is not None

    def test_reference_from_selection_frame(self, sample_mask: np.ndarray) -> None:
        """Reference bbox should come from the selection frame."""
        import numpy as np
        # Make different masks: small at frame 0, large at frame 2
        small_mask = np.zeros((100, 100), dtype=np.uint8)
        small_mask[35:65, 35:65] = 255  # 30x30 centered

        masks = [small_mask, small_mask, sample_mask, small_mask, small_mask]
        motion = compute_scene_motion(masks, selection_frame=2, selection_frame_in_list=2)

        # Reference should be from frame 2 (the 60x60 mask)
        assert motion.reference_bbox is not None
        assert abs(motion.reference_bbox.width - 60) <= 2


class TestSmoothMotion:
    def test_smoothing_reduces_noise(self) -> None:
        """Smoothed motion should have less variance."""
        import random
        random.seed(42)

        frames = []
        for i in range(20):
            noise_x = random.gauss(0, 5)
            noise_y = random.gauss(0, 5)
            frames.append(FrameMotion(
                frame_index=i,
                centroid_x=100 + noise_x,
                centroid_y=100 + noise_y,
                bbox=BoundingBox(x=0, y=0, width=50, height=50),
                scale_x=1.0,
                scale_y=1.0,
                rotation_deg=0.0,
                opacity=1.0,
                visibility=True,
                area=2500,
            ))

        smoothed = smooth_motion(frames)

        # Raw variance should be higher than smoothed
        raw_var_x = sum((f.centroid_x - 100) ** 2 for f in frames) / len(frames)
        smooth_var_x = sum((f.centroid_x - 100) ** 2 for f in smoothed) / len(smoothed)
        assert smooth_var_x <= raw_var_x

    def test_preserves_length(self) -> None:
        """Smoothing should not change the number of frames."""
        frames = [
            FrameMotion(
                frame_index=i,
                centroid_x=float(i * 10),
                centroid_y=50.0,
                bbox=BoundingBox(x=0, y=0, width=50, height=50),
                visibility=True,
            )
            for i in range(10)
        ]
        smoothed = smooth_motion(frames)
        assert len(smoothed) == len(frames)

    def test_short_list_passthrough(self) -> None:
        """Very short lists should pass through unchanged."""
        frames = [
            FrameMotion(
                frame_index=0,
                centroid_x=50.0,
                centroid_y=50.0,
                bbox=BoundingBox(x=0, y=0, width=50, height=50),
                visibility=True,
            )
        ]
        smoothed = smooth_motion(frames)
        assert len(smoothed) == 1
        assert smoothed[0].centroid_x == 50.0
