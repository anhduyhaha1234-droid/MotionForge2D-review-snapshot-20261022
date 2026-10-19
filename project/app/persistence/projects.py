"""Durable Project repository and service (S03-T02).

This module is the durable authority for Projects.  It implements the
approved persistence domain contract (PERSISTENCE_DOMAIN_CONTRACT.md §4
``project``) on the S01 ``project`` table.  No schema migration was
needed: the existing table already carries CHECK constraints for name
length (1-200), the exact status set, positive revision, and RESTRICT
FKs to ``channel``/``workspace`` (verified against the S03-T01 head).

Design rules enforced here (mirroring ``app/persistence/channels.py``):

- **No JSON dual-write.**  Durable project operations never create a
  project directory or ``project.json`` and never touch the legacy
  filesystem project store (AC1).
- **No hard delete.**  There is no delete method; ``archive_project`` is
  the only removal path (AC1/AC5).
- **Transactions are caller-bounded.**  The repository accepts a Session
  and never commits/rolls back on its own (contract §6).  The service
  opens exactly ONE session per request operation and commits once —
  including the workspace bootstrap (same transaction as the first
  project row).
- **Atomic optimistic concurrency (CAS).**  ``update_project`` and
  ``archive_project`` execute a conditional UPDATE with
  ``WHERE id = :id AND workspace_id = :ws AND revision = :expected`` and
  inspect the affected row count: exactly one writer wins, every accepted
  business update bumps ``revision`` once, stale updates raise
  ``ProjectConflictError`` (HTTP 409), and the workspace predicate makes
  a project id from another workspace behave as unknown (HTTP 404).
- **Channel-aware validation (AC3).**  Newly assigned channel references
  are validated atomically inside the caller's transaction: the channel
  must exist, belong to the same workspace, have the correct role
  (``source`` → source_channel_id, ``production`` → production_channel_id)
  and be ACTIVE at assignment time.  References that already exist
  survive a later channel archive (a channel archived after assignment
  keeps the project reference valid — no cascade, contract §5).  All
  validation happens BEFORE the CAS binds values; no raw IntegrityError
  escapes the API.
- **DTO/ORM boundary.**  The repository returns plain dataclass read
  records (``ProjectRecord``); the service maps them to Pydantic DTOs.
  No ORM instance ever crosses into the API layer (AC2/AC6).
- **Explicit-null clearing.**  PATCH distinguishes an omitted field from
  an explicit JSON ``null`` (Pydantic ``model_fields_set``); nullable
  metadata (``description``, channel references, ``default_output_profile``,
  ``resume_step``) can be cleared.  ``name``/``status`` are never null.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar, cast, overload

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.persistence.models import (
    PROJECT_STATUSES,
    Channel,
    Project,
    Workspace,
)

__all__ = [
    "ACTIVE_PROJECT_STATUS",
    "ARCHIVED_PROJECT_STATUS",
    "DEFAULT_WORKSPACE_ID",
    "ChannelReferenceError",
    "PROJECT_STATUSES",
    "ProjectConflictError",
    "ProjectNotFoundError",
    "ProjectRecord",
    "ProjectRepository",
    "ProjectService",
    "normalize_project_name",
]

DEFAULT_WORKSPACE_ID = "default"
ACTIVE_PROJECT_STATUS = "active"
ARCHIVED_PROJECT_STATUS = "archived"

#: Sentinel distinguishing "field omitted" from "explicit null (clear)".
#: Repository update methods treat ``None`` as "no change"; the service
#: maps an explicit JSON null from the API to this sentinel so the column
#: is set to NULL in the CAS update.
UNSET = object()


def normalize_project_name(name: str) -> str:
    """Normalize a project display name (trim; keep display case)."""
    return name.strip()


@dataclass(frozen=True)
class ProjectRecord:
    """Read model of a Project row (no ORM instances escape the repository)."""

    id: str
    workspace_id: str
    legacy_id: str | None
    name: str
    description: str
    status: str
    source_channel_id: str | None
    production_channel_id: str | None
    default_output_profile: str | None
    resume_step: str | None
    created_at: datetime | None
    updated_at: datetime | None
    archived_at: datetime | None
    revision: int


class ProjectNotFoundError(Exception):
    """No Project row exists for the requested id (in the workspace)."""


class ProjectConflictError(Exception):
    """Optimistic-concurrency conflict: the expected revision is stale (AC4)."""


class ChannelReferenceError(Exception):
    """A channel reference is invalid: missing, cross-workspace, wrong role
    or not active at assignment time (AC3) — mapped to an actionable
    HTTP 4xx."""


def _project_record(project: Project) -> ProjectRecord:
    return ProjectRecord(
        id=project.id,
        workspace_id=project.workspace_id,
        legacy_id=project.legacy_id,
        name=project.name,
        description=project.description or "",
        status=project.status,
        source_channel_id=project.source_channel_id,
        production_channel_id=project.production_channel_id,
        default_output_profile=project.default_output_profile,
        resume_step=project.resume_step,
        created_at=project.created_at,
        updated_at=project.updated_at,
        archived_at=project.archived_at,
        revision=project.revision,
    )


def _validate_channel_reference(
    session: Session,
    workspace_id: str,
    channel_id: str | None,
    *,
    role: str,
) -> None:
    """Validate a NEW channel assignment inside the caller's transaction.

    Raises:
        ChannelReferenceError: the channel does not exist, belongs to a
            different workspace, has the wrong role, or is not active.
            Existing references are NOT revalidated (a channel archived
            after assignment keeps the project reference — AC3/contract §5).
    """
    if channel_id is None:
        return
    channel = session.get(Channel, channel_id)
    if channel is None:
        raise ChannelReferenceError(
            f"{role}_channel_id {channel_id!r} does not reference an "
            "existing channel"
        )
    if channel.workspace_id != workspace_id:
        raise ChannelReferenceError(
            f"{role}_channel_id {channel_id!r} belongs to a different workspace"
        )
    if channel.role != role:
        raise ChannelReferenceError(
            f"{role}_channel_id {channel_id!r} is not a {role} channel "
            f"(role={channel.role!r})"
        )
    if channel.status != "active":
        raise ChannelReferenceError(
            f"{role}_channel_id {channel_id!r} is not an active channel "
            f"(status={channel.status!r})"
        )


class ProjectRepository:
    """Transactional durable Project store (SQLite).

    The repository never commits on its own: the caller owns the
    transaction (contract §6).  Writes are guarded database updates (CAS),
    not SELECT-then-mutate.
    """

    def __init__(
        self,
        session: Session,
        *,
        archive_after_read: Callable[[], None] | None = None,
    ) -> None:
        self._session = session
        self._archive_after_read = archive_after_read

    # ── Creation ──────────────────────────────────────────────────────────

    def create_project(
        self,
        *,
        workspace_id: str,
        name: str,
        description: str = "",
        source_channel_id: str | None = None,
        production_channel_id: str | None = None,
        default_output_profile: str | None = None,
        resume_step: str | None = None,
        legacy_id: str | None = None,
    ) -> ProjectRecord:
        """Create one Project row in the caller's transaction.

        Channel references are validated BEFORE binding (AC3): same
        workspace, correct role, active.  No filesystem directory or
        ``project.json`` is ever created (AC1).

        Raises:
            ChannelReferenceError: a channel reference is invalid.
            ValueError: invalid name/status values or a missing workspace
                row (the service bootstraps the workspace in the same
                transaction).
        """
        normalized = normalize_project_name(name)
        if not normalized:
            raise ValueError("name must be a non-empty string")
        if len(normalized) > 200:
            raise ValueError("name must be at most 200 characters")

        workspace_exists = self._session.scalar(
            select(Workspace.id).where(Workspace.id == workspace_id)
        )
        if workspace_exists is None:
            raise ValueError(
                f"workspace {workspace_id!r} does not exist; create the "
                "workspace row before creating projects"
            )

        _validate_channel_reference(
            self._session, workspace_id, source_channel_id, role="source"
        )
        _validate_channel_reference(
            self._session, workspace_id, production_channel_id, role="production"
        )

        project = Project(
            workspace_id=workspace_id,
            legacy_id=legacy_id,
            name=normalized,
            description=description or "",
            status=ACTIVE_PROJECT_STATUS,
            source_channel_id=source_channel_id,
            production_channel_id=production_channel_id,
            default_output_profile=default_output_profile,
            resume_step=resume_step,
            revision=1,
        )
        self._session.add(project)
        self._session.flush()
        return _project_record(project)

    # ── Reads ─────────────────────────────────────────────────────────────

    def get_project(self, project_id: str, workspace_id: str) -> ProjectRecord:
        """Load a Project by id within *workspace_id* (404 semantics).

        A project id that exists but belongs to another workspace is
        treated as unknown: it must never be read across workspace
        boundaries (AC6).
        """
        project = self._session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if project is None:
            raise ProjectNotFoundError(
                f"Project {project_id!r} not found in workspace {workspace_id!r}"
            )
        return _project_record(project)

    def list_projects(
        self,
        workspace_id: str,
        *,
        status: str | None = None,
        active_only: bool = True,
    ) -> list[ProjectRecord]:
        """List Projects for a workspace (archived excluded by default)."""
        query = select(Project).where(Project.workspace_id == workspace_id)
        if status is not None:
            if status not in PROJECT_STATUSES:
                raise ValueError(
                    f"status must be one of {PROJECT_STATUSES}, got {status!r}"
                )
            query = query.where(Project.status == status)
        elif active_only:
            query = query.where(Project.status != ARCHIVED_PROJECT_STATUS)
        query = query.order_by(Project.created_at, Project.name)
        return [_project_record(row) for row in self._session.scalars(query).all()]

    # ── Business update (atomic CAS, AC4) ─────────────────────────────────

    def update_project(
        self,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        source_channel_id: Any = None,
        production_channel_id: Any = None,
        default_output_profile: Any = None,
        resume_step: Any = None,
    ) -> ProjectRecord:
        """Apply one business update via a conditional database UPDATE.

        The CAS predicate is ``id = :project_id AND workspace_id =
        :workspace_id AND revision = :expected_revision``; the affected
        row count decides the outcome:
        - 0 rows + project exists (wrong revision) → ProjectConflictError;
        - 0 rows + project missing in workspace → ProjectNotFoundError;
        - 1 row → accepted; ``revision`` bumped exactly once by the SQL.

        NEW channel references are validated BEFORE the CAS binds values
        (AC3); an existing reference is only revalidated when the PATCH
        explicitly changes it.  ``None`` values mean "no change" for every
        field (the API layer passes explicit ``null`` clears via a
        sentinel; see the route).
        """
        if name is not None:
            normalized = normalize_project_name(name)
            if not normalized:
                raise ValueError("name must be a non-empty string")
        else:
            normalized = None

        if status == ARCHIVED_PROJECT_STATUS:
            raise ValueError(
                "status 'archived' is only accepted by the archive endpoint"
            )
        if status is not None and status not in PROJECT_STATUSES:
            raise ValueError(
                f"status must be one of {PROJECT_STATUSES}, got {status!r}"
            )

        # Channel references: validate NEW assignments; the sentinel UNSET
        # means "explicit null" (clear), None means "omitted" (unchanged).
        if source_channel_id not in (None, UNSET):
            _validate_channel_reference(
                self._session, workspace_id, str(source_channel_id), role="source"
            )
        if production_channel_id not in (None, UNSET):
            _validate_channel_reference(
                self._session,
                workspace_id,
                str(production_channel_id),
                role="production",
            )

        values: dict[str, Any] = {}
        if normalized is not None:
            values["name"] = normalized
        if description is not None:
            values["description"] = description
        if status is not None:
            values["status"] = status
        if source_channel_id not in (None,):
            values["source_channel_id"] = (
                None if source_channel_id is UNSET else source_channel_id
            )
        if production_channel_id not in (None,):
            values["production_channel_id"] = (
                None if production_channel_id is UNSET else production_channel_id
            )
        if default_output_profile not in (None,):
            values["default_output_profile"] = (
                None if default_output_profile is UNSET else default_output_profile
            )
        if resume_step not in (None,):
            values["resume_step"] = (
                None if resume_step is UNSET else resume_step
            )
        values["revision"] = Project.revision + 1
        values["updated_at"] = datetime.now(UTC)

        result = self._session.execute(
            update(Project)
            .where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
                Project.revision == expected_revision,
                Project.status != ARCHIVED_PROJECT_STATUS,
            )
            .values(**values)
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            # Distinguish stale revision from cross-workspace/unknown id.
            probe_row = self._session.execute(
                select(Project.revision, Project.workspace_id).where(
                    Project.id == project_id
                )
            ).first()
            if probe_row is None or probe_row[1] != workspace_id:
                raise ProjectNotFoundError(
                    f"Project {project_id!r} not found in workspace {workspace_id!r}"
                )
            current_status = self._session.scalar(
                select(Project.status).where(Project.id == project_id)
            )
            if current_status == ARCHIVED_PROJECT_STATUS:
                raise ProjectConflictError(
                    f"Project {project_id} is archived and immutable"
                )
            raise ProjectConflictError(
                f"revision mismatch for Project {project_id}: expected "
                f"{expected_revision}, current {probe_row[0]}"
            )
        self._session.flush()
        return self.get_project(project_id, workspace_id)

    # ── Archive (AC5; atomic CAS, idempotent) ─────────────────────────────

    def archive_project(
        self,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
    ) -> ProjectRecord:
        """Archive a Project with an atomic CAS.

        - Active row + matching revision → archived (``archived_at`` set,
          ``revision`` bumped once).
        - Already-archived row → idempotent no-op returning the current
          row WITHOUT another bump (a repeat against an archived row must
          not fail and must not bump).
        - Active row + stale revision → ProjectConflictError (409).
        - Concurrent winner: the loser's zero-row CAS re-reads with a
          FRESH database SELECT (bypassing the identity map — ``session.get``
          would return the caller's stale in-session object) and returns
          the now-archived row idempotently (200, no bump).
        - Missing / other-workspace id → ProjectNotFoundError (404).

        Archive preserves timestamps, channel references and future child
        relationships (no cascade, no hard delete — contract §5).  There
        is deliberately **no** hard-delete method.
        """
        current = self._session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if current is None:
            raise ProjectNotFoundError(
                f"Project {project_id!r} not found in workspace {workspace_id!r}"
            )
        if self._archive_after_read is not None:
            self._archive_after_read()
        if current.status == ARCHIVED_PROJECT_STATUS:
            return _project_record(current)

        result = self._session.execute(
            update(Project)
            .where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
                Project.status != ARCHIVED_PROJECT_STATUS,
                Project.revision == expected_revision,
            )
            .values(
                status=ARCHIVED_PROJECT_STATUS,
                archived_at=datetime.now(UTC),
                revision=Project.revision + 1,
                updated_at=datetime.now(UTC),
            )
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            # Concurrent-archive race: a second caller may have read
            # active, lost the CAS to the first archiver, and now sees
            # zero rows.  Force a FRESH database read (explicit SELECT,
            # bypassing the identity map) within this transaction: if the
            # row is now archived, return it idempotently (no bump, 200);
            # otherwise report the stale active revision (409).
            fresh = self._session.execute(
                select(Project).where(
                    Project.id == project_id,
                    Project.workspace_id == workspace_id,
                ).execution_options(populate_existing=True)
            ).scalar_one_or_none()
            if fresh is not None and fresh.status == ARCHIVED_PROJECT_STATUS:
                return _project_record(fresh)
            raise ProjectConflictError(
                f"revision mismatch for Project {project_id}: expected "
                f"{expected_revision} while archiving"
            )
        self._session.flush()
        return self.get_project(project_id, workspace_id)


class ProjectService:
    """Request-bounded facade: exactly ONE transaction per operation.

    The service owns the session lifecycle (open → operate → commit; roll
    back on error) so every API request is transaction-bounded, including
    the workspace bootstrap: the workspace row is created in the SAME
    transaction as the first project (atomic insert pattern).
    """

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    _T = TypeVar("_T")

    @overload
    def _run(self, fn: Callable[..., _T], *args: Any, **kwargs: Any) -> _T: ...

    @overload
    def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...

    def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        with self._session_factory() as session:
            repo = ProjectRepository(session)
            try:
                result = fn(repo, *args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def _run_write(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Run a SQLite write under a reserved lock from its first read.

        ``BEGIN IMMEDIATE`` serializes competing writers before channel
        validation.  Therefore a channel archive cannot commit between the
        active-channel check and the Project INSERT/UPDATE that binds it.
        The configured bounded busy timeout still applies while waiting.
        """
        with self._session_factory() as session:
            try:
                session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                result = fn(ProjectRepository(session), *args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def create(
        self,
        *,
        workspace_id: str,
        name: str,
        description: str = "",
        source_channel_id: str | None = None,
        production_channel_id: str | None = None,
        default_output_profile: str | None = None,
        resume_step: str | None = None,
    ) -> ProjectRecord:
        """Create the workspace row and the project in ONE transaction.

        The workspace bootstrap is race-safe: an ``ON CONFLICT DO
        NOTHING`` insert means a concurrent first-use loses the workspace
        insert without failing the project creation — the transaction
        still commits the project with the workspace row the winner
        inserted.
        """
        with self._session_factory() as session:
            repo = ProjectRepository(session)
            try:
                session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                session.execute(
                    sqlite_insert(Workspace)
                    .values(id=workspace_id, name=workspace_id)
                    .on_conflict_do_nothing(index_elements=[Workspace.id])
                )
                record = repo.create_project(
                    workspace_id=workspace_id,
                    name=name,
                    description=description,
                    source_channel_id=source_channel_id,
                    production_channel_id=production_channel_id,
                    default_output_profile=default_output_profile,
                    resume_step=resume_step,
                )
                session.commit()
                return record
            except Exception:
                session.rollback()
                raise

    def get(self, project_id: str, workspace_id: str) -> ProjectRecord:
        return self._run(ProjectRepository.get_project, project_id, workspace_id)

    def list(
        self,
        workspace_id: str,
        *,
        status: str | None = None,
        active_only: bool = True,
    ) -> list[ProjectRecord]:
        return self._run(
            ProjectRepository.list_projects,
            workspace_id,
            status=status,
            active_only=active_only,
        )

    def update(
        self,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        source_channel_id: Any = None,
        production_channel_id: Any = None,
        default_output_profile: Any = None,
        resume_step: Any = None,
    ) -> ProjectRecord:
        # ``_run`` is generic over the repository callable; the Any-typed
        # channel-ref kwargs defeat inference, so cast the result.
        return cast(
            "ProjectRecord",
            self._run_write(
                ProjectRepository.update_project,
                project_id,
                workspace_id,
                expected_revision=expected_revision,
                name=name,
                description=description,
                status=status,
                source_channel_id=source_channel_id,
                production_channel_id=production_channel_id,
                default_output_profile=default_output_profile,
                resume_step=resume_step,
            ),
        )

    def archive(
        self, project_id: str, workspace_id: str, *, expected_revision: int
    ) -> ProjectRecord:
        return cast(
            "ProjectRecord",
            self._run_write(
                ProjectRepository.archive_project,
                project_id,
                workspace_id,
                expected_revision=expected_revision,
            ),
        )
