"""Tests for list all projects endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


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
        deps,
        "_project_wf",
        __import__(
            "app.workflow.project_workflow",
            fromlist=["ProjectWorkflowService"],
        ).ProjectWorkflowService(test_config),
    )
    monkeypatch.setattr(
        deps,
        "_job_service",
        __import__(
            "app.workflow.job_service", fromlist=["JobService"],
        ).JobService(),
    )
    monkeypatch.setattr(
        deps,
        "_replacement_service",
        __import__(
            "app.workflow.replacement_service",
            fromlist=["ReplacementService"],
        ).ReplacementService(deps._project_wf),
    )
    monkeypatch.setattr(
        deps,
        "_seg_service",
        __import__(
            "app.workflow.segmentation_service",
            fromlist=["SegmentationService"],
        ).SegmentationService(test_config),
    )

    return test_root


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from app.api.app import app

    return TestClient(app, raise_server_exceptions=False)


def test_list_projects_empty(client: TestClient) -> None:
    """GET /api/projects returns empty list when no projects exist."""
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_projects_after_create(client: TestClient) -> None:
    """GET /api/projects returns created project."""
    # Create a project
    create_resp = client.post("/api/projects", json={"name": "Test Project"})
    assert create_resp.status_code == 201
    project_id = create_resp.json()["project_id"]

    # List projects
    list_resp = client.get("/api/projects")
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert len(projects) >= 1
    assert any(p["project_id"] == project_id for p in projects)


def test_list_projects_has_timestamps(client: TestClient) -> None:
    """GET /api/projects returns projects with created_at and updated_at."""
    create_resp = client.post("/api/projects", json={"name": "TS Project"})
    assert create_resp.status_code == 201
    project_id = create_resp.json()["project_id"]

    list_resp = client.get("/api/projects")
    projects = list_resp.json()
    match = next(p for p in projects if p["project_id"] == project_id)
    assert match["created_at"] != ""
    assert match["updated_at"] != ""
    assert match["name"] == "TS Project"
