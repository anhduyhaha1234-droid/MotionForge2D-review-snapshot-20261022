"""Tests for the FastAPI API endpoints."""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.schemas import (
    BoundingBox,
    FrameMotion,
    JobState,
    ObjectKind,
    SceneInfo,
    SceneMotion,
    SelectionInput,
    SelectionMode,
    TrackedObject,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _patch_project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override project root so all tests use a temp directory."""
    test_root = tmp_path / "motionforge_test"
    test_root.mkdir()

    from app.api import deps
    from app.config import AppConfig

    test_config = AppConfig(
        project_root=test_root,
        models_dir=test_root / "models",
        output_dir=test_root / "output",
    )
    monkeypatch.setattr(deps, "_config", test_config)
    monkeypatch.setattr(
        deps, "_project_wf",
        __import__(
            "app.workflow.project_workflow", fromlist=["ProjectWorkflowService"],
        ).ProjectWorkflowService(test_config),
    )
    # Durable job service bound to a temp database (same bootstrap as the
    # shared conftest fixture) so the local fixtures never touch the real
    # production database.
    from alembic import command
    from alembic.config import Config

    from app.persistence import create_engine_for_path, create_session_factory
    from app.workflow.job_service import JobService

    db_path = test_root / "data" / "test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    project_root_dir = Path(__file__).resolve().parent.parent
    cfg = Config(str(project_root_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(project_root_dir / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    command.upgrade(cfg, "head")
    factory = create_session_factory(create_engine_for_path(db_path))
    monkeypatch.setattr(
        deps, "_job_service",
        JobService(factory, managed_root=test_root / "artifacts"),
    )
    monkeypatch.setattr(deps, "_lifecycle_db", db_path, raising=False)
    monkeypatch.setattr(
        deps, "_replacement_service",
        __import__(
            "app.workflow.replacement_service", fromlist=["ReplacementService"],
        ).ReplacementService(deps._project_wf),
    )
    monkeypatch.setattr(
        deps, "_seg_service",
        __import__(
            "app.workflow.segmentation_service", fromlist=["SegmentationService"],
        ).SegmentationService(test_config),
    )

    return test_root


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from app.api.app import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def project_id(client: TestClient) -> str:
    """Create a test project and return its ID."""
    resp = client.post("/api/projects", json={"name": "Test Project"})
    assert resp.status_code == 201
    return resp.json()["project_id"]


def _create_fake_frames(
    project_dir: Path, scene_id: int = 0, count: int = 5,
) -> None:
    """Create fake frame images in the project directory."""
    frames_dir = project_dir / "frames" / f"scene_{scene_id}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(
            frame, (10 + i * 2, 10), (50 + i * 2, 50), (0, 0, 255), -1,
        )
        cv2.imwrite(str(frames_dir / f"frame_{i:06d}.png"), frame)


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestCreateProject:
    def test_create_project(self, client: TestClient) -> None:
        resp = client.post("/api/projects", json={"name": "My Project"})
        assert resp.status_code == 201
        data = resp.json()
        assert "project_id" in data
        assert data["project"]["name"] == "My Project"

    def test_create_project_dir(
        self, client: TestClient, _patch_project_root: Path,
    ) -> None:
        resp = client.post("/api/projects", json={"name": "Dir Test"})
        pid = resp.json()["project_id"]
        proj_file = _patch_project_root / "projects" / pid / "project.json"
        assert proj_file.exists()


class TestUploadVideo:
    def test_upload_video(
        self, client: TestClient, project_id: str, tmp_path: Path,
    ) -> None:
        fake_video = tmp_path / "test.mp4"
        fake_video.write_bytes(b"\x00" * 100)

        with open(fake_video, "rb") as f:
            resp = client.post(
                f"/api/projects/{project_id}/video",
                files={"file": ("test.mp4", f, "video/mp4")},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_upload_video_missing_project(
        self, client: TestClient, tmp_path: Path,
    ) -> None:
        fake_video = tmp_path / "test.mp4"
        fake_video.write_bytes(b"\x00" * 100)

        with open(fake_video, "rb") as f:
            resp = client.post(
                "/api/projects/nonexistent/video",
                files={"file": ("test.mp4", f, "video/mp4")},
            )
        assert resp.status_code == 404


class TestIngest:
    def test_ingest_returns_job(self, client: TestClient, project_id: str) -> None:
        resp = client.post(f"/api/projects/{project_id}/ingest")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] in ("queued", "running", "completed", "failed")

    def test_ingest_missing_project(self, client: TestClient) -> None:
        resp = client.post("/api/projects/nonexistent/ingest")
        assert resp.status_code == 404


class TestGetProject:
    def test_get_project(self, client: TestClient, project_id: str) -> None:
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"

    def test_get_project_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/projects/nonexistent")
        assert resp.status_code == 404


class TestGetScenes:
    def test_get_scenes(
        self, client: TestClient, project_id: str,
        _patch_project_root: Path,
    ) -> None:
        from app.api import deps

        pwf = deps._project_wf
        svc = pwf.get_project_service(project_id)
        svc.load()
        svc.set_scenes([
            SceneInfo(
                scene_id=0, start_frame=0, end_frame=29,
                start_time_sec=0.0, end_time_sec=1.0,
                duration_sec=1.0, frame_count=30,
            ),
        ])

        resp = client.get(f"/api/projects/{project_id}/scenes")
        assert resp.status_code == 200
        scenes = resp.json()
        assert len(scenes) == 1
        assert scenes[0]["scene_id"] == 0

    def test_get_scenes_empty(self, client: TestClient, project_id: str) -> None:
        resp = client.get(f"/api/projects/{project_id}/scenes")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetFrame:
    def test_get_frame(
        self, client: TestClient, _patch_project_root: Path,
    ) -> None:
        from app.api import deps

        pwf = deps._project_wf
        pid, _ = pwf.create_project("Frame Test")
        proj_dir = pwf._project_dir(pid)
        _create_fake_frames(proj_dir, scene_id=0, count=3)

        resp = client.get(f"/api/projects/{pid}/frames/0?scene_id=0")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_get_frame_not_found(self, client: TestClient, project_id: str) -> None:
        resp = client.get(f"/api/projects/{project_id}/frames/999")
        assert resp.status_code == 404


class TestPreviewMask:
    def test_preview_mask(
        self, client: TestClient, _patch_project_root: Path,
    ) -> None:
        from app.api import deps

        pwf = deps._project_wf
        pid, _ = pwf.create_project("Mask Test")
        proj_dir = pwf._project_dir(pid)
        _create_fake_frames(proj_dir, scene_id=0, count=3)

        resp = client.post(
            f"/api/projects/{pid}/objects/preview-mask",
            json={
                "frame_index": 0,
                "selection": {
                    "mode": "point",
                    "frame_index": 0,
                    "x": 30.0,
                    "y": 30.0,
                },
                "backend": "contour",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "mask_path" in data
        assert "nonzero_pixels" in data


class TestCreateObject:
    def test_create_object(self, client: TestClient, project_id: str) -> None:
        resp = client.post(
            f"/api/projects/{project_id}/objects",
            json={
                "name": "Character A",
                "kind": "character",
                "selection": {
                    "mode": "point",
                    "frame_index": 5,
                    "x": 100.0,
                    "y": 200.0,
                },
                "scene_id": 0,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "object_id" in data

    def test_create_object_with_mask(
        self, client: TestClient, _patch_project_root: Path,
    ) -> None:
        from app.api import deps

        pwf = deps._project_wf
        pid, _ = pwf.create_project("Obj Mask Test")

        mask_data = [[0] * 10 for _ in range(10)]
        mask_data[3][3] = 255

        resp = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "Masked Object",
                "selection": {
                    "mode": "point",
                    "frame_index": 0,
                    "x": 5.0,
                    "y": 5.0,
                },
                "scene_id": 0,
                "mask_data": mask_data,
            },
        )
        assert resp.status_code == 201


class TestGetObject:
    def test_get_object(
        self, client: TestClient, project_id: str,
        _patch_project_root: Path,
    ) -> None:
        from app.api import deps

        pwf = deps._project_wf

        obj = TrackedObject(
            object_id="test_obj",
            name="Test Object",
            kind=ObjectKind.CHARACTER,
            selection=SelectionInput(
                mode=SelectionMode.POINT, frame_index=0, x=50.0, y=50.0,
            ),
            scene_id=0,
            motion=SceneMotion(
                scene_id=0,
                frames=[
                    FrameMotion(
                        frame_index=0, centroid_x=50.0, centroid_y=50.0,
                        bbox=BoundingBox(x=20, y=20, width=60, height=60),
                    ),
                ],
                reference_bbox=BoundingBox(x=20, y=20, width=60, height=60),
            ),
        )
        pwf.add_tracked_object(project_id, obj)

        resp = client.get(f"/api/projects/{project_id}/objects/test_obj")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object_id"] == "test_obj"
        assert data["motion"] is not None

    def test_get_object_not_found(
        self, client: TestClient, project_id: str,
    ) -> None:
        resp = client.get(f"/api/projects/{project_id}/objects/nonexistent")
        assert resp.status_code == 404


class TestUpdateReplacement:
    def test_update_replacement_settings(
        self, client: TestClient, project_id: str,
        _patch_project_root: Path,
    ) -> None:
        from app.api import deps

        pwf = deps._project_wf

        obj = TrackedObject(
            object_id="rep_obj",
            name="Rep Object",
            kind=ObjectKind.CHARACTER,
            selection=SelectionInput(
                mode=SelectionMode.POINT, frame_index=0, x=50.0, y=50.0,
            ),
            scene_id=0,
        )
        pwf.add_tracked_object(project_id, obj)

        resp = client.patch(
            f"/api/projects/{project_id}/objects/rep_obj"
            "/replacement-settings",
            json={
                "replacement_config": {
                    "mode": "static_asset",
                    "assetPath": "objects/rep_obj/replacement.png",
                    "anchor": {"x": 0.5, "y": 0.5},
                    "offset": {"x": 0.0, "y": 0.0},
                    "scale": 1.2,
                    "rotationOffsetDeg": 15.0,
                    "opacity": 0.9,
                    "fitMode": "contain",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["replacement_config"]["scale"] == 1.2
        assert data["replacement_config"]["rotation_offset_deg"] == 15.0

    def test_update_replacement_not_found(
        self, client: TestClient, project_id: str,
    ) -> None:
        resp = client.patch(
            f"/api/projects/{project_id}/objects/nonexistent"
            "/replacement-settings",
            json={"replacement_config": {"scale": 1.0}},
        )
        assert resp.status_code == 404


class TestJobStatus:
    def test_job_status(self, client: TestClient) -> None:
        from app.api import deps
        from app.workflow.durable_worker import WorkerContext

        job_svc = deps._job_service

        def dummy_handler(ctx: WorkerContext) -> dict:
            ctx.progress(50, "Halfway")
            return {"ok": True}

        # Explicit stable test job type registered on the injected worker
        # (PM CR4: no closure shim — registered handler + versioned manifest).
        job_svc.worker.register_handler("TEST_SYNTH", dummy_handler)
        info = job_svc.create_job(
            "TEST_SYNTH",
            input_manifest={"schema_version": 1, "payload": "status"},
        )

        resp = client.get(f"/api/jobs/{info.job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == info.job_id
        assert data["status"] in ("queued", "running", "completed")

    def test_job_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/jobs/nonexistent")
        assert resp.status_code == 404


class TestJobCancel:
    def test_job_cancel(self, client: TestClient) -> None:
        from app.api import deps
        from app.workflow.durable_worker import WorkerContext

        job_svc = deps._job_service

        def slow_handler(ctx: WorkerContext) -> dict:
            for i in range(100):
                if ctx.is_cancelled():
                    return {"cancelled": True}
                ctx.progress(float(i), f"Step {i}")
                time.sleep(0.01)
            return {"done": True}

        job_svc.worker.register_handler("TEST_SLOW", slow_handler)
        info = job_svc.create_job(
            "TEST_SLOW",
            input_manifest={"schema_version": 1, "payload": "cancel"},
        )
        job_svc.start_worker()
        try:
            resp = client.post(f"/api/jobs/{info.job_id}/cancel")
            assert resp.status_code == 200
            assert resp.json()["status"] == "cancel_requested"

            for _ in range(200):
                final = job_svc.get_job(info.job_id)
                if final.state in (
                    JobState.CANCELLED, JobState.CANCELLING, JobState.COMPLETED,
                ):
                    break
                time.sleep(0.05)
            assert final is not None
            assert final.state in (
                JobState.CANCELLED, JobState.CANCELLING, JobState.COMPLETED,
            )
        finally:
            job_svc.stop_worker(timeout=5.0)

    def test_cancel_already_completed(self, client: TestClient) -> None:
        from app.api import deps
        from app.workflow.durable_worker import WorkerContext

        job_svc = deps._job_service

        def quick_handler(ctx: WorkerContext) -> dict:
            return {"done": True}

        job_svc.worker.register_handler("TEST_QUICK", quick_handler)
        info = job_svc.create_job(
            "TEST_QUICK",
            input_manifest={"schema_version": 1, "payload": "quick"},
        )
        # The durable worker must actually run before we can expect the job
        # to be terminal.  Start the worker (explicit lifecycle), wait for
        # completion, then stop it.
        job_svc.start_worker()
        try:
            for _ in range(100):
                if job_svc.get_job(info.job_id).state == JobState.COMPLETED:
                    break
                time.sleep(0.05)
        finally:
            job_svc.stop_worker(timeout=5.0)

        resp = client.post(f"/api/jobs/{info.job_id}/cancel")
        assert resp.status_code == 400

    def test_cancel_nonexistent(self, client: TestClient) -> None:
        resp = client.post("/api/jobs/nonexistent/cancel")
        assert resp.status_code == 404


class TestHealthCheck:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
