"""Durable worker engine for MotionForge 2D (S02-T03).

This module implements the S02-T03 surface of the approved
``docs/architecture/DURABLE_JOB_CONTRACT.md`` V1.1 and the S02-T02
``JobRepository``:

- **Explicit lifecycle, no import-time thread.**  Constructing a worker never
  starts anything.  ``run_forever`` / ``run_once`` are explicit entry points
  and are the only places a poll loop may run.  Importing this module (or any
  ``app`` package) starts no background work.
- **Deterministic, injectable clock / sleeper / handler registry.**
  ``DurableWorker`` accepts ``clock`` (``() -> datetime``) and ``sleeper``
  (``(seconds) -> None``) so retry/backoff, heartbeat cadence and race tests
  run against a fake clock and never sleep for real.  Handlers are registered
  per job type with ``register_handler``; an unknown job type fails safely
  (the Job fails with ``UNKNOWN_HANDLER``) instead of running nothing.
- **Fenced worker mutations.**  Every repository write the worker performs
  while the Job is running/cancelling carries the current fence token.  A
  lost/stale lease aborts the attempt: the worker stops executing, cannot
  publish state or outputs, and leaves the Job for the S02-T04 reconciler.
- **Retry/backoff with a stable envelope.**  Transient failures are retried
  with bounded exponential backoff (base 1s, multiplier 4, cap 16s, jitter
  ≤20%) up to the Job's ``max_attempts``; permanent failures and exhausted
  retries persist a stable error envelope (§10.1) and the Job transitions to
  ``failed``.
- **Cooperative cancellation.**  Cancel wins before the next effect/step;
  the worker drains to terminal ``cancelled`` and never publishes final
  outputs.  The completed-vs-cancel race is serialized by the repository's
  guarded transitions (first committed writer wins).
- **Fail-closed output validation.**  Step/job completion requires the
  step's declared outputs to be present on disk with matching sha256/size
  (``ManagedRoot`` evidence); missing/staging output can never be marked
  complete (contract §9.3, invariant §15-5).
- **No API cutover.**  This module does not touch API routes, migrations,
  the legacy in-memory ``JobService``, or runtime wiring.  The legacy
  service remains the runtime authority until S02-T05.

Synthetic deterministic handlers (no GPU/model/network) are used by the test
suite; production job-type handlers are a separate concern.
"""

from __future__ import annotations

import logging
import random
import threading
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.persistence.artifacts import ManagedRoot, hash_file
from app.persistence.jobs import (
    TERMINAL_STATES,
    FencedWorkerError,
    JobError,
    JobRecord,
    JobRepository,
    LeaseConflictError,
    StepRecord,
)
from app.persistence.models import Job as _JobORM

__all__ = [
    "CANCELLED_ERROR_CODE",
    "DEFAULT_HEARTBEAT_INTERVAL",
    "DEFAULT_LEASE_TTL",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_POLL_INTERVAL",
    "DEFAULT_RETRY_BASE_DELAY",
    "DEFAULT_RETRY_CAP_DELAY",
    "DEFAULT_RETRY_MAX_JITTER",
    "DEFAULT_RETRY_MULTIPLIER",
    "DURABLE_WORKER_CP_VERSION",
    "OUTPUT_PURPOSES",
    "PERMANENT_ERROR_CODES",
    "PUBLICATION_FAILED_CODE",
    "TRANSIENT_ERROR_CODES",
    "UNKNOWN_HANDLER_CODE",
    "VALIDATION_FAILED_CODE",
    "WorkerConfig",
    "WorkerContext",
    "DurableWorker",
    "build_worker_context",
    "error_envelope",
    "new_worker_id",
]

# ── Contract constants (DURABLE_JOB_CONTRACT V1.1) ───────────────────────────

#: Version tag required on every persisted checkpoint (contract §7.2).
DURABLE_WORKER_CP_VERSION = 1

#: Default lease TTL used when the worker is not given one (contract §5.2).
DEFAULT_LEASE_TTL = 60

#: Default heartbeat interval; the worker heartbeats once per claimed Job
#: when the job's work loop runs longer than this (contract §5.2).
DEFAULT_HEARTBEAT_INTERVAL = 15

#: Default poll interval between queue scans.
DEFAULT_POLL_INTERVAL = 1.0

#: Default per-Job retry budget (contract §6.1).
DEFAULT_MAX_ATTEMPTS = 3

#: Backoff: exponential 1s, 4s, 16s capped at 16s with jitter <= 20%.
DEFAULT_RETRY_BASE_DELAY = 1.0
DEFAULT_RETRY_MULTIPLIER = 4.0
DEFAULT_RETRY_CAP_DELAY = 16.0
DEFAULT_RETRY_MAX_JITTER = 0.2

