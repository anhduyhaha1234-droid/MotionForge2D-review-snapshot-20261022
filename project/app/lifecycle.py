"""Explicit application lifecycle for the MotionForge backend (S02-T05).

AC1 wiring: the application initializes/upgrades the database **only**
through the approved bootstrap path (Alembic upgrade on an explicit
database target, guarded by the schema-revision check), reconciles stale
in-flight Jobs **before** the worker starts polling, and shutdown stops and
joins worker + reconciler.  Nothing here runs at import time — every
function must be called explicitly by the process entry point
(``app.main`` lifespan) or by tests.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.workflow.job_reconciler import JobReconciler, ReconcileConfig
from app.workflow.job_service import JobService

__all__ = [
    "Lifecycle",
    "default_database_path",
]

log = logging.getLogger("motionforge.lifecycle")


def default_database_path(project_root: str | Path | None = None) -> Path:
    """The production database path under the configured project root."""
    if project_root is None:
        try:
            from app.api import deps  # noqa: PLC0415

            project_root = Path(deps._config.project_root)
        except Exception:
            from app.config import config as _cfg  # noqa: PLC0415

            project_root = Path(_cfg.project_root)
    return Path(project_root) / "data" / "motionforge.db"


class Lifecycle:
    """Bounded lifecycle controller binding one JobService + reconciler.

    Usage (entry point)::

        lifecycle = Lifecycle(job_service, session_factory)
        lifecycle.initialize()          # explicit bootstrap/upgrade
        lifecycle.start()               # reconcile once, then worker start
        ... serving ...
        lifecycle.stop()                # stop/join worker + reconciler
    """

    def __init__(
        self,
        job_service: JobService,
        session_factory: Callable[[], Session],
        *,
        reconciler: JobReconciler | None = None,
        reconcile_batch_size: int = 50,
        log_reconcile: bool = True,
    ) -> None:
        self._job_service = job_service
        self._session_factory = session_factory
        self._reconciler = reconciler or JobReconciler(
            session_factory,
            config=ReconcileConfig(batch_size=reconcile_batch_size),
        )
        self._log_reconcile = log_reconcile
        self._started = False

    # ── Bootstrap (AC1) ───────────────────────────────────────────────────

    def initialize(self) -> None:
        """Run the approved bootstrap path (idempotent; explicit only).

        Upgrades the explicit database target through Alembic after the
        S01 pre-upgrade backup policy and schema-revision guard.  Never a
        module-import side effect.
        """
        self._job_service.initialize()

    def reconcile_once(self) -> Any:
        """Run one bounded reconciliation pass (S02-T04) and log the report."""
        report = self._reconciler.reconcile_once()
        if self._log_reconcile:
            log.info(
                "startup reconcile: scanned=%d fenced=%d requeued=%d failed=%d "
                "cancelled=%d skipped=%d errors=%d",
                report.scanned,
                report.fenced,
                report.requeued,
                report.failed,
                report.cancelled,
                report.skipped,
                len(report.errors),
            )
        return report

    def start(self) -> None:
        """Start the runtime: reconcile BEFORE the worker polls, then start.

        The reconciler runs synchronously here (bounded pass) so queued and
        running Jobs from a previous process lifetime are fenced/resolved
        before the worker can claim anything (AC5: restart integration).
        """
        if self._started:
            return
        self.reconcile_once()
        self._job_service.start_worker()
        self._started = True

    def stop(self, timeout: float | None = 5.0) -> None:
        """Stop and join the worker poll loop (shutdown, AC1)."""
        self._job_service.stop_worker(timeout=timeout)
        self._started = False

    @property
    def started(self) -> bool:
        return self._started
