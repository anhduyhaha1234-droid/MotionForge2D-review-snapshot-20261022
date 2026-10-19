"""Pytest configuration and fixtures."""

from __future__ import annotations

import contextlib
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure FFmpeg is findable on Windows (WinGet installs to non-PATH location)
_ffmpeg = shutil.which("ffmpeg")
if _ffmpeg is None:
    _winget_links = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links"
    if _winget_links.is_dir():
        os.environ["PATH"] = str(_winget_links) + os.pathsep + os.environ.get("PATH", "")


@pytest.fixture
def sample_project_data() -> dict:
    """Minimal valid project data for testing."""
    return {
        "version": "1.0.0",
        "name": "Test Project",
        "source_video": "/tmp/test.mp4",
        "video_metadata": {
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "duration_seconds": 10.0,
            "total_frames": 300,
            "codec": "h264",
            "has_audio": True,
            "audio_codec": "aac",
            "file_size_bytes": 5000000,
            "file_path": "/tmp/test.mp4",
        },
        "scenes": [
            {
                "scene_id": 0,
                "start_frame": 0,
                "end_frame": 149,
                "start_time_sec": 0.0,
                "end_time_sec": 5.0,
                "duration_sec": 5.0,
                "frame_count": 150,
            },
            {
                "scene_id": 1,
                "start_frame": 150,
                "end_frame": 299,
                "start_time_sec": 5.0,
                "end_time_sec": 10.0,
                "duration_sec": 5.0,
                "frame_count": 150,
            },
        ],
        "objects": [],
    }


@pytest.fixture
def sample_frame() -> np.ndarray[Any, Any]:
    """A simple 100x100 BGR test frame with a colored rectangle."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:, :] = (30, 30, 30)  # Dark gray background
    cv2.rectangle(frame, (20, 20), (80, 80), (0, 0, 255), -1)  # Red square
    return frame


@pytest.fixture
def sample_mask() -> np.ndarray[Any, Any]:
    """A 100x100 binary mask matching the red square in sample_frame."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 255
    return mask


@pytest.fixture()
def _patch_project_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect project root + durable DB to temp dirs so tests never write
    to the real projects/ tree or the production database.

    Returns the test project root (contains projects/ subdir).
    """
    test_root = tmp_path / "motionforge_test"
    test_root.mkdir(exist_ok=True)
    monkeypatch.setenv("MOTIONFORGE_PROJECT_ROOT", str(test_root))

    from app.api import deps
    from app.config import AppConfig
    from app.persistence import create_engine_for_path, create_session_factory
    from app.workflow.job_service import JobService

    test_config = AppConfig(
        project_root=test_root,
        models_dir=test_root / "models",
        output_dir=test_root / "output",
    )
    monkeypatch.setattr(deps, "_config", test_config)
    monkeypatch.setattr(
        deps,
        "_project_wf",
        __import__(
            "app.workflow.project_workflow",
            fromlist=["ProjectWorkflowService"],
        ).ProjectWorkflowService(test_config),
    )

    # Durable job service bound to a temp database + temp managed root.
    db_path = test_root / "data" / "test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    from alembic import command
    from alembic.config import Config

    project_root_dir = Path(__file__).resolve().parent.parent
    cfg = Config(str(project_root_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(project_root_dir / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    command.upgrade(cfg, "head")

    factory = create_session_factory(create_engine_for_path(db_path))
    svc = JobService(
        factory,
        worker=None,
        managed_root=test_root / "artifacts",
    )
    monkeypatch.setattr(deps, "_job_service", svc)
    # Reset the lazy channel-service singleton so it rebinds to the new
    # durable DB path for this test (the singleton caches its session
    # factory across tests otherwise).
    monkeypatch.setattr(deps, "_channel_service", None, raising=False)
    # Reset the lazy durable project-service singleton the same way.
    monkeypatch.setattr(deps, "_project_service", None, raising=False)
    # Reset the lazy durable video-item-service singleton the same way.
    monkeypatch.setattr(deps, "_video_service", None, raising=False)
    # Ensure the durable database the app lifespan may target is the test DB
    # (TestClient triggers the lifespan; without this the lifespan would
    # create/upgrade a real ``motionforge.db`` under the patched root).
    monkeypatch.setattr(deps, "_lifecycle_db", db_path, raising=False)
    return test_root


@pytest.fixture()
def registered_test_job_type() -> str:
    """A stable job type whose handler tests register on the injected worker.

    After the closure-shim removal (PM CR4), tests must register an explicit
    stable test job type/handler on the injected worker and submit a
    versioned manifest — no unreconstructable callable is accepted.
    """
    return "TEST_SYNTH"


@pytest.fixture()
def client(_patch_project_root: Path):
    """FastAPI test client with isolated project root + durable DB."""
    from fastapi.testclient import TestClient

    from app.api.app import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _stop_test_workers():
    """Stop any durable worker thread started by a test at teardown."""
    yield
    from app.api import deps

    svc = deps._job_service
    with contextlib.suppress(Exception):
        svc.stop_worker(timeout=2.0)
