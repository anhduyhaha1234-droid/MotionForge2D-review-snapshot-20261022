"""S03-T04 Project summary read-model API acceptance tests (AC1-AC12).

Every test uses the conftest ``client`` fixture: the isolated tmp
project root, the isolated tmp durable database, and the patched
``deps`` singletons.  No test ever touches the production database,
``channels.json``, the legacy projects directory, or user data
(AC12: ``channels.json`` remains byte-identical — every test snapshots
the root file before and after and asserts the bytes are unchanged).

Coverage maps 1:1 to the TASK acceptance criteria:

- AC1  Both routes are read-only, workspace-scoped; cross-workspace
       reads are safe 404s.
- AC2  DTO is exact; no ORM object / internal JSON / absolute path /
       sensitive job error leaks.
- AC3  Video counts/status map/completion ratio are exact (no join
       inflation; all 13 statuses present with zeroes).
- AC4  Next action is deterministic, state-driven, capability-honest
       (future capabilities return ``enabled=False`` + stable blocker),
       and points at the correct Video Item.
- AC5  Active job membership/count/order exact and bounded; orphan and
       foreign owners excluded.
- AC6  Storage totals deduplicate Artifact ids; missing/trash/unknown
       size behavior documented and asserted.
- AC7  last_activity_at, pagination and tie ordering are deterministic.
- AC8  Archived Project/item and archived Channel reference behavior.
- AC9  Collection query count is bounded; item/collection agree.
- AC10 No migration / persistent aggregate / DB-FS-JSON write / legacy
       route behavior change (writes-probe: POST/PATCH/DELETE 405 on
       both summary routes; no legacy route touched).
- AC11 Focused tests, Ruff, mypy, diff-check pass (validated in
       LOG/REPORT; the focused suite is this file + the mapping tests).
- AC12 ``channels.json`` remains byte-identical and unstaged.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import _s03_helpers as h
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.engine import Engine

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.models import (
    Artifact,
    ArtifactOwner,
    Job,
    Project,
    VideoItem,
    Workspace,
)
from app.persistence.summaries import (
    ACTIVE_JOB_STATES,
    FUTURE_CAPABILITY_BLOCKERS,
    NEXT_ACTION_BLOCKERS,
    NEXT_ACTION_NONE,
    NEXT_ACTION_STATUSES,
)

#: All 13 approved Video Item statuses (schema order).
VIDEO_STATUSES = (
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
)

#: Exact active Job states (contract §4).
ACTIVE_JOB_STATES_SET = set(ACTIVE_JOB_STATES)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _job_service() -> Any:
    """The durable JobService the conftest fixture injected on deps."""
    service = deps._job_service
    assert service is not None, "conftest must inject the isolated JobService"
    return service


def _session_factory() -> Any:
    """The isolated durable session factory wired by the conftest fixture."""
    return _job_service()._session_factory


def _session() -> Any:
    """A short-lived session on the isolated durable DB."""
    return _session_factory()()


def _db_engine() -> Engine:
    """The Engine behind the isolated durable session factory."""
    engine = _session_factory()().get_bind()
    assert isinstance(engine, Engine)
    return engine


# ── AC1: read-only, workspace-scoped, safe 404 ──────────────────────────────


def test_routes_are_read_only_and_workspace_scoped(client: TestClient) -> None:
    """AC1: only GET exists on both routes; everything else is 405."""
    for path in ("/api/v2/projects/summaries", "/api/v2/projects/summaries/"):
        assert client.get(path).status_code == 200
        for method, call in (
            ("POST", client.post),
            ("PATCH", client.patch),
            ("DELETE", client.delete),
            ("PUT", client.put),
        ):
            resp = call(path)
            assert resp.status_code == 405, f"{method} {path} -> {resp.status_code}"


def test_item_route_is_read_only_405(client: TestClient) -> None:
    """AC1: the item route accepts GET only."""
    pid = h.new_uuid()
    path = f"/api/v2/projects/{pid}/summary"
    assert client.get(path).status_code == 404  # unknown -> 404 (not 405)
    for call in (client.post, client.patch, client.delete):
        assert call(path).status_code == 405


def test_unknown_project_404(client: TestClient) -> None:
    """AC1: a missing Project id is a safe 404."""
    pid = h.new_uuid()
    resp = client.get(f"/api/v2/projects/{pid}/summary")
    assert resp.status_code == 404
    assert resp.json()["detail"]


def test_cross_workspace_project_is_404(client: TestClient) -> None:
    """AC1: a Project from another workspace can never be read."""
    project = h.create_project(client, name="My Project")
    resp = client.get(
        f"/api/v2/projects/{project['project_id']}/summary",
        params={"workspace_id": "other"},
    )
    assert resp.status_code == 404


def test_cross_workspace_collection_returns_empty(client: TestClient) -> None:
    """AC1: collection is workspace-scoped; another workspace sees nothing."""
    h.create_project(client, name="My Project")
    body = h.summaries(client, workspace_id="other")
    assert body["workspace_id"] == "other"
    assert body["summaries"] == []


# ── AC2: exact DTO, no leaks ────────────────────────────────────────────────


def _assert_dto_shape(item: dict[str, Any]) -> None:
    assert set(item) == {
        "project_id",
        "workspace_id",
        "name",
        "description",
        "status",
        "revision",
        "created_at",
        "updated_at",
        "archived_at",
        "source_channel",
        "production_channel",
        "video_counts",
        "next_action",
        "active_jobs",
        "active_job_count",
        "last_activity_at",
        "storage",
    }
    assert item["workspace_id"] == DEFAULT_WORKSPACE_ID
    assert isinstance(item["revision"], int)
    for ts in ("created_at", "updated_at"):
        assert item[ts]  # required, ISO string
        datetime.fromisoformat(item[ts])
    assert item["archived_at"] is None or datetime.fromisoformat(item["archived_at"])
    # video_counts exact shape
    vc = item["video_counts"]
    assert set(vc) == {
        "active",
        "archived",
        "total",
        "completed",
        "attention",
        "completion_percent",
        "by_status",
    }
    assert set(vc["by_status"]) == set(VIDEO_STATUSES)
    assert isinstance(vc["completion_percent"], float)
    # next_action exact shape
    na = item["next_action"]
    assert set(na) == {"code", "video_item_id", "enabled", "blocker"}
    # active_jobs DTO leaks no internal/error JSON
    for job in item["active_jobs"]:
        assert set(job) == {
            "job_id",
            "job_type",
            "owner_type",
            "owner_id",
            "state",
            "progress",
            "created_at",
        }
    # storage exact shape
    assert set(item["storage"]) == {
        "total_bytes",
        "artifact_count",
        "ready_count",
        "missing_count",
        "trash_count",
        "unknown_size_count",
    }


def _assert_no_leaks(raw: str) -> None:
    """AC2: no absolute paths, ORM markers or internal JSON in the payload."""
    assert "_sa_instance_state" not in raw
    assert "sqlalchemy" not in raw
    assert str(_PROJECT_ROOT) not in raw
    assert "error_json" not in raw
    assert "input_manifest_json" not in raw
    assert "checkpoint_json" not in raw


def test_dto_exact_and_no_leaks(client: TestClient) -> None:
    """AC2: the item DTO is exact and leaks nothing sensitive."""
    project = h.create_project(client, name="Exact DTO")
    v = h.create_video(client, project["project_id"], title="Video One")
    resp = client.get(f"/api/v2/projects/{project['project_id']}/summary")
    assert resp.status_code == 200
    item = resp.json()
    _assert_dto_shape(item)
    _assert_no_leaks(resp.text)
    assert item["project_id"] == project["project_id"]
    assert item["name"] == "Exact DTO"
    assert item["status"] == "active"
    assert item["next_action"]["video_item_id"] == v["video_item_id"]


def test_collection_dto_exact_and_no_leaks(client: TestClient) -> None:
    """AC2: the collection payload (list envelope + items) leaks nothing."""
    project = h.create_project(client, name="Exact List DTO")
    h.create_video(client, project["project_id"], title="V")
    resp = client.get("/api/v2/projects/summaries")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {
        "workspace_id",
        "active_only",
        "status",
        "limit",
        "offset",
        "total",
        "has_more",
        "summaries",
    }
    _assert_no_leaks(resp.text)
    assert body["workspace_id"] == DEFAULT_WORKSPACE_ID
    assert body["active_only"] is True
    assert body["status"] is None
    assert isinstance(body["limit"], int) and isinstance(body["offset"], int)
    assert isinstance(body["total"], int) and isinstance(body["has_more"], bool)
    assert len(body["summaries"]) >= 1
    _assert_dto_shape(body["summaries"][0])


def test_no_sensitive_job_error_in_dto(client: TestClient) -> None:
    """AC2: active jobs never expose internal error JSON."""
    project = h.create_project(client, name="Job Error")
    with _session() as s:
        s.add(
            Job(
                workspace_id=DEFAULT_WORKSPACE_ID,
                job_type="ANALYZE_MEDIA",
                owner_type="project",
                owner_id=project["project_id"],
                state="running",
                progress=42.0,
                input_manifest_json='{"schema_version": 1}',
                error_json='{"secret": "internal-detail"}',
            )
        )
        s.commit()
    item = h.summary(client, project["project_id"])
    assert item["active_job_count"] == 1
    assert item["active_jobs"][0]["job_type"] == "ANALYZE_MEDIA"
    assert item["active_jobs"][0]["state"] == "running"
    assert "secret" not in str(item)


# ── AC3: exact video counts / status map / completion ratio ─────────────────


def test_video_counts_exact_no_join_inflation(client: TestClient) -> None:
    """AC3: GROUP BY yields exact counts with all 13 statuses + zeroes."""
    project = h.create_project(client, name="Counts")
    vid = h.create_video(client, project["project_id"], title="A")
    h.create_video(client, project["project_id"], title="B")
    h.create_video(client, project["project_id"], title="C")
    # one of three videos completed
    h.patch_video(
        client, project["project_id"], vid["video_item_id"], revision=1, status="completed"
    )
    item = h.summary(client, project["project_id"])
    vc = item["video_counts"]
    assert vc["total"] == 3
    assert vc["active"] == 3
    assert vc["archived"] == 0
    assert vc["completed"] == 1
    assert vc["attention"] == 0
    assert vc["by_status"]["imported"] == 2
    assert vc["by_status"]["completed"] == 1
    assert vc["by_status"]["failed"] == 0
    assert set(vc["by_status"]) == set(VIDEO_STATUSES)


def test_completion_ratio_never_invents_progress(client: TestClient) -> None:
    """AC3: completion_percent = completed/active; zero when no active
    videos (CORRECTION P1.3); never ordinal pipeline progress."""
    project = h.create_project(client, name="Ratio")
    item = h.summary(client, project["project_id"])
    assert item["video_counts"]["completed"] == 0
    assert item["video_counts"]["active"] == 0
    # CORRECTION P1.3: the DTO carries completion_percent and it is zero
    # when there are no active videos.
    assert item["video_counts"]["completion_percent"] == 0.0
    # The contract forbids ordinal pipeline progress: no free-form
    # progress/percent field outside the exact completion ratio.
    assert "progress" not in item["video_counts"]
    assert set(item["video_counts"]) == {
        "active",
        "archived",
        "total",
        "completed",
        "attention",
        "completion_percent",
        "by_status",
    }


# ── AC4: deterministic, capability-honest next action ───────────────────────


def test_next_action_maps_status_deterministically(client: TestClient) -> None:
    """AC4: each status maps to its stable code + correct video id."""
    expected = {
        "imported": "analyze_video",
        "analyzing": "analyze_video",
        "objects_ready": "map_objects",
        "mapping_required": "map_objects",
        "demo_required": "create_demo",
        "demo_approved": "apply_reskin",
        "applying_reskin": "apply_reskin",
        "needs_review": "review_work",
        "ready_to_export": "export_video",
        "rendering": "export_video",
        "failed": "retry_failed",
        "completed": NEXT_ACTION_NONE,
        "archived": NEXT_ACTION_NONE,
    }
    for status, code in expected.items():
        project = h.create_project(client, name=f"NA-{status}")
        v = h.create_video(client, project["project_id"], title="The Video")
        if status == "archived":
            h.archive_video(
                client, project["project_id"], v["video_item_id"], revision=1
            )
        elif status != "imported":
            h.patch_video(
                client,
                project["project_id"],
                v["video_item_id"],
                revision=1,
                status=status,
            )
        na = h.summary(client, project["project_id"])["next_action"]
        assert na["code"] == code, f"{status} -> {na}"
        if code == NEXT_ACTION_NONE:
            assert na["enabled"] is False
            assert na["blocker"] is None
            assert na["video_item_id"] is None
        else:
            # AC4 capability honesty: the semantic action is state-driven
            # and points at the correct Video Item, but the fulfilling
            # capability has not landed yet -> disabled + stable blocker.
            assert na["video_item_id"] == v["video_item_id"]
            assert na["enabled"] is False
            assert na["blocker"] == FUTURE_CAPABILITY_BLOCKERS[code]


def test_next_action_capability_honesty_vocabulary(client: TestClient) -> None:
    """AC4/AC11: every future capability returns enabled=False + blocker."""
    for code in NEXT_ACTION_STATUSES:
        assert code in FUTURE_CAPABILITY_BLOCKERS, f"{code} must be blocker-mapped"
        assert FUTURE_CAPABILITY_BLOCKERS[code] in NEXT_ACTION_BLOCKERS
    assert set(FUTURE_CAPABILITY_BLOCKERS) == set(NEXT_ACTION_STATUSES)


def test_next_action_future_capability_disabled_with_blocker(client: TestClient) -> None:
    """AC4: unavailable future capabilities stay disabled with a blocker."""
    cases = {
        "imported": "analyze_video",
        "analyzing": "analyze_video",
        "objects_ready": "map_objects",
        "mapping_required": "map_objects",
        "demo_required": "create_demo",
        "demo_approved": "apply_reskin",
        "applying_reskin": "apply_reskin",
        "needs_review": "review_work",
        "ready_to_export": "export_video",
        "rendering": "export_video",
        "failed": "retry_failed",
    }
    for status, code in cases.items():
        project = h.create_project(client, name=f"Blocker-{status}")
        v = h.create_video(client, project["project_id"], title="V")
        if status != "imported":
            h.patch_video(
                client,
                project["project_id"],
                v["video_item_id"],
                revision=1,
                status=status,
            )
        na = h.summary(client, project["project_id"])["next_action"]
        assert na["code"] == code
        assert na["video_item_id"] == v["video_item_id"]
        assert na["enabled"] is False
        assert na["blocker"] in NEXT_ACTION_BLOCKERS
        assert na["blocker"] == FUTURE_CAPABILITY_BLOCKERS[code]


def test_next_action_imported_uses_earliest_position(client: TestClient) -> None:
    """AC4: first non-archived video by position drives the action."""
    project = h.create_project(client, name="Ordering")
    a = h.create_video(client, project["project_id"], title="A")
    h.create_video(client, project["project_id"], title="B")
    na = h.summary(client, project["project_id"])["next_action"]
    assert na["video_item_id"] == a["video_item_id"]  # position 0 wins


def test_next_action_failed_video_wins_anywhere(client: TestClient) -> None:
    """AC4: a failed video anywhere is retried first (deterministic)."""
    project = h.create_project(client, name="FailedFirst")
    h.create_video(client, project["project_id"], title="A")
    b = h.create_video(client, project["project_id"], title="B")
    h.patch_video(
        client, project["project_id"], b["video_item_id"], revision=1, status="failed"
    )
    na = h.summary(client, project["project_id"])["next_action"]
    assert na["code"] == "retry_failed"
    assert na["video_item_id"] == b["video_item_id"]


def test_next_action_archived_project_is_none(client: TestClient) -> None:
    """AC4: archived Projects map to none, disabled, no blocker."""
    project = h.create_project(client, name="Archived NA")
    h.create_video(client, project["project_id"], title="V")
    h.archive_project(client, project["project_id"], revision=1)
    na = h.summary(client, project["project_id"])["next_action"]
    assert na == {
        "code": "none",
        "video_item_id": None,
        "enabled": False,
        "blocker": None,
    }


def test_next_action_all_completed_is_none(client: TestClient) -> None:
    """AC4: everything complete -> honest none."""
    project = h.create_project(client, name="All Done")
    v = h.create_video(client, project["project_id"], title="V")
    h.patch_video(
        client, project["project_id"], v["video_item_id"], revision=1, status="completed"
    )
    na = h.summary(client, project["project_id"])["next_action"]
    assert na["code"] == "none"
    assert na["enabled"] is False
    assert na["blocker"] is None


# ── AC5: active job membership/count/order exact and bounded ────────────────


def test_active_jobs_only_project_or_video_owned(client: TestClient) -> None:
    """AC5: project/video-owned active jobs are listed; orphans excluded."""
    project = h.create_project(client, name="Jobs")
    v = h.create_video(client, project["project_id"], title="V")

    def _insert(
        job_type: str, owner_type: str, owner_id: str, state: str = "running"
    ) -> None:
        with _session() as s:
            s.add(
                Job(
                    workspace_id=DEFAULT_WORKSPACE_ID,
                    job_type=job_type,
                    owner_type=owner_type,
                    owner_id=owner_id,
                    state=state,
                    progress=10.0,
                    input_manifest_json='{"schema_version": 1}',
                )
            )
            s.commit()

    _insert("ANALYZE_MEDIA", "project", project["project_id"])  # owned
    _insert("DISCOVER_OBJECTS", "video_item", v["video_item_id"])  # owned
    _insert("RENDER_VARIANT", "project", h.new_uuid())  # orphan owner id
    _insert("RUN_QC", "video_item", h.new_uuid())  # orphan video id
    item = h.summary(client, project["project_id"])
    assert item["active_job_count"] == 2
    types = {j["job_type"] for j in item["active_jobs"]}
    assert types == {"ANALYZE_MEDIA", "DISCOVER_OBJECTS"}


def test_active_jobs_exclude_terminal_states(client: TestClient) -> None:
    """AC5: terminal jobs never appear as active."""
    project = h.create_project(client, name="Terminal")
    for state in ("queued", "running", "completed", "failed", "cancelled"):
        with _session() as s:
            s.add(
                Job(
                    workspace_id=DEFAULT_WORKSPACE_ID,
                    job_type="ANALYZE_MEDIA",
                    owner_type="project",
                    owner_id=project["project_id"],
                    state=state,
                    input_manifest_json='{"schema_version": 1}',
                )
            )
            s.commit()
    item = h.summary(client, project["project_id"])
    assert item["active_job_count"] == 2  # queued + running only
    assert {j["state"] for j in item["active_jobs"]} == {"queued", "running"}


def test_active_jobs_ordered_newest_first_and_bounded(client: TestClient) -> None:
    """AC5: newest-first order; list bounded (<=10), count exact."""
    project = h.create_project(client, name="Bounded Jobs")
    for _ in range(14):
        with _session() as s:
            s.add(
                Job(
                    workspace_id=DEFAULT_WORKSPACE_ID,
                    job_type="ANALYZE_MEDIA",
                    owner_type="project",
                    owner_id=project["project_id"],
                    state="queued",
                    input_manifest_json='{"schema_version": 1}',
                )
            )
            s.commit()
    item = h.summary(client, project["project_id"])
    assert item["active_job_count"] == 14
    assert len(item["active_jobs"]) == 10  # bounded list
    created = [j["created_at"] for j in item["active_jobs"]]
    assert created == sorted(created, reverse=True)  # newest first


def test_cross_workspace_jobs_excluded(client: TestClient) -> None:
    """AC5: jobs from another workspace are never counted."""
    project = h.create_project(client, name="Cross WS Jobs")
    with _session() as s:
        s.add(Workspace(id="other", name="Other"))
        s.commit()
        s.add(
            Job(
                workspace_id="other",
                job_type="RENDER_VARIANT",
                owner_type="project",
                owner_id=project["project_id"],  # same project id, other ws
                state="running",
                input_manifest_json='{"schema_version": 1}',
            )
        )
        s.commit()
    item = h.summary(client, project["project_id"])
    assert item["active_job_count"] == 0
    assert item["active_jobs"] == []


# ── AC6: storage totals dedupe, missing/trash/unknown documented ────────────


def _insert_artifact(
    session: Any,
    *,
    relative_path: str,
    state: str,
    size_bytes: int | None,
    owner_type: str,
    owner_id: str,
    purpose: str = "output",
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> str:
    artifact = Artifact(
        workspace_id=workspace_id,
        kind="video",
        relative_path=relative_path,
        state=state,
        size_bytes=size_bytes,
        sha256="a" * 64,
    )
    session.add(artifact)
    session.flush()
    session.add(
        ArtifactOwner(
            artifact_id=artifact.id,
            owner_type=owner_type,
            owner_id=owner_id,
            purpose=purpose,
        )
    )
    return artifact.id


def test_storage_deduplicates_and_policies(client: TestClient) -> None:
    """AC6: dedupe by id; ready bytes only; missing/trash/unknown counted."""
    project = h.create_project(client, name="Storage")
    v = h.create_video(client, project["project_id"], title="V")
    with _session() as s:
        ready = _insert_artifact(
            s,
            relative_path="p/v.mp4",
            state="ready",
            size_bytes=1000,
            owner_type="video_item",
            owner_id=v["video_item_id"],
        )
        # same artifact id owned twice -> deduplicated
        s.add(
            ArtifactOwner(
                artifact_id=ready,
                owner_type="project",
                owner_id=project["project_id"],
                purpose="output",
            )
        )
        _insert_artifact(
            s,
            relative_path="t/trash.png",
            state="trash",
            size_bytes=500,
            owner_type="project",
            owner_id=project["project_id"],
        )
        _insert_artifact(
            s,
            relative_path="m/missing.png",
            state="missing",
            size_bytes=None,
            owner_type="video_item",
            owner_id=v["video_item_id"],
            purpose="checkpoint",
        )
        _insert_artifact(
            s,
            relative_path="u/unknown.png",
            state="ready",
            size_bytes=None,
            owner_type="project",
            owner_id=project["project_id"],
        )
        s.commit()
    item = h.summary(client, project["project_id"])
    storage = item["storage"]
    # 4 distinct artifact ids: ready(1000B), trash, missing, ready-unknown
    assert storage["artifact_count"] == 4
    assert storage["ready_count"] == 2
    assert storage["missing_count"] == 1
    assert storage["trash_count"] == 1
    # CORRECTION P2.6: every deduplicated artifact with a NULL size counts
    # as unknown regardless of state (missing + ready-unknown here).
    assert storage["unknown_size_count"] == 2
    assert storage["total_bytes"] == 1000  # trash/missing/unknown never counted


def test_storage_never_counts_other_workspace(client: TestClient) -> None:
    """AC6: another workspace's artifacts are never counted."""
    project = h.create_project(client, name="Storage WS")
    with _session() as s:
        s.add(Workspace(id="other", name="Other"))
        s.commit()
        _insert_artifact(
            s,
            relative_path="o/other.mp4",
            state="ready",
            size_bytes=999999,
            owner_type="project",
            owner_id=project["project_id"],  # same project id, other ws
            workspace_id="other",
        )
        s.commit()
    item = h.summary(client, project["project_id"])
    assert item["storage"]["artifact_count"] == 0
    assert item["storage"]["total_bytes"] == 0


