"""Shared test helpers for the S03 durable API suites.

Every helper goes through the conftest ``client`` fixture, so all reads
and writes land in the isolated tmp durable database — never the
production database, ``channels.json``, the legacy projects directory or
user data.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


def _root_channels_bytes() -> bytes:
    """The production-root channels.json bytes (must never change)."""
    root = Path(__file__).resolve().parent.parent / "channels.json"
    return root.read_bytes() if root.exists() else b""


def create_project(
    client: TestClient, name: str = "Summary Project", **extra: object
) -> dict[str, Any]:
    """Create a durable Project through the S03-T02 API (same isolated DB)."""
    payload: dict[str, object] = {"name": name, **extra}
    resp = client.post("/api/v2/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


def create_video(
    client: TestClient, project_id: str, title: str = "Video", **extra: object
) -> dict[str, Any]:
    """Append a durable Video Item through the S03-T03 API."""
    payload: dict[str, object] = {"title": title, **extra}
    resp = client.post(f"/api/v2/projects/{project_id}/videos", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


def make_channel(client: TestClient, name: str, role: str = "source") -> dict[str, Any]:
    """Create a durable Channel through the S03-T01 API (same isolated DB)."""
    resp = client.post("/api/channels", json={"name": name, "role": role})
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


def patch_video(
    client: TestClient,
    project_id: str,
    video_id: str,
    *,
    revision: int,
    status: str,
) -> dict[str, Any]:
    """Move a Video Item to a pipeline status (CAS on revision)."""
    resp = client.patch(
        f"/api/v2/projects/{project_id}/videos/{video_id}",
        json={"status": status, "revision": revision},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def archive_project(client: TestClient, project_id: str, revision: int) -> dict[str, Any]:
    """Archive a durable Project (idempotent CAS)."""
    resp = client.post(
        f"/api/v2/projects/{project_id}/archive", json={"revision": revision}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def archive_video(
    client: TestClient, project_id: str, video_id: str, revision: int
) -> dict[str, Any]:
    """Archive a durable Video Item (idempotent CAS)."""
    resp = client.post(
        f"/api/v2/projects/{project_id}/videos/{video_id}/archive",
        json={"revision": revision},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def summary(
    client: TestClient, project_id: str, workspace_id: str = "default"
) -> dict[str, Any]:
    """GET one Project summary."""
    resp = client.get(
        f"/api/v2/projects/{project_id}/summary",
        params={"workspace_id": workspace_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def summaries(
    client: TestClient,
    workspace_id: str = "default",
    **params: Any,
) -> dict[str, Any]:
    """GET the Project summary collection."""
    resp = client.get(
        "/api/v2/projects/summaries",
        params={"workspace_id": workspace_id, **params},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def new_uuid() -> str:
    """A fresh UUIDv4 string (never collides with real rows)."""
    return str(uuid.uuid4())


def job_record(
    workspace_id: str,
    job_type: str,
    owner_type: str,
    owner_id: str,
    state: str = "queued",
    progress: float = 0.0,
) -> dict[str, Any]:
    """Build a durable Job row payload (schema-shaped, SQLAlchemy-ready)."""
    return {
        "id": new_uuid(),
        "workspace_id": workspace_id,
        "job_type": job_type,
        "owner_type": owner_type,
        "owner_id": owner_id,
        "state": state,
        "resource_class": "cpu_light",
        "priority": 50,
        "max_attempts": 3,
        "progress": progress,
        "idempotency_key": None,
        "input_generation": None,
        "parent_job_id": None,
        "predecessor_job_id": None,
        "input_manifest_json": '{"schema_version": 1}',
        "created_at": None,
        "updated_at": None,
        "started_at": None,
        "finished_at": None,
        "archived_at": None,
        "revision": 1,
    }
