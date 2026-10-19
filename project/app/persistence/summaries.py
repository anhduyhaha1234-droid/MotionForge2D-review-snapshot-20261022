"""Project summary read model (S03-T04) — live, durable, read-only.

This module implements the approved read-model contract of
``docs/pm/sessions/S03-T04-project-summary/TASK.md`` on the S01/S02
durable tables.  Design rules enforced here:

- **No persistence of aggregates.**  ``SummaryRepository`` derives every
  value live from durable rows inside ONE consistent read boundary (a
  single caller-owned Session; the service commits nothing because reads
  only).  There is no cache, no aggregate table, no migration, and no
  filesystem/JSON write.
- **One shared algorithm.**  ``summarize_one`` and ``list_summaries``
  both call the same ``_compose`` batch composer so the collection and
  item routes can never disagree (AC9, CORRECTION P1.1).  The composer
  performs a CONSTANT number of SQL queries for a page — independent of
  page size and of the total number of Projects:
    1. one page-select of ``project`` rows (ordered by the
       authoritative global activity key, ``last_activity DESC, id
       ASC``), then, for the whole page at once,
    2. one GROUP BY ``video_item.status``,
    3. one video-id read,
    4. one max(video.updated_at) read,
    5. one all-Job activity key read (max of ``updated_at``/``created_at``
       for Project- and real-Video-owned jobs of ANY state),
    6. one active-job list read (``created_at DESC, id ASC``, bounded),
    7. one active-job count read,
    8. one artifact-ownership read,
    9. one artifact-totals read,
    10. one channel-display read.
  There is no per-Project query anywhere — N+1 is impossible by
  construction (CORRECTION P1.1).
- **No join inflation.**  Video counts use a GROUP BY on ``video_item``
  (one row per video).  Artifact bytes deduplicate by Artifact id in
  Python after a single ownership join restricted to the owning
  Workspace's ``artifact`` rows, so a shared artifact owned by several
  Video Items of the same Project is counted once and another workspace's
  artifacts are never counted.
- **Polymorphic owner safety (AC5).**  Active jobs are owned by the
  Project itself or by its real Video Items only (``owner_type`` +
  ``owner_id`` membership).  Orphan owner ids, cross-workspace owners and
  terminal states are excluded by construction.
- **Capability honesty (AC4).**  ``next_action`` is derived only from the
  authoritative Video Item status set and the Project lifecycle.  No QC
  blocker, output version, ETA, or capability/system readiness is
  fabricated; unavailable future capabilities stay disabled with a
  blocker.
- **DTO boundary.**  The repository returns plain frozen dataclasses; no
  ORM instance ever crosses into the API layer (AC2).

Storage policy (AC6, CORRECTION P2.6): ``total_bytes`` sums
``size_bytes`` ONLY for ``ready`` artifacts; ``missing`` and ``trash``
artifacts are counted per state but never contribute bytes; **every**
deduplicated artifact with a ``NULL`` size (``unknown_size_count``) is
counted as unknown **regardless of its state** and excluded from the byte
total.

Global ordering (CORRECTION P1.2): page selection orders by the
authoritative ``last_activity_at`` — ``max(project.updated_at,
newest video updated_at, newest owned-Job updated_at, newest owned-Job
created_at)`` — computed BEFORE ``ORDER BY ... LIMIT/OFFSET``, then by
project id ASC on ties.  This is a global order across page boundaries:
an old Project with a newer Video or terminal Job outranks a recently
updated Project.

SQL page bounding (CORRECTION P2-R2.1): the page SELECT applies SQL
``OFFSET offset LIMIT limit+1`` AFTER the global ordering, so the
database — not Python — bounds the rows.  ``limit + 1`` is the
honest-``has_more`` probe; the extra row is never composed.

Per-Project active-job top-10 (CORRECTION P2-R2.2): the active-job list
uses a window rank partitioned by the RESOLVED Project ownership
(project id for Project-owned jobs, real Video Item id for
video_item-owned jobs, NULL for orphans) and ordered by
``created_at DESC, id ASC``; the outer SELECT keeps ``rank <= 10`` per
partition.  A Project whose jobs are all older than another page
Project's newest 10 still receives its OWN newest 10, with one constant
query for the whole page (no N+1).

Explicit read snapshot (CORRECTION P1.4): the request dependency
(``app/api/deps.get_summary_repository``) begins an explicit SQLAlchemy
read transaction (``session.begin()``) at the request boundary and
closes it with ``rollback()`` — every statement in one request observes
one SQLite snapshot.  This repository itself never commits.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import case, func, literal, or_, select
from sqlalchemy.orm import Session

from app.persistence.models import (
    ARCHIVED_VIDEO_STATUS,
    PROJECT_STATUSES,
    VIDEO_PIPELINE_STATES,
    Artifact,
    ArtifactOwner,
    Channel,
    Job,
    Project,
    VideoItem,
)

__all__ = [
    "ACTIVE_JOB_STATES",
    "FUTURE_CAPABILITY_BLOCKERS",
    "NEXT_ACTION_BLOCKERS",
    "NEXT_ACTION_NONE",
    "NEXT_ACTION_STATUSES",
    "ActiveJobRecord",
    "ChannelDisplayRecord",
    "ProjectSummaryError",
    "ProjectSummaryNotFoundError",
    "ProjectSummaryRecord",
    "StorageRecord",
    "SummaryRepository",
    "VideoCountsRecord",
    "determine_next_action",
    "map_video_status_counts",
]

#: Exact active Job states (DURABLE_JOB_CONTRACT V1.1 §4).
ACTIVE_JOB_STATES = ("pending", "queued", "running", "cancelling")

#: Semantic next-action codes.  The backend returns codes, never localized
#: UI prose (TASK.md read-model contract).
NEXT_ACTION_NONE = "none"
NEXT_ACTION_STATUSES = (
    "analyze_video",
    "map_objects",
    "create_demo",
    "apply_reskin",
    "review_work",
    "export_video",
    "retry_failed",
)

#: Blocker codes for disabled future capabilities (capability honesty).
NEXT_ACTION_BLOCKERS = (
    "qc_unavailable",
    "output_unavailable",
    "capability_unavailable",
)

#: Capability blockers for semantic actions whose authoritative domain has
#: not landed yet (roadmap PLANNED sprints).  Explicit so the honest
#: ``enabled=False`` + stable blocker contract survives per-sprint flips:
#: when a sprint lands, its entry moves to ``None`` and the action becomes
#: enabled.  Codes are exactly the approved blocker vocabulary.
FUTURE_CAPABILITY_BLOCKERS = {
    "analyze_video": "capability_unavailable",  # S05 import/analyze PLANNED
    "map_objects": "capability_unavailable",  # S08 object intelligence PLANNED
    "create_demo": "capability_unavailable",  # S09 demo-first reskin PLANNED
    "apply_reskin": "capability_unavailable",  # S10 full apply PLANNED
    "review_work": "qc_unavailable",  # S11 QC/review queue PLANNED
    "export_video": "output_unavailable",  # S12 validated output PLANNED
    "retry_failed": "capability_unavailable",  # video retry pipeline PLANNED
}


class ProjectSummaryError(Exception):
    """Base error for the summary read model."""


class ProjectSummaryNotFoundError(ProjectSummaryError):
    """No Project row exists for the requested id (in the workspace)."""


@dataclass(frozen=True)
class StorageRecord:
    """Known managed storage for a Project's owned Artifacts (AC6)."""

    total_bytes: int
    artifact_count: int
    ready_count: int
    missing_count: int
    trash_count: int
    unknown_size_count: int


