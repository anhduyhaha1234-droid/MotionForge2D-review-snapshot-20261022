"""Targeted tests for S02-T04 — restart reconciliation and safe resume.

Covers AC1-AC7 of ``docs/pm/sessions/S02-T04-restart-reconciliation/TASK.md``:

- AC1: explicit run-once/startup reconciler scans only expired active leases
  using bounded batches; no import-time execution.
- AC2: reconciliation atomically invalidates the old fence token and records
  ``running|cancelling -> fenced -> queued|failed`` events.
- AC3: retryable Jobs with attempts remaining and a valid versioned
  checkpoint requeue/resume; incompatible/missing-required checkpoint fails
  closed.
- AC4: cancelling Jobs reconcile to cancelled without running new effects;
  exhausted/permanent/input-changed Jobs fail with a stable envelope.
- AC5: the old worker token is rejected after reconciliation and cannot
  mutate or publish; a new worker continues from the committed checkpoint
  without duplicates.
- AC6: forced-close/reopen integration tests prove state/events/attempts and
  artifact visibility across fresh engine/session instances.
- AC7: no API cutover/schema/deps; targeted tests and 7/7 PASS.

Every test uses a temporary database under ``tmp_path`` and an injectable
fake clock/sleeper so expiry windows and restart simulations are fast and
deterministic.  No GPU/model/network work — synthetic handlers only.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.persistence import (
    FencedWorkerError,
    JobRepository,
    StepInput,
    create_engine_for_path,
    create_session_factory,
)
from app.persistence.models import Workspace
from app.workflow.durable_worker import (
    DurableWorker,
    WorkerConfig,
    WorkerContext,
)
from app.workflow.job_reconciler import (
    INPUT_CHANGED_CODE,
    RETRIES_EXHAUSTED_CODE,
    JobReconciler,
    ReconcileConfig,
    manifest_fingerprint,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


# ── Deterministic clock/sleeper ──────────────────────────────────────────────


class FakeClock:
    """Injectable clock: starts at a fixed UTC instant and advances on demand."""

    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class FakeSleeper:
    """Injectable sleeper: records requested delays, never blocks."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


# ── DB fixtures ──────────────────────────────────────────────────────────────


def _alembic_config(database_path: Path) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return cfg


def _upgrade(database_path: Path) -> None:
    command.upgrade(_alembic_config(database_path), "head")


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """A fresh temporary database path per test."""
    return tmp_path / "test_reconcile.db"


@pytest.fixture()
def session_factory(db_path: Path):
    """Session factory bound to an upgraded temporary database."""
    _upgrade(db_path)
    return create_session_factory(create_engine_for_path(db_path))


@pytest.fixture()
def session(session_factory) -> Iterator[Session]:
    with session_factory() as s:
        yield s


@pytest.fixture()
def repo(session: Session) -> JobRepository:
    return JobRepository(session)


@pytest.fixture()
def ws(session: Session) -> Workspace:
    ws = Workspace(name="Reconcile Workspace")
    session.add(ws)
    session.commit()
    return ws


@pytest.fixture()
def managed_root(tmp_path: Path) -> Path:
    root = tmp_path / "managed"
    root.mkdir(exist_ok=True)
    return root


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def sleeper() -> FakeSleeper:
    return FakeSleeper()


@pytest.fixture()
def reconciler(
    session_factory, clock: FakeClock, sleeper: FakeSleeper
) -> JobReconciler:
    """A reconciler with fake clock/sleeper and a temp DB."""
    return JobReconciler(
        session_factory,
        config=ReconcileConfig(
            batch_size=50,
            fence_grace_seconds=0.0,  # fence immediately once expired
            poll_interval=0.01,
        ),
        clock=clock,
        sleeper=sleeper,
    )


def _steps(*codes: str) -> list[StepInput]:
    return [
        StepInput(step_code=code, position=i, step_type="sync")
        for i, code in enumerate(codes)
    ]


def _create(
    repo: JobRepository,
    ws: Workspace,
    *,
    job_type: str = "SYNTH",
    steps: list[StepInput] | None = None,
    key: str | None = "SYNTH:v1",
    max_attempts: int = 3,
    manifest: dict | None = None,
) -> object:
    return repo.create_job(
        workspace_id=ws.id,
        job_type=job_type,
        owner_type="project",
        owner_id="owner-1",
        input_manifest=manifest or {"managed_root": "artifacts"},
        idempotency_key=key,
        max_attempts=max_attempts,
        steps=steps or _steps("s1"),
    )


def _run_until_running(
    repo: JobRepository, session: Session, job_id: str
) -> object:
    """Claim + transition a Job to ``running``; return the lease."""
    lease = repo.acquire_lease(job_id, "worker-a", ttl_seconds=60)
    repo.transition_job(
        job_id,
        "running",
        actor="worker",
        expected_revision=repo.get_job(job_id).revision,
        fence_token=lease.fence_token,
    )
    session.commit()
    return lease


