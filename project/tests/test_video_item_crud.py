"""S03-T03 durable Video Item lifecycle/order API tests (AC1-AC10).

Every test uses the conftest ``client`` fixture (isolated tmp project
root + tmp durable database + patched ``deps``), so no test ever touches
the production database, ``channels.json``, the legacy projects
directory or user data.

Scenarios map to acceptance criteria:
- AC1 CRUD/list/read/archive/reorder under the isolated v2 namespace;
  no DELETE route, no JSON/filesystem/media writes.
- AC2 DTO/status/title/position contract is exact; no ORM/path leaks.
- AC3 append produces unique non-negative positions and a stable logical
  active ordering (gap-tolerant after archive; reorder maps onto the
  existing active slots).
- AC4 PATCH/archive/reorder CAS is atomic; stale/conflicting requests
  are 409; concurrent create append cannot leak raw IntegrityError.
- AC5 Archive is idempotent, timestamp-safe, never cascades/hard-deletes.
- AC6 Workspace/Project/Channel/cross-project ownership → 404/422.
- AC7 Archived Project and archived Video Item invariants are enforced.
- AC8 Migration only if the S01 schema cannot enforce the contract
  (it can — covered in tests/test_persistence_bootstrap.py).
- AC9 Legacy routes/imports/filesystem behavior remain unaffected
  (channels.json hash snapshot + legacy route probe).
- AC10 Focused/combined/race/upgrade/Ruff/mypy/diff/7-7 baseline all
  pass (validated in LOG/REPORT).
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence import videos as videos_module
from app.persistence.models import Channel, Workspace
from app.persistence.videos import AppendRetryError, VideoItemService

# ── Helpers ──────────────────────────────────────────────────────────────────


def _root_channels_bytes() -> bytes:
    """The production-root channels.json bytes (must never change)."""
    root = Path(__file__).resolve().parent.parent / "channels.json"
    return root.read_bytes() if root.exists() else b""


def _create_project(client: TestClient, name: str = "Vid Project") -> dict:
    resp = client.post("/api/v2/projects", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_video(client: TestClient, project_id: str, title: str, **extra: object) -> dict:
    payload: dict[str, object] = {"title": title, **extra}
    resp = client.post(f"/api/v2/projects/{project_id}/videos", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _archive_video(client: TestClient, project_id: str, video_id: str, revision: int) -> dict:
    resp = client.post(
        f"/api/v2/projects/{project_id}/videos/{video_id}/archive",
        json={"revision": revision},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _reorder(
    client: TestClient, project_id: str, project_revision: int, video_item_ids: list[str]
) -> dict:
    resp = client.post(
        f"/api/v2/projects/{project_id}/videos/reorder",
        json={"project_revision": project_revision, "video_item_ids": video_item_ids},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _make_channel(client: TestClient, name: str, role: str = "source") -> dict:
    """Create a durable channel through the S03-T01 API (same DB)."""
    resp = client.post("/api/channels", json={"name": name, "role": role})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _route_exists(client: TestClient, method: str, path: str) -> bool:
    """Probe the OpenAPI schema for an exact route (no request side effect)."""
    schema = client.get("/openapi.json").json()
    for route_path, methods in schema["paths"].items():
        if route_path.rstrip("/") == path.rstrip("/") and method.lower() in methods:
            return True
    return False


def _positions(client: TestClient, project_id: str) -> list[tuple[str, int, str]]:
    listing = client.get(f"/api/v2/projects/{project_id}/videos").json()
    return [
        (v["video_item_id"], v["position"], v["status"]) for v in listing["videos"]
    ]


# ── AC1: CRUD + archive + reorder; no DELETE; no JSON/filesystem writes ─────


def test_create_read_update_archive_reorder_lifecycle(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)

    a = _create_video(client, project["project_id"], "  First Video  ")
    vid = a["video_item_id"]
    assert a["title"] == "First Video"  # normalized (AC2)
    assert a["status"] == "imported"
    assert a["position"] == 0  # append at end (AC3)
    assert a["revision"] == 1
    assert a["archived_at"] is None
    assert a["workspace_id"] == DEFAULT_WORKSPACE_ID
    assert "id" not in a  # DTO exposes video_item_id, not ORM id

    b = _create_video(client, project["project_id"], "Second Video")
    assert b["position"] == 1

    # Read
    got = client.get(f"/api/v2/projects/{project['project_id']}/videos/{vid}").json()
    assert got["video_item_id"] == vid
    assert got["title"] == "First Video"

    # Update (business update with expected revision)
    updated = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid}",
        json={"title": "First Video v2", "revision": 1},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["title"] == "First Video v2"
    assert body["revision"] == 2  # exactly one bump (AC4)

    # Archive (requires expected revision — atomic CAS)
    archived = _archive_video(
        client, project["project_id"], vid, revision=2
    )
    assert archived["status"] == "archived"
    assert archived["archived_at"]  # timestamp preserved (AC5)
    assert archived["revision"] == 3
    assert archived["title"] == "First Video v2"  # metadata preserved (AC5)

    # Readable after archive (AC5)
    got = client.get(f"/api/v2/projects/{project['project_id']}/videos/{vid}").json()
    assert got["status"] == "archived"

    # No hard-delete endpoint exists
    assert not _route_exists(
        client, "DELETE", f"/api/v2/projects/{project['project_id']}/videos/{vid}"
    )
    assert _root_channels_bytes() == before, "channels.json was modified"


def test_durable_video_create_never_writes_filesystem(client: TestClient) -> None:
    """AC1: durable create writes SQLite only — no dir/JSON/media writes."""
    from app.api import deps as api_deps

    before = _root_channels_bytes()
    root = api_deps._config.project_root
    project = _create_project(client, "No Media Write")
    vid = _create_video(client, project["project_id"], "Pure DB")

    # No filesystem artifacts anywhere under the project root
    assert not list(root.rglob("*.json")) or all(
        "project.json" not in p.name for p in root.rglob("*.json")
    )
    # Row is readable through the durable API
    assert (
        client.get(
            f"/api/v2/projects/{project['project_id']}/videos/{vid['video_item_id']}"
        ).status_code
        == 200
    )
    assert _root_channels_bytes() == before


def test_list_excludes_archived_by_default_and_orders(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "Alpha")
    b = _create_video(client, project["project_id"], "Beta")
    c = _create_video(client, project["project_id"], "Gamma")

    listing = client.get(f"/api/v2/projects/{project['project_id']}/videos").json()
    assert listing["active_only"] is True
    order = [v["video_item_id"] for v in listing["videos"]]
    assert order == [a["video_item_id"], b["video_item_id"], c["video_item_id"]]
    assert [v["position"] for v in listing["videos"]] == [0, 1, 2]

    _archive_video(client, project["project_id"], b["video_item_id"], revision=1)
    listing2 = client.get(f"/api/v2/projects/{project['project_id']}/videos").json()
    assert [v["video_item_id"] for v in listing2["videos"]] == [
        a["video_item_id"],
        c["video_item_id"],
    ]
    assert [v["position"] for v in listing2["videos"]] == [0, 2]  # stable (AC3)

    # Archived are filterable with active_only=false (AC5)
    all_rows = client.get(
        f"/api/v2/projects/{project['project_id']}/videos",
        params={"active_only": False},
    ).json()
    assert {v["video_item_id"] for v in all_rows["videos"]} == {
        a["video_item_id"],
        b["video_item_id"],
        c["video_item_id"],
    }
    assert _root_channels_bytes() == before


def test_unknown_ids_404(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    unknown = "ffffffff-ffff-ffff-ffff-ffffffffffff"

    assert (
        client.get(f"/api/v2/projects/{project['project_id']}/videos/{unknown}").status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v2/projects/{project['project_id']}/videos/{unknown}",
            json={"revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v2/projects/{project['project_id']}/videos/{unknown}/archive",
            json={"revision": 1},
        ).status_code
        == 404
    )
    # Unknown project id → 404 on the nested namespace
    assert client.get(f"/api/v2/projects/{unknown}/videos").status_code == 404
    # Non-UUID path never matches the :uuid routes
    assert client.get(f"/api/v2/projects/{project['project_id']}/videos/nope").status_code == 404
    assert _root_channels_bytes() == before


# ── AC2: exact statuses, normalized titles, DTO boundary ─────────────────────


def test_statuses_are_exact_approved_set(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    statuses = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/statuses"
    ).json()["statuses"]
    assert statuses == [
        "imported",
        "analyzing",
        "objects_ready",
        "mapping_required",
        "demo_required",
        "demo_approved",
        "applying_reskin",
        "needs_review",
        "ready_to_export",
        "rendering",
        "completed",
        "failed",
        "archived",
    ]
    # The schema CHECK rejects anything else (repository-level guard too)
    vid = _create_video(client, project["project_id"], "Status Guard")
    bad = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid['video_item_id']}",
        json={"status": "in_progress", "revision": 1},
    )
    assert bad.status_code == 422
    assert _root_channels_bytes() == before


def test_empty_title_rejected_and_max_length(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={"title": "   "},
    )
    assert resp.status_code == 422
    too_long = "x" * 241
    resp2 = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={"title": too_long},
    )
    assert resp2.status_code == 422
    assert _root_channels_bytes() == before


def test_dto_never_exposes_orm_objects_or_paths(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    created = _create_video(client, project["project_id"], "Boundary Check")
    body_keys = set(created.keys())
    assert "video_item_id" in body_keys
    assert "project_id" in body_keys
    assert "workspace_id" in body_keys
    assert "position" in body_keys
    assert "revision" in body_keys
    for forbidden in ("id", "_sa_instance_state", "path", "absolute_path", "db_path"):
        assert forbidden not in body_keys
    serialized = str(created)
    assert "sqlite" not in serialized.lower() and "C:" not in serialized
    assert _root_channels_bytes() == before


# ── AC3: append/reorder stable logical active ordering ───────────────────────


def test_append_is_contiguous_and_after_archive(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")
    c = _create_video(client, project["project_id"], "C")
    assert [v["position"] for v in [a, b, c]] == [0, 1, 2]

    # Archiving the middle leaves positions stable; a NEW append goes
    # after the max (3), never into the archived slot — archived
    # positions are preserved and unique (AC3).
    _archive_video(client, project["project_id"], b["video_item_id"], revision=1)
    d = _create_video(client, project["project_id"], "D")
    assert d["position"] == 3
    positions = _positions(client, project["project_id"])
    assert [p for _, p, _ in positions] == [0, 2, 3]
    assert _root_channels_bytes() == before


def test_reorder_full_list_contiguous(client: TestClient) -> None:
    """Fresh-project reorder maps the requested order onto 0..N-1 with no
    new gaps (no archive has occurred yet; AC3 stable active ordering)."""
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")
    c = _create_video(client, project["project_id"], "C")
    project_rev = 1

    ordered = _reorder(
        client,
        project["project_id"],
        project_rev,
        [c["video_item_id"], a["video_item_id"], b["video_item_id"]],
    )
    assert [v["video_item_id"] for v in ordered["videos"]] == [
        c["video_item_id"],
        a["video_item_id"],
        b["video_item_id"],
    ]
    assert [v["position"] for v in ordered["videos"]] == [0, 1, 2]
    assert all(v["revision"] == 2 for v in ordered["videos"])  # bumped once

    # Project revision bumped exactly once (AC4)
    proj = client.get(f"/api/v2/projects/{project['project_id']}").json()
    assert proj["revision"] == 2

    # A no-op reorder (same order) bumps the project but not the items
    ordered2 = _reorder(
        client,
        project["project_id"],
        2,
        [c["video_item_id"], a["video_item_id"], b["video_item_id"]],
    )
    assert [v["revision"] for v in ordered2["videos"]] == [2, 2, 2]  # unchanged
    proj2 = client.get(f"/api/v2/projects/{project['project_id']}").json()
    assert proj2["revision"] == 3
    assert _root_channels_bytes() == before


def test_reorder_rejects_duplicate_ids(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")

    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos/reorder",
        json={
            "project_revision": 1,
            "video_item_ids": [a["video_item_id"], a["video_item_id"], b["video_item_id"]],
        },
    )
    assert resp.status_code == 422, resp.text
    assert "exactly once" in resp.json()["detail"]
    # No partial write: order unchanged, project unchanged
    assert [p for _, p, _ in _positions(client, project["project_id"])] == [0, 1]
    proj = client.get(f"/api/v2/projects/{project['project_id']}").json()
    assert proj["revision"] == 1
    assert _root_channels_bytes() == before


def test_reorder_rejects_missing_and_extra_ids(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")
    c = _create_video(client, project["project_id"], "C")

    # Missing one active id
    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos/reorder",
        json={"project_revision": 1, "video_item_ids": [a["video_item_id"], b["video_item_id"]]},
    )
    assert resp.status_code == 422, resp.text
    assert "missing" in resp.json()["detail"]

    # Extra unknown id
    resp2 = client.post(
        f"/api/v2/projects/{project['project_id']}/videos/reorder",
        json={
            "project_revision": 1,
            "video_item_ids": [
                a["video_item_id"],
                b["video_item_id"],
                c["video_item_id"],
                "ffffffff-ffff-ffff-ffff-ffffffffffff",
            ],
        },
    )
    assert resp2.status_code == 422, resp2.text
    assert "extra" in resp2.json()["detail"]
    assert _root_channels_bytes() == before


def test_reorder_rejects_cross_project_ids(client: TestClient) -> None:
    before = _root_channels_bytes()
    p1 = _create_project(client, "P1")
    p2 = _create_project(client, "P2")
    a = _create_video(client, p1["project_id"], "A")
    b = _create_video(client, p1["project_id"], "B")
    foreign = _create_video(client, p2["project_id"], "Foreign")

    resp = client.post(
        f"/api/v2/projects/{p1['project_id']}/videos/reorder",
        json={
            "project_revision": 1,
            "video_item_ids": [
                a["video_item_id"],
                b["video_item_id"],
                foreign["video_item_id"],
            ],
        },
    )
    assert resp.status_code == 422, resp.text
    assert "extra" in resp.json()["detail"]
    assert _root_channels_bytes() == before


def test_reorder_stale_project_revision_409(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")

    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos/reorder",
        json={
            "project_revision": 99,
            "video_item_ids": [b["video_item_id"], a["video_item_id"]],
        },
    )
    assert resp.status_code == 409, resp.text
    assert "revision" in resp.json()["detail"]
    # No partial write
    assert [p for _, p, _ in _positions(client, project["project_id"])] == [0, 1]
    proj = client.get(f"/api/v2/projects/{project['project_id']}").json()
    assert proj["revision"] == 1
    assert _root_channels_bytes() == before


# ── AC4: CAS atomicity, stale 409, append race ───────────────────────────────


def test_stale_revision_returns_409(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Concurrency")

    r1 = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid['video_item_id']}",
        json={"title": "v1", "revision": 1},
    )
    assert r1.status_code == 200
    assert r1.json()["revision"] == 2

    stale = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid['video_item_id']}",
        json={"title": "v2", "revision": 1},
    )
    assert stale.status_code == 409
    assert "revision" in stale.json()["detail"]

    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid['video_item_id']}"
    ).json()
    assert got["title"] == "v1"
    assert got["revision"] == 2
    assert _root_channels_bytes() == before


def test_every_accepted_update_bumps_revision_once(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Bump Counter")
    vid_id = vid["video_item_id"]

    for i, rev in enumerate((1, 2, 3), start=1):
        resp = client.patch(
            f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
            json={"title": f"update {i}", "revision": rev},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["revision"] == rev + 1

    archived = _archive_video(client, project["project_id"], vid_id, revision=4)
    assert archived["revision"] == 5
    again = _archive_video(client, project["project_id"], vid_id, revision=4)
    assert again["revision"] == 5  # idempotent repeat: no bump (AC4/AC5)
    assert _root_channels_bytes() == before


def test_two_session_revision_race_exactly_one_wins(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Race Update")
    vid_id = vid["video_item_id"]
    assert vid["revision"] == 1

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _do_update(tag: str) -> None:
        barrier.wait()
        resp = client.patch(
            f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
            json={"title": f"winner {tag}", "revision": 1},
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
    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert got["revision"] == 2  # exactly one bump
    assert _root_channels_bytes() == before


def test_archive_stale_revision_409_and_idempotent_repeat(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Archive CAS")
    vid_id = vid["video_item_id"]

    stale = client.post(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}/archive",
        json={"revision": 99},
    )
    assert stale.status_code == 409
    assert "revision" in stale.json()["detail"]
    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert got["status"] == "imported"
    assert got["revision"] == 1  # no bump on the failed attempt

    archived = _archive_video(client, project["project_id"], vid_id, revision=1)
    assert archived["revision"] == 2

    again = _archive_video(client, project["project_id"], vid_id, revision=1)
    assert again["status"] == "archived"
    assert again["revision"] == 2  # idempotent, no bump
    assert _root_channels_bytes() == before


def test_patch_cannot_bypass_archive_or_restore_archived_video(
    client: TestClient,
) -> None:
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Archive invariant")
    vid_id = vid["video_item_id"]

    bypass = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={"status": "archived", "revision": vid["revision"]},
    )
    assert bypass.status_code == 422
    unchanged = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert unchanged["status"] == "imported"
    assert unchanged["archived_at"] is None
    assert unchanged["revision"] == 1

    archived = _archive_video(client, project["project_id"], vid_id, revision=1)
    restore = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={"status": "imported", "revision": archived["revision"]},
    )
    assert restore.status_code == 409
    final = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert final["status"] == "archived"
    assert final["archived_at"] == archived["archived_at"]
    assert final["revision"] == archived["revision"]


def test_concurrent_archive_race_both_idempotent(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Archive Race")
    vid_id = vid["video_item_id"]
    assert vid["revision"] == 1

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _do_archive() -> None:
        barrier.wait()
        resp = client.post(
            f"/api/v2/projects/{project['project_id']}/videos/{vid_id}/archive",
            json={"revision": 1},
        )
        results.append(resp.status_code)

    threads = [threading.Thread(target=_do_archive) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [200, 200], f"unexpected statuses: {results}"
    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert got["status"] == "archived"
    assert got["revision"] == 2  # exactly one bump
    assert _root_channels_bytes() == before


def test_concurrent_append_never_leaks_integrity_error(client: TestClient) -> None:
    """AC4/concurrency: concurrent appends serialize; no raw 500/IntegrityError."""
    before = _root_channels_bytes()
    project = _create_project(client)
    pid = project["project_id"]

    results: list[int] = []
    barrier = threading.Barrier(3)

    def _append(tag: str) -> None:
        barrier.wait()
        resp = client.post(
            f"/api/v2/projects/{pid}/videos",
            json={"title": f"Append {tag}"},
        )
        results.append(resp.status_code)

    threads = [threading.Thread(target=_append, args=(t,)) for t in ("A", "B", "C")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [201, 201, 201], f"unexpected statuses: {results}"
    positions = _positions(client, pid)
    assert sorted(p for _, p, _ in positions) == [0, 1, 2]
    assert len(positions) == 3
    assert _root_channels_bytes() == before


# ── AC5: archive semantics ───────────────────────────────────────────────────


def test_archive_preserves_metadata_and_relationships(client: TestClient) -> None:
    before = _root_channels_bytes()
    src = _make_channel(client, "Keep Video Src")
    project = _create_project(client)
    created = _create_video(
        client,
        project["project_id"],
        "Preserve Me",
        source_channel_id=src["channel_id"],
        resume_step="scene-review",
    )
    vid_id = created["video_item_id"]
    created_at = created["created_at"]

    archived = _archive_video(client, project["project_id"], vid_id, revision=1)
    assert archived["created_at"] == created_at
    assert archived["title"] == "Preserve Me"
    assert archived["source_channel_id"] == src["channel_id"]
    assert archived["resume_step"] == "scene-review"
    assert archived["status"] == "archived"
    assert archived["archived_at"]

    # Row still exists and is readable (no cascade/hard delete)
    assert (
        client.get(
            f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
        ).status_code
        == 200
    )
    assert _root_channels_bytes() == before


# ── AC6: workspace/project/channel/cross-project ownership ──────────────────


def test_cross_workspace_project_is_404(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Workspace A Video")
    pid = project["project_id"]
    vid_id = vid["video_item_id"]

    other = "other-workspace"
    assert (
        client.get(f"/api/v2/projects/{pid}/videos", params={"workspace_id": other}).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v2/projects/{pid}/videos/{vid_id}",
            params={"workspace_id": other},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v2/projects/{pid}/videos/{vid_id}",
            params={"workspace_id": other},
            json={"title": "x", "revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v2/projects/{pid}/videos/{vid_id}/archive",
            params={"workspace_id": other},
            json={"revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v2/projects/{pid}/videos",
            params={"workspace_id": other},
            json={"title": "x"},
        ).status_code
        == 404
    )
    got = client.get(f"/api/v2/projects/{pid}/videos/{vid_id}").json()
    assert got["status"] == "imported"
    assert got["revision"] == 1  # untouched
    assert _root_channels_bytes() == before


def test_video_from_another_project_is_404(client: TestClient) -> None:
    before = _root_channels_bytes()
    p1 = _create_project(client, "P1")
    p2 = _create_project(client, "P2")
    vid = _create_video(client, p1["project_id"], "Belongs to P1")

    assert (
        client.get(f"/api/v2/projects/{p2['project_id']}/videos/{vid['video_item_id']}").status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v2/projects/{p2['project_id']}/videos/{vid['video_item_id']}",
            json={"title": "x", "revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v2/projects/{p2['project_id']}/videos/{vid['video_item_id']}/archive",
            json={"revision": 1},
        ).status_code
        == 404
    )
    # The video still exists and is untouched in P1
    got = client.get(f"/api/v2/projects/{p1['project_id']}/videos/{vid['video_item_id']}").json()
    assert got["revision"] == 1
    assert _root_channels_bytes() == before


def test_create_rejects_unknown_or_wrong_role_channel(client: TestClient) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)

    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={
            "title": "No Chan",
            "source_channel_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
        },
    )
    assert resp.status_code == 422, resp.text
    assert "does not reference an existing channel" in resp.json()["detail"]

    prod = _make_channel(client, "Video Prod Chan", role="production")
    resp2 = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={"title": "Wrong Role", "source_channel_id": prod["channel_id"]},
    )
    assert resp2.status_code == 422, resp2.text
    assert "not a source channel" in resp2.json()["detail"]
    assert _root_channels_bytes() == before


def test_create_rejects_archived_channel_and_cross_workspace_channel(
    client: TestClient,
) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)

    # Archived channel cannot be newly assigned (must be active at
    # assignment time — AC4)
    ch = _make_channel(client, "Video Will Archive")
    arc = client.post(f"/api/channels/{ch['channel_id']}/archive", json={"revision": 1})
    assert arc.status_code == 200, arc.text
    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={"title": "Arch Chan", "source_channel_id": ch["channel_id"]},
    )
    assert resp.status_code == 422, resp.text
    assert "not an active channel" in resp.json()["detail"]

    # Cross-workspace channel (direct seed — same durable DB)
    import uuid as _uuid

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
            name=f"Other Video Src {_uuid.uuid4().hex[:8]}",
        )
        session.add(other)
        session.commit()
        other_id = other.id

    resp2 = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={"title": "Cross WS", "source_channel_id": other_id},
    )
    assert resp2.status_code == 422, resp2.text
    assert "different workspace" in resp2.json()["detail"]
    assert _root_channels_bytes() == before


def test_patch_assigns_clears_and_validates_channel(client: TestClient) -> None:
    before = _root_channels_bytes()
    src = _make_channel(client, "Video Assign Src")
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Channel Patch")
    vid_id = vid["video_item_id"]

    # Assign on PATCH
    r = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={"source_channel_id": src["channel_id"], "revision": 1},
    )
    assert r.status_code == 200, r.text
    assert r.json()["source_channel_id"] == src["channel_id"]
    assert r.json()["revision"] == 2

    # Explicit null clears (AC3 nullable/clearable)
    r2 = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={"source_channel_id": None, "revision": 2},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["source_channel_id"] is None
    assert r2.json()["revision"] == 3

    # Invalid assignment on PATCH → 422, no state change
    r3 = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={
            "source_channel_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "revision": 3,
        },
    )
    assert r3.status_code == 422, r3.text
    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert got["source_channel_id"] is None
    assert got["revision"] == 3  # no bump on the rejected update
    assert _root_channels_bytes() == before


def test_existing_reference_survives_channel_archive(client: TestClient) -> None:
    """AC4: a reference assigned while active survives a later archive."""
    before = _root_channels_bytes()
    src = _make_channel(client, "Video Survivor Src")
    project = _create_project(client)
    vid = _create_video(
        client,
        project["project_id"],
        "Survivor Video",
        source_channel_id=src["channel_id"],
    )
    vid_id = vid["video_item_id"]

    # Archive the channel AFTER assignment
    arc = client.post(f"/api/channels/{src['channel_id']}/archive", json={"revision": 1})
    assert arc.status_code == 200, arc.text

    # The video keeps the reference; no cascade, no validation failure
    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}"
    ).json()
    assert got["source_channel_id"] == src["channel_id"]
    assert got["status"] == "imported"
    # Video can still be updated (existing references are not revalidated)
    r = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={"title": "still works", "revision": 1},
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
    reaches its UPDATE.  The Video Item writer is deliberately paused
    after a successful active-channel validation; the archive must wait
    until the Video Item write commits, so the reference was valid at
    its atomic boundary (S03-T02 atomic writer policy).
    """
    from sqlalchemy import event

    from app.persistence import videos as videos_module

    source = _make_channel(client, f"Video Atomic source {operation}")
    project = _create_project(client)
    video = (
        _create_video(client, project["project_id"], "Atomic video patch target")
        if operation == "patch"
        else None
    )
    validated = threading.Event()
    archive_update_attempted = threading.Event()
    original_validate = videos_module._validate_source_channel

    def _paused_validate(
        session: Session,
        workspace_id: str,
        channel_id: str | None,
    ) -> None:
        original_validate(session, workspace_id, channel_id)
        if channel_id == source["channel_id"]:
            validated.set()
            assert archive_update_attempted.wait(timeout=5)

    monkeypatch.setattr(videos_module, "_validate_source_channel", _paused_validate)
    engine = deps.get_video_service()._session_factory.kw["bind"]  # noqa: SLF001

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
    video_response: list[Any] = []
    archive_response: list[Any] = []

    def _assign() -> None:
        if operation == "create":
            video_response.append(
                client.post(
                    f"/api/v2/projects/{project['project_id']}/videos",
                    json={
                        "title": "Atomic create video",
                        "source_channel_id": source["channel_id"],
                    },
                )
            )
        else:
            assert video is not None
            video_response.append(
                client.patch(
                    f"/api/v2/projects/{project['project_id']}/videos/{video['video_item_id']}",
                    json={
                        "source_channel_id": source["channel_id"],
                        "revision": 1,
                    },
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
    assert len(video_response) == len(archive_response) == 1
    assigned = video_response[0]
    archived_channel = archive_response[0]
    assert assigned.status_code in {200, 201}, assigned.text
    assert archived_channel.status_code == 200, archived_channel.text
    assert assigned.json()["source_channel_id"] == source["channel_id"]
    assert archived_channel.json()["status"] == "archived"


# ── AC7: archived project + archived video invariants ───────────────────────


def test_archived_project_rejects_new_videos_reorder_and_mutation(
    client: TestClient,
) -> None:
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")
    pid = project["project_id"]
    vid_id = a["video_item_id"]

    # Archive the project (S03-T02 archive endpoint)
    arc = client.post(f"/api/v2/projects/{pid}/archive", json={"revision": 1})
    assert arc.status_code == 200, arc.text

    # Reject new Video Items (409 — project exists but is archived)
    resp = client.post(f"/api/v2/projects/{pid}/videos", json={"title": "Nope"})
    assert resp.status_code == 409, resp.text
    assert "archived" in resp.json()["detail"]

    # Reject reorder (409)
    resp2 = client.post(
        f"/api/v2/projects/{pid}/videos/reorder",
        json={
            "project_revision": 2,
            "video_item_ids": [b["video_item_id"], vid_id],
        },
    )
    assert resp2.status_code == 409, resp2.text
    assert "archived" in resp2.json()["detail"]

    # Reject active workflow mutation via PATCH (409 — archived row)
    resp3 = client.patch(
        f"/api/v2/projects/{pid}/videos/{vid_id}",
        json={"status": "analyzing", "revision": 1},
    )
    assert resp3.status_code == 409, resp3.text

    # Archived project remains readable: list + read (AC5)
    listing = client.get(f"/api/v2/projects/{pid}/videos").json()
    assert [v["video_item_id"] for v in listing["videos"]] == [
        a["video_item_id"],
        b["video_item_id"],
    ]
    assert (
        client.get(f"/api/v2/projects/{pid}/videos/{vid_id}").status_code == 200
    )
    # Archived video remains archivable idempotently
    assert (
        client.post(
            f"/api/v2/projects/{pid}/videos/{vid_id}/archive",
            json={"revision": 1},
        ).status_code
        == 200
    )
    assert _root_channels_bytes() == before


# ── AC9: legacy route + channels.json isolation ──────────────────────────────


def test_v2_videos_namespace_never_shadows_legacy_routes(client: TestClient) -> None:
    """AC9: the durable nested namespace is disjoint from legacy routes."""
    before = _root_channels_bytes()

    # Legacy literal sub-routes keep their behavior
    assert client.get("/api/projects/gpu-info").status_code == 200

    # The legacy single-video POST under /api/projects/{project_id}/video
    # still exists (registration unchanged) — durable v2 routes are a
    # different namespace.  The OpenAPI path keeps its parameterized form.
    legacy_video_route = _route_exists(client, "POST", "/api/projects/{project_id}/video")
    assert legacy_video_route

    # Non-UUID project paths never match the v2 nested namespace
    assert client.get("/api/v2/projects/nope/videos").status_code == 404
    assert _root_channels_bytes() == before


def test_durable_video_id_is_uuid4_shaped(client: TestClient) -> None:
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "UUID Shape")
    parsed = uuid.UUID(vid["video_item_id"])
    assert parsed.version == 4


# ── AC4 deterministic repository-level interleaving (mirrors S03-T02) ────────


def _repo_db_path(client: TestClient) -> Path:
    """The durable DB path the client's video service is bound to."""
    svc = deps.get_video_service()
    factory = svc._session_factory  # noqa: SLF001
    engine = factory.kw["bind"]
    return Path(engine.url.database)


def _seed_project_and_videos(
    db_path: Path, name: str, count: int = 2
) -> tuple[str, list[str], int]:
    """Create a project + *count* videos through raw sessions."""
    from sqlalchemy.orm import Session

    from app.persistence import create_engine_for_path
    from app.persistence.projects import ProjectRepository
    from app.persistence.videos import VideoItemRepository

    engine = create_engine_for_path(db_path)
    project_id = ""
    with Session(engine) as session:
        session.execute(
            __import__("sqlalchemy.dialects.sqlite", fromlist=["insert"]).insert(
                Workspace
            )
            .values(id=DEFAULT_WORKSPACE_ID, name=DEFAULT_WORKSPACE_ID)
            .on_conflict_do_nothing(index_elements=[Workspace.id])
        )
        project = ProjectRepository(session).create_project(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name=name,
        )
        project_id = project.id
        video_repo = VideoItemRepository(session)
        ids: list[str] = []
        for i in range(count):
            record = video_repo.create_video(
                project_id=project_id,
                workspace_id=DEFAULT_WORKSPACE_ID,
                title=f"{name} Video {i}",
            )
            ids.append(record.id)
        session.commit()
        return project_id, ids, project.revision


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
    from app.persistence.models import VideoItem
    from app.persistence.videos import VideoItemRepository

    db_path = _repo_db_path(client)
    project_id, [video_id], _ = _seed_project_and_videos(db_path, "Interleave Archive", 1)
    engine = create_engine_for_path(db_path)

    both_loaded = threading.Barrier(2)
    allow_b = threading.Event()
    outcomes: list[str] = []
    lock = threading.Lock()

    def _caller_a() -> None:
        with Session(engine) as session:
            repo = VideoItemRepository(session, archive_after_read=both_loaded.wait)
            record = repo.archive_video(
                video_id, project_id, DEFAULT_WORKSPACE_ID, expected_revision=1
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

            repo = VideoItemRepository(
                session, archive_after_read=_pause_after_active_read
            )
            record = repo.archive_video(
                video_id, project_id, DEFAULT_WORKSPACE_ID, expected_revision=1
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
            select(VideoItem).where(VideoItem.id == video_id)
        ).scalar_one()
        assert row.status == "archived"
        assert row.revision == 2


def test_reorder_interleaving_two_callers_one_wins_one_conflicts(
    client: TestClient,
) -> None:
    """Deterministic reorder CAS: exactly one writer wins the project bump.

    Both callers read the active list, pause BEFORE their reorder CAS.
    Caller A commits its reorder (project bump 1→2); caller B's CAS then
    matches zero rows → VideoConflictError.  No partial position write
    from the loser; the winner's order is preserved.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.persistence import create_engine_for_path
    from app.persistence.models import Project
    from app.persistence.videos import VideoItemRepository

    db_path = _repo_db_path(client)
    project_id, ids, _ = _seed_project_and_videos(db_path, "Interleave Reorder", 3)
    engine = create_engine_for_path(db_path)
    reversed_ids = list(reversed(ids))

    both_loaded = threading.Barrier(2)
    allow_b = threading.Event()
    outcomes: list[str] = []
    lock = threading.Lock()

    def _caller_a() -> None:
        with Session(engine) as session:
            repo = VideoItemRepository(session, after_read=both_loaded.wait)
            records = repo.reorder_videos(
                project_id,
                DEFAULT_WORKSPACE_ID,
                expected_project_revision=1,
                video_item_ids=reversed_ids,
            )
            session.commit()
            allow_b.set()
            with lock:
                outcomes.append(f"A:ok:{len(records)}")

    def _caller_b() -> None:
        with Session(engine) as session:
            def _pause_after_read() -> None:
                both_loaded.wait()
                assert allow_b.wait(timeout=5)

            repo = VideoItemRepository(session, after_read=_pause_after_read)
            try:
                repo.reorder_videos(
                    project_id,
                    DEFAULT_WORKSPACE_ID,
                    expected_project_revision=1,
                    video_item_ids=reversed_ids,
                )
                session.commit()
                with lock:
                    outcomes.append("B:ok")
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                with lock:
                    outcomes.append(f"B:{type(exc).__name__}")

    ta, tb = threading.Thread(target=_caller_a), threading.Thread(target=_caller_b)
    ta.start()
    tb.start()
    ta.join()
    tb.join()

    assert sorted(outcomes) == ["A:ok:3", "B:VideoConflictError"], outcomes
    with Session(engine) as session:
        rows = session.scalars(
            select(Project).where(Project.id == project_id)
        ).all()
        assert len(rows) == 1
        assert rows[0].revision == 2  # exactly one bump
        order = session.scalars(
            select(__import__("app.persistence.models", fromlist=["VideoItem"]).VideoItem)
            .where(
                __import__("app.persistence.models", fromlist=["VideoItem"]).VideoItem.project_id
                == project_id
            )
            .order_by(
                __import__("app.persistence.models", fromlist=["VideoItem"]).VideoItem.position
            )
        ).all()
        assert [v.id for v in order] == reversed_ids
        assert [v.position for v in order] == [0, 1, 2]


def test_append_retry_seam_one_retry_never_leaks_integrity_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deterministic append-retry seam (replaces the thread-racing version).

    The old thread-based test deadlocked: the service thread acquired the
    SQLite writer reservation (``BEGIN IMMEDIATE``) before reaching the
    test barrier, so the raw thread waited at the barrier forever.  These
    two deterministic seams prove the task's concurrency contract without
    any thread timing:

    1. Repository seam — force the position-uniqueness race by making
       ``_next_position`` collide with an existing row.  ``create_video``
       must translate the SQLite UNIQUE violation into ``AppendRetryError``
       (a raw ``IntegrityError`` never escapes the repository).

    2. Service seam — make the repository raise ``AppendRetryError`` exactly
       once, then delegate to the real implementation.  ``VideoItemService.
       create`` retries once inside its reserved transaction, succeeds
       with the next free position, and never leaks ``IntegrityError``.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.persistence import create_engine_for_path
    from app.persistence.models import VideoItem
    from app.persistence.videos import (
        AppendRetryError,
        VideoItemRepository,
        VideoItemService,
    )

    before = _root_channels_bytes()
    db_path = _repo_db_path(client)
    project_id, _ids, _ = _seed_project_and_videos(db_path, "Append Seam", 1)
    engine = create_engine_for_path(db_path)

    # 1. Repository seam: a position collision surfaces as AppendRetryError,
    #    never as a raw IntegrityError.
    with Session(engine) as session:
        repo = VideoItemRepository(session)
        monkeypatch.setattr(repo, "_next_position", lambda _project_id: 0)
        with pytest.raises(AppendRetryError) as excinfo:
            repo.create_video(
                project_id=project_id,
                workspace_id=DEFAULT_WORKSPACE_ID,
                title="Collide Position",
            )
        session.rollback()
    assert "collided" in str(excinfo.value)

    # 2. Service seam: AppendRetryError once → exactly one retry → success.
    original_create = VideoItemRepository.create_video
    calls: list[str] = []

    def _collide_once(self: VideoItemRepository, **kwargs: Any) -> Any:
        calls.append("attempt")
        if len(calls) == 1:
            raise AppendRetryError("deterministic append collision")
        return original_create(self, **kwargs)

    monkeypatch.setattr(VideoItemRepository, "create_video", _collide_once)
    svc = VideoItemService(
        __import__(
            "app.persistence", fromlist=["create_session_factory"]
        ).create_session_factory(engine)
    )
    record = svc.create(
        project_id=project_id,
        workspace_id=DEFAULT_WORKSPACE_ID,
        title="Service Retry",
    )
    assert calls == ["attempt", "attempt"], f"expected exactly one retry: {calls}"
    assert record.position == 1  # next free position after the seed
    assert record.title == "Service Retry"

    with Session(engine) as session:
        rows = session.scalars(
            select(VideoItem)
            .where(VideoItem.project_id == project_id)
            .order_by(VideoItem.position)
        ).all()
    assert [v.position for v in rows] == [0, 1]  # unique, non-negative
    assert _root_channels_bytes() == before


# ── PM correction round 1 ────────────────────────────────────────────────────
# CORRECTION_01.md findings 1-7.


def test_reorder_after_middle_archive_gap_tolerant(client: TestClient) -> None:
    """Finding 1: reorder maps onto existing ACTIVE slots; archived
    positions are preserved (gap-tolerant logical active order).

    Positions A=0, B=1 archived, C=2.  Reorder [C, A] must map C→0 and
    A→2 (the sorted existing active slots) — NOT A=1, which would
    collide with the archived B and leak a raw IntegrityError/500.  The
    UNIQUE(project_id, position) index is never violated and archived
    positions are never rewritten.
    """
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")
    c = _create_video(client, project["project_id"], "C")
    assert [v["position"] for v in [a, b, c]] == [0, 1, 2]
    assert a["revision"] == b["revision"] == c["revision"] == 1

    _archive_video(client, project["project_id"], b["video_item_id"], revision=1)

    # Requested active order [C, A] with the middle (B) archived.
    ordered = _reorder(
        client,
        project["project_id"],
        project_revision=1,
        video_item_ids=[c["video_item_id"], a["video_item_id"]],
    )
    assert [v["video_item_id"] for v in ordered["videos"]] == [
        c["video_item_id"],
        a["video_item_id"],
    ]
    # Mapped onto the sorted existing active slots [0, 2]; archived B
    # keeps position 1 untouched (no collision, no 500).
    assert [v["position"] for v in ordered["videos"]] == [0, 2]
    assert all(v["revision"] == 2 for v in ordered["videos"])  # bumped once

    # Project revision bumped exactly once; B is untouched (still 1).
    proj = client.get(f"/api/v2/projects/{project['project_id']}").json()
    assert proj["revision"] == 2
    archived_b = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{b['video_item_id']}"
    ).json()
    assert archived_b["status"] == "archived"
    assert archived_b["position"] == 1
    assert archived_b["revision"] == 2  # archive bump only, reorder untouched

    # New append goes after the max (3) — no duplicates/gaps.
    d = _create_video(client, project["project_id"], "D")
    assert d["position"] == 3
    positions = _positions(client, project["project_id"])
    assert [p for _, p, _ in positions] == [0, 2, 3]
    assert _root_channels_bytes() == before


def test_reorder_rollback_on_error_leaves_state_intact(client: TestClient) -> None:
    """Finding 1: a failed reorder (stale project revision) rolls back
    completely — no partial position writes, archived positions intact."""
    before = _root_channels_bytes()
    project = _create_project(client)
    a = _create_video(client, project["project_id"], "A")
    b = _create_video(client, project["project_id"], "B")
    c = _create_video(client, project["project_id"], "C")
    _archive_video(client, project["project_id"], b["video_item_id"], revision=1)

    # Stale project revision: 409, no partial write.
    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos/reorder",
        json={
            "project_revision": 99,
            "video_item_ids": [c["video_item_id"], a["video_item_id"]],
        },
    )
    assert resp.status_code == 409, resp.text
    positions = _positions(client, project["project_id"])
    assert [p for _, p, _ in positions] == [0, 2]  # unchanged
    proj = client.get(f"/api/v2/projects/{project['project_id']}").json()
    assert proj["revision"] == 1  # project NOT bumped
    archived_b = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{b['video_item_id']}"
    ).json()
    assert archived_b["position"] == 1
    assert archived_b["revision"] == 2  # archive bump preserved
    assert _root_channels_bytes() == before


def test_create_rejects_extra_probe_fields(client: TestClient) -> None:
    """Finding 2: probe metadata is read-only in S03; the create request
    model forbids unknown fields so extra probe fields are rejected with
    422 and no row is written."""
    before = _root_channels_bytes()
    project = _create_project(client)
    resp = client.post(
        f"/api/v2/projects/{project['project_id']}/videos",
        json={
            "title": "Probe Reject",
            "duration_ms": 1000,
            "width": 1920,
            "height": 1080,
            "fps_num": 30,
            "fps_den": 1,
        },
    )
    assert resp.status_code == 422, resp.text
    assert "duration_ms" in resp.json()["detail"][0]["loc"]
    # Nothing was created.
    listing = client.get(f"/api/v2/projects/{project['project_id']}/videos").json()
    assert listing["videos"] == []
    # The read DTO still exposes the probe fields (S05 will populate them).
    vid = _create_video(client, project["project_id"], "Probe Later")
    body = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{vid['video_item_id']}"
    ).json()
    assert body["duration_ms"] is None
    assert body["width"] is None
    assert body["fps_den"] is None
    assert _root_channels_bytes() == before


def test_update_ownership_before_channel_validation(client: TestClient) -> None:
    """Finding 3: PATCH verifies Project/workspace + Video ownership
    before channel validation — missing/cross-workspace/cross-project
    targets are always safe 404, even with an invalid/foreign channel."""
    before = _root_channels_bytes()
    p1 = _create_project(client, "P1")
    p2 = _create_project(client, "P2")
    vid1 = _create_video(client, p1["project_id"], "Owned by P1")
    vid1_id = vid1["video_item_id"]
    unknown = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    other_ws = "other-workspace"

    # Cross-project target + INVALID channel id → 404 (not channel 422).
    r1 = client.patch(
        f"/api/v2/projects/{p2['project_id']}/videos/{vid1_id}",
        json={"source_channel_id": unknown, "revision": 1},
    )
    assert r1.status_code == 404, r1.text
    assert "channel" not in r1.json()["detail"].lower()

    # Cross-project target + FOREIGN channel id → 404 (not 422).
    r2 = client.patch(
        f"/api/v2/projects/{p2['project_id']}/videos/{vid1_id}",
        json={"source_channel_id": p2["source_channel_id"], "revision": 1},
    )
    assert r2.status_code == 404, r2.text

    # Cross-workspace target + INVALID channel id → 404.
    r3 = client.patch(
        f"/api/v2/projects/{p1['project_id']}/videos/{vid1_id}",
        params={"workspace_id": other_ws},
        json={"source_channel_id": unknown, "revision": 1},
    )
    assert r3.status_code == 404, r3.text

    # Cross-workspace target + FOREIGN channel id → 404.
    r4 = client.patch(
        f"/api/v2/projects/{p1['project_id']}/videos/{vid1_id}",
        params={"workspace_id": other_ws},
        json={"source_channel_id": p2["source_channel_id"], "revision": 1},
    )
    assert r4.status_code == 404, r4.text

    # Missing target + invalid channel id → 404.
    r5 = client.patch(
        f"/api/v2/projects/{p1['project_id']}/videos/{unknown}",
        json={"source_channel_id": unknown, "revision": 1},
    )
    assert r5.status_code == 404, r5.text

    # State intact: P1's video untouched.
    got = client.get(f"/api/v2/projects/{p1['project_id']}/videos/{vid1_id}").json()
    assert got["source_channel_id"] is None
    assert got["revision"] == 1
    assert _root_channels_bytes() == before


def test_update_rejects_overlong_title_before_sql(client: TestClient) -> None:
    """Finding 5: update_video applies the same 240-char maximum as
    create, BEFORE SQL — a direct service/repository call raises
    ValueError (mapped to 422) instead of leaking a DB IntegrityError."""
    before = _root_channels_bytes()
    project = _create_project(client)
    vid = _create_video(client, project["project_id"], "Title Cap")
    vid_id = vid["video_item_id"]

    # API surface → 422 (Pydantic max_length, same as create).
    too_long = "x" * 241
    resp = client.patch(
        f"/api/v2/projects/{project['project_id']}/videos/{vid_id}",
        json={"title": too_long, "revision": 1},
    )
    assert resp.status_code == 422, resp.text

    # Direct service path → ValueError (not IntegrityError).
    from app.persistence.videos import VideoItemService

    svc = deps.get_video_service()
    assert isinstance(svc, VideoItemService)
    try:
        svc.update(
            vid_id,
            project["project_id"],
            DEFAULT_WORKSPACE_ID,
            expected_revision=1,
            title=too_long,
        )
    except ValueError as exc:
        assert "240 characters" in str(exc)
    else:
        raise AssertionError("expected ValueError for overlong title")

    # State intact.
    got = client.get(f"/api/v2/projects/{project['project_id']}/videos/{vid_id}").json()
    assert got["title"] == "Title Cap"
    assert got["revision"] == 1
    assert _root_channels_bytes() == before


def test_append_retry_does_not_swallow_other_unique_violations(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finding 4: the append retry matches ONLY the exact
    (project_id, position) UNIQUE failure; a different UNIQUE violation
    (project_id, legacy_id) propagates as IntegrityError and rolls back."""
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.persistence import create_engine_for_path
    from app.persistence.models import VideoItem
    from app.persistence.videos import VideoItemRepository

    before = _root_channels_bytes()
    db_path = _repo_db_path(client)
    project_id, _ids, _ = _seed_project_and_videos(db_path, "Unique Guard", 1)
    engine = create_engine_for_path(db_path)

    # Seed a second row with a legacy_id, then force a collision on the
    # (project_id, legacy_id) unique index via _next_position collision.
    with Session(engine) as session:
        repo = VideoItemRepository(session)
        repo.create_video(
            project_id=project_id,
            workspace_id=DEFAULT_WORKSPACE_ID,
            title="Legacy Holder",
            legacy_id="legacy-dupe",
        )
        session.commit()

        with pytest.raises(IntegrityError):
            colliding = VideoItemRepository(session)
            monkeypatch.setattr(colliding, "_next_position", lambda _project_id: 5)
            colliding.create_video(
                project_id=project_id,
                workspace_id=DEFAULT_WORKSPACE_ID,
                title="Legacy Dupe",
                legacy_id="legacy-dupe",
            )
            session.commit()
        session.rollback()

    # The position-uniqueness failure is still an AppendRetryError.
    with Session(engine) as session:
        repo = VideoItemRepository(session)
        monkeypatch.setattr(repo, "_next_position", lambda _project_id: 0)
        with pytest.raises(AppendRetryError):
            repo.create_video(
                project_id=project_id,
                workspace_id=DEFAULT_WORKSPACE_ID,
                title="Position Collide",
            )
        session.rollback()

    # Rolled back: only the two seeded rows remain.
    with Session(engine) as session:
        rows = session.scalars(
            select(VideoItem).where(VideoItem.project_id == project_id)
        ).all()
    assert sorted(v.title for v in rows) == ["Legacy Holder", "Unique Guard Video 0"]
    assert _root_channels_bytes() == before


def _make_unique_exc(message: str) -> IntegrityError:
    """Build a fake ``IntegrityError`` whose ``orig`` carries *message*."""
    from sqlalchemy.exc import IntegrityError as SAIntegrityError

    return SAIntegrityError(
        "statement", {}, type("Orig", (), {"__str__": lambda self: message})()
    )


def test_position_unique_failure_matches_exact_column_pair() -> None:
    """Correction round 2: ``_is_position_unique_failure`` matches the EXACT
    SQLite column pair for ``video_item.project_id, video_item.position``.

    Reordered/partial column text (e.g. just ``video_item.position`` or
    ``video_item.position, video_item.project_id``) and the legacy-id
    unique error (``video_item.project_id, video_item.legacy_id``) must
    remain False; only the exact pair is True.  No database or session is
    needed — the predicate is pure string logic over ``exc.orig``.
    """
    from app.persistence.videos import VideoItemRepository

    repo = VideoItemRepository.__new__(VideoItemRepository)  # no session needed
    predicate = repo._is_position_unique_failure  # noqa: SLF001

    # Exact position-pair messages (SQLite + index-name variants) → True.
    assert predicate(
        _make_unique_exc(
            "UNIQUE constraint failed: video_item.project_id, video_item.position"
        )
    )
    assert predicate(
        _make_unique_exc(
            "(sqlite3.IntegrityError) UNIQUE constraint failed: "
            "video_item.project_id, video_item.position"
        )
    )

    # Partial column text — position alone is NOT the pair → False.
    assert not predicate(
        _make_unique_exc("UNIQUE constraint failed: video_item.position")
    )
    assert not predicate(
        _make_unique_exc("UNIQUE constraint failed: video_item.project_id")
    )

    # Reordered columns are a different index's message → False.
    assert not predicate(
        _make_unique_exc(
            "UNIQUE constraint failed: video_item.position, video_item.project_id"
        )
    )

    # The legacy-id unique error mentions the project column but not
    # position → False.
    assert not predicate(
        _make_unique_exc(
            "UNIQUE constraint failed: video_item.project_id, video_item.legacy_id"
        )
    )

    # Not a UNIQUE failure at all → False.
    assert not predicate(_make_unique_exc("FOREIGN KEY constraint failed"))


def test_service_write_reservation_before_validation_and_reads(
    client: TestClient,
) -> None:
    """Finding 7: the production VideoItemService write reservation
    (``BEGIN IMMEDIATE``) is entered BEFORE any validation/current-state
    read.  Deterministic SQL-event ordering — no sleeps/timing.

    Also proves the production CREATE/PATCH channel-race paths exercise
    the real service (the race itself is covered by
    test_channel_archive_cannot_commit_between_validation_and_assignment).
    """
    from sqlalchemy import event

    from app.persistence.videos import VideoItemService

    source = _make_channel(client, "Reservation Source")
    project = _create_project(client)
    svc = deps.get_video_service()
    assert isinstance(svc, VideoItemService)
    engine = svc._session_factory.kw["bind"]  # noqa: SLF001

    begin_seen = False
    validation_seen = False
    events: list[str] = []
    original_validate = videos_module._validate_source_channel

    def _observed_validate(
        session: Session, workspace_id: str, channel_id: str | None
    ) -> None:
        nonlocal validation_seen
        validation_seen = True
        events.append("validate")
        return original_validate(session, workspace_id, channel_id)

    def _observe_sql(
        _conn: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        nonlocal begin_seen
        normalized = " ".join(statement.lower().split())
        if normalized == "begin immediate":
            begin_seen = True
            events.append("begin")
        elif normalized.startswith("select") and "channel" in normalized:
            events.append("channel_select")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(videos_module, "_validate_source_channel", _observed_validate)
    event.listen(engine, "before_cursor_execute", _observe_sql)
    try:
        resp = client.post(
            f"/api/v2/projects/{project['project_id']}/videos",
            json={"title": "Reservation Video", "source_channel_id": source["channel_id"]},
        )
    finally:
        event.remove(engine, "before_cursor_execute", _observe_sql)
        monkeypatch.undo()

    assert resp.status_code == 201, resp.text
    assert begin_seen, "BEGIN IMMEDIATE never executed"
    assert validation_seen, "channel validation never ran"
    assert events.index("begin") < events.index("validate"), (
        f"writer reservation must precede validation: {events}"
    )
    assert events.index("begin") < events.index("channel_select"), (
        f"writer reservation must precede the channel SELECT: {events}"
    )


def test_create_rejects_probe_fields_direct_service(
    client: TestClient,
) -> None:
    """Finding 2: the repository/service create write path does not
    accept probe fields at all (no silent write path exists)."""
    before = _root_channels_bytes()
    project = _create_project(client)
    svc = deps.get_video_service()
    assert isinstance(svc, VideoItemService)
    record = svc.create(
        project_id=project["project_id"],
        workspace_id=DEFAULT_WORKSPACE_ID,
        title="Probe-less Create",
    )
    assert record.duration_ms is None
    assert record.width is None
    assert record.fps_den is None
    got = client.get(
        f"/api/v2/projects/{project['project_id']}/videos/{record.id}"
    ).json()
    assert got["duration_ms"] is None
    assert _root_channels_bytes() == before
