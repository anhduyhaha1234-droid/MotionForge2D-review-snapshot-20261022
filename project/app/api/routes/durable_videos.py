"""Durable Video Item lifecycle/order API (S03-T03).

Endpoints operate under the explicit transition namespace
``/api/v2/projects/{project_id:uuid}/videos``.  They write SQLite only
(no JSON dual-write, no filesystem/media writes, no legacy route
changes).  Responses are Pydantic DTOs (AC2/AC6).

**Namespace isolation (AC1/AC9):** every durable route lives under the
UUID-constrained v2 project path; the legacy ``/api/projects`` router is
untouched and keeps serving the current filesystem workflows.  There is
**no DELETE route** — ``POST .../videos/{video_id:uuid}/archive`` is the
only removal path (AC5).  Source artifact/probe metadata are read-only
in this task (S05 owns import and media probing).

Conflict semantics are stable and actionable:

- ``404`` unknown project/video (or cross-workspace/cross-project id),
- ``409`` stale revision (optimistic concurrency) — PATCH, archive,
  reorder — or a mutation against an archived Project (new Video
  Items, reorder, active workflow PATCH are rejected until a restore
  policy exists),
- ``422`` invalid payload (FastAPI validation) or invalid source
  channel reference (missing / cross-workspace / wrong role / not
  active), or a reorder id-set contract violation.

Archived Projects remain readable (list/read) but reject new Video
Items, reorder, and active workflow mutation until a restore policy
exists.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import get_video_service
from app.persistence import (
    DEFAULT_WORKSPACE_ID,
    ReorderValidationError,
    VideoChannelReferenceError,
    VideoConflictError,
    VideoItemRecord,
    VideoItemService,
    VideoNotFoundError,
)
from app.schemas import (
    VideoItemArchiveRequest,
    VideoItemCreate,
    VideoItemData,
    VideoItemReorderRequest,
    VideoItemStatus,
    VideoItemUpdate,
    VideoListResponse,
)

router = APIRouter(
    prefix="/api/v2/projects/{project_id:uuid}/videos",
    tags=["durable-videos"],
)

#: The local install owns exactly one workspace (contract §3).
WORKSPACE_ID = DEFAULT_WORKSPACE_ID


def _service() -> VideoItemService:
    return get_video_service()


def _to_dto(record: VideoItemRecord) -> VideoItemData:
    """DTO boundary: repository record -> Pydantic response (AC6)."""
    return VideoItemData.from_row(record)


def _not_found(message: str) -> HTTPException:
    return HTTPException(404, message)


@router.get("")
@router.get("/")
def list_videos(
    project_id: uuid.UUID,
    workspace_id: str = WORKSPACE_ID,
    status: VideoItemStatus | None = None,
    active_only: bool = True,
) -> VideoListResponse:
    """List Video Items for a project (archived excluded by default).

    Ordered by position (AC3).  Archived Projects remain readable (AC5).
    A project id from another workspace is a 404.
    """
    try:
        records = _service().list_videos(
            str(project_id),
            workspace_id,
            status=status.value if status is not None else None,
            active_only=active_only,
        )
    except VideoNotFoundError as err:
        raise _not_found(str(err)) from err
    return VideoListResponse(
        project_id=str(project_id),
        workspace_id=workspace_id,
        active_only=active_only,
        videos=[_to_dto(r) for r in records],
    )


@router.get("/statuses")
def video_statuses() -> dict[str, object]:
    """Expose the exact approved pipeline status set (AC2)."""
    return {"statuses": [s.value for s in VideoItemStatus]}


@router.post("", status_code=201)
@router.post("/", status_code=201)
def create_video(
    project_id: uuid.UUID,
    body: VideoItemCreate,
    workspace_id: str = WORKSPACE_ID,
) -> VideoItemData:
    """Append a Video Item at the end of the Project's list (AC1/AC3).

    The source channel (if any) is validated atomically at the write
    boundary: same workspace, ``source`` role, active at assignment time
    (AC4/atomic writer policy).  Archived Projects reject new Video
    Items (404).
    """
    try:
        record = _service().create(
            project_id=str(project_id),
            workspace_id=workspace_id,
            title=body.title,
            source_channel_id=body.source_channel_id,
            resume_step=body.resume_step,
        )
    except VideoNotFoundError as err:
        raise _not_found(str(err)) from err
    except VideoConflictError as err:
        raise HTTPException(409, str(err)) from err
    except VideoChannelReferenceError as err:
        raise HTTPException(422, str(err)) from err
    return _to_dto(record)


@router.get("/{video_id:uuid}")
def get_video(
    project_id: uuid.UUID,
    video_id: uuid.UUID,
    workspace_id: str = WORKSPACE_ID,
) -> VideoItemData:
    """Read one Video Item within the project (archived readable, AC5).

    A video id from another project is a 404 (never read across project
    boundaries, AC6).
    """
    try:
        record = _service().get(str(video_id), str(project_id), workspace_id)
    except VideoNotFoundError as err:
        raise _not_found(str(err)) from err
    return _to_dto(record)


@router.patch("/{video_id:uuid}")
def update_video(
    project_id: uuid.UUID,
    video_id: uuid.UUID,
    body: VideoItemUpdate,
    workspace_id: str = WORKSPACE_ID,
) -> VideoItemData:
    """Apply one business update guarded by atomic optimistic concurrency.

    A stale ``revision`` returns 409 with the current revision so the
    client can refetch and retry.  Nullable fields follow the patch
    contract: omitted = unchanged, explicit JSON ``null`` = cleared
    (``model_fields_set``).  ``title: null`` / ``status: null`` are 422
    validation errors.  Generic PATCH can never enter or leave
    ``archived`` (422 for ``status: archived``; 409 for updates against
    an archived row — the archive endpoint is the only removal path).
    Source channel references are validated only when the PATCH
    explicitly assigns them (AC4).
    """
    fields = body.model_fields_set
    if "title" in fields and body.title is None:
        raise HTTPException(422, "title must not be null (title is required)")
    if "status" in fields and body.status is None:
        raise HTTPException(422, "status must not be null (status is required)")
    if body.status == VideoItemStatus.ARCHIVED:
        raise HTTPException(
            422,
            "status 'archived' is only accepted by the archive endpoint",
        )

    from app.persistence.videos import UNSET

    def _clear_or_none(field_name: str, *, nullable: bool) -> Any:
        if field_name in fields and getattr(body, field_name) is None:
            return UNSET if nullable else ""
        return getattr(body, field_name) if field_name in fields else None

    try:
        record = _service().update(
            str(video_id),
            str(project_id),
            workspace_id,
            expected_revision=body.revision,
            title=_clear_or_none("title", nullable=False),
            status=_clear_or_none("status", nullable=False),
            source_channel_id=_clear_or_none("source_channel_id", nullable=True),
            resume_step=_clear_or_none("resume_step", nullable=True),
        )
    except VideoNotFoundError as err:
        raise _not_found(str(err)) from err
    except VideoConflictError as err:
        raise HTTPException(409, str(err)) from err
    except VideoChannelReferenceError as err:
        raise HTTPException(422, str(err)) from err
    return _to_dto(record)


@router.post("/{video_id:uuid}/archive")
def archive_video(
    project_id: uuid.UUID,
    video_id: uuid.UUID,
    body: VideoItemArchiveRequest,
    workspace_id: str = WORKSPACE_ID,
) -> VideoItemData:
    """Archive a Video Item with an atomic CAS on the expected revision.

    - Active + matching revision → archived (revision bumped once).
    - Already archived → idempotent no-op returning the current row.
    - Active + stale revision → 409.
    - Unknown / cross-project id → 404.

    Archive preserves all metadata and relationships (no cascade, no
    hard delete — AC5).
    """
    try:
        record = _service().archive(
            str(video_id),
            str(project_id),
            workspace_id,
            expected_revision=body.revision,
        )
    except VideoNotFoundError as err:
        raise _not_found(str(err)) from err
    except VideoConflictError as err:
        raise HTTPException(409, str(err)) from err
    return _to_dto(record)


@router.post("/reorder")
def reorder_videos(
    project_id: uuid.UUID,
    body: VideoItemReorderRequest,
    workspace_id: str = WORKSPACE_ID,
) -> VideoListResponse:
    """Atomically reorder the complete set of active Video Items.

    The request carries the expected Project revision and the COMPLETE
    set of active Video Item ids exactly once, in the desired order.
    Missing/extra/duplicate/cross-project ids fail with 422 BEFORE any
    write (no partial writes).  The Project row is bumped exactly once
    (stale ``project_revision`` → 409); only Video Items whose position
    changes are bumped.  Archived Projects reject reorder (404).
    """
    try:
        records = _service().reorder(
            str(project_id),
            workspace_id,
            expected_project_revision=body.project_revision,
            video_item_ids=body.video_item_ids,
        )
    except VideoNotFoundError as err:
        raise _not_found(str(err)) from err
    except VideoConflictError as err:
        raise HTTPException(409, str(err)) from err
    except ReorderValidationError as err:
        raise HTTPException(422, str(err)) from err
    return VideoListResponse(
        project_id=str(project_id),
        workspace_id=workspace_id,
        active_only=True,
        videos=[_to_dto(r) for r in records],
    )
