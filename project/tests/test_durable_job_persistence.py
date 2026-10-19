"""Targeted tests for S02-T02 — durable job schema and lifecycle repository.

Covers AC1-AC6 of ``docs/pm/sessions/S02-T02-job-persistence/TASK.md``:

- AC1: the forward migration creates Job, JobStep, JobAttempt, JobEvent and
  JobLease with contract constraints/FKs/indexes, and matches the ORM.
- AC2: upgrade from the S01 revision preserves existing rows; fresh upgrade
  and database reopen work; downgrade refuses (never assumed as recovery).
- AC3: the repository creates jobs/steps atomically and enforces one active
  or completed Job per ``(workspace_id, idempotency_key)`` while a terminal
  failed/cancelled retry creates exactly one linked successor.
- AC4: guarded state transitions validate allowed endpoints, revisions and
  fence tokens; every accepted transition appends a JobEvent in one tx.
- AC5: attempt accounting, progress/checkpoint/error envelopes and lease
  acquire/heartbeat/release persist with bounded transactional behavior.
- AC6: no worker/API cutover or dual-write; targeted tests 7/7 PASS.

Every test uses a temporary database under ``tmp_path`` — never a database
under production project/user data.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence import (
    FENCED_WORKER_ERROR_CODE,
    IDEMPOTENCY_KEY_IN_USE_CODE,
    INVALID_STATE_TRANSITION_CODE,
    LEASE_CONFLICT_CODE,
    FencedWorkerError,
    IdempotencyKeyInUse,
    InvalidStateTransition,
    JobAlreadyTerminalError,
    JobError,
    JobNotFoundError,
    JobRepository,
    JobStepCreationError,
    LeaseConflictError,
    StepInput,
    create_engine_for_path,
    create_session_factory,
)
from app.persistence.models import (
    Job,
    JobAttempt,
    JobEvent,
    JobLease,
    JobStep,
    Workspace,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"
S01_REVISION = "a1b2c3d4e5f6"
JOB_HEAD_REVISION = "23b308b1fd0b"
# NOTE (PM review round 3): do NOT hard-code later heads here.  The
# durable-job tests resolve the current Alembic head dynamically and prove
# JOB_HEAD_REVISION is an ancestor of it, so future migrations cannot
# break these tests.


# ── Helpers ──────────────────────────────────────────────────────────────────


def _alembic_config(database_path: Path) -> Config:
    """Build an Alembic Config pointed at a temporary database."""
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return cfg


def _upgrade(database_path: Path, revision: str) -> None:
    """Run ``alembic upgrade <revision>`` against the temporary database."""
    command.upgrade(_alembic_config(database_path), revision)


def _downgrade(database_path: Path, revision: str) -> None:
    """Run ``alembic downgrade <revision>`` (used only to prove refusal)."""
    command.downgrade(_alembic_config(database_path), revision)


def _insert_s01_rows(session: Session) -> Workspace:
    """Insert a minimal S01 workspace row (and return it)."""
    ws = Workspace(name="S01 Workspace")
    session.add(ws)
    session.commit()
    return ws


def _make_ws(session: Session, name: str = "Job Workspace") -> Workspace:
    ws = Workspace(name=name)
    session.add(ws)
    session.commit()
    return ws


def _steps(*codes: str, depends: dict[str, tuple[str, ...]] | None = None) -> list[StepInput]:
    """Build a step plan of sequential steps, optionally with dependencies."""
    depends = depends or {}
    return [
        StepInput(
            step_code=code,
            position=i,
            depends_on=tuple(depends.get(code, ())),
        )
        for i, code in enumerate(codes)
    ]


def _create_job(
    repo: JobRepository,
    ws: Workspace,
    *,
    key: str | None = "RENDER_VARIANT:v1",
    generation: str | None = "g1",
    state: str = "queued",
    steps: list[StepInput] | None = None,
) -> object:
    return repo.create_job(
        workspace_id=ws.id,
        job_type="RENDER_VARIANT",
        owner_type="project",
        owner_id="owner-1",
        input_manifest={"source_artifact_id": "art-1", "variant": "v1"},
        idempotency_key=key,
        input_generation=generation,
        state=state,
        steps=steps or _steps("probe", "render"),
    )


def _lease(repo: JobRepository, job_id: str, worker: str = "worker-a") -> object:
    return repo.acquire_lease(job_id, worker, ttl_seconds=60)


def _run_job_until_running(
    repo: JobRepository, session: Session, job_id: str
) -> object:
    """Transition a job to running and return its current lease."""
    lease = _lease(repo, job_id)
    repo.transition_job(
        job_id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    return lease


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """A fresh temporary database path per test (file must not exist yet)."""
    return tmp_path / "test_jobs.db"


@pytest.fixture()
def upgraded_db(db_path: Path) -> Iterator[Path]:
    """A temp database upgraded to the S02 head by Alembic."""
    _upgrade(db_path, "head")
    yield db_path


@pytest.fixture()
def session_factory(upgraded_db: Path):
    """Session factory bound to the upgraded temp database."""
    return create_session_factory(create_engine_for_path(upgraded_db))


@pytest.fixture()
def session(session_factory) -> Iterator[Session]:
    """A session bound to the upgraded temp database."""
    with session_factory() as s:
        yield s


@pytest.fixture()
def repo(session: Session) -> JobRepository:
    """Repository over the fixture session."""
    return JobRepository(session)


@pytest.fixture()
def ws(session: Session) -> Workspace:
    """A workspace row committed in the fixture session."""
    return _make_ws(session)


# ── AC1: migration schema ────────────────────────────────────────────────────


def test_migration_creates_all_five_job_tables(upgraded_db: Path) -> None:
    """AC1: the forward migration creates the five job tables."""
    engine = create_engine_for_path(upgraded_db)
    tables = set(inspect(engine).get_table_names())
    expected = {
        "job",
        "job_step",
        "job_attempt",
        "job_event",
        "job_lease",
    }
    assert expected <= tables, f"missing job tables: {expected - tables}"


def test_migration_has_contract_constraints(upgraded_db: Path) -> None:
    """AC1: contract constraints/FKs/indexes exist on the job tables."""
    engine = create_engine_for_path(upgraded_db)
    inspector = inspect(engine)

    job_pk = inspector.get_pk_constraint("job")
    assert job_pk["constrained_columns"] == ["id"]

    # Unique: per-workspace idempotency key + generation (partial unique
    # index over non-NULL keys of non-terminal rows, contract §8.1/§8.5),
    # one successor per predecessor.
    job_indexes = {ix["name"]: ix for ix in inspector.get_indexes("job")}
    key_index = job_indexes.get("uq_job_idempotency_key")
    assert key_index is not None
    assert bool(key_index["unique"]) is True
    assert key_index["column_names"] == [
        "workspace_id",
        "idempotency_key",
        "input_generation",
    ]
    # The partial index covers only active/completed rows: terminal
    # failed/cancelled predecessors keep their full audit identity and may
    # be succeeded by a Job reusing the same key.
    with engine.connect() as conn:
        ddl = conn.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name='uq_job_idempotency_key'"
        ).scalar()
    assert ddl is not None and "state NOT IN ('failed','cancelled')" in ddl

    job_uniques = {tuple(u["column_names"]) for u in inspector.get_unique_constraints("job")}
    assert ("predecessor_job_id",) in job_uniques

    # Check constraints include state machine and revision guards.
    job_checks = {ck["name"] for ck in inspector.get_check_constraints("job")}
    assert "ck_job_state" in job_checks
    assert "ck_job_revision_positive" in job_checks
    assert "ck_job_priority_range" in job_checks

    step_uniques = {
        tuple(u["column_names"]) for u in inspector.get_unique_constraints("job_step")
    }
    assert ("job_id", "step_code") in step_uniques
    assert ("job_id", "position") in step_uniques

    attempt_uniques = {
        tuple(u["column_names"]) for u in inspector.get_unique_constraints("job_attempt")
    }
    assert ("job_id", "step_id", "attempt") in attempt_uniques
    assert ("job_id", "step_code", "attempt") in attempt_uniques

    # FKs to job (RESTRICT).
    job_fks = {tuple(fk["constrained_columns"]) for fk in inspector.get_foreign_keys("job_step")}
    assert ("job_id",) in job_fks

    lease_pk = inspector.get_pk_constraint("job_lease")
    assert lease_pk["constrained_columns"] == ["job_id"]


def test_orm_matches_migrated_schema(upgraded_db: Path) -> None:
    """AC1: ORM models reflect exactly the migrated job tables."""
    engine = create_engine_for_path(upgraded_db)
    orm_tables = {Job.__tablename__, JobStep.__tablename__, JobAttempt.__tablename__,
                  JobEvent.__tablename__, JobLease.__tablename__}
    db_tables = {
        "job",
        "job_step",
        "job_attempt",
        "job_event",
        "job_lease",
    }
    assert orm_tables == db_tables
    # Every ORM table exists in the migrated database.
    inspector = inspect(engine)
    migrated = set(inspector.get_table_names())
    assert orm_tables <= migrated


def test_head_revision_is_durable_job_schema(upgraded_db: Path) -> None:
    """AC1: the head revision includes the S02 job migration.

    Future-safe (PM review round 3 finding 3): resolve the Alembic
    CURRENT head dynamically instead of hard-coding S03 as the permanent
    head; prove the S02 job revision is an ancestor of whatever the head
    is today, so adding later migrations cannot break this test.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory(str(PROJECT_ROOT / "migrations"))
    current_head = script.get_current_head()
    assert current_head is not None

    engine = create_engine_for_path(upgraded_db)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    # The database is upgraded to the current head...
    assert version == current_head
    # ...and the S02 job revision is an ancestor of that head.
    ancestors = {rev.revision for rev in script.walk_revisions(base=JOB_HEAD_REVISION)}
    assert JOB_HEAD_REVISION in ancestors
    assert current_head in ancestors


