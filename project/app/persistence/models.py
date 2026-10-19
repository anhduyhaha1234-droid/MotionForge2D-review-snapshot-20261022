"""SQLAlchemy ORM models for the approved S01 persistence contract.

These models mirror ``docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md``
exactly.  No Job/JobStep tables exist yet (deferred to S02-T01).  Models are
the storage layer only — they are never exported as API schemas.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    text as sa_text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

__all__ = [
    "ARTIFACT_KINDS",
    "ARTIFACT_STATES",
    "ARCHIVED_VIDEO_STATUS",
    "CHARACTER_STATUSES",
    "CHARACTER_SYMMETRIES",
    "CHARACTER_TYPES",
    "CHANNEL_ROLES",
    "CHANNEL_STATUSES",
    "CORE_POSE_SLOTS",
    "JOB_ACTORS",
    "JOB_STATES",
    "JOB_STEP_STATES",
    "LEGACY_IMPORT_STATUSES",
    "OWNER_TYPES",
    "PACK_STATUSES",
    "PROJECT_STATUSES",
    "RESOURCE_CLASSES",
    "SCENE_STATUSES",
    "STEP_TYPES",
    "VIDEO_PIPELINE_STATES",
    "Artifact",
    "ArtifactOwner",
    "Character",
    "CharacterAsset",
    "CharacterPackVersion",
    "Channel",
    "Job",
    "JobAttempt",
    "JobEvent",
    "JobLease",
    "JobStep",
    "LegacyImport",
    "Project",
    "Scene",
    "VideoItem",
    "Workspace",
    "utc_now",
]

# ── Enum-like constants (stored as validated strings) ────────────────────────

CHANNEL_ROLES = ("source", "production")
CHANNEL_STATUSES = ("active", "archived")
PROJECT_STATUSES = (
    "draft",
    "active",
    "needs_review",
    "rendering",
    "completed",
    "archived",
)
VIDEO_PIPELINE_STATES = (
    "imported",
    "analyzing",
    "objects_ready",
    "mapping_required",
    "demo_required",
    "demo_approved",
    "applying_reskin",
    "needs_review",
    "ready_to_export",
    "rendering",
    "completed",
    "failed",
    "archived",
)
#: Convenience constant: the archive terminal state of a Video Item.
ARCHIVED_VIDEO_STATUS = "archived"
CHARACTER_STATUSES = ("draft", "generating", "needs_review", "ready", "archived")
CHARACTER_TYPES = ("character", "prop", "other")
CHARACTER_SYMMETRIES = ("symmetric", "asymmetric")
PACK_STATUSES = ("draft", "validating", "ready", "published", "archived")
CORE_POSE_SLOTS = ("front", "three_quarter", "side", "back", "sitting", "walking")
SCENE_STATUSES = ("pending", "draft", "approved")
ARTIFACT_KINDS = ("video", "image", "audio", "document", "other")
ARTIFACT_STATES = ("staging", "ready", "trash", "missing", "failed")
OWNER_TYPES = ("channel", "project", "video_item", "scene", "artifact")
LEGACY_IMPORT_STATUSES = ("previewed", "importing", "completed", "failed", "rolled_back")
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
JOB_ACTORS = ("worker", "scheduler", "api", "reconciler", "system")


def utc_now() -> datetime:
    """Timezone-aware UTC now used by every default timestamp."""
    return datetime.now(UTC)


def _new_id() -> str:
    """Opaque public identifier (UUIDv7-compatible string; UUID4 initial)."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Declarative base for all persistence models."""


# ── Mixins ────────────────────────────────────────────────────────────────────


