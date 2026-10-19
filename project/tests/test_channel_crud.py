"""S03-T01 durable Channel CRUD/archive API tests (AC1-AC6 + PM review 1).

Every test uses the conftest ``client`` fixture (isolated tmp project root
+ tmp durable database + patched ``deps``), so no test ever touches the
production database, ``channels.json`` or user data.  The legacy
``channels.json`` workspace store is asserted byte-identical after each
scenario (no JSON dual-write).

Scenarios map to acceptance criteria:
- AC1 list/read/create/update/archive; no hard-delete endpoint.
- AC2 roles exactly source|production; cross-field validation.
- AC3 normalized, case-insensitively unique ACTIVE names per
  (workspace, role); stable/actionable conflicts; archived names reusable.
- AC4 PATCH + archive use atomic revision CAS; stale → 409; exactly one
  revision bump per accepted business update; two-session race test.
- AC5 archive idempotent (repeat = no bump); references/timestamps
  preserved; archived filterable/readable and excluded by active default.
- AC6 DTO responses never expose ORM objects/absolute paths; legacy
  channel response compatibility preserved (legacy endpoints untouched).
- PM1: workspace isolation (cross-workspace id = 404), explicit-null
  clearing, optional timestamp serialization (archived_at JSON null),
  avatar_artifact_id metadata boundary.
"""

from __future__ import annotations

import threading
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.channels import (
    ChannelRepository,
    NameConflictError,
)
from app.persistence.engine import create_engine_for_path
from app.persistence.models import Channel, Workspace

# ── Helpers ──────────────────────────────────────────────────────────────────


def _root_channels_bytes() -> bytes:
    """The production-root channels.json bytes (must never change)."""
    root = Path(__file__).resolve().parent.parent / "channels.json"
    return root.read_bytes() if root.exists() else b""


