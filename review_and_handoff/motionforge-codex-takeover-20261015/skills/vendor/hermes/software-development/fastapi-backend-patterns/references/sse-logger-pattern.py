"""
FastAPI SSE Logger with asyncio.Queue broadcasting.

Pattern: Each SSE client gets its own Queue. add_log() broadcasts to all.
This prevents one slow client from blocking others.

Usage:
    from app.core.logger import add_log, sse_stream
    
    # In startup
    await add_log("Server started", "info")
    
    # In router
    @router.get("/logs/stream")
    async def logs_stream():
        return StreamingResponse(sse_stream(), media_type="text/event-stream")
"""

import asyncio
import json
from datetime import datetime, timezone

# Registered client queues
_queues: list[asyncio.Queue] = []


def add_log_sync(message: str, level: str = "info"):
    """Synchronous log add (for use in non-async contexts like startup)."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    }
    data = json.dumps(log_entry)
    for q in list(_queues):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass  # Drop oldest or skip — don't block


async def add_log(message: str, level: str = "info"):
    """Async log add. Broadcasts to all registered SSE clients."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    }
    data = json.dumps(log_entry)
    for q in list(_queues):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


async def sse_stream():
    """
    Async generator for SSE endpoint.
    Each call creates a new Queue, registers it, and yields messages.
    On disconnect (GeneratorExit), removes the queue.
    """
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _queues.append(q)
    try:
        while True:
            data = await q.get()
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        if q in _queues:
            _queues.remove(q)


# Router integration example:
#
# from fastapi import APIRouter
# from fastapi.responses import StreamingResponse
# from app.core.logger import sse_stream
#
# router = APIRouter()
#
# @router.get("/logs/stream")
# async def logs_stream():
#     return StreamingResponse(
#         sse_stream(),
#         media_type="text/event-stream",
#         headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
#     )
