"""Durable job repository enforcing the approved V1.1 job contract.

This module implements the S02-T02 persistence surface of
``docs/architecture/DURABLE_JOB_CONTRACT.md``:

- Job/JobStep creation is atomic; steps are created together with the Job in
  one transaction and each Job gets exactly one ``created`` JobEvent.
- Idempotency: at most one **active or completed** Job per
  ``(workspace_id, idempotency_key)`` (contract §8.1/§8.5).  A duplicate
  request for a completed key returns the existing Job; a duplicate for an
  active key raises ``IdempotencyKeyInUse``; a terminal failed/cancelled Job
  may be retried through :meth:`JobRepository.create_successor`, which links
  exactly one successor per predecessor and rejects cycles.
- Guarded state transitions (contract §4.3/§4.4): every transition validates
  the allowed endpoint table, matches the expected current state and
  ``revision``, and — for worker transitions on a leased Job — requires the
  current fence token.  Accepted transitions bump ``revision`` and append a
  ``JobEvent`` in the same transaction.  Terminal rows are immutable: no
  repository method transitions a terminal Job, and ``delete_job`` refuses
  terminal rows.
- Lease acquire/heartbeat/release (contract §5) are atomic, single-row
  guarded writes; a stale worker's writes are rejected with
  ``FencedWorkerError`` (token mismatch) — the fence token is the
  enforcement point, not the timestamp.
- Attempt accounting, progress/checkpoint/error envelopes persist with
  bounded transactional behavior (one short transaction per call).

This is a pure persistence layer: no worker loop, no reconciler, no API
cutover, no dual-write.  The legacy in-memory ``JobService`` remains the
runtime authority until S02-T05.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    JOB_ACTORS,
    JOB_STATES,
    RESOURCE_CLASSES,
    STEP_TYPES,
    Job,
    JobAttempt,
    JobEvent,
    JobLease,
    JobStep,
)

__all__ = [
    "FENCED_WORKER_ERROR_CODE",
    "IDEMPOTENCY_KEY_IN_USE_CODE",
    "INVALID_STATE_TRANSITION_CODE",
    "LEASE_CONFLICT_CODE",
    "TERMINAL_STATES",
    "FencedWorkerError",
    "IdempotencyKeyInUse",
    "InvalidStateTransition",
    "JobAlreadyTerminalError",
    "JobCreationError",
    "JobError",
    "JobNotFoundError",
    "JobRepository",
    "JobStepCreationError",
    "JobStepNotFoundError",
    "LeaseConflictError",
    "LeaseExpiredError",
    "LeaseNotFoundError",
    "StepInput",
    "create_job_revision",
    "parse_json",
    "terminal_job_states",
]
#: Stable error codes surfaced by the repository (contract §10.1).
INVALID_STATE_TRANSITION_CODE = "INVALID_STATE_TRANSITION"
IDEMPOTENCY_KEY_IN_USE_CODE = "IDEMPOTENCY_KEY_IN_USE"
FENCED_WORKER_ERROR_CODE = "FENCED_WORKER"
LEASE_CONFLICT_CODE = "LEASE_CONFLICT"

#: Terminal Job states: rows in these states are immutable (contract §4.5-4).
TERMINAL_STATES: frozenset[str] = frozenset({"cancelled", "completed", "failed"})
#: States that count as "the logical work is already done" for idempotency
#: reuse (contract §8.1: completed ⇒ return the existing Job).
COMPLETED_REUSE_STATES: frozenset[str] = frozenset({"completed"})

#: Job transition endpoints (contract §4.3).  Every key/values pair is a
#: closed set; anything else is an invalid transition.
JOB_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"queued"}),
    "queued": frozenset({"running", "cancelling", "cancelled"}),
    "running": frozenset({"cancelling", "completed", "failed", "fenced", "cancelled"}),
    "cancelling": frozenset({"running", "cancelled", "failed", "fenced"}),
    "fenced": frozenset({"queued", "failed", "cancelled"}),
    # Terminal states: no outgoing transitions (immutable rows).
    "cancelled": frozenset(),
    "completed": frozenset(),
    "failed": frozenset(),
}

#: JobStep transition endpoints (contract §4.4).
JOB_STEP_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"ready", "skipped"}),
    "ready": frozenset({"running", "cancelling"}),
    "running": frozenset({"completed", "failed", "cancelling", "ready"}),
    "cancelling": frozenset({"cancelled", "failed", "ready"}),
    "failed": frozenset({"ready"}),
    # Terminal step states: no outgoing transitions.
    "cancelled": frozenset(),
    "completed": frozenset(),
    "skipped": frozenset(),
}

#: Default lease TTL (seconds) used when a caller does not specify one.
DEFAULT_LEASE_TTL_SECONDS = 60


def terminal_job_states() -> frozenset[str]:
    """Return the set of terminal Job states (immutable rows)."""
    return TERMINAL_STATES


def create_job_revision() -> int:
    """Start every Job at optimistic-concurrency revision 1 (S01 policy)."""
    return 1


def _new_id() -> str:
    """Opaque public identifier (UUIDv7-compatible string; UUID4 initial)."""
    return str(uuid.uuid4())


def parse_json(raw: str | None, default: Any) -> Any:
    """Parse a stored JSON payload, falling back to *default* on None/garbage.

    JSON payloads in this schema are internal (manifests, checkpoints,
    envelopes, details).  A malformed payload fails closed to the provided
    default so a corrupted row can never crash a reader.
    """
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


# ── Exceptions ───────────────────────────────────────────────────────────────


class JobError(Exception):
    """Base class for all durable-job repository errors."""


class JobNotFoundError(JobError):
    """No Job row exists for the requested id."""


class JobStepNotFoundError(JobError):
    """No JobStep row exists for the requested id."""


class JobAlreadyTerminalError(JobError):
    """The Job is terminal and therefore immutable (contract §4.5-4)."""


class InvalidStateTransition(JobError):  # noqa: N818 - stable contract name
    """The requested state transition is not an allowed endpoint.

    Carries the stable machine-readable code ``INVALID_STATE_TRANSITION``
    (contract §4.3).
    """

    def __init__(self, message: str, *, job_id: str | None = None) -> None:
        super().__init__(message)
        self.job_id = job_id
        self.code = INVALID_STATE_TRANSITION_CODE


class FencedWorkerError(JobError):
    """The worker's fence token does not match the current lease.

    The fence token is the enforcement point (contract §5.3-1): the write is
    dropped and the worker must abort its attempt silently.
    """

    def __init__(self, message: str, *, job_id: str | None = None) -> None:
        super().__init__(message)
        self.job_id = job_id
        self.code = FENCED_WORKER_ERROR_CODE


class IdempotencyKeyInUse(JobError):  # noqa: N818 - stable contract name
    """A duplicate idempotency key was rejected.

    At most one active or completed Job may exist per
    ``(workspace_id, idempotency_key)`` (contract §8.1/§8.5).
    """

    def __init__(self, message: str, *, key: str, job_id: str | None = None) -> None:
        super().__init__(message)
        self.key = key
        self.job_id = job_id
        self.code = IDEMPOTENCY_KEY_IN_USE_CODE


class JobCreationError(JobError):
    """A Job could not be created; the transaction was rolled back."""


class JobStepCreationError(JobCreationError):
    """JobStep creation failed (duplicate code/position, unknown dependency,
    cyclic dependency or a non-pending predecessor)."""


class LeaseNotFoundError(JobError):
    """No lease row exists for the Job (nothing to heartbeat/release)."""


class LeaseExpiredError(JobError):
    """The lease is expired; re-claim is required before further writes."""


class LeaseConflictError(JobError):
    """The Job is already leased by another worker with a live lease.

    Carries the stable machine-readable code ``LEASE_CONFLICT``.  Only an
    absent or expired/released lease may be acquired (contract §5.3-2).
    """

    def __init__(self, message: str, *, job_id: str | None = None) -> None:
        super().__init__(message)
        self.job_id = job_id
        self.code = LEASE_CONFLICT_CODE


# ── Input contracts ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class StepInput:
    """Declarative JobStep input for :meth:`JobRepository.create_job`.

    Attributes:
        step_code: Stable logical name of the step (unique within the Job).
        position: Non-negative execution order within the Job.
        step_type: ``sync`` or ``async`` (contract §3).
        depends_on: Step codes that must be terminal-``completed`` or
            ``skipped`` before this step runs (Job-level DAG).
        resource_class: Capacity requirement; defaults to the Job's class.
        priority: Scheduling priority; defaults to the Job's priority.
        weight: Progress weight (Job progress = Σ step weight × step
            progress, contract §7.3).
        max_attempts: Per-step retry budget; defaults to the Job's budget.
        checkpoint: Initial checkpoint payload (schema-versioned JSON).
    """

    step_code: str
    position: int
    step_type: str = "sync"
    depends_on: tuple[str, ...] = ()
    resource_class: str | None = None
    priority: int | None = None
    weight: float = 1.0
    max_attempts: int | None = None
    checkpoint: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.step_code:
            raise JobStepCreationError("step_code must be a non-empty string")
        if self.position < 0:
            raise JobStepCreationError("position must be non-negative")
        if self.step_type not in STEP_TYPES:
            raise JobStepCreationError(
                f"step_type must be one of {STEP_TYPES}, got {self.step_type!r}"
            )
        if self.weight < 0:
            raise JobStepCreationError("weight must be non-negative")
        if self.max_attempts is not None and self.max_attempts < 1:
            raise JobStepCreationError("max_attempts must be >= 1")


@dataclass
class JobRecord:
    """Read model of a Job row (no ORM instances escape the repository)."""

    id: str
    workspace_id: str
    job_type: str
    owner_type: str
    owner_id: str
    parent_job_id: str | None
    predecessor_job_id: str | None
    state: str
    resource_class: str
    priority: int
    max_attempts: int
    attempt: int
    idempotency_key: str | None
    input_generation: str | None = None
    input_manifest: dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    error: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    revision: int = 1


@dataclass
class StepRecord:
    """Read model of a JobStep row."""

    id: str
    job_id: str
    step_code: str
    position: int
    step_type: str
    depends_on: list[str] = field(default_factory=list)
    state: str = "pending"
    resource_class: str = "cpu_light"
    priority: int = 50
    weight: float = 1.0
    attempt: int = 0
    max_attempts: int = 3
    checkpoint: dict[str, Any] | None = None
    progress: float = 0.0
    error: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    revision: int = 1


@dataclass
class LeaseRecord:
    """Read model of a JobLease row."""

    job_id: str
    worker_id: str
    lease_version: int
    fence_token: str
    acquired_at: datetime
    expires_at: datetime
    heartbeat_at: datetime
    ttl_seconds: int


@dataclass
class EventRecord:
    """Read model of a JobEvent row."""

    id: str
    job_id: str
    step_id: str | None
    step_code: str | None
    event_type: str
    from_state: str | None
    to_state: str | None
    actor: str
    worker_id: str | None
    fence_token: str | None
    reason_code: str | None
    revision: int | None
    details: dict[str, Any] | None
    created_at: datetime | None


@dataclass
class AttemptRecord:
    """Read model of a JobAttempt row (append-only history, contract §8.2)."""

    id: str
    job_id: str
    step_id: str | None
    step_code: str
    attempt: int
    worker_id: str
    fence_token: str
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    started_at: datetime
    finished_at: datetime | None


def _job_record(job: Job) -> JobRecord:
    return JobRecord(
        id=job.id,
        workspace_id=job.workspace_id,
        job_type=job.job_type,
        owner_type=job.owner_type,
        owner_id=job.owner_id,
        parent_job_id=job.parent_job_id,
        predecessor_job_id=job.predecessor_job_id,
        state=job.state,
        resource_class=job.resource_class,
        priority=job.priority,
        max_attempts=job.max_attempts,
        attempt=job.attempt,
        idempotency_key=job.idempotency_key,
        input_generation=job.input_generation,
        input_manifest=parse_json(job.input_manifest_json, {}),
        progress=job.progress,
        error=parse_json(job.error_json, None),
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        revision=job.revision,
    )


def _step_record(step: JobStep) -> StepRecord:
    return StepRecord(
        id=step.id,
        job_id=step.job_id,
        step_code=step.step_code,
        position=step.position,
        step_type=step.step_type,
        depends_on=list(parse_json(step.depends_on_json, [])),
        state=step.state,
        resource_class=step.resource_class,
        priority=step.priority,
        weight=step.weight,
        attempt=step.attempt,
        max_attempts=step.max_attempts,
        checkpoint=parse_json(step.checkpoint_json, None),
        progress=step.progress,
        error=parse_json(step.error_json, None),
        started_at=step.started_at,
        finished_at=step.finished_at,
        revision=step.revision,
    )


def _lease_record(lease: JobLease) -> LeaseRecord:
    return LeaseRecord(
        job_id=lease.job_id,
        worker_id=lease.worker_id,
        lease_version=lease.lease_version,
        fence_token=lease.fence_token,
        acquired_at=lease.acquired_at,
        expires_at=lease.expires_at,
        heartbeat_at=lease.heartbeat_at,
        ttl_seconds=lease.ttl_seconds,
    )


def _event_record(event: JobEvent) -> EventRecord:
    return EventRecord(
        id=event.id,
        job_id=event.job_id,
        step_id=event.step_id,
        step_code=event.step_code,
        event_type=event.event_type,
        from_state=event.from_state,
        to_state=event.to_state,
        actor=event.actor,
        worker_id=event.worker_id,
        fence_token=event.fence_token,
        reason_code=event.reason_code,
        revision=event.revision,
        details=parse_json(event.details_json, None),
        created_at=event.created_at,
    )


def _attempt_record(attempt: JobAttempt) -> AttemptRecord:
    return AttemptRecord(
        id=attempt.id,
        job_id=attempt.job_id,
        step_id=attempt.step_id,
        step_code=attempt.step_code,
        attempt=attempt.attempt,
        worker_id=attempt.worker_id,
        fence_token=attempt.fence_token,
        result=parse_json(attempt.result_json, None),
        error=parse_json(attempt.error_json, None),
        started_at=attempt.started_at,
        finished_at=attempt.finished_at,
    )


# ── Repository ───────────────────────────────────────────────────────────────


class JobRepository:
    """Transactional durable-job store.

    The repository never commits on its own: the caller owns the transaction
    (persistence domain contract §6).  All state changes inside one method
    call happen in the caller's single session transaction; a failed call
    leaves the transaction untouched for the caller to roll back.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Creation ────────────────────────────────────────────────────────────

    def create_job(
        self,
        *,
        workspace_id: str,
        job_type: str,
        owner_type: str,
        owner_id: str,
        input_manifest: dict[str, Any],
        idempotency_key: str | None = None,
        input_generation: str | None = None,
        resource_class: str = "cpu_light",
        priority: int = 50,
        max_attempts: int = 3,
        state: str = "queued",
        parent_job_id: str | None = None,
        steps: Sequence[StepInput] = (),
        actor: str = "api",
    ) -> JobRecord:
        """Create a Job and its steps atomically with a ``created`` event.

        Steps are validated and inserted in the same transaction as the Job;
        if any step is invalid the whole creation fails and nothing is
        written (contract §7.1: one transaction per atomic unit).

        Raises:
            JobCreationError: invalid job attributes or state.
            IdempotencyKeyInUse: an active or completed Job already exists
                for ``(workspace_id, idempotency_key)``.
            JobStepCreationError: invalid step plan (duplicate codes,
                duplicate positions, unknown/cyclic dependencies, or a step
                target state that is not ``pending``).
        """
        self._validate_job_attributes(
            workspace_id=workspace_id,
            job_type=job_type,
            owner_type=owner_type,
            owner_id=owner_id,
            resource_class=resource_class,
            priority=priority,
            max_attempts=max_attempts,
            state=state,
            actor=actor,
        )
        if state not in JOB_STATES:
            raise JobCreationError(f"state must be one of {JOB_STATES}, got {state!r}")
        if state in TERMINAL_STATES:
            raise JobCreationError(
                f"a new Job cannot be created in terminal state {state!r}; "
                "use create_successor for retry/restart"
            )

        existing = self._find_existing_for_key(workspace_id, idempotency_key)
        if existing is not None:
            if existing.state in COMPLETED_REUSE_STATES:
                return _job_record(existing)
            raise IdempotencyKeyInUse(
                f"idempotency key {idempotency_key!r} is already in use by "
                f"active job {existing.id} (state={existing.state})",
                key=idempotency_key or "",
                job_id=existing.id,
            )

        if parent_job_id is not None:
            parent = self._session.get(Job, parent_job_id)
            if parent is None:
                raise JobCreationError(f"parent_job_id {parent_job_id!r} does not exist")
            if parent.workspace_id != workspace_id:
                raise JobCreationError(
                    "parent Job must belong to the same workspace (contract §3)"
                )

        # Guard the partial unique index ourselves so the failure mode is the
        # stable IdempotencyKeyInUse, not a raw IntegrityError.  The index
        # stays as the concurrency backstop (two sessions racing the same key
        # are still rejected by the database).
        if idempotency_key is not None:
            blocker = self._session.scalar(
                select(Job).where(
                    Job.workspace_id == workspace_id,
                    Job.idempotency_key == idempotency_key,
                    Job.input_generation == input_generation,
                )
            )
            if blocker is not None:
                if blocker.state in COMPLETED_REUSE_STATES:
                    return _job_record(blocker)
                raise IdempotencyKeyInUse(
                    f"idempotency key {idempotency_key!r} is already in use by "
                    f"active job {blocker.id} (state={blocker.state})",
                    key=idempotency_key,
                    job_id=blocker.id,
                )

        now = datetime.now(UTC)
        job = Job(
            workspace_id=workspace_id,
            job_type=job_type,
            owner_type=owner_type,
            owner_id=owner_id,
            parent_job_id=parent_job_id,
            state=state,
            resource_class=resource_class,
            priority=priority,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            input_generation=input_generation,
            input_manifest_json=json.dumps(input_manifest, sort_keys=True),
            created_at=now,
            updated_at=now,
            revision=create_job_revision(),
        )
        self._session.add(job)
        self._session.flush()
        self._create_steps_for_job(job, steps, resource_class, priority, max_attempts)

        self._append_event(
            job=job,
            event_type="created",
            from_state=None,
            to_state=state,
            actor=actor,
            reason_code=None,
            revision=job.revision,
            details={"manifest_fingerprint": self._fingerprint(input_manifest)},
        )
        return _job_record(job)

    def create_successor(
        self,
        *,
        predecessor_job_id: str,
        input_manifest: dict[str, Any],
        idempotency_key: str | None = None,
        input_generation: str | None = None,
        steps: Sequence[StepInput] = (),
        resource_class: str | None = None,
        priority: int | None = None,
        max_attempts: int | None = None,
        actor: str = "api",
    ) -> JobRecord:
        """Create the successor of a terminal failed/cancelled Job (§6.4).

        The predecessor row is never mutated.  The successor gets a fresh id,
        inherits the predecessor's job_type/owner/workspace and — when
        *idempotency_key* is omitted — reuses the predecessor's key and
        generation, which keeps the ``(workspace, key)`` uniqueness rule
        (one active/completed Job per key) intact.  ``predecessor_job_id``
        is globally unique, so each predecessor has at most one successor.

        Raises:
            JobNotFoundError: the predecessor does not exist.
            InvalidStateTransition: the predecessor is not terminal.
            IdempotencyKeyInUse: the key already has an active or completed
                Job (including a successor created earlier).
        """
        predecessor = self._session.get(Job, predecessor_job_id)
        if predecessor is None:
            raise JobNotFoundError(f"Job {predecessor_job_id!r} not found")
        if predecessor.state not in TERMINAL_STATES:
            raise InvalidStateTransition(
                f"cannot create a successor for Job {predecessor.id!r}: "
                f"predecessor state {predecessor.state!r} is not terminal",
                job_id=predecessor.id,
            )

        key = idempotency_key if idempotency_key is not None else predecessor.idempotency_key
        generation = (
            input_generation
            if input_generation is not None
            else predecessor.input_generation
        )
        existing = self._find_existing_for_key(
            predecessor.workspace_id, key, generation
        )
        if existing is not None and existing.id != predecessor.id:
            if existing.state in COMPLETED_REUSE_STATES:
                return _job_record(existing)
            raise IdempotencyKeyInUse(
                f"idempotency key {key!r} is already in use by active job "
                f"{existing.id} (state={existing.state})",
                key=key or "",
                job_id=existing.id,
            )
        if (
            existing is not None
            and existing.id == predecessor.id
            and existing.state in COMPLETED_REUSE_STATES
        ):
            # A completed logical run is never retried (contract §8.1):
            # the completed Job itself is the reuse result.
            return _job_record(existing)

        # Exactly one successor per predecessor (contract §8.5): the unique
        # constraint on predecessor_job_id is the enforcement point, and this
        # pre-check turns the raw IntegrityError into the stable conflict.
        successor_exists = self._session.scalar(
            select(Job.id).where(Job.predecessor_job_id == predecessor.id)
        )
        if successor_exists is not None:
            raise IdempotencyKeyInUse(
                f"predecessor {predecessor.id!r} already has successor "
                f"{successor_exists} (at most one successor per "
                "predecessor, contract §8.5)",
                key=key or "",
                job_id=predecessor.id,
            )

        now = datetime.now(UTC)
        successor = Job(
            workspace_id=predecessor.workspace_id,
            job_type=predecessor.job_type,
            owner_type=predecessor.owner_type,
            owner_id=predecessor.owner_id,
            predecessor_job_id=predecessor.id,
            state="queued",
            resource_class=resource_class or predecessor.resource_class,
            priority=predecessor.priority if priority is None else priority,
            max_attempts=predecessor.max_attempts if max_attempts is None else max_attempts,
            idempotency_key=key,
            input_generation=generation,
            input_manifest_json=json.dumps(input_manifest, sort_keys=True),
            created_at=now,
            updated_at=now,
            revision=create_job_revision(),
        )
        try:
            self._session.add(successor)
            self._session.flush()
        except IntegrityError as exc:
            # Concurrency backstop: the partial unique index enforces one
            # active/completed owner per (workspace, key, generation) and the
            # unique predecessor_job_id enforces one successor per
            # predecessor.  A racing writer loses with the stable conflict.
            raise IdempotencyKeyInUse(
                f"idempotency key {key!r} is already in use by another active "
                f"or completed Job in workspace {predecessor.workspace_id} "
                f"(or predecessor {predecessor.id!r} already has a successor)",
                key=key or "",
                job_id=predecessor.id,
            ) from exc

        _ = self._create_steps_for_job(
            successor,
            steps,
            successor.resource_class,
            successor.priority,
            successor.max_attempts,
        )
        self._append_event(
            job=successor,
            event_type="created",
            from_state=None,
            to_state="queued",
            actor=actor,
            reason_code=None,
            revision=successor.revision,
            details={"manifest_fingerprint": self._fingerprint(input_manifest)},
        )
        return _job_record(successor)

    def _create_steps_for_job(
        self,
        job: Job,
        steps: Sequence[StepInput],
        job_resource_class: str,
        job_priority: int,
        job_max_attempts: int,
    ) -> list[StepRecord]:
        """Insert validated JobStep rows for *job* in the current transaction.

        Validation happens before any insert: duplicate codes, duplicate
        positions, unknown dependency codes, cyclic dependencies and step
        target states other than ``pending`` all fail without writing.
        """
        codes: set[str] = set()
        positions: set[int] = set()
        for step in steps:
            if step.step_code in codes:
                raise JobStepCreationError(
                    f"duplicate step_code {step.step_code!r} in step plan"
                )
            if step.position in positions:
                raise JobStepCreationError(
                    f"duplicate position {step.position} in step plan"
                )
            codes.add(step.step_code)
            positions.add(step.position)

        known = {step.step_code for step in steps}
        for step in steps:
            unknown = [d for d in step.depends_on if d not in known]
            if unknown:
                raise JobStepCreationError(
                    f"step {step.step_code!r} depends on unknown steps: {unknown}"
                )
            if step.step_code in step.depends_on:
                raise JobStepCreationError(
                    f"step {step.step_code!r} cannot depend on itself"
                )

        # Cycle detection over the Job-level DAG (contract §3: cyclic
        # dependencies rejected at creation).  Walk each step's first
        # dependency edge; revisiting a node on the walk proves a cycle.
        def _follow_cycle(start: str) -> bool:
            seen: set[str] = set()
            current = start
            while True:
                if current in seen:
                    return True
                seen.add(current)
                step = next((s for s in steps if s.step_code == current), None)
                if step is None or not step.depends_on:
                    return False
                current = step.depends_on[0]

        for step in steps:
            if _follow_cycle(step.step_code):
                raise JobStepCreationError(
                    f"cyclic dependency detected involving step {step.step_code!r}"
                )

        inserted: list[JobStep] = []
        for step in steps:
            row = JobStep(
                job_id=job.id,
                step_code=step.step_code,
                position=step.position,
                step_type=step.step_type,
                depends_on_json=json.dumps(list(step.depends_on)),
                state="pending",
                resource_class=step.resource_class or job_resource_class,
                priority=step.priority if step.priority is not None else job_priority,
                weight=step.weight,
                attempt=0,
                max_attempts=step.max_attempts or job_max_attempts,
                checkpoint_json=(
                    json.dumps(step.checkpoint) if step.checkpoint is not None else None
                ),
                progress=0.0,
                revision=create_job_revision(),
            )
            self._session.add(row)
            inserted.append(row)
        self._session.flush()
        return [_step_record(row) for row in inserted]

    def _find_existing_for_key(
        self, workspace_id: str, idempotency_key: str | None, input_generation: str | None = None
    ) -> Job | None:
        """Return the Job blocking the ``(workspace, key, generation)`` rule.

        Uniqueness is scoped per workspace and per input generation (contract
        §8.1: ``(workspace_id, idempotency_key)`` is unique among terminal
        Jobs too; a fresh logical run bumps ``input_generation`` and yields a
        different key).  The partial unique index ``uq_job_idempotency_key``
        enforces this at the database level — only non-terminal rows with a
        non-NULL key are indexed, so terminal failed/cancelled predecessors
        keep their full audit identity and the same key may be reused by a
        successor.
        """
        if idempotency_key is None:
            return None
        return self._session.scalar(
            select(Job).where(
                Job.workspace_id == workspace_id,
                Job.idempotency_key == idempotency_key,
                Job.input_generation == input_generation,
            )
        )

    # ── Read ────────────────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> JobRecord:
        """Load a Job by id; raise :class:`JobNotFoundError` when absent."""
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        return _job_record(job)

    def get_step(self, step_id: str) -> StepRecord:
        """Load a JobStep by id; raise :class:`JobStepNotFoundError`."""
        step = self._session.get(JobStep, step_id)
        if step is None:
            raise JobStepNotFoundError(f"JobStep {step_id!r} not found")
        return _step_record(step)

    def list_jobs(
        self,
        workspace_id: str,
        *,
        states: Iterable[str] | None = None,
        owner_type: str | None = None,
        owner_id: str | None = None,
        limit: int = 100,
    ) -> list[JobRecord]:
        """List Jobs for a workspace, newest first, bounded by *limit*."""
        query = select(Job).where(Job.workspace_id == workspace_id)
        if states is not None:
            query = query.where(Job.state.in_(list(states)))
        if owner_type is not None:
            query = query.where(Job.owner_type == owner_type)
        if owner_id is not None:
            query = query.where(Job.owner_id == owner_id)
        query = query.order_by(Job.created_at.desc()).limit(max(1, limit))
        return [_job_record(row) for row in self._session.scalars(query).all()]

    def list_steps(self, job_id: str) -> list[StepRecord]:
        """List a Job's steps ordered by position."""
        rows = self._session.scalars(
            select(JobStep)
            .where(JobStep.job_id == job_id)
            .order_by(JobStep.position)
        ).all()
        return [_step_record(row) for row in rows]

    def list_events(self, job_id: str, *, limit: int = 100) -> list[EventRecord]:
        """List the append-only JobEvent log, newest first."""
        rows = self._session.scalars(
            select(JobEvent)
            .where(JobEvent.job_id == job_id)
            .order_by(JobEvent.created_at.desc())
            .limit(max(1, limit))
        ).all()
        return [_event_record(row) for row in rows]

    def list_attempts(self, job_id: str, *, limit: int = 100) -> list[AttemptRecord]:
        """List append-only attempt history, newest first."""
        rows = self._session.scalars(
            select(JobAttempt)
            .where(JobAttempt.job_id == job_id)
            .order_by(JobAttempt.started_at.desc())
            .limit(max(1, limit))
        ).all()
        return [_attempt_record(row) for row in rows]

    # ── Guarded transitions ─────────────────────────────────────────────────

    def transition_job(
        self,
        job_id: str,
        to_state: str,
        *,
        actor: str,
        expected_revision: int,
        fence_token: str | None = None,
        reason_code: str | None = None,
        error: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> JobRecord:
        """Apply one guarded Job state transition in the caller's transaction.

        Guards (contract §4.3/§4.5):
        - the endpoint must exist in the transition table;
        - the Job must currently be in the *expected* state (optimistic
          concurrency on ``revision``);
        - terminal rows never transition (the table has no terminal edges and
          the row check below refuses them regardless);
        - worker transitions on a leased Job must present the current fence
          token (contract §5.3-1).

        Every accepted transition bumps ``revision`` and appends a JobEvent
        with actor/revision in the same transaction (contract §10.2).

        Raises:
            JobNotFoundError: unknown Job.
            InvalidStateTransition: disallowed endpoint, terminal row, or
                revision mismatch.
            FencedWorkerError: the supplied fence token does not match the
                current lease.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")

        allowed = JOB_TRANSITIONS.get(job.state, frozenset())
        if to_state not in allowed:
            raise InvalidStateTransition(
                f"invalid Job transition {job.state!r} -> {to_state!r} for "
                f"Job {job_id} (endpoint not allowed)",
                job_id=job_id,
            )
        if job.state in TERMINAL_STATES:
            raise InvalidStateTransition(
                f"Job {job_id} is terminal ({job.state!r}); terminal rows are "
                "immutable (contract §4.5-4)",
                job_id=job_id,
            )
        if job.revision != expected_revision:
            raise InvalidStateTransition(
                f"revision mismatch for Job {job_id}: expected "
                f"{expected_revision}, current {job.revision}",
                job_id=job_id,
            )
        if actor not in JOB_ACTORS:
            raise InvalidStateTransition(
                f"unknown actor {actor!r} for Job transition {job.state!r} -> {to_state!r}",
                job_id=job_id,
            )

        # Worker transitions on a leased Job always require the current fence
        # token (contract §5.3-1).  Scheduler/reconciler/system transitions
        # (e.g. running -> fenced, fenced -> queued) are authority writes and
        # do not carry a worker token.
        if actor == "worker":
            self._require_fence_token(job, fence_token)

        from_state = job.state
        job.state = to_state
        job.revision += 1
        if to_state == "running" and job.started_at is None:
            job.started_at = datetime.now(UTC)
        if to_state in TERMINAL_STATES and job.finished_at is None:
            job.finished_at = datetime.now(UTC)
        if error is not None:
            job.error_json = json.dumps(error, sort_keys=True)
        if to_state == "failed" and error is None:
            job.error_json = json.dumps(
                {"error_code": "UNKNOWN", "message": "no error envelope"}, sort_keys=True
            )

        self._append_event(
            job=job,
            event_type="transition",
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            fence_token=fence_token,
            reason_code=reason_code,
            revision=job.revision,
            details=details,
        )
        return _job_record(job)

    def transition_step(
        self,
        step_id: str,
        to_state: str,
        *,
        actor: str,
        expected_revision: int,
        fence_token: str | None = None,
        reason_code: str | None = None,
        error: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> StepRecord:
        """Apply one guarded JobStep state transition (contract §4.4).

        Guards mirror :meth:`transition_job` (endpoint table, revision,
        terminal immutability, fence token when the Job is leased).
        """
        step = self._session.get(JobStep, step_id)
        if step is None:
            raise JobStepNotFoundError(f"JobStep {step_id!r} not found")

        allowed = JOB_STEP_TRANSITIONS.get(step.state, frozenset())
        if to_state not in allowed:
            raise InvalidStateTransition(
                f"invalid JobStep transition {step.state!r} -> {to_state!r} "
                f"for step {step_id}",
                job_id=step.job_id,
            )
        if step.state in TERMINAL_STATES:
            raise InvalidStateTransition(
                f"JobStep {step_id} is terminal ({step.state!r}); terminal "
                "rows are immutable (contract §4.5-4)",
                job_id=step.job_id,
            )
        if step.revision != expected_revision:
            raise InvalidStateTransition(
                f"revision mismatch for JobStep {step_id}: expected "
                f"{expected_revision}, current {step.revision}",
                job_id=step.job_id,
            )
        if actor not in JOB_ACTORS:
            raise InvalidStateTransition(
                f"unknown actor {actor!r} for JobStep transition "
                f"{step.state!r} -> {to_state!r}",
                job_id=step.job_id,
            )

        job = self._session.get(Job, step.job_id)
        if job is not None and actor == "worker":
            self._require_fence_token(job, fence_token)

        from_state = step.state
        step.state = to_state
        step.revision += 1
        if to_state == "running" and step.started_at is None:
            step.started_at = datetime.now(UTC)
        if to_state in TERMINAL_STATES and step.finished_at is None:
            step.finished_at = datetime.now(UTC)
        if error is not None:
            step.error_json = json.dumps(error, sort_keys=True)

        self._append_event(
            job=self._session.get(Job, step.job_id) or step.job,
            step=step,
            event_type="step_transition",
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            fence_token=fence_token,
            reason_code=reason_code,
            revision=step.revision,
            details=details,
        )
        return _step_record(step)

    # ── Attempt accounting ──────────────────────────────────────────────────

    def record_attempt(
        self,
        *,
        job_id: str,
        step_id: str | None,
        step_code: str,
        attempt: int,
        worker_id: str,
        fence_token: str,
        result: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        finished_at: datetime | None = None,
    ) -> AttemptRecord:
        """Append one attempt-history row (contract §8.2, append-only).

        The row is inserted in the caller's transaction; the unique
        constraint ``(job_id, step_id, attempt)`` (and
        ``(job_id, step_code, attempt)``) rejects duplicate records.
        """
        if attempt < 1:
            raise JobError("attempt number must be >= 1")
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        if job.state in ("running", "cancelling"):
            # Attempt accounting is a worker-owned write: missing AND stale
            # tokens both raise FENCED_WORKER (contract §5.3-1).
            self._require_fence_token(job, fence_token)
        row = JobAttempt(
            job_id=job_id,
            step_id=step_id,
            step_code=step_code,
            attempt=attempt,
            worker_id=worker_id,
            fence_token=fence_token,
            result_json=json.dumps(result, sort_keys=True) if result is not None else None,
            error_json=json.dumps(error, sort_keys=True) if error is not None else None,
            finished_at=finished_at,
        )
        self._session.add(row)
        self._session.flush()
        return _attempt_record(row)

    def latest_attempt_number(self, job_id: str, step_id: str) -> int:
        """Return the highest attempt row number for ``(job, step)`` (0 if none).

        Attempt rows are append-only and unique per ``(job_id, step_id,
        attempt)`` (contract §8.2).  A worker re-claiming a Job after a
        reconciler requeue numbers its per-claim attempts from this durable
        base, so no attempt row is ever duplicated across claims.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        step = self._session.get(JobStep, step_id)
        if step is None:
            raise JobStepNotFoundError(f"JobStep {step_id!r} not found")
        return int(
            self._session.scalar(
                select(JobAttempt.attempt)
                .where(
                    JobAttempt.job_id == job_id,
                    JobAttempt.step_id == step_id,
                )
                .order_by(JobAttempt.attempt.desc())
                .limit(1)
            )
            or 0
        )

    # ── Attempt accounting (reconciler authority, contract §8.2) ─────────────

    def bump_job_attempt(self, job_id: str) -> int:
        """Increment the Job-level attempt counter (reconciler requeue).

        Contract §8.2: every re-claim (requeue after fence) increments the
        attempt counter in the same transaction that acquires the lease.  The
        reconciler performs the bump in the same transaction as the
        ``fenced -> queued`` transition so attempt accounting is atomic with
        the state change.  The bump is unconditional (no revision guard): the
        reconciler has already verified the Job is in ``fenced``/``queued``
        and holds the only writer path for that row.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        job.attempt += 1
        return job.attempt

    def bump_step_attempt(self, step_id: str) -> int:
        """Increment a JobStep's attempt counter (reconciler requeue).

        The step counter tracks the number of times the step has been
        (re)claimed since its last ``completed``; the worker's per-claim
        attempt rows (attempt 1..N within a claim) are numbered from this
        durable base so no attempt row is ever duplicated across claims.
        """
        step = self._session.get(JobStep, step_id)
        if step is None:
            raise JobStepNotFoundError(f"JobStep {step_id!r} not found")
        step.attempt += 1
        return step.attempt

    # ── Progress / checkpoint / error envelopes ─────────────────────────────

    def update_progress(
        self, job_id: str, progress: float, *, fence_token: str | None = None
    ) -> JobRecord:
        """Persist Job progress (bounded 0..100; contract §7.3).

        Progress is a worker-owned write: while the Job is running/cancelling
        a missing OR stale fence token raises ``FENCED_WORKER``.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        if job.state in ("running", "cancelling"):
            self._require_fence_token(job, fence_token)
        job.progress = max(0.0, min(100.0, progress))
        return _job_record(job)

    def update_step_progress(
        self, step_id: str, progress: float, *, fence_token: str | None = None
    ) -> StepRecord:
        """Persist JobStep progress (bounded 0..100).

        While the owning Job is running/cancelling a missing OR stale fence
        token raises ``FENCED_WORKER``.
        """
        step = self._session.get(JobStep, step_id)
        if step is None:
            raise JobStepNotFoundError(f"JobStep {step_id!r} not found")
        job = self._session.get(Job, step.job_id)
        if job is not None and job.state in ("running", "cancelling"):
            self._require_fence_token(job, fence_token)
        step.progress = max(0.0, min(100.0, progress))
        return _step_record(step)

    def write_checkpoint(
        self,
        step_id: str,
        checkpoint: dict[str, Any],
        *,
        fence_token: str | None = None,
    ) -> StepRecord:
        """Persist a versioned step checkpoint atomically with its progress.

        The checkpoint must be schema-versioned (contract §7.2).  A worker
        write while the Job is running/cancelling is fenced: a missing OR
        stale token raises ``FENCED_WORKER`` (contract §5.3-1).
        """
        step = self._session.get(JobStep, step_id)
        if step is None:
            raise JobStepNotFoundError(f"JobStep {step_id!r} not found")
        if "schema_version" not in checkpoint:
            raise JobError(
                "checkpoint must carry a schema_version (contract §7.2 fail-closed)"
            )
        job = self._session.get(Job, step.job_id)
        if job is not None and job.state in ("running", "cancelling"):
            self._require_fence_token(job, fence_token)
        step.checkpoint_json = json.dumps(checkpoint, sort_keys=True)
        return _step_record(step)

    def set_job_error(
        self, job_id: str, error: dict[str, Any], *, fence_token: str | None = None
    ) -> JobRecord:
        """Persist the final error envelope (contract §10.1).

        While the Job is running/cancelling a missing OR stale fence token
        raises ``FENCED_WORKER``.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        if job.state in ("running", "cancelling"):
            self._require_fence_token(job, fence_token)
        job.error_json = json.dumps(error, sort_keys=True)
        return _job_record(job)

    # ── Leases (contract §5) ────────────────────────────────────────────────

    def acquire_lease(
        self,
        job_id: str,
        worker_id: str,
        *,
        ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    ) -> LeaseRecord:
        """Atomically claim the Job for *worker_id* for a bounded window.

        The claim is a guarded compare-and-swap on the ``job_lease`` row
        (contract §5.3-2): a live unexpired lease held by ANY worker (self or
        another) is rejected with :class:`LeaseConflictError`; only an absent
        or expired/released lease may be acquired.  Reacquisition after
        expiry/release monotonically bumps ``lease_version`` (and the Job's
        ``revision``) and issues a fresh random fence token (contract §5.1).
        Two sessions racing the same Job can never both win — the SQLite
        statement is a single atomic write (contract §15-1).

        Raises:
            JobNotFoundError: unknown Job.
            JobError: invalid TTL or the Job is not in a claimable state.
            LeaseConflictError: another worker holds a live lease.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        if ttl_seconds < 1:
            raise JobError("ttl_seconds must be >= 1")
        if job.state not in ("queued", "running", "cancelling", "fenced"):
            raise JobError(
                f"Job {job_id} in state {job.state!r} cannot be leased"
            )

        now = datetime.now(UTC)
        expires = now + timedelta(seconds=ttl_seconds)
        token = uuid.uuid4().hex

        def _aware(dt: datetime) -> datetime:
            """SQLite may return naive datetimes; normalize to aware UTC."""
            return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

        # Step 1 — atomic INSERT ... ON CONFLICT DO NOTHING.  This is the
        # single guarded write that decides the race: exactly one session
        # inserts the first lease row (lease_version=1); every other session
        # sees rowcount 0 and falls through to the conflict check below.
        stmt = sqlite_insert(JobLease).values(
            job_id=job_id,
            worker_id=worker_id,
            lease_version=1,
            fence_token=token,
            acquired_at=now,
            expires_at=expires,
            heartbeat_at=now,
            ttl_seconds=ttl_seconds,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=[JobLease.job_id])
        result = cast("CursorResult[Any]", self._session.execute(stmt))
        if result.rowcount == 1:
            self._session.flush()
            self._bump_job_revision(job)
            return self.get_lease(job_id) or _lease_record(
                JobLease(
                    job_id=job_id,
                    worker_id=worker_id,
                    lease_version=1,
                    fence_token=token,
                    acquired_at=now,
                    expires_at=expires,
                    heartbeat_at=now,
                    ttl_seconds=ttl_seconds,
                )
            )

        # Step 2 — a lease row exists.  Only an expired/released lease may be
        # re-claimed: atomic guarded UPDATE that matches the exact current
        # lease_version and requires the old expiry to have passed.
        existing = self._session.get(JobLease, job_id)
        if existing is None:
            # The INSERT lost to a concurrent commit; re-run it once.
            result = cast("CursorResult[Any]", self._session.execute(stmt))
            if result.rowcount == 1:
                self._session.flush()
                self._bump_job_revision(job)
                return self.get_lease(job_id) or _lease_record(
                    JobLease(
                        job_id=job_id,
                        worker_id=worker_id,
                        lease_version=1,
                        fence_token=token,
                        acquired_at=now,
                        expires_at=expires,
                        heartbeat_at=now,
                        ttl_seconds=ttl_seconds,
                    )
                )
            existing = self._session.get(JobLease, job_id)
            if existing is None:  # pragma: no cover - defensive
                raise LeaseConflictError(
                    f"lease claim lost for Job {job_id} (concurrent writer)",
                    job_id=job_id,
                )

        if _aware(existing.expires_at) > now:
            raise LeaseConflictError(
                f"Job {job_id} is already leased by worker "
                f"{existing.worker_id!r} until {existing.expires_at.isoformat()} "
                f"(lease_version={existing.lease_version}); only an absent or "
                "expired/released lease may be acquired (contract §5.3-2)",
                job_id=job_id,
            )

        old_version = existing.lease_version
        next_version = old_version + 1
        # Compare expiry in SQL (not via the ORM evaluator, which would mix
        # naive loaded values with aware bound parameters).
        updated = update(JobLease).where(
            JobLease.job_id == job_id,
            JobLease.lease_version == old_version,
            sa_text("expires_at <= :now").bindparams(now=now),
        ).values(
            worker_id=worker_id,
            lease_version=next_version,
            fence_token=token,
            acquired_at=now,
            expires_at=expires,
            heartbeat_at=now,
            ttl_seconds=ttl_seconds,
        )
        result = cast("CursorResult[Any]", self._session.execute(updated))
        if result.rowcount != 1:
            # A concurrent re-claim won the CAS; our claim is rejected.
            raise LeaseConflictError(
                f"lease re-claim lost for Job {job_id} (concurrent claimant)",
                job_id=job_id,
            )
        self._session.flush()
        self._bump_job_revision(job)
        return self.get_lease(job_id) or _lease_record(
            JobLease(
                job_id=job_id,
                worker_id=worker_id,
                lease_version=next_version,
                fence_token=token,
                acquired_at=now,
                expires_at=expires,
                heartbeat_at=now,
                ttl_seconds=ttl_seconds,
            )
        )

    def _bump_job_revision(self, job: Job) -> None:
        """Increment the Job's optimistic-concurrency revision on lease (re)claim."""
        job.revision += 1

    def heartbeat_lease(
        self, job_id: str, worker_id: str, fence_token: str, *, ttl_seconds: int | None = None
    ) -> LeaseRecord:
        """Renew the lease; fails when the token no longer matches (§5.3-1).

        The row update carries the worker's fence token; a mismatch means the
        worker was fenced and its heartbeat is dropped.
        """
        lease = self._session.get(JobLease, job_id)
        if lease is None:
            raise LeaseNotFoundError(f"no lease for Job {job_id!r}")
        if lease.worker_id != worker_id or lease.fence_token != fence_token:
            raise FencedWorkerError(
                f"heartbeat rejected for Job {job_id}: fence token mismatch "
                "(worker was fenced)",
                job_id=job_id,
            )
        now = datetime.now(UTC)
        ttl = lease.ttl_seconds if ttl_seconds is None else ttl_seconds
        if ttl < 1:
            raise JobError("ttl_seconds must be >= 1")
        lease.heartbeat_at = now
        lease.expires_at = now + timedelta(seconds=ttl)
        lease.ttl_seconds = ttl
        return _lease_record(lease)

    def release_lease(self, job_id: str, worker_id: str, fence_token: str) -> None:
        """Release the lease held by *worker_id* (graceful shutdown, §5.3-5).

        Expiring the lease with ``expires_at = now`` marks the claim released
        so the reconciler can re-claim from the current checkpoint.
        """
        lease = self._session.get(JobLease, job_id)
        if lease is None:
            raise LeaseNotFoundError(f"no lease for Job {job_id!r}")
        if lease.worker_id != worker_id or lease.fence_token != fence_token:
            raise FencedWorkerError(
                f"lease release rejected for Job {job_id}: fence token mismatch",
                job_id=job_id,
            )
        now = datetime.now(UTC)
        lease.expires_at = now
        lease.heartbeat_at = now

    def invalidate_lease(self, job_id: str) -> LeaseRecord | None:
        """Atomically invalidate a Job's lease row (contract §5.3-2).

        This is the reconciler's fencing primitive: it replaces the current
        ``fence_token`` with a unique sentinel (the token is the enforcement
        point, §5.3-1, so the old worker's every subsequent write is rejected
        with ``FENCED_WORKER``) and marks the lease released
        (``expires_at = now``) so it can be re-claimed from the current
        checkpoint.  ``lease_version`` is NOT bumped: the lease row is
        *retired*, not re-acquired — a re-claim by a new worker later bumps
        the version and issues a fresh token.  The sentinel is a non-empty
        random value because the schema CHECK ``ck_job_lease_token_nonempty``
        forbids an empty token.  The caller owns the transaction; the
        invalidation commits with the caller's ``fenced`` state transition
        (one atomic unit per Job, contract §5.3-2).
        """
        lease = self._session.get(JobLease, job_id)
        if lease is None:
            return None
        now = datetime.now(UTC)
        lease.fence_token = f"fenced:{uuid.uuid4().hex}"
        lease.expires_at = now
        lease.heartbeat_at = now
        return _lease_record(lease)

    def get_lease(self, job_id: str) -> LeaseRecord | None:
        """Return the current lease row, or None when the Job has no lease."""
        lease = self._session.get(JobLease, job_id)
        return _lease_record(lease) if lease is not None else None

    def _require_fence_token(self, job: Job, fence_token: str | None) -> None:
        """Enforce the fence token for a leased Job (contract §5.3-1).

        The token is the enforcement point: any worker write without a token
        or with a token that does not match the current lease row is rejected
        with ``FENCED_WORKER``.
        """
        if fence_token is None:
            raise FencedWorkerError(
                f"fence token required for worker write on Job {job.id}",
                job_id=job.id,
            )
        lease = self._session.get(JobLease, job.id)
        if lease is None:
            raise FencedWorkerError(
                f"no lease for Job {job.id}; worker writes require a valid "
                "lease (contract §5.3-1)",
                job_id=job.id,
            )
        if lease.fence_token != fence_token:
            raise FencedWorkerError(
                f"fence token mismatch for Job {job.id}: worker was fenced "
                "(contract §5.3-3)",
                job_id=job.id,
            )

    # ── Delete ──────────────────────────────────────────────────────────────

    def delete_job(self, job_id: str) -> None:
        """Delete a Job row (active rows only).

        Terminal rows are immutable and refuse deletion (contract §4.5-4);
        their retention/cleanup is a future explicit workflow.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found")
        if job.state in TERMINAL_STATES:
            raise JobAlreadyTerminalError(
                f"Job {job_id} is terminal ({job.state!r}); terminal rows are "
                "immutable and cannot be deleted"
            )
        self._session.delete(job)
        self._session.flush()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _append_event(
        self,
        *,
        job: Job,
        step: JobStep | None = None,
        event_type: str,
        from_state: str | None,
        to_state: str | None,
        actor: str,
        fence_token: str | None = None,
        reason_code: str | None = None,
        revision: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> EventRecord:
        event = JobEvent(
            job_id=job.id,
            step_id=step.id if step is not None else None,
            step_code=step.step_code if step is not None else None,
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            worker_id=fence_token and self._worker_for_token(job.id, fence_token),
            fence_token=fence_token,
            reason_code=reason_code,
            revision=revision,
            details_json=(
                json.dumps(details, sort_keys=True) if details is not None else None
            ),
        )
        self._session.add(event)
        self._session.flush()
        return _event_record(event)

    def _worker_for_token(self, job_id: str, fence_token: str) -> str | None:
        """Resolve the worker id recorded on the lease for the event log."""
        lease = self._session.get(JobLease, job_id)
        if lease is not None and lease.fence_token == fence_token:
            return lease.worker_id
        return None

    @staticmethod
    def _fingerprint(manifest: dict[str, Any] | None) -> str:
        """Stable fingerprint of an input manifest (contract §8.1).

        Recorded on the ``created`` event so the reconciler can fail closed
        with ``INPUT_CHANGED`` if a Job's manifest is ever mutated after
        creation (manifests are immutable by contract; the fingerprint is the
        durable baseline).
        """
        import hashlib

        canonical = json.dumps(manifest or {}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _validate_job_attributes(
        self,
        *,
        workspace_id: str,
        job_type: str,
        owner_type: str,
        owner_id: str,
        resource_class: str,
        priority: int,
        max_attempts: int,
        state: str,
        actor: str,
    ) -> None:
        if not workspace_id:
            raise JobCreationError("workspace_id is required")
        if not job_type:
            raise JobCreationError("job_type is required")
        if not owner_type:
            raise JobCreationError("owner_type is required")
        if not owner_id:
            raise JobCreationError("owner_id is required")
        if resource_class not in RESOURCE_CLASSES:
            raise JobCreationError(
                f"resource_class must be one of {RESOURCE_CLASSES}, got {resource_class!r}"
            )
        if not 0 <= priority <= 100:
            raise JobCreationError("priority must be within [0, 100]")
        if max_attempts < 1:
            raise JobCreationError("max_attempts must be >= 1")
        if actor not in JOB_ACTORS:
            raise JobCreationError(f"actor must be one of {JOB_ACTORS}, got {actor!r}")
