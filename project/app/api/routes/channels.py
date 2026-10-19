"""Durable Channel CRUD/archive API (S03-T01).

Endpoints operate on the explicit workspace (``DEFAULT_WORKSPACE_ID`` for
the local install) through the durable ``ChannelService`` (SQLite).  They
never touch ``channels.json`` (the legacy workspace store) and never expose
ORM objects or absolute paths — responses are Pydantic DTOs (AC6).

There is **no hard-delete endpoint**: ``POST .../archive`` (with a required
``revision`` for atomic CAS) is the only removal path (AC1/AC5).  Conflict
semantics are stable and actionable:

- ``404`` unknown channel (or channel from another workspace),
- ``409`` stale revision (optimistic concurrency) or active-name conflict
  within ``(workspace, role)``,
- ``422`` invalid payload (FastAPI validation).

Legacy ``channels.json`` endpoints (``app/api/routes/projects.py``:
``/api/projects/channels``) are untouched for frontend compatibility.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import get_channel_service
from app.persistence import (
    DEFAULT_WORKSPACE_ID,
    ArtifactReferenceError,
    ChannelConflictError,
    ChannelNotFoundError,
    ChannelRecord,
    ChannelService,
    NameConflictError,
)
from app.schemas import (
    ChannelArchiveRequest,
    ChannelCreate,
    ChannelData,
    ChannelListResponse,
    ChannelRole,
    ChannelStatus,
    ChannelUpdate,
)

router = APIRouter(prefix="/api/channels", tags=["channels"])

#: The local install owns exactly one workspace (contract §3).
WORKSPACE_ID = DEFAULT_WORKSPACE_ID

#: Static discovery routes must be declared BEFORE the parameterized
#: ``/{channel_id}`` route or FastAPI captures them as channel ids.
_STATIC_ROUTES_REGISTERED = False


def _register_static_routes() -> None:
    """Declare the role/status discovery endpoints before the id route."""
    global _STATIC_ROUTES_REGISTERED
    if _STATIC_ROUTES_REGISTERED:
        return

    @router.get("/roles")
    def channel_roles() -> dict[str, object]:
        """Expose the exact approved role set (AC2)."""
        return {"roles": [r.value for r in ChannelRole]}

    @router.get("/statuses")
    def channel_statuses() -> dict[str, object]:
        """Expose the exact approved status set (AC2)."""
        return {"statuses": [s.value for s in ChannelStatus]}

    _STATIC_ROUTES_REGISTERED = True


_register_static_routes()


def _service() -> ChannelService:
    return get_channel_service()


def _not_found(channel_id: str) -> HTTPException:
    return HTTPException(404, f"Channel {channel_id!r} not found")


def _to_dto(record: ChannelRecord) -> ChannelData:
    """DTO boundary: repository record -> Pydantic response (AC6)."""
    return ChannelData.from_row(record)


@router.get("")
@router.get("/")
def list_channels(
    workspace_id: str = WORKSPACE_ID,
    role: ChannelRole | None = None,
    active_only: bool = True,
) -> ChannelListResponse:
    """List Channels for the explicit workspace.

    ``active_only`` defaults to True, so archived Channels are excluded by
    default but remain filterable/readable (AC5).
    """
    records = _service().list(
        workspace_id,
        role=role.value if role is not None else None,
        active_only=active_only,
    )
    return ChannelListResponse(
        workspace_id=workspace_id,
        active_only=active_only,
        channels=[_to_dto(r) for r in records],
    )


@router.get("/{channel_id}")
def get_channel(channel_id: str, workspace_id: str = WORKSPACE_ID) -> ChannelData:
    """Read one Channel within the workspace (archived readable, AC5).

    A channel id from another workspace is a 404 (never read across
    workspace boundaries).
    """
    try:
        record = _service().get(channel_id, workspace_id)
    except ChannelNotFoundError as err:
        raise _not_found(channel_id) from err
    return _to_dto(record)


@router.post("", status_code=201)
@router.post("/", status_code=201)
def create_channel(
    body: ChannelCreate,
    workspace_id: str = WORKSPACE_ID,
) -> ChannelData:
    """Create an active Channel (role source|production, AC2).

    The workspace row and the channel row are created in ONE transaction
    (request-bounded, PM review finding 7).
    """
    try:
        record = _service().create(
            workspace_id=workspace_id,
            role=body.role.value,
            name=body.name,
            description=body.description,
            color=body.color,
            avatar_artifact_id=body.avatar_artifact_id,
            target_language=body.target_language,
            default_output_profile=body.default_output_profile,
        )
    except NameConflictError as err:
        raise HTTPException(409, str(err)) from err
    except ArtifactReferenceError as err:
        raise HTTPException(422, str(err)) from err
    return _to_dto(record)


@router.patch("/{channel_id}")
def update_channel(
    channel_id: str, body: ChannelUpdate, workspace_id: str = WORKSPACE_ID
) -> ChannelData:
    """Apply one business update guarded by atomic optimistic concurrency.

    A stale ``revision`` returns 409 with the current revision so the
    client can refetch and retry.  Nullable metadata fields follow the
    patch contract: omitted = unchanged, explicit JSON ``null`` = cleared
    (``model_fields_set``).
    """
    fields = body.model_fields_set
    # Null contract (PM review round 2 finding 3):
    # - name: nullable column? NO — name is required non-null; explicit
    #   JSON null must be a 422 validation error, never a clear.
    # - description: non-null column with default "" — explicit null is
    #   normalized to "" (the required empty string), never bound as NULL.
    # - color / target_language / default_output_profile /
    #   avatar_artifact_id: truly nullable metadata — explicit null clears.
    if "name" in fields and body.name is None:
        raise HTTPException(422, "name must not be null (name is required)")

    from app.persistence.channels import UNSET

    def _clear_or_none(field_name: str, *, nullable: bool) -> Any:
        if field_name in fields and getattr(body, field_name) is None:
            return UNSET if nullable else ""
        return getattr(body, field_name) if field_name in fields else None

    try:
        record = _service().update(
            channel_id,
            workspace_id,
            expected_revision=body.revision,
            name=_clear_or_none("name", nullable=False),
            description=_clear_or_none("description", nullable=False),
            color=_clear_or_none("color", nullable=True),
            avatar_artifact_id=_clear_or_none("avatar_artifact_id", nullable=True),
            target_language=_clear_or_none("target_language", nullable=True),
            default_output_profile=_clear_or_none("default_output_profile", nullable=True),
        )
    except ChannelNotFoundError as err:
        raise _not_found(channel_id) from err
    except ChannelConflictError as err:
        raise HTTPException(409, str(err)) from err
    except NameConflictError as err:
        raise HTTPException(409, str(err)) from err
    except ArtifactReferenceError as err:
        raise HTTPException(422, str(err)) from err
    return _to_dto(record)


@router.post("/{channel_id}/archive")
def archive_channel(
    channel_id: str, body: ChannelArchiveRequest, workspace_id: str = WORKSPACE_ID
) -> ChannelData:
    """Archive a Channel with an atomic CAS on the expected revision.

    - Active + matching revision → archived (revision bumped once).
    - Already archived → idempotent no-op returning the current row.
    - Active + stale revision → 409.
    - Unknown / other-workspace id → 404.
    """
    try:
        record = _service().archive(
            channel_id, workspace_id, expected_revision=body.revision
        )
    except ChannelNotFoundError as err:
        raise _not_found(channel_id) from err
    except ChannelConflictError as err:
        raise HTTPException(409, str(err)) from err
    return _to_dto(record)


def channel_roles() -> dict[str, object]:
    """Expose the exact approved role set (AC2)."""
    return {"roles": [r.value for r in ChannelRole]}


def channel_statuses() -> dict[str, object]:
    """Expose the exact approved status set (AC2)."""
    return {"statuses": [s.value for s in ChannelStatus]}
