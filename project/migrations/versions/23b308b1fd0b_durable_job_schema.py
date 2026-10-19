"""durable job schema (S02-T02)

Hand-authored forward migration for the approved V1.1 durable job contract
(see docs/architecture/DURABLE_JOB_CONTRACT.md).  Adds the five job tables —
``job``, ``job_step``, ``job_attempt``, ``job_event`` and ``job_lease`` —
with the contract constraints, foreign keys and partial indexes needed by
S02-T02..T05.  Deliberately NOT reversible: downgrade is never assumed as a
recovery path (PERSISTENCE_DOMAIN_CONTRACT §7), and dropping these tables
would silently destroy durable job state.

Revision ID: 23b308b1fd0b
Revises: a1b2c3d4e5f6
Create Date: 2026-08-03
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "23b308b1fd0b"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JOB_STATES = (
    "pending",
    "queued",
    "running",
    "cancelling",
    "cancelled",
    "completed",
    "failed",
    "fenced",
)
JOB_STEP_STATES = (
    "pending",
    "ready",
    "running",
    "cancelling",
    "cancelled",
    "completed",
    "failed",
    "skipped",
)
RESOURCE_CLASSES = ("cpu_light", "cpu_heavy", "gpu", "io")
STEP_TYPES = ("sync", "async")


def upgrade() -> None:
    """Create the durable job schema (S02-T02)."""
    op.create_table(
        "job",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("owner_type", sa.String(length=24), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("parent_job_id", sa.String(length=36), nullable=True),
        sa.Column("predecessor_job_id", sa.String(length=36), nullable=True),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("resource_class", sa.String(length=16), nullable=False, server_default="cpu_light"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("input_generation", sa.String(length=64), nullable=True),
        sa.Column("input_manifest_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "state IN ('pending','queued','running','cancelling','cancelled',"
            "'completed','failed','fenced')",
            name="ck_job_state",
        ),
        sa.CheckConstraint(
            "resource_class IN ('cpu_light','cpu_heavy','gpu','io')",
            name="ck_job_resource_class",
        ),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="ck_job_priority_range"),
        sa.CheckConstraint("max_attempts >= 1", name="ck_job_max_attempts_positive"),
        sa.CheckConstraint("attempt >= 0", name="ck_job_attempt_nonneg"),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_job_progress_range"),
        sa.CheckConstraint(
            "length(job_type) > 0", name="ck_job_type_nonempty"
        ),
        sa.CheckConstraint("length(owner_type) > 0", name="ck_job_owner_type_nonempty"),
        sa.CheckConstraint("length(owner_id) > 0", name="ck_job_owner_id_nonempty"),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_job_finished_requires_started",
        ),
        sa.CheckConstraint("revision > 0", name="ck_job_revision_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspace.id"], name="fk_job_workspace", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["parent_job_id"], ["job.id"], name="fk_job_parent_job", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_job_id"],
            ["job.id"],
            name="fk_job_predecessor_job",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index(
            "uq_job_idempotency_key",
            "workspace_id",
            "idempotency_key",
            "input_generation",
            unique=True,
            sqlite_where=sa.text(
                "idempotency_key IS NOT NULL AND state NOT IN ('failed','cancelled')"
            ),
        ),
        sa.UniqueConstraint(
            "predecessor_job_id", name="uq_job_predecessor_job_id"
        ),
    )
    op.create_index("ix_job_workspace_key", "job", ["workspace_id", "idempotency_key"], unique=False)
    op.create_index("ix_job_workspace_state", "job", ["workspace_id", "state"], unique=False)
    op.create_index("ix_job_queue", "job", ["state", "priority", "created_at"], unique=False)
    op.create_index(
        "ix_job_owner", "job", ["owner_type", "owner_id"], unique=False
    )
    op.create_index(
        "ix_job_parent", "job", ["parent_job_id"], unique=False
    )
    op.create_table(
        "job_step",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("step_code", sa.String(length=128), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=16), nullable=False, server_default="sync"),
        sa.Column("depends_on_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("resource_class", sa.String(length=16), nullable=False, server_default="cpu_light"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("checkpoint_json", sa.Text(), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "state IN ('pending','ready','running','cancelling','cancelled',"
            "'completed','failed','skipped')",
            name="ck_job_step_state",
        ),
        sa.CheckConstraint(
            "step_type IN ('sync','async')", name="ck_job_step_type"
        ),
        sa.CheckConstraint(
            "resource_class IN ('cpu_light','cpu_heavy','gpu','io')",
            name="ck_job_step_resource_class",
        ),
        sa.CheckConstraint("position >= 0", name="ck_job_step_position_nonneg"),
        sa.CheckConstraint(
            "priority BETWEEN 0 AND 100", name="ck_job_step_priority_range"
        ),
        sa.CheckConstraint("weight >= 0", name="ck_job_step_weight_nonneg"),
        sa.CheckConstraint("attempt >= 0", name="ck_job_step_attempt_nonneg"),
        sa.CheckConstraint(
            "max_attempts >= 1", name="ck_job_step_max_attempts_positive"
        ),
        sa.CheckConstraint(
            "progress >= 0 AND progress <= 100", name="ck_job_step_progress_range"
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_job_step_finished_requires_started",
        ),
        sa.CheckConstraint("revision > 0", name="ck_job_step_revision_positive"),
        sa.ForeignKeyConstraint(
            ["job_id"], ["job.id"], name="fk_job_step_job", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "step_code", name="uq_job_step_job_code"),
        sa.UniqueConstraint("job_id", "position", name="uq_job_step_job_position"),
    )
    op.create_index("ix_job_step_job_position", "job_step", ["job_id", "position"], unique=False)
    op.create_index(
        "ix_job_step_job_state", "job_step", ["job_id", "state"], unique=False
    )
    op.create_table(
        "job_attempt",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.String(length=36), nullable=True),
        sa.Column("step_code", sa.String(length=128), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("fence_token", sa.String(length=64), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_json", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempt >= 1", name="ck_job_attempt_number_positive"),
        sa.CheckConstraint("length(worker_id) > 0", name="ck_job_attempt_worker_nonempty"),
        sa.CheckConstraint(
            "length(fence_token) > 0", name="ck_job_attempt_token_nonempty"
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_job_attempt_finished_requires_started",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["job.id"], name="fk_job_attempt_job", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["step_id"], ["job_step.id"], name="fk_job_attempt_step", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_id", "step_id", "attempt", name="uq_job_attempt_job_step_number"
        ),
        sa.UniqueConstraint(
            "job_id", "step_code", "attempt", name="uq_job_attempt_job_code_number"
        ),
    )
    op.create_index(
        "ix_job_attempt_job_step", "job_attempt", ["job_id", "step_id", "attempt"], unique=False
    )
    op.create_table(
        "job_event",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.String(length=36), nullable=True),
        sa.Column("step_code", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("from_state", sa.String(length=16), nullable=True),
        sa.Column("to_state", sa.String(length=16), nullable=True),
        sa.Column("actor", sa.String(length=32), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.Column("fence_token", sa.String(length=64), nullable=True),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint("length(event_type) > 0", name="ck_job_event_type_nonempty"),
        sa.CheckConstraint(
            "actor IN ('worker','scheduler','api','reconciler','system')",
            name="ck_job_event_actor",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["job.id"], name="fk_job_event_job", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["step_id"], ["job_step.id"], name="fk_job_event_step", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_event_job_created", "job_event", ["job_id", "created_at"], unique=False)
    op.create_index(
        "ix_job_event_job_step", "job_event", ["job_id", "step_id"], unique=False
    )
    op.create_table(
        "job_lease",
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("lease_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fence_token", sa.String(length=64), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ttl_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "lease_version >= 1", name="ck_job_lease_version_positive"
        ),
        sa.CheckConstraint("length(worker_id) > 0", name="ck_job_lease_worker_nonempty"),
        sa.CheckConstraint(
            "length(fence_token) > 0", name="ck_job_lease_token_nonempty"
        ),
        sa.CheckConstraint(
            "ttl_seconds > 0", name="ck_job_lease_ttl_positive"
        ),
        sa.CheckConstraint(
            "expires_at >= acquired_at", name="ck_job_lease_expires_after_acquired"
        ),
        sa.CheckConstraint(
            "heartbeat_at >= acquired_at", name="ck_job_lease_heartbeat_after_acquired"
        ),
        sa.CheckConstraint("revision > 0", name="ck_job_lease_revision_positive"),
        sa.ForeignKeyConstraint(
            ["job_id"], ["job.id"], name="fk_job_lease_job", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("job_id"),
    )


def downgrade() -> None:
    """Refuse to drop the durable job schema.

    Recovery is backup restore, never a lossy downgrade (persistence domain
    contract §7 "Rollback and compatibility").  Terminal Job rows are
    immutable and must never be destroyed by a migration step.
    """
    raise RuntimeError(
        "Revision 23b308b1fd0b (durable job schema) is not reversible; "
        "restore a pre-S02 backup instead of downgrading."
    )
