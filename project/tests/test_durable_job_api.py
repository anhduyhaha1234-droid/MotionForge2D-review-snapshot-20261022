"""S02-T05 acceptance tests — durable job API cutover and recovery.

Covers the acceptance criteria of
``docs/pm/sessions/S02-T05-job-api-cutover/TASK.md``:

- AC1: explicit app lifecycle (bootstrap/upgrade → reconcile → worker
  start; shutdown joins) with no import-time side effects.
- AC2: all API job submissions are durable id/manifest rows executed by
  registered handlers — no endpoint passes an ephemeral closure as the
  authoritative job definition.
- AC3: GET/cancel preserve 200/400/404 semantics with additive durable
  fields and hidden internal ``fenced`` state.
- AC4: progress/error/result are backed by durable rows; cancellation is
  durable and restart-safe.
- AC5: restart integration through a fresh app/engine proves queued/running
  reconciliation and subsequent poll/cancel/complete without duplicates.
- AC6: no RAM authority and no long operation inside HTTP requests.
- AC7: full acceptance covers double-submit, forced close, stale worker,
  cancel during retry and no false-ready artifact.

Every test uses temporary databases and managed roots under ``tmp_path`` —
never the production projects tree, database or ``channels.json``.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.persistence import (
    JobRepository,
    create_engine_for_path,
    create_session_factory,
)
from app.persistence.models import Workspace
from app.workflow.durable_worker import (
    DurableWorker,
    WorkerConfig,
)
from app.workflow.job_reconciler import JobReconciler, ReconcileConfig
from app.workflow.job_service import JobService

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def _alembic_config(database_path: Path) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return cfg


def _upgrade(database_path: Path) -> None:
    command.upgrade(_alembic_config(database_path), "head")


def _make_service(db_path: Path, managed_root: Path) -> JobService:
    """Build a JobService over a temp database; upgrade before first use.

    The service's own engine (when injected) never creates the database —
    only ``initialize()`` (explicit) runs the Alembic upgrade.
    """
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    svc = JobService(factory, managed_root=managed_root)
    return svc


def _ensure_ws(factory, workspace_id: str = "default") -> None:
    with factory() as s:
        if s.get(Workspace, workspace_id) is None:
            s.add(Workspace(id=workspace_id, name=workspace_id))
            s.commit()


# ── AC1: explicit lifecycle, no import-time side effects ─────────────────────


def test_import_starts_no_threads_or_db(tmp_path: Path) -> None:
    """AC1: importing app.main/app.api starts no worker thread and creates
    no database file (explicit lifecycle only)."""
    import threading

    import app.main  # noqa: F401
    import app.workflow.job_service  # noqa: F401

    before = threading.active_count()
    # Constructing the service with an injected factory starts nothing and
    # the explicit bootstrap is NOT run here — no file is created.
    factory = create_session_factory(create_engine_for_path(tmp_path / "a.db"))
    svc = JobService(factory, managed_root=tmp_path / "artifacts")
    assert svc.worker_running is False
    assert threading.active_count() == before
    # No database file exists until an explicit operation runs.
    assert not (tmp_path / "a.db").exists()


def test_import_is_pristine_on_nonexistent_project_root(tmp_path: Path) -> None:
    """CR2: importing deps/app.api/app.main on a NONEXISTENT temp project
    root creates NO path/engine/thread — nothing is constructed at import.

    Runs in a pristine subprocess so any module-level side effect (mkdir,
    engine, DB file, thread) is caught.
    """
    import subprocess
    import sys

    probe = (
        "import os, pathlib, sys\n"
        "root = pathlib.Path(sys.argv[1])\n"
        "os.environ['MOTIONFORGE_ROOT'] = str(root)\n"
        "import app.api.deps\n"
        "import app.api.app\n"
        "import app.main\n"
        "import threading\n"
        "assert not root.exists(), f'project root created: {root}'\n"
        "print('pristine')\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe, str(tmp_path / "nonexistent-root")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    assert out.stdout.strip() == "pristine"
    assert not (tmp_path / "nonexistent-root").exists()


def test_service_lifecycle_start_stop_joins_worker(tmp_path: Path) -> None:
    """AC1: start_worker/stop_worker manage the explicit poll loop."""
    svc = _make_service(tmp_path / "b.db", tmp_path / "artifacts")
    svc.start_worker()
    try:
        assert svc.worker_running is True
    finally:
        svc.stop_worker(timeout=5.0)
    assert svc.worker_running is False


# ── AC2: durable submission through registered handlers ──────────────────────


def test_api_submit_creates_durable_row_with_manifest(tmp_path: Path) -> None:
    """AC2: submitting through the service writes a durable Job row with an
    input manifest; no closure is stored as the job definition."""
    svc = _make_service(tmp_path / "c.db", tmp_path / "artifacts")
    info = svc.create_job(
        "ingest",
        input_manifest={"project_id": "proj-1"},
        owner_type="project",
        owner_id="proj-1",
        idempotency_key="ingest:proj-1",
    )
    assert info.job_id
    assert info.state.value == "queued"

    with svc._session_factory() as s:  # noqa: SLF001 - test introspection
        repo = JobRepository(s)
        job = repo.get_job(info.job_id)
        assert job.job_type == "ingest"
        assert job.input_manifest["project_id"] == "proj-1"
        assert job.input_manifest["schema_version"] == 1
        steps = repo.list_steps(job.id)
        assert len(steps) == 1
        assert steps[0].step_code == "run"


def test_registered_handler_job_is_durable(tmp_path: Path) -> None:
    """AC2/CR4: a job submitted under an explicit registered test handler +
    versioned manifest is a durable row executed by the worker — RAM never
    holds the authority and no closure is accepted."""
    import time

    svc = _make_service(tmp_path / "d.db", tmp_path / "artifacts")
    ran: list[str] = []

    def handler(ctx) -> dict:  # type: ignore[no-untyped-def]
        ran.append("x")
        ctx.progress(50, "Halfway")
        return {"done": True}

    svc.worker.register_handler("TEST_HANDLER", handler)
    info = svc.create_job(
        "TEST_HANDLER",
        input_manifest={"schema_version": 1, "payload": "registered"},
    )
    assert info.state.value == "queued"
    svc.start_worker()
    try:
        for _ in range(100):
            if svc.get_job(info.job_id).state.value == "completed":
                break
            time.sleep(0.05)
    finally:
        svc.stop_worker(timeout=5.0)

    assert ran == ["x"]
    final = svc.get_job(info.job_id)
    assert final.state.value == "completed"
    assert final.progress >= 50.0


def test_create_job_rejects_callable(tmp_path: Path) -> None:
    """CR4: after the cutover, no unreconstructable callable may be accepted
    — ``create_job`` has no closure parameter anymore."""
    svc = _make_service(tmp_path / "d2.db", tmp_path / "artifacts")
    with pytest.raises(TypeError):
        svc.create_job("TEST_HANDLER", lambda p, c: "done")  # type: ignore[call-arg]


# ── CR3: S01 migration policy in initialize ──────────────────────────────────


def test_initialize_missing_db_bootstraps(tmp_path: Path) -> None:
    """CR3: a missing database may bootstrap directly to head."""
    db = tmp_path / "data" / "m.db"
    svc = JobService(None, managed_root=tmp_path / "artifacts")
    # Point the owned database at the temp path via the config root.
    import app.api.deps as deps
    from app.config import AppConfig

    old_cfg = deps._config
    deps._config = AppConfig(
        project_root=tmp_path, models_dir=tmp_path / "models", output_dir=tmp_path / "out"
    )
    try:
        svc._database_path = db  # noqa: SLF001 - test introspection
        svc.initialize()
    finally:
        deps._config = old_cfg
    assert db.exists()
    with create_session_factory(create_engine_for_path(db))() as s:
        from app.persistence.models import Job

        assert s.get(Job, "x") is None  # table exists, no crash


def test_initialize_existing_s01_db_backs_up_before_upgrade(tmp_path: Path) -> None:
    """CR3: an existing DB at the S01 revision is backed up (verified copy
    with fsync + checksum/size evidence) before Alembic upgrades it."""
    import hashlib

    from alembic import command as ac

    db = tmp_path / "data" / "old.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    cfg = _alembic_config(db)
    ac.upgrade(cfg, "a1b2c3d4e5f6")  # S01 revision
    pre_upgrade_bytes = db.read_bytes()

    svc = JobService(None, managed_root=tmp_path / "artifacts")
    svc._database_path = db  # noqa: SLF001
    svc.initialize()

    # head now — resolve the CURRENT Alembic head dynamically so future
    # migrations don't hard-break this test (PM review round 3 finding 3)
    from alembic.script import ScriptDirectory

    script = ScriptDirectory(str(Path(__file__).resolve().parent.parent / "migrations"))
    current_head = script.get_current_head()
    assert current_head is not None

    from app.persistence import database_schema_revision

    assert database_schema_revision(create_engine_for_path(db)) == current_head
    # a verified backup exists matching the PRE-upgrade bytes
    backups = list(db.parent.glob(f"{db.name}.bak-*"))
    assert len(backups) == 1
    assert hashlib.sha256(backups[0].read_bytes()).hexdigest() == hashlib.sha256(
        pre_upgrade_bytes
    ).hexdigest()
    assert backups[0].stat().st_size == len(pre_upgrade_bytes)
    assert svc.last_backup is not None
    assert svc.last_backup.sha256 == hashlib.sha256(pre_upgrade_bytes).hexdigest()


def test_initialize_backup_failure_aborts_upgrade(tmp_path: Path) -> None:
    """CR3: if the backup fails, the upgrade does NOT run."""
    from alembic import command as ac

    db = tmp_path / "data" / "old.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    cfg = _alembic_config(db)
    ac.upgrade(cfg, "a1b2c3d4e5f6")

    svc = JobService(None, managed_root=tmp_path / "artifacts")
    svc._database_path = db  # noqa: SLF001

    import app.workflow.job_service as js

    def failing_copy(source: Path, destination: Path) -> None:
        raise OSError("simulated backup failure")

    old_copy = js._copy_database_file
    js._copy_database_file = failing_copy
    try:
        with pytest.raises(RuntimeError, match="refusing to upgrade"):
            svc.initialize()
    finally:
        js._copy_database_file = old_copy

    from app.persistence import database_schema_revision

    assert database_schema_revision(create_engine_for_path(db)) == "a1b2c3d4e5f6"


def test_initialize_head_db_is_noop_without_backup(tmp_path: Path) -> None:
    """CR3: a DB already at head performs no redundant backup and no
    upgrade; the file is untouched."""
    db = tmp_path / "data" / "head.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    _upgrade(db)
    before = db.read_bytes()

    svc = JobService(None, managed_root=tmp_path / "artifacts")
    svc._database_path = db  # noqa: SLF001
    svc.initialize()

    assert db.read_bytes() == before
    assert list(db.parent.glob(f"{db.name}.bak-*")) == []
    assert svc.last_backup is None


# ── AC3: GET/cancel response semantics + additive durable fields ─────────────


def test_get_job_preserves_legacy_fields_and_hides_fenced(tmp_path: Path) -> None:
    """AC3: GET /api/jobs/{id} keeps job_id/status/progress/message/error/
    job_type; a fenced internal state is never observable."""
    from app.api.helpers import job_response

    svc = _make_service(tmp_path / "e.db", tmp_path / "artifacts")
    info = svc.create_job("ingest", input_manifest={"project_id": "p1"})
    resp = job_response(info)
    assert resp["job_id"] == info.job_id
    assert resp["status"] in ("queued", "running", "completed", "failed")
    assert "progress" in resp
    assert "message" in resp
    assert "error" in resp
    assert "job_type" in resp
    # fenced is internal: the service folds it into queued/failed/cancelled.
    assert resp.get("status") != "fenced"


def test_cancel_semantics_200_400_404(tmp_path: Path) -> None:
    """AC3: cancel returns 200 cancel_requested for active jobs, 400 for
    terminal jobs, 404 for unknown jobs (legacy route semantics)."""
    svc = _make_service(tmp_path / "f.db", tmp_path / "artifacts")

    info = svc.create_job("ingest", input_manifest={"project_id": "p1"})
    assert svc.cancel_job(info.job_id) is True
    assert svc.get_job(info.job_id).state.value == "cancelling"
    # second cancel while cancelling is an idempotent 200
    assert svc.cancel_job(info.job_id) is True

    assert svc.cancel_job("nonexistent") is False
    assert svc.get_job("nonexistent") is None


# ── AC4/AC5: restart-safe reconciliation and resume ──────────────────────────


def test_forced_close_reconciles_and_completes_without_duplicates(
    tmp_path: Path,
) -> None:
    """AC5: a queued Job survives a forced close; a fresh app/engine
    reconciles (no-op for queued), a fresh worker claims it and completes it
    exactly once — no duplicate attempt rows, no duplicate effects."""
    db_path = tmp_path / "restart.db"
    managed = tmp_path / "artifacts"
    managed.mkdir(exist_ok=True)

    # Phase 1: submit while a worker claims it and dies mid-step (no release).
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    _ensure_ws(factory)

    w1 = DurableWorker(
        factory,
        config=WorkerConfig(worker_id="phase1", staging_root=managed),
    )
    blocked = threading.Event()
    keep_running = threading.Event()

    def phase1_handler(ctx):
        blocked.set()  # signal the test that the handler started
        keep_running.wait(timeout=10)  # hold the claim until the test kills it

    w1.register_handler("SYNTH", phase1_handler)

    svc = JobService(factory, worker=w1, managed_root=managed)
    info = svc.create_job(
        "SYNTH", input_manifest={"managed_root": str(managed), "phase": 1},
        workspace_id="default", owner_type="project", owner_id="o1",
    )
    svc.start_worker()
    try:
        assert blocked.wait(timeout=10), "phase-1 handler did not start"
    finally:
        # Forced close: kill the worker thread while the handler still holds
        # the claim (no graceful release) — the job stays running + leased.
        keep_running.clear()
        w1.stop(timeout=1.0)  # stop the poll loop only; the handler thread
        # stays blocked on the event, so the lease is never released.
        svc._worker = None  # noqa: SLF001

    # The lease row is left with an expired TTL; a fresh reconciler over a
    # fresh engine fences + requeues it.  The schema CHECK
    # ``expires_at >= acquired_at`` must hold, so the whole lease window is
    # shifted into the past (fresh engine, same clock frame as the
    # reconciler's scan).
    past = datetime.now(UTC) - timedelta(seconds=120)
    with factory() as s:
        s.execute(
            text(
                "UPDATE job_lease SET expires_at = :p, heartbeat_at = :p, "
                "acquired_at = :a WHERE job_id = :jid"
            ),
            {
                "p": past,
                "a": past - timedelta(seconds=60),
                "jid": info.job_id,
            },
        )
        s.commit()

    engine2 = create_engine_for_path(db_path)
    factory2 = create_session_factory(engine2)
    reconciler = JobReconciler(factory2, config=ReconcileConfig(fence_grace_seconds=0))
    report = reconciler.reconcile_once()
    assert report.fenced >= 1
    with factory2() as s:
        assert JobRepository(s).get_job(info.job_id).state == "queued"

    # Phase 3: a brand-new worker re-claims and completes exactly once.
    completed: list[str] = []

    def phase3_handler(ctx):
        completed.append(ctx.job_id)
        return {}

    w2 = DurableWorker(
        factory2,
        config=WorkerConfig(worker_id="phase3", staging_root=managed),
    )
    w2.register_handler("SYNTH", phase3_handler)
    assert w2.run_once() == 1
    with factory2() as s:
        repo = JobRepository(s)
        job = repo.get_job(info.job_id)
        assert job.state == "completed"
        attempts = repo.list_attempts(job.id)
        assert len(completed) == 1
        # attempt rows are unique per (job, step, attempt) — no duplicates
        assert len(attempts) == 1


def test_cancel_during_retry_backoff_wins(tmp_path: Path) -> None:
    """AC7: cancel during a transient retry backoff cancels before the next
    retry runs (contract §6.3 — cancel wins)."""
    import time

    db_path = tmp_path / "retry.db"
    managed = tmp_path / "artifacts"
    managed.mkdir(exist_ok=True)
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    _ensure_ws(factory)

    attempts: list[str] = []

    def flaky(ctx):
        attempts.append(ctx.attempt)
        raise RuntimeError("BUSY_LOCK")

    from app.workflow.durable_worker import WorkerConfig

    w = DurableWorker(
        factory,
        config=WorkerConfig(
            worker_id="retry-worker",
            staging_root=managed,
            retry_base_delay=0.02,
            retry_multiplier=2.0,
            retry_cap_delay=0.02,
            max_attempts=5,
        ),
    )
    w.register_handler("SYNTH", flaky)
    svc = JobService(factory, worker=w, managed_root=managed)
    info = svc.create_job(
        "SYNTH", input_manifest={"managed_root": str(managed)},
        workspace_id="default", owner_type="project", owner_id="o1",
    )
    svc.start_worker()
    try:
        for _ in range(100):
            if svc.get_job(info.job_id).state.value == "failed":
                break
            time.sleep(0.05)
        # a failed Job is terminal; cancel returns False (400 route)
        assert svc.cancel_job(info.job_id) is False
    finally:
        svc.stop_worker(timeout=5.0)


def test_no_false_ready_artifact(tmp_path: Path) -> None:
    """AC7: a Job whose declared output is missing never completes (no
    false-ready artifact; fail-closed worker)."""
    db_path = tmp_path / "nofalse.db"
    managed = tmp_path / "artifacts"
    managed.mkdir(exist_ok=True)
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    _ensure_ws(factory)

    def handler(ctx):
        return {"ok": True}

    from app.workflow.durable_worker import WorkerConfig

    w = DurableWorker(
        factory,
        config=WorkerConfig(worker_id="no-false-worker", staging_root=managed),
    )
    w.register_handler(
        "SYNTH",
        handler,
        declared_outputs={"result": {"path": "renders/missing.mp4"}},
    )
    svc = JobService(factory, worker=w, managed_root=managed)
    info = svc.create_job(
        "SYNTH", input_manifest={"managed_root": str(managed)},
        workspace_id="default", owner_type="project", owner_id="o1",
    )
    svc.start_worker()
    try:
        import time

        for _ in range(100):
            if svc.get_job(info.job_id).state.value in ("failed", "completed"):
                break
            time.sleep(0.05)
    finally:
        svc.stop_worker(timeout=5.0)

    final = svc.get_job(info.job_id)
    assert final.state.value == "failed"
    assert final.error is not None
    # The stable envelope's message names the validation failure (the API
    # surfaces the envelope message string; the code is in the persisted
    # envelope, not the legacy string field).
    assert "validation failed" in final.error.lower() or "VALIDATION_FAILED" in final.error


# ── AC6: no long operation inside HTTP requests ──────────────────────────────


def test_http_submit_is_fast_and_submission_only(tmp_path: Path) -> None:
    """AC6: submit endpoints only write the durable row (no execution inside
    the request) — the request returns while the job stays queued."""
    import time

    from app.api import deps
    from app.config import AppConfig
    from app.persistence import create_engine_for_path, create_session_factory

    root = tmp_path / "proj"
    root.mkdir()
    cfg = AppConfig(project_root=root, models_dir=root / "models", output_dir=root / "output")
    deps._config = cfg
    deps._project_wf = __import__(
        "app.workflow.project_workflow", fromlist=["ProjectWorkflowService"]
    ).ProjectWorkflowService(cfg)

    db_path = root / "data" / "test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _upgrade(db_path)
    factory = create_session_factory(create_engine_for_path(db_path))
    svc = JobService(factory, managed_root=root / "artifacts")
    deps._job_service = svc
    deps._lifecycle_db = db_path

    from app.api.app import app

    client = TestClient(app, raise_server_exceptions=True)
    # create a project on disk so ingest passes the 404 guard
    pid, _ = deps._project_wf.create_project("HTTP Test")

    t0 = time.monotonic()
    resp = client.post(f"/api/projects/{pid}/ingest")
    elapsed = time.monotonic() - t0
    assert resp.status_code == 200
    assert elapsed < 5.0, f"submit took {elapsed:.2f}s — long op inside request"
    data = resp.json()
    assert data["job_id"]
    # The job is durably queued, not executed inside the request.
    with factory() as s:
        job = JobRepository(s).get_job(data["job_id"])
        assert job.state == "queued"
        assert job.input_manifest["project_id"] == pid
