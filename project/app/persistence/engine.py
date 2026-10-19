"""Engine and session factory bootstrap for the MotionForge SQLite database.

All engine/session construction in MotionForge goes through this module so
every SQLite connection is configured uniformly:

- foreign keys are enabled (the domain contract requires them on every
  connection), and
- writes use a bounded busy timeout instead of failing immediately when the
  database is briefly locked by another process.

Nothing here creates a database or touches any path at import time.  An
explicit call to :func:`create_engine_for_path` is the only way to create an
engine, and schema creation/upgrade is an explicit Alembic operation
(``alembic upgrade head``), never a module-import or request side effect.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

__all__ = [
    "BUSY_TIMEOUT_MS",
    "FOREIGN_KEYS_PRAGMA",
    "create_engine_for_path",
    "create_session_factory",
]

#: Bounded busy timeout for SQLite write transactions (milliseconds).
BUSY_TIMEOUT_MS = 5000

#: SQLite PRAGMA executed on every new connection.
FOREIGN_KEYS_PRAGMA = "PRAGMA foreign_keys=ON"

_ENGINE_OPTIONS: dict[str, Any] = {
    "connect_args": {
        "timeout": BUSY_TIMEOUT_MS / 1000.0,
        "check_same_thread": False,
    },
    "pool_pre_ping": True,
}


def create_engine_for_path(database_path: str | Path) -> Engine:
    """Create a configured SQLite engine for an explicit database path.

    The path may be a filesystem path (e.g. ``"data/motionforge.db"``) or the
    SQLAlchemy URL string ``"sqlite:///..."``.  Nothing is created on disk
    until a connection is opened.

    Args:
        database_path: Explicit database location.  Relative paths are
            resolved against the current working directory.

    Returns:
        A configured SQLAlchemy :class:`~sqlalchemy.Engine`.
    """
    if isinstance(database_path, Path):
        database_path = str(database_path)
    database_path = database_path.replace("\\", "/")
    if not database_path.startswith("sqlite"):
        database_path = f"sqlite:///{database_path}"
    engine = create_engine(database_path, **_ENGINE_OPTIONS)
    _enable_foreign_keys(engine)
    return engine


def _enable_foreign_keys(engine: Engine) -> None:
    """Enable SQLite foreign keys on every new connection.

    SQLite disables FK enforcement by default per connection; the domain
    contract requires it on every connection, so we install a connection
    event listener.
    """

    @event.listens_for(engine, "connect")
    def _set_fk_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute(FOREIGN_KEYS_PRAGMA)
        cursor.close()


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a configured session factory bound to *engine*."""
    return sessionmaker(bind=engine, expire_on_commit=False)
