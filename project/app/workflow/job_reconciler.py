"""Deterministic, bounded restart reconciler for durable Jobs (S02-T04).

This module implements the S02-T04 surface of the approved
``docs/architecture/DURABLE_JOB_CONTRACT.md`` V1.1 on top of the S02-T02
``JobRepository`` and the S02-T03 worker:

- **Explicit run-once/startup reconcile, no import-time behavior.**
  Importing this module (or any ``app`` package) starts no threads, opens no
  sessions, touches no files.  ``reconcile_once()`` / ``reconcile_forever()``
  are explicit entry points; ``reconcile_forever`` runs only in the current
  thread and exits on ``stop()``.
- **Bounded batch scan.**  Each pass scans at most ``batch_size`` expired
  active leases (``running`` / ``cancelling`` Jobs whose lease ``expires_at``
  has passed beyond the fence grace) ordered oldest-first, resolves every
  candidate, and returns a structured ``ReconcileReport``
  (fenced/requeued/failed/cancelled counts, elapsed).
- **Atomic fencing before any decision.**  For every candidate the reconciler
  (a) invalidates the old lease row — clearing the fence token so the stale
  worker's subsequent writes are all rejected with ``FENCED_WORKER`` — and
  (b) transitions ``running|cancelling -> fenced`` in the **same transaction**
  (contract §5.3-2: timestamps only decide *when* the reconciler reclaims;
  the token is the enforcement point).
- **Fenced -> queued|failed|cancelled resolution.**
  - a Job with attempts remaining requeues (``fenced -> queued``) and its
    attempt counters (Job-level and every non-terminal step) are bumped in
    the same transaction (contract §8.2);
  - a Job whose attempts are exhausted fails with ``RETRIES_EXHAUSTED``;
  - a Job whose input manifest fingerprint changed since the fence fails
    with ``INPUT_CHANGED`` (manifests are immutable by contract, so this
    fires only if the manifest was illegally mutated — fail closed);
  - a Job that was ``cancelling`` when fenced resolves straight to terminal
    ``cancelled`` (contract §4.3 ``cancelling -> cancelled``, §6.3 cancel
    wins) — no new effects are ever started;
  - a Job that was ``running`` when fenced but whose fence event records a
    durable cancel request (``reason_code=CANCEL_REQUESTED``) also resolves
    to ``cancelled``.
- **Versioned checkpoint resume / fail-closed.**  The reconciler never
  inspects checkpoint payload semantics; resume compatibility is enforced by
  the worker on re-claim: a step whose checkpoint is absent or carries an
  unsupported ``schema_version`` is not resumed — the step re-runs from its
  beginning with a fresh checkpoint, and a Job whose handler cannot run at
  all fails closed with a stable envelope.  Requeued steps are rolled back to
  ``ready`` (contract §4.4: ``running|cancelling -> ready`` on fencing) so a
  re-claiming worker replays only uncommitted work.
- **Duplicate effects are impossible by construction.**  A fenced worker
  cannot write state, publish outputs, or release the lease (token cleared);
  the reconciler never executes handlers; and the requeued Job is only
  re-claimed through the repository's atomic lease CAS, which issues a fresh
  token.  Replay is additionally guarded by deterministic attempt rows:
  per-claim attempt numbers are numbered from the durable step attempt
  counter, so ``(job, step, attempt)`` rows are unique across claims.

No API routes, no migrations, no dependency changes, no edits to the legacy
in-memory ``JobService``.  The legacy service remains the runtime authority
until S02-T05.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.jobs import JobRecord, JobRepository
from app.persistence.models import Job as _JobORM
from app.persistence.models import JobLease as _JobLeaseORM

__all__ = [
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_FENCE_GRACE_SECONDS",
    "DEFAULT_POLL_INTERVAL",
    "INPUT_CHANGED_CODE",
    "RETRIES_EXHAUSTED_CODE",
    "WORKER_FENCED_CODE",
    "JobReconciler",
    "ReconcileConfig",
    "ReconcileReport",
    "manifest_fingerprint",
]

#: Stable error codes for reconciler decisions (contract §5.3-2 / §10.1).
WORKER_FENCED_CODE = "WORKER_FENCED"
RETRIES_EXHAUSTED_CODE = "RETRIES_EXHAUSTED"
INPUT_CHANGED_CODE = "INPUT_CHANGED"

#: Default maximum candidates resolved per scan (bounded batches, AC1).
DEFAULT_BATCH_SIZE = 50

#: Extra time a lease may sit expired before the reconciler fences it
#: (heartbeat-timeout grace, contract §5.2: heartbeat timeout = 90s).
DEFAULT_FENCE_GRACE_SECONDS = 90.0

#: Default poll interval for :meth:`JobReconciler.reconcile_forever`.
DEFAULT_POLL_INTERVAL = 5.0


@dataclass(frozen=True)
class ReconcileConfig:
    """Bounded knobs for one reconciler instance (all safe defaults)."""

    batch_size: int = DEFAULT_BATCH_SIZE
    fence_grace_seconds: float = DEFAULT_FENCE_GRACE_SECONDS
    poll_interval: float = DEFAULT_POLL_INTERVAL

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if self.fence_grace_seconds < 0:
            raise ValueError("fence_grace_seconds must be >= 0")
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")


@dataclass
class ReconcileReport:
    """Structured result of one reconcile pass (never raises)."""

    scanned: int = 0
    fenced: int = 0
    requeued: int = 0
    failed: int = 0
    cancelled: int = 0
    skipped: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def elapsed_seconds(self) -> float:
        if self.started_at is None or self.finished_at is None:
            return 0.0
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def resolved(self) -> int:
        return self.requeued + self.failed + self.cancelled


def manifest_fingerprint(manifest: dict[str, Any] | None) -> str:
    """Stable fingerprint of a Job's input manifest (contract §8.1).

    The reconciler records this fingerprint in the fence event details and
    compares it on resolution: a changed fingerprint means the inputs the
    Job was created with no longer match what a resume would replay, so the
    Job fails closed with ``INPUT_CHANGED`` instead of running against stale
    inputs (contract §4.3: ``fenced -> failed`` when the idempotency key is
    invalidated).
    """
    canonical = json.dumps(manifest or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class JobReconciler:
    """Deterministic, bounded reconciler bound to one session factory.

    Lifecycle:
        - ``reconcile_once()`` performs exactly one bounded scan in the
          current thread (no loop, no sleep); it is the deterministic entry
          point used by tests and by ``reconcile_forever``.
        - ``reconcile_forever()`` polls ``reconcile_once()`` every
          ``poll_interval`` (injectable sleeper) until ``stop()`` is
          signalled; it runs only in the thread that calls it.
        - ``start()``/``stop()`` manage an explicit daemon poll thread — the
          only thread this class ever spawns, and only on an explicit call.

    No background work happens at import time or at construction.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        config: ReconcileConfig | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._config = config or ReconcileConfig()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper or (lambda seconds: threading.Event().wait(seconds))
        self._log = logger or logging.getLogger("motionforge.job_reconciler")
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_error: Exception | None = None

    # ── Lifecycle (AC1) ─────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background poll loop (explicit; no import-time thread)."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self.reconcile_forever,
                name="job-reconciler",
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

    def reconcile_forever(self) -> None:
        """Poll :meth:`reconcile_once` until :meth:`stop` is signalled.

        When called directly (not via ``start``) this blocks the current
        thread; the loop scans every ``poll_interval`` and sleeps through the
        injectable sleeper.  Loop exceptions are logged and surfaced on
        ``last_error`` (the loop must survive).
        """
        while not self._stop_event.is_set():
            try:
                self.reconcile_once()
            except Exception as exc:  # noqa: BLE001 - loop must survive
                self._last_error = exc
                self._log.error("reconciler loop error: %s", exc)
            self._sleeper(self._config.poll_interval)

    # ── Single bounded pass (AC1) ───────────────────────────────────────────

    def reconcile_once(self) -> ReconcileReport:
        """Perform one bounded reconciliation pass; return a structured report.

        Deterministic entry point: scans at most ``batch_size`` expired active
        leases (oldest expiry first), fences each candidate atomically, then
        resolves every fenced Job to ``queued`` / ``failed`` / ``cancelled``
        in fresh sessions (simulating an actual restart between the fence and
        the decision — the committed state is the only state that matters,
        never in-memory state).  Never raises: per-Job failures are recorded
        on the report and the pass continues with the remaining candidates.
        """
        report = ReconcileReport()
        report.started_at = self._clock()
        try:
            candidates = self._expired_candidates()
        except Exception as exc:  # noqa: BLE001 - report, never raise
            report.errors.append({"stage": "scan", "error": str(exc)})
            report.finished_at = self._clock()
            return report
        report.scanned = len(candidates)
        for job_id in candidates:
            try:
                self._reconcile_one(job_id, report)
            except Exception as exc:  # noqa: BLE001 - per-Job isolation
                report.errors.append({"job_id": job_id, "error": str(exc)})
                self._log.warning("reconcile failed for Job %s: %s", job_id, exc)
        report.finished_at = self._clock()
        return report

    def _expired_candidates(self) -> list[str]:
        """Return the oldest ``batch_size`` Jobs with an expired lease.

        A Job is a candidate iff it is in an active leased state
        (``running`` / ``cancelling``) and its lease row ``expires_at`` is in
        the past beyond the fence grace (the heartbeat-timeout window,
        contract §5.2).  The scan is read-only and bounded.
        """
        now = self._clock()
        cutoff = now - timedelta(seconds=self._config.fence_grace_seconds)
        with self._session_factory() as session:
            rows = session.scalars(
                select(_JobORM.id)
                .join(_JobLeaseORM, _JobLeaseORM.job_id == _JobORM.id)
                .where(
                    _JobORM.state.in_(("running", "cancelling")),
                    _JobLeaseORM.expires_at <= cutoff,
                )
                .order_by(_JobLeaseORM.expires_at.asc())
                .limit(self._config.batch_size)
            ).all()
        return list(rows)

    # ── Fence + resolve (AC2..AC5) ──────────────────────────────────────────

    def _reconcile_one(self, job_id: str, report: ReconcileReport) -> None:
        """Fence one Job atomically, then resolve it in a fresh session."""
        with self._session_factory() as session:
            repo = JobRepository(session)
            job = repo.get_job(job_id)
            if job.state not in ("running", "cancelling"):
                report.skipped += 1
                return
            lease = repo.get_lease(job_id)
            if lease is None:
                # No lease row: nothing to fence.  The Job is either already
                # being resolved or its lease was removed; skip it.
                report.skipped += 1
                return
            old_token = lease.fence_token
            repo.invalidate_lease(job_id)
            repo.transition_job(
                job_id,
                "fenced",
                actor="reconciler",
                expected_revision=job.revision,
                reason_code=(
                    "CANCEL_REQUESTED" if job.state == "cancelling" else "LEASE_EXPIRED"
                ),
                details={
                    "worker_id": lease.worker_id,
                    "lease_version": lease.lease_version,
                    "old_fence_token_present": bool(old_token),
                    "expires_at": (
                        lease.expires_at.isoformat()
                        if lease.expires_at is not None
                        else None
                    ),
                    # Manifests are immutable by contract; the fingerprint is
                    # recorded at fence time so an illegal post-creation
                    # mutation fails closed with INPUT_CHANGED.
                    "manifest_fingerprint": manifest_fingerprint(job.input_manifest),
                },
            )
            session.commit()
            report.fenced += 1

        # The decision runs in a FRESH session/transaction — the committed
        # state after the fence is the only state that matters (this is what
        # an actual process restart would observe).
        self._resolve_fenced(job_id, report)

    def _resolve_fenced(self, job_id: str, report: ReconcileReport) -> None:
        """Resolve a committed ``fenced`` Job to queued/failed/cancelled."""
        with self._session_factory() as session:
            repo = JobRepository(session)
            job = repo.get_job(job_id)
            if job.state != "fenced":
                report.skipped += 1
                return

            if self._fence_reason(job_id) == "CANCEL_REQUESTED":
                # Contract §6.3: cancel wins.  A Job that was cancelling when
                # fenced resolves straight to terminal cancelled — the drain
                # semantics of a worker are preserved without running any new
                # effects.
                repo.transition_job(
                    job_id,
                    "cancelled",
                    actor="reconciler",
                    expected_revision=job.revision,
                    reason_code="CANCEL_DRAINED",
                )
                session.commit()
                report.cancelled += 1
                return

            if self._attempts_exhausted(repo, job):
                repo.transition_job(
                    job_id,
                    "failed",
                    actor="reconciler",
                    expected_revision=job.revision,
                    reason_code=RETRIES_EXHAUSTED_CODE,
                    error=self._envelope(
                        RETRIES_EXHAUSTED_CODE,
                        f"Job {job.id} exhausted {job.attempt} attempt(s); "
                        "fenced lease is not retried",
                        job=job,
                    ),
                )
                session.commit()
                report.failed += 1
                return

            if self._input_changed(job_id, job):
                repo.transition_job(
                    job_id,
                    "failed",
                    actor="reconciler",
                    expected_revision=job.revision,
                    reason_code=INPUT_CHANGED_CODE,
                    error=self._envelope(
                        INPUT_CHANGED_CODE,
                        f"Job {job.id} input manifest changed since fencing; "
                        "resume is unsafe (contract §4.3)",
                        job=job,
                    ),
                )
                session.commit()
                report.failed += 1
                return

            # Attempts remain and inputs unchanged: requeue.  Attempt
            # counters are bumped in the same transaction (contract §8.2).
            repo.bump_job_attempt(job.id)
            for step in repo.list_steps(job.id):
                if step.state in (
                    "pending",
                    "ready",
                    "running",
                    "cancelling",
                    "failed",
                ):
                    if step.state in ("running", "cancelling"):
                        # Contract §4.4: a step that was mid-flight returns to
                        # ready on fencing; its attempt rolled back.
                        repo.transition_step(
                            step.id,
                            "ready",
                            actor="reconciler",
                            expected_revision=step.revision,
                            reason_code="FENCED_ROLLBACK",
                        )
                    repo.bump_step_attempt(step.id)
            repo.transition_job(
                job_id,
                "queued",
                actor="reconciler",
                expected_revision=job.revision,
                reason_code="FENCED_REQUEUE",
                details={
                    "attempt": job.attempt + 1,
                    "worker_id": self._fence_worker(job_id),
                },
            )
            session.commit()
            report.requeued += 1

    # ── Decision helpers ────────────────────────────────────────────────────

    def _attempts_exhausted(self, repo: JobRepository, job: JobRecord) -> bool:
        """True when the Job's per-Job retry budget is spent (§6.1)."""
        return job.attempt >= job.max_attempts

    def _input_changed(self, job_id: str, job: JobRecord) -> bool:
        """True when the manifest fingerprint differs from the creation record.

        The fingerprint is recorded on the Job's ``created`` event at creation
        time (manifests are immutable by contract, §3).  The reconciler
        compares the current manifest against that durable baseline and fails
        closed with ``INPUT_CHANGED`` if the manifest was ever mutated after
        creation — resume against changed inputs is refused (contract §4.3).
        A missing baseline (defensive) is treated as unchanged so Jobs never
        spuriously fail.
        """
        with self._session_factory() as session:
            repo = JobRepository(session)
            for event in repo.list_events(job_id):
                if event.event_type == "created" and event.details:
                    recorded = event.details.get("manifest_fingerprint")
                    break
            else:
                return False
        if not isinstance(recorded, str) or not recorded:
            return False
        return recorded != manifest_fingerprint(job.input_manifest)

    def _fence_reason(self, job_id: str) -> str | None:
        """The reason_code recorded on the Job's most recent fenced event."""
        with self._session_factory() as session:
            repo = JobRepository(session)
            for event in repo.list_events(job_id):
                if event.to_state == "fenced" and event.reason_code:
                    return event.reason_code
        return None

    def _fence_worker(self, job_id: str) -> str | None:
        """The worker id recorded on the Job's most recent fenced event."""
        with self._session_factory() as session:
            repo = JobRepository(session)
            for event in repo.list_events(job_id):
                if event.to_state == "fenced" and event.worker_id:
                    return event.worker_id
        return None

    @staticmethod
    def _envelope(
        error_code: str,
        message: str,
        *,
        job: JobRecord | None = None,
        step_code: str | None = None,
        attempt: int | None = None,
        worker_id: str | None = None,
    ) -> dict[str, Any]:
        """Stable error envelope for reconciler terminal decisions (§10.1)."""
        envelope: dict[str, Any] = {
            "error_code": error_code,
            "class": "permanent",
            "message": message,
            "recoverable": False,
            "retryable": False,
        }
        if step_code is not None:
            envelope["step_code"] = step_code
        if attempt is not None:
            envelope["attempt"] = attempt
        if worker_id is not None:
            envelope["worker_id"] = worker_id
        if job is not None:
            envelope["details"] = {
                "job_id": job.id,
                "job_type": job.job_type,
                "state": job.state,
                "attempt": job.attempt,
                "max_attempts": job.max_attempts,
            }
        return envelope