@dataclass(frozen=True)
class ChannelDisplayRecord:
    """Display-only Channel reference (id + name; no role revalidation)."""

    channel_id: str
    name: str
    role: str
    status: str


@dataclass(frozen=True)
class VideoCountsRecord:
    """Video Item counts without join inflation (one row per video)."""

    active: int
    archived: int
    total: int
    completed: int
    attention: int
    completion_percent: float
    by_status: dict[str, int]


@dataclass(frozen=True)
class ActiveJobRecord:
    """A bounded newest-first active Job owned by the Project or its videos."""

    job_id: str
    job_type: str
    owner_type: str
    owner_id: str
    state: str
    progress: float
    created_at: datetime | None


@dataclass(frozen=True)
class ProjectSummaryRecord:
    """Read model of one Project summary (no ORM instances escape)."""

    project_id: str
    workspace_id: str
    name: str
    description: str
    status: str
    revision: int
    created_at: datetime | None
    updated_at: datetime | None
    archived_at: datetime | None
    source_channel: ChannelDisplayRecord | None
    production_channel: ChannelDisplayRecord | None
    video_counts: VideoCountsRecord
    next_action: str
    next_action_video_item_id: str | None
    next_action_enabled: bool
    next_action_blocker: str | None
    active_jobs: list[ActiveJobRecord]
    active_job_count: int
    last_activity_at: datetime | None
    storage: StorageRecord


