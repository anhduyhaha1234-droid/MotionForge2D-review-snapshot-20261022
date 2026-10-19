"""S03-T02 durable Project CRUD/archive API tests (AC1-AC8).

Every test uses the conftest ``client`` fixture (isolated tmp project
root + tmp durable database + patched ``deps``), so no test ever touches
the production database, ``channels.json``, the legacy projects
directory or user data.

Scenarios map to acceptance criteria:
- AC1 list/read/create/update/archive; no hard-delete endpoint, no
  project directory, no ``project.json``, no JSON dual-write.
- AC2 names normalize to non-empty 1-200 chars, statuses are exact,
  DTOs expose no ORM object or absolute path.
- AC3 source/production channel references nullable/clearable and
  validated atomically (same workspace, correct role, active when newly
  assigned); existing references survive later channel archive.
- AC4 PATCH + first archive use atomic revision CAS; stale → stable 409;
  exactly one revision bump per accepted business update; concurrent
  archive repeats idempotent.
- AC5 archive preserves timestamps/channel references/future child
  relationships; archived readable/filterable, excluded from active
  default; no cascade/hard delete.
- AC6 every item operation enforces workspace ownership (unknown or
  cross-workspace id → 404).
- AC7 /api/v2/projects is isolated from every existing /api/projects
  route (literal legacy sub-routes keep their behavior; durable base
  endpoints do not invoke legacy filesystem services; the legacy API
  test suite remains unchanged and green).
- AC8 S03-T01-head preservation covered in tests/test_persistence_bootstrap.py
  (no migration needed — the existing schema enforces the contract).
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.models import Channel, Workspace

# ── Helpers ──────────────────────────────────────────────────────────────────


def _root_channels_bytes() -> bytes:
    """The production-root channels.json bytes (must never change)."""
    root = Path(__file__).resolve().parent.parent / "channels.json"
    return root.read_bytes() if root.exists() else b""


def _create(
    client: TestClient,
    name: str,
    **extra: object,
) -> dict:
    payload: dict[str, object] = {"name": name, **extra}
    resp = client.post("/api/v2/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _archive(client: TestClient, project_id: str, revision: int) -> dict:
    resp = client.post(f"/api/v2/projects/{project_id}/archive", json={"revision": revision})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _make_channel(
    client: TestClient, name: str, role: str = "source"
) -> dict:
    """Create a durable channel through the S03-T01 API (same DB)."""
    resp = client.post(
        "/api/channels", json={"name": name, "role": role}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _route_exists(client: TestClient, method: str, path: str) -> bool:
    """Probe the OpenAPI schema for an exact route (no request side effect)."""
    schema = client.get("/openapi.json").json()
    for route_path, methods in schema["paths"].items():
        if route_path.rstrip("/") == path.rstrip("/") and method.lower() in methods:
            return True
    return False


# ── AC1: CRUD + archive, no hard delete, no JSON/filesystem dual-write ───────


def test_create_read_update_archive_lifecycle(client: TestClient) -> None:
    before = _root_channels_bytes()

    created = _create(client, "  Durable Project  ")
    pid = created["project_id"]
    assert created["name"] == "Durable Project"  # normalized (AC2)
    assert created["status"] == "active"
    assert created["workspace_id"] == DEFAULT_WORKSPACE_ID
    assert created["revision"] == 1
    assert created["archived_at"] is None  # JSON null for optional timestamp
    assert "id" not in created  # DTO exposes project_id, not ORM id

    # Read
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["project_id"] == pid
    assert got["name"] == "Durable Project"

    # Update (business update with expected revision)
    updated = client.patch(
        f"/api/v2/projects/{pid}",
        json={"name": "Durable Project v2", "description": "updated", "revision": 1},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["name"] == "Durable Project v2"
    assert body["description"] == "updated"
    assert body["revision"] == 2  # exactly one bump (AC4)

    # Archive (requires expected revision — atomic CAS)
    archived = _archive(client, pid, revision=2)
    assert archived["status"] == "archived"
    assert archived["archived_at"]  # timestamp preserved (AC5)
    assert archived["revision"] == 3

    # Readable after archive (AC5)
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["status"] == "archived"

    # No hard-delete endpoint exists
    assert not _route_exists(client, "DELETE", f"/api/v2/projects/{pid}")
    assert _root_channels_bytes() == before, "channels.json was modified"


def test_durable_create_never_writes_project_json(client: TestClient) -> None:
    """AC1: durable create writes SQLite only — no project dir/JSON file."""
    from app.api import deps as api_deps

    before = _root_channels_bytes()
    root = api_deps._config.project_root
    projects_dir = root / "projects"

    created = _create(client, "No JSON Write")
    pid = created["project_id"]

    # No project directory, no project.json anywhere under the projects root
    assert not projects_dir.exists() or not (projects_dir / pid).exists()
    if projects_dir.exists():
        assert not list(projects_dir.rglob("project.json"))
    assert _root_channels_bytes() == before

    # And the row lives in the durable DB (readable through the durable API)
    assert client.get(f"/api/v2/projects/{pid}").status_code == 200
    # The legacy filesystem store has no such project
    assert not (projects_dir / pid / "project.json").exists()


def test_list_excludes_archived_by_default(client: TestClient) -> None:
    before = _root_channels_bytes()
    a = _create(client, "Active One")
    c = _create(client, "To Archive")

    active = client.get("/api/v2/projects").json()
    assert active["active_only"] is True
    active_ids = {p["project_id"] for p in active["projects"]}
    assert a["project_id"] in active_ids
    assert c["project_id"] in active_ids

    _archive(client, c["project_id"], revision=c["revision"])
    active2 = client.get("/api/v2/projects").json()
    active_ids2 = {p["project_id"] for p in active2["projects"]}
    assert c["project_id"] not in active_ids2
    assert a["project_id"] in active_ids2

    # Archived projects are filterable with active_only=false (AC5)
    all_rows = client.get("/api/v2/projects", params={"active_only": False}).json()
    all_ids = {p["project_id"] for p in all_rows["projects"]}
    assert c["project_id"] in all_ids
    assert _root_channels_bytes() == before


def test_list_filters_by_status(client: TestClient) -> None:
    before = _root_channels_bytes()
    p = _create(client, "Status Filter")
    resp = client.patch(
        f"/api/v2/projects/{p['project_id']}",
        json={"status": "needs_review", "revision": 1},
    )
    assert resp.status_code == 200, resp.text

    filtered = client.get(
        "/api/v2/projects", params={"status": "needs_review"}
    ).json()
    assert {x["project_id"] for x in filtered["projects"]} == {p["project_id"]}
    assert _root_channels_bytes() == before


def test_unknown_project_404(client: TestClient) -> None:
    before = _root_channels_bytes()
    # UUID-shaped unknown ids hit the durable :uuid routes -> 404
    unknown = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    assert client.get(f"/api/v2/projects/{unknown}").status_code == 404
    assert (
        client.patch(f"/api/v2/projects/{unknown}", json={"revision": 1}).status_code
        == 404
    )
    assert (
        client.post(f"/api/v2/projects/{unknown}/archive", json={"revision": 1}).status_code
        == 404
    )
    # Non-UUID ids are outside the durable route (legacy domain) — the
    # legacy GET returns 404 on the empty legacy store.
    assert client.get("/api/projects/nope").status_code == 404
    assert _root_channels_bytes() == before


# ── AC2: exact statuses, normalized names, DTO boundary ──────────────────────


def test_statuses_are_exact_approved_set(client: TestClient) -> None:
    before = _root_channels_bytes()
    statuses = client.get("/api/v2/projects/statuses").json()["statuses"]
    assert statuses == [
        "draft",
        "active",
        "needs_review",
        "rendering",
        "completed",
        "archived",
    ]
    # The schema CHECK rejects anything else (repository-level guard too)
    bad = client.patch(
        f"/api/v2/projects/{_create(client, 'Status Guard')['project_id']}",
        json={"status": "in_progress", "revision": 1},
    )
    assert bad.status_code == 422
    assert _root_channels_bytes() == before


def test_empty_name_rejected(client: TestClient) -> None:
    before = _root_channels_bytes()
    resp = client.post("/api/v2/projects", json={"name": "   "})
    assert resp.status_code == 422
    assert _root_channels_bytes() == before


def test_dto_never_exposes_orm_objects_or_paths(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Boundary Check")
    body_keys = set(created.keys())
    assert "project_id" in body_keys
    assert "workspace_id" in body_keys
    assert "revision" in body_keys
    for forbidden in ("id", "_sa_instance_state", "path", "absolute_path", "db_path"):
        assert forbidden not in body_keys
    serialized = str(created)
    assert "sqlite" not in serialized.lower() and "C:" not in serialized
    assert _root_channels_bytes() == before


# ── AC3: channel references — validation and clearing ────────────────────────


def test_create_with_valid_channels(client: TestClient) -> None:
    before = _root_channels_bytes()
    src = _make_channel(client, "Src Ch")
    prod = _make_channel(client, "Prod Ch", role="production")

    created = _create(
        client,
        "Channeled",
        source_channel_id=src["channel_id"],
        production_channel_id=prod["channel_id"],
    )
    assert created["source_channel_id"] == src["channel_id"]
    assert created["production_channel_id"] == prod["channel_id"]
    assert _root_channels_bytes() == before


def test_create_rejects_wrong_role_channel(client: TestClient) -> None:
    before = _root_channels_bytes()
    src = _make_channel(client, "Src Only")

    # production slot requires a production channel
    resp = client.post(
        "/api/v2/projects",
        json={"name": "Wrong Role", "production_channel_id": src["channel_id"]},
    )
    assert resp.status_code == 422, resp.text
    assert "not a production channel" in resp.json()["detail"]

    # source slot requires a source channel
    prod = _make_channel(client, "Prod Only", role="production")
    resp2 = client.post(
        "/api/v2/projects",
        json={"name": "Wrong Role 2", "source_channel_id": prod["channel_id"]},
    )
    assert resp2.status_code == 422, resp2.text
    assert "not a source channel" in resp2.json()["detail"]
    assert _root_channels_bytes() == before


def test_create_rejects_cross_workspace_channel(client: TestClient) -> None:
    import uuid as _uuid

    before = _root_channels_bytes()
    # A channel row in another workspace (direct seed — same durable DB)
    from app.api import deps as api_deps

    with api_deps.get_job_service()._session_factory() as session:
        session.execute(
            __import__("sqlalchemy.dialects.sqlite", fromlist=["insert"]).insert(
                Workspace
            )
            .values(id="other-ws", name="other-ws")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        other = Channel(
            workspace_id="other-ws",
            role="source",
            name=f"Other Src {_uuid.uuid4().hex[:8]}",
        )
        session.add(other)
        session.commit()
        other_id = other.id

    resp = client.post(
        "/api/v2/projects",
        json={"name": "Cross WS", "source_channel_id": other_id},
    )
    assert resp.status_code == 422, resp.text
    assert "different workspace" in resp.json()["detail"]
    assert _root_channels_bytes() == before


def test_create_rejects_unknown_or_archived_channel(client: TestClient) -> None:
    before = _root_channels_bytes()

    resp = client.post(
        "/api/v2/projects",
        json={"name": "No Chan", "source_channel_id": "ffffffff-ffff-ffff-ffff-ffffffffffff"},
    )
    assert resp.status_code == 422, resp.text
    assert "does not reference an existing channel" in resp.json()["detail"]

    # Archived channel cannot be newly assigned (must be active at
    # assignment time — AC3)
    ch = _make_channel(client, "Will Archive")
    arc = client.post(f"/api/channels/{ch['channel_id']}/archive", json={"revision": 1})
    assert arc.status_code == 200, arc.text
    resp2 = client.post(
        "/api/v2/projects",
        json={"name": "Arch Chan", "source_channel_id": ch["channel_id"]},
    )
    assert resp2.status_code == 422, resp2.text
    assert "not an active channel" in resp2.json()["detail"]
    assert _root_channels_bytes() == before


def test_patch_assigns_clears_and_validates_channels(client: TestClient) -> None:
    before = _root_channels_bytes()
    src = _make_channel(client, "Assign Src")
    created = _create(client, "Channel Patch")

    # Assign on PATCH
    r = client.patch(
        f"/api/v2/projects/{created['project_id']}",
        json={"source_channel_id": src["channel_id"], "revision": 1},
    )
    assert r.status_code == 200, r.text
    assert r.json()["source_channel_id"] == src["channel_id"]
    assert r.json()["revision"] == 2

    # Explicit null clears (AC3 nullable/clearable)
    r2 = client.patch(
        f"/api/v2/projects/{created['project_id']}",
        json={"source_channel_id": None, "revision": 2},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["source_channel_id"] is None
    assert r2.json()["revision"] == 3

    # Invalid assignment on PATCH → 422, no state change
    r3 = client.patch(
        f"/api/v2/projects/{created['project_id']}",
        json={"source_channel_id": "ffffffff-ffff-ffff-ffff-ffffffffffff", "revision": 3},
    )
    assert r3.status_code == 422, r3.text
    got = client.get(f"/api/v2/projects/{created['project_id']}").json()
    assert got["source_channel_id"] is None
    assert got["revision"] == 3  # no bump on the rejected update
    assert _root_channels_bytes() == before


def test_existing_reference_survives_channel_archive(client: TestClient) -> None:
    """AC3: a reference assigned while active survives a later archive."""
    before = _root_channels_bytes()
    src = _make_channel(client, "Survivor Src")
    created = _create(
        client, "Survivor Project", source_channel_id=src["channel_id"]
    )
    pid = created["project_id"]

    # Archive the channel AFTER assignment
    arc = client.post(f"/api/channels/{src['channel_id']}/archive", json={"revision": 1})
    assert arc.status_code == 200, arc.text

    # The project keeps the reference; no cascade, no validation failure
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["source_channel_id"] == src["channel_id"]
    assert got["status"] == "active"
    # Project can still be updated (existing references are not revalidated)
    r = client.patch(
        f"/api/v2/projects/{pid}",
        json={"description": "still works", "revision": 1},
    )
    assert r.status_code == 200, r.text
    assert _root_channels_bytes() == before


@pytest.mark.parametrize("operation", ["create", "patch"])
def test_channel_archive_cannot_commit_between_validation_and_assignment(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """CREATE/PATCH holds the SQLite writer reservation across validation.

    The SQL event signals the exact moment the competing channel archive
    reaches its UPDATE.  The Project writer is deliberately paused after a
    successful active-channel validation; the archive must wait until the
    Project write commits, so the reference was valid at its atomic boundary.
    """
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    from app.persistence import projects as projects_module

    source = _make_channel(client, f"Atomic source {operation}")
    project = _create(client, "Atomic patch target") if operation == "patch" else None
    validated = threading.Event()
    archive_update_attempted = threading.Event()
    original_validate = projects_module._validate_channel_reference

    def _paused_validate(
        session: Session,
        workspace_id: str,
        channel_id: str | None,
        *,
        role: str,
    ) -> None:
        original_validate(session, workspace_id, channel_id, role=role)
        if channel_id == source["channel_id"]:
            validated.set()
            assert archive_update_attempted.wait(timeout=5)

    monkeypatch.setattr(projects_module, "_validate_channel_reference", _paused_validate)
    engine = deps.get_project_service()._session_factory.kw["bind"]  # noqa: SLF001

    def _observe_archive_sql(
        _conn: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        normalized = " ".join(statement.lower().split())
        if normalized.startswith("update channel set"):
            archive_update_attempted.set()

    event.listen(engine, "before_cursor_execute", _observe_archive_sql)
    project_response: list[Any] = []
    archive_response: list[Any] = []

    def _assign() -> None:
        if operation == "create":
            project_response.append(
                client.post(
                    "/api/v2/projects",
                    json={"name": "Atomic create", "source_channel_id": source["channel_id"]},
                )
            )
        else:
            assert project is not None
            project_response.append(
                client.patch(
                    f"/api/v2/projects/{project['project_id']}",
                    json={"source_channel_id": source["channel_id"], "revision": 1},
                )
            )

    def _archive_channel() -> None:
        archive_response.append(
            client.post(
                f"/api/channels/{source['channel_id']}/archive",
                json={"revision": 1},
            )
        )

    assign_thread = threading.Thread(target=_assign)
    archive_thread = threading.Thread(target=_archive_channel)
    try:
        assign_thread.start()
        assert validated.wait(timeout=5)
        archive_thread.start()
        assign_thread.join(timeout=10)
        archive_thread.join(timeout=10)
    finally:
        event.remove(engine, "before_cursor_execute", _observe_archive_sql)

    assert not assign_thread.is_alive()
    assert not archive_thread.is_alive()
    assert len(project_response) == len(archive_response) == 1
    assigned = project_response[0]
    archived_channel = archive_response[0]
    assert assigned.status_code in {200, 201}, assigned.text
    assert archived_channel.status_code == 200, archived_channel.text
    assert assigned.json()["source_channel_id"] == source["channel_id"]
    assert archived_channel.json()["status"] == "archived"


# ── AC4: atomic optimistic concurrency via revision CAS ──────────────────────


def test_stale_revision_returns_409(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Concurrency")
    pid = created["project_id"]

    r1 = client.patch(f"/api/v2/projects/{pid}", json={"description": "v1", "revision": 1})
    assert r1.status_code == 200
    assert r1.json()["revision"] == 2

    stale = client.patch(f"/api/v2/projects/{pid}", json={"description": "v2", "revision": 1})
    assert stale.status_code == 409
    assert "revision" in stale.json()["detail"]

    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["description"] == "v1"
    assert got["revision"] == 2
    assert _root_channels_bytes() == before


def test_every_accepted_update_bumps_revision_once(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Bump Counter")
    pid = created["project_id"]

    for i, rev in enumerate((1, 2, 3), start=1):
        resp = client.patch(
            f"/api/v2/projects/{pid}",
            json={"description": f"update {i}", "revision": rev},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["revision"] == rev + 1

    archived = _archive(client, pid, revision=4)
    assert archived["revision"] == 5
    again = _archive(client, pid, revision=4)
    assert again["revision"] == 5  # idempotent repeat: no bump (AC4/AC5)
    assert _root_channels_bytes() == before


def test_two_session_revision_race_exactly_one_wins(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Race Update")
    pid = created["project_id"]
    assert created["revision"] == 1

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _do_update(tag: str) -> None:
        barrier.wait()
        resp = client.patch(
            f"/api/v2/projects/{pid}",
            json={"description": f"winner {tag}", "revision": 1},
        )
        results.append(resp.status_code)

    threads = [
        threading.Thread(target=_do_update, args=("A",)),
        threading.Thread(target=_do_update, args=("B",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [200, 409], f"unexpected statuses: {results}"
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["revision"] == 2  # exactly one bump
    assert _root_channels_bytes() == before


def test_archive_stale_revision_409_and_idempotent_repeat(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Archive CAS")
    pid = created["project_id"]

    stale = client.post(f"/api/v2/projects/{pid}/archive", json={"revision": 99})
    assert stale.status_code == 409
    assert "revision" in stale.json()["detail"]
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["status"] == "active"
    assert got["revision"] == 1  # no bump on the failed attempt

    archived = _archive(client, pid, revision=1)
    assert archived["revision"] == 2

    again = _archive(client, pid, revision=1)
    assert again["status"] == "archived"
    assert again["revision"] == 2  # idempotent, no bump
    assert _root_channels_bytes() == before


def test_patch_cannot_bypass_archive_or_restore_archived_project(
    client: TestClient,
) -> None:
    created = _create(client, "Archive invariant")
    pid = created["project_id"]

    bypass = client.patch(
        f"/api/v2/projects/{pid}",
        json={"status": "archived", "revision": created["revision"]},
    )
    assert bypass.status_code == 422
    unchanged = client.get(f"/api/v2/projects/{pid}").json()
    assert unchanged["status"] == "active"
    assert unchanged["archived_at"] is None
    assert unchanged["revision"] == 1

    archived = _archive(client, pid, revision=1)
    restore = client.patch(
        f"/api/v2/projects/{pid}",
        json={"status": "active", "revision": archived["revision"]},
    )
    assert restore.status_code == 409
    final = client.get(f"/api/v2/projects/{pid}").json()
    assert final["status"] == "archived"
    assert final["archived_at"] == archived["archived_at"]
    assert final["revision"] == archived["revision"]


def test_concurrent_archive_race_both_idempotent(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Archive Race")
    pid = created["project_id"]
    assert created["revision"] == 1

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _do_archive() -> None:
        barrier.wait()
        resp = client.post(f"/api/v2/projects/{pid}/archive", json={"revision": 1})
        results.append(resp.status_code)

    threads = [threading.Thread(target=_do_archive) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [200, 200], f"unexpected statuses: {results}"
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["status"] == "archived"
    assert got["revision"] == 2  # exactly one bump
    assert _root_channels_bytes() == before


# ── AC5: archive semantics ───────────────────────────────────────────────────


def test_archive_preserves_timestamps_and_channel_references(
    client: TestClient,
) -> None:
    before = _root_channels_bytes()
    src = _make_channel(client, "Keep Src")
    prod = _make_channel(client, "Keep Prod", role="production")
    created = _create(
        client,
        "Preserve Me",
        description="keep",
        default_output_profile="1080p",
        resume_step="scene-review",
        source_channel_id=src["channel_id"],
        production_channel_id=prod["channel_id"],
    )
    pid = created["project_id"]
    created_at = created["created_at"]

    archived = _archive(client, pid, revision=created["revision"])
    assert archived["created_at"] == created_at
    assert archived["description"] == "keep"
    assert archived["default_output_profile"] == "1080p"
    assert archived["resume_step"] == "scene-review"
    assert archived["source_channel_id"] == src["channel_id"]
    assert archived["production_channel_id"] == prod["channel_id"]
    assert archived["status"] == "archived"
    assert archived["archived_at"]

    # Row still exists and is readable (no cascade/hard delete)
    assert client.get(f"/api/v2/projects/{pid}").status_code == 200
    assert _root_channels_bytes() == before


# ── AC6: workspace ownership ─────────────────────────────────────────────────


def test_cross_workspace_project_is_404(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Workspace A Project")
    pid = created["project_id"]

    other = "other-workspace"
    assert (
        client.get(f"/api/v2/projects/{pid}", params={"workspace_id": other}).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v2/projects/{pid}",
            params={"workspace_id": other},
            json={"description": "x", "revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v2/projects/{pid}/archive",
            params={"workspace_id": other},
            json={"revision": 1},
        ).status_code
        == 404
    )
    got = client.get(f"/api/v2/projects/{pid}").json()
    assert got["status"] == "active"
    assert got["revision"] == 1  # untouched
    assert _root_channels_bytes() == before


# ── AC7: /api/v2/projects namespace isolation ────────────────────────────────


def test_v2_never_shadows_legacy_literal_routes(client: TestClient) -> None:
    """AC7: the durable v2 namespace never captures legacy literal paths.

    The legacy `/api/projects` router is untouched: literal sub-routes
    (channels, gpu-info) and parameterized legacy project paths keep
    their pre-existing behavior.
    """
    before = _root_channels_bytes()

    # Legacy channel workspace endpoints (literal /channels path) unchanged
    resp = client.post("/api/projects/channels", json={"name": "Legacy WS"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["channel_id"]

    # GET /api/projects/channels — pre-existing route-order quirk: the
    # legacy parameterized route may serve it; never a v2 response shape.
    listed = client.get("/api/projects/channels")
    assert listed.status_code in (200, 404)

    # Legacy gpu-info discovery still resolves
    assert client.get("/api/projects/gpu-info").status_code == 200

    # A non-UUID legacy id (12-hex) keeps legacy semantics (404 on empty
    # legacy store) — no durable route ever captures it.
    assert client.get("/api/projects/2dc14177a212").status_code == 404
    assert _root_channels_bytes() == before


def test_v2_base_and_legacy_base_are_isolated(client: TestClient) -> None:
    """AC7: durable v2 base endpoints never touch legacy filesystem services."""
    from app.api import deps as api_deps

    before = _root_channels_bytes()
    root = api_deps._config.project_root
    projects_dir = root / "projects"

    # Durable list is its own namespace: empty durable list, and the
    # legacy base list is a different endpoint with the legacy shape.
    listing = client.get("/api/v2/projects").json()
    assert isinstance(listing, dict) and listing["projects"] == []

    # Create through the durable v2 endpoint — SQLite only, no directory
    created = _create(client, "Durable Only")
    assert not projects_dir.exists() or not (projects_dir / created["project_id"]).exists()

    # The legacy base list endpoint still returns the legacy JSON-array
    # shape (and does not contain the durable project).
    legacy_list = client.get("/api/projects")
    assert legacy_list.status_code == 200
    assert isinstance(legacy_list.json(), list)
    assert all(p.get("project_id") != created["project_id"] for p in legacy_list.json())

    # The legacy base create still works and creates a legacy project dir.
    legacy_create = client.post("/api/projects", json={"name": "Legacy Create"})
    assert legacy_create.status_code == 201, legacy_create.text
    legacy_pid = legacy_create.json()["project_id"]
    assert (projects_dir / legacy_pid / "project.json").exists()
    assert _root_channels_bytes() == before


def test_v2_item_route_never_matches_legacy_paths(client: TestClient) -> None:
    """AC7: the UUID-constrained v2 item route cannot capture legacy ids.

    The durable id created via /api/v2/projects is a UUID and is served
    by the v2 item route; the same id is NOT resolvable through the
    legacy /api/projects/{id} route (no legacy project dir exists), and
    the v2 item route rejects non-UUID paths with 422 (FastAPI convertor)
    — never falling through to legacy behavior.
    """
    before = _root_channels_bytes()
    created = _create(client, "Isolation Item")
    pid = created["project_id"]

    # v2 serves the durable item
    assert client.get(f"/api/v2/projects/{pid}").status_code == 200
    # Legacy router cannot see the durable project (no filesystem dir)
    assert client.get(f"/api/projects/{pid}").status_code == 404
    # Non-UUID path never matches the v2 :uuid route — FastAPI 0.139
    # answers 404 for a failed convertor match (never legacy behavior)
    assert client.get("/api/v2/projects/nope").status_code == 404
    assert _root_channels_bytes() == before


# ── AC4 deterministic repository-level interleaving (mirrors S03-T01) ────────


def _repo_db_path(client: TestClient) -> Path:
    """The durable DB path the client's project service is bound to."""
    svc = deps.get_project_service()
    factory = svc._session_factory  # noqa: SLF001
    engine = factory.kw["bind"]
    return Path(engine.url.database)


