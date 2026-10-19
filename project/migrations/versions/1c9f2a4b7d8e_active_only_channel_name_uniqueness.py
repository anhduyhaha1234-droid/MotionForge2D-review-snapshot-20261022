"""active-only case-insensitive channel name uniqueness (S03-T01)

PM review round 1 finding 1: the S01 ``channel`` table carried an
unconditional ``UNIQUE(workspace_id, role, name)`` that reserved names of
ARCHIVED channels, rejecting the valid archive-then-recreate workflow the
approved domain contract allows (uniqueness "among active channels",
PERSISTENCE_DOMAIN_CONTRACT.md §4).

This forward migration replaces that constraint with an atomic,
case-insensitive, ACTIVE-ONLY unique index:

- ``lower(name)`` is the index key, so ``My Channel`` / ``my channel``
  collide case-insensitively for the same (workspace, role).
- The partial ``WHERE status = 'active'`` clause makes the index enforce
  uniqueness only among active rows, so an archived channel's name is
  immediately reusable by a new active channel.
- SQLite cannot ALTER constraints, so the migration uses Alembic batch
  mode.  Because other tables (``project``, ``video_item``) hold FK
  references to ``channel.id``, the batch rebuild must run with
  ``PRAGMA foreign_keys=OFF`` for the copy-and-move window (SQLite
  legacy_alter_table semantics): the table is rebuilt, rows are copied
  verbatim, and the swap happens inside one transaction, so all S02 rows
  and their FK references are preserved.  A database that already
  contains an active duplicate (case-variant) cannot exist at S02 because
  the S02 unconditional unique index (NOCASE collation on ``name``)
  already rejected it.

The plain non-unique index ``ix_channel_workspace_role_name`` is kept for
read-path ordering/lookup.

Revision ID: 1c9f2a4b7d8e
Revises: 23b308b1fd0b
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c9f2a4b7d8e"
down_revision: str | None = "23b308b1fd0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rebuild ``channel`` in batch mode: drop the unconditional unique
    constraint, add the active-only partial unique index on ``lower(name)``.

    Foreign keys are disabled for the copy-and-move window so the swap is
    not blocked by referencing rows; row identity and references are
    preserved (verified by the S02→head upgrade tests).
    """
    conn = op.get_bind()
    conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        with op.batch_alter_table("channel") as batch_op:
            batch_op.drop_constraint(
                "uq_channel_workspace_role_name", type_="unique"
            )
        op.execute(
            "CREATE UNIQUE INDEX uq_channel_active_workspace_role_name "
            "ON channel (workspace_id, role, lower(name)) WHERE status = 'active'"
        )
    finally:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    """Refuse to re-introduce the unconditional constraint.

    Recovery is backup restore (PERSISTENCE_DOMAIN_CONTRACT §7): the
    unconditional unique constraint would reject legitimate
    archive-then-recreate rows created after this migration.
    """
    raise RuntimeError(
        "Revision 1c9f2a4b7d8e (active-only channel name uniqueness) is not "
        "reversible; restore a pre-S03 backup instead of downgrading."
    )