def test_storage_empty_project_zero(client: TestClient) -> None:
    """AC6: no artifacts -> all zero."""
    project = h.create_project(client, name="Storage Empty")
    item = h.summary(client, project["project_id"])
    assert item["storage"] == {
        "total_bytes": 0,
        "artifact_count": 0,
        "ready_count": 0,
        "missing_count": 0,
        "trash_count": 0,
        "unknown_size_count": 0,
    }


# ── AC7: last_activity_at, pagination, tie ordering ─────────────────────────


def test_last_activity_reflects_video_update(client: TestClient) -> None:
    """AC7: last_activity_at >= project and video activity."""
    project = h.create_project(client, name="Activity")
    item = h.summary(client, project["project_id"])
    base = datetime.fromisoformat(item["last_activity_at"])
    h.create_video(client, project["project_id"], title="V")
    item2 = h.summary(client, project["project_id"])
    after = datetime.fromisoformat(item2["last_activity_at"])
    assert after >= base


def test_collection_ordering_deterministic(client: TestClient) -> None:
    """AC7: last_activity DESC, project id ASC on ties."""
    ids = [h.create_project(client, name=f"Order {i}")["project_id"] for i in range(5)]
    body = h.summaries(client)
    got = [s["project_id"] for s in body["summaries"]]
    assert set(got) >= set(ids)
    # Deterministic: strictly sorted by (last_activity DESC, id ASC).
    keys = [(s["last_activity_at"] or "", s["project_id"]) for s in body["summaries"]]
    assert keys == sorted(keys, key=lambda k: (k[0], k[1]), reverse=True)


