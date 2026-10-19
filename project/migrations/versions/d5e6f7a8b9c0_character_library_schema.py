"""Add character library schema (S06-T01)

Revision ID: d5e6f7a8b9c0
Revises: 1c9f2a4b7d8e
Create Date: 2026-08-04 11:13:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: str | None = '1c9f2a4b7d8e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'character',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('character_type', sa.String(length=32), server_default='character', nullable=False),
        sa.Column('symmetry', sa.String(length=32), server_default='symmetric', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='draft', nullable=False),
        sa.Column('default_version_id', sa.String(length=36), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('length(name) > 0', name='ck_character_name_nonempty'),
        sa.CheckConstraint('length(name) <= 200', name='ck_character_name_len'),
        sa.CheckConstraint('length(code) > 0', name='ck_character_code_nonempty'),
        sa.CheckConstraint('length(code) <= 64', name='ck_character_code_len'),
        sa.CheckConstraint("character_type IN ('character','prop','other')", name='ck_character_type'),
        sa.CheckConstraint("symmetry IN ('symmetric','asymmetric')", name='ck_character_symmetry'),
        sa.CheckConstraint("status IN ('draft','generating','needs_review','ready','archived')", name='ck_character_status'),
        sa.CheckConstraint('revision > 0', name='ck_character_revision_positive'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_character_active_workspace_code',
        'character',
        ['workspace_id', sa.text('lower(code)')],
        unique=True,
        sqlite_where=sa.text("status != 'archived'"),
        postgresql_where=sa.text("status != 'archived'"),
    )

    op.create_table(
        'character_pack_version',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('character_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='draft', nullable=False),
        sa.Column('validation_json', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('version > 0', name='ck_pack_version_positive'),
        sa.CheckConstraint("status IN ('draft','validating','ready','published','archived')", name='ck_pack_version_status'),
        sa.CheckConstraint('revision > 0', name='ck_pack_version_revision_positive'),
        sa.ForeignKeyConstraint(['character_id'], ['character.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id', 'version', name='uq_pack_version_character_version'),
    )

    op.create_table(
        'character_asset',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('pack_version_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('pose_slot', sa.String(length=64), nullable=False),
        sa.Column('artifact_id', sa.String(length=36), nullable=False),
        sa.Column('revision', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint('length(pose_slot) > 0', name='ck_character_asset_pose_slot_nonempty'),
        sa.CheckConstraint('length(pose_slot) <= 64', name='ck_character_asset_pose_slot_len'),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifact.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['pack_version_id'], ['character_pack_version.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pack_version_id', 'pose_slot', name='uq_character_asset_version_pose_slot'),
    )


def downgrade() -> None:
    raise RuntimeError("Character library migration is not reversible per S06 contract")
