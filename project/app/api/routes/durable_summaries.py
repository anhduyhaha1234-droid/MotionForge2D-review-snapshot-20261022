"""Durable Project summary read model API (S03-T04).

Read-only routes under the isolated v2 namespace:

- ``GET /api/v2/projects/summaries`` — collection (active by default,
  optional exact ``status`` filter, bounded ``limit``/``offset``,
  deterministic ordering by ``last_activity_at DESC`` then project id).
- ``GET /api/v2/projects/{project_id:uuid}/summary`` — one Project
  summary (archived Projects readable, AC8).

Both routes share one algorithm: :class:`SummaryRepository` derives every
value live from durable rows in ONE consistent read boundary and returns
plain frozen dataclasses; the routes map them to Pydantic DTOs so no ORM
object ever crosses the API boundary (AC2).  No aggregate is persisted,
no file/JSON is written, and no legacy ``/api/projects`` route is touched
(AC10).

Error semantics are stable: a Project that does not exist — or exists in
another workspace — is a plain 404; an invalid ``status`` filter is a 422
(FastAPI enum validation); an invalid ``limit``/``offset`` is a 422
(FastAPI query validation).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import SummaryRepositoryDep
from app.persistence import (
    DEFAULT_WORKSPACE_ID,
    ProjectSummaryNotFoundError,
    ProjectSummaryRecord,
)
from app.schemas import (
    ProjectStatus,
    ProjectSummaryData,
    ProjectSummaryListResponse,
)

router = APIRouter(prefix="/api/v2/projects", tags=["durable-summaries"])

#: The local install owns exactly one workspace (contract §3).
WORKSPACE_ID = DEFAULT_WORKSPACE_ID

#: Hard bound for one collection page (AC9: query count bounded
#: independently of the number of Projects).
SUMMARY_PAGE_LIMIT_MAX = 200


def _to_dto(record: ProjectSummaryRecord) -> ProjectSummaryData:
    """DTO boundary: repository read record -> Pydantic response (AC2)."""
    return ProjectSummaryData.from_record(record)


@router.get("/summaries")
@router.get("/summaries/")
def list_summaries(
    service: SummaryRepositoryDep,
    workspace_id: str = WORKSPACE_ID,
    status: ProjectStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=SUMMARY_PAGE_LIMIT_MAX)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectSummaryListResponse:
    """List Project summaries for the workspace (AC1/AC3/AC7).

    The collection defaults to active Projects (``status`` omitted) and
    supports exact project-status filtering.  Ordering is deterministic:
    ``last_activity_at DESC`` then project id ascending.  The page is
    bounded by ``limit``/``offset``; the repository already caps the
    underlying query so the count never scales with the total number of
    Projects.
    """
    records, total_count = service.list_summaries(
        workspace_id,
        status=status.value if status is not None else None,
        limit=limit,
        offset=offset,
    )
    # Honest pagination (CORRECTION P2.7): ``total`` is the exact filtered
    # count; ``has_more`` is True only when more rows exist AFTER this page
    # (offset + len(page) < total), so an exactly-full final page reports
    # has_more=False.
    has_more = offset + len(records) < total_count
    return ProjectSummaryListResponse(
        workspace_id=workspace_id,
        active_only=status is None,
        status=status.value if status is not None else None,
        limit=limit,
        offset=offset,
        total=total_count,
        has_more=has_more,
        summaries=[_to_dto(record) for record in records],
    )


@router.get("/{project_id:uuid}/summary")
@router.get("/{project_id:uuid}/summary/")
def get_project_summary(
    project_id: uuid.UUID,
    service: SummaryRepositoryDep,
    workspace_id: str = WORKSPACE_ID,
) -> ProjectSummaryData:
    """Read one Project summary within the workspace (AC1/AC8).

    Archived Projects remain readable.  A project id from another
    workspace is a 404 — the repository filters by ``workspace_id`` in
    the same query, so cross-workspace reads are impossible by
    construction (AC6).
    """
    try:
        record = service.summarize_one(str(project_id), workspace_id)
    except ProjectSummaryNotFoundError as err:
        raise HTTPException(404, str(err)) from err
    return _to_dto(record)