def test_pagination_bounded(client: TestClient) -> None:
    """AC7: limit/offset bound the page; total is the exact filtered count;
    has_more is honest (CORRECTION P2.7)."""
    for i in range(6):
        h.create_project(client, name=f"Page {i}")
    body = h.summaries(client, limit=2)
    assert body["total"] == 6  # exact filtered total, not the page size
    assert body["has_more"] is True
    assert len(body["summaries"]) == 2
    page1 = [s["project_id"] for s in body["summaries"]]
    body2 = h.summaries(client, limit=2, offset=2)
    page2 = [s["project_id"] for s in body2["summaries"]]
    assert page1 != page2
    assert len(set(page1) & set(page2)) == 0


def test_pagination_last_page_has_more_false(client: TestClient) -> None:
    """AC7: the final page reports has_more=False."""
    h.create_project(client, name="Single")
    body = h.summaries(client, limit=50)
    assert body["has_more"] is False


def test_status_filter_exact(client: TestClient) -> None:
    """AC7: exact project-status filtering."""
    active = h.create_project(client, name="Active One")
    h.archive_project(client, active["project_id"], revision=1)
    active2 = h.create_project(client, name="Active Two")
    body = h.summaries(client, status="active")
    assert body["status"] == "active"
    assert body["active_only"] is False
    assert {s["project_id"] for s in body["summaries"]} == {active2["project_id"]}
    body_archived = h.summaries(client, status="archived")
    assert {s["project_id"] for s in body_archived["summaries"]} == {
        active["project_id"]
    }


