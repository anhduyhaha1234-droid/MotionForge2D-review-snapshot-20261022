"""MotionForge 2D entry point.

Run with: uvicorn app.main:app --reload

The FastAPI lifespan (app/api/app.py) performs the explicit application
lifecycle: bootstrap/upgrade the database, reconcile stale in-flight Jobs,
start the durable worker, and on shutdown stop/join worker + reconciler.
Importing this module never starts threads, opens sessions, or touches
files (AC1 — no import-time side effects).
"""

from __future__ import annotations

import cv2

cv2.setNumThreads(8)

from app.api.app import app  # noqa: E402, F401

__all__ = ["app"]
