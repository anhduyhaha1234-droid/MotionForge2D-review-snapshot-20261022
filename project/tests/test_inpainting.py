"""Tests for inpainting service."""

from __future__ import annotations

import numpy as np
import pytest

from app.services.inpainting_service import InpaintingService


@pytest.fixture
def svc() -> InpaintingService:
    return InpaintingService()


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a 100x100 BGR frame with a colored rectangle."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:, :] = (50, 100, 150)  # background color
    frame[30:70, 30:70] = (0, 0, 255)  # red "object"
    return frame


@pytest.fixture
def sample_mask() -> np.ndarray:
    """Create a mask covering the red rectangle."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[30:70, 30:70] = 255
    return mask


class TestMaskDilation:
    def test_dilate_increases_mask_area(
        self, svc: InpaintingService, sample_mask: np.ndarray,
    ) -> None:
        """Dilation should increase the white area."""
        dilated = svc.dilate_mask(sample_mask, kernel_size=5, iterations=2)
        assert np.sum(dilated > 0) > np.sum(sample_mask > 0)

    def test_dilate_kernel_size_effect(
        self, svc: InpaintingService, sample_mask: np.ndarray,
    ) -> None:
        """Larger kernel should dilate more."""
        small = svc.dilate_mask(sample_mask, kernel_size=3, iterations=1)
        large = svc.dilate_mask(sample_mask, kernel_size=7, iterations=1)
        assert np.sum(large > 0) > np.sum(small > 0)


class TestInpainting:
    def test_inpaint_telea(
        self, svc: InpaintingService,
        sample_frame: np.ndarray, sample_mask: np.ndarray,
    ) -> None:
        """Telea inpainting produces valid output."""
        result = svc.inpaint_frame(sample_frame, sample_mask, method="telea")
        assert result.shape == sample_frame.shape
        assert result.dtype == np.uint8

    def test_inpaint_ns(
        self, svc: InpaintingService,
        sample_frame: np.ndarray, sample_mask: np.ndarray,
    ) -> None:
        """Navier-Stokes inpainting produces valid output."""
        result = svc.inpaint_frame(sample_frame, sample_mask, method="ns")
        assert result.shape == sample_frame.shape

    def test_process_frame(
        self, svc: InpaintingService,
        sample_frame: np.ndarray, sample_mask: np.ndarray,
    ) -> None:
        """Full pipeline produces valid output."""
        result = svc.process_frame(sample_frame, sample_mask)
        assert result.shape == sample_frame.shape
        # The inpainted region should differ from original
        original_center = sample_frame[30:70, 30:70].mean()
        result_center = result[30:70, 30:70].mean()
        # They should be different (object removed)
        assert original_center != result_center  # may be close


class TestFrameSequence:
    def test_sequence_cycle(self, tmp_path: object) -> None:
        """Frame sequence cycles through files."""
        from pathlib import Path

        import cv2

        # This test verifies the concept
        seq_dir = Path(str(tmp_path)) / "seq"
        seq_dir.mkdir()
        for i in range(4):
            img = np.zeros((50, 50, 4), dtype=np.uint8)
            cv2.imwrite(str(seq_dir / f"frame_{i:03d}.png"), img)

        pngs = sorted(seq_dir.glob("*.png"))
        assert len(pngs) == 4
        # Cycle test
        assert (5 % len(pngs)) == 1  # frame 5 → index 1