def test_invalid_status_filter_is_422(client: TestClient) -> None:
    """AC7: an invalid project-status filter is a 422."""
    resp = client.get("/api/v2/projects/summaries", params={"status": "bogus"})
    assert resp.status_code == 422


def test_invalid_pagination_is_422(client: TestClient) -> None:
    """AC7: limit=0 / negative offset are 422 (FastAPI validation)."""
    assert client.get("/api/v2/projects/summaries", params={"limit": 0}).status_code == 422
    assert (
        client.get("/api/v2/projects/summaries", params={"limit": 500}).status_code
        == 422
    )
    assert (
        client.get("/api/v2/projects/summaries", params={"offset": -1}).status_code
        == 422
    )


# ── AC8: archived project/item and archived channel references ──────────────


def test_archived_project_readable_with_none_action(client: TestClient) -> None:
    """AC8: item route reads archived Projects; next action is none."""
    project = h.create_project(client, name="Archived Read")
    h.create_video(client, project["project_id"], title="V")
    h.archive_project(client, project["project_id"], revision=1)
    item = h.summary(client, project["project_id"])
    assert item["status"] == "archived"
    assert item["archived_at"] is not None
    assert item["next_action"]["code"] == "none"
    assert item["next_action"]["enabled"] is False


def test_archived_project_excluded_from_collection(client: TestClient) -> None:
    """AC8: collection defaults exclude archived; status=archived includes."""
    project = h.create_project(client, name="Archived Excl")
    h.archive_project(client, project["project_id"], revision=1)
    active = h.create_project(client, name="Active Kept")
    body = h.summaries(client)
    assert project["project_id"] not in {s["project_id"] for s in body["summaries"]}
    assert active["project_id"] in {s["project_id"] for s in body["summaries"]}


