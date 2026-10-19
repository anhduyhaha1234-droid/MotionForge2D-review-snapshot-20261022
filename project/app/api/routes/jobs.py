"""Job status and cancel endpoints (S02-T05 durable cutover).

The routes keep the legacy response contract (200/400/404; ``status`` key
renamed from ``state`` by :func:`job_response`) while reading durable rows
through the API job service.  No long operation executes inside these
requests: submit is a durable insert, poll is a read, cancel is a guarded
state transition (AC3/AC4/AC6).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_job_service
from app.api.helpers import job_response

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job_status(job_id: str) -> dict[str, object]:
    """Get job status (durable row; fenced state is never exposed)."""
    job_svc = get_job_service()
    info = job_svc.get_job(job_id)
    if info is None:
        raise HTTPException(404, "Job not found")
    return job_response(info)


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str) -> dict[str, object]:
    """Durably request cancellation of a running/queued job.

    Semantics preserved from the legacy service (contract §11.2): 200
    ``{"status": "cancel_requested"}`` when the durable cancel flag was set,
    400 when the Job is terminal, 404 when unknown.  A second cancel while
    ``cancelling`` is an idempotent 200 (contract §6.3).
    """
    job_svc = get_job_service()
    success = job_svc.cancel_job(job_id)
    if not success:
        info = job_svc.get_job(job_id)
        if info is None:
            raise HTTPException(404, "Job not found")
        raise HTTPException(400, f"Cannot cancel job in state: {info.state.value}")
    return {"status": "cancel_requested", "job_id": job_id}
