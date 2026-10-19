"""Durable Video Item repository and service (S03-T03).

This module is the durable authority for Video Items.  It implements the
approved persistence domain contract (PERSISTENCE_DOMAIN_CONTRACT.md §4
``video_item``) on the S01 ``video_item`` table.  **No schema migration
was needed**: the existing table already carries CHECK constraints for
title length (1-240), ``position >= 0`` with ``UNIQUE(project_id,
position)``, the exact 13-state status set, positive revision, and
RESTRICT FKs to ``project``/``channel``/``artifact`` (verified against
the S03-T02 head ``1c9f2a4b7d8e``).

Design rules enforced here (mirroring ``app/persistence/projects.py``):

- **No JSON dual-write / no filesystem writes.**  Durable Video Item
  operations never touch legacy filesystem workflows, media bytes or
  ``channels.json`` (AC1/AC9).
- **No hard delete.**  There is no delete method; ``archive_video`` is
  the only removal path (AC5).
- **Transactions are caller-bounded.**  The repository accepts a Session
  and never commits/rolls back on its own (contract §6).  The service
  opens exactly ONE session per request operation and commits once.
- **Atomic optimistic concurrency (CAS).**  ``update_video`` and
  ``archive_video`` execute a conditional UPDATE with ``WHERE id = :id
  AND project_id = :project_id AND revision = :expected`` and inspect
  the affected row count; stale updates raise ``VideoConflictError``
  (HTTP 409), missing/cross-workspace ids raise ``VideoNotFoundError``
  (HTTP 404).
- **Append-at-end create.**  ``create_video`` computes the next position
  as ``MAX(position) + 1`` among active rows of the project.  A
  concurrent create cannot leak a raw ``IntegrityError``: the SQLite
  writer reservation (``BEGIN IMMEDIATE`` in the service) serializes
  appends, and the ``UNIQUE(project_id, position)`` index remains the
  concurrency backstop (serialize/retry deterministically — see
  ``AppendRetryError``).
- **One-transaction reorder with two-phase positions.**  ``reorder``
  validates the complete active id set exactly-once, bumps the Project
  revision once (CAS on ``project_revision``), then rewrites positions
  using collision-safe two-phase offsets (``MAX(position)+N+1`` first,
  then compact to 0..N-1) so the ``UNIQUE(project_id, position)`` index
  never fires mid-transaction.  Only Video Items whose position changes
  are bumped.
- **Channel validation at the atomic boundary (S03-T02 policy).**  A NEW
  ``source_channel_id`` assignment is validated inside the caller's
  transaction — the channel must exist, belong to the same workspace,
  have role ``source`` and be ACTIVE at assignment time.  Existing
  references survive later channel archive (no cascade, contract §5).
  The service wraps writes in ``BEGIN IMMEDIATE`` so a competing channel
  archive cannot commit between validation and assignment.
- **Archived-project guard.**  Creating Video Items, reordering, and
  active workflow mutation are rejected on archived Projects (domain
  contract; a restore policy is future work).
- **DTO/ORM boundary.**  The repository returns plain dataclass read
  records (``VideoItemRecord``); the service maps them to Pydantic
  DTOs.  No ORM instance ever crosses into the API layer.
- **Explicit-null clearing.**  PATCH distinguishes an omitted field from
  an explicit JSON ``null`` (Pydantic ``model_fields_set``); nullable
  metadata (``source_channel_id``, ``resume_step``) can be cleared.
  Probe metadata (``duration_ms``, ``width``, ``height``, ``fps_num``,
  ``fps_den``, ``source_artifact_id``) is read-only in this task (S05
  owns import and media probing).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar, cast, overload

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    ARCHIVED_VIDEO_STATUS,
    VIDEO_PIPELINE_STATES,
    Channel,
    Project,
    VideoItem,
)

__all__ = [
    "ARCHIVED_VIDEO_STATUS",
    "AppendRetryError",
    "ChannelReferenceError",
    "ReorderValidationError",
    "VIDEO_PIPELINE_STATES",
    "VideoConflictError",
    "VideoItemRecord",
    "VideoItemRepository",
    "VideoItemService",
    "VideoNotFoundError",
    "normalize_video_title",
]

#: Sentinel distinguishing "field omitted" from "explicit null (clear)".
UNSET = object()

#: Stable pipeline state a new Video Item starts in (contract §4).
DEFAULT_VIDEO_STATUS = "imported"


def normalize_video_title(title: str) -> str:
    """Normalize a Video Item title (trim; keep display case)."""
    return title.strip()


@dataclass(frozen=True)
class VideoItemRecord:
    """Read model of a Video Item row (no ORM instances escape the repo)."""

    id: str
    project_id: str
    workspace_id: str
    legacy_id: str | None
    title: str
    position: int
    status: str
    source_artifact_id: str | None
    source_channel_id: str | None
    duration_ms: int | None
    width: int | None
    height: int | None
    fps_num: int | None
    fps_den: int | None
    resume_step: str | None
    resume_payload_json: str | None
    created_at: datetime | None
    updated_at: datetime | None
    archived_at: datetime | None
    revision: int


class VideoNotFoundError(Exception):
    """No Video Item row exists for the requested id (in the project)."""


class VideoConflictError(Exception):
    """Optimistic-concurrency conflict: the expected revision is stale (AC4)."""


class ChannelReferenceError(Exception):
    """A channel reference is invalid: missing, cross-workspace, wrong role
    or not active at assignment time — mapped to an actionable HTTP 4xx."""


class ReorderValidationError(Exception):
    """A reorder request violates the complete-set/exactly-once contract
    (missing/extra/duplicate/cross-project ids) — rejected before any
    write (AC4)."""


class AppendRetryError(Exception):
    """Internal signal: a concurrent create append lost the position race
    and must retry deterministically (never leaks raw IntegrityError)."""


def _video_record(video: VideoItem) -> VideoItemRecord:
    return VideoItemRecord(
        id=video.id,
        project_id=video.project_id,
        workspace_id=video.project.workspace_id,
        legacy_id=video.legacy_id,
        title=video.title,
        position=video.position,
        status=video.status,
        source_artifact_id=video.source_artifact_id,
        source_channel_id=video.source_channel_id,
        duration_ms=video.duration_ms,
        width=video.width,
        height=video.height,
        fps_num=video.fps_num,
        fps_den=video.fps_den,
        resume_step=video.resume_step,
        resume_payload_json=video.resume_payload_json,
        created_at=video.created_at,
        updated_at=video.updated_at,
        archived_at=video.archived_at,
        revision=video.revision,
    )


def _validate_source_channel(
    session: Session,
    workspace_id: str,
    channel_id: str | None,
) -> None:
    """Validate a NEW source-channel assignment inside the caller's txn.

    Raises:
        ChannelReferenceError: the channel does not exist, belongs to a
            different workspace, has the wrong role, or is not active.
            Existing references are NOT revalidated (a channel archived
            after assignment keeps the Video Item reference — contract
            §5).
    """
    if channel_id is None:
        return
    channel = session.get(Channel, channel_id)
    if channel is None:
        raise ChannelReferenceError(
            f"source_channel_id {channel_id!r} does not reference an "
            "existing channel"
        )
    if channel.workspace_id != workspace_id:
        raise ChannelReferenceError(
            f"source_channel_id {channel_id!r} belongs to a different workspace"
        )
    if channel.role != "source":
        raise ChannelReferenceError(
            f"source_channel_id {channel_id!r} is not a source channel "
            f"(role={channel.role!r})"
        )
    if channel.status != "active":
        raise ChannelReferenceError(
            f"source_channel_id {channel_id!r} is not an active channel "
            f"(status={channel.status!r})"
        )


class VideoItemRepository:
    """Transactional durable Video Item store (SQLite).

    The repository never commits on its own: the caller owns the
    transaction (contract §6).  Writes are guarded database updates
    (CAS), not SELECT-then-mutate.  Every method takes the owning
    ``project_id`` (and the workspace predicate via the project join)
    so a Video Item from another project/workspace behaves as unknown.
    """

    def __init__(
        self,
        session: Session,
        *,
        archive_after_read: Callable[[], None] | None = None,
        after_read: Callable[[], None] | None = None,
    ) -> None:
        self._session = session
        self._archive_after_read = archive_after_read
        #: Deterministic pause point invoked by multi-row operations
        #: (reorder) AFTER reading the current state and BEFORE the CAS
        #: write.  Used by concurrency tests to force an interleaving.
        self._after_read = after_read

    # ── Helpers ──────────────────────────────────────────────────────────

    def _load_project(self, project_id: str, workspace_id: str) -> Project:
        """Load the owning Project within the workspace (404 semantics)."""
        project = self._session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if project is None:
            raise VideoNotFoundError(
                f"Project {project_id!r} not found in workspace {workspace_id!r}"
            )
        return project

    def _load_video(
        self, video_id: str, project_id: str, workspace_id: str
    ) -> VideoItem:
        """Load a Video Item row scoped to its project + workspace (404).

        The workspace predicate goes through the owning Project join, so
        a Video Item whose project belongs to another workspace behaves
        as unknown (AC6) — it can never be read or mutated across
        workspace boundaries.
        """
        video = self._session.scalar(
            select(VideoItem)
            .join(Project, Project.id == VideoItem.project_id)
            .where(
                VideoItem.id == video_id,
                VideoItem.project_id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if video is None:
            raise VideoNotFoundError(
                f"Video Item {video_id!r} not found in project {project_id!r}"
            )
        return video

    def _next_position(self, project_id: str) -> int:
        """The append-at-end position: MAX(position)+1 over ALL rows
        (active + archived) so positions stay unique across the project."""
        current_max = self._session.scalar(
            select(func.max(VideoItem.position)).where(
                VideoItem.project_id == project_id
            )
        )
        return 0 if current_max is None else current_max + 1

    def _active_positions(self, project_id: str) -> list[int]:
        """Sorted positions of active Video Items (used by reorder)."""
        rows = self._session.scalars(
            select(VideoItem.position)
            .where(
                VideoItem.project_id == project_id,
                VideoItem.status != ARCHIVED_VIDEO_STATUS,
            )
            .order_by(VideoItem.position)
        ).all()
        return list(rows)

    # ── Creation (append at end; AC3) ────────────────────────────────────

    def create_video(
        self,
        *,
        project_id: str,
        workspace_id: str,
        title: str,
        source_channel_id: str | None = None,
        resume_step: str | None = None,
        legacy_id: str | None = None,
    ) -> VideoItemRecord:
        """Append one Video Item at the end of the Project's list.
        The owning Project must be active (archived Projects reject new
        Video Items).  NEW channel references are validated BEFORE
        binding (AC4/atomic writer policy).  Position is computed inside
        the caller's transaction; the service's ``BEGIN IMMEDIATE``
        reservation makes concurrent appends serialize, and the
        repository retries deterministically on a position-uniqueness
        race (``AppendRetryError``) — a raw ``IntegrityError`` never escapes.

        Probe metadata (``duration_ms``, ``width``, ``height``,
        ``fps_num``, ``fps_den``) is deliberately NOT accepted on the S03
        create write path: it is read-only in this task and S05 owns
        import/media probing (it remains readable in the response DTO).

        Raises:
            ChannelReferenceError: an invalid source-channel reference.
            VideoNotFoundError: project missing / cross-workspace /
                archived.
            AppendRetryError: the caller lost the position race; the service
                retries once within the same reserved write transaction.
            ValueError: invalid title values.
        """
        normalized = normalize_video_title(title)
        if not normalized:
            raise ValueError("title must be a non-empty string")
        if len(normalized) > 240:
            raise ValueError("title must be at most 240 characters")

        project = self._load_project(project_id, workspace_id)
        if project.status == "archived":
            raise VideoConflictError(
                f"Project {project_id!r} is archived; new Video Items are "
                "rejected until a restore policy exists"
            )

        _validate_source_channel(self._session, workspace_id, source_channel_id)

        position = self._next_position(project_id)
        video = VideoItem(
            project_id=project_id,
            legacy_id=legacy_id,
            title=normalized,
            position=position,
            status=DEFAULT_VIDEO_STATUS,
            source_channel_id=source_channel_id,
            resume_step=resume_step,
            revision=1,
        )
        self._session.add(video)
        try:
            self._session.flush()
        except IntegrityError as exc:
            # The UNIQUE(project_id, position) index is the concurrency
            # backstop.  ONLY an exact position-uniqueness failure
            # (uq_video_item_project_position) is an append race; every
            # other integrity error (e.g. the (project_id, legacy_id)
            # unique index, the channel FK, the project FK) must propagate
            # as the real failure and roll the transaction back.
            if self._is_position_unique_failure(exc):
                raise AppendRetryError(
                    f"concurrent append to project {project_id!r} collided; retry"
                ) from exc
            raise
        return _video_record(video)

    def _is_position_unique_failure(self, exc: IntegrityError) -> bool:
        """True only for the exact ``(project_id, position)`` UNIQUE failure.

        SQLite reports ``UNIQUE constraint failed: video_item.project_id,
        video_item.position`` for the append position race (the index
        ``uq_video_item_project_position``).  We parse the column list
        after the marker and compare it EXACTLY (order and membership) to
        that pair, so a partial or reordered text (e.g. just
        ``video_item.position``, or
        ``video_item.position, video_item.project_id``) is never mistaken
        for the append race.  A different unique index (e.g.
        ``uq_video_item_project_legacy_id``) reports its own column pair
        and must NOT be treated as an append race.
        """
        message = str(exc.orig)
        marker = "UNIQUE constraint failed: "
        start = message.rfind(marker)
        if start == -1:
            return False
        columns = [column.strip() for column in message[start + len(marker):].split(",")]
        return columns == ["video_item.project_id", "video_item.position"]

    # ── Reads ─────────────────────────────────────────────────────────────

    def get_video(
        self, video_id: str, project_id: str, workspace_id: str
    ) -> VideoItemRecord:
        """Load a Video Item by id within *project_id* (404 semantics)."""
        return _video_record(self._load_video(video_id, project_id, workspace_id))

    def list_videos(
        self,
        project_id: str,
        workspace_id: str,
        *,
        status: str | None = None,
        active_only: bool = True,
    ) -> list[VideoItemRecord]:
        """List Video Items for a project (archived excluded by default).

        The owning Project must exist in the workspace (404 semantics);
        archived Projects remain readable (AC5).  The list is ordered by
        position, then creation time for determinism.
        """
        self._load_project(project_id, workspace_id)
        query = select(VideoItem).where(VideoItem.project_id == project_id)
        if status is not None:
            if status not in VIDEO_PIPELINE_STATES:
                raise ValueError(
                    f"status must be one of {VIDEO_PIPELINE_STATES}, got {status!r}"
                )
            query = query.where(VideoItem.status == status)
        elif active_only:
            query = query.where(VideoItem.status != ARCHIVED_VIDEO_STATUS)
        query = query.order_by(VideoItem.position, VideoItem.created_at)
        return [_video_record(row) for row in self._session.scalars(query).all()]

    # ── Business update (atomic CAS, AC4) ─────────────────────────────────

    def update_video(
        self,
        video_id: str,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
        title: str | None = None,
        status: str | None = None,
        source_channel_id: Any = None,
        resume_step: Any = None,
    ) -> VideoItemRecord:
        """Apply one business update via a conditional database UPDATE.

        The CAS predicate is ``id = :video_id AND project_id =
        :project_id AND revision = :expected_revision``; the affected row
        count decides the outcome:
        - 0 rows + video exists (wrong revision) → VideoConflictError;
        - 0 rows + video missing / project archived → VideoNotFoundError;
        - 1 row → accepted; ``revision`` bumped exactly once by the SQL.

        Generic PATCH can never enter or leave ``archived`` (the archive
        endpoint is the only removal path).  NEW source-channel
        references are validated BEFORE the CAS binds values (AC4); an
        existing reference is only revalidated when the PATCH explicitly
        changes it.  Ownership of the Project/workspace and the target
        Video is verified BEFORE any channel validation, so a
        missing/cross-workspace/cross-project target is always a safe
        404 (never a channel-dependent 422).  ``None`` values mean "no
        change" for every field (the API layer passes explicit ``null``
        clears via a sentinel).
        """
        if title is not None:
            normalized = normalize_video_title(title)
            if not normalized:
                raise ValueError("title must be a non-empty string")
            if len(normalized) > 240:
                raise ValueError("title must be at most 240 characters")
        else:
            normalized = None

        if status == ARCHIVED_VIDEO_STATUS:
            raise ValueError(
                "status 'archived' is only accepted by the archive endpoint"
            )
        if status is not None and status not in VIDEO_PIPELINE_STATES:
            raise ValueError(
                f"status must be one of {VIDEO_PIPELINE_STATES}, got {status!r}"
            )

        # Ownership FIRST (PM correction 3): prove the Project/workspace
        # and the target Video belong to the requested project BEFORE any
        # channel-reference validation.  A missing/cross-workspace/
        # cross-project target must produce a safe 404 regardless of the
        # payload's channel id — never a channel-dependent 422.
        self._load_video(video_id, project_id, workspace_id)

        # Archived Project invariant (AC7): active workflow mutation is
        # rejected on archived Projects until a restore policy exists.
        # Reads of archived Projects stay allowed; business writes do not.
        project = self._session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if project is not None and project.status == "archived":
            raise VideoConflictError(
                f"Project {project_id!r} is archived; Video Item mutation is "
                "rejected until a restore policy exists"
            )

        # Source channel: validate NEW assignments only (the sentinel UNSET
        # means "explicit null" (clear), None means "omitted" (unchanged)).
        if source_channel_id not in (None, UNSET):
            _validate_source_channel(
                self._session, workspace_id, str(source_channel_id)
            )

        values: dict[str, Any] = {}
        if normalized is not None:
            values["title"] = normalized
        if status is not None:
            values["status"] = status
        if source_channel_id not in (None,):
            values["source_channel_id"] = (
                None if source_channel_id is UNSET else source_channel_id
            )
        if resume_step not in (None,):
            values["resume_step"] = (
                None if resume_step is UNSET else resume_step
            )
        values["revision"] = VideoItem.revision + 1
        values["updated_at"] = datetime.now(UTC)

        result = self._session.execute(
            update(VideoItem)
            .where(
                VideoItem.id == video_id,
                VideoItem.project_id == project_id,
                VideoItem.revision == expected_revision,
                VideoItem.status != ARCHIVED_VIDEO_STATUS,
            )
            .values(**values)
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            # Distinguish stale revision from unknown/archived states.
            probe = self._session.execute(
                select(VideoItem.revision, VideoItem.status)
                .join(Project, Project.id == VideoItem.project_id)
                .where(
                    VideoItem.id == video_id,
                    VideoItem.project_id == project_id,
                    Project.workspace_id == workspace_id,
                )
            ).first()
            if probe is None:
                raise VideoNotFoundError(
                    f"Video Item {video_id!r} not found in project {project_id!r}"
                )
            if probe[1] == ARCHIVED_VIDEO_STATUS:
                raise VideoConflictError(
                    f"Video Item {video_id} is archived and immutable"
                )
            raise VideoConflictError(
                f"revision mismatch for Video Item {video_id}: expected "
                f"{expected_revision}, current {probe[0]}"
            )
        self._session.flush()
        return self.get_video(video_id, project_id, workspace_id)

    # ── Archive (AC5; atomic CAS, idempotent) ─────────────────────────────

    def archive_video(
        self,
        video_id: str,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
    ) -> VideoItemRecord:
        """Archive a Video Item with an atomic CAS.

        - Active row + matching revision → archived (``archived_at`` set,
          ``revision`` bumped once).
        - Already-archived row → idempotent no-op returning the current
          row WITHOUT another bump (a repeat against an archived row must
          not fail and must not bump).
        - Active row + stale revision → VideoConflictError (409).
        - Concurrent winner: the loser's zero-row CAS re-reads with a
          FRESH database SELECT (bypassing the identity map — the
          ``populate_existing`` flag forces a reload of the strongly
          cached row) and returns the now-archived row idempotently
          (200, no bump).
        - Missing / cross-project id → VideoNotFoundError (404).

        Archive preserves all metadata and relationships (no cascade, no
        hard delete — contract §5).  There is deliberately **no**
        hard-delete method.
        """
        current = self._session.scalar(
            select(VideoItem)
            .join(Project, Project.id == VideoItem.project_id)
            .where(
                VideoItem.id == video_id,
                VideoItem.project_id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if current is None:
            raise VideoNotFoundError(
                f"Video Item {video_id!r} not found in project {project_id!r}"
            )
        if self._archive_after_read is not None:
            self._archive_after_read()
        if current.status == ARCHIVED_VIDEO_STATUS:
            return _video_record(current)

        result = self._session.execute(
            update(VideoItem)
            .where(
                VideoItem.id == video_id,
                VideoItem.project_id == project_id,
                VideoItem.status != ARCHIVED_VIDEO_STATUS,
                VideoItem.revision == expected_revision,
            )
            .values(
                status=ARCHIVED_VIDEO_STATUS,
                archived_at=datetime.now(UTC),
                revision=VideoItem.revision + 1,
                updated_at=datetime.now(UTC),
            )
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            # Concurrent-archive race: a second caller may have read
            # active, lost the CAS to the first archiver, and now sees
            # zero rows.  Force a FRESH database read (explicit SELECT
            # with populate_existing=True, bypassing the identity map —
            # session.get would return the caller's stale in-session
            # object): if the row is now archived, return it idempotently
            # (no bump, 200); otherwise report the stale active revision
            # (409).
            fresh = self._session.execute(
                select(VideoItem)
                .join(Project, Project.id == VideoItem.project_id)
                .where(
                    VideoItem.id == video_id,
                    VideoItem.project_id == project_id,
                    Project.workspace_id == workspace_id,
                )
                .execution_options(populate_existing=True)
            ).scalar_one_or_none()
            if fresh is not None and fresh.status == ARCHIVED_VIDEO_STATUS:
                return _video_record(fresh)
            raise VideoConflictError(
                f"revision mismatch for Video Item {video_id}: expected "
                f"{expected_revision} while archiving"
            )
        self._session.flush()
        return self.get_video(video_id, project_id, workspace_id)

    # ── Atomic full-list reorder (AC3/AC4) ────────────────────────────────

    def reorder_videos(
        self,
        project_id: str,
        workspace_id: str,
        *,
        expected_project_revision: int,
        video_item_ids: list[str],
    ) -> list[VideoItemRecord]:
        """Atomically reorder the complete set of active Video Items.

        Contract (AC4):
        - The request carries the expected Project revision and the
          COMPLETE set of active Video Item ids exactly once.
        - Missing/extra/duplicate/cross-project ids fail BEFORE any
          write (no partial writes).
        - The Project row is bumped exactly once (CAS on
          ``expected_project_revision``).
        - Only Video Items whose position changes are bumped.
        - The requested active order is mapped onto the SORTED existing
          active position slots; archived rows keep their positions
          untouched (the logical active order is gap-tolerant after an
          archive).  Positions are rewritten with collision-safe
          two-phase offsets so the ``UNIQUE(project_id, position)``
          index never fires mid-transaction.
        - After a reorder, the active list is returned in the requested
          order at the existing active slots (no NEW gaps are introduced
          and no existing gaps are filled; archived positions are never
          rewritten).

        Raises:
            ReorderValidationError: id-set contract violation.
            VideoNotFoundError: project missing / cross-workspace /
                archived.
            VideoConflictError: stale project revision.
        """
        project = self._load_project(project_id, workspace_id)
        if project.status == "archived":
            raise VideoConflictError(
                f"Project {project_id!r} is archived; reorder is rejected "
                "until a restore policy exists"
            )

        # Validate the complete active set exactly once (no partial writes).
        active_rows = self._session.scalars(
            select(VideoItem).where(
                VideoItem.project_id == project_id,
                VideoItem.status != ARCHIVED_VIDEO_STATUS,
            )
        ).all()
        active_by_id = {row.id: row for row in active_rows}

        # Deterministic pause point for concurrency tests: both callers
        # have now read the active set; the next write is the CAS.
        if self._after_read is not None:
            self._after_read()

        if len(video_item_ids) != len(set(video_item_ids)):
            raise ReorderValidationError(
                "video_item_ids must contain each active Video Item exactly once"
            )
        if set(video_item_ids) != set(active_by_id):
            missing = sorted(set(active_by_id) - set(video_item_ids))
            extra = sorted(set(video_item_ids) - set(active_by_id))
            raise ReorderValidationError(
                "reorder must carry the complete set of active Video Items; "
                f"missing={missing} extra={extra}"
            )

        # CAS the Project revision exactly once before any position write.
        project_update = self._session.execute(
            update(Project)
            .where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
                Project.status != "archived",
                Project.revision == expected_project_revision,
            )
            .values(
                revision=Project.revision + 1,
                updated_at=datetime.now(UTC),
            )
        )
        if project_update.rowcount == 0:  # type: ignore[attr-defined]
            probe = self._session.execute(
                select(Project.revision).where(
                    Project.id == project_id,
                    Project.workspace_id == workspace_id,
                )
            ).first()
            if probe is None:
                raise VideoNotFoundError(
                    f"Project {project_id!r} not found in workspace {workspace_id!r}"
                )
            raise VideoConflictError(
                f"revision mismatch for Project {project_id}: expected "
                f"{expected_project_revision} while reordering, current {probe[0]}"
            )

        # Gap-tolerant mapping (PM correction 1): the requested active
        # order is mapped onto the SORTED existing active position slots.
        # Archived rows keep their positions untouched, so the active
        # order may be gap-tolerant after an archive (e.g. active slots 0
        # and 2 with a middle archived row at 1).  The UNIQUE(project_id,
        # position) constraint is never violated and archived positions
        # are never rewritten — the domain contract only requires a
        # unique non-negative position and owned ordering, not gap-free
        # numeric positions (archived slots are intentionally preserved).
        active_slots = self._active_positions(project_id)
        desired_positions: dict[str, int] = {
            vid: slot for vid, slot in zip(video_item_ids, active_slots)
        }
        changed = [
            row for row in active_rows if row.position != desired_positions[row.id]
        ]

        if changed:
            # Two-phase positions: move every changed row to a
            # collision-free offset ABOVE the current max first, then
            # place each row at its desired existing active slot.  The
            # UNIQUE(project_id, position) index never fires
            # mid-transaction and archived positions are never touched.
            base = self._next_position(project_id)
            now = datetime.now(UTC)
            for i, row in enumerate(changed):
                row.position = base + i + 1
                row.updated_at = now
            self._session.flush()
            for _i, row in enumerate(changed):
                row.position = desired_positions[row.id]
                row.updated_at = now
                row.revision = row.revision + 1
            self._session.flush()

        # Return the ordered active list (requested order, active slots).
        ordered = [
            active_by_id[vid] for vid in video_item_ids if vid in active_by_id
        ]
        return [_video_record(row) for row in ordered]


class VideoItemService:
    """Request-bounded facade: exactly ONE transaction per operation.

    The service owns the session lifecycle (open → operate → commit;
    roll back on error).  Writes acquire the SQLite writer reservation
    (``BEGIN IMMEDIATE``) from their first read, so a competing channel
    archive or project archive cannot commit between channel validation
    and the Video Item write (S03-T02 atomic writer policy).
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
            repo = VideoItemRepository(session)
            try:
                result = fn(repo, *args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def _run_write(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Run a SQLite write under a reserved lock from its first read."""
        with self._session_factory() as session:
            try:
                session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                result = fn(VideoItemRepository(session), *args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def create(
        self,
        *,
        project_id: str,
        workspace_id: str,
        title: str,
        source_channel_id: str | None = None,
        resume_step: str | None = None,
    ) -> VideoItemRecord:
        """Append a Video Item under the reserved writer lock.

        A concurrent append that loses the position race raises
        ``AppendRetryError`` from the repository; the service retries once
        deterministically within the same reserved transaction so no raw
        ``IntegrityError`` leaks to the API (task concurrency bullet).

        Probe metadata is read-only in this task (S05 owns import/probing):
        the S03 create write path never accepts ``duration_ms``/``width``/
        ``height``/``fps_num``/``fps_den``.
        """
        with self._session_factory() as session:
            repo = VideoItemRepository(session)
            try:
                session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                try:
                    record = repo.create_video(
                        project_id=project_id,
                        workspace_id=workspace_id,
                        title=title,
                        source_channel_id=source_channel_id,
                        resume_step=resume_step,
                    )
                except AppendRetryError:
                    session.rollback()
                    session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                    record = repo.create_video(
                        project_id=project_id,
                        workspace_id=workspace_id,
                        title=title,
                        source_channel_id=source_channel_id,
                        resume_step=resume_step,
                    )
                session.commit()
                return record
            except Exception:
                session.rollback()
                raise

    def get(self, video_id: str, project_id: str, workspace_id: str) -> VideoItemRecord:
        return self._run(
            VideoItemRepository.get_video, video_id, project_id, workspace_id
        )

    def list_videos(
        self,
        project_id: str,
        workspace_id: str,
        *,
        status: str | None = None,
        active_only: bool = True,
    ) -> list[VideoItemRecord]:
        result = self._run(
            VideoItemRepository.list_videos,
            project_id,
            workspace_id,
            status=status,
            active_only=active_only,
        )
        return result

    def update(
        self,
        video_id: str,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
        title: str | None = None,
        status: str | None = None,
        source_channel_id: Any = None,
        resume_step: Any = None,
    ) -> VideoItemRecord:
        return cast(
            "VideoItemRecord",
            self._run_write(
                VideoItemRepository.update_video,
                video_id,
                project_id,
                workspace_id,
                expected_revision=expected_revision,
                title=title,
                status=status,
                source_channel_id=source_channel_id,
                resume_step=resume_step,
            ),
        )

    def archive(
        self,
        video_id: str,
        project_id: str,
        workspace_id: str,
        *,
        expected_revision: int,
    ) -> VideoItemRecord:
        return cast(
            "VideoItemRecord",
            self._run_write(
                VideoItemRepository.archive_video,
                video_id,
                project_id,
                workspace_id,
                expected_revision=expected_revision,
            ),
        )

    def reorder(
        self,
        project_id: str,
        workspace_id: str,
        *,
        expected_project_revision: int,
        video_item_ids: list[str],
    ) -> list[VideoItemRecord]:
        return cast(
            "list[VideoItemRecord]",
            self._run_write(
                VideoItemRepository.reorder_videos,
                project_id,
                workspace_id,
                expected_project_revision=expected_project_revision,
                video_item_ids=video_item_ids,
            ),
        )