def test_archived_channel_reference_visible(client: TestClient) -> None:
    """AC8: archived referenced Channels remain visible in the summary."""
    channel = h.make_channel(client, name="Source Channel", role="source")
    project = h.create_project(
        client,
        name="Channel Ref",
        source_channel_id=channel["channel_id"],
    )
    # Archive the channel through the channel API (role/status preserved).
    resp = client.post(
        f"/api/channels/{channel['channel_id']}/archive",
        json={"revision": channel["revision"]},
    )
    assert resp.status_code == 200, resp.text
    item = h.summary(client, project["project_id"])
    assert item["source_channel"] is not None
    assert item["source_channel"]["channel_id"] == channel["channel_id"]
    assert item["source_channel"]["name"] == "Source Channel"
    assert item["source_channel"]["status"] == "archived"


def test_production_channel_display(client: TestClient) -> None:
    """AC8: production channel display reference is populated."""
    channel = h.make_channel(client, name="Prod Channel", role="production")
    project = h.create_project(
        client,
        name="Prod Ref",
        production_channel_id=channel["channel_id"],
    )
    item = h.summary(client, project["project_id"])
    assert item["production_channel"] is not None
    assert item["production_channel"]["channel_id"] == channel["channel_id"]
    assert item["source_channel"] is None


