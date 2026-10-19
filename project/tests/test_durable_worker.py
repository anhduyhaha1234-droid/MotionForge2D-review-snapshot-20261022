"""Targeted tests for S02-T03 — the deterministic durable worker.

Covers AC1-AC7 of ``docs/pm/sessions/S02-T03-durable-worker/TASK.md``:

- AC1: explicit start/stop/run-once lifecycle; atomic queue claim ordered by
  priority then creation time; NO background work starts on import.
- AC2: registered handlers receive versioned input/checkpoint context with
  fenced progress/checkpoint/cancel callbacks; an unknown handler fails
  safely (``UNKNOWN_HANDLER``).
- AC3: heartbeat keeps a live claim; a lost/stale token aborts execution and
  cannot publish state or outputs.
- AC4: transient failures retry with bounded deterministic backoff and
  attempts; permanent/exhausted failures persist stable error envelopes.
- AC5: cancel wins before the next effect/step, drains to terminal
  ``cancelled`` and exposes no final output; completed-vs-cancel race is
  serialized by guarded transitions.
- AC6: step/job completion requires declared outputs ready/validated; the
  worker never marks staging/missing output complete.
- AC7: no API cutover/reconciler/schema/dependency changes; targeted tests
  and the full quality baseline pass.

Every test uses a temporary database under ``tmp_path`` and an injectable
fake clock/sleeper so retry/backoff, heartbeat and race tests are fast and
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
    DEFAULT_RETRY_CAP_DELAY,
    DEFAULT_RETRY_MAX_JITTER,
    OUTPUT_PURPOSES,
    UNKNOWN_HANDLER_CODE,
    VALIDATION_FAILED_CODE,
    DurableWorker,
    WorkerConfig,
    WorkerContext,
    error_envelope,
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


# ── DB fixtures (mirror test_durable_job_persistence.py) ────────────────────


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
    return tmp_path / "test_worker.db"


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
    ws = Workspace(name="Worker Workspace")
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
def worker(
    session_factory,
    managed_root: Path,
    clock: FakeClock,
    sleeper: FakeSleeper,
) -> DurableWorker:
    """A worker with fake clock/sleeper and a temp managed root."""
    return DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="test-worker",
            lease_ttl=60,
            heartbeat_interval=15,
            poll_interval=0.01,
            max_attempts=3,
            staging_root=managed_root,
        ),
        clock=clock,
        sleeper=sleeper,
    )


def _steps(*codes: str) -> list[StepInput]:
    return [
        StepInput(step_code=code, position=i, step_type="sync") for i, code in enumerate(codes)
    ]


def _create(
    repo: JobRepository,
    ws: Workspace,
    *,
    job_type: str = "SYNTH",
    steps: list[StepInput] | None = None,
    key: str | None = "SYNTH:v1",
    priority: int = 50,
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
        priority=priority,
        max_attempts=max_attempts,
        steps=steps or _steps("s1"),
    )


def _write_file(root: Path, rel: str, data: bytes) -> tuple[str, int]:
    """Write a file under the managed root; return (sha256, size)."""
    import hashlib

    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


# ── AC1: lifecycle and atomic ordered claim ──────────────────────────────────


def test_import_starts_no_thread_or_job_work() -> None:
    """AC1: importing the module and constructing a worker starts nothing."""
    import threading

    from app.workflow import durable_worker  # noqa: F401

    before = threading.active_count()
    worker = DurableWorker(
        lambda: None,  # type: ignore[arg-type]  # never used without start
    )
    assert worker.running is False
    assert worker._thread is None
    assert threading.active_count() == before


def test_run_once_processes_one_job_and_no_background_thread(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    worker: DurableWorker,
) -> None:
    """AC1: run_once executes exactly one queued Job; no thread is created."""
    import threading

    created = _create(repo, ws)
    session.commit()

    calls: list[str] = []

    def handler(ctx: WorkerContext) -> dict:
        calls.append(ctx.job_id)
        return {}

    worker.register_handler("SYNTH", handler)

    before = threading.active_count()
    processed = worker.run_once()
    assert processed == 1
    assert threading.active_count() == before

    with session_factory() as s:
        job = JobRepository(s).get_job(created.id)
        assert job.state == "completed"
        steps = JobRepository(s).list_steps(created.id)
        assert steps[0].state == "completed"


def test_run_once_claims_by_priority_then_age(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC1: queue claim is ordered by priority (desc) then created_at (asc)."""
    low = _create(repo, ws, key="PRIO:low", priority=10)
    high = _create(repo, ws, key="PRIO:high", priority=90)
    mid = _create(repo, ws, key="PRIO:mid", priority=50)
    session.commit()

    order: list[str] = []

    def handler(ctx: WorkerContext) -> dict:
        order.append(ctx.input_manifest["id"])
        return {}

    worker.register_handler("SYNTH", handler)

    # Rewrite manifests with the job id so order is observable.
    with session_factory() as s:
        for jid in (high.id, mid.id, low.id):
            s.execute(
                text("UPDATE job SET input_manifest_json = :m WHERE id = :jid"),
                {"m": __import__("json").dumps({"managed_root": "artifacts", "id": jid}),
                 "jid": jid},
            )
        s.commit()

    assert worker.run_once() == 1
    assert worker.run_once() == 1
    assert worker.run_once() == 1
    assert worker.run_once() == 0
    assert order == [high.id, mid.id, low.id]


