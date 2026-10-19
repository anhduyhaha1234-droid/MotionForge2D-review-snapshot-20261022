"""initial S01 persistence schema

Hand-authored migration for the approved S01 domain contract
(see docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md).  Contains only the
S01 entities — no Job/JobStep tables, no artifact management behavior, no
legacy import, no API cutover.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-08-03
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the S01 persistence schema."""
    op.create_table(
        "workspace",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
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
        sa.CheckConstraint("length(name) BETWEEN 1 AND 120", name="ck_workspace_name_len"),
        sa.CheckConstraint("revision > 0", name="ck_workspace_revision_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "channel",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("legacy_id", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=200, collation="NOCASE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("avatar_artifact_id", sa.String(length=36), nullable=True),
        sa.Column("target_language", sa.String(length=32), nullable=True),
        sa.Column("default_output_profile", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
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
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("length(name) > 0", name="ck_channel_name_nonempty"),
        sa.CheckConstraint("length(name) <= 200", name="ck_channel_name_len"),
        sa.CheckConstraint("role IN ('source', 'production')", name="ck_channel_role"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_channel_status"),
        sa.CheckConstraint("revision > 0", name="ck_channel_revision_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspace.id"], name="fk_channel_workspace", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["avatar_artifact_id"],
            ["artifact.id"],
            name="fk_channel_avatar_artifact",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id", "role", "name", name="uq_channel_workspace_role_name"
        ),
        sa.UniqueConstraint("workspace_id", "legacy_id", name="uq_channel_workspace_legacy_id"),
    )
    op.create_index(
        "ix_channel_workspace_role_name",
        "channel",
        ["workspace_id", "role", "name"],
        unique=False,
    )
    op.create_table(
        "project",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("legacy_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("source_channel_id", sa.String(length=36), nullable=True),
        sa.Column("production_channel_id", sa.String(length=36), nullable=True),
        sa.Column("default_output_profile", sa.String(length=64), nullable=True),
        sa.Column("resume_step", sa.String(length=64), nullable=True),
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
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("length(name) BETWEEN 1 AND 200", name="ck_project_name_len"),
        sa.CheckConstraint(
            "status IN ('draft','active','needs_review','rendering','completed','archived')",
            name="ck_project_status",
        ),
        sa.CheckConstraint("revision > 0", name="ck_project_revision_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspace.id"], name="fk_project_workspace", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_channel_id"],
            ["channel.id"],
            name="fk_project_source_channel",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["production_channel_id"],
            ["channel.id"],
            name="fk_project_production_channel",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "legacy_id", name="uq_project_workspace_legacy_id"),
    )
    op.create_index("ix_project_workspace_status", "project", ["workspace_id", "status"], unique=False)
    op.create_table(
        "video_item",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("legacy_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="imported"),
        sa.Column("source_artifact_id", sa.String(length=36), nullable=True),
        sa.Column("source_channel_id", sa.String(length=36), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("fps_num", sa.Integer(), nullable=True),
        sa.Column("fps_den", sa.Integer(), nullable=True),
        sa.Column("resume_step", sa.String(length=64), nullable=True),
        sa.Column("resume_payload_json", sa.Text(), nullable=True),
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
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("length(title) BETWEEN 1 AND 240", name="ck_video_item_title_len"),
        sa.CheckConstraint("position >= 0", name="ck_video_item_position_nonneg"),
        sa.CheckConstraint(
            "status IN ('imported','analyzing','objects_ready','mapping_required',"
            "'demo_required','demo_approved','applying_reskin','needs_review',"
            "'ready_to_export','rendering','completed','failed','archived')",
            name="ck_video_item_status",
        ),
        sa.CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_video_item_duration_ms"),
        sa.CheckConstraint("width IS NULL OR width >= 0", name="ck_video_item_width"),
        sa.CheckConstraint("height IS NULL OR height >= 0", name="ck_video_item_height"),
        sa.CheckConstraint("fps_num IS NULL OR fps_num > 0", name="ck_video_item_fps_num"),
        sa.CheckConstraint("fps_den IS NULL OR fps_den > 0", name="ck_video_item_fps_den"),
        sa.CheckConstraint("revision > 0", name="ck_video_item_revision_positive"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["project.id"], name="fk_video_item_project", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_channel_id"],
            ["channel.id"],
            name="fk_video_item_source_channel",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_artifact_id"],
            ["artifact.id"],
            name="fk_video_item_source_artifact",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "position", name="uq_video_item_project_position"),
        sa.UniqueConstraint("project_id", "legacy_id", name="uq_video_item_project_legacy_id"),
    )
    op.create_index(
        "ix_video_item_project_position", "video_item", ["project_id", "position"], unique=False
    )
    op.create_table(
        "scene",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("video_item_id", sa.String(length=36), nullable=False),
        sa.Column("legacy_scene_id", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("start_frame", sa.Integer(), nullable=False),
        sa.Column("end_frame", sa.Integer(), nullable=False),
        sa.Column("start_time_ms", sa.Integer(), nullable=False),
        sa.Column("end_time_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
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
        sa.CheckConstraint("position >= 0", name="ck_scene_position_nonneg"),
        sa.CheckConstraint("start_frame >= 0", name="ck_scene_start_frame_nonneg"),
        sa.CheckConstraint("end_frame >= 0", name="ck_scene_end_frame_nonneg"),
        sa.CheckConstraint("start_time_ms >= 0", name="ck_scene_start_time_ms_nonneg"),
        sa.CheckConstraint("end_time_ms >= 0", name="ck_scene_end_time_ms_nonneg"),
        sa.CheckConstraint("end_frame >= start_frame", name="ck_scene_end_frame_ge_start"),
        sa.CheckConstraint("end_time_ms >= start_time_ms", name="ck_scene_end_time_ms_ge_start"),
        sa.CheckConstraint("status IN ('pending', 'draft', 'approved')", name="ck_scene_status"),
        sa.CheckConstraint("revision > 0", name="ck_scene_revision_positive"),
        sa.ForeignKeyConstraint(
            ["video_item_id"],
            ["video_item.id"],
            name="fk_scene_video_item",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_item_id", "position", name="uq_scene_video_item_position"),
        sa.UniqueConstraint(
            "video_item_id", "legacy_scene_id", name="uq_scene_video_item_legacy_id"
        ),
    )
    op.create_index(
        "ix_scene_video_item_position", "scene", ["video_item_id", "position"], unique=False
    )
    op.create_table(
        "artifact",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("relative_path", sa.String(length=1024), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="staging"),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
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
        sa.Column("trashed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("length(relative_path) > 0", name="ck_artifact_path_nonempty"),
        sa.CheckConstraint("kind IN ('video','image','audio','document','other')", name="ck_artifact_kind"),
        sa.CheckConstraint(
            "state IN ('staging','ready','trash','missing','failed')",
            name="ck_artifact_state",
        ),
        sa.CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="ck_artifact_size_bytes"),
        sa.CheckConstraint("sha256 IS NULL OR length(sha256) = 64", name="ck_artifact_sha256_len"),
        sa.CheckConstraint("revision > 0", name="ck_artifact_revision_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspace.id"], name="fk_artifact_workspace", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "relative_path", name="uq_artifact_workspace_path"),
    )
    op.create_index(
        "ix_artifact_workspace_path", "artifact", ["workspace_id", "relative_path"], unique=False
    )
    op.create_table(
        "artifact_owner",
        sa.Column("artifact_id", sa.String(length=36), nullable=False),
        sa.Column("owner_type", sa.String(length=24), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "owner_type IN ('channel','project','video_item','scene','artifact')",
            name="ck_artifact_owner_type",
        ),
        sa.CheckConstraint("length(purpose) > 0", name="ck_artifact_owner_purpose_nonempty"),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["artifact.id"], name="fk_artifact_owner_artifact", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("artifact_id", "owner_type", "owner_id", "purpose"),
    )
    op.create_index(
        "ix_artifact_owner_owner", "artifact_owner", ["owner_type", "owner_id"], unique=False
    )
    op.create_table(
        "legacy_import",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("source_locator", sa.String(length=1024), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="previewed"),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column("error_json", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("length(source_kind) > 0", name="ck_legacy_import_kind_nonempty"),
        sa.CheckConstraint(
            "length(source_locator) > 0", name="ck_legacy_import_locator_nonempty"
        ),
        sa.CheckConstraint("length(source_sha256) = 64", name="ck_legacy_import_sha256_len"),
        sa.CheckConstraint(
            "status IN ('previewed','importing','completed','failed','rolled_back')",
            name="ck_legacy_import_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_kind", "source_sha256", name="uq_legacy_import_kind_sha256"),
    )


def downgrade() -> None:
    """Drop the S01 persistence schema (reversible for the initial revision)."""
    op.drop_table("legacy_import")
    op.drop_index("ix_artifact_owner_owner", table_name="artifact_owner")
    op.drop_table("artifact_owner")
    op.drop_index("ix_artifact_workspace_path", table_name="artifact")
    op.drop_table("artifact")
    op.drop_index("ix_scene_video_item_position", table_name="scene")
    op.drop_table("scene")
    op.drop_index("ix_video_item_project_position", table_name="video_item")
    op.drop_table("video_item")
    op.drop_index("ix_project_workspace_status", table_name="project")
    op.drop_table("project")
    op.drop_index("ix_channel_workspace_role_name", table_name="channel")
    op.drop_table("channel")
    op.drop_table("workspace")