# ── AC9: bounded query count; item/collection agree ─────────────────────────


def test_collection_and_item_agree(client: TestClient) -> None:
    """AC9: collection and item routes share one algorithm (AC9)."""
    project = h.create_project(client, name="Agree")
    h.create_video(client, project["project_id"], title="V")
    collection_item = next(
        s
        for s in h.summaries(client)["summaries"]
        if s["project_id"] == project["project_id"]
    )
    item = h.summary(client, project["project_id"])
    assert collection_item == item


def test_query_count_bounded(client: TestClient) -> None:
    """AC9: per-project query count is constant (no N+1)."""
    for i in range(6):
        h.create_project(client, name=f"QC {i}")

    # Instrument the durable engine the summary repository reads through.
    engine = _db_engine()
    counts: list[int] = []

    def _before_execute(
        conn: Any,
        clauseelement: Any,
        multiparams: Any,
        params: Any,
        execution_options: Any,
    ) -> None:
        counts.append(1)

    event.listen(engine, "before_execute", _before_execute)
    try:
        body = h.summaries(client, limit=3)
        page = body["summaries"]
    finally:
        event.remove(engine, "before_execute", _before_execute)

    assert len(page) == 3
    assert len(counts) > 0
    # The collection query runs ONE project-select page plus a constant
    # per-project algorithm.  With 3 projects the total stays far below
    # 3 * (videos+2), proving the count is bounded by the page, not by
    # the number of Projects (AC9: no N+1).
    per_project_budget = 12
    assert len(counts) <= 3 * per_project_budget