#: Stable error codes (contract §6.1 / §10.1).
UNKNOWN_HANDLER_CODE = "UNKNOWN_HANDLER"
VALIDATION_FAILED_CODE = "VALIDATION_FAILED"
PUBLICATION_FAILED_CODE = "PUBLICATION_FAILED"
CANCELLED_ERROR_CODE = "CANCELLED"
PERMANENT_ERROR_CODES: frozenset[str] = frozenset(
    {
        "INPUT_MISSING",
        "SCHEMA_MISMATCH",
        "VALIDATION_FAILED",
        "UNSUPPORTED_CODEC",
        "PUBLICATION_FAILED",
        "UNKNOWN_HANDLER",
        "OUTPUT_MISSING",
    }
)
TRANSIENT_ERROR_CODES: frozenset[str] = frozenset(
    {
        "BUSY_LOCK",
        "NETWORK_TIMEOUT",
        "PROVIDER_429",
        "DISK_FULL",
        "GPU_OOM",
        "TRANSIENT",
    }
)
#: Purposes that count as a Job's final output (contract §9.2) — the only
#: purposes whose presence is required before a Job may be ``completed``.
OUTPUT_PURPOSES: frozenset[str] = frozenset({"render", "final", "result"})


# ── Error envelope helpers (contract §10.1) ──────────────────────────────────


def error_envelope(
    error_code: str,
    message: str,
    *,
    step_code: str | None = None,
    attempt: int | None = None,
    worker_id: str | None = None,
    recoverable: bool = True,
    retryable: bool = False,
    retry_after_s: float | None = None,
    details: dict[str, Any] | None = None,
    stack: str | None = None,
) -> dict[str, Any]:
    """Build the stable persisted error envelope shape (§10.1).

    ``class`` is derived from the error code: transient codes are
    ``"transient"``, permanent codes are ``"permanent"``, and the cancel code
    is ``"cancel"``.  Unknown codes default to ``"permanent"`` so a handler
    bug can never be silently retried forever.
    """
    if error_code in TRANSIENT_ERROR_CODES:
        error_class = "transient"
    elif error_code == CANCELLED_ERROR_CODE:
        error_class = "cancel"
    else:
        error_class = "permanent"
    envelope: dict[str, Any] = {
        "error_code": error_code,
        "class": error_class,
        "message": message,
    }
    if step_code is not None:
        envelope["step_code"] = step_code
    if attempt is not None:
        envelope["attempt"] = attempt
    if worker_id is not None:
        envelope["worker_id"] = worker_id
    envelope["recoverable"] = recoverable
    envelope["retryable"] = retryable
    if retry_after_s is not None:
        envelope["retry_after_s"] = retry_after_s
    if details is not None:
        envelope["details"] = details
    if stack is not None:
        envelope["stack"] = stack
    return envelope


def new_worker_id() -> str:
    """A unique per-process/per-pod worker id (contract §5.1)."""
    import socket

    host = socket.gethostname() or "unknown"
    boot = uuid.uuid4().hex[:8]
    return f"{host}-{boot}"


# ── Configuration ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorkerConfig:
    """Bounded knobs for one worker instance (all optional, all safe defaults)."""

    worker_id: str = field(default_factory=new_worker_id)
    lease_ttl: int = DEFAULT_LEASE_TTL
    #: Heartbeat thread scheduling: renew every ``heartbeat_interval``
    #: seconds (contract §5.2) and stop when the claim finishes; a single
    #: stuck beat is tolerated by the reconciler's 3-missed-beat window.
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    heartbeat_join_timeout: float = 5.0
    poll_interval: float = DEFAULT_POLL_INTERVAL
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    retry_base_delay: float = DEFAULT_RETRY_BASE_DELAY
    retry_multiplier: float = DEFAULT_RETRY_MULTIPLIER
    retry_cap_delay: float = DEFAULT_RETRY_CAP_DELAY
    retry_max_jitter: float = DEFAULT_RETRY_MAX_JITTER
    staging_root: Path | None = None

    def __post_init__(self) -> None:
        if self.lease_ttl < 1:
            raise ValueError("lease_ttl must be >= 1")
        if self.heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be > 0")
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be > 0")
        if self.heartbeat_join_timeout <= 0:
            raise ValueError("heartbeat_join_timeout must be > 0")
        if self.retry_base_delay <= 0:
            raise ValueError("retry_base_delay must be > 0")
        if self.retry_multiplier <= 1:
            raise ValueError("retry_multiplier must be > 1")
        if self.retry_cap_delay < self.retry_base_delay:
            raise ValueError("retry_cap_delay must be >= retry_base_delay")
        if not 0 <= self.retry_max_jitter <= 0.5:
            raise ValueError("retry_max_jitter must be within [0, 0.5]")


# ── Handler-facing context (AC2) ─────────────────────────────────────────────


@dataclass
class WorkerContext:
    """Versioned execution context handed to every registered step handler.

    ``input_manifest`` is the Job's immutable input identity (§3).
    ``checkpoint`` is the step's persisted resume payload, always carrying a
    ``schema_version``; handlers write it back through ``write_checkpoint``.

    The callbacks are the *fenced* mutation surface: they all carry the
    worker's current fence token and raise ``FencedWorkerError`` if the lease
    was lost or re-claimed.  A handler must never touch the repository
    directly.
    """

    job_id: str
    job_type: str
    step_code: str
    step_id: str
    workspace_id: str
    owner_type: str
    owner_id: str
    input_manifest: dict[str, Any]
    attempt: int
    checkpoint: dict[str, Any]
    worker_id: str
    fence_token: str
    ttl_seconds: int
    progress: Callable[[float, str | None], None]
    write_checkpoint: Callable[[dict[str, Any]], None]
    is_cancelled: Callable[[], bool]
    staging_dir: Callable[[], Path]