# ── Pure mapping helpers (unit-testable, no database) ────────────────────────


def map_video_status_counts(status_counts: dict[str, int]) -> VideoCountsRecord:
    """Map a raw ``{status: count}`` dict into the exact summary counts.

    Every one of the 13 approved Video Item statuses is present in
    ``by_status`` including zeroes.  ``active`` counts every non-archived
    status; ``total`` counts every row.  ``completed`` is the count of
    ``completed`` videos; ``attention`` is the count of statuses that need
    a human decision (``needs_review``, ``failed``, ``mapping_required``,
    ``demo_required``).  ``completion_percent`` is
    ``completed / active * 100`` and is zero when there are no active
    videos (CORRECTION P1.3) — never invented ordinal pipeline progress.
    """
    by_status = {
        status: int(status_counts.get(status, 0)) for status in VIDEO_PIPELINE_STATES
    }
    total = sum(by_status.values())
    archived = by_status[ARCHIVED_VIDEO_STATUS]
    active = total - archived
    completed = by_status["completed"]
    completion_percent = (completed / active * 100.0) if active > 0 else 0.0
    return VideoCountsRecord(
        active=active,
        archived=archived,
        total=total,
        completed=completed,
        attention=(
            by_status["needs_review"]
            + by_status["failed"]
            + by_status["mapping_required"]
            + by_status["demo_required"]
        ),
        completion_percent=completion_percent,
        by_status=by_status,
    )


def determine_next_action(
    *,
    project_status: str,
    video_status: str,
    video_id: str | None = None,
    project_has_archived_only_videos: bool = False,
) -> tuple[str, str | None, bool, str | None]:
    """Return ``(code, video_item_id, enabled, blocker)`` deterministically.

    Rules (TASK.md read-model contract, AC4):

    - Archived Project or no non-archived videos → ``none``, disabled, no
      blocker.
    - The action maps from the authoritative Video Item status and points
      at that exact Video Item id.
    - Unavailable future capabilities stay disabled with an explicit
      blocker (no capability/system readiness is fabricated): every
      semantic action whose fulfilling capability has not landed yet
      returns ``enabled=False`` + a stable blocker code
      (``FUTURE_CAPABILITY_BLOCKERS``).
    """
    if project_status == "archived" or project_has_archived_only_videos:
        return (NEXT_ACTION_NONE, None, False, None)

    mapping = {
        "imported": ("analyze_video", True),
        "analyzing": ("analyze_video", True),
        "objects_ready": ("map_objects", True),
        "mapping_required": ("map_objects", True),
        "demo_required": ("create_demo", True),
        "demo_approved": ("apply_reskin", True),
        "applying_reskin": ("apply_reskin", True),
        "needs_review": ("review_work", True),
        "ready_to_export": ("export_video", True),
        "rendering": ("export_video", True),
        "failed": ("retry_failed", True),
    }
    code, _enabled = mapping.get(video_status, (NEXT_ACTION_NONE, False))
    if code == NEXT_ACTION_NONE:
        return (NEXT_ACTION_NONE, None, False, None)
    # Capability honesty: the semantic action is correct for the state, but
    # the capability that would fulfill it has not landed yet (roadmap
    # PLANNED sprint) — return it disabled with a stable blocker instead of
    # advertising an unavailable button as enabled.
    blocker = FUTURE_CAPABILITY_BLOCKERS.get(code)
    return (code, video_id, blocker is None, blocker)


# ── Repository ───────────────────────────────────────────────────────────────