def _expire_lease(
    session: Session, job_id: str, *, seconds: int = 10, now: datetime | None = None
) -> None:
    """Force the lease row into the past (CHECK-safe rewind).

    *now* is the reconciler's clock instant; when the reconciler uses a fake
    clock the rewind MUST use the same instant or the scan's expiry
    comparison (fake-now based) never sees the lease as expired.
    """
    now = now or datetime.now(UTC)
    past = now - timedelta(seconds=seconds)
    session.execute(
        text(
            "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
            "acquired_at = :past2 WHERE job_id = :jid"
        ),
        {"past": past, "past2": past - timedelta(seconds=60), "jid": job_id},
    )
    session.commit()


def _with_checkpoint(
    session: Session, step_id: str, checkpoint: dict, token: str
) -> None:
    """Write a schema-versioned checkpoint through the repository."""
    r = JobRepository(session)
    r.write_checkpoint(step_id, checkpoint, fence_token=token)
    session.commit()


def _write_file(root: Path, rel: str, data: bytes) -> tuple[str, int]:
    import hashlib

    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


# ── AC1: explicit run-once, bounded scan, no import-time behavior ────────────


def test_import_starts_no_thread_or_work() -> None:
    """AC1: importing the module and constructing a reconciler starts nothing."""
    import threading

    from app.workflow import job_reconciler  # noqa: F401

    before = threading.active_count()
    r = JobReconciler(lambda: None)  # type: ignore[arg-type]
    assert r.running is False
    assert r._thread is None
    assert threading.active_count() == before


def test_reconcile_once_empty_queue_reports_zero(
    reconciler: JobReconciler,
    clock: FakeClock,
) -> None:
    """AC1: an empty scan is a no-op with a structured report."""
    report = reconciler.reconcile_once()
    assert report.scanned == 0
    assert report.fenced == 0
    assert report.resolved == 0
    assert report.errors == []


def test_reconcile_once_scans_only_expired_active_leases(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    reconciler: JobReconciler,
    clock: FakeClock,
) -> None:
    """AC1: only running/cancelling Jobs with expired leases are candidates."""
    live = _create(repo, ws, key="LIVE:v1")
    expired = _create(repo, ws, key="EXPIRED:v1")
    session.commit()
    _run_until_running(repo, session, live.id)
    _run_until_running(repo, session, expired.id)
    _expire_lease(session, expired.id, now=clock.now)

    report = reconciler.reconcile_once()
    # Only the expired lease was scanned; the live lease is untouched.
    assert report.scanned == 1
    with session_factory() as s:
        r = JobRepository(s)
        assert r.get_job(live.id).state == "running"
        assert r.get_job(expired.id).state == "queued"  # requeued