# ── AC2: migration safety ────────────────────────────────────────────────────


def test_upgrade_from_s01_preserves_existing_rows(db_path: Path) -> None:
    """AC2: upgrading from the S01 revision preserves existing rows."""
    _upgrade(db_path, S01_REVISION)
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        ws = _insert_s01_rows(session)
        ws_id = ws.id

    _upgrade(db_path, "head")
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        loaded = session.get(Workspace, ws_id)
        assert loaded is not None
        assert loaded.name == "S01 Workspace"
        tables = set(inspect(engine).get_table_names())
        assert "job" in tables and "job_lease" in tables


def test_fresh_upgrade_and_reopen(db_path: Path) -> None:
    """AC2: fresh upgrade to head works; data survives reopen."""
    _upgrade(db_path, "head")
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        ws = _make_ws(session, "Reopen Workspace")
        repo = JobRepository(session)
        created = repo.create_job(
            workspace_id=ws.id,
            job_type="RUN_QC",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={"x": 1},
            idempotency_key="RUN_QC:v1",
            steps=_steps("qc"),
        )
        session.commit()
        job_id = created.id

    # Reopen with a brand-new engine/connection.
    engine2 = create_engine_for_path(db_path)
    with Session(engine2) as session2:
        repo2 = JobRepository(session2)
        loaded = repo2.get_job(job_id)
        assert loaded.job_type == "RUN_QC"
        assert loaded.idempotency_key == "RUN_QC:v1"
        assert loaded.state == "queued"
        steps = repo2.list_steps(job_id)
        assert [s.step_code for s in steps] == ["qc"]