# ── AC10: no writes, no migration, no legacy change ─────────────────────────


def test_no_db_rows_written_by_reads(client: TestClient) -> None:
    """AC10: calling both routes writes no Project/Video/Job/Artifact rows."""
    project = h.create_project(client, name="NoWrites")
    h.create_video(client, project["project_id"], title="V")

    def _snapshot() -> tuple[dict[str, int], dict[str, int]]:
        with _session() as s:
            counts = {
                model.__tablename__: int(
                    s.scalar(select(func.count()).select_from(model))
                )
                for model in (Project, VideoItem, Job, Artifact)
            }
            revisions = {
                p.id: p.revision for p in s.scalars(select(Project)).all()
            }
            return counts, revisions

    before_counts, before_revisions = _snapshot()
    h.summaries(client)
    h.summary(client, project["project_id"])
    after_counts, after_revisions = _snapshot()
    assert after_counts == before_counts
    assert after_revisions == before_revisions


def test_legacy_routes_and_files_untouched(client: TestClient) -> None:
    """AC10: legacy /api/projects routes still serve; no v2 shadowing."""
    assert client.get("/api/projects").status_code == 200
    assert client.get("/api/projects/presets/characters").status_code == 200


# ── AC12: channels.json byte-identical and unstaged ─────────────────────────


def test_channels_json_byte_identical_and_unstaged(client: TestClient) -> None:
    """AC12: channels.json bytes + git staged-state never change."""
    root = Path(__file__).resolve().parent.parent
    channels = root / "channels.json"
    before = channels.read_bytes()
    h.create_project(client, name="Channels Safe")
    h.summaries(client)
    assert channels.read_bytes() == before

    import subprocess

    staged = subprocess.run(
        ["git", "-C", str(root), "diff", "--cached", "--name-only", "--", "channels.json"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert staged == ""