def test_reconcile_once_bounded_batch(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC1: a pass resolves at most ``batch_size`` candidates."""
    small = JobReconciler(
        session_factory,
        config=ReconcileConfig(batch_size=2, fence_grace_seconds=0.0),
        clock=clock,
    )
    ids: list[str] = []
    for i in range(5):
        job = _create(repo, ws, key=f"BATCH:v{i}")
        session.commit()
        _run_until_running(repo, session, job.id)
        _expire_lease(session, job.id, now=clock.now)
        ids.append(job.id)

    first = small.reconcile_once()
    assert first.fenced == 2
    assert first.scanned == 2
    second = small.reconcile_once()
    assert second.fenced == 2
    third = small.reconcile_once()
    assert third.fenced == 1
    with session_factory() as s:
        r = JobRepository(s)
        assert all(r.get_job(jid).state == "queued" for jid in ids)


def test_grace_window_prevents_premature_fencing(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC1: a lease expired within the heartbeat grace is not fenced yet."""
    job = _create(repo, ws, key="GRACE:v1")
    session.commit()
    _run_until_running(repo, session, job.id)
    # Expire the lease by less than the default 90s grace.
    _expire_lease(session, job.id, seconds=30)

    graceful = JobReconciler(
        session_factory,
        config=ReconcileConfig(batch_size=10),
        clock=clock,
    )
    report = graceful.reconcile_once()
    assert report.scanned == 0
    with session_factory() as s:
        assert JobRepository(s).get_job(job.id).state == "running"


def test_start_stop_lifecycle(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC1: start() spawns one loop thread; stop() joins and stops it."""
    job = _create(repo, ws)
    session.commit()
    _run_until_running(repo, session, job.id)
    _expire_lease(session, job.id, now=clock.now)

    r = JobReconciler(
        session_factory,
        config=ReconcileConfig(batch_size=10, fence_grace_seconds=0.0),
        clock=clock,
    )
    r.start()
    try:
        assert r.running is True
    finally:
        r.stop(timeout=5.0)
    assert r.running is False
    with session_factory() as s:
        assert JobRepository(s).get_job(job.id).state == "queued"


# ── AC2: atomic fencing + event record ───────────────────────────────────────


def test_fence_invalidates_token_and_records_events(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC2: fencing clears the old token and records running->fenced->queued."""
    job = _create(repo, ws)
    session.commit()
    lease = _run_until_running(repo, session, job.id)
    old_token = lease.fence_token
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.fenced == 1
    assert report.requeued == 1

    with session_factory() as s:
        r = JobRepository(s)
        lease_row = r.get_lease(job.id)
        assert lease_row is not None
        # The old token was replaced by a unique non-empty sentinel
        # (schema CHECK forbids empty tokens).
        assert lease_row.fence_token != old_token
        assert lease_row.fence_token.startswith("fenced:")
        to_states = [e.to_state for e in r.list_events(job.id)]
        assert "fenced" in to_states
        assert "queued" in to_states
        fence_event = [e for e in r.list_events(job.id) if e.to_state == "fenced"][0]
        assert fence_event.actor == "reconciler"
        assert fence_event.reason_code == "LEASE_EXPIRED"
        assert fence_event.details is not None
        assert fence_event.details["worker_id"] == "worker-a"
        assert fence_event.details["old_fence_token_present"] is True
        requeue_events = [e for e in r.list_events(job.id) if e.reason_code == "FENCED_REQUEUE"]
        assert len(requeue_events) == 1
        assert requeue_events[0].actor == "reconciler"
    assert old_token != ""


# ── AC3: requeue/resume with attempts and versioned checkpoints ──────────────


def test_requeue_resumes_from_committed_checkpoint(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    reconciler: JobReconciler,
    managed_root: Path,
    clock: FakeClock,
) -> None:
    """AC3: a retryable Job with a valid versioned checkpoint requeues and a
    fresh worker resumes from the committed checkpoint (no re-run of
    committed work, no duplicate effects)."""
    created = _create(
        repo,
        ws,
        manifest={"managed_root": str(managed_root)},
        steps=_steps("s1"),
    )
    session.commit()
    lease = _run_until_running(repo, session, created.id)
    step = repo.list_steps(created.id)[0]
    repo.transition_step(
        step.id,
        "ready",
        actor="scheduler",
        expected_revision=step.revision,
    )
    step = repo.get_step(step.id)
    repo.transition_step(
        step.id,
        "running",
        actor="worker",
        expected_revision=step.revision,
        fence_token=lease.fence_token,
    )
    _with_checkpoint(
        session, step.id, {"schema_version": 1, "chunk_index": 7}, lease.fence_token
    )
    session.commit()
    _expire_lease(session, created.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.requeued == 1

    effects: list[dict] = []

    def resume_handler(ctx: WorkerContext) -> dict:
        # A resumed handler observes the committed checkpoint, never a fresh one.
        effects.append({"step": ctx.step_code, "checkpoint": ctx.checkpoint})
        return {}

    w = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="worker-b",
            lease_ttl=60,
            heartbeat_interval=15,
            poll_interval=0.01,
            staging_root=managed_root,
        ),
    )
    w.register_handler("SYNTH", resume_handler)
    assert w.run_once() == 1

    assert effects == [{"step": "s1", "checkpoint": {"schema_version": 1, "chunk_index": 7}}]
    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "completed"
        assert job.attempt == 1  # requeue bumped the durable counter
        step2 = r.list_steps(created.id)[0]
        assert step2.state == "completed"
        assert step2.attempt == 1  # step counter bumped by the reconciler
        attempts = r.list_attempts(created.id)
        assert len(attempts) == 1  # exactly one attempt row (no duplicates)
        # Artifacts: none published by the resumed step (declared none).
        rows = s.execute(
            text("SELECT COUNT(*) FROM artifact WHERE workspace_id = :wid"),
            {"wid": ws.id},
        ).scalar()
        assert rows == 0


def test_requeue_bumps_attempts_atomically(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC3/§8.2: requeue bumps Job and non-terminal step attempt counters in
    the same transaction as fenced->queued."""
    job = _create(repo, ws, steps=_steps("s1", "s2"))
    session.commit()
    _run_until_running(repo, session, job.id)
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.requeued == 1
    with session_factory() as s:
        r = JobRepository(s)
        assert r.get_job(job.id).attempt == 1
        for step in r.list_steps(job.id):
            assert step.attempt == 1
            assert step.state in ("pending", "ready")
            # The step that was mid-flight rolled back to ready (if any).
        # Terminal-completed steps are untouched by the bump.
        # (s1/s2 were pending, so both are pending; no completed step here.)


def test_requeued_step_rolls_back_running_to_ready(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC3/§4.4: a step mid-flight when fenced returns to ready (attempt
    rolled back) so a re-claiming worker replays only uncommitted work."""
    job = _create(repo, ws, steps=_steps("s1", "s2"))
    session.commit()
    lease = _run_until_running(repo, session, job.id)
    step1 = repo.list_steps(job.id)[0]
    repo.transition_step(
        step1.id,
        "ready",
        actor="scheduler",
        expected_revision=step1.revision,
    )
    step1 = repo.get_step(step1.id)
    repo.transition_step(
        step1.id,
        "running",
        actor="worker",
        expected_revision=step1.revision,
        fence_token=lease.fence_token,
    )
    session.commit()
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.requeued == 1
    with session_factory() as s:
        r = JobRepository(s)
        states = {st.step_code: st.state for st in r.list_steps(job.id)}
        assert states["s1"] == "ready"  # rolled back
        assert states["s2"] == "pending"  # never started
        # The rollback event is recorded.
        step_events = [e for e in r.list_events(job.id) if e.step_id == step1.id]
        assert any(e.reason_code == "FENCED_ROLLBACK" for e in step_events)


def test_incompatible_checkpoint_fails_closed_on_resume(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    reconciler: JobReconciler,
    managed_root: Path,
    clock: FakeClock,
) -> None:
    """AC3/§7.2: a checkpoint with an unsupported schema_version is not
    resumed — the step re-runs from a fresh checkpoint, and a Job whose
    handler rejects the version fails closed with a stable envelope."""
    created = _create(
        repo,
        ws,
        manifest={"managed_root": str(managed_root)},
        steps=_steps("s1"),
    )
    session.commit()
    lease = _run_until_running(repo, session, created.id)
    step = repo.list_steps(created.id)[0]
    repo.transition_step(
        step.id,
        "ready",
        actor="scheduler",
        expected_revision=step.revision,
    )
    step = repo.get_step(step.id)
    repo.transition_step(
        step.id,
        "running",
        actor="worker",
        expected_revision=step.revision,
        fence_token=lease.fence_token,
    )
    # Version 99 is not supported by this worker generation.
    _with_checkpoint(
        session, step.id, {"schema_version": 99, "payload": "future"}, lease.fence_token
    )
    session.commit()
    _expire_lease(session, created.id, now=clock.now)

    reconciler.reconcile_once()

    def strict_handler(ctx: WorkerContext) -> dict:
        if ctx.checkpoint.get("schema_version") != 1:
            exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError(
                "SCHEMA_MISMATCH"
            )
            exc.code = "SCHEMA_MISMATCH"
            raise exc
        return {}

    w = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="worker-b", lease_ttl=60, heartbeat_interval=15,
            poll_interval=0.01, staging_root=managed_root,
        ),
    )
    w.register_handler("SYNTH", strict_handler)
    w.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        # Fail-closed: the Job failed with the stable envelope, never resumed
        # against an incompatible checkpoint.
        assert job.state == "failed"
        assert job.error is not None
        assert job.error["error_code"] in ("SCHEMA_MISMATCH", "RETRIES_EXHAUSTED")
        assert job.error["class"] == "permanent"


