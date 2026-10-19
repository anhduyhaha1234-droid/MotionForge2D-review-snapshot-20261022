"""FastAPI application — MotionForge 2D API server.

Lifecycle (S02-T05 AC1): the app initializes/upgrades the durable database
through the approved bootstrap path (with the S01 pre-upgrade backup
policy), reconciles stale in-flight Jobs before the worker polls, starts
the durable worker, and on shutdown stops and joins worker + reconciler.
All of it is explicit lifespan wiring — importing this module (or
``app.main``) starts nothing, opens no sessions, creates no files.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import deps
from app.api.routes import (
    channels,
    durable_characters,
    durable_projects,
    durable_summaries,
    durable_videos,
    frames,
    jobs,
    projects,
)
from app.lifecycle import Lifecycle, default_database_path
from app.persistence import create_engine_for_path, create_session_factory

log = logging.getLogger("motionforge.lifecycle")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Explicit application lifecycle (AC1).

    Startup:
      1. bootstrap/upgrade the explicit database (approved path + S01
         pre-upgrade backup policy),
      2. reconcile stale in-flight Jobs (S02-T04) BEFORE worker polling,
      3. start the durable worker poll loop.
    Shutdown: stop/join the worker poll loop (the reconciler runs in the
    same thread as its caller; there is no separate reconciler thread to
    join — :meth:`Lifecycle.stop` stops the worker).
    """
    job_service = deps.get_job_service()
    session_factory = getattr(job_service, "_session_factory", None)
    if session_factory is None:
        session_factory = create_session_factory(
            create_engine_for_path(default_database_path())
        )
    # Tests inject a patched database path on deps (never the production DB).
    injected = getattr(deps, "_lifecycle_db", None)
    if injected is not None:
        session_factory = create_session_factory(create_engine_for_path(injected))
    lifecycle = Lifecycle(job_service, session_factory)
    lifecycle.initialize()
    lifecycle.start()
    app.state.lifecycle = lifecycle
    try:
        yield
    finally:
        lifecycle.stop()


app = FastAPI(
    title="MotionForge 2D API",
    version="0.2.0",
    description="Local-first 2D animation motion extraction and replacement",
    redirect_slashes=False,
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(projects.router)
app.include_router(jobs.router)
app.include_router(frames.router)
app.include_router(channels.router)
# Durable Project API (S03-T02) — isolated under /api/v2/projects, never
# shadows the legacy /api/projects router (AC7 namespace isolation).
app.include_router(durable_projects.router)
# Durable Video Item API (S03-T03) — nested under the UUID-constrained
# /api/v2/projects/{project_id:uuid}/videos namespace, disjoint from every
# legacy route (AC1/AC9 namespace isolation).
app.include_router(durable_videos.router)
# Durable Project summary read model (S03-T04) — read-only collection and
# item routes under the isolated /api/v2/projects namespace.
app.include_router(durable_summaries.router)
# Durable Character Library API (S06-T01) — /api/v2/characters namespace,
# disjoint from every legacy route (AC1/AC9 namespace isolation).
app.include_router(durable_characters.router)


@app.get("/health")
@app.get("/api/v1/health")
@app.head("/health")
@app.head("/api/v1/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "motionforge-2d"}