#: Registered step handler signature.
StepHandler = Callable[[WorkerContext], dict[str, Any]]

#: Validator for a step's declared outputs before completion (fail-closed).
OutputValidator = Callable[
    [WorkerContext, dict[str, Any], Path], dict[str, Any]
]

#: Runtime config the worker hands to a handler's ``run_job`` (internal).
_RuntimeConfig = Mapping[str, Any]


# ── Registry ─────────────────────────────────────────────────────────────────


@dataclass
class _HandlerEntry:
    """One registered job-type handler."""

    handler: Callable[..., Any]
    declared_outputs: dict[str, Any] | None
    output_validator: OutputValidator | None
    resource_class: str | None = None


class DurableWorker:
    """A deterministic durable worker bound to one repository/session factory.

    Lifecycle:
        - ``start()``/``stop()`` manage an explicit poll loop in a daemon
          thread (the *only* thread this class ever starts, and only on an
          explicit call).
        - ``run_once()`` performs exactly one queue scan without any loop or
          thread; it is the deterministic entry point used by tests and by
          ``run_forever``.
        - ``run_forever()`` runs the loop in the current thread (or in the
          background thread when ``start()`` was called); it returns only
          after ``stop()``.

    No background work happens at import time or at construction.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        config: WorkerConfig | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
        rng: random.Random | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._config = config or WorkerConfig()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper or (lambda seconds: threading.Event().wait(seconds))
        self._rng = rng or random.Random()
        self._log = logger or logging.getLogger("motionforge.durable_worker")
        self._handlers: dict[str, _HandlerEntry] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_error: Exception | None = None
        # Per-claim heartbeat state: the loop thread, its stop signal and a
        # thread-safe failure channel (contract §5.3 — a failed beat must
        # abort the execution path before any subsequent state/output write).
        self._hb_lock = threading.Lock()
        self._hb_thread: threading.Thread | None = None
        self._hb_stop = threading.Event()
        self._hb_error: FencedWorkerError | Exception | None = None

    # ── Handler registry (AC2) ───────────────────────────────────────────────

    def register_handler(
        self,
        job_type: str,
        handler: Callable[..., Any],
        *,
        declared_outputs: dict[str, Any] | None = None,
        output_validator: OutputValidator | None = None,
        resource_class: str | None = None,
    ) -> None:
        """Register the step handler for *job_type*.

        The registry is keyed by the Job's ``job_type``; a Job whose type has
        no registered handler fails safely with ``UNKNOWN_HANDLER`` (never
        runs nothing).
        """
        if not job_type:
            raise ValueError("job_type must be non-empty")
        if not callable(handler):
            raise ValueError("handler must be callable")
        with self._lock:
            self._handlers[job_type] = _HandlerEntry(
                handler=handler,
                declared_outputs=declared_outputs,
                output_validator=output_validator,
                resource_class=resource_class,
            )

    def unregister_handler(self, job_type: str) -> None:
        """Remove a registered handler (used by tests to prove fail-closed)."""
        with self._lock:
            self._handlers.pop(job_type, None)

    # ── Lifecycle (AC1) ──────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background poll loop (explicit; no import-time thread)."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self.run_forever,
                name=f"durable-worker-{self._config.worker_id[:8]}",
                daemon=True,
            )
            self._thread.start()

    def stop(self, timeout: float | None = 5.0) -> None:
        """Signal the poll loop to stop and join the background thread."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        self._thread = None

    @property
    def running(self) -> bool:
        """True while the background poll loop is alive."""
        thread = self._thread
        return thread is not None and thread.is_alive()

    @property
    def last_error(self) -> Exception | None:
        """The last unhandled loop error (diagnostics; never swallowed)."""
        return self._last_error

    def run_once(self) -> int:
        """Perform exactly one queue scan; return the number of claims attempted.

        Deterministic entry point: scans queued Jobs ordered by priority
        (highest first) then created time (oldest first), claims the first
        eligible Job, and executes it to a terminal state or a fenced abort.
        No polling loop and no sleeping (except handler backoff); the only
        thread started here is the per-claim heartbeat thread, which is
        stopped and joined on every terminal path.  The claim (lease +
        running) is committed inside ``_claim_next``; the execution
        transaction is committed here once the Job reaches a terminal state
        (or rolled back on a fenced abort so a stale worker can never publish
        partial state).

        Fencing is handled at this boundary (contract §5.3-3): a
        ``FencedWorkerError`` raised from a handler callback, a guarded
        write, or the heartbeat thread is caught here, logged, and converted
        into a silent abort — the Job keeps the new owner's lease and no
        stale state/output is persisted.  ``run_once`` itself does not raise
        ``FencedWorkerError``.
        """
        with self._session_factory() as session:
            repo = JobRepository(session)
            job = self._claim_next(session, repo)
            if job is None:
                return 0
            try:
                lease = repo.get_lease(job.id)
                if lease is None:
                    session.rollback()
                    return 1
                self._start_heartbeat(job.id, lease.fence_token)
                try:
                    self._execute_job(session, repo, job)
                finally:
                    self._stop_heartbeat()
                # A failed heartbeat aborts before any subsequent write.
                hb_error = self._heartbeat_error()
                if hb_error is not None:
                    raise hb_error
            except FencedWorkerError as exc:
                # Fenced worker aborts silently at the worker/scheduler
                # boundary (contract §5.3-3): structured log + resource
                # cleanup; never release the new owner's lease, never
                # publish outputs, never mutate state.
                self._log.warning(
                    "worker %s fenced on Job %s (attempt aborted silently): %s",
                    self._config.worker_id,
                    job.id,
                    exc,
                )
                session.rollback()
                return 1
            # The JobRecord object was snapshotted at claim time; re-read the
            # live row to decide commit vs rollback.
            live = repo.get_job(job.id)
            if live.state in TERMINAL_STATES:
                session.commit()
            else:
                # Fenced abort or non-terminal: roll back so nothing a stale
                # worker wrote is ever persisted.
                session.rollback()
            return 1

    def run_forever(self) -> None:
        """Run the claim→execute loop until :meth:`stop` is signalled.

        When called directly (not via ``start``) this blocks the current
        thread; the loop polls the queue every ``poll_interval`` and sleeps
        through the injectable sleeper.
        """
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001 - loop must survive
                self._last_error = exc
                self._log.error("durable worker loop error: %s", exc)
            self._sleeper(self._config.poll_interval)

    # ── Per-claim heartbeat thread (AC3) ────────────────────────────────────

    def _start_heartbeat(self, job_id: str, fence_token: str) -> None:
        """Start the heartbeat loop for one claimed Job.

        The loop renews the lease in its own short-lived Session every
        ``heartbeat_interval`` seconds (contract §5.2) — independent of
        handler behavior — so a silent long-running handler stays leased.
        It never shares a Session with the execution thread and never holds
        a write transaction while the handler computes.  On a beat failure
        (``LeaseConflictError``/``FencedWorkerError``) it records the error
        on a thread-safe channel and stops; the execution path observes the
        channel and aborts before any subsequent state/output write.
        """
        with self._hb_lock:
            self._hb_stop.clear()
            self._hb_error = None
            self._hb_thread = threading.Thread(
                target=self._heartbeat_loop,
                args=(job_id, fence_token),
                name=f"hb-{self._config.worker_id[:8]}-{job_id[:8]}",
                daemon=True,
            )
            self._hb_thread.start()

    def _heartbeat_loop(self, job_id: str, fence_token: str) -> None:
        """Renew the lease until stopped or the token/lease is lost."""
        while not self._hb_stop.is_set():
            if self._hb_stop.wait(self._config.heartbeat_interval):
                return
            try:
                with self._session_factory() as s:
                    repo = JobRepository(s)
                    lease = repo.get_lease(job_id)
                    if lease is None:
                        raise FencedWorkerError(
                            f"no lease for Job {job_id}; heartbeat cannot "
                            "renew (contract §5.3-1)",
                            job_id=job_id,
                        )
                    if (
                        lease.worker_id != self._config.worker_id
                        or lease.fence_token != fence_token
                    ):
                        raise FencedWorkerError(
                            f"heartbeat rejected for Job {job_id}: lease "
                            "belongs to another worker (never overwrite a "
                            "newer worker's lease, contract §5.3)",
                            job_id=job_id,
                        )
                    repo.heartbeat_lease(
                        job_id,
                        self._config.worker_id,
                        fence_token,
                        ttl_seconds=self._config.lease_ttl,
                    )
                    s.commit()
            except (FencedWorkerError, LeaseConflictError, Exception) as exc:  # noqa: BLE001
                with self._hb_lock:
                    if self._hb_error is None:
                        self._hb_error = exc
                self._log.warning(
                    "heartbeat failed for Job %s (worker %s): %s",
                    job_id,
                    self._config.worker_id,
                    exc,
                )
                return

    def _stop_heartbeat(self) -> None:
        """Signal the heartbeat loop to stop and join it (bounded wait)."""
        with self._hb_lock:
            thread = self._hb_thread
            self._hb_thread = None
        if thread is not None and thread is not threading.current_thread():
            self._hb_stop.set()
            thread.join(timeout=self._config.heartbeat_join_timeout)

    def _heartbeat_error(self) -> Exception | None:
        """Return the recorded heartbeat failure, if any (thread-safe)."""
        with self._hb_lock:
            return self._hb_error

    def _heartbeat_thread_alive(self) -> bool:
        """True while the per-claim heartbeat thread is running."""
        with self._hb_lock:
            thread = self._hb_thread
            return thread is not None and thread.is_alive()

    # ── Queue claim (AC1: atomic, ordered by priority/time) ─────────────────

    def _claim_next(self, session: Session, repo: JobRepository) -> JobRecord | None:
        """Atomically claim the highest-priority oldest queued Job, if any."""
        from sqlalchemy import select

        candidate = session.scalar(
            select(_JobORM)
            .where(_JobORM.state == "queued")
            .order_by(
                _JobORM.priority.desc(),
                _JobORM.created_at.asc(),
            )
            .limit(1)
        )
        if candidate is None:
            return None
        try:
            lease = repo.acquire_lease(
                candidate.id, self._config.worker_id, ttl_seconds=self._config.lease_ttl
            )
            # Contract §4.3: queued -> running guarded by the lease holder.
            # acquire_lease bumps the Job's revision, so re-read the current
            # row before the guarded transition (the pre-claim revision is
            # stale by one).
            claimed = repo.get_job(candidate.id)
            repo.transition_job(
                candidate.id,
                "running",
                actor="worker",
                expected_revision=claimed.revision,
                fence_token=lease.fence_token,
            )
            session.commit()
            return repo.get_job(candidate.id)
        except (LeaseConflictError, FencedWorkerError, JobError):
            session.rollback()
            return None

    # ── Execution (AC2..AC6) ─────────────────────────────────────────────────

    def _execute_job(
        self, session: Session, repo: JobRepository, job: JobRecord
    ) -> None:
        """Execute a claimed Job to terminal (or fenced abort) inside *session*.

        The caller owns the transaction; every mutation inside this method is
        fenced with the current token and committed by the caller.
        """
        lease = repo.get_lease(job.id)
        if lease is None:
            return  # nothing to do; no lease means no claim
        token = lease.fence_token
        entry = self._handlers.get(job.job_type)
        if entry is None:
            self._fail_job(
                repo,
                job,
                token,
                error_envelope(
                    UNKNOWN_HANDLER_CODE,
                    f"no handler registered for job type {job.job_type!r}",
                    step_code=None,
                    attempt=job.attempt,
                    worker_id=self._config.worker_id,
                    recoverable=False,
                    retryable=False,
                ),
            )
            return

        steps = repo.list_steps(job.id)
        for step in steps:
            if self._job_cancelling(session, repo, job, token):
                self._cancel_drain(session, repo, job, steps, token)
                return
            self._run_step(session, repo, job, step, entry, token)
            if job.state in TERMINAL_STATES:
                return
            if repo.get_job(job.id).state in TERMINAL_STATES:
                return

        # All steps ran: job completion gate (AC6).
        self._complete_or_fail(session, repo, job, steps, token)

    def _run_step(
        self,
        session: Session,
        repo: JobRepository,
        job: JobRecord,
        step: StepRecord,
        entry: _HandlerEntry,
        token: str,
    ) -> None:
        """Run one step with attempt accounting, retries and fencing.

        Each repository write commits immediately (bounded write windows),
        so the SQLite connection never holds a write lock while a handler
        runs — handlers and their fenced callbacks can open their own
        sessions, and a concurrent reconciler/worker can re-claim (fence)
        mid-step.
        """
        step_attempt = 0
        # Durable base for per-claim attempt rows (contract §8.2): after a
        # reconciler requeue the per-step attempt counter was bumped, so this
        # claim's rows are numbered from that base and never collide with the
        # previous claim's rows — replay cannot duplicate effects or attempts.
        attempt_base = repo.latest_attempt_number(job.id, step.id)
        while True:
            current = repo.get_step(step.id)
            if current.state in TERMINAL_STATES:
                return
            if current.state == "pending":
                repo.transition_step(
                    step.id,
                    "ready",
                    actor="scheduler",
                    expected_revision=current.revision,
                )
                session.commit()
                current = repo.get_step(step.id)
            if current.state == "ready":
                repo.transition_step(
                    step.id,
                    "running",
                    actor="worker",
                    expected_revision=current.revision,
                    fence_token=token,
                )
                session.commit()
                current = repo.get_step(step.id)

            step_attempt += 1
            job_now = repo.get_job(job.id)
            # Per-claim attempt rows are numbered from the durable per-step
            # attempt counter captured at claim time (attempt_base) so rows
            # never collide across claims (contract §8.2).
            ctx = self._make_context(
                job_now, current, attempt_base + step_attempt, token
            )
            try:
                result = entry.handler(ctx)
            except FencedWorkerError:
                return  # fenced: abort silently, no state writes
            except Exception as exc:  # noqa: BLE001 - classified by code
                envelope = self._classify_error(exc, current, step_attempt)
                repo.record_attempt(
                    job_id=job.id,
                    step_id=step.id,
                    step_code=current.step_code,
                    attempt=step_attempt,
                    worker_id=self._config.worker_id,
                    fence_token=token,
                    error=envelope,
                )
                session.commit()
                self._log.warning(
                    "step %s attempt %d failed: %s", current.step_code, step_attempt, envelope
                )
                # Cancel wins before the next effect/step (contract §6.3):
                # if the durable cancel flag was set during this attempt, the
                # retry is NOT started — the Job drains to cancelled.
                if self._job_cancelling(session, repo, job, token):
                    self._cancel_drain(session, repo, job, None, token)
                    return
                if not envelope.get("retryable"):
                    # Attempt budget exhausted: a transient code that can no
                    # longer be retried fails with the stable RETRIES_EXHAUSTED
                    # envelope (contract §6.1); a permanent code keeps its own
                    # envelope.
                    if envelope.get("class") == "transient":
                        self._fail_job(
                            repo,
                            job,
                            token,
                            error_envelope(
                                "RETRIES_EXHAUSTED",
                                f"step {current.step_code!r} exhausted "
                                f"{step_attempt} attempt(s)",
                                step_code=current.step_code,
                                attempt=step_attempt,
                                worker_id=self._config.worker_id,
                                recoverable=False,
                                retryable=False,
                                details={"max_attempts": self._step_max_attempts(current)},
                            ),
                        )
                    else:
                        self._fail_job(repo, job, token, envelope)
                    session.commit()
                    return
                # Transient with attempts remaining: bounded backoff, then
                # this step's NEXT loop iteration retries it.
                delay = self._backoff_delay(step_attempt)
                self._sleeper(delay)
                session.commit()
                continue

            # Handler returned: validate declared outputs (AC6, fail-closed).
            # Cancel wins before the next effect/step (contract §6.3): a
            # durable cancel flag set during this attempt drains the Job
            # instead of completing/publishing anything.
            if self._job_cancelling(session, repo, job, token):
                self._cancel_drain(session, repo, job, None, token)
                return
            try:
                validation = self._validate_outputs(ctx, entry, result)
            except Exception as exc:  # noqa: BLE001 - validation failure
                envelope = error_envelope(
                    VALIDATION_FAILED_CODE,
                    f"output validation failed for step {current.step_code!r}: {exc}",
                    step_code=current.step_code,
                    attempt=step_attempt,
                    worker_id=self._config.worker_id,
                    recoverable=False,
                    retryable=False,
                    details={"validation_error": str(exc)},
                )
                repo.record_attempt(
                    job_id=job.id,
                    step_id=step.id,
                    step_code=current.step_code,
                    attempt=step_attempt,
                    worker_id=self._config.worker_id,
                    fence_token=token,
                    error=envelope,
                )
                self._fail_job(repo, job, token, envelope)
                return

            repo.transition_step(
                step.id,
                "completed",
                actor="worker",
                expected_revision=current.revision,
                fence_token=token,
                details={"validation": validation} if validation else None,
            )
            repo.record_attempt(
                job_id=job.id,
                step_id=step.id,
                step_code=current.step_code,
                attempt=step_attempt,
                worker_id=self._config.worker_id,
                fence_token=token,
                result=result,
            )
            session.commit()
            return

    def _complete_or_fail(
        self,
        session: Session,
        repo: JobRepository,
        job: JobRecord,
        steps: list[StepRecord],
        token: str,
    ) -> None:
        """Job completion gate: all steps terminal-completed/skipped AND every
        declared final output validated ⇒ ``completed``; else fail closed."""
        job_now = repo.get_job(job.id)
        if job_now.state in TERMINAL_STATES:
            return
        remaining = [s for s in repo.list_steps(job.id) if s.state not in ("completed", "skipped")]
        if remaining:
            self._fail_job(
                repo,
                job,
                token,
                error_envelope(
                    "STEP_NOT_COMPLETED",
                    f"cannot complete Job with unfinished steps: "
                    f"{[s.step_code for s in remaining]}",
                    worker_id=self._config.worker_id,
                    recoverable=False,
                    retryable=False,
                ),
            )
            return
        entry = self._handlers.get(job.job_type)
        declared = entry.declared_outputs if entry is not None else None
        if declared:
            missing = self._missing_declared_outputs(
                repo, job, declared, token
            )
            if missing:
                self._fail_job(
                    repo,
                    job,
                    token,
                    error_envelope(
                        "OUTPUT_MISSING",
                        f"declared final outputs not ready/validated: {missing}",
                        worker_id=self._config.worker_id,
                        recoverable=False,
                        retryable=False,
                        details={"missing": missing},
                    ),
                )
                return
        repo.transition_job(
            job.id,
            "completed",
            actor="worker",
            expected_revision=job_now.revision,
            fence_token=token,
        )

    def _missing_declared_outputs(
        self,
        repo: JobRepository,
        job: JobRecord,
        declared: dict[str, Any],
        token: str,
    ) -> list[str]:
        """Return the declared outputs that are not ready-validated on disk."""
        missing: list[str] = []
        managed = self._managed_for(repo, job)
        for name, spec in declared.items():
            rel = spec.get("path") if isinstance(spec, dict) else None
            if not rel:
                missing.append(f"{name}:no-path")
                continue
            target = managed.resolve(rel)
            if not target.is_file():
                missing.append(f"{name}:missing-file")
                continue
            if isinstance(spec, dict) and spec.get("sha256"):
                try:
                    if hash_file(target) != spec["sha256"]:
                        missing.append(f"{name}:sha256-mismatch")
                except OSError:
                    missing.append(f"{name}:unreadable")
            if isinstance(spec, dict) and spec.get("size_bytes") is not None:
                try:
                    if target.stat().st_size != int(spec["size_bytes"]):
                        missing.append(f"{name}:size-mismatch")
                except OSError:
                    missing.append(f"{name}:unreadable")
        return missing

    def _validate_outputs(
        self, ctx: WorkerContext, entry: _HandlerEntry, result: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Run the handler's output validator against a step result.

        Fail-closed: any validator exception or non-pass result rejects the
        step; a missing validator accepts the handler's own staged writes
        only when they pass the declared-output disk checks.
        """
        declared = entry.declared_outputs or {}
        if entry.output_validator is not None:
            return entry.output_validator(ctx, result, ctx.staging_dir())
        if not declared:
            return None
        # No custom validator: disk evidence is the gate.  Output checks run
        # in a fresh committed session so they read a consistent committed
        # view (never the worker's in-flight transaction).
        with self._session_factory() as s:
            repo = JobRepository(s)
            return self._check_declared_outputs(repo, ctx, declared)

    def _check_declared_outputs(
        self, repo: JobRepository, ctx: WorkerContext, declared: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate that every declared output exists with matching evidence."""
        job = repo.get_job(ctx.job_id)
        managed = self._managed_for(repo, job)
        evidence: dict[str, Any] = {}
        for name, spec in declared.items():
            rel = spec.get("path") if isinstance(spec, dict) else None
            if not rel:
                raise JobError(f"declared output {name!r} has no path")
            target = managed.resolve(rel)
            if not target.is_file():
                raise JobError(f"declared output {name!r} missing at {rel}")
            sha = hash_file(target)
            size = target.stat().st_size
            if isinstance(spec, dict) and spec.get("sha256") and sha != spec["sha256"]:
                raise JobError(f"declared output {name!r} sha256 mismatch")
            if isinstance(spec, dict) and spec.get("size_bytes") is not None and size != int(
                spec["size_bytes"]
            ):
                raise JobError(f"declared output {name!r} size mismatch")
            evidence[name] = {"relative_path": rel, "sha256": sha, "size_bytes": size}
        return evidence

    # ── Cancel drain (AC5) ───────────────────────────────────────────────────

    def _job_cancelling(
        self, session: Session, repo: JobRepository, job: JobRecord, token: str
    ) -> bool:
        """True when the Job is in ``cancelling`` (durable cancel flag set)."""
        job_now = repo.get_job(job.id)
        return job_now.state == "cancelling"

    def _cancel_drain(
        self,
        session: Session,
        repo: JobRepository,
        job: JobRecord,
        steps: list[StepRecord] | None,
        token: str,
    ) -> None:
        """Drain a cancelling Job: no new effects; terminal ``cancelled``."""
        for step in repo.list_steps(job.id):
            current = repo.get_step(step.id)
            if current.state in TERMINAL_STATES:
                continue
            # Contract §4.4: pending steps go pending -> ready first, then
            # ready/running -> cancelling -> cancelled (no new effects).
            if current.state == "pending":
                repo.transition_step(
                    step.id,
                    "ready",
                    actor="scheduler",
                    expected_revision=current.revision,
                )
                current = repo.get_step(step.id)
            if current.state == "ready":
                # Contract §4.4: a ready step that has never run must pass
                # through running so its started_at is set (the DB CHECK
                # ``finished_at IS NULL OR started_at IS NOT NULL`` forbids a
                # terminal write on a step that never started).
                repo.transition_step(
                    step.id,
                    "running",
                    actor="worker",
                    expected_revision=current.revision,
                    fence_token=token,
                    details={"cancel_drain": True},
                )
                session.commit()
                current = repo.get_step(step.id)
            if current.state in ("running", "cancelling"):
                repo.transition_step(
                    step.id,
                    "cancelling",
                    actor="worker",
                    expected_revision=current.revision,
                    fence_token=token,
                    details={"cancel_requested_at": datetime.now(UTC).isoformat()},
                )
                session.commit()
                current = repo.get_step(step.id)
            if current.state == "cancelling":
                repo.transition_step(
                    step.id,
                    "cancelled",
                    actor="worker",
                    expected_revision=current.revision,
                    fence_token=token,
                )
            session.commit()
        job_now = repo.get_job(job.id)
        if job_now.state == "cancelling":
            repo.transition_job(
                job.id,
                "cancelled",
                actor="worker",
                expected_revision=job_now.revision,
                fence_token=token,
                reason_code="CANCEL_DRAINED",
            )
            session.commit()

    # ── Fencing, attempts, classification ────────────────────────────────────

    def _fail_job(
        self,
        repo: JobRepository,
        job: JobRecord,
        token: str,
        envelope: dict[str, Any],
    ) -> None:
        """Persist the error envelope and transition the Job to ``failed``."""
        job_now = repo.get_job(job.id)
        if job_now.state in TERMINAL_STATES:
            return
        repo.set_job_error(job.id, envelope, fence_token=token)
        repo.transition_job(
            job.id,
            "failed",
            actor="worker",
            expected_revision=job_now.revision,
            fence_token=token,
            error=envelope,
            reason_code=envelope.get("error_code"),
        )

    def _classify_error(
        self, exc: Exception, step: StepRecord, attempt: int
    ) -> dict[str, Any]:
        """Classify a handler exception into a stable envelope (§6.1)."""
        code = getattr(exc, "code", None) or getattr(exc, "error_code", None) or type(
            exc
        ).__name__.upper()
        code = str(code)
        transient = code in TRANSIENT_ERROR_CODES
        retryable = transient and attempt < self._step_max_attempts(step)
        return error_envelope(
            code,
            str(exc),
            step_code=step.step_code,
            attempt=attempt,
            worker_id=self._config.worker_id,
            recoverable=transient,
            retryable=retryable,
            retry_after_s=self._backoff_delay(attempt) if transient else None,
            details={"error_type": type(exc).__name__},
        )

    def _step_max_attempts(self, step: StepRecord) -> int:
        return max(1, step.max_attempts or self._config.max_attempts)

    def _backoff_delay(self, attempt: int) -> float:
        """Bounded exponential backoff with jitter <= 20% (contract §6.1)."""
        base = self._config.retry_base_delay * (self._config.retry_multiplier ** (attempt - 1))
        capped = min(base, self._config.retry_cap_delay)
        jitter = capped * self._config.retry_max_jitter * (self._rng.random() * 2 - 1)
        return max(0.0, capped + jitter)

    def _make_context(
        self,
        job: JobRecord,
        step: StepRecord,
        attempt: int,
        token: str,
    ) -> WorkerContext:
        """Build the versioned handler context (AC2)."""
        checkpoint = step.checkpoint or {"schema_version": DURABLE_WORKER_CP_VERSION}
        if "schema_version" not in checkpoint:
            checkpoint = dict(checkpoint)
            checkpoint["schema_version"] = DURABLE_WORKER_CP_VERSION
        staged = self._staging_dir(job, step)

        def progress(pct: float, msg: str | None = None) -> None:
            with self._session_factory() as s:
                r = JobRepository(s)
                r.update_progress(job.id, pct, fence_token=token)
                if msg:
                    r.update_step_progress(step.id, pct, fence_token=token)
                s.commit()

        def write_checkpoint(cp: dict[str, Any]) -> None:
            with self._session_factory() as s:
                r = JobRepository(s)
                r.write_checkpoint(step.id, cp, fence_token=token)
                s.commit()

        def is_cancelled() -> bool:
            with self._session_factory() as s:
                j = JobRepository(s).get_job(job.id)
                return j.state == "cancelling"

        def staging_dir() -> Path:
            staged.mkdir(parents=True, exist_ok=True)
            return staged

        return WorkerContext(
            job_id=job.id,
            job_type=job.job_type,
            step_code=step.step_code,
            step_id=step.id,
            workspace_id=job.workspace_id,
            owner_type=job.owner_type,
            owner_id=job.owner_id,
            input_manifest=job.input_manifest,
            attempt=attempt,
            checkpoint=checkpoint,
            worker_id=self._config.worker_id,
            fence_token=token,
            ttl_seconds=self._config.lease_ttl,
            progress=progress,
            write_checkpoint=write_checkpoint,
            is_cancelled=is_cancelled,
            staging_dir=staging_dir,
        )

    def _staging_dir(self, job: JobRecord, step: StepRecord) -> Path:
        """Staging path for a step under the managed root (contract §9.1)."""
        root = self._managed_root(job)
        return root / "staging" / job.id / step.step_code

    def _managed_root(self, job: JobRecord) -> Path:
        """Resolve the managed root for a Job (config root or workspace root)."""
        if self._config.staging_root is not None:
            return self._config.staging_root
        return Path(job.input_manifest.get("managed_root", "artifacts"))

    def _managed_for(self, repo: JobRepository, job: JobRecord) -> ManagedRoot:
        """A ManagedRoot bound to the Job's managed root (containment-safe)."""
        return ManagedRoot(self._managed_root(job))


def build_worker_context(
    *,
    job_id: str,
    job_type: str,
    step_code: str,
    step_id: str,
    workspace_id: str,
    owner_type: str,
    owner_id: str,
    input_manifest: dict[str, Any],
    attempt: int,
    checkpoint: dict[str, Any],
    worker_id: str,
    fence_token: str,
    ttl_seconds: int,
    progress: Callable[[float, str | None], None],
    write_checkpoint: Callable[[dict[str, Any]], None],
    is_cancelled: Callable[[], bool],
    staging_dir: Callable[[], Path],
) -> WorkerContext:
    """Standalone constructor for :class:`WorkerContext` (test convenience)."""
    return WorkerContext(
        job_id=job_id,
        job_type=job_type,
        step_code=step_code,
        step_id=step_id,
        workspace_id=workspace_id,
        owner_type=owner_type,
        owner_id=owner_id,
        input_manifest=input_manifest,
        attempt=attempt,
        checkpoint=checkpoint,
        worker_id=worker_id,
        fence_token=fence_token,
        ttl_seconds=ttl_seconds,
        progress=progress,
        write_checkpoint=write_checkpoint,
        is_cancelled=is_cancelled,
        staging_dir=staging_dir,
    )