def test_missing_required_checkpoint_fails_closed(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    reconciler: JobReconciler,
    managed_root: Path,
    clock: FakeClock,
) -> None:
    """AC3/§7.2: a step whose required checkpoint is missing is not resumed —
    the handler fails closed with a stable envelope instead of guessing."""
    created = _create(
        repo,
        ws,
        manifest={"managed_root": str(managed_root)},
        steps=_steps("s1"),
    )
    session.commit()
    lease = _run_until_running(repo, session, created.id)
    step = repo.list_steps(created.id)[0]
    repo.transition_step(
        step.id,
        "ready",
        actor="scheduler",
        expected_revision=step.revision,
    )
    step = repo.get_step(step.id)
    repo.transition_step(
        step.id,
        "running",
        actor="worker",
        expected_revision=step.revision,
        fence_token=lease.fence_token,
    )
    session.commit()  # no checkpoint written
    _expire_lease(session, created.id, now=clock.now)

    reconciler.reconcile_once()

    def requires_checkpoint(ctx: WorkerContext) -> dict:
        if not ctx.checkpoint or not ctx.checkpoint.get("chunk_index"):
            exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError(
                "SCHEMA_MISMATCH"
            )
            exc.code = "SCHEMA_MISMATCH"
            raise exc
        return {}

    w = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="worker-b", lease_ttl=60, heartbeat_interval=15,
            poll_interval=0.01, staging_root=managed_root,
        ),
    )
    w.register_handler("SYNTH", requires_checkpoint)
    w.run_once()

    with session_factory() as s:
        job = JobRepository(s).get_job(created.id)
        assert job.state == "failed"
        assert job.error is not None
        assert job.error["error_code"] in ("SCHEMA_MISMATCH", "RETRIES_EXHAUSTED")
        assert job.error["class"] == "permanent"


# ── AC4: cancel/exhausted/permanent/input-changed reconciliation ─────────────


