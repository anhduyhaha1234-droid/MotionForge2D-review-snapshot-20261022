"""Durable Channel repository and service (S03-T01).

This module is the durable authority for source/production Channels.  It
implements the approved persistence domain contract (PERSISTENCE_DOMAIN_CONTRACT.md
§4 ``channel``) on the S01 ``channel`` table plus the S03-T01 migration
``1c9f2a4b7d8e`` (active-only, case-insensitive unique index on
``(workspace_id, role, lower(name))``).

Design rules enforced here:

- **No JSON dual-write.**  Legacy ``channels.json`` remains the *legacy*
  channel-workspace store and is never touched by this module.
- **No hard delete.**  There is no delete method; ``archive_channel`` is
  the only removal path.
- **Transactions are caller-bounded.**  The repository accepts a Session
  and never commits/rolls back on its own (contract §6).  The service
  opens exactly ONE session per request operation and commits once —
  including the workspace bootstrap, which is created in the same
  transaction as the first channel (no two-transaction create).
- **Atomic optimistic concurrency (CAS).**  ``update_channel`` and
  ``archive_channel`` execute a conditional UPDATE with
  ``WHERE id = :id AND workspace_id = :ws AND revision = :expected`` and
  inspect the affected row count: exactly one writer wins, every accepted
  business update bumps ``revision`` once, stale updates raise
  ``ChannelConflictError`` (HTTP 409), and the workspace predicate makes
  a channel id from another workspace behave as unknown (HTTP 404).
- **DTO/ORM boundary.**  The repository returns plain dataclass read
  records (``ChannelRecord``); the service maps them to Pydantic DTOs.
  No ORM instance ever crosses into the API layer.
- **Explicit-null clearing.**  PATCH distinguishes an omitted field from
  an explicit JSON ``null`` (Pydantic ``model_fields_set``); nullable
  metadata (``color``, ``target_language``, ``default_output_profile``,
  ``avatar_artifact_id``) can be cleared.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar, overload

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    CHANNEL_ROLES,
    CHANNEL_STATUSES,
    Artifact,
    Channel,
    Workspace,
)

__all__ = [
    "ACTIVE_STATUS",
    "ARCHIVED_STATUS",
    "ArtifactReferenceError",
    "CHANNEL_ROLES",
    "CHANNEL_STATUSES",
    "ChannelConflictError",
    "ChannelNotFoundError",
    "ChannelRecord",
    "ChannelRepository",
    "ChannelService",
    "DEFAULT_WORKSPACE_ID",
    "NameConflictError",
    "normalize_channel_name",
]

DEFAULT_WORKSPACE_ID = "default"
ACTIVE_STATUS = "active"
ARCHIVED_STATUS = "archived"

#: Sentinel distinguishing "field omitted" from "explicit null (clear)".
#: Repository update methods treat ``None`` as "no change"; the service
#: maps an explicit JSON null from the API to this sentinel so the column
#: is set to NULL in the CAS update.
UNSET = object()


def normalize_channel_name(name: str) -> str:
    """Normalize a channel display name (trim; keep display case).

    Uniqueness is enforced case-insensitively by the partial unique index
    on ``lower(name)`` (S03-T01 migration), so the stored name keeps its
    display form while conflicts are detected regardless of case (AC3).
    """
    return name.strip()


@dataclass(frozen=True)
class ChannelRecord:
    """Read model of a Channel row (no ORM instances escape the repository)."""

    id: str
    workspace_id: str
    legacy_id: str | None
    role: str
    name: str
    description: str
    color: str | None
    avatar_artifact_id: str | None
    target_language: str | None
    default_output_profile: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None
    archived_at: datetime | None
    revision: int


class ChannelNotFoundError(Exception):
    """No Channel row exists for the requested id (in the workspace)."""


class NameConflictError(Exception):
    """An active Channel with the same (workspace, role, normalized name)
    already exists (case-insensitive, AC3)."""


class ChannelConflictError(Exception):
    """Optimistic-concurrency conflict: the expected revision is stale (AC4)."""


class ArtifactReferenceError(Exception):
    """An avatar artifact reference is invalid (missing, cross-workspace or
    wrong kind) — mapped to an actionable HTTP 4xx (PM review round 2)."""


def _validate_avatar_reference(
    session: Session,
    workspace_id: str,
    avatar_artifact_id: str | None,
    *,
    channel_id: str | None = None,
) -> None:
    """Validate an avatar artifact reference before repository binding.

    Raises:
        ArtifactReferenceError: the artifact does not exist, belongs to a
            different workspace, or is not an ``image`` kind.  The message
            is stable and actionable for the API layer (HTTP 422/404).
    """
    if avatar_artifact_id is None:
        return
    artifact = session.get(Artifact, avatar_artifact_id)
    if artifact is None:
        raise ArtifactReferenceError(
            f"avatar_artifact_id {avatar_artifact_id!r} does not reference "
            "an existing artifact"
        )
    if artifact.workspace_id != workspace_id:
        raise ArtifactReferenceError(
            f"avatar_artifact_id {avatar_artifact_id!r} belongs to a "
            "different workspace"
        )
    if artifact.kind != "image":
        raise ArtifactReferenceError(
            f"avatar_artifact_id {avatar_artifact_id!r} is not an image "
            f"artifact (kind={artifact.kind!r})"
        )


def _channel_record(channel: Channel) -> ChannelRecord:
    return ChannelRecord(
        id=channel.id,
        workspace_id=channel.workspace_id,
        legacy_id=channel.legacy_id,
        role=channel.role,
        name=channel.name,
        description=channel.description or "",
        color=channel.color,
        avatar_artifact_id=channel.avatar_artifact_id,
        target_language=channel.target_language,
        default_output_profile=channel.default_output_profile,
        status=channel.status,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
        archived_at=channel.archived_at,
        revision=channel.revision,
    )


class ChannelRepository:
    """Transactional durable Channel store (SQLite).

    The repository never commits on its own: the caller owns the
    transaction (contract §6).  Writes are guarded database updates (CAS),
    not SELECT-then-mutate.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Creation ──────────────────────────────────────────────────────────

    def create_channel(
        self,
        *,
        workspace_id: str,
        role: str,
        name: str,
        description: str = "",
        color: str | None = None,
        avatar_artifact_id: str | None = None,
        target_language: str | None = None,
        default_output_profile: str | None = None,
        legacy_id: str | None = None,
    ) -> ChannelRecord:
        """Create one Channel row in the caller's transaction.

        Raises:
            NameConflictError: an **active** Channel already exists for
                ``(workspace_id, role, name)`` case-insensitively (the
                partial unique index is the concurrency backstop; the
                pre-check turns the failure mode into the stable conflict).
            ValueError: invalid role/status values or a missing workspace
                row (the service bootstraps the workspace in the same
                transaction).
        """
        if role not in CHANNEL_ROLES:
            raise ValueError(f"role must be one of {CHANNEL_ROLES}, got {role!r}")
        normalized = normalize_channel_name(name)
        if not normalized:
            raise ValueError("name must be a non-empty string")
        if len(normalized) > 200:
            raise ValueError("name must be at most 200 characters")

        blocker = self._find_active_by_name(workspace_id, role, normalized)
        if blocker is not None:
            raise NameConflictError(
                f"an active {role} channel named {normalized!r} already exists "
                f"in workspace {workspace_id!r} (channel {blocker.id})"
            )

        workspace_exists = self._session.scalar(
            select(Workspace.id).where(Workspace.id == workspace_id)
        )
        if workspace_exists is None:
            raise ValueError(
                f"workspace {workspace_id!r} does not exist; create the "
                "workspace row before creating channels"
            )

        _validate_avatar_reference(
            self._session, workspace_id, avatar_artifact_id
        )

        channel = Channel(
            workspace_id=workspace_id,
            legacy_id=legacy_id,
            role=role,
            name=normalized,
            description=description or "",
            color=color,
            avatar_artifact_id=avatar_artifact_id,
            target_language=target_language,
            default_output_profile=default_output_profile,
            status=ACTIVE_STATUS,
            revision=1,
        )
        self._session.add(channel)
        try:
            self._session.flush()
        except IntegrityError as exc:
            # Concurrency backstop: the partial unique index on
            # (workspace_id, role, lower(name)) WHERE status='active'.
            # ONLY a unique-violation on the channel name is a name
            # conflict; every other integrity error (e.g. the
            # avatar_artifact_id FK, the workspace FK) must propagate as
            # the real failure (PM review finding 9: actionable FK
            # validation).
            if "UNIQUE constraint failed" in str(exc.orig):
                raise NameConflictError(
                    f"an active {role} channel named {normalized!r} already exists "
                    f"in workspace {workspace_id!r}"
                ) from exc
            raise
        return _channel_record(channel)

    # ── Reads ─────────────────────────────────────────────────────────────

    def get_channel(self, channel_id: str, workspace_id: str) -> ChannelRecord:
        """Load a Channel by id within *workspace_id* (404 semantics).

        A channel id that exists but belongs to another workspace is
        treated as unknown: it must never be read across workspace
        boundaries (PM review finding 6).
        """
        channel = self._session.scalar(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.workspace_id == workspace_id,
            )
        )
        if channel is None:
            raise ChannelNotFoundError(
                f"Channel {channel_id!r} not found in workspace {workspace_id!r}"
            )
        return _channel_record(channel)

    def list_channels(
        self,
        workspace_id: str,
        *,
        role: str | None = None,
        active_only: bool = True,
    ) -> list[ChannelRecord]:
        """List Channels for a workspace (archived excluded by default)."""
        query = select(Channel).where(Channel.workspace_id == workspace_id)
        if role is not None:
            if role not in CHANNEL_ROLES:
                raise ValueError(f"role must be one of {CHANNEL_ROLES}, got {role!r}")
            query = query.where(Channel.role == role)
        if active_only:
            query = query.where(Channel.status == ACTIVE_STATUS)
        query = query.order_by(Channel.name, Channel.created_at)
        return [_channel_record(row) for row in self._session.scalars(query).all()]

    # ── Business update (atomic CAS, AC4) ─────────────────────────────────

    def update_channel(
        self,
        channel_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        avatar_artifact_id: str | None = None,
        target_language: str | None = None,
        default_output_profile: str | None = None,
    ) -> ChannelRecord:
        """Apply one business update via a conditional database UPDATE.

        The CAS predicate is ``id = :channel_id AND workspace_id =
        :workspace_id AND revision = :expected_revision``; the affected
        row count decides the outcome:
        - 0 rows + channel exists (wrong revision) → ChannelConflictError;
        - 0 rows + channel missing in workspace → ChannelNotFoundError;
        - 1 row → accepted; ``revision`` bumped exactly once by the SQL.

        Name conflicts are pre-checked (case-insensitive active-only) and
        backed by the partial unique index (racing writers lose with
        NameConflictError).  A channel from another workspace can never be
        matched by the CAS predicate.

        ``None`` values mean "no change" for every field (the API layer
        passes explicit ``null`` clears via a sentinel; see the route).
        """
        if name is not None:
            normalized = normalize_channel_name(name)
            if not normalized:
                raise ValueError("name must be a non-empty string")
            existing = self.get_channel(channel_id, workspace_id)
            if normalized != existing.name:
                blocker = self._find_active_by_name(
                    workspace_id, existing.role, normalized
                )
                if blocker is not None and blocker.id != channel_id:
                    raise NameConflictError(
                        f"an active {existing.role} channel named "
                        f"{normalized!r} already exists in workspace "
                        f"{workspace_id!r} (channel {blocker.id})"
                    )
        else:
            normalized = None

        # Validate avatar reference BEFORE the CAS binds values (round 2).
        if avatar_artifact_id not in (None, UNSET):
            _validate_avatar_reference(
                self._session,
                workspace_id,
                str(avatar_artifact_id),
            )
        elif avatar_artifact_id is UNSET and channel_id:
            existing = self.get_channel(channel_id, workspace_id)
            if existing.avatar_artifact_id is not None:
                # clearing an existing reference is a no-op FK-wise; the
                # artifact row may be anything (it is only dereferenced on
                # set, not on clear).
                pass

        values: dict[str, Any] = {}
        if normalized is not None:
            values["name"] = normalized
        if description is not None:
            values["description"] = description
        if color is not None:
            values["color"] = color
        if avatar_artifact_id is not None:
            values["avatar_artifact_id"] = avatar_artifact_id
        if target_language is not None:
            values["target_language"] = target_language
        if default_output_profile is not None:
            values["default_output_profile"] = default_output_profile
        values["revision"] = Channel.revision + 1
        values["updated_at"] = datetime.now(UTC)

        # Explicit-null clears arrive as the UNSET sentinel (the API maps
        # JSON null → UNSET, omitted → None).  Set those columns to NULL.
        for field, sentinel in (
            ("color", color),
            ("avatar_artifact_id", avatar_artifact_id),
            ("target_language", target_language),
            ("default_output_profile", default_output_profile),
        ):
            if sentinel is UNSET:
                values[field] = None

        try:
            result = self._session.execute(
                update(Channel)
                .where(
                    Channel.id == channel_id,
                    Channel.workspace_id == workspace_id,
                    Channel.revision == expected_revision,
                )
                .values(**values)
            )
        except IntegrityError as exc:
            # The active-name partial unique index
            # (uq_channel_active_workspace_role_name) may fire during a
            # concurrent two-channel rename-to-one-free-name race (PM
            # review round 3 finding 2).  ONLY a UNIQUE violation on this
            # index is a name conflict; any other integrity error (e.g.
            # avatar FK) must propagate as the real failure.
            if "UNIQUE constraint failed" in str(exc.orig):
                raise NameConflictError(
                    f"an active channel named {normalized or name!r} already "
                    f"exists in workspace {workspace_id!r}"
                ) from exc
            raise
        if result.rowcount == 0:  # type: ignore[attr-defined]
            # Distinguish stale revision from cross-workspace/unknown id.
            probe_row = self._session.execute(
                select(Channel.revision, Channel.workspace_id).where(
                    Channel.id == channel_id
                )
            ).first()
            if probe_row is None or probe_row[1] != workspace_id:
                raise ChannelNotFoundError(
                    f"Channel {channel_id!r} not found in workspace {workspace_id!r}"
                )
            raise ChannelConflictError(
                f"revision mismatch for Channel {channel_id}: expected "
                f"{expected_revision}, current {probe_row[0]}"
            )
        self._session.flush()
        return self.get_channel(channel_id, workspace_id)

    # ── Archive (AC5; atomic CAS, idempotent) ─────────────────────────────

    def archive_channel(
        self,
        channel_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
    ) -> ChannelRecord:
        """Archive a Channel with an atomic CAS.

        - Active row + matching revision → archived (``archived_at`` set,
          ``revision`` bumped once).
        - Already-archived row → idempotent no-op returning the current
          row WITHOUT another bump (a repeat against an archived row must
          not fail and must not bump).
        - Active row + stale revision → ChannelConflictError (409).
        - Concurrent winner: the loser's zero-row CAS re-reads with a
          FRESH database SELECT (not ``session.get``, which would return
          the caller's identity-mapped stale object) and returns the
          now-archived row idempotently (200, no bump) — PM review
          round 3 finding 1.
        - Missing / other-workspace id → ChannelNotFoundError (404).

        There is deliberately **no** hard-delete method.
        """
        current = self._session.scalar(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.workspace_id == workspace_id,
            )
        )
        if current is None:
            raise ChannelNotFoundError(
                f"Channel {channel_id!r} not found in workspace {workspace_id!r}"
            )
        if current.status == ARCHIVED_STATUS:
            return _channel_record(current)

        result = self._session.execute(
            update(Channel)
            .where(
                Channel.id == channel_id,
                Channel.workspace_id == workspace_id,
                Channel.status == ACTIVE_STATUS,
                Channel.revision == expected_revision,
            )
            .values(
                status=ARCHIVED_STATUS,
                archived_at=datetime.now(UTC),
                revision=Channel.revision + 1,
                updated_at=datetime.now(UTC),
            )
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            # Concurrent-archive race (PM review round 2 finding 4 / round 3
            # finding 1): a second caller may have read active, lost the CAS
            # to the first archiver, and now sees zero rows.  Force a FRESH
            # database read (explicit SELECT, bypassing the identity map —
            # session.get would return the caller's stale in-session object)
            # within this transaction: if the row is now archived, return
            # the current archived row idempotently (no bump, 200);
            # otherwise report the stale active revision (409).
            fresh = self._session.execute(
                select(Channel).where(
                    Channel.id == channel_id,
                    Channel.workspace_id == workspace_id,
                ).execution_options(populate_existing=True)
            ).scalar_one_or_none()
            if fresh is not None and fresh.status == ARCHIVED_STATUS:
                return _channel_record(fresh)
            raise ChannelConflictError(
                f"revision mismatch for Channel {channel_id}: expected "
                f"{expected_revision} while archiving"
            )
        self._session.flush()
        return self.get_channel(channel_id, workspace_id)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _find_active_by_name(
        self, workspace_id: str, role: str, name: str
    ) -> Channel | None:
        """Case-insensitive active-name lookup (lower(name))."""
        return self._session.scalar(
            select(Channel).where(
                Channel.workspace_id == workspace_id,
                Channel.role == role,
                Channel.status == ACTIVE_STATUS,
                func.lower(Channel.name) == name.lower(),
            )
        )


class ChannelService:
    """Request-bounded facade: exactly ONE transaction per operation.

    The service owns the session lifecycle (open → operate → commit; roll
    back on error) so every API request is transaction-bounded, including
    the workspace bootstrap: the workspace row is created in the SAME
    transaction as the first channel (atomic insert pattern, no
    two-transaction create, PM review finding 7).
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
            repo = ChannelRepository(session)
            try:
                result = fn(repo, *args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def create(
        self,
        *,
        workspace_id: str,
        role: str,
        name: str,
        description: str = "",
        color: str | None = None,
        avatar_artifact_id: str | None = None,
        target_language: str | None = None,
        default_output_profile: str | None = None,
    ) -> ChannelRecord:
        """Create the workspace row and the channel in ONE transaction.

        The workspace bootstrap is race-safe: an ``INSERT OR IGNORE``-style
        insert (SQLite ON CONFLICT DO NOTHING) means a concurrent first-use
        loses the workspace insert without failing the channel creation —
        the transaction still commits the channel with the workspace row
        the winner inserted (PM review finding 7).
        """
        with self._session_factory() as session:
            repo = ChannelRepository(session)
            try:
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                session.execute(
                    sqlite_insert(Workspace)
                    .values(id=workspace_id, name=workspace_id)
                    .on_conflict_do_nothing(index_elements=[Workspace.id])
                )
                record = repo.create_channel(
                    workspace_id=workspace_id,
                    role=role,
                    name=name,
                    description=description,
                    color=color,
                    avatar_artifact_id=avatar_artifact_id,
                    target_language=target_language,
                    default_output_profile=default_output_profile,
                )
                session.commit()
                return record
            except Exception:
                session.rollback()
                raise

    def get(self, channel_id: str, workspace_id: str) -> ChannelRecord:
        return self._run(ChannelRepository.get_channel, channel_id, workspace_id)

    def list(
        self,
        workspace_id: str,
        *,
        role: str | None = None,
        active_only: bool = True,
    ) -> list[ChannelRecord]:
        return self._run(
            ChannelRepository.list_channels,
            workspace_id,
            role=role,
            active_only=active_only,
        )

    def update(
        self,
        channel_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
        name: str | None = None,
        description: str | None = None,
        color: Any = None,
        avatar_artifact_id: Any = None,
        target_language: Any = None,
        default_output_profile: Any = None,
    ) -> ChannelRecord:
        return self._run(
            ChannelRepository.update_channel,
            channel_id,
            workspace_id,
            expected_revision=expected_revision,
            name=name,
            description=description,
            color=color,
            avatar_artifact_id=avatar_artifact_id,
            target_language=target_language,
            default_output_profile=default_output_profile,
        )

    def archive(
        self, channel_id: str, workspace_id: str, *, expected_revision: int
    ) -> ChannelRecord:
        return self._run(
            ChannelRepository.archive_channel,
            channel_id,
            workspace_id,
            expected_revision=expected_revision,
        )
