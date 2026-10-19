"""Alembic environment configuration (SQLite, explicit target_metadata)."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Engine

from app.persistence.engine import create_engine_for_path
from app.persistence.models import Base

# this is the Alembic Config object, which provides access to the values within
# the .ini file in use.
config = context.config

# Interpret the config file for Python logging; this line sets up loggers
# basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def _database_url() -> str:
    """Resolve the SQLite URL for this migration run.

    Order of precedence:
    1. ``sqlalchemy.url`` explicitly configured on the command line
       (``alembic -x db_url=... upgrade head``),
    2. the ``MOTIONFORGE_DATABASE_URL`` environment variable,
    3. ``sqlalchemy.url`` from alembic.ini (explicit bootstrap path).

    This keeps migrations explicit: nothing is created or upgraded unless an
    explicit bootstrap operation (or a test) points at a concrete database.
    """
    x_args = getattr(config, "cmd_opts", None)
    if x_args is not None:
        x_values = getattr(x_args, "x", None) or ()
        for x in x_values:
            if x.startswith("db_url="):
                return x.split("=", 1)[1]
    env_url = os.environ.get("MOTIONFORGE_DATABASE_URL")
    if env_url:
        return env_url
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError(
            "No database URL configured. Pass -x db_url=<sqlite url> or set "
            "MOTIONFORGE_DATABASE_URL, or configure sqlalchemy.url in alembic.ini."
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DB connection)."""
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the database directly).

    Uses the shared engine factory so the online connection has the same
    configuration as application connections — most importantly
    ``PRAGMA foreign_keys=ON`` on every SQLite connection, which the domain
    contract requires.  The database target remains explicit (see
    :func:`_database_url`); no default production database is implied.
    """
    url = _database_url()
    engine: Engine = create_engine_for_path(url)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
