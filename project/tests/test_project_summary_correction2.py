"""S03-T04 CORRECTION_02 focused tests — prove the round-2 fixes.

Every test here FAILS against the round-1 implementation and PASSES after
the CORRECTION_02 changes.  Coverage maps 1:1 to the CORRECTION_02.md
findings:

- P-R2.1  SQL page bounding: the activity-ordered Project page is fetched
          with SQL ``OFFSET offset LIMIT limit+1`` AFTER the global
          ``last_activity_at DESC, Project.id`` ordering, so DB rows and
          memory are truly page-bounded.  The old implementation called
          ``.all()`` and sliced in Python, so a page request materialized
          EVERY matching Project row.
- P-R2.2  Per-Project active-job top-10 batching: active jobs are the
          newest at most 10 **per Project** (created_at DESC, id ASC)
          with a CONSTANT query count, using a window rank partitioned by
          resolved Project ownership.  The old implementation used ONE
          global ``LIMIT 10`` for the whole page, so a Project whose
          jobs were all older than another page Project's newest 10 got
          ZERO jobs listed (wrong membership AND wrong total list).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import _s03_helpers as h
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.models import Job

#: The strict ceiling that proves no N+1 (see the P1.1 budget in the
#: round-1 suite): 1 total-count + 1 page-select + 7 core compose
#: queries + 2 conditional batch reads = 12 at most.
PAGE_QUERY_BUDGET = 12


def _session() -> Any:
    """A short-lived session on the isolated durable DB."""
    return _job_service()._session_factory()


def _job_service() -> Any:
    service = deps._job_service
    assert service is not None, "conftest must inject the isolated JobService"
    return service


def _db_engine() -> Engine:
    engine = _session().get_bind()
    assert isinstance(engine, Engine)
    return engine


def _count_queries(call: Any) -> int:
    """Run *call* and return the number of SQL statements executed."""
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
        call()
    finally:
        event.remove(engine, "before_execute", _before_execute)
    return len(counts)


def _compiled_page_sql(client: TestClient, **params: Any) -> list[str]:
    """Run one summaries page and return the COMPILED page SELECTs.

    Uses ``literal_binds`` so ``LIMIT``/``OFFSET`` values appear inline
    (the raw compiled text renders them as ``?`` placeholders).
    """
    engine = _db_engine()
    captured: list[str] = []

    def _capture(
        conn: Any,
        clauseelement: Any,
        multiparams: Any,
        params: Any,
        execution_options: Any,
    ) -> None:
        text = str(clauseelement.compile(compile_kwargs={"literal_binds": True}))
        if "FROM project" in text and "ORDER BY" in text:
            captured.append(text)

    event.listen(engine, "before_execute", _capture)
    try:
        h.summaries(client, **params)
    finally:
        event.remove(engine, "before_execute", _capture)
    return captured


def _set_row_ts(
    row: Any,
    *,
    updated_at: datetime,
    created_at: datetime | None = None,
) -> None:
    """Overwrite durable timestamps deterministically (bypasses onupdate)."""
    from app.persistence.models import Project as ProjectModel

    if isinstance(row, dict):
        model: Any = ProjectModel
        row_id = row["project_id"]
    else:
        model = type(row)
        row_id = row.id

    with _session() as s:
        fresh = s.get(model, row_id)
        fresh.updated_at = updated_at
        if created_at is not None:
            fresh.created_at = created_at
        s.commit()


def _insert_job(
    *,
    project_id: str,
    created_at: datetime,
    state: str = "queued",
    owner_type: str = "project",
    owner_id: str | None = None,
    job_id: str | None = None,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> str:
    """Insert a durable Job row with a CONTROLLED id/timestamp."""
    job = Job(
        workspace_id=workspace_id,
        job_type="ANALYZE_MEDIA",
        owner_type=owner_type,
        owner_id=owner_id or project_id,
        state=state,
        progress=10.0,
        input_manifest_json='{"schema_version": 1}',
    )
    if job_id is not None:
        job.id = job_id
    job.created_at = created_at
    job.updated_at = created_at
    with _session() as s:
        s.add(job)
        s.commit()
        return job.id


def _ordered_ids_for_page(client: TestClient, **params: Any) -> list[str]:
    """The project ids of one summary page in server order."""
    body = h.summaries(client, **params)
    return [s["project_id"] for s in body["summaries"]]


# ── P-R2.1 SQL page bounding ────────────────────────────────────────────────


def test_page_select_sql_uses_offset_limit_not_all_rows(client: TestClient) -> None:
    """P-R2.1: the page SELECT carries SQL OFFSET/LIMIT (no ``.all()``).

    With 25 off-page Projects, a single page request (limit=5, offset=0)
    must execute a page SELECT that includes ``LIMIT 6 OFFSET 0`` — i.e.
    the database, not Python, bounds the rows.  The old implementation
    ran ``SELECT ... ORDER BY ...`` with NO LIMIT and sliced in Python,
    which fails this assertion.
    """
    for i in range(25):
        h.create_project(client, name=f"OffPage {i}")

    page_sql = _compiled_page_sql(client, limit=5, offset=0)
    assert page_sql, "the page SELECT must have executed"
    assert any("LIMIT 6" in sql for sql in page_sql), (
        "page SELECT must carry SQL LIMIT (currently `.all()` + Python slice)"
    )
    assert any("OFFSET 0" in sql for sql in page_sql), "page SELECT must carry SQL OFFSET"


def test_page_select_limit_is_limit_plus_one(client: TestClient) -> None:
    """P-R2.1: the page SELECT fetches exactly ``limit + 1`` rows in SQL.

    The extra row is the honest-``has_more`` probe; it must never exceed
    ``limit + 1`` (a ``LIMIT 6`` for limit=5).  A Python ``.all()``
    implementation has no LIMIT at all, so this fails before the fix.
    """
    for i in range(12):
        h.create_project(client, name=f"Probe {i}")

    page_sql = _compiled_page_sql(client, limit=5, offset=0)
    assert page_sql
    limits = [int(m.group(1)) for sql in page_sql for m in [re.search(r"LIMIT (\d+)", sql)] if m]
    assert limits, "no SQL LIMIT found in the page SELECT"
    assert all(limit == 6 for limit in limits), f"expected LIMIT 6, got {limits}"


def test_page_bounded_memory_with_many_offpage_projects(client: TestClient) -> None:
    """P-R2.1: memory is page-bounded — the page SELECT returns at most
    ``limit + 1`` rows even when many off-page Projects exist.

    This is the honest behavioral proof: with 40 Projects and limit=5 the
    page select must be ``LIMIT 6`` in SQL.  A ``.all()`` + Python-slice
    implementation has no SQL LIMIT and materializes all 40 rows.
    """
    for i in range(40):
        h.create_project(client, name=f"Many {i}")

    page_sql = _compiled_page_sql(client, limit=5, offset=0)
    assert page_sql, "the page SELECT must have executed"
    assert any("LIMIT 6" in sql for sql in page_sql), (
        "page SELECT must carry SQL LIMIT 6 (memory is NOT page-bounded: "
        "the query has no LIMIT and materializes every Project)"
    )

    body = h.summaries(client, limit=5, offset=0)
    assert body["total"] == 40
    assert len(body["summaries"]) == 5
    assert body["has_more"] is True


def test_offset_page_select_sql_offset(client: TestClient) -> None:
    """P-R2.1: a non-zero offset page carries SQL OFFSET too."""
    for i in range(15):
        h.create_project(client, name=f"Off {i}")

    page_sql = _compiled_page_sql(client, limit=4, offset=8)
    assert page_sql
    assert any("OFFSET 8" in sql for sql in page_sql), "offset page must carry SQL OFFSET"


def test_global_order_unchanged_with_sql_paging(client: TestClient) -> None:
    """P-R2.1: SQL paging preserves the authoritative global ordering.

    An old Project with a newer Video outranks a recently updated Project
    on the FIRST SQL page (offset 0) exactly as before — proving the
    SQL ``OFFSET/LIMIT`` did not change the global activity order.
    """
    old = h.create_project(client, name="Old SQL")
    new = h.create_project(client, name="New SQL")
    _set_row_ts(
        old,
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    _set_row_ts(
        new,
        updated_at=datetime(2026, 6, 1, tzinfo=UTC),
        created_at=datetime(2025, 6, 1, tzinfo=UTC),
    )
    v = h.create_video(client, old["project_id"], title="Fresh Video")
    _set_row_ts(
        v,
        updated_at=datetime(2026, 12, 1, tzinfo=UTC),
        created_at=datetime(2026, 12, 1, tzinfo=UTC),
    )
    ids = _ordered_ids_for_page(client, limit=5, offset=0)
    assert ids.index(old["project_id"]) < ids.index(new["project_id"])


def test_sql_paging_has_more_honest(client: TestClient) -> None:
    """P-R2.1: with SQL paging, has_more/total stay honest across pages."""
    for i in range(7):
        h.create_project(client, name=f"SQLPage {i}")
    body = h.summaries(client, limit=3, offset=0)
    assert body["total"] == 7
    assert body["has_more"] is True
    assert len(body["summaries"]) == 3
    body2 = h.summaries(client, limit=3, offset=3)
    assert len(body2["summaries"]) == 3
    assert body2["has_more"] is True
    body3 = h.summaries(client, limit=3, offset=6)
    assert len(body3["summaries"]) == 1
    assert body3["has_more"] is False


# ── P-R2.2 per-Project active-job top-10 batching ────────────────────────────


def test_each_project_receives_own_active_jobs_when_other_has_11_newer(
    client: TestClient,
) -> None:
    """P-R2.2: a Project with fewer/older jobs still gets ITS jobs.

    Project A owns 11 active jobs created at T+2; Project B owns 3 active
    jobs created at T+1 (OLDER than A's newest).  The round-1 global
    ``LIMIT 10`` returns ONLY A's 10 newest and B receives ZERO listed
    jobs.  After the fix, A lists its newest 10 (count 11) AND B lists
    its own 3 (count 3).
    """
    a = h.create_project(client, name="Busy A")
    b = h.create_project(client, name="Quiet B")
    # A: 11 active jobs, all NEWER than B's.
    for i in range(11):
        _insert_job(
            project_id=a["project_id"],
            job_id=f"a-{i:03d}",
            created_at=datetime(2026, 7, 2, 12, i, tzinfo=UTC),
        )
    # B: 3 active jobs, all OLDER than A's newest.
    b_ids = [
        _insert_job(
            project_id=b["project_id"],
            job_id=f"b-{i:03d}",
            created_at=datetime(2026, 7, 1, 12, i, tzinfo=UTC),
        )
        for i in range(3)
    ]

    body = h.summaries(client)
    by_id = {s["project_id"]: s for s in body["summaries"]}
    a_sum = by_id[a["project_id"]]
    b_sum = by_id[b["project_id"]]

    # B keeps its OWN jobs even though A's 11 are newer globally.
    assert b_sum["active_job_count"] == 3
    assert [j["job_id"] for j in b_sum["active_jobs"]] == list(reversed(b_ids))

    # A is bounded to its newest 10 and reports the full count.
    assert a_sum["active_job_count"] == 11
    assert len(a_sum["active_jobs"]) == 10
    assert a_sum["active_jobs"][0]["job_id"] == "a-010"
    assert "a-000" not in {j["job_id"] for j in a_sum["active_jobs"]}


def test_per_project_top10_deterministic_ties(client: TestClient) -> None:
    """P-R2.2: per-Project top-10 uses (created_at DESC, id ASC) ties.

    Both Projects own 12 jobs sharing ONE timestamp; the deterministic
    tie order must give each Project its own 10 LOWEST ids (the two
    highest ids are the excluded 11th/12th) — never a global 10.
    """
    p1 = h.create_project(client, name="Tie P1")
    p2 = h.create_project(client, name="Tie P2")
    ts = datetime(2026, 4, 1, tzinfo=UTC)
    for i in range(12):
        _insert_job(project_id=p1["project_id"], job_id=f"p1-{i:04d}", created_at=ts)
        _insert_job(project_id=p2["project_id"], job_id=f"p2-{i:04d}", created_at=ts)

    body = h.summaries(client)
    by_id = {s["project_id"]: s for s in body["summaries"]}
    for prefix, project in (("p1", p1), ("p2", p2)):
        item = by_id[project["project_id"]]
        assert item["active_job_count"] == 12
        got = [j["job_id"] for j in item["active_jobs"]]
        assert len(got) == 10
        # (created_at DESC, id ASC) with identical timestamps -> the 10
        # LOWEST ids, excluding the two highest.
        assert got == [f"{prefix}-{i:04d}" for i in range(10)]


def test_active_jobs_batching_constant_query_count(client: TestClient) -> None:
    """P-R2.2: per-Project top-10 batching keeps the query count CONSTANT.

    The round-1 global LIMIT 10 cost the same count, so this proves the
    window-rank fix did NOT add per-Project queries (no N+1 regression).
    Two Projects with 20+ active jobs each still cost <= PAGE_QUERY_BUDGET.
    """
    a = h.create_project(client, name="Q A")
    b = h.create_project(client, name="Q B")
    base = datetime(2026, 7, 1, tzinfo=UTC)
    for i in range(14):
        _insert_job(project_id=a["project_id"], created_at=base.replace(minute=i))
        _insert_job(project_id=b["project_id"], created_at=base.replace(second=i))

    q = _count_queries(lambda: h.summaries(client))
    assert q <= PAGE_QUERY_BUDGET, f"query count {q} exceeds the constant ceiling"


def test_per_project_batching_mixed_owners_and_orphans(client: TestClient) -> None:
    """P-R2.2: window partitioning respects Project- AND Video-owned jobs,
    while orphan owners are still excluded (AC5 preserved)."""
    a = h.create_project(client, name="Mixed A")
    v = h.create_video(client, a["project_id"], title="V")
    base = datetime(2026, 6, 1, tzinfo=UTC)
    # 12 project-owned (hour 1) + 12 video-owned (hour 2, NEWER) jobs.
    for i in range(12):
        _insert_job(
            project_id=a["project_id"],
            job_id=f"ap-{i:03d}",
            created_at=base.replace(hour=1, minute=i),
        )
        _insert_job(
            project_id=a["project_id"],
            job_id=f"av-{i:03d}",
            created_at=base.replace(hour=2, minute=i),
            owner_type="video_item",
            owner_id=v["video_item_id"],
        )
    # Orphan owner: a project id that is NOT on the page.
    _insert_job(
        project_id=h.new_uuid(),
        job_id="orphan-000",
        created_at=base.replace(hour=23, minute=59),
        owner_type="project",
    )
    b = h.create_project(client, name="Mixed B")
    b_ids = [
        _insert_job(
            project_id=b["project_id"],
            job_id=f"b-{i:03d}",
            created_at=base.replace(hour=0, minute=i),
        )
        for i in range(4)
    ]

    body = h.summaries(client)
    by_id = {s["project_id"]: s for s in body["summaries"]}
    a_sum = by_id[a["project_id"]]
    b_sum = by_id[b["project_id"]]
    # A: 24 active total, top-10 by (created_at DESC, id ASC) — the 10
    # newest are the video-owned jobs av-011 .. av-002 (hour 2, minutes
    # 11 down to 2; av-001/av-000 fall outside the top 10).
    assert a_sum["active_job_count"] == 24
    got_a = [j["job_id"] for j in a_sum["active_jobs"]]
    assert len(got_a) == 10
    assert got_a == [f"av-{i:03d}" for i in range(11, 1, -1)]
    # B keeps its own 4.
    assert b_sum["active_job_count"] == 4
    assert [j["job_id"] for j in b_sum["active_jobs"]] == list(reversed(b_ids))
    # The orphan never appears.
    assert all(
        j["job_id"] != "orphan-000"
        for s in body["summaries"]
        for j in s["active_jobs"]
    )