class TimestampMixin:
    """Created/updated UTC timestamps plus optimistic-concurrency revision."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=sa_text("(CURRENT_TIMESTAMP)"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=sa_text("(CURRENT_TIMESTAMP)"),
        nullable=False,
    )
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default=sa_text("1"), nullable=False
    )


class ArchivableMixin(TimestampMixin):
    """Adds an optional archived_at timestamp."""

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── Entities ──────────────────────────────────────────────────────────────────


class Workspace(TimestampMixin, Base):
    """Root ownership boundary for channels, projects and future libraries."""

    __tablename__ = "workspace"
    __table_args__ = (
        CheckConstraint("length(name) BETWEEN 1 AND 120", name="ck_workspace_name_len"),
        CheckConstraint("revision > 0", name="ck_workspace_revision_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    channels: Mapped[list[Channel]] = relationship(back_populates="workspace")
    projects: Mapped[list[Project]] = relationship(back_populates="workspace")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="workspace")
    jobs: Mapped[list[Job]] = relationship(back_populates="workspace")
    characters: Mapped[list[Character]] = relationship(back_populates="workspace")


class Channel(ArchivableMixin, Base):
    """Source or production channel owned by a workspace."""

    __tablename__ = "channel"
    __table_args__ = (
        # Uniqueness of ACTIVE channel names is enforced by the partial
        # unique index ``uq_channel_active_workspace_role_name`` (S03-T01
        # migration 1c9f2a4b7d8e): case-insensitive (lower(name)) and
        # active-only (status='active').  The legacy unconditional
        # constraint was dropped by that migration so archived names can
        # be reused by a new active channel.
        UniqueConstraint(
            "workspace_id", "legacy_id", name="uq_channel_workspace_legacy_id"
        ),
        CheckConstraint("length(name) > 0", name="ck_channel_name_nonempty"),
        CheckConstraint("length(name) <= 200", name="ck_channel_name_len"),
        CheckConstraint("role IN ('source', 'production')", name="ck_channel_role"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_channel_status"),
        CheckConstraint("revision > 0", name="ck_channel_revision_positive"),
        Index("ix_channel_workspace_role_name", "workspace_id", "role", "name"),
        Index(
            "uq_channel_active_workspace_role_name",
            "workspace_id",
            "role",
            sa_text("lower(name)"),
            unique=True,
            sqlite_where=sa_text("status = 'active'"),
            postgresql_where=sa_text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    legacy_id: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(200, collation="NOCASE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    color: Mapped[str | None] = mapped_column(String(32))
    avatar_artifact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("artifact.id", ondelete="RESTRICT")
    )
    target_language: Mapped[str | None] = mapped_column(String(32))
    default_output_profile: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")

    workspace: Mapped[Workspace] = relationship(back_populates="channels")


class Project(ArchivableMixin, Base):
    """Project aggregate root: owns VideoItem ordering and project defaults."""

    __tablename__ = "project"
    __table_args__ = (
        UniqueConstraint("workspace_id", "legacy_id", name="uq_project_workspace_legacy_id"),
        CheckConstraint("length(name) BETWEEN 1 AND 200", name="ck_project_name_len"),
        CheckConstraint(
            "status IN ('draft','active','needs_review','rendering','completed','archived')",
            name="ck_project_status",
        ),
        CheckConstraint("revision > 0", name="ck_project_revision_positive"),
        Index("ix_project_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    legacy_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    source_channel_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("channel.id", ondelete="RESTRICT")
    )
    production_channel_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("channel.id", ondelete="RESTRICT")
    )
    default_output_profile: Mapped[str | None] = mapped_column(String(64))
    resume_step: Mapped[str | None] = mapped_column(String(64))

    workspace: Mapped[Workspace] = relationship(back_populates="projects")
    source_channel: Mapped[Channel | None] = relationship(foreign_keys=[source_channel_id])
    production_channel: Mapped[Channel | None] = relationship(
        foreign_keys=[production_channel_id]
    )
    video_items: Mapped[list[VideoItem]] = relationship(
        back_populates="project", order_by="VideoItem.position"
    )


class VideoItem(ArchivableMixin, Base):
    """Pipeline unit: owns its scene records and references its source media."""

    __tablename__ = "video_item"
    __table_args__ = (
        UniqueConstraint("project_id", "position", name="uq_video_item_project_position"),
        UniqueConstraint("project_id", "legacy_id", name="uq_video_item_project_legacy_id"),
        CheckConstraint("length(title) BETWEEN 1 AND 240", name="ck_video_item_title_len"),
        CheckConstraint("position >= 0", name="ck_video_item_position_nonneg"),
        CheckConstraint(
            "status IN ('imported','analyzing','objects_ready','mapping_required',"
            "'demo_required','demo_approved','applying_reskin','needs_review',"
            "'ready_to_export','rendering','completed','failed','archived')",
            name="ck_video_item_status",
        ),
        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0", name="ck_video_item_duration_ms"
        ),
        CheckConstraint("width IS NULL OR width >= 0", name="ck_video_item_width"),
        CheckConstraint("height IS NULL OR height >= 0", name="ck_video_item_height"),
        CheckConstraint("fps_num IS NULL OR fps_num > 0", name="ck_video_item_fps_num"),
        CheckConstraint("fps_den IS NULL OR fps_den > 0", name="ck_video_item_fps_den"),
        CheckConstraint("revision > 0", name="ck_video_item_revision_positive"),
        Index("ix_video_item_project_position", "project_id", "position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("project.id", ondelete="RESTRICT"), nullable=False
    )
    legacy_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="imported")
    source_artifact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("artifact.id", ondelete="RESTRICT")
    )
    source_channel_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("channel.id", ondelete="RESTRICT")
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    fps_num: Mapped[int | None] = mapped_column(Integer)
    fps_den: Mapped[int | None] = mapped_column(Integer)
    resume_step: Mapped[str | None] = mapped_column(String(64))
    resume_payload_json: Mapped[str | None] = mapped_column(Text)

    project: Mapped[Project] = relationship(back_populates="video_items")
    source_channel: Mapped[Channel | None] = relationship(foreign_keys=[source_channel_id])
    scenes: Mapped[list[Scene]] = relationship(
        back_populates="video_item", order_by="Scene.position"
    )


class Scene(TimestampMixin, Base):
    """Scene record owned by a VideoItem (cascade only inside authorized purge)."""

    __tablename__ = "scene"
    __table_args__ = (
        UniqueConstraint("video_item_id", "position", name="uq_scene_video_item_position"),
        UniqueConstraint(
            "video_item_id", "legacy_scene_id", name="uq_scene_video_item_legacy_id"
        ),
        CheckConstraint("position >= 0", name="ck_scene_position_nonneg"),
        CheckConstraint("start_frame >= 0", name="ck_scene_start_frame_nonneg"),
        CheckConstraint("end_frame >= 0", name="ck_scene_end_frame_nonneg"),
        CheckConstraint("start_time_ms >= 0", name="ck_scene_start_time_ms_nonneg"),
        CheckConstraint("end_time_ms >= 0", name="ck_scene_end_time_ms_nonneg"),
        CheckConstraint("end_frame >= start_frame", name="ck_scene_end_frame_ge_start"),
        CheckConstraint("end_time_ms >= start_time_ms", name="ck_scene_end_time_ms_ge_start"),
        CheckConstraint("status IN ('pending', 'draft', 'approved')", name="ck_scene_status"),
        CheckConstraint("revision > 0", name="ck_scene_revision_positive"),
        Index("ix_scene_video_item_position", "video_item_id", "position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    video_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("video_item.id", ondelete="CASCADE"), nullable=False
    )
    legacy_scene_id: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    video_item: Mapped[VideoItem] = relationship(back_populates="scenes")


class Artifact(TimestampMixin, Base):
    """Managed file record; bytes live under the configured managed root."""

    __tablename__ = "artifact"
    __table_args__ = (
        UniqueConstraint("workspace_id", "relative_path", name="uq_artifact_workspace_path"),
        CheckConstraint("length(relative_path) > 0", name="ck_artifact_path_nonempty"),
        CheckConstraint(
            "kind IN ('video','image','audio','document','other')", name="ck_artifact_kind"
        ),
        CheckConstraint(
            "state IN ('staging','ready','trash','missing','failed')",
            name="ck_artifact_state",
        ),
        CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="ck_artifact_size_bytes"),
        CheckConstraint(
            "sha256 IS NULL OR length(sha256) = 64", name="ck_artifact_sha256_len"
        ),
        CheckConstraint("revision > 0", name="ck_artifact_revision_positive"),
        Index("ix_artifact_workspace_path", "workspace_id", "relative_path"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="staging")
    sha256: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workspace: Mapped[Workspace] = relationship(back_populates="artifacts")
    owners: Mapped[list[ArtifactOwner]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan"
    )


class ArtifactOwner(Base):
    """Explicit polymorphic owner link between an artifact and a business entity."""

    __tablename__ = "artifact_owner"
    __table_args__ = (
        CheckConstraint(
            "owner_type IN ('channel','project','video_item','scene','artifact')",
            name="ck_artifact_owner_type",
        ),
        CheckConstraint("length(purpose) > 0", name="ck_artifact_owner_purpose_nonempty"),
        Index("ix_artifact_owner_owner", "owner_type", "owner_id"),
    )

    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifact.id", ondelete="RESTRICT"), primary_key=True
    )
    owner_type: Mapped[str] = mapped_column(String(24), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(32), primary_key=True)

    artifact: Mapped[Artifact] = relationship(back_populates="owners")


class LegacyImport(Base):
    """Idempotent record of a legacy JSON import attempt."""

    __tablename__ = "legacy_import"
    __table_args__ = (
        UniqueConstraint("source_kind", "source_sha256", name="uq_legacy_import_kind_sha256"),
        CheckConstraint("length(source_kind) > 0", name="ck_legacy_import_kind_nonempty"),
        CheckConstraint("length(source_locator) > 0", name="ck_legacy_import_locator_nonempty"),
        CheckConstraint("length(source_sha256) = 64", name="ck_legacy_import_sha256_len"),
        CheckConstraint(
            "status IN ('previewed','importing','completed','failed','rolled_back')",
            name="ck_legacy_import_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_locator: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="previewed")
    summary_json: Mapped[str | None] = mapped_column(Text)
    error_json: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── Durable job entities (S02-T02, DURABLE_JOB_CONTRACT V1.1) ────────────────


class Job(TimestampMixin, Base):
    """Durable unit of user-visible work (approved DURABLE_JOB_CONTRACT V1.1).

    Terminal rows are immutable: no field changes, no re-run, no delete.
    Retry/restart of a terminal Job is a new successor Job linked through
    ``predecessor_job_id`` (contract §4.5-4, §6.4, §8.5).  Uniqueness: one
    active or completed Job per ``(workspace_id, idempotency_key)``.
    """

    __tablename__ = "job"
    __table_args__ = (
        Index(
            "uq_job_idempotency_key",
            "workspace_id",
            "idempotency_key",
            "input_generation",
            unique=True,
            sqlite_where=sa_text(
                "idempotency_key IS NOT NULL AND state NOT IN ('failed','cancelled')"
            ),
        ),
        UniqueConstraint("predecessor_job_id", name="uq_job_predecessor_job_id"),
        CheckConstraint(
            "state IN ('pending','queued','running','cancelling','cancelled',"
            "'completed','failed','fenced')",
            name="ck_job_state",
        ),
        CheckConstraint(
            "resource_class IN ('cpu_light','cpu_heavy','gpu','io')",
            name="ck_job_resource_class",
        ),
        CheckConstraint("priority BETWEEN 0 AND 100", name="ck_job_priority_range"),
        CheckConstraint("max_attempts >= 1", name="ck_job_max_attempts_positive"),
        CheckConstraint("attempt >= 0", name="ck_job_attempt_nonneg"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_job_progress_range"),
        CheckConstraint("length(job_type) > 0", name="ck_job_type_nonempty"),
        CheckConstraint("length(owner_type) > 0", name="ck_job_owner_type_nonempty"),
        CheckConstraint("length(owner_id) > 0", name="ck_job_owner_id_nonempty"),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_job_finished_requires_started",
        ),
        CheckConstraint("revision > 0", name="ck_job_revision_positive"),
        Index("ix_job_workspace_key", "workspace_id", "idempotency_key"),
        Index("ix_job_workspace_state", "workspace_id", "state"),
        Index("ix_job_queue", "state", "priority", "created_at"),
        Index("ix_job_owner", "owner_type", "owner_id"),
        Index("ix_job_parent", "parent_job_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_type: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    parent_job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job.id", ondelete="RESTRICT")
    )
    predecessor_job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job.id", ondelete="RESTRICT")
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    resource_class: Mapped[str] = mapped_column(
        String(16), nullable=False, default="cpu_light"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    input_generation: Mapped[str | None] = mapped_column(String(64))
    input_manifest_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_json: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workspace: Mapped[Workspace] = relationship(back_populates="jobs")
    steps: Mapped[list[JobStep]] = relationship(
        back_populates="job", order_by="JobStep.position"
    )
    attempts: Mapped[list[JobAttempt]] = relationship(back_populates="job")
    events: Mapped[list[JobEvent]] = relationship(back_populates="job")
    lease: Mapped[JobLease | None] = relationship(back_populates="job")


class JobStep(TimestampMixin, Base):
    """Ordered, resumable unit inside a Job (checkpoint boundary)."""

    __tablename__ = "job_step"
    __table_args__ = (
        UniqueConstraint("job_id", "step_code", name="uq_job_step_job_code"),
        UniqueConstraint("job_id", "position", name="uq_job_step_job_position"),
        CheckConstraint(
            "state IN ('pending','ready','running','cancelling','cancelled',"
            "'completed','failed','skipped')",
            name="ck_job_step_state",
        ),
        CheckConstraint("step_type IN ('sync','async')", name="ck_job_step_type"),
        CheckConstraint(
            "resource_class IN ('cpu_light','cpu_heavy','gpu','io')",
            name="ck_job_step_resource_class",
        ),
        CheckConstraint("position >= 0", name="ck_job_step_position_nonneg"),
        CheckConstraint("priority BETWEEN 0 AND 100", name="ck_job_step_priority_range"),
        CheckConstraint("weight >= 0", name="ck_job_step_weight_nonneg"),
        CheckConstraint("attempt >= 0", name="ck_job_step_attempt_nonneg"),
        CheckConstraint("max_attempts >= 1", name="ck_job_step_max_attempts_positive"),
        CheckConstraint(
            "progress >= 0 AND progress <= 100", name="ck_job_step_progress_range"
        ),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_job_step_finished_requires_started",
        ),
        CheckConstraint("revision > 0", name="ck_job_step_revision_positive"),
        Index("ix_job_step_job_position", "job_id", "position"),
        Index("ix_job_step_job_state", "job_id", "state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job.id", ondelete="RESTRICT"), nullable=False
    )
    step_code: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(16), nullable=False, default="sync")
    depends_on_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    resource_class: Mapped[str] = mapped_column(
        String(16), nullable=False, default="cpu_light"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    checkpoint_json: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_json: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    job: Mapped[Job] = relationship(back_populates="steps")


class JobAttempt(Base):
    """Append-only record of one JobStep execution (contract §8.2)."""

    __tablename__ = "job_attempt"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "step_id", "attempt", name="uq_job_attempt_job_step_number"
        ),
        UniqueConstraint(
            "job_id", "step_code", "attempt", name="uq_job_attempt_job_code_number"
        ),
        CheckConstraint("attempt >= 1", name="ck_job_attempt_number_positive"),
        CheckConstraint("length(worker_id) > 0", name="ck_job_attempt_worker_nonempty"),
        CheckConstraint("length(fence_token) > 0", name="ck_job_attempt_token_nonempty"),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_job_attempt_finished_requires_started",
        ),
        Index("ix_job_attempt_job_step", "job_id", "step_id", "attempt"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job.id", ondelete="RESTRICT"), nullable=False
    )
    step_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_step.id", ondelete="RESTRICT")
    )
    step_code: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    fence_token: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text)
    error_json: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    job: Mapped[Job] = relationship(back_populates="attempts")


class JobEvent(Base):
    """Append-only state-transition log (contract §10.2)."""

    __tablename__ = "job_event"
    __table_args__ = (
        CheckConstraint("length(event_type) > 0", name="ck_job_event_type_nonempty"),
        CheckConstraint(
            "actor IN ('worker','scheduler','api','reconciler','system')",
            name="ck_job_event_actor",
        ),
        Index("ix_job_event_job_created", "job_id", "created_at"),
        Index("ix_job_event_job_step", "job_id", "step_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job.id", ondelete="RESTRICT"), nullable=False
    )
    step_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_step.id", ondelete="RESTRICT")
    )
    step_code: Mapped[str | None] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_state: Mapped[str | None] = mapped_column(String(16))
    to_state: Mapped[str | None] = mapped_column(String(16))
    actor: Mapped[str] = mapped_column(String(32), nullable=False)
    worker_id: Mapped[str | None] = mapped_column(String(128))
    fence_token: Mapped[str | None] = mapped_column(String(64))
    reason_code: Mapped[str | None] = mapped_column(String(64))
    revision: Mapped[int | None] = mapped_column(Integer)
    details_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    job: Mapped[Job] = relationship(back_populates="events")


class JobLease(TimestampMixin, Base):
    """Exclusive claim by one worker over a Job for a bounded time window."""

    __tablename__ = "job_lease"
    __table_args__ = (
        CheckConstraint("lease_version >= 1", name="ck_job_lease_version_positive"),
        CheckConstraint("length(worker_id) > 0", name="ck_job_lease_worker_nonempty"),
        CheckConstraint("length(fence_token) > 0", name="ck_job_lease_token_nonempty"),
        CheckConstraint("ttl_seconds > 0", name="ck_job_lease_ttl_positive"),
        CheckConstraint(
            "expires_at >= acquired_at", name="ck_job_lease_expires_after_acquired"
        ),
        CheckConstraint(
            "heartbeat_at >= acquired_at", name="ck_job_lease_heartbeat_after_acquired"
        ),
    )

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job.id", ondelete="RESTRICT"), primary_key=True
    )
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    lease_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fence_token: Mapped[str] = mapped_column(String(64), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    job: Mapped[Job] = relationship(back_populates="lease")


class Character(ArchivableMixin, Base):
    """Reusable workspace character asset definition."""

    __tablename__ = "character"
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_character_name_nonempty"),
        CheckConstraint("length(name) <= 200", name="ck_character_name_len"),
        CheckConstraint("length(code) > 0", name="ck_character_code_nonempty"),
        CheckConstraint("length(code) <= 64", name="ck_character_code_len"),
        CheckConstraint(
            "character_type IN ('character','prop','other')",
            name="ck_character_type",
        ),
        CheckConstraint(
            "symmetry IN ('symmetric','asymmetric')",
            name="ck_character_symmetry",
        ),
        CheckConstraint(
            "status IN ('draft','generating','needs_review','ready','archived')",
            name="ck_character_status",
        ),
        CheckConstraint("revision > 0", name="ck_character_revision_positive"),
        Index(
            "uq_character_active_workspace_code",
            "workspace_id",
            sa_text("lower(code)"),
            unique=True,
            postgresql_where=sa_text("status != 'archived'"),
            sqlite_where=sa_text("status != 'archived'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    character_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="character"
    )
    symmetry: Mapped[str] = mapped_column(
        String(32), nullable=False, default="symmetric"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )
    default_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "character_pack_version.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_character_default_version",
        ),
    )
    description: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default=sa_text("1"), nullable=False
    )

    workspace: Mapped[Workspace] = relationship(back_populates="characters")
    versions: Mapped[list[CharacterPackVersion]] = relationship(
        back_populates="character",
        foreign_keys="[CharacterPackVersion.character_id]",
    )


class CharacterPackVersion(ArchivableMixin, Base):
    """Versioned pose pack for a Character."""

    __tablename__ = "character_pack_version"
    __table_args__ = (
        UniqueConstraint(
            "character_id", "version", name="uq_pack_version_character_version"
        ),
        CheckConstraint("version > 0", name="ck_pack_version_positive"),
        CheckConstraint(
            "status IN ('draft','validating','ready','published','archived')",
            name="ck_pack_version_status",
        ),
        CheckConstraint("revision > 0", name="ck_pack_version_revision_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    character_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("character.id", ondelete="RESTRICT"), nullable=False
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )
    validation_json: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default=sa_text("1"), nullable=False
    )

    character: Mapped[Character] = relationship(
        back_populates="versions",
        foreign_keys=[character_id],
    )
    workspace: Mapped[Workspace] = relationship()
    assets: Mapped[list[CharacterAsset]] = relationship(back_populates="pack_version")


class CharacterAsset(TimestampMixin, Base):
    """Pose asset slot attachment referencing an Artifact."""

    __tablename__ = "character_asset"
    __table_args__ = (
        UniqueConstraint(
            "pack_version_id", "pose_slot", name="uq_character_asset_version_pose_slot"
        ),
        CheckConstraint("length(pose_slot) > 0", name="ck_character_asset_pose_slot_nonempty"),
        CheckConstraint("length(pose_slot) <= 64", name="ck_character_asset_pose_slot_len"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    pack_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("character_pack_version.id", ondelete="RESTRICT"), nullable=False
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspace.id", ondelete="RESTRICT"), nullable=False
    )
    pose_slot: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifact.id", ondelete="RESTRICT"), nullable=False
    )

    pack_version: Mapped[CharacterPackVersion] = relationship(back_populates="assets")
    artifact: Mapped[Artifact] = relationship()
    workspace: Mapped[Workspace] = relationship()