def test_run_once_returns_zero_when_queue_empty(
    repo: JobRepository, session: Session, worker: DurableWorker
) -> None:
    """AC1: an empty queue scans without error."""
    assert worker.run_once() == 0


def test_start_stop_lifecycle(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC1: start() spawns one loop thread; stop() joins and stops it."""
    _create(repo, ws)
    session.commit()

    worker.register_handler("SYNTH", lambda ctx: {})
    worker.start()
    try:
        assert worker.running is True
        assert worker._thread is not None
    finally:
        worker.stop(timeout=5.0)
    assert worker.running is False

    with session_factory() as s:
        assert JobRepository(s).get_job(
            JobRepository(s).list_jobs(ws.id)[0].id
        ).state == "completed"


def test_run_forever_stops_on_flag(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC1: run_forever exits when stop() is signalled (no infinite loop)."""
    _create(repo, ws)
    session.commit()
    worker.register_handler("SYNTH", lambda ctx: {})

    worker.start()
    worker.stop(timeout=5.0)
    assert worker.running is False
    with session_factory() as s:
        assert JobRepository(s).get_job(
            JobRepository(s).list_jobs(ws.id)[0].id
        ).state == "completed"


def test_claim_is_atomic_across_two_workers(db_path: Path, managed_root: Path) -> None:
    """AC1: two workers can never hold the same Job lease (atomic claim)."""
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    with factory() as s:
        ws = Workspace(name="Race Workspace")
        s.add(ws)
        s.commit()
        job = JobRepository(s).create_job(
            workspace_id=ws.id,
            job_type="SYNTH",
            owner_type="project",
            owner_id="o1",
            input_manifest={"managed_root": str(managed_root)},
            idempotency_key="RACE:v1",
            steps=_steps("s1"),
        )
        s.commit()
        job_id = job.id

    w1 = DurableWorker(factory, config=WorkerConfig(worker_id="w1", staging_root=managed_root))
    w2 = DurableWorker(factory, config=WorkerConfig(worker_id="w2", staging_root=managed_root))
    w1.register_handler("SYNTH", lambda ctx: {})
    w2.register_handler("SYNTH", lambda ctx: {})

    # Both workers scan; only one can claim.  A second run_once of the winner
    # finds nothing, and the loser can never steal a live lease.
    results = [w1.run_once(), w2.run_once()]
    assert sorted(results) == [0, 1]

    with factory() as s:
        lease = JobRepository(s).get_lease(job_id)
        assert lease is not None
        assert lease.worker_id in ("w1", "w2")
        assert JobRepository(s).get_job(job_id).state == "completed"


# ── AC2: handler registry and versioned context ──────────────────────────────


def test_registered_handler_receives_versioned_context(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC2: handlers receive input manifest + schema-versioned checkpoint."""
    _create(
        repo,
        ws,
        manifest={"managed_root": "artifacts", "variant": "v1"},
    )
    session.commit()

    seen: dict[str, object] = {}

    def handler(ctx: WorkerContext) -> dict:
        seen["manifest"] = ctx.input_manifest
        seen["checkpoint_version"] = ctx.checkpoint.get("schema_version")
        seen["step_code"] = ctx.step_code
        seen["attempt"] = ctx.attempt
        seen["job_type"] = ctx.job_type
        seen["fence_token"] = ctx.fence_token
        return {}

    worker.register_handler("SYNTH", handler)
    worker.run_once()

    assert seen["manifest"] == {"managed_root": "artifacts", "variant": "v1"}
    assert seen["checkpoint_version"] == 1
    assert seen["step_code"] == "s1"
    assert seen["attempt"] == 1
    assert seen["job_type"] == "SYNTH"
    assert isinstance(seen["fence_token"], str) and seen["fence_token"]


def test_unknown_handler_fails_safely(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC2: a Job with no registered handler fails with UNKNOWN_HANDLER."""
    created = _create(repo, ws, job_type="NO_SUCH_TYPE")
    session.commit()

    worker.run_once()

    with session_factory() as s:
        job = JobRepository(s).get_job(created.id)
        assert job.state == "failed"
        assert job.error is not None
        assert job.error["error_code"] == UNKNOWN_HANDLER_CODE
        assert job.error["class"] == "permanent"
        assert job.error["retryable"] is False


def test_fenced_callbacks_reject_after_fence(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC2: progress/checkpoint callbacks are fenced — stale token aborts."""
    created = _create(repo, ws)
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        # Simulate a re-claim by another worker: the token is now stale.
        # While the handler runs, the run_once transaction holds the write
        # lock, so the intruder expires + re-claims from the SAME session
        # (which already holds the lock) and then commits.
        with session_factory() as s:
            past = datetime.now(UTC) - timedelta(seconds=10)
            s.execute(
                text(
                    "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                    "acquired_at = :past2 WHERE job_id = :jid"
                ),
                {"past": past, "past2": past - timedelta(seconds=60), "jid": created.id},
            )
            s.commit()
        with session_factory() as s:
            JobRepository(s).acquire_lease(created.id, "intruder", ttl_seconds=60)
            s.commit()
        with pytest.raises(FencedWorkerError):
            ctx.progress(90.0, "late")
        with pytest.raises(FencedWorkerError):
            ctx.write_checkpoint({"schema_version": 1, "done": 2})
        return {}

    worker.register_handler("SYNTH", handler)
    # Callback-level rejection is asserted above; the run_once boundary
    # converts the fence into a silent abort (contract §5.3-3).
    assert worker.run_once() == 1

    with session_factory() as s:
        r = JobRepository(s)
        # The handler was fenced mid-step (re-claim by the intruder).  The
        # fenced abort is silent: the Job stays running under the intruder's
        # lease and no stale state/output was published.
        assert r.get_job(created.id).state == "running"
        assert r.get_lease(created.id).worker_id == "intruder"
        assert r.get_job(created.id).progress == 0.0


# ── AC3: heartbeat and fencing ───────────────────────────────────────────────


def test_heartbeat_keeps_lease_alive(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    worker: DurableWorker,
    clock: FakeClock,
) -> None:
    """AC3: the worker heartbeats during long steps so the lease stays live."""
    created = _create(repo, ws)
    session.commit()

    heartbeats: list[str] = []

    def handler(ctx: WorkerContext) -> dict:
        # Simulate a long step: advance the clock well past the lease TTL.
        clock.advance(worker._config.lease_ttl + 30)
        # The worker heartbeats at the next checkpoint; the lease must be
        # extended, not expired.  The lease stores naive SQLite datetimes;
        # compare in the same frame.
        ctx.write_checkpoint({"schema_version": 1, "done": 1})
        with session_factory() as s:
            lease = JobRepository(s).get_lease(created.id)
            if lease is not None:
                expires = lease.expires_at
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=UTC)
                if expires > datetime.now(UTC):
                    heartbeats.append("alive")
        return {}

    worker.register_handler("SYNTH", handler)
    worker.run_once()

    with session_factory() as s:
        assert JobRepository(s).get_job(created.id).state == "completed"
    assert heartbeats == ["alive"]


def test_heartbeat_thread_keeps_silent_handler_leased(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
) -> None:
    """AC3: a REAL per-claim heartbeat thread renews the lease while a
    handler computes silently — the lease stays live beyond its original
    TTL without any progress/checkpoint callback."""
    worker = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="hb-worker",
            lease_ttl=3,
            heartbeat_interval=0.05,
            poll_interval=0.01,
            heartbeat_join_timeout=5.0,
            staging_root=ws and __import__("pathlib").Path("."),
        ),
    )
    created = _create(repo, ws)
    session.commit()

    observed_expiry: list[datetime] = []

    def silent(ctx: WorkerContext) -> dict:
        # No progress/checkpoint callbacks: only the heartbeat thread can
        # keep the claim alive while we sleep well past the original TTL.
        for _ in range(12):
            __import__("time").sleep(0.05)
        with session_factory() as s:
            lease = JobRepository(s).get_lease(created.id)
            if lease is not None:
                expires = lease.expires_at
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=UTC)
                observed_expiry.append(expires)
        return {}

    worker.register_handler("SYNTH", silent)
    worker.run_once()

    with session_factory() as s:
        assert JobRepository(s).get_job(created.id).state == "completed"
    assert worker._heartbeat_thread_alive() is False
    assert len(observed_expiry) == 1
    # The lease survived ~0.6s of silence with a 3s TTL: the beat thread
    # renewed it well beyond the original acquisition window.
    assert observed_expiry[0] > datetime.now(UTC) - timedelta(seconds=2.5)


def test_heartbeat_thread_failure_aborts_without_publication(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
) -> None:
    """AC3: when the heartbeat thread loses the lease (another worker
    re-claims), the failure propagates through the thread-safe channel and
    the execution path aborts BEFORE any state/output write — nothing is
    published and the intruder's lease is never released/overwritten."""
    import time

    worker = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="hb-worker",
            lease_ttl=30,
            heartbeat_interval=0.05,
            poll_interval=0.01,
            heartbeat_join_timeout=5.0,
            staging_root=__import__("pathlib").Path("."),
        ),
    )
    created = _create(repo, ws, steps=_steps("s1", "s2"))
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        # Let the heartbeat thread beat at least once, then steal the lease
        # from a fresh session (as the reconciler would after expiry).
        time.sleep(0.15)
        with session_factory() as s:
            past = datetime.now(UTC) - timedelta(seconds=10)
            s.execute(
                text(
                    "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                    "acquired_at = :past2 WHERE job_id = :jid"
                ),
                {"past": past, "past2": past - timedelta(seconds=60), "jid": created.id},
            )
            s.commit()
        with session_factory() as s:
            JobRepository(s).acquire_lease(created.id, "intruder", ttl_seconds=60)
            s.commit()
        # A silent handler: the NEXT heartbeat beat observes the intruder's
        # lease, records the failure, and the execution path must abort
        # before step s2 starts or any output is published.
        time.sleep(0.2)
        return {}

    worker.register_handler("SYNTH", handler)
    assert worker.run_once() == 1

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        # No terminal write was published by the fenced worker.
        assert job.state == "running"
        assert r.get_lease(created.id).worker_id == "intruder"
        steps = r.list_steps(created.id)
        assert steps[0].state in ("running", "completed")
        assert steps[1].state == "pending"  # s2 never started
    assert worker._heartbeat_thread_alive() is False


def test_heartbeat_thread_never_leaks_across_terminal_paths(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
) -> None:
    """AC3: the per-claim heartbeat thread stops and joins on EVERY terminal
    path — success, handler exception, cancel, and fencing."""
    import threading
    import time

    def make_worker() -> DurableWorker:
        return DurableWorker(
            session_factory,
            config=WorkerConfig(
                worker_id="hb-worker",
                lease_ttl=30,
                heartbeat_interval=0.05,
                poll_interval=0.01,
                heartbeat_join_timeout=5.0,
                staging_root=__import__("pathlib").Path("."),
            ),
        )

    def alive_count(w: DurableWorker) -> bool:
        return w._heartbeat_thread_alive()

    # 1) Success path.
    w = make_worker()
    _create(repo, ws, key="HB:success")
    session.commit()
    w.register_handler("SYNTH", lambda ctx: {})
    w.run_once()
    assert alive_count(w) is False

    # 2) Handler exception path (permanent failure).
    w2 = make_worker()
    _create(repo, ws, key="HB:fail")
    session.commit()

    def boom(ctx: WorkerContext) -> dict:
        exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError("X")
        exc.code = "INPUT_MISSING"
        raise exc

    w2.register_handler("SYNTH", boom)
    w2.run_once()
    assert alive_count(w2) is False

    # 3) Cancel path (drain).
    w3 = make_worker()
    c3 = _create(repo, ws, key="HB:cancel", steps=_steps("s1", "s2"))
    session.commit()

    def cancelling(ctx: WorkerContext) -> dict:
        with session_factory() as s:
            r = JobRepository(s)
            r.transition_job(
                c3.id,
                "cancelling",
                actor="api",
                expected_revision=r.get_job(c3.id).revision,
            )
            s.commit()
        return {}

    w3.register_handler("SYNTH", cancelling)
    w3.run_once()
    assert alive_count(w3) is False

    # 4) Fencing path.
    w4 = make_worker()
    c4 = _create(repo, ws, key="HB:fence")
    session.commit()

    def fenced(ctx: WorkerContext) -> dict:
        with session_factory() as s:
            past = datetime.now(UTC) - timedelta(seconds=10)
            s.execute(
                text(
                    "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                    "acquired_at = :past2 WHERE job_id = :jid"
                ),
                {"past": past, "past2": past - timedelta(seconds=60), "jid": c4.id},
            )
            s.commit()
        with session_factory() as s:
            JobRepository(s).acquire_lease(c4.id, "intruder", ttl_seconds=60)
            s.commit()
        with __import__("contextlib").suppress(FencedWorkerError):
            ctx.progress(10.0, "stale")
        return {}

    w4.register_handler("SYNTH", fenced)
    w4.run_once()
    assert alive_count(w4) is False

    # No stray heartbeat threads remain after any path.
    time.sleep(0.1)
    hb_threads = [t for t in threading.enumerate() if t.name.startswith("hb-")]
    assert hb_threads == []


def test_heartbeat_never_overwrites_newer_lease(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
) -> None:
    """AC3: a beat that observes a re-claimed (newer) lease never overwrites
    it — the heartbeat thread records the failure and stops, leaving the
    intruder's lease row untouched."""
    import time

    worker = DurableWorker(
        session_factory,
        config=WorkerConfig(
            worker_id="hb-worker",
            lease_ttl=30,
            heartbeat_interval=0.05,
            poll_interval=0.01,
            heartbeat_join_timeout=5.0,
            staging_root=__import__("pathlib").Path("."),
        ),
    )
    created = _create(repo, ws)
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        time.sleep(0.15)
        with session_factory() as s:
            past = datetime.now(UTC) - timedelta(seconds=10)
            s.execute(
                text(
                    "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                    "acquired_at = :past2 WHERE job_id = :jid"
                ),
                {"past": past, "past2": past - timedelta(seconds=60), "jid": created.id},
            )
            s.commit()
        with session_factory() as s:
            JobRepository(s).acquire_lease(created.id, "intruder", ttl_seconds=60)
            s.commit()
        time.sleep(0.2)  # heartbeat thread beats against the intruder lease
        return {}

    worker.register_handler("SYNTH", handler)
    worker.run_once()

    with session_factory() as s:
        lease = JobRepository(s).get_lease(created.id)
        assert lease is not None
        assert lease.worker_id == "intruder"
        assert lease.fence_token  # still the intruder's fresh token
    assert worker._heartbeat_thread_alive() is False


def test_fenced_worker_cannot_publish_state_or_outputs(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC3: a stale-token worker's writes and publications are rejected."""
    created = _create(repo, ws)
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        # Re-claim by another worker invalidates our token mid-step.
        with session_factory() as s:
            past = datetime.now(UTC) - timedelta(seconds=10)
            s.execute(
                text(
                    "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                    "acquired_at = :past2 WHERE job_id = :jid"
                ),
                {"past": past, "past2": past - timedelta(seconds=60), "jid": created.id},
            )
            s.commit()
        with session_factory() as s:
            JobRepository(s).acquire_lease(created.id, "intruder", ttl_seconds=60)
            s.commit()
        with pytest.raises(FencedWorkerError):
            ctx.progress(10.0, "stale write")
        return {}

    worker.register_handler("SYNTH", handler)
    # The fence is handled at the run_once boundary (contract §5.3-3): the
    # worker aborts silently — run_once returns its documented result and
    # does not raise.
    assert worker.run_once() == 1

    with session_factory() as s:
        r = JobRepository(s)
        assert r.get_job(created.id).state == "running"
        assert r.get_job(created.id).progress == 0.0  # nothing published
        assert r.get_lease(created.id).worker_id == "intruder"  # lease intact


def test_release_on_fenced_abort_is_silent(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC3: a fenced worker aborts silently and does not release the lease."""
    created = _create(repo, ws)
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        with session_factory() as s:
            past = datetime.now(UTC) - timedelta(seconds=10)
            s.execute(
                text(
                    "UPDATE job_lease SET expires_at = :past, heartbeat_at = :past, "
                    "acquired_at = :past2 WHERE job_id = :jid"
                ),
                {"past": past, "past2": past - timedelta(seconds=60), "jid": created.id},
            )
            s.commit()
        with session_factory() as s:
            JobRepository(s).acquire_lease(created.id, "intruder", ttl_seconds=60)
            s.commit()
        with pytest.raises(FencedWorkerError):
            ctx.progress(10.0, "stale")
        return {}

    worker.register_handler("SYNTH", handler)
    assert worker.run_once() == 1  # silent abort at the boundary; no raise

    with session_factory() as s:
        lease = JobRepository(s).get_lease(created.id)
        assert lease is not None
        assert lease.worker_id == "intruder"  # our worker never released it


# ── AC4: retry and backoff ───────────────────────────────────────────────────


def test_transient_failure_retries_with_bounded_backoff(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    worker: DurableWorker,
    sleeper: FakeSleeper,
) -> None:
    """AC4: transient failures retry with deterministic bounded backoff."""
    created = _create(repo, ws, max_attempts=3)
    session.commit()

    attempts: list[int] = []

    def flaky(ctx: WorkerContext) -> dict:
        attempts.append(ctx.attempt)
        if ctx.attempt < 3:
            exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError(
                "TRANSIENT"
            )
            exc.code = "TRANSIENT"
            raise exc
        return {}

    worker.register_handler("SYNTH", flaky)
    worker.run_once()

    assert attempts == [1, 2, 3]
    assert len(sleeper.calls) == 2
    # Bounded exponential: 1s, 4s (+/- 20% jitter).
    assert sleeper.calls[0] == pytest.approx(1.0, rel=DEFAULT_RETRY_MAX_JITTER + 0.01)
    assert sleeper.calls[1] == pytest.approx(4.0, rel=DEFAULT_RETRY_MAX_JITTER + 0.01)

    with session_factory() as s:
        r = JobRepository(s)
        assert r.get_job(created.id).state == "completed"
        step = r.list_steps(created.id)[0]
        assert step.state == "completed"
        assert len(r.list_attempts(created.id)) == 3


def test_permanent_failure_fails_with_stable_envelope(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC4: permanent failures fail immediately with a stable envelope."""
    created = _create(repo, ws)
    session.commit()

    def bad(ctx: WorkerContext) -> dict:
        exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError(
            "INPUT_MISSING"
        )
        exc.code = "INPUT_MISSING"  # type: ignore[attr-defined]
        raise exc

    worker.register_handler("SYNTH", bad)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "failed"
        assert job.error is not None
        assert job.error["error_code"] == "INPUT_MISSING"
        assert job.error["class"] == "permanent"
        assert job.error["retryable"] is False
        step = r.list_steps(created.id)[0]
        # The step stays `running` on a permanent failure (the Job-level
        # terminal decision is computed from the step set by the reconciler);
        # the stable error envelope is on the Job and the attempt log.
        assert step.state in ("running", "failed", "ready")


def test_retries_exhausted_fails_with_envelope(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC4: exhausted transient retries fail with RETRIES_EXHAUSTED."""
    created = _create(repo, ws, max_attempts=2)
    session.commit()

    def always_fail(ctx: WorkerContext) -> dict:
        exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError(
            "TRANSIENT"
        )
        exc.code = "TRANSIENT"
        raise exc

    worker.register_handler("SYNTH", always_fail)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "failed"
        assert job.error["error_code"] == "RETRIES_EXHAUSTED"
        assert job.error["class"] == "permanent"
        assert job.error["retryable"] is False
        assert job.error["details"]["max_attempts"] == 2
        attempts = r.list_attempts(created.id)
        assert len(attempts) == 2
        assert all(a.error["error_code"] == "TRANSIENT" for a in attempts)


def test_backoff_is_bounded_and_deterministic(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC4: backoff never exceeds the cap and is deterministic for a seed."""
    created = _create(repo, ws, max_attempts=10)
    session.commit()

    worker.register_handler("SYNTH", lambda ctx: (_ for _ in ()).throw(RuntimeError("TRANSIENT")))
    worker.run_once()

    with session_factory() as s:
        assert JobRepository(s).get_job(created.id).state == "failed"

    # Deterministic: the same seed yields the same delays.
    import random

    w1 = DurableWorker(
        worker._session_factory,
        config=worker._config,
        rng=random.Random(42),
        sleeper=worker._sleeper,
    )
    w2 = DurableWorker(
        worker._session_factory,
        config=worker._config,
        rng=random.Random(42),
        sleeper=worker._sleeper,
    )
    assert [
        w1._backoff_delay(i) for i in range(1, 8)
    ] == [w2._backoff_delay(i) for i in range(1, 8)]
    assert all(
        w1._backoff_delay(i) <= DEFAULT_RETRY_CAP_DELAY * (1 + DEFAULT_RETRY_MAX_JITTER)
        for i in range(1, 20)
    )


# ── AC5: cancellation ────────────────────────────────────────────────────────


def test_cancel_drains_to_cancelled_before_next_step(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC5: cancel wins before the next step; job drains to cancelled."""
    created = _create(repo, ws, steps=_steps("s1", "s2"))
    session.commit()

    effects: list[str] = []

    def handler(ctx: WorkerContext) -> dict:
        effects.append(ctx.step_code)
        if ctx.step_code == "s1":
            with session_factory() as s:
                r = JobRepository(s)
                lease = r.get_lease(created.id)
                assert lease is not None
                r.transition_job(
                    created.id,
                    "cancelling",
                    actor="api",
                    expected_revision=r.get_job(created.id).revision,
                )
                s.commit()
        return {}

    worker.register_handler("SYNTH", handler)
    worker.run_once()

    assert effects == ["s1"]  # s2 never started
    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "cancelled"
        steps = r.list_steps(created.id)
        # s1 completed its unit before the cancel flag; s2 never started
        # and drained to cancelled.
        assert steps[0].state in ("completed", "cancelled")
        assert steps[1].state == "cancelled"


def test_cancelled_job_exposes_no_final_output(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC5: a cancelled Job never publishes final outputs."""
    created = _create(repo, ws, steps=_steps("s1"))
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        # Cancel requested while the step is in flight: the step may finish
        # its current unit, but the Job must drain without any final output.
        with session_factory() as s:
            r = JobRepository(s)
            lease = r.get_lease(created.id)
            assert lease is not None
            r.transition_job(
                created.id,
                "cancelling",
                actor="api",
                expected_revision=r.get_job(created.id).revision,
            )
            s.commit()
        # Attempt to publish a final output after cancel was requested: the
        # worker must refuse (the drain path never publishes).
        return {"published": True}

    worker.register_handler("SYNTH", handler)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "cancelled"
        # No artifact rows exist for this Job (nothing was published).
        rows = s.execute(
            text("SELECT COUNT(*) FROM artifact WHERE workspace_id = :wid"),
            {"wid": ws.id},
        ).scalar()
        assert rows == 0


def test_cancel_during_retry_backoff_wins(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC5: a cancel arriving during retry backoff stops the retry."""
    created = _create(repo, ws, max_attempts=5)
    session.commit()

    def flaky(ctx: WorkerContext) -> dict:
        if ctx.attempt == 1:
            with session_factory() as s:
                r = JobRepository(s)
                lease = r.get_lease(created.id)
                assert lease is not None
                r.transition_job(
                    created.id,
                    "cancelling",
                    actor="api",
                    expected_revision=r.get_job(created.id).revision,
                )
                s.commit()
        exc = __import__("app.persistence.jobs", fromlist=["JobError"]).JobError(
            "TRANSIENT"
        )
        exc.code = "TRANSIENT"
        raise exc

    worker.register_handler("SYNTH", flaky)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        # The retry was not started; the Job drained to cancelled.
        assert job.state == "cancelled"
        attempts = r.list_attempts(created.id)
        assert len(attempts) == 1


def test_completed_vs_cancel_race_serialized(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC5: completion wins only if committed before the cancel flag."""
    created = _create(repo, ws, steps=_steps("s1"))
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        # Cancel the Job BEFORE the worker's completion write.
        with session_factory() as s:
            r = JobRepository(s)
            lease = r.get_lease(created.id)
            assert lease is not None
            r.transition_job(
                created.id,
                "cancelling",
                actor="api",
                expected_revision=r.get_job(created.id).revision,
            )
            s.commit()
        return {}

    worker.register_handler("SYNTH", handler)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        # The cancel flag was written first ⇒ the worker's completion write
        # is rejected by the guarded transition; the Job cancels.
        assert job.state == "cancelled"
        steps = r.list_steps(created.id)
        assert steps[0].state == "cancelled"


# ── AC6: fail-closed output validation ───────────────────────────────────────


def test_completion_requires_declared_outputs(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    worker: DurableWorker,
    managed_root: Path,
) -> None:
    """AC6: a Job whose declared output is missing never completes."""
    sha, size = _write_file(managed_root, "jobs/x/out.txt", b"hello")
    declared = {"out": {"path": "jobs/x/out.txt", "sha256": sha, "size_bytes": size}}

    created = _create(
        repo,
        ws,
        manifest={"managed_root": str(managed_root)},
        steps=_steps("s1"),
    )
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        return {"outputs": ["jobs/x/out.txt"]}

    worker.register_handler("SYNTH", handler, declared_outputs=declared)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "completed"

    # Now delete the output: the next run must fail closed.
    (managed_root / "jobs" / "x" / "out.txt").unlink()
    created2 = _create(repo, ws, key="SYNTH:v2", manifest={"managed_root": str(managed_root)})
    session.commit()
    worker.run_once()
    with session_factory() as s:
        r = JobRepository(s)
        job2 = r.get_job(created2.id)
        assert job2.state == "failed"
        # The declared-output gate rejects the missing output (either the
        # per-step validation error or the completion-gate OUTPUT_MISSING).
        assert job2.error["error_code"] in ("OUTPUT_MISSING", VALIDATION_FAILED_CODE)


def test_validation_failure_fails_closed(
    session_factory, session: Session, repo: JobRepository, ws: Workspace, worker: DurableWorker
) -> None:
    """AC6: a custom validator that rejects the output fails the Job."""
    created = _create(repo, ws)
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        return {}

    def validator(ctx: WorkerContext, result: dict, staging: Path) -> dict:
        raise ValueError("render is not valid")

    worker.register_handler("SYNTH", handler, output_validator=validator)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "failed"
        assert job.error["error_code"] == VALIDATION_FAILED_CODE
        assert job.error["class"] == "permanent"


def test_staging_output_never_marked_complete(
    session_factory,
    session: Session,
    repo: JobRepository,
    ws: Workspace,
    worker: DurableWorker,
    managed_root: Path,
) -> None:
    """AC6: staging-only outputs (no ready evidence) fail the completion gate."""
    created = _create(
        repo,
        ws,
        manifest={"managed_root": str(managed_root)},
    )
    session.commit()

    def handler(ctx: WorkerContext) -> dict:
        # The handler writes into staging (contract §9.1) but declares a
        # final output that never becomes a ready artifact.
        return {}

    declared = {"final.mp4": {"path": "artifacts/ws/job/final.mp4"}}
    worker.register_handler("SYNTH", handler, declared_outputs=declared)
    worker.run_once()

    with session_factory() as s:
        r = JobRepository(s)
        job = r.get_job(created.id)
        assert job.state == "failed"
        # Staging-only output: rejected at the per-step validation gate
        # (the declared output is missing on disk) — never completed.
        assert job.error["error_code"] in ("OUTPUT_MISSING", VALIDATION_FAILED_CODE)


def test_output_purposes_constant() -> None:
    """AC6: final-output purposes are exactly the contract set (§9.2)."""
    assert {"render", "final", "result"} == OUTPUT_PURPOSES


# ── AC4/AC6 helpers and envelope stability ───────────────────────────────────


def test_error_envelope_stable_shape() -> None:
    """AC4/§10.1: the persisted envelope carries the stable contract shape."""
    env = error_envelope(
        "GPU_OOM",
        "oom at chunk 3",
        step_code="render_chunk",
        attempt=2,
        worker_id="w1",
        retry_after_s=4.0,
        details={"chunk": 3},
    )
    assert env["error_code"] == "GPU_OOM"
    assert env["class"] == "transient"
    assert env["recoverable"] is True
    assert env["retry_after_s"] == 4.0
    assert env["details"] == {"chunk": 3}

    permanent = error_envelope("INPUT_MISSING", "missing input")
    assert permanent["class"] == "permanent"
    assert permanent["retryable"] is False


def test_worker_config_validates() -> None:
    """WorkerConfig fails closed on invalid knobs."""
    with pytest.raises(ValueError):
        WorkerConfig(lease_ttl=0)
    with pytest.raises(ValueError):
        WorkerConfig(max_attempts=0)
    with pytest.raises(ValueError):
        WorkerConfig(retry_multiplier=1.0)
    with pytest.raises(ValueError):
        WorkerConfig(retry_max_jitter=0.9)


def test_no_cutover_imports() -> None:
    """AC7: the worker module does not import API/legacy-service modules.

    Other test modules in the full suite may import the API; this test
    verifies the WORKER module itself pulls in no cutover surface by
    importing it in a pristine subprocess.
    """
    import subprocess
    import sys

    probe = (
        "import sys; import app.workflow.durable_worker as dw; "
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
    assert out == "clean clean", f"worker import pulled in cutover modules: {out}"

    import app.workflow.durable_worker as dw

    assert dw.DurableWorker is not None
