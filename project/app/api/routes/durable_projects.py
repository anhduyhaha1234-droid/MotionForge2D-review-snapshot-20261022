"""Durable Project CRUD/archive API (S03-T02).

Endpoints operate on the explicit workspace (``DEFAULT_WORKSPACE_ID`` for
the local install) through the durable ``ProjectService`` (SQLite).  They
never create a project directory or ``project.json`` and never touch the
legacy filesystem project store — no JSON dual-write (AC1).  Responses
are Pydantic DTOs (AC2/AC6).

**Namespace isolation (AC7):** all durable routes live under the explicit
transition namespace ``/api/v2/projects`` (base list/create, ``/statuses``
discovery and ``/{project_id:uuid}`` item paths).  Every existing
``/api/projects`` route — base, literal and nested legacy routes — is
untouched and keeps serving the current filesystem workflows.  The UUID
constraint guarantees the v2 item paths never capture literal legacy
paths, and the durable endpoints never invoke legacy filesystem services.

There is **no hard-delete endpoint**: ``POST .../archive`` (with a
required ``revision`` for atomic CAS) is the only removal path
(AC1/AC5).  Conflict semantics are stable and actionable:

- ``404`` unknown project (or project from another workspace),
- ``409`` stale revision (optimistic concurrency),
- ``422`` invalid payload (FastAPI validation) or invalid channel
  reference (missing / cross-workspace / wrong role / not active).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import get_project_service
from app.persistence import (
    DEFAULT_WORKSPACE_ID,
    ChannelReferenceError,
    ProjectConflictError,
    ProjectNotFoundError,
    ProjectRecord,
    ProjectService,
)
from app.schemas import (
    DurableProjectData,
    ProjectArchiveRequest,
    ProjectCreate,
    ProjectListResponse,
    ProjectStatus,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/v2/projects", tags=["durable-projects"])

#: The local install owns exactly one workspace (contract §3).
WORKSPACE_ID = DEFAULT_WORKSPACE_ID


def _service() -> ProjectService:
    return get_project_service()


def _not_found(project_id: str) -> HTTPException:
    return HTTPException(404, f"Project {project_id!r} not found")


def _to_dto(record: ProjectRecord) -> DurableProjectData:
    """DTO boundary: repository record -> Pydantic response (AC6)."""
    return DurableProjectData.from_row(record)


@router.get("")
@router.get("/")
def list_projects(
    workspace_id: str = WORKSPACE_ID,
    status: ProjectStatus | None = None,
    active_only: bool = True,
) -> ProjectListResponse:
    """List Projects for the explicit workspace.

    ``active_only`` defaults to True, so archived Projects are excluded by
    default but remain filterable/readable (AC5).  An explicit ``status``
    filter overrides ``active_only``.
    """
    records = _service().list(
        workspace_id,
        status=status.value if status is not None else None,
        active_only=active_only,
    )
    return ProjectListResponse(
        workspace_id=workspace_id,
        active_only=active_only,
        projects=[_to_dto(r) for r in records],
    )


@router.get("/statuses")
def project_statuses() -> dict[str, object]:
    """Expose the exact approved status set (AC2)."""
    return {"statuses": [s.value for s in ProjectStatus]}


@router.post("", status_code=201)
@router.post("/", status_code=201)
def create_project(
    body: ProjectCreate,
    workspace_id: str = WORKSPACE_ID,
) -> DurableProjectData:
    """Create a durable Project (SQLite only, AC1/AC2).

    The workspace row and the project row are created in ONE transaction
    (request-bounded).  Channel references are validated atomically
    (same workspace, correct role, active — AC3).
    """
    try:
        record = _service().create(
            workspace_id=workspace_id,
            name=body.name,
            description=body.description,
            source_channel_id=body.source_channel_id,
            production_channel_id=body.production_channel_id,
            default_output_profile=body.default_output_profile,
            resume_step=body.resume_step,
        )
    except ChannelReferenceError as err:
        raise HTTPException(422, str(err)) from err
    return _to_dto(record)


@router.get("/{project_id:uuid}")
def get_project(
    project_id: uuid.UUID, workspace_id: str = WORKSPACE_ID
) -> DurableProjectData:
    """Read one Project within the workspace (archived readable, AC5).

    A project id from another workspace is a 404 (never read across
    workspace boundaries, AC6).
    """
    try:
        record = _service().get(str(project_id), workspace_id)
    except ProjectNotFoundError as err:
        raise _not_found(str(project_id)) from err
    return _to_dto(record)


@router.patch("/{project_id:uuid}")
def update_project(
    project_id: uuid.UUID, body: ProjectUpdate, workspace_id: str = WORKSPACE_ID
) -> DurableProjectData:
    """Apply one business update guarded by atomic optimistic concurrency.

    A stale ``revision`` returns 409 with the current revision so the
    client can refetch and retry.  Nullable fields follow the patch
    contract: omitted = unchanged, explicit JSON ``null`` = cleared
    (``model_fields_set``).  ``name: null`` / ``status: null`` are 422
    validation errors.  Channel references are validated only when the
    PATCH explicitly assigns them (AC3).
    """
    fields = body.model_fields_set
    if "name" in fields and body.name is None:
        raise HTTPException(422, "name must not be null (name is required)")
    if "status" in fields and body.status is None:
        raise HTTPException(422, "status must not be null (status is required)")
    if body.status == ProjectStatus.ARCHIVED:
        raise HTTPException(
            422,
            "status 'archived' is only accepted by the archive endpoint",
        )

    from app.persistence.projects import UNSET

    def _clear_or_none(field_name: str, *, nullable: bool) -> Any:
        if field_name in fields and getattr(body, field_name) is None:
            return UNSET if nullable else ""
        return getattr(body, field_name) if field_name in fields else None

    try:
        record = _service().update(
            str(project_id),
            workspace_id,
            expected_revision=body.revision,
            name=_clear_or_none("name", nullable=False),
            description=_clear_or_none("description", nullable=False),
            status=_clear_or_none("status", nullable=False),
            source_channel_id=_clear_or_none("source_channel_id", nullable=True),
            production_channel_id=_clear_or_none(
                "production_channel_id", nullable=True
            ),
            default_output_profile=_clear_or_none(
                "default_output_profile", nullable=True
            ),
            resume_step=_clear_or_none("resume_step", nullable=True),
        )
    except ProjectNotFoundError as err:
        raise _not_found(str(project_id)) from err
    except ProjectConflictError as err:
        raise HTTPException(409, str(err)) from err
    except ChannelReferenceError as err:
        raise HTTPException(422, str(err)) from err
    return _to_dto(record)


@router.post("/{project_id:uuid}/archive")
def archive_project(
    project_id: uuid.UUID,
    body: ProjectArchiveRequest,
    workspace_id: str = WORKSPACE_ID,
) -> DurableProjectData:
    """Archive a Project with an atomic CAS on the expected revision.

    - Active + matching revision → archived (revision bumped once).
    - Already archived → idempotent no-op returning the current row.
    - Active + stale revision → 409.
    - Unknown / other-workspace id → 404.

    Archive preserves timestamps, channel references and future child
    relationships (no cascade, no hard delete — AC5).
    """
    try:
        record = _service().archive(
            str(project_id), workspace_id, expected_revision=body.revision
        )
    except ProjectNotFoundError as err:
        raise _not_found(str(project_id)) from err
    except ProjectConflictError as err:
        raise HTTPException(409, str(err)) from err
    return _to_dto(record)