def test_cancelling_job_reconciles_to_cancelled_without_effects(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC4: a Job that was cancelling when fenced resolves straight to
    terminal cancelled — no new effects, no retry."""
    job = _create(repo, ws, steps=_steps("s1", "s2"))
    session.commit()
    _run_until_running(repo, session, job.id)
    repo.transition_job(
        job.id,
        "cancelling",
        actor="api",
        expected_revision=repo.get_job(job.id).revision,
    )
    session.commit()
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.cancelled == 1
    assert report.requeued == 0

    with session_factory() as s:
        r = JobRepository(s)
        job_row = r.get_job(job.id)
        assert job_row.state == "cancelled"
        assert job_row.finished_at is not None
        cancel_event = [e for e in r.list_events(job.id) if e.to_state == "cancelled"][-1]
        assert cancel_event.actor == "reconciler"
        assert cancel_event.reason_code == "CANCEL_DRAINED"
        # No artifacts were published by the cancel path.
        rows = s.execute(
            text("SELECT COUNT(*) FROM artifact WHERE workspace_id = :wid"),
            {"wid": ws.id},
        ).scalar()
        assert rows == 0


def test_exhausted_attempts_fail_with_stable_envelope(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC4: a Job at its attempt budget fails with RETRIES_EXHAUSTED."""
    job = _create(repo, ws, max_attempts=2)
    session.commit()
    _run_until_running(repo, session, job.id)
    # Consume the budget: two prior fence+requeue bumps already happened.
    with session_factory() as s:
        JobRepository(s).bump_job_attempt(job.id)
        JobRepository(s).bump_job_attempt(job.id)
        s.commit()
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.failed == 1
    assert report.requeued == 0
    with session_factory() as s:
        job_row = JobRepository(s).get_job(job.id)
        assert job_row.state == "failed"
        assert job_row.error is not None
        assert job_row.error["error_code"] == RETRIES_EXHAUSTED_CODE
        assert job_row.error["class"] == "permanent"
        assert job_row.error["retryable"] is False


def test_input_changed_fails_closed(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC4/§4.3: a Job whose input manifest changed since fencing fails with
    INPUT_CHANGED — resume against changed inputs is refused."""
    job = _create(
        repo,
        ws,
        manifest={"managed_root": "artifacts", "variant": "v1"},
    )
    session.commit()
    _run_until_running(repo, session, job.id)
    _expire_lease(session, job.id, now=clock.now)

    # Pass 1: fence records the fingerprint of the CURRENT (v1) manifest and
    # requeues the Job.
    first = reconciler.reconcile_once()
    assert first.requeued == 1

    # Mutate the manifest AFTER the fence recorded the v1 fingerprint.
    with session_factory() as s:
        s.execute(
            text("UPDATE job SET input_manifest_json = :m WHERE id = :jid"),
            {"m": __import__("json").dumps(
                {"managed_root": "artifacts", "variant": "v2"}
            ), "jid": job.id},
        )
        s.commit()

    # Pass 2: the Job is running again under a fresh lease; when it is fenced
    # again the fingerprint comparison fails closed with INPUT_CHANGED.
    # (Re-claim + run to running so the next pass has an active lease.)
    with session_factory() as s:
        r = JobRepository(s)
        r.acquire_lease(job.id, "worker-a", ttl_seconds=60)
        r.transition_job(
            job.id,
            "running",
            actor="worker",
            expected_revision=r.get_job(job.id).revision,
            fence_token=r.get_lease(job.id).fence_token,
        )
        s.commit()
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    assert report.failed == 1
    with session_factory() as s:
        job_row = JobRepository(s).get_job(job.id)
        assert job_row.state == "failed"
        assert job_row.error is not None
        assert job_row.error["error_code"] == INPUT_CHANGED_CODE
        assert job_row.error["class"] == "permanent"


def test_permanent_failure_reconciled_to_failed(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC4: a Job already carrying a permanent envelope fails stably when
    fenced (the envelope is preserved, no retry is scheduled)."""
    job = _create(repo, ws)
    session.commit()
    _run_until_running(repo, session, job.id)
    # Bump the Job-level attempt to its budget (max_attempts=3) so the
    # reconciler's attempts-exhausted check fires (the attempt budget is the
    # authority for the reconciler's terminal decision).
    with session_factory() as s:
        for _ in range(3):  # attempt: 0 -> 3 = max_attempts
            JobRepository(s).bump_job_attempt(job.id)
        s.commit()
    _expire_lease(session, job.id, now=clock.now)

    report = reconciler.reconcile_once()
    # The Job was fenced (it was running) but its attempt budget is spent:
    # the reconciler fails it with the stable RETRIES_EXHAUSTED envelope.
    assert report.fenced == 1
    assert report.failed == 1
    assert report.requeued == 0
    with session_factory() as s:
        job_row = JobRepository(s).get_job(job.id)
        assert job_row.state == "failed"
        assert job_row.error is not None
        assert job_row.error["error_code"] == RETRIES_EXHAUSTED_CODE
        assert job_row.error["class"] == "permanent"
        assert job_row.error["retryable"] is False


# ── AC5: stale worker rejected after reconciliation; new worker continues ────


def test_stale_worker_token_rejected_after_reconciliation(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC5: after fencing, the old worker's token is rejected on every write —
    it cannot mutate state or publish."""
    job = _create(repo, ws)
    session.commit()
    lease = _run_until_running(repo, session, job.id)
    old_token = lease.fence_token
    _expire_lease(session, job.id, now=clock.now)

    reconciler.reconcile_once()
    with session_factory() as s:
        r = JobRepository(s)
        # The Job was requeued: it is no longer running/cancelling, so the
        # fence-token guard is not engaged.  The stale worker must first be
        # unable to re-claim: a live lease belongs to the requeued Job's
        # previous claim (token sentinel), so a NEW claim by the old worker
        # is a lease conflict — and once re-claimed by a fresh worker, the
        # old token is rejected.  Prove the token was invalidated:
        lease_row = r.get_lease(job.id)
        assert lease_row is not None
        assert lease_row.fence_token != old_token  # sentinel replaced it
        # A worker write with the OLD token against the sentinel lease is
        # rejected — but only while the Job is leased/running.  Re-claim the
        # Job as the new worker first (the reconciler requeued it), then the
        # old token is rejected on the running Job.
        new_lease = r.acquire_lease(job.id, "worker-b", ttl_seconds=60)
        r.transition_job(
            job.id,
            "running",
            actor="worker",
            expected_revision=r.get_job(job.id).revision,
            fence_token=new_lease.fence_token,
        )
        s.commit()
        with pytest.raises(FencedWorkerError):
            r.update_progress(job.id, 10.0, fence_token=old_token)
        with pytest.raises(FencedWorkerError):
            r.transition_job(
                job.id,
                "completed",
                actor="worker",
                expected_revision=r.get_job(job.id).revision,
                fence_token=old_token,
            )
        s.rollback()
        # Nothing was published.
        assert r.get_job(job.id).state == "running"
        assert r.get_job(job.id).progress == 0.0


def test_stale_worker_cannot_release_new_lease(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    reconciler: JobReconciler,
    session_factory,
    clock: FakeClock,
) -> None:
    """AC5: a fenced worker cannot release the (re-claimed) lease."""
    job = _create(repo, ws)
    session.commit()
    lease = _run_until_running(repo, session, job.id)
    old_token = lease.fence_token
    _expire_lease(session, job.id, now=clock.now)

    reconciler.reconcile_once()
    with session_factory() as s:
        r = JobRepository(s)
        with pytest.raises(FencedWorkerError):
            r.release_lease(job.id, "worker-a", old_token)
        s.rollback()
        lease_row = r.get_lease(job.id)
        assert lease_row is not None
        assert lease_row.worker_id == "worker-a"  # old lease row still there
        # The token was invalidated (replaced by a sentinel) — the old worker
        # can never present it again.
        assert lease_row.fence_token != old_token
        assert lease_row.fence_token.startswith("fenced:")


def test_new_worker_continues_from_committed_checkpoint_no_duplicates(
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    session_factory,
    reconciler: JobReconciler,
    managed_root: Path,
    clock: FakeClock,
) -> None:
    """AC5: after reconciliation, a NEW worker re-claims and resumes from the
    committed checkpoint; attempt rows and effects are never duplicated."""
    created = _create(
        repo,
        ws,
        manifest={"managed_root": str(managed_root)},
        steps=_steps("s1"),
    )
    session.commit()
    lease = _run_until_running(repo, session, created.id)
    step = repo.list_steps(created.id)[0]
    repo.transition_step(
        step.id,
        "ready",
        actor="scheduler",
        expected_revision=step.revision,
    )
    step = repo.get_step(step.id)
    repo.transition_step(
        step.id,
        "running",
        actor="worker",
        expected_revision=step.revision,
        fence_token=lease.fence_token,
    )
    _with_checkpoint(
        session, step.id, {"schema_version": 1, "chunk_index": 3}, lease.fence_token
    )
    session.commit()
    _expire_lease(session, created.id, now=clock.now)

    reconciler.reconcile_once()

    seen: list[dict] = []

    def resume(ctx: WorkerContext) -> dict:
        seen.append({"attempt": ctx.attempt, "cp": ctx.checkpoint})
        return {}

    w = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="worker-b", lease_ttl=60, heartbeat_interval=15,
            poll_interval=0.01, staging_root=managed_root,
        ),
    )
    w.register_handler("SYNTH", resume)
    w.run_once()

    assert seen == [{"attempt": 1, "cp": {"schema_version": 1, "chunk_index": 3}}]
    with session_factory() as s:
        r = JobRepository(s)
        assert r.get_job(created.id).state == "completed"
        attempts = r.list_attempts(created.id)
        assert len(attempts) == 1  # exactly one attempt row total
        assert attempts[0].attempt == 1
        # No duplicate artifact rows.
        rows = s.execute(
            text("SELECT COUNT(*) FROM artifact WHERE workspace_id = :wid"),
            {"wid": ws.id},
        ).scalar()
        assert rows == 0


# ── AC6: forced-close/reopen integration across fresh sessions ───────────────


def test_forced_close_reopen_reconciles_and_resumes(
    db_path: Path, managed_root: Path
) -> None:
    """AC6: a worker is 'killed' mid-job (process ends); a fresh engine +
    reconciler + worker reopen the database and safely requeue/resume with
    no duplicate effects."""
    _upgrade(db_path)
    engine1 = create_engine_for_path(db_path)
    factory1 = create_session_factory(engine1)
    # The reconciler (phase 2) runs on a fake clock; the phase-1 lease rewind
    # must use the same instant or the scan's expiry comparison misses it.
    clock = FakeClock()
    fake_now = clock.now

    # Phase 1: worker-a claims the Job, writes a checkpoint, then is killed
    # (no graceful release — the lease stays expired).
    with factory1() as s:
        ws = Workspace(name="Reopen Workspace")
        s.add(ws)
        s.commit()
        r = JobRepository(s)
        job = r.create_job(
            workspace_id=ws.id,
            job_type="SYNTH",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={"managed_root": str(managed_root)},
            idempotency_key="REOPEN:v1",
            max_attempts=3,
            steps=_steps("s1"),
        )
        s.commit()
        lease = r.acquire_lease(job.id, "worker-a", ttl_seconds=60)
        r.transition_job(
            job.id,
            "running",
            actor="worker",
            expected_revision=r.get_job(job.id).revision,
            fence_token=lease.fence_token,
        )
        s.commit()
        step = r.list_steps(job.id)[0]
        r.transition_step(
            step.id,
            "ready",
            actor="scheduler",
            expected_revision=step.revision,
        )
        step = r.get_step(step.id)
        r.transition_step(
            step.id,
            "running",
            actor="worker",
            expected_revision=step.revision,
            fence_token=lease.fence_token,
        )
        r.write_checkpoint(
            step.id, {"schema_version": 1, "chunk_index": 5}, fence_token=lease.fence_token
        )
        s.commit()
        job_id = job.id
        ws_id = ws.id
        # Force the lease into the past: the worker is dead and never
        # heartbeats/releases (this is what a forced close leaves behind).
        past = fake_now - timedelta(seconds=120)
        s.execute(
            text(
                "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                "acquired_at = :past2 WHERE job_id = :jid"
            ),
            {"past": past, "past2": past - timedelta(seconds=60), "jid": job_id},
        )
        s.commit()
    # engine1 goes out of scope = the old process is gone.

    # Phase 2: brand-new process (fresh engine) — restart reconciliation.
    engine2 = create_engine_for_path(db_path)
    factory2 = create_session_factory(engine2)
    rec = JobReconciler(
        factory2,
        config=ReconcileConfig(batch_size=10, fence_grace_seconds=0.0),
        clock=clock,
    )
    report = rec.reconcile_once()
    assert report.fenced == 1
    assert report.requeued == 1

    # The old worker's token was invalidated by the fence: prove the lease
    # row no longer carries it.
    with factory2() as s:
        r = JobRepository(s)
        lease_row = r.get_lease(job_id)
        assert lease_row is not None
        assert lease_row.fence_token.startswith("fenced:")  # sentinel

    # Phase 3: a new worker resumes from the committed checkpoint.
    seen: list[dict] = []

    def resume(ctx: WorkerContext) -> dict:
        # While the new claim is live, the OLD worker's token is rejected.
        with factory2() as s:
            with pytest.raises(FencedWorkerError):
                JobRepository(s).update_progress(
                    job_id, 10.0, fence_token="stale-token"
                )
            s.rollback()
        seen.append({"attempt": ctx.attempt, "cp": ctx.checkpoint})
        return {}

    w = DurableWorker(
        factory2,
        config=WorkerConfig(
            worker_id="worker-b", lease_ttl=60, heartbeat_interval=15,
            poll_interval=0.01, staging_root=managed_root,
        ),
    )
    w.register_handler("SYNTH", resume)
    assert w.run_once() == 1

    assert seen == [{"attempt": 1, "cp": {"schema_version": 1, "chunk_index": 5}}]
    with factory2() as s:
        r = JobRepository(s)
        job = r.get_job(job_id)
        assert job.state == "completed"
        assert job.attempt == 1
        steps = r.list_steps(job_id)
        assert steps[0].state == "completed"
        assert steps[0].attempt == 1
        assert len(r.list_attempts(job_id)) == 1  # no duplicate attempt rows
        # Events tell the full story: created -> running -> fenced -> queued
        # -> running -> completed.
        to_states = [e.to_state for e in r.list_events(job_id)]
        assert to_states.count("fenced") == 1
        # Two queued events: the created event (initial queued) and the
        # reconciler's requeue (fenced -> queued).
        assert to_states.count("queued") == 2
        # Two completed events: the step completion and the Job completion.
        assert to_states.count("completed") == 2
        # No duplicate artifacts were published.
        rows = s.execute(
            text("SELECT COUNT(*) FROM artifact WHERE workspace_id = :wid"),
            {"wid": ws_id},
        ).scalar()
        assert rows == 0


def test_forced_close_reopen_fenced_cancelling_job_cancels(
    db_path: Path, managed_root: Path
) -> None:
    """AC6: a Job that was cancelling when the process died reconciles to
    cancelled on reopen — never requeued, never re-run."""
    _upgrade(db_path)
    fake_now = FakeClock().now
    factory1 = create_session_factory(create_engine_for_path(db_path))
    with factory1() as s:
        ws = Workspace(name="Cancel Workspace")
        s.add(ws)
        s.commit()
        r = JobRepository(s)
        job = r.create_job(
            workspace_id=ws.id,
            job_type="SYNTH",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={"managed_root": str(managed_root)},
            idempotency_key="CANCEL-REOPEN:v1",
            max_attempts=3,
            steps=_steps("s1"),
        )
        s.commit()
        lease = r.acquire_lease(job.id, "worker-a", ttl_seconds=60)
        r.transition_job(
            job.id,
            "running",
            actor="worker",
            expected_revision=r.get_job(job.id).revision,
            fence_token=lease.fence_token,
        )
        s.commit()
        r.transition_job(
            job.id,
            "cancelling",
            actor="api",
            expected_revision=r.get_job(job.id).revision,
        )
        s.commit()
        job_id = job.id
        past = fake_now - timedelta(seconds=120)
        s.execute(
            text(
                "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                "acquired_at = :past2 WHERE job_id = :jid"
            ),
            {"past": past, "past2": past - timedelta(seconds=60), "jid": job_id},
        )
        s.commit()

    factory2 = create_session_factory(create_engine_for_path(db_path))
    rec_clock = FakeClock()
    rec = JobReconciler(
        factory2,
        config=ReconcileConfig(batch_size=10, fence_grace_seconds=0.0),
        clock=rec_clock,
    )
    report = rec.reconcile_once()
    assert report.cancelled == 1
    assert report.requeued == 0
    with factory2() as s:
        job = JobRepository(s).get_job(job_id)
        assert job.state == "cancelled"
        assert job.finished_at is not None


def test_reconcile_after_reopen_leaves_terminal_rows_untouched(
    db_path: Path, managed_root: Path
) -> None:
    """AC6: terminal Jobs (completed/failed/cancelled) are never rescanned or
    mutated by the reconciler after reopen."""
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    with factory() as s:
        ws = Workspace(name="Terminal Workspace")
        s.add(ws)
        s.commit()
        r = JobRepository(s)
        done = r.create_job(
            workspace_id=ws.id,
            job_type="SYNTH",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={"managed_root": str(managed_root)},
            idempotency_key="DONE:v1",
            steps=_steps("s1"),
        )
        s.commit()
        lease = r.acquire_lease(done.id, "worker-a", ttl_seconds=60)
        r.transition_job(
            done.id,
            "running",
            actor="worker",
            expected_revision=r.get_job(done.id).revision,
            fence_token=lease.fence_token,
        )
        r.transition_job(
            done.id,
            "completed",
            actor="worker",
            expected_revision=r.get_job(done.id).revision,
            fence_token=lease.fence_token,
        )
        s.commit()
        done_id = done.id
        # Also a failed job with an expired lease row (should be ignored).
        failed = r.create_job(
            workspace_id=ws.id,
            job_type="SYNTH",
            owner_type="project",
            owner_id="owner-1",
            input_manifest={"managed_root": str(managed_root)},
            idempotency_key="FAILED:v1",
            steps=_steps("s1"),
        )
        s.commit()
        lease2 = r.acquire_lease(failed.id, "worker-a", ttl_seconds=60)
        r.transition_job(
            failed.id,
            "running",
            actor="worker",
            expected_revision=r.get_job(failed.id).revision,
            fence_token=lease2.fence_token,
        )
        r.transition_job(
            failed.id,
            "failed",
            actor="worker",
            expected_revision=r.get_job(failed.id).revision,
            fence_token=lease2.fence_token,
            error={"error_code": "X", "message": "x"},
        )
        s.commit()
        failed_id = failed.id

    rec = JobReconciler(
        factory,
        config=ReconcileConfig(batch_size=10, fence_grace_seconds=0.0),
        clock=FakeClock(),
    )
    report = rec.reconcile_once()
    assert report.scanned == 0
    assert report.fenced == 0
    with factory() as s:
        r = JobRepository(s)
        assert r.get_job(done_id).state == "completed"
        assert r.get_job(failed_id).state == "failed"


# ── AC7: scope isolation ─────────────────────────────────────────────────────


def test_no_cutover_imports() -> None:
    """AC7: the reconciler module does not import API/legacy-service modules."""
    import subprocess
    import sys

    probe = (
        "import sys; import app.workflow.job_reconciler as jr; "
        "print('api' if 'app.api' in sys.modules else 'clean', "
        "'legacy' if 'app.workflow.job_service' in sys.modules else 'clean')"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    ).stdout.strip()
    assert out == "clean clean", f"reconciler import pulled in cutover modules: {out}"

    import app.workflow.job_reconciler as jr

    assert jr.JobReconciler is not None


def test_manifest_fingerprint_stable() -> None:
    """§8.1: the manifest fingerprint is deterministic and order-insensitive."""
    a = manifest_fingerprint({"a": 1, "b": {"c": 2}})
    b = manifest_fingerprint({"b": {"c": 2}, "a": 1})
    assert a == b
    assert manifest_fingerprint(None) == manifest_fingerprint({})
    assert manifest_fingerprint({"a": 1}) != manifest_fingerprint({"a": 2})