def test_downgrade_is_refused(db_path: Path) -> None:
    """AC2: downgrade is not assumed as recovery — the migration refuses."""
    _upgrade(db_path, "head")
    with pytest.raises(RuntimeError, match="not reversible"):
        _downgrade(db_path, S01_REVISION)


def test_no_worker_or_api_cutover_tables(upgraded_db: Path) -> None:
    """AC6: no worker/API cutover tables or dual-write artifacts."""
    engine = create_engine_for_path(upgraded_db)
    tables = set(inspect(engine).get_table_names())
    unexpected = tables - {
        "workspace",
        "channel",
        "project",
        "video_item",
        "scene",
        "artifact",
        "artifact_owner",
        "legacy_import",
        "alembic_version",
        "job",
        "job_step",
        "job_attempt",
        "job_event",
        "job_lease",
        "character",
        "character_pack_version",
        "character_asset",
    }
    assert not unexpected, f"unexpected tables: {sorted(unexpected)}"


# ── AC3: atomic creation and idempotency ─────────────────────────────────────


def test_create_job_with_steps_is_atomic(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: Job + steps + created event are written in one transaction."""
    created = _create_job(repo, ws)
    session.commit()
    assert created.state == "queued"
    assert created.revision == 1

    steps = repo.list_steps(created.id)
    assert [s.step_code for s in steps] == ["probe", "render"]
    assert all(s.state == "pending" for s in steps)
    events = repo.list_events(created.id)
    assert len(events) == 1
    assert events[0].event_type == "created"
    assert events[0].to_state == "queued"
    assert events[0].revision == 1


def test_failed_step_plan_rolls_back_job(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: an invalid step plan fails atomically — no Job row is written."""
    with pytest.raises(JobStepCreationError):
        repo.create_job(
            workspace_id=ws.id,
            job_type="RENDER_VARIANT",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={},
            idempotency_key="bad-plan",
            steps=_steps("a", "a"),  # duplicate step_code
        )
    session.rollback()
    assert repo.list_jobs(ws.id) == []


def test_duplicate_active_key_rejected(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: a second active Job with the same key is rejected with 409 code."""
    _create_job(repo, ws, key="K:v1")
    session.commit()
    with pytest.raises(IdempotencyKeyInUse) as excinfo:
        _create_job(repo, ws, key="K:v1")
    assert excinfo.value.code == IDEMPOTENCY_KEY_IN_USE_CODE
    session.rollback()
    assert len(repo.list_jobs(ws.id)) == 1


def test_duplicate_completed_key_returns_existing(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: a duplicate key for a completed Job returns the existing Job."""
    created = _create_job(repo, ws, key="K:done")
    lease = _lease(repo, created.id)
    repo.transition_job(
        created.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        created.id, "completed", actor="worker", expected_revision=3, fence_token=lease.fence_token
    )
    session.commit()

    duplicate = _create_job(repo, ws, key="K:done")
    assert duplicate.id == created.id
    assert duplicate.state == "completed"


def test_same_key_other_workspace_allowed(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: the same idempotency key in another workspace is independent."""
    _create_job(repo, ws, key="SHARED:v1")
    session.commit()
    ws2 = _make_ws(session, "Other Workspace")
    other = _create_job(repo, ws2, key="SHARED:v1")
    assert other.id is not None and other.workspace_id == ws2.id


def test_successor_after_failed_creates_linked_job(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: retry of a terminal failed Job creates exactly one successor."""
    failed = _create_job(repo, ws, key="RETRY:v1")
    lease = _lease(repo, failed.id)
    repo.transition_job(
        failed.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        failed.id,
        "failed",
        actor="worker",
        expected_revision=3,
        fence_token=lease.fence_token,
        error={"error_code": "INPUT_MISSING", "message": "boom"},
    )
    session.commit()

    successor = repo.create_successor(predecessor_job_id=failed.id, input_manifest={})
    assert successor.id != failed.id
    assert successor.predecessor_job_id == failed.id
    assert successor.idempotency_key == "RETRY:v1"
    assert successor.state == "queued"
    session.commit()

    # Exactly one successor per predecessor; a second retry is rejected
    # because the key now belongs to an active Job.
    with pytest.raises(IdempotencyKeyInUse):
        repo.create_successor(predecessor_job_id=failed.id, input_manifest={})
    session.rollback()

    successors = [
        j
        for j in repo.list_jobs(ws.id)
        if j.predecessor_job_id == failed.id
    ]
    assert len(successors) == 1


def test_successor_preserves_predecessor_identity(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """PM correction regression: successor creation mutates nothing on the
    terminal predecessor (contract §4.5-4/§6.4).

    The failed/cancelled predecessor retains its idempotency key, input
    generation, manifest, timestamps, error envelope and revision — it is
    never rewritten, keyed NULL, or otherwise modified.  The successor gets a
    fresh id, reuses the same key AND generation, and carries the link.
    """
    failed = _create_job(repo, ws, key="IMMUTABLE:v1", generation="gen-7")
    lease = _lease(repo, failed.id)
    repo.transition_job(
        failed.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        failed.id,
        "failed",
        actor="worker",
        expected_revision=3,
        fence_token=lease.fence_token,
        error={"error_code": "INPUT_MISSING", "message": "boom"},
    )
    session.commit()

    before = repo.get_job(failed.id)
    successor = repo.create_successor(predecessor_job_id=failed.id, input_manifest={"x": 2})
    session.commit()
    after = repo.get_job(failed.id)

    # Predecessor row is bit-for-bit unchanged on every field we can read.
    assert after.id == before.id
    assert after.workspace_id == before.workspace_id
    assert after.job_type == before.job_type
    assert after.owner_type == before.owner_type
    assert after.owner_id == before.owner_id
    assert after.parent_job_id == before.parent_job_id
    assert after.predecessor_job_id == before.predecessor_job_id
    assert after.state == before.state == "failed"
    assert after.resource_class == before.resource_class
    assert after.priority == before.priority
    assert after.max_attempts == before.max_attempts
    assert after.attempt == before.attempt
    # PM correction: the key AND generation stay on the predecessor.
    assert after.idempotency_key == before.idempotency_key == "IMMUTABLE:v1"
    assert after.input_generation == before.input_generation == "gen-7"
    assert after.input_manifest == before.input_manifest
    assert after.progress == before.progress
    assert after.error == before.error
    assert after.created_at == before.created_at
    assert after.updated_at == before.updated_at
    assert after.started_at == before.started_at
    assert after.finished_at == before.finished_at
    assert after.revision == before.revision == 4

    # The successor reuses key + generation and links the predecessor.
    assert successor.id != failed.id
    assert successor.idempotency_key == "IMMUTABLE:v1"
    assert successor.input_generation == "gen-7"
    assert successor.predecessor_job_id == failed.id
    assert successor.state == "queued"

    # The predecessor's terminal immutability still holds: no transitions.
    with pytest.raises(InvalidStateTransition):
        repo.transition_job(failed.id, "queued", actor="reconciler", expected_revision=4)
    session.rollback()


def test_concurrent_successor_creation_yields_exactly_one(
    db_path: Path, tmp_path: Path
) -> None:
    """PM correction: concurrent successor creation yields exactly one
    successor per predecessor.

    Two independent sessions race create_successor on the same terminal
    predecessor; the unique predecessor_job_id constraint (backed by the
    repository's IntegrityError translation) lets exactly one win.  The
    predecessor's key is never mutated by either writer.
    """
    _upgrade(db_path, "head")
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        ws = _make_ws(session)
        repo = JobRepository(session)
        job = repo.create_job(
            workspace_id=ws.id,
            job_type="RENDER_VARIANT",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={},
            idempotency_key="CONCURRENT:v1",
            input_generation="g1",
        )
        lease = repo.acquire_lease(job.id, "worker-a")
        repo.transition_job(
            job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
        )
        repo.transition_job(
            job.id,
            "failed",
            actor="worker",
            expected_revision=3,
            fence_token=lease.fence_token,
            error={"error_code": "X", "message": "x"},
        )
        session.commit()
        pred_id = job.id
        pred_key = job.idempotency_key

    results: list[object] = []
    errors: list[Exception] = []
    # Two independent sessions race the same terminal predecessor.
    for _ in range(2):
        with Session(engine) as session:
            repo2 = JobRepository(session)
            try:
                results.append(
                    repo2.create_successor(predecessor_job_id=pred_id, input_manifest={})
                )
                session.commit()
            except Exception as exc:  # noqa: BLE001 - capture either outcome
                errors.append(exc)
                session.rollback()

    assert len(results) + len(errors) == 2
    assert len(results) == 1, f"expected exactly one successor, got {len(results)}: {errors}"
    assert all(isinstance(e, IdempotencyKeyInUse) for e in errors)

    # The predecessor kept its key and generation through the race.
    with Session(engine) as session:
        pred = session.get(Job, pred_id)
        assert pred is not None
        assert pred.idempotency_key == pred_key
        assert pred.state == "failed"
        succs = session.execute(
            __import__("sqlalchemy").text(
                "SELECT count(*) FROM job WHERE predecessor_job_id = :pid"
            ),
            {"pid": pred_id},
        ).scalar()
        assert succs == 1


def test_same_key_different_generation_is_independent(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: a fresh logical run bumps input_generation and yields a
    different key — both Jobs may exist (contract §8.1)."""
    first = _create_job(repo, ws, key="GEN:v1", generation="g1")
    session.commit()
    second = _create_job(repo, ws, key="GEN:v1", generation="g2")
    session.commit()
    assert first.id != second.id
    assert first.input_generation == "g1"
    assert second.input_generation == "g2"
    # Same key + same generation is still a conflict.
    with pytest.raises(IdempotencyKeyInUse):
        _create_job(repo, ws, key="GEN:v1", generation="g1")
    session.rollback()


def test_successor_of_active_job_rejected(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: a successor cannot be created for a non-terminal predecessor."""
    active = _create_job(repo, ws, key="ACTIVE:v1")
    session.commit()
    with pytest.raises(InvalidStateTransition):
        repo.create_successor(predecessor_job_id=active.id, input_manifest={})
    session.rollback()


def test_successor_of_completed_job_reuses_key(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: a completed logical run is not retried — the completed row wins.

    Creating a successor for a completed predecessor is a contradiction:
    the key already belongs to a completed Job, which is the reuse case
    (contract §8.1/§8.5), not a retry case.  The repository returns the
    completed Job so no duplicate or successor is ever created for a
    completed logical run.
    """
    done = _create_job(repo, ws, key="COMPLETED:v1")
    lease = _lease(repo, done.id)
    repo.transition_job(
        done.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        done.id, "completed", actor="worker", expected_revision=3, fence_token=lease.fence_token
    )
    session.commit()

    successor = repo.create_successor(predecessor_job_id=done.id, input_manifest={})
    assert successor.id == done.id
    assert successor.state == "completed"
    # No successor row was created for the completed Job.
    jobs = repo.list_jobs(ws.id)
    assert [j.id for j in jobs] == [done.id]


def test_successor_cycle_rejected(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: a successor may never reference its own descendant (cycle)."""
    a = _create_job(repo, ws, key="CYCLE:v1")
    lease = _lease(repo, a.id)
    repo.transition_job(
        a.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        a.id,
        "failed",
        actor="worker",
        expected_revision=3,
        fence_token=lease.fence_token,
        error={"error_code": "X", "message": "x"},
    )
    session.commit()
    b = repo.create_successor(predecessor_job_id=a.id, input_manifest={})
    session.commit()

    # b is active; it can never reference a as its predecessor again and
    # a cannot be a successor of b (a is terminal and already has a
    # successor, which the unique predecessor constraint enforces).
    with pytest.raises(IdempotencyKeyInUse):
        repo.create_successor(predecessor_job_id=a.id, input_manifest={})
    session.rollback()
    assert repo.get_job(b.id).predecessor_job_id == a.id


def test_steps_reject_unknown_and_cyclic_dependencies(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: step plans with unknown or cyclic dependencies are rejected."""
    with pytest.raises(JobStepCreationError):
        repo.create_job(
            workspace_id=ws.id,
            job_type="RENDER_VARIANT",
            owner_type="project",
            owner_id="o1",
            input_manifest={},
            idempotency_key="unknown-dep",
            steps=_steps("a", "b", depends={"b": ("nope",)}),
        )
    session.rollback()
    with pytest.raises(JobStepCreationError):
        repo.create_job(
            workspace_id=ws.id,
            job_type="RENDER_VARIANT",
            owner_type="project",
            owner_id="o1",
            input_manifest={},
            idempotency_key="cycle-dep",
            steps=_steps("a", "b", depends={"a": ("b",), "b": ("a",)}),
        )
    session.rollback()
    assert repo.list_jobs(ws.id) == []


def test_terminal_job_cannot_be_deleted(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC3: terminal rows are immutable — delete is refused."""
    job = _create_job(repo, ws, key="DEL:v1")
    lease = _lease(repo, job.id)
    repo.transition_job(
        job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        job.id, "completed", actor="worker", expected_revision=3, fence_token=lease.fence_token
    )
    session.commit()
    with pytest.raises(JobAlreadyTerminalError):
        repo.delete_job(job.id)
    session.rollback()
    assert repo.get_job(job.id).state == "completed"


def test_invalid_fk_fails(session: Session, ws: Workspace) -> None:
    """AC1: job.workspace_id is a real FK (RESTRICT)."""
    repo = JobRepository(session)
    with pytest.raises(IntegrityError):
        repo.create_job(
            workspace_id="00000000-0000-0000-0000-000000000000",
            job_type="RENDER_VARIANT",
            owner_type="project",
            owner_id="o1",
            input_manifest={},
            idempotency_key="bad-fk",
        )
    session.rollback()


# ── AC4: guarded transitions ─────────────────────────────────────────────────


def test_invalid_transition_rejected(repo: JobRepository, session: Session, ws: Workspace) -> None:
    """AC4: endpoints outside the transition table are rejected."""
    job = _create_job(repo, ws, state="pending")
    session.commit()
    with pytest.raises(InvalidStateTransition) as excinfo:
        repo.transition_job(
            job.id, "running", actor="scheduler", expected_revision=1
        )
    assert excinfo.value.code == INVALID_STATE_TRANSITION_CODE
    session.rollback()
    assert repo.get_job(job.id).state == "pending"


def test_terminal_state_immutable(repo: JobRepository, session: Session, ws: Workspace) -> None:
    """AC4: no transition leaves a terminal state; rows are immutable."""
    job = _create_job(repo, ws)
    lease = _lease(repo, job.id)
    repo.transition_job(
        job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        job.id, "completed", actor="worker", expected_revision=3, fence_token=lease.fence_token
    )
    session.commit()

    with pytest.raises(InvalidStateTransition):
        repo.transition_job(
            job.id, "queued", actor="reconciler", expected_revision=3
        )
    session.rollback()
    with pytest.raises(InvalidStateTransition):
        repo.transition_job(
            job.id, "failed", actor="worker", expected_revision=3, fence_token="x"
        )
    session.rollback()


def test_revision_mismatch_rejected(repo: JobRepository, session: Session, ws: Workspace) -> None:
    """AC4: optimistic concurrency — a stale revision is rejected."""
    job = _create_job(repo, ws)
    session.commit()
    with pytest.raises(InvalidStateTransition):
        repo.transition_job(job.id, "running", actor="scheduler", expected_revision=99)
    session.rollback()
    assert repo.get_job(job.id).state == "queued"


def test_fence_token_required_for_worker_transitions(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC4: worker transitions on a leased Job require the fence token."""
    job = _create_job(repo, ws)
    _lease(repo, job.id, worker="worker-a")
    session.commit()
    with pytest.raises(FencedWorkerError):
        repo.transition_job(job.id, "running", actor="worker", expected_revision=2)
    session.rollback()


def test_fenced_worker_write_rejected(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC4: a stale worker's write is dropped (fence token mismatch)."""
    job = _create_job(repo, ws)
    _lease(repo, job.id, worker="worker-a")
    session.commit()
    with pytest.raises(FencedWorkerError) as excinfo:
        repo.transition_job(
            job.id, "running", actor="worker", expected_revision=2, fence_token="stale-token"
        )
    assert excinfo.value.code == FENCED_WORKER_ERROR_CODE
    session.rollback()
    assert repo.get_job(job.id).state == "queued"


def test_live_lease_conflict_rejected(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """PM correction: a live unexpired lease held by another worker rejects."""
    job = _create_job(repo, ws)
    _lease(repo, job.id, worker="worker-a")
    session.commit()
    with pytest.raises(LeaseConflictError) as excinfo:
        _lease(repo, job.id, worker="worker-b")
    assert excinfo.value.code == LEASE_CONFLICT_CODE
    session.rollback()
    # The original lease is untouched.
    assert repo.get_lease(job.id).worker_id == "worker-a"


def test_expired_lease_reacquisition_bumps_version_and_token(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """PM correction: reacquisition after expiry monotonically bumps
    lease_version and the Job revision and issues a fresh token."""
    job = _create_job(repo, ws)
    first = _lease(repo, job.id, worker="worker-a")
    session.commit()
    assert first.lease_version == 1
    assert repo.get_job(job.id).revision == 2  # created(1) + claim(2)

    # Force expiry by rewinding the lease row (acquired_at too, so the
    # expires_at >= acquired_at CHECK stays satisfied).
    past = datetime.now(UTC) - timedelta(seconds=10)
    session.execute(
        text(
            "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
            "acquired_at = :past2 WHERE job_id = :jid"
        ),
        {"past": past, "past2": past - timedelta(seconds=60), "jid": job.id},
    )
    session.commit()

    second = _lease(repo, job.id, worker="worker-b")
    session.commit()
    assert second.lease_version == first.lease_version + 1
    assert second.fence_token != first.fence_token
    assert second.worker_id == "worker-b"
    assert repo.get_job(job.id).revision == 3  # claim bumped again

    # The old worker is now fenced.
    with pytest.raises(FencedWorkerError):
        repo.transition_job(
            job.id, "running", actor="worker", expected_revision=3, fence_token=first.fence_token
        )
    session.rollback()


def test_every_transition_appends_event(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC4: every accepted transition appends a JobEvent in the same tx."""
    job = _create_job(repo, ws, state="pending")
    session.commit()
    repo.transition_job(job.id, "queued", actor="scheduler", expected_revision=1)
    lease = _lease(repo, job.id, worker="worker-a")
    repo.transition_job(
        job.id, "running", actor="worker", expected_revision=3, fence_token=lease.fence_token
    )
    session.commit()

    events = repo.list_events(job.id)
    by_type = {e.event_type: e for e in events}
    assert "created" in by_type
    assert "transition" in by_type
    running_event = [e for e in events if e.to_state == "running"][0]
    assert running_event.actor == "worker"
    assert running_event.worker_id == "worker-a"
    assert running_event.fence_token == lease.fence_token
    assert running_event.revision == 4
    # Order: created(rev 1) -> queued(rev 2) -> lease bump(rev 3) -> running(rev 4)
    revs = [e.revision for e in reversed(events)]
    assert revs == [1, 2, 4]


def test_step_transitions_guarded(repo: JobRepository, session: Session, ws: Workspace) -> None:
    """AC4: JobStep transitions validate endpoints and fence tokens."""
    job = _create_job(repo, ws)
    lease = _lease(repo, job.id)
    repo.transition_job(
        job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    step = repo.list_steps(job.id)[0]
    repo.transition_step(
        step.id, "ready", actor="scheduler", expected_revision=1
    )
    repo.transition_step(
        step.id,
        "running",
        actor="worker",
        expected_revision=2,
        fence_token=lease.fence_token,
    )
    session.commit()

    assert repo.get_step(step.id).state == "running"
    with pytest.raises(InvalidStateTransition):
        # running -> completed with a stale revision is rejected by the
        # optimistic-concurrency guard.
        repo.transition_step(
            step.id,
            "completed",
            actor="worker",
            expected_revision=99,
            fence_token=lease.fence_token,
        )
    session.rollback()
    # A worker write without the fence token is fenced (contract §5.3-1).
    with pytest.raises(FencedWorkerError):
        repo.transition_step(step.id, "completed", actor="worker", expected_revision=3)
    session.rollback()
    # Step event recorded.
    events = repo.list_events(job.id)
    step_events = [e for e in events if e.step_id == step.id]
    assert any(e.to_state == "running" for e in step_events)


# ── AC5: attempts, envelopes, leases ─────────────────────────────────────────


def test_attempt_accounting_persists(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: attempt rows are append-only and carry worker/token/result."""
    job = _create_job(repo, ws)
    step = repo.list_steps(job.id)[0]
    lease = _lease(repo, job.id, worker="worker-a")
    repo.record_attempt(
        job_id=job.id,
        step_id=step.id,
        step_code=step.step_code,
        attempt=1,
        worker_id="worker-a",
        fence_token=lease.fence_token,
        result={"output": "ok"},
    )
    repo.record_attempt(
        job_id=job.id,
        step_id=step.id,
        step_code=step.step_code,
        attempt=2,
        worker_id="worker-a",
        fence_token=lease.fence_token,
        error={"error_code": "GPU_OOM", "class": "transient", "message": "oom"},
    )
    session.commit()

    attempts = repo.list_attempts(job.id)
    assert len(attempts) == 2
    by_number = {a.attempt: a for a in attempts}
    assert by_number[1].result == {"output": "ok"}
    assert by_number[2].error["error_code"] == "GPU_OOM"
    assert by_number[1].fence_token == lease.fence_token


def test_duplicate_attempt_number_rejected(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: duplicate attempt records for the same step are rejected."""
    job = _create_job(repo, ws)
    step = repo.list_steps(job.id)[0]
    lease = _lease(repo, job.id)
    repo.record_attempt(
        job_id=job.id,
        step_id=step.id,
        step_code=step.step_code,
        attempt=1,
        worker_id="worker-a",
        fence_token=lease.fence_token,
    )
    session.commit()
    with pytest.raises(IntegrityError):
        repo.record_attempt(
            job_id=job.id,
            step_id=step.id,
            step_code=step.step_code,
            attempt=1,
            worker_id="worker-a",
            fence_token=lease.fence_token,
        )
        session.commit()
    session.rollback()


def test_progress_checkpoint_error_envelopes(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: progress, checkpoint and error envelopes persist durably."""
    job = _create_job(repo, ws)
    step = repo.list_steps(job.id)[0]
    lease = _lease(repo, job.id, worker="worker-a")
    repo.update_progress(job.id, 42.5, fence_token=lease.fence_token)
    repo.update_step_progress(step.id, 12.0, fence_token=lease.fence_token)
    repo.write_checkpoint(
        step.id,
        {"schema_version": 1, "chunk_index": 3},
        fence_token=lease.fence_token,
    )
    session.commit()

    loaded = repo.get_job(job.id)
    assert loaded.progress == 42.5
    loaded_step = repo.get_step(step.id)
    assert loaded_step.progress == 12.0
    assert loaded_step.checkpoint == {"schema_version": 1, "chunk_index": 3}


def test_checkpoint_requires_schema_version(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: a checkpoint without schema_version fails closed (§7.2)."""
    job = _create_job(repo, ws)
    step = repo.list_steps(job.id)[0]
    with pytest.raises(JobError):
        repo.write_checkpoint(step.id, {"chunk_index": 1})
    session.rollback()


def test_lease_acquire_heartbeat_release(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: lease acquire/heartbeat/release persist with bounded behavior."""
    job = _create_job(repo, ws)
    lease = _lease(repo, job.id, worker="worker-a")
    session.commit()

    loaded = repo.get_lease(job.id)
    assert loaded is not None
    assert loaded.worker_id == "worker-a"
    assert loaded.lease_version == 1
    assert loaded.expires_at > loaded.acquired_at

    # Heartbeat extends expiry.
    before = loaded.expires_at
    renewed = repo.heartbeat_lease(
        job.id, "worker-a", lease.fence_token, ttl_seconds=120
    )
    session.commit()
    renewed_at = renewed.expires_at
    if renewed_at.tzinfo is None:
        renewed_at = renewed_at.replace(tzinfo=UTC)
    assert renewed_at > before.replace(tzinfo=UTC) if before.tzinfo is None else renewed_at > before
    assert renewed.ttl_seconds == 120

    # A different worker's heartbeat is fenced.
    with pytest.raises(FencedWorkerError):
        repo.heartbeat_lease(job.id, "worker-b", lease.fence_token)
    session.rollback()

    # Graceful release expires the lease immediately.
    repo.release_lease(job.id, "worker-a", lease.fence_token)
    session.commit()
    released = repo.get_lease(job.id)
    assert released is not None
    released_at = released.expires_at
    if released_at.tzinfo is None:
        released_at = released_at.replace(tzinfo=UTC)
    assert released_at <= datetime.now(UTC) + timedelta(seconds=1)


def test_lease_acquisition_is_exclusive_per_job(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: a Job has exactly one lease row (one writer per job)."""
    job = _create_job(repo, ws)
    _lease(repo, job.id, worker="worker-a")
    session.commit()
    rows = session.execute(
        text("SELECT COUNT(*) FROM job_lease WHERE job_id = :jid"), {"jid": job.id}
    ).scalar()
    assert rows == 1


def test_release_lease_then_reacquire(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: a gracefully released lease may be re-acquired (new token)."""
    job = _create_job(repo, ws)
    first = _lease(repo, job.id, worker="worker-a")
    repo.release_lease(job.id, "worker-a", first.fence_token)
    session.commit()
    second = _lease(repo, job.id, worker="worker-b")
    session.commit()
    assert second.lease_version == first.lease_version + 1
    assert second.fence_token != first.fence_token
    assert second.worker_id == "worker-b"


def test_two_session_lease_race_exactly_one_claimant(db_path: Path) -> None:
    """PM correction: a REAL two-session race on the same Job — exactly one
    claimant succeeds, the other receives LeaseConflictError.

    Both sessions synchronize on a barrier so they execute their atomic
    claim concurrently (not sequentially).  The INSERT ... ON CONFLICT DO
    NOTHING / guarded CAS guarantees a single winner.
    """
    import threading

    _upgrade(db_path, "head")
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        ws = _make_ws(session)
        repo = JobRepository(session)
        job = repo.create_job(
            workspace_id=ws.id,
            job_type="RENDER_VARIANT",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={},
            idempotency_key="RACE:v1",
            input_generation="g1",
        )
        session.commit()
        job_id = job.id

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def claimant(worker: str) -> None:
        with Session(engine) as s:
            r = JobRepository(s)
            barrier.wait()
            try:
                r.acquire_lease(job_id, worker, ttl_seconds=60)
                s.commit()
                outcome = "won"
            except LeaseConflictError:
                s.rollback()
                outcome = "conflict"
            with lock:
                outcomes.append(outcome)

    threads = [threading.Thread(target=claimant, args=(f"w{i}",)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(outcomes) == ["conflict", "won"]
    with Session(engine) as session:
        rows = session.execute(
            text("SELECT COUNT(*) FROM job_lease WHERE job_id = :jid"), {"jid": job_id}
        ).scalar()
        assert rows == 1
        winner = session.execute(
            text(
                "SELECT worker_id FROM job_lease WHERE job_id = :jid"
            ),
            {"jid": job_id},
        ).scalar()
        assert winner in ("w0", "w1")


def test_missing_token_rejected_on_worker_writes(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """PM correction: omission of the fence token is NOT a bypass — every
    worker-owned write while running/cancelling rejects a missing token with
    FENCED_WORKER."""
    job = _create_job(repo, ws)
    _run_job_until_running(repo, session, job.id)
    step = repo.list_steps(job.id)[0]
    session.commit()

    with pytest.raises(FencedWorkerError):
        repo.update_progress(job.id, 10.0)
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.update_step_progress(step.id, 5.0)
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.write_checkpoint(step.id, {"schema_version": 1, "i": 1})
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.record_attempt(
            job_id=job.id,
            step_id=step.id,
            step_code=step.step_code,
            attempt=1,
            worker_id="worker-a",
            fence_token=None,
        )
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.set_job_error(job.id, {"error_code": "X", "message": "x"})
    session.rollback()

    # Nothing was written.
    assert repo.get_job(job.id).progress == 0.0
    assert repo.get_step(step.id).progress == 0.0
    assert repo.get_step(step.id).checkpoint is None
    assert repo.list_attempts(job.id) == []


def test_stale_token_rejected_on_worker_writes(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """PM correction: a stale token is rejected on every worker-owned write."""
    job = _create_job(repo, ws)
    _run_job_until_running(repo, session, job.id)
    step = repo.list_steps(job.id)[0]
    session.commit()

    with pytest.raises(FencedWorkerError):
        repo.update_progress(job.id, 10.0, fence_token="stale")
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.update_step_progress(step.id, 5.0, fence_token="stale")
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.write_checkpoint(step.id, {"schema_version": 1, "i": 1}, fence_token="stale")
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.record_attempt(
            job_id=job.id,
            step_id=step.id,
            step_code=step.step_code,
            attempt=1,
            worker_id="worker-a",
            fence_token="stale",
        )
    session.rollback()
    with pytest.raises(FencedWorkerError):
        repo.set_job_error(job.id, {"error_code": "X", "message": "x"}, fence_token="stale")
    session.rollback()

    assert repo.get_job(job.id).progress == 0.0
    assert repo.get_step(step.id).progress == 0.0
    assert repo.list_attempts(job.id) == []


def test_release_and_requeue_flow(repo: JobRepository, session: Session, ws: Workspace) -> None:
    """AC4+AC5: running -> fenced -> queued uses the guarded table."""
    job = _create_job(repo, ws)
    lease = _lease(repo, job.id, worker="worker-a")
    repo.transition_job(
        job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    repo.transition_job(
        job.id, "fenced", actor="reconciler", expected_revision=3, reason_code="LEASE_EXPIRED"
    )
    repo.transition_job(job.id, "queued", actor="reconciler", expected_revision=4)
    session.commit()
    assert repo.get_job(job.id).state == "queued"
    events = repo.list_events(job.id)
    assert any(e.reason_code == "LEASE_EXPIRED" for e in events)


def test_fenced_worker_cannot_publish_state(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC4: a fenced worker's state write after re-claim is rejected."""
    job = _create_job(repo, ws)
    old_lease = _lease(repo, job.id, worker="worker-a")
    session.commit()
    # Force the lease expired (rewind acquired_at too for the CHECK), then
    # worker-b re-claims.
    past = datetime.now(UTC) - timedelta(seconds=10)
    session.execute(
        text(
            "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
            "acquired_at = :past2 WHERE job_id = :jid"
        ),
        {"past": past, "past2": past - timedelta(seconds=60), "jid": job.id},
    )
    session.commit()
    new_lease = _lease(repo, job.id, worker="worker-b")  # reconciler re-claim
    session.commit()
    assert new_lease.fence_token != old_lease.fence_token
    with pytest.raises(FencedWorkerError):
        repo.transition_job(
            job.id,
            "running",
            actor="worker",
            expected_revision=3,
            fence_token=old_lease.fence_token,
        )
    session.rollback()


def test_worker_id_resolution_in_events(
    repo: JobRepository, session: Session, ws: Workspace
) -> None:
    """AC5: events carry the worker id resolved from the lease."""
    job = _create_job(repo, ws)
    lease = _lease(repo, job.id, worker="worker-x")
    repo.transition_job(
        job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
    )
    session.commit()
    running = [e for e in repo.list_events(job.id) if e.to_state == "running"][0]
    assert running.worker_id == "worker-x"
    assert running.actor == "worker"


# ── AC2/AC6: reopen + scope ──────────────────────────────────────────────────


def test_reopen_preserves_jobs_and_leases(db_path: Path) -> None:
    """AC2: jobs, steps, attempts, events and leases survive reopen."""
    _upgrade(db_path, "head")
    engine = create_engine_for_path(db_path)
    with Session(engine) as session:
        ws = _make_ws(session)
        repo = JobRepository(session)
        job = _create_job(repo, ws, key="REOPEN:v1")
        lease = _lease(repo, job.id, worker="worker-a")
        step = repo.list_steps(job.id)[0]
        repo.transition_job(
            job.id, "running", actor="worker", expected_revision=2, fence_token=lease.fence_token
        )
        repo.record_attempt(
            job_id=job.id,
            step_id=step.id,
            step_code=step.step_code,
            attempt=1,
            worker_id="worker-a",
            fence_token=lease.fence_token,
        )
        repo.write_checkpoint(
            step.id, {"schema_version": 1, "done": 1}, fence_token=lease.fence_token
        )
        session.commit()
        job_id, step_id, token = job.id, step.id, lease.fence_token

    engine2 = create_engine_for_path(db_path)
    with Session(engine2) as session2:
        repo2 = JobRepository(session2)
        loaded = repo2.get_job(job_id)
        assert loaded.state == "running"
        assert len(repo2.list_events(job_id)) == 2  # created + transition
        assert len(repo2.list_attempts(job_id)) == 1
        lease2 = repo2.get_lease(job_id)
        assert lease2 is not None and lease2.fence_token == token
        step2 = repo2.get_step(step_id)
        assert step2.checkpoint == {"schema_version": 1, "done": 1}


def test_unknown_job_raises_not_found(repo: JobRepository) -> None:
    """Repository reads fail closed for unknown ids."""
    with pytest.raises(JobNotFoundError):
        repo.get_job("does-not-exist")
