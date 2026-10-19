"""Runtime schema-revision guard for MotionForge SQLite databases.

The database's Alembic revision is authoritative (see the migration policy in
the persistence domain contract).  If a database was created by a NEWER
application version, its revision id will be unknown to this application's
migration scripts.  Starting up against such a database is refused with an
actionable error instead of risking incompatible reads/writes.
"""

from __future__ import annotations

from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text

__all__ = [
    "SCHEMA_REVISION_REFUSED_MESSAGE",
    "assert_schema_revision_supported",
    "database_schema_revision",
    "max_supported_schema_revision",
]

SCHEMA_REVISION_REFUSED_MESSAGE = (
    "Database schema revision '{revision}' (database: {database_path}) is newer "
    "than the maximum revision this application supports ('{supported}'). "
    "Refusing to start: the database was created by a newer MotionForge "
    "version. Use that newer version to read/write this database, or restore a "
    "backup at a supported revision."
)


def max_supported_schema_revision(script_location: str | Path) -> str | None:
    """Return the head revision of the bundled Alembic migration scripts."""
    script = ScriptDirectory(str(script_location))
    return script.get_current_head()


def database_schema_revision(engine: Engine) -> str | None:
    """Return the revision the database claims in ``alembic_version``."""
    inspector = __import__("sqlalchemy").inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        return None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
    return row[0] if row else None


def assert_schema_revision_supported(
    engine: Engine,
    script_location: str | Path,
    database_path: str | Path = "",
) -> None:
    """Raise if *engine*'s database is at a revision newer than supported.

    A database with no ``alembic_version`` table is treated as uninitialized
    and allowed through (explicit bootstrap paths decide whether to create
    it).  A revision that exists in the bundled scripts (same or older) is
    supported; an unknown revision is refused.
    """
    supported = max_supported_schema_revision(script_location)
    revision = database_schema_revision(engine)
    if revision is None:
        return
    if revision in _known_revisions(script_location):
        return
    raise RuntimeError(
        SCHEMA_REVISION_REFUSED_MESSAGE.format(
            revision=revision,
            database_path=database_path or str(engine.url),
            supported=supported,
        )
    )


def _known_revisions(script_location: str | Path) -> set[str]:
    script = ScriptDirectory(str(script_location))
    return {r.revision for r in script.walk_revisions()}