class SummaryRepository:
    """Read-only summary repository bound to one Session.

    The repository never commits/rolls back; reads only.  ``_compose`` is
    the single batch algorithm shared by collection and item routes.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def summarize_one(self, project_id: str, workspace_id: str) -> ProjectSummaryRecord:
        """Summarize one Project within *workspace_id* (404 semantics)."""
        project = self._session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )
        if project is None:
            raise ProjectSummaryNotFoundError(
                f"Project {project_id!r} not found in workspace {workspace_id!r}"
            )
        records = self._compose([project], workspace_id)
        return records[project_id]

    def list_summaries(
        self,
        workspace_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ProjectSummaryRecord], int]:
        """List Project summaries for a workspace (archived excluded by
        default), bounded by *limit*/*offset*.

        Returns ``(page_records, total_count)`` where *total_count* is
        the exact number of rows matching the workspace/filter predicate
        (CORRECTION P2.7 — an honest ``total``, not the page count).

        Page selection uses the authoritative global activity key
        (``last_activity_at DESC``, then project id ASC) computed in SQL
        BEFORE ``ORDER BY ... LIMIT/OFFSET`` (CORRECTION P1.2), so the
        page boundary is stable across pages even when an old Project has
        a newer Video or terminal Job.  The returned page is composed by
        the SAME batch algorithm as the item route (AC9) with a constant
        query count independent of page size.

        The page is fetched with ``limit + 1`` rows so the caller can
        report an honest ``has_more`` even when the final page is exactly
        full (CORRECTION P2.7); the extra row is never composed.
        """
        if status is not None and status not in PROJECT_STATUSES:
            raise ValueError(
                f"status must be one of {PROJECT_STATUSES}, got {status!r}"
            )
        query = select(Project).where(Project.workspace_id == workspace_id)
        if status is not None:
            query = query.where(Project.status == status)
        else:
            query = query.where(Project.status != "archived")
        # Exact filtered total (P2.7): one COUNT over the SAME predicate.
        total_count = int(
            self._session.scalar(
                select(func.count(Project.id))
                .where(Project.workspace_id == workspace_id)
                .where(
                    Project.status == status
                    if status is not None
                    else Project.status != "archived"
                )
            )
            or 0
        )
        # Global authoritative ordering BEFORE the page slice (P1.2), then
        # apply SQL OFFSET/LIMIT so the DATABASE bounds the rows — the page
        # SELECT never materializes off-page Projects (CORRECTION P2-R2.1).
        # ``limit + 1`` is the honest-``has_more`` probe (P2.7).
        query = query.order_by(_activity_expr().desc(), Project.id)
        bounded_limit = max(1, min(int(limit), 200))
        bounded_offset = max(0, int(offset))
        projects = self._session.scalars(
            query.offset(bounded_offset).limit(bounded_limit + 1)
        ).all()
        if not projects:
            return [], total_count
        page = list(projects[:bounded_limit])
        records = self._compose(page, workspace_id)
        return [records[p.id] for p in page], total_count

    # ── Shared batch algorithm (AC9, CORRECTION P1.1) ──────────────────────

    def _compose(
        self, projects: Sequence[Project], workspace_id: str
    ) -> dict[str, ProjectSummaryRecord]:
        """Compose summaries for *projects* in exactly 9 batch queries.

        All reads are restricted to *workspace_id*; every loop below
        indexes an already-fetched mapping (never a query), so the total
        query count is constant for the page.
        """
        session = self._session
        project_ids = [p.id for p in projects]
        project_ids_in = project_ids if len(project_ids) > 1 else project_ids

        # 1. Video counts per project (one row per video; no inflation).
        video_rows = session.execute(
            select(VideoItem.project_id, VideoItem.status, func.count(VideoItem.id))
            .where(VideoItem.project_id.in_(project_ids_in))
            .group_by(VideoItem.project_id, VideoItem.status)
        ).all()
        status_by_project: dict[str, dict[str, int]] = {
            pid: {} for pid in project_ids
        }
        for pid, status, count in video_rows:
            status_by_project[pid][status] = int(count)
        video_counts = {
            pid: map_video_status_counts(status_by_project[pid]) for pid in project_ids
        }

        # 2. Real Video Item ids per project (active + archived).  They bound
        #    job ownership and artifact ownership to real rows, so an orphan
        #    polymorphic owner can never match (AC5).
        video_id_rows = session.execute(
            select(VideoItem.project_id, VideoItem.id).where(
                VideoItem.project_id.in_(project_ids_in)
            )
        ).all()
        video_ids_by_project: dict[str, list[str]] = {pid: [] for pid in project_ids}
        for pid, vid in video_id_rows:
            video_ids_by_project[pid].append(vid)

        # 3. Newest Video updated_at per project (activity P1.2/P1.5).
        max_video_rows = session.execute(
            select(VideoItem.project_id, func.max(VideoItem.updated_at))
            .where(VideoItem.project_id.in_(project_ids_in))
            .group_by(VideoItem.project_id)
        ).all()
        max_video_by_project: dict[str, datetime | None] = {
            pid: max_ts for pid, max_ts in max_video_rows
        }

        # 4. All Job activity keys per project — ANY state (active AND
        #    terminal), Project- or real-Video-owned (P1.5).  A job's
        #    authoritative activity is max(updated_at, created_at).
        job_activity_rows = session.execute(
            select(
                Job.owner_type,
                Job.owner_id,
                func.max(Job.updated_at),
                func.max(Job.created_at),
            )
            .where(
                Job.workspace_id == workspace_id,
                or_(
                    (Job.owner_type == "project") & (Job.owner_id.in_(project_ids_in)),
                    (Job.owner_type == "video_item")
                    & (
                        Job.owner_id.in_(
                            [vid for ids in video_ids_by_project.values() for vid in ids]
                        )
                        if any(video_ids_by_project.values())
                        else Job.owner_id == "_none_"
                    ),
                ),
            )
            .group_by(Job.owner_type, Job.owner_id)
        ).all()
        job_activity_by_owner: dict[tuple[str, str], datetime | None] = {}
        for owner_type, owner_id, max_updated, max_created in job_activity_rows:
            candidates = [t for t in (max_updated, max_created) if t is not None]
            job_activity_by_owner[(owner_type, owner_id)] = max(candidates) if candidates else None

        # 6. Next-action target videos: the first non-archived video per
        #    project (failed wins anywhere).  Batched so the item and
        #    collection routes never issue a per-project SELECT (P1.1).
        next_action_rows = session.execute(
            select(
                VideoItem.project_id,
                VideoItem.id,
                VideoItem.status,
                VideoItem.position,
            )
            .where(
                VideoItem.project_id.in_(project_ids_in),
                VideoItem.status != ARCHIVED_VIDEO_STATUS,
            )
            .order_by(VideoItem.position, VideoItem.id)
        ).all()
        next_action_videos_by_project: dict[str, list[tuple[str, str]]] = {
            pid: [] for pid in project_ids
        }
        for pid, vid, status, _position in next_action_rows:
            next_action_videos_by_project[pid].append((vid, status))

        # 7. Active-job list — newest at most 10 PER PROJECT — and 8.
        #    active-job count.  Both read the same row set restricted to
        #    the SAME owner predicate so count and membership agree
        #    exactly.  The list query uses a window rank partitioned by
        #    the RESOLVED Project ownership (``_project_of_owner`` result,
        #    computed in the same query) and ordered by
        #    (created_at DESC, id ASC); rows ranked > 10 are filtered by
        #    the outer SELECT so a Project whose jobs are all older than
        #    another page Project's newest 10 STILL receives its own
        #    top-10 (CORRECTION P2-R2.2).  One query serves every Project
        #    of the page — the count stays constant (no N+1).
        active_owner_predicate = or_(
            (Job.owner_type == "project") & (Job.owner_id.in_(project_ids_in)),
            (Job.owner_type == "video_item")
            & (
                Job.owner_id.in_(
                    [vid for ids in video_ids_by_project.values() for vid in ids]
                )
                if any(video_ids_by_project.values())
                else Job.owner_id == "_none_"
            ),
        )
        if project_ids:
            whens = []
            for pid in project_ids:
                whens.append(((Job.owner_type == "project") & (Job.owner_id == pid), pid))
                vids = video_ids_by_project.get(pid, [])
                if vids:
                    whens.append(((Job.owner_type == "video_item") & (Job.owner_id.in_(vids)), pid))
            pid_case = case(*whens, else_=None)
        else:
            pid_case = case((literal(False), Job.owner_id), else_=None)
        rank_window = (
            func.row_number()
            .over(
                partition_by=pid_case,
                order_by=(Job.created_at.desc(), Job.id.asc()),
            )
            .label("owner_rank")
        )
        active_job_inner = (
            select(
                Job.id,
                Job.job_type,
                Job.owner_type,
                Job.owner_id,
                Job.state,
                Job.progress,
                Job.created_at,
                pid_case.label("owner_project_id"),
                rank_window,
            )
            .where(
                Job.workspace_id == workspace_id,
                Job.state.in_(ACTIVE_JOB_STATES),
                active_owner_predicate,
            )
            .subquery()
        )
        active_job_rows = session.execute(
            select(
                active_job_inner.c.id,
                active_job_inner.c.job_type,
                active_job_inner.c.owner_type,
                active_job_inner.c.owner_id,
                active_job_inner.c.state,
                active_job_inner.c.progress,
                active_job_inner.c.created_at,
                active_job_inner.c.owner_project_id,
            )
            .where(active_job_inner.c.owner_rank <= 10)
            .order_by(
                active_job_inner.c.owner_project_id,
                active_job_inner.c.created_at.desc(),
                active_job_inner.c.id.asc(),
            )
        ).all()
        active_jobs_by_project: dict[str, list[ActiveJobRecord]] = {
            pid: [] for pid in project_ids
        }
        for (
            job_id,
            job_type,
            owner_type,
            owner_id,
            state,
            progress,
            created_at,
            owner_project_id,
        ) in active_job_rows:
            if owner_project_id is None:
                continue
            active_jobs_by_project[owner_project_id].append(
                ActiveJobRecord(
                    job_id=job_id,
                    job_type=job_type,
                    owner_type=owner_type,
                    owner_id=owner_id,
                    state=state,
                    progress=progress,
                    created_at=created_at,
                )
            )

        active_job_count_rows = session.execute(
            select(Job.owner_type, Job.owner_id, func.count(Job.id))
            .where(
                Job.workspace_id == workspace_id,
                Job.state.in_(ACTIVE_JOB_STATES),
                active_owner_predicate,
            )
            .group_by(Job.owner_type, Job.owner_id)
        ).all()
        active_count_by_project: dict[str, int] = {pid: 0 for pid in project_ids}
        for owner_type, owner_id, count in active_job_count_rows:
            pid = _project_of_owner(owner_type, owner_id, project_ids, video_ids_by_project)
            if pid is not None:
                active_count_by_project[pid] += int(count)

        # 7. Artifact ownership restricted to this workspace's artifacts.
        artifact_id_rows = session.execute(
            select(ArtifactOwner.owner_type, ArtifactOwner.owner_id, ArtifactOwner.artifact_id)
            .join(Artifact, Artifact.id == ArtifactOwner.artifact_id)
            .where(
                Artifact.workspace_id == workspace_id,
                or_(
                    (ArtifactOwner.owner_type == "project")
                    & (ArtifactOwner.owner_id.in_(project_ids_in)),
                    (ArtifactOwner.owner_type == "video_item")
                    & (
                        ArtifactOwner.owner_id.in_(
                            [vid for ids in video_ids_by_project.values() for vid in ids]
                        )
                        if any(video_ids_by_project.values())
                        else ArtifactOwner.owner_id == "_none_"
                    ),
                ),
            )
        ).all()
        artifact_ids_by_project: dict[str, list[str]] = {pid: [] for pid in project_ids}
        for owner_type, owner_id, artifact_id in artifact_id_rows:
            pid = _project_of_owner(owner_type, owner_id, project_ids, video_ids_by_project)
            if pid is not None and artifact_id not in artifact_ids_by_project[pid]:
                artifact_ids_by_project[pid].append(artifact_id)
        all_artifact_ids = list(
            dict.fromkeys(aid for ids in artifact_ids_by_project.values() for aid in ids)
        )
        artifact_state_size = self._artifact_state_size(workspace_id, all_artifact_ids)
        storage_by_project = {
            pid: self._storage_from_rows(
                artifact_state_size, artifact_ids_by_project[pid]
            )
            for pid in project_ids
        }

        # 8. Channel display references (archived channels remain visible;
        #    workspace predicate prevents cross-workspace disclosure — P2.8).
        channel_ids = list(
            dict.fromkeys(
                pid
                for p in projects
                for pid in (p.source_channel_id, p.production_channel_id)
                if pid is not None
            )
        )
        channel_display = self._channel_displays(workspace_id, channel_ids)

        # ── Assemble records (pure mapping; no queries) ────────────────────
        records: dict[str, ProjectSummaryRecord] = {}
        for project in projects:
            pid = project.id
            counts = video_counts[pid]
            next_action, video_item_id, enabled, blocker = _next_action_from_videos(
                project=project,
                video_counts=counts,
                videos=next_action_videos_by_project[pid],
            )
            # Authoritative activity (P1.2/P1.5): max of project.updated_at,
            # newest video updated_at, and every owned Job's activity.
            activity_candidates: list[datetime | None] = [project.updated_at]
            if pid in max_video_by_project:
                activity_candidates.append(max_video_by_project[pid])
            job_activity_owner = job_activity_by_owner.get(("project", pid))
            if job_activity_owner is not None:
                activity_candidates.append(job_activity_owner)
            for vid in video_ids_by_project[pid]:
                ja = job_activity_by_owner.get(("video_item", vid))
                if ja is not None:
                    activity_candidates.append(ja)
            valid = [c for c in activity_candidates if c is not None]
            last_activity_at = max(valid) if valid else None

            records[pid] = ProjectSummaryRecord(
                project_id=pid,
                workspace_id=workspace_id,
                name=project.name,
                description=project.description or "",
                status=project.status,
                revision=project.revision,
                created_at=project.created_at,
                updated_at=project.updated_at,
                archived_at=project.archived_at,
                source_channel=(
                    channel_display.get(project.source_channel_id)
                    if project.source_channel_id
                    else None
                ),
                production_channel=(
                    channel_display.get(project.production_channel_id)
                    if project.production_channel_id
                    else None
                ),
                video_counts=counts,
                next_action=next_action,
                next_action_video_item_id=video_item_id,
                next_action_enabled=enabled,
                next_action_blocker=blocker,
                active_jobs=active_jobs_by_project[pid],
                active_job_count=active_count_by_project[pid],
                last_activity_at=last_activity_at,
                storage=storage_by_project[pid],
            )
        return records

    def _artifact_state_size(
        self, workspace_id: str, artifact_ids: list[str]
    ) -> dict[str, tuple[str, int | None]]:
        """One batch read: artifact_id -> (state, size_bytes) for the page."""
        if not artifact_ids:
            return {}
        rows = self._session.execute(
            select(Artifact.id, Artifact.state, Artifact.size_bytes).where(
                Artifact.workspace_id == workspace_id,
                Artifact.id.in_(artifact_ids),
            )
        ).all()
        return {artifact_id: (state, size) for artifact_id, state, size in rows}

    def _storage_from_rows(
        self,
        artifact_state_size: dict[str, tuple[str, int | None]],
        artifact_ids: list[str],
    ) -> StorageRecord:
        """Pure aggregation of already-fetched artifact rows (no queries).

        ``unknown_size_count`` counts EVERY deduplicated artifact whose
        ``size_bytes`` is NULL, regardless of state (CORRECTION P2.6).
        """
        total_bytes = 0
        ready_count = 0
        missing_count = 0
        trash_count = 0
        unknown_size_count = 0
        for artifact_id in dict.fromkeys(artifact_ids):
            state, size = artifact_state_size[artifact_id]
            if size is None:
                # CORRECTION P2.6: every deduplicated artifact with a NULL
                # size is unknown REGARDLESS of its state.
                unknown_size_count += 1
            if state == "ready":
                ready_count += 1
                if size is not None:
                    total_bytes += int(size)
            elif state == "missing":
                missing_count += 1
            elif state == "trash":
                trash_count += 1
        return StorageRecord(
            total_bytes=total_bytes,
            artifact_count=len(dict.fromkeys(artifact_ids)),
            ready_count=ready_count,
            missing_count=missing_count,
            trash_count=trash_count,
            unknown_size_count=unknown_size_count,
        )

    def _channel_displays(
        self, workspace_id: str, channel_ids: list[str]
    ) -> dict[str, ChannelDisplayRecord]:
        """One batch read of Channel display refs within *workspace_id*.

        The workspace predicate is IN the WHERE clause (CORRECTION P2.8):
        a malformed/imported cross-workspace reference resolves to an
        empty display record — the other workspace's metadata is never
        disclosed.
        """
        if not channel_ids:
            return {}
        rows = self._session.execute(
            select(Channel.id, Channel.name, Channel.role, Channel.status).where(
                Channel.workspace_id == workspace_id,
                Channel.id.in_(channel_ids),
            )
        ).all()
        found = {
            channel_id: ChannelDisplayRecord(
                channel_id=channel_id,
                name=name,
                role=role,
                status=status,
            )
            for channel_id, name, role, status in rows
        }
        for channel_id in dict.fromkeys(channel_ids):
            if channel_id not in found:
                found[channel_id] = ChannelDisplayRecord(
                    channel_id=channel_id,
                    name="",
                    role="",
                    status="",
                )
        return found

def _next_action_from_videos(
    *,
    project: Project,
    video_counts: VideoCountsRecord,
    videos: list[tuple[str, str]],
) -> tuple[str, str | None, bool, str | None]:
    """Pick the first non-archived video deterministically and map it.

    *videos* is the batched list of ``(video_id, status)`` for the
    project, ordered by ``(position, id)`` (already fetched by the
    composer — no query here, P1.1).  A ``failed`` video anywhere is
    retried before any other action; otherwise the first video wins.
    Archived Projects and projects with no non-archived videos map to
    ``none``.
    """
    if project.status == "archived" or video_counts.active == 0:
        return (NEXT_ACTION_NONE, None, False, None)
    target = next((video for video in videos if video[1] == "failed"), None)
    if target is None and videos:
        target = videos[0]
    if target is None:
        return (NEXT_ACTION_NONE, None, False, None)
    return determine_next_action(
        project_status=project.status,
        video_status=target[1],
        video_id=target[0],
    )


def _greatest_expr(*exprs: Any) -> Any:
    """SQLite-safe ``greatest``: a nested CASE expression.

    SQLite has no ``greatest()`` function; ``func.max(a, b)`` compiles to
    the scalar ``max()`` which behaves differently inside aggregates, so
    the maximum of N expressions is expressed as a nested CASE chain:
    ``CASE WHEN a >= b THEN a ELSE b END``.
    """
    if len(exprs) == 1:
        return exprs[0]
    left = exprs[0]
    right = _greatest_expr(*exprs[1:])
    return case((left >= right, left), else_=right)


def _activity_expr() -> Any:
    """SQL expression for the authoritative global activity key.

    ``greatest(project.updated_at, max(video.updated_at), max(job
    activity))`` per project — computed BEFORE LIMIT/OFFSET so the page
    boundary is globally ordered by real activity (CORRECTION P1.2).  The
    implementation uses correlated subqueries that reuse the durable
    indexes (project id, video project_id, job owner) and stay cheap for
    the workspace.
    """
    video_activity = (
        select(func.max(VideoItem.updated_at))
        .where(VideoItem.project_id == Project.id)
        .scalar_subquery()
    )
    job_activity = (
        select(
            _greatest_expr(
                func.max(Job.updated_at), func.max(Job.created_at)
            )
        )
        .where(
            Job.workspace_id == Project.workspace_id,
            Job.owner_type == "project",
            Job.owner_id == Project.id,
        )
        .scalar_subquery()
    )
    job_video_activity = (
        select(
            _greatest_expr(
                func.max(Job.updated_at), func.max(Job.created_at)
            )
        )
        .where(
            Job.workspace_id == Project.workspace_id,
            Job.owner_type == "video_item",
            Job.owner_id.in_(
                select(VideoItem.id).where(VideoItem.project_id == Project.id)
            ),
        )
        .scalar_subquery()
    )
    return _greatest_expr(
        Project.updated_at,
        func.coalesce(video_activity, Project.updated_at),
        func.coalesce(job_activity, Project.updated_at),
        func.coalesce(job_video_activity, Project.updated_at),
    )


def _project_of_owner(
    owner_type: str,
    owner_id: str,
    project_ids: list[str],
    video_ids_by_project: dict[str, list[str]],
) -> str | None:
    """Map an owner row back to its page Project (pure dict lookup).

    Project owners match directly; video_item owners match against the
    real Video id sets of the page.  An orphan/cross-workspace owner that
    cannot be mapped is skipped (AC5).
    """
    if owner_type == "project":
        return owner_id if owner_id in project_ids else None
    if owner_type == "video_item":
        for pid, vids in video_ids_by_project.items():
            if owner_id in vids:
                return pid
    return None


def _activity_key(value: datetime | None) -> tuple[int, int]:
    """Deterministic sort key: None (no activity) sorts last, otherwise
    the microsecond-resolution UTC timestamp sorts descending."""
    if value is None:
        return (0, 0)
    return (1, int(value.timestamp() * 1_000_000))