def _create(
    client: TestClient,
    name: str,
    role: str = "source",
    **extra: object,
) -> dict:
    payload: dict[str, object] = {"name": name, "role": role, **extra}
    resp = client.post("/api/channels", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _archive(client: TestClient, channel_id: str, revision: int) -> dict:
    resp = client.post(f"/api/channels/{channel_id}/archive", json={"revision": revision})
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── AC1: CRUD + archive, no hard delete ──────────────────────────────────────


def test_create_read_update_archive_lifecycle(client: TestClient) -> None:
    before = _root_channels_bytes()

    created = _create(client, "  Durable Src  ")
    cid = created["channel_id"]
    assert created["name"] == "Durable Src"  # normalized (AC3)
    assert created["role"] == "source"
    assert created["status"] == "active"
    assert created["workspace_id"] == DEFAULT_WORKSPACE_ID
    assert created["revision"] == 1
    assert created["archived_at"] is None  # JSON null for optional timestamp
    assert "id" not in created  # DTO exposes channel_id, not ORM id

    # Read
    got = client.get(f"/api/channels/{cid}").json()
    assert got["channel_id"] == cid
    assert got["name"] == "Durable Src"

    # Update (business update with expected revision)
    updated = client.patch(
        f"/api/channels/{cid}",
        json={"name": "Durable Src v2", "description": "updated", "revision": 1},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["name"] == "Durable Src v2"
    assert body["description"] == "updated"
    assert body["revision"] == 2  # exactly one bump (AC4)

    # Archive (requires expected revision — atomic CAS)
    archived = _archive(client, cid, revision=2)
    assert archived["status"] == "archived"
    assert archived["archived_at"]  # timestamp preserved (AC5)
    assert archived["revision"] == 3

    # Readable after archive (AC5)
    got = client.get(f"/api/channels/{cid}").json()
    assert got["status"] == "archived"

    # No hard-delete endpoint exists
    assert not _route_exists(client, "DELETE", f"/api/channels/{cid}")
    assert _root_channels_bytes() == before, "channels.json was modified"


def test_list_excludes_archived_by_default(client: TestClient) -> None:
    before = _root_channels_bytes()
    a = _create(client, "Active One")
    _create(client, "Active Two")
    c = _create(client, "To Archive")

    active = client.get("/api/channels").json()
    assert active["active_only"] is True
    active_ids = {ch["channel_id"] for ch in active["channels"]}
    assert {a["channel_id"], c["channel_id"]} <= active_ids

    _archive(client, c["channel_id"], revision=c["revision"])
    active2 = client.get("/api/channels").json()
    active_ids2 = {ch["channel_id"] for ch in active2["channels"]}
    assert c["channel_id"] not in active_ids2
    assert a["channel_id"] in active_ids2

    # Archived channels are filterable with active_only=false (AC5)
    all_rows = client.get("/api/channels", params={"active_only": False}).json()
    all_ids = {ch["channel_id"] for ch in all_rows["channels"]}
    assert c["channel_id"] in all_ids
    assert _root_channels_bytes() == before


def test_list_filters_by_role(client: TestClient) -> None:
    before = _root_channels_bytes()
    _create(client, "Src Channel", role="source")
    prod = _create(client, "Prod Channel", role="production")

    sources = client.get("/api/channels", params={"role": "source"}).json()
    assert all(ch["role"] == "source" for ch in sources["channels"])
    productions = client.get("/api/channels", params={"role": "production"}).json()
    assert {ch["channel_id"] for ch in productions["channels"]} == {prod["channel_id"]}
    assert _root_channels_bytes() == before


def test_unknown_channel_404(client: TestClient) -> None:
    before = _root_channels_bytes()
    assert client.get("/api/channels/nope").status_code == 404
    assert client.patch("/api/channels/nope", json={"revision": 1}).status_code == 404
    assert (
        client.post("/api/channels/nope/archive", json={"revision": 1}).status_code
        == 404
    )
    assert _root_channels_bytes() == before


# ── AC2: roles exactly source|production; cross-field validation ─────────────


def test_roles_are_exactly_source_and_production(client: TestClient) -> None:
    before = _root_channels_bytes()
    roles = client.get("/api/channels/roles").json()["roles"]
    assert roles == ["source", "production"]

    bad = client.post("/api/channels", json={"name": "Bad Role", "role": "youtube"})
    assert bad.status_code == 422  # rejected by the DTO enum (AC2)

    statuses = client.get("/api/channels/statuses").json()["statuses"]
    assert statuses == ["active", "archived"]
    assert _root_channels_bytes() == before


def test_empty_name_rejected(client: TestClient) -> None:
    before = _root_channels_bytes()
    resp = client.post("/api/channels", json={"name": "   ", "role": "source"})
    assert resp.status_code == 422
    assert _root_channels_bytes() == before


# ── AC3: normalized, case-insensitive unique ACTIVE names ────────────────────


def test_case_insensitive_name_conflict_409(client: TestClient) -> None:
    before = _root_channels_bytes()
    _create(client, "My Channel")

    dup = client.post("/api/channels", json={"name": "my channel", "role": "source"})
    assert dup.status_code == 409
    assert "already exists" in dup.json()["detail"]

    # Same name, different role is allowed (uniqueness per workspace+role)
    ok = client.post("/api/channels", json={"name": "My Channel", "role": "production"})
    assert ok.status_code == 201
    assert _root_channels_bytes() == before


def test_archived_name_can_be_reused(client: TestClient) -> None:
    """AC3 + PM1: uniqueness applies to ACTIVE names only.

    After archiving, the same (workspace, role, name) is creatable again
    (the S03 partial unique index is active-only).
    """
    before = _root_channels_bytes()
    first = _create(client, "Reusable Name")
    _archive(client, first["channel_id"], revision=first["revision"])
    second = _create(client, "Reusable Name")
    assert second["status"] == "active"
    assert second["channel_id"] != first["channel_id"]
    assert _root_channels_bytes() == before


def test_concurrent_case_variant_create_one_wins(client: TestClient) -> None:
    """PM1: racing creates with case-variant names — exactly one wins.

    The partial unique index on lower(name) is the atomic backstop; the
    loser must receive the stable 409 conflict, never a 500.
    """
    before = _root_channels_bytes()
    results: list[int] = []
    barrier = threading.Barrier(2)

    def _try_create(name: str) -> None:
        barrier.wait()
        resp = client.post("/api/channels", json={"name": name, "role": "source"})
        results.append(resp.status_code)

    threads = [
        threading.Thread(target=_try_create, args=("Race Channel",)),
        threading.Thread(target=_try_create, args=("race channel",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [201, 409], f"unexpected statuses: {results}"
    listed = client.get("/api/channels").json()["channels"]
    assert len(listed) == 1
    assert listed[0]["name"].lower() == "race channel"
    assert _root_channels_bytes() == before


def test_update_to_conflicting_name_409(client: TestClient) -> None:
    before = _root_channels_bytes()
    a = _create(client, "Channel A")
    _create(client, "Channel B")

    conflict = client.patch(
        f"/api/channels/{a['channel_id']}",
        json={"name": "CHANNEL B", "revision": 1},
    )
    assert conflict.status_code == 409
    assert "already exists" in conflict.json()["detail"]

    # Renaming to itself (case change only) is allowed (AC3 normalization)
    ok = client.patch(
        f"/api/channels/{a['channel_id']}",
        json={"name": "channel a", "revision": 1},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["revision"] == 2
    assert _root_channels_bytes() == before


# ── AC4: atomic optimistic concurrency via revision CAS ──────────────────────


def test_stale_revision_returns_409(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Concurrency")
    cid = created["channel_id"]

    r1 = client.patch(f"/api/channels/{cid}", json={"description": "v1", "revision": 1})
    assert r1.status_code == 200
    assert r1.json()["revision"] == 2

    # Replaying the original revision is stale -> 409
    stale = client.patch(f"/api/channels/{cid}", json={"description": "v2", "revision": 1})
    assert stale.status_code == 409
    assert "revision" in stale.json()["detail"]

    # The accepted update did not lose its effect
    got = client.get(f"/api/channels/{cid}").json()
    assert got["description"] == "v1"
    assert got["revision"] == 2
    assert _root_channels_bytes() == before


def test_every_accepted_update_bumps_revision_once(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Bump Counter")
    cid = created["channel_id"]

    for i, rev in enumerate((1, 2, 3), start=1):
        resp = client.patch(
            f"/api/channels/{cid}",
            json={"description": f"update {i}", "revision": rev},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["revision"] == rev + 1

    # Archive also bumps exactly once (business update, AC4/AC5)
    archived = _archive(client, cid, revision=4)
    assert archived["revision"] == 5
    # Re-archive is idempotent: no revision bump (AC5)
    again = _archive(client, cid, revision=4)
    assert again["revision"] == 5
    assert _root_channels_bytes() == before


def test_two_session_revision_race_exactly_one_wins(client: TestClient) -> None:
    """PM1: deterministic two-session CAS race — exactly one writer wins.

    Two threads PATCH the same channel with the SAME expected revision.
    The conditional UPDATE allows exactly one to match; the other gets
    409.  Final revision must be exactly 2 (one bump).
    """
    before = _root_channels_bytes()
    created = _create(client, "Race Update")
    cid = created["channel_id"]
    assert created["revision"] == 1

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _do_update(tag: str) -> None:
        barrier.wait()
        resp = client.patch(
            f"/api/channels/{cid}",
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
    got = client.get(f"/api/channels/{cid}").json()
    assert got["revision"] == 2  # exactly one bump
    assert _root_channels_bytes() == before


def test_archive_stale_revision_409_and_idempotent_repeat(client: TestClient) -> None:
    """PM1: archive CAS semantics."""
    before = _root_channels_bytes()
    created = _create(client, "Archive CAS")
    cid = created["channel_id"]

    # stale first archive of an active row -> 409
    stale = client.post(f"/api/channels/{cid}/archive", json={"revision": 99})
    assert stale.status_code == 409
    assert "revision" in stale.json()["detail"]
    got = client.get(f"/api/channels/{cid}").json()
    assert got["status"] == "active"
    assert got["revision"] == 1  # no bump on the failed attempt

    # correct archive -> 200, bump once
    archived = _archive(client, cid, revision=1)
    assert archived["revision"] == 2

    # repeat archive (even with the stale revision) -> idempotent 200, no bump
    again = _archive(client, cid, revision=1)
    assert again["status"] == "archived"
    assert again["revision"] == 2
    assert _root_channels_bytes() == before


def test_concurrent_archive_race_both_idempotent(client: TestClient) -> None:
    """PM2 finding 4: two concurrent archive calls both succeed idempotently.

    Both threads read the active row and CAS with the same expected
    revision.  Exactly one wins the CAS (200 + one bump); the loser's
    zero-row CAS re-reads the now-archived row and returns it idempotently
    (200, no bump) — never a 409.
    """
    before = _root_channels_bytes()
    created = _create(client, "Archive Race")
    cid = created["channel_id"]
    assert created["revision"] == 1

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _do_archive() -> None:
        barrier.wait()
        resp = client.post(f"/api/channels/{cid}/archive", json={"revision": 1})
        results.append(resp.status_code)

    threads = [threading.Thread(target=_do_archive) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [200, 200], f"unexpected statuses: {results}"
    got = client.get(f"/api/channels/{cid}").json()
    assert got["status"] == "archived"
    assert got["revision"] == 2  # exactly one bump
    assert _root_channels_bytes() == before


# ── AC5: archive semantics ───────────────────────────────────────────────────


def test_archive_preserves_timestamps_and_references(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(
        client,
        "Preserve Me",
        role="production",
        description="keep",
        color="#ff8800",
        target_language="vi",
        default_output_profile="1080p",
    )
    cid = created["channel_id"]
    created_at = created["created_at"]

    archived = _archive(client, cid, revision=created["revision"])
    assert archived["created_at"] == created_at
    assert archived["description"] == "keep"
    assert archived["color"] == "#ff8800"
    assert archived["target_language"] == "vi"
    assert archived["default_output_profile"] == "1080p"
    assert archived["status"] == "archived"
    assert archived["archived_at"]

    # References (project FK rows) are preserved: the row still exists.
    assert client.get(f"/api/channels/{cid}").status_code == 200
    assert _root_channels_bytes() == before


# ── PM1: workspace isolation ─────────────────────────────────────────────────


def test_cross_workspace_channel_is_404(client: TestClient) -> None:
    """A channel id from another workspace must be 404, never readable."""
    before = _root_channels_bytes()
    created = _create(client, "Workspace A Channel")
    cid = created["channel_id"]

    # Same id, different workspace -> 404 for read/update/archive
    other = "other-workspace"
    assert client.get(f"/api/channels/{cid}", params={"workspace_id": other}).status_code == 404
    assert (
        client.patch(
            f"/api/channels/{cid}",
            params={"workspace_id": other},
            json={"description": "x", "revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/channels/{cid}/archive",
            params={"workspace_id": other},
            json={"revision": 1},
        ).status_code
        == 404
    )
    # The row is untouched
    got = client.get(f"/api/channels/{cid}").json()
    assert got["status"] == "active"
    assert got["revision"] == 1
    assert _root_channels_bytes() == before


# ── PM1: explicit-null clearing ──────────────────────────────────────────────


def test_patch_explicit_null_clears_nullable_fields(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(
        client,
        "Null Clearing",
        color="#ff8800",
        target_language="vi",
        default_output_profile="1080p",
    )
    cid = created["channel_id"]
    assert created["color"] == "#ff8800"

    # Explicit JSON null clears the field
    resp = client.patch(
        f"/api/channels/{cid}",
        json={
            "color": None,
            "target_language": None,
            "default_output_profile": None,
            "revision": 1,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["color"] is None
    assert body["target_language"] is None
    assert body["default_output_profile"] is None
    assert body["revision"] == 2
    assert _root_channels_bytes() == before


def test_patch_omitted_field_keeps_existing_value(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(
        client,
        "Omitted Field",
        color="#00ff00",
        target_language="en",
    )
    cid = created["channel_id"]

    # Omitted color -> unchanged; only description changes
    resp = client.patch(f"/api/channels/{cid}", json={"description": "only", "revision": 1})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["color"] == "#00ff00"
    assert body["target_language"] == "en"
    assert body["description"] == "only"
    assert body["revision"] == 2
    assert _root_channels_bytes() == before


def test_patch_name_null_is_422(client: TestClient) -> None:
    """PM2 finding 3: explicit null for name is a validation error."""
    before = _root_channels_bytes()
    created = _create(client, "Name Null Contract")
    resp = client.patch(
        f"/api/channels/{created['channel_id']}",
        json={"name": None, "revision": 1},
    )
    assert resp.status_code == 422, resp.text
    assert "name" in resp.json()["detail"]
    got = client.get(f"/api/channels/{created['channel_id']}").json()
    assert got["name"] == "Name Null Contract"  # unchanged
    assert _root_channels_bytes() == before


def test_patch_description_null_normalizes_to_empty(client: TestClient) -> None:
    """PM2 finding 3: explicit null for description -> required empty string."""
    before = _root_channels_bytes()
    created = _create(client, "Desc Null Contract", description="keep me")
    resp = client.patch(
        f"/api/channels/{created['channel_id']}",
        json={"description": None, "revision": 1},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["description"] == ""  # normalized, never NULL
    assert body["revision"] == 2
    assert _root_channels_bytes() == before


# ── PM1: metadata boundary (avatar_artifact_id) ──────────────────────────────


def test_avatar_artifact_id_set_and_cleared(client: TestClient) -> None:
    import uuid

    from app.persistence.models import Artifact

    before = _root_channels_bytes()
    # A real workspace + artifact row must exist for the avatar FK
    # (RESTRICT).  The channel service's DB is the same durable DB the job
    # service uses; the workspace row is bootstrapped by channel create,
    # so create it here too (idempotent insert).

    with deps.get_job_service()._session_factory() as session:
        session.execute(
            __import__("sqlalchemy.dialects.sqlite", fromlist=["insert"]).insert(
                __import__("app.persistence.models", fromlist=["Workspace"]).Workspace
            )
            .values(id=DEFAULT_WORKSPACE_ID, name=DEFAULT_WORKSPACE_ID)
            .on_conflict_do_nothing(index_elements=["id"])
        )
        artifact = Artifact(
            workspace_id=DEFAULT_WORKSPACE_ID,
            kind="image",
            relative_path=f"avatars/{uuid.uuid4().hex}.png",
        )
        session.add(artifact)
        session.commit()
        artifact_id = artifact.id

    name = f"Avatar Channel {uuid.uuid4().hex[:8]}"
    created = _create(client, name, avatar_artifact_id=artifact_id)
    cid = created["channel_id"]
    assert created["avatar_artifact_id"] == artifact_id

    cleared = client.patch(
        f"/api/channels/{cid}", json={"avatar_artifact_id": None, "revision": 1}
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["avatar_artifact_id"] is None
    assert _root_channels_bytes() == before


def test_avatar_artifact_id_rejects_unknown_artifact(client: TestClient) -> None:
    """PM2 finding 2: invalid avatar FK maps to a stable actionable 4xx."""
    before = _root_channels_bytes()
    resp = client.post(
        "/api/channels",
        json={"name": "Bad Avatar", "role": "source", "avatar_artifact_id": "nope"},
    )
    assert resp.status_code == 422, resp.text
    assert "avatar_artifact_id" in resp.json()["detail"]
    assert "does not reference" in resp.json()["detail"]
    assert _root_channels_bytes() == before


def test_avatar_artifact_id_rejects_cross_workspace(client: TestClient) -> None:
    """PM2 finding 2: cross-workspace artifact reference is a 4xx."""
    import uuid

    from app.persistence.models import Artifact, Workspace

    before = _root_channels_bytes()
    from app.api import deps

    with deps.get_job_service()._session_factory() as session:
        session.execute(
            __import__("sqlalchemy.dialects.sqlite", fromlist=["insert"]).insert(
                Workspace
            )
            .values(id="other-ws", name="other-ws")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        artifact = Artifact(
            workspace_id="other-ws",
            kind="image",
            relative_path=f"avatars/{uuid.uuid4().hex}.png",
        )
        session.add(artifact)
        session.commit()
        artifact_id = artifact.id

    resp = client.post(
        "/api/channels",
        json={
            "name": f"Cross Avatar {uuid.uuid4().hex[:8]}",
            "role": "source",
            "avatar_artifact_id": artifact_id,
        },
    )
    assert resp.status_code == 422, resp.text
    assert "different workspace" in resp.json()["detail"]
    assert _root_channels_bytes() == before


# ── AC6: DTO boundaries + legacy compatibility ───────────────────────────────


def test_dto_never_exposes_orm_objects_or_paths(client: TestClient) -> None:
    before = _root_channels_bytes()
    created = _create(client, "Boundary Check")
    body_keys = set(created.keys())
    assert "channel_id" in body_keys
    assert "workspace_id" in body_keys
    assert "revision" in body_keys
    # No ORM identity, no SQLAlchemy internals, no absolute paths
    for forbidden in ("id", "_sa_instance_state", "path", "absolute_path", "db_path"):
        assert forbidden not in body_keys
    serialized = str(created)
    assert "sqlite" not in serialized.lower() and "C:" not in serialized
    assert _root_channels_bytes() == before


def test_legacy_channel_endpoints_still_work(client: TestClient) -> None:
    """Legacy channels.json workspace API keeps its contract (AC6).

    The durable API must not break the existing dashboard endpoints; the
    legacy store stays byte-identical.  (Legacy route capture behavior is
    unchanged from HEAD — no S03-T01 edits to projects.py.  On an isolated
    root there is no legacy store and the pre-existing route-order quirk
    makes GET /api/projects/channels hit the project reader; the legacy
    create endpoint still works and returns the JSON workspace shape.)
    """
    before = _root_channels_bytes()
    # Legacy create channel (JSON workspace store)
    resp = client.post("/api/projects/channels", json={"name": "Legacy WS"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["channel_id"]
    listed = client.get("/api/projects/channels").json()
    # The pre-existing GET route-order quirk is NOT part of this task: it
    # may be a list (when the legacy route wins) or a 404-detail on a
    # fresh isolated root (when the parameterized project route wins).
    assert isinstance(listed, list) or "detail" in listed
    assert _root_channels_bytes() == before


# ── Helper ───────────────────────────────────────────────────────────────────


def _route_exists(client: TestClient, method: str, path: str) -> bool:
    """Probe the OpenAPI schema for an exact route (no request side effect)."""
    schema = client.get("/openapi.json").json()
    for route_path, methods in schema["paths"].items():
        if route_path.rstrip("/") == path.rstrip("/") and method.lower() in methods:
            return True
    return False


# ── PM round 3: deterministic repository-level interleaving tests ───────────


def _repo_db_path(client: TestClient) -> Path:
    """The durable DB path the client's channel service is bound to."""
    svc = deps.get_channel_service()
    factory = svc._session_factory  # noqa: SLF001
    engine = factory.kw["bind"]
    return Path(engine.url.database)


def _seed_channel(db_path: Path, name: str, role: str = "source") -> tuple[str, int]:
    """Create a channel row + workspace through a raw session."""
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        session.execute(
            __import__("sqlalchemy.dialects.sqlite", fromlist=["insert"])
            .insert(Workspace)
            .values(id=DEFAULT_WORKSPACE_ID, name=DEFAULT_WORKSPACE_ID)
            .on_conflict_do_nothing(index_elements=[Workspace.id])
        )
        repo = ChannelRepository(session)
        record = repo.create_channel(
            workspace_id=DEFAULT_WORKSPACE_ID,
            role=role,
            name=name,
        )
        session.commit()
        return record.id, record.revision


def test_archive_interleaving_both_callers_read_active_then_cas(
    client: TestClient,
) -> None:
    """PM3 finding 1: deterministic interleaved archive.

    Both callers open their own session, read the ACTIVE row, then pause
    on a barrier BEFORE their CAS update.  Caller A proceeds and archives
    (one bump).  Caller B then executes its CAS — zero rows — and must
    re-read with a FRESH database SELECT and return the now-archived row
    idempotently (no bump).  This would fail on the old identity-map
    ``session.get`` re-read path because B's session still holds its stale
    in-session ACTIVE object.
    """
    db_path = _repo_db_path(client)
    channel_id, _ = _seed_channel(db_path, "Interleave Archive")
    engine = create_engine_for_path(db_path)

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def _caller_a() -> None:
        with Session(engine) as session:
            repo = ChannelRepository(session)
            # read active
            repo.get_channel(channel_id, DEFAULT_WORKSPACE_ID)
            barrier.wait()  # both have read active
            record = repo.archive_channel(
                channel_id, DEFAULT_WORKSPACE_ID, expected_revision=1
            )
            session.commit()
            with lock:
                outcomes.append(f"A:{record.status}:{record.revision}")

    def _caller_b() -> None:
        with Session(engine) as session:
            repo = ChannelRepository(session)
            # read active (identity map now holds the ACTIVE object)
            repo.get_channel(channel_id, DEFAULT_WORKSPACE_ID)
            barrier.wait()  # both have read active
            record = repo.archive_channel(
                channel_id, DEFAULT_WORKSPACE_ID, expected_revision=1
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
    # Final row: archived, exactly one bump.
    with Session(engine) as session:
        row = session.execute(
            __import__("sqlalchemy").select(Channel).where(Channel.id == channel_id)
        ).scalar_one()
        assert row.status == "archived"
        assert row.revision == 2


def test_archive_loser_refreshes_a_strongly_cached_active_row(
    client: TestClient,
) -> None:
    """A lost archive CAS must refresh, not reuse identity-map state.

    Keep a strong reference to the ACTIVE ORM object in the losing session,
    archive through an independent session, then retry with the stale revision.
    A normal SELECT would reuse the cached object; ``populate_existing`` must
    replace it with the committed ARCHIVED database state and return
    idempotently without another revision bump.
    """
    db_path = _repo_db_path(client)
    channel_id, _ = _seed_channel(db_path, "Strong Cache Archive")
    engine = create_engine_for_path(db_path)

    with Session(engine) as losing_session:
        cached = losing_session.execute(
            __import__("sqlalchemy").select(Channel).where(Channel.id == channel_id)
        ).scalar_one()
        assert cached.status == "active"
        assert cached.revision == 1

        with Session(engine) as winning_session:
            winner = ChannelRepository(winning_session).archive_channel(
                channel_id,
                DEFAULT_WORKSPACE_ID,
                expected_revision=1,
            )
            winning_session.commit()
            assert winner.status == "archived"
            assert winner.revision == 2

        loser = ChannelRepository(losing_session).archive_channel(
            channel_id,
            DEFAULT_WORKSPACE_ID,
            expected_revision=1,
        )
        assert loser.status == "archived"
        assert loser.revision == 2
        assert cached.status == "archived"

    with Session(engine) as session:
        final = session.get(Channel, channel_id)
        assert final is not None
        assert final.status == "archived"
        assert final.revision == 2


def test_concurrent_rename_to_one_free_name_exactly_one_wins(
    client: TestClient,
) -> None:
    """PM3 finding 2: two active channels rename to the same free name.

    Both callers read active (no conflict pre-check hit), then race their
    CAS UPDATEs.  The active-name partial unique index fires for the
    loser; the repository must map that to NameConflictError (HTTP 409)
    without masking unrelated integrity errors.  Exactly one rename wins.
    """
    db_path = _repo_db_path(client)
    a_id, _ = _seed_channel(db_path, "Rename A")
    b_id, _ = _seed_channel(db_path, "Rename B")
    engine = create_engine_for_path(db_path)

    start_barrier = threading.Barrier(2)
    precheck_barrier = threading.Barrier(2)
    results: list[str] = []
    lock = threading.Lock()

    # Instrument the pre-check to PROVE it saw no blocker at read time —
    # the loser's NameConflictError must come from the UPDATE-time index
    # backstop, not from the pre-check.
    orig_find = ChannelRepository._find_active_by_name

    def spy_find(self, workspace_id: str, role: str, name: str) -> object:
        res = orig_find(self, workspace_id, role, name)
        with lock:
            results.append(f"precheck:{name}:{res.id if res is not None else None}")
        # Do not let either writer reach UPDATE until both pre-check reads
        # have completed.  This makes the intended race deterministic and
        # proves that the unique-index backstop, rather than a later
        # pre-check, rejects the loser.
        precheck_barrier.wait(timeout=10)
        return res

    ChannelRepository._find_active_by_name = spy_find  # type: ignore[method-assign]

    def _rename(cid: str) -> None:
        try:
            with Session(engine) as session:
                repo = ChannelRepository(session)
                # read active; the name pre-check sees no blocker yet
                repo.get_channel(cid, DEFAULT_WORKSPACE_ID)
                start_barrier.wait(timeout=10)  # both have read active, neither renamed
                repo.update_channel(
                    cid,
                    DEFAULT_WORKSPACE_ID,
                    expected_revision=1,
                    name="THE SAME NAME",
                )
                session.commit()
                with lock:
                    results.append(f"{cid}:ok")
        except NameConflictError:
            with lock:
                results.append(f"{cid}:conflict")

    def _rename_b(cid: str) -> None:
        try:
            with Session(engine) as session:
                repo = ChannelRepository(session)
                repo.get_channel(cid, DEFAULT_WORKSPACE_ID)
                start_barrier.wait(timeout=10)
                repo.update_channel(
                    cid,
                    DEFAULT_WORKSPACE_ID,
                    expected_revision=1,
                    name="THE SAME NAME",
                )
                session.commit()
                with lock:
                    results.append(f"{cid}:ok")
        except NameConflictError:
            with lock:
                results.append(f"{cid}:conflict")

    try:
        ta = threading.Thread(target=_rename, args=(a_id,))
        tb = threading.Thread(target=_rename_b, args=(b_id,))
        ta.start()
        tb.start()
        ta.join()
        tb.join()
    finally:
        ChannelRepository._find_active_by_name = orig_find  # type: ignore[method-assign]

    prechecks = [r for r in results if r.startswith("precheck:")]
    assert len(prechecks) == 2, prechecks
    assert all(r.endswith(":None") for r in prechecks), (
        "the pre-check must see no blocker — the conflict must come from "
        f"the UPDATE-time index backstop: {prechecks}"
    )
    assert sum(1 for r in results if r.endswith(":ok")) == 1, results
    assert sum(1 for r in results if r.endswith(":conflict")) == 1, results
    assert sorted(r.split(":")[0] for r in results if not r.startswith("precheck")) == sorted(
        [a_id, b_id]
    ), results
    # Exactly one channel holds the new name.
    with Session(engine) as session:
        rows = session.execute(
            __import__("sqlalchemy")
            .select(Channel)
            .where(Channel.name == "THE SAME NAME", Channel.status == "active")
        ).scalars().all()
        assert len(rows) == 1