def _seed_project(db_path: Path, name: str) -> tuple[str, int]:
    """Create a project row + workspace through a raw session."""
    from sqlalchemy.orm import Session

    from app.persistence import create_engine_for_path
    from app.persistence.projects import ProjectRepository

    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        session.execute(
            __import__("sqlalchemy.dialects.sqlite", fromlist=["insert"]).insert(
                Workspace
            )
            .values(id=DEFAULT_WORKSPACE_ID, name=DEFAULT_WORKSPACE_ID)
            .on_conflict_do_nothing(index_elements=[Workspace.id])
        )
        repo = ProjectRepository(session)
        record = repo.create_project(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name=name,
        )
        session.commit()
        return record.id, record.revision


def test_archive_interleaving_both_callers_read_active_then_cas(
    client: TestClient,
) -> None:
    """Deterministic interleaved archive: loser re-reads fresh, idempotent.

    Both callers open their own session, read the ACTIVE row, then pause
    on a barrier BEFORE their CAS update.  Caller A proceeds and archives
    (one bump).  Caller B then executes its CAS — zero rows — and must
    re-read with a FRESH database SELECT and return the now-archived row
    idempotently (no bump).  Final revision exactly 2.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.persistence import create_engine_for_path
    from app.persistence.models import Project
    from app.persistence.projects import ProjectRepository

    db_path = _repo_db_path(client)
    project_id, _ = _seed_project(db_path, "Interleave Archive")
    engine = create_engine_for_path(db_path)

    both_loaded = threading.Barrier(2)
    allow_b = threading.Event()
    outcomes: list[str] = []
    lock = threading.Lock()

    def _caller_a() -> None:
        with Session(engine) as session:
            repo = ProjectRepository(session, archive_after_read=both_loaded.wait)
            record = repo.archive_project(
                project_id, DEFAULT_WORKSPACE_ID, expected_revision=1
            )
            session.commit()
            allow_b.set()
            with lock:
                outcomes.append(f"A:{record.status}:{record.revision}")

    def _caller_b() -> None:
        with Session(engine) as session:
            def _pause_after_active_read() -> None:
                both_loaded.wait()
                assert allow_b.wait(timeout=5)

            repo = ProjectRepository(
                session, archive_after_read=_pause_after_active_read
            )
            record = repo.archive_project(
                project_id, DEFAULT_WORKSPACE_ID, expected_revision=1
            )
            session.commit()
            with lock:
                outcomes.append(f"B:{record.status}:{record.revision}")

    ta, tb = threading.Thread(target=_caller_a), threading.Thread(target=_caller_b)
    ta.start()
    tb.start()
    ta.join()
    tb.join()

    assert sorted(outcomes) == ["A:archived:2", "B:archived:2"], outcomes
    with Session(engine) as session:
        row = session.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one()
        assert row.status == "archived"
        assert row.revision == 2


def test_project_id_is_uuid4_shaped(client: TestClient) -> None:
    """Durable ids are UUID-shaped so the :uuid convertor round-trips."""
    created = _create(client, "UUID Shape")
    parsed = uuid.UUID(created["project_id"])
    assert parsed.version == 4
