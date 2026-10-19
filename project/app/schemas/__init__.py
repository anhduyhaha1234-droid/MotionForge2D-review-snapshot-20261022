"""Pydantic schemas for MotionForge project data model.

Schema version 2.0.0 — adds tracking metadata, occlusion, confidence.
Backward compatible: can load v1.0.0 projects via migration.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ─── Enums ────────────────────────────────────────────────────────────────────

class ObjectKind(str, Enum):
    CHARACTER = "character"
    PROP = "prop"
    EFFECT = "effect"
    BACKGROUND = "background"


class SelectionMode(str, Enum):
    POINT = "point"         # Single positive click
    BBOX = "bounding_box"   # Bounding box selection


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Replacement Config (from TRANSFORM_SPEC.md) ────────────────────────────

class FitMode(str, Enum):
    CONTAIN = "contain"
    COVER = "cover"
    STRETCH = "stretch"


class ClipMode(str, Enum):
    ASSET_ALPHA = "asset_alpha"
    ORIGINAL_MASK = "original_mask"
    INTERSECTION = "intersection"


class ReplacementMode(str, Enum):
    NONE = "none"
    STATIC_ASSET = "static_asset"
    FRAME_SEQUENCE = "frame_sequence"
    KEYFRAME_ASSETS = "keyframe_assets"


class Point2D(BaseModel):
    x: float = 0.0
    y: float = 0.0


class ReplacementConfig(BaseModel):
    """Replacement transform settings matching docs/TRANSFORM_SPEC.md."""
    mode: ReplacementMode = ReplacementMode.STATIC_ASSET
    asset_path: str = Field(default="", alias="assetPath")
    anchor: Point2D = Field(default_factory=Point2D)
    offset: Point2D = Field(default_factory=Point2D)
    scale: float = 1.0
    rotation_offset_deg: float = Field(default=0.0, alias="rotationOffsetDeg")
    opacity: float = 1.0
    fit_mode: FitMode = Field(default=FitMode.CONTAIN, alias="fitMode")
    clip_mode: ClipMode = Field(default=ClipMode.ASSET_ALPHA, alias="clipMode")
    frame_sequence_dir: str = Field(default="", alias="frameSequenceDir")
    frame_sequence_fps: float = Field(default=0.0, alias="frameSequenceFps")

    model_config = {"populate_by_name": True}


# ─── Character Reference Repository ──────────────────────────────────────────

class CharacterPosePaths(BaseModel):
    """Reference image paths for the 6 canonical character poses."""

    sitting: str = "sitting.png"
    standing: str = "standing.png"
    three_quarter: str = "three_quarter.png"
    walking: str = "walking.png"
    talking: str = "talking.png"
    back: str = "back.png"


class CharacterReferencePack(BaseModel):
    """A reference character pack: id, display name, and 6 pose images."""

    character_id: str
    name: str
    poses: CharacterPosePaths


# ─── Object Crop Manifest ────────────────────────────────────────────────────

class ObjectCrop(BaseModel):
    """A single crop image for a tracked object at a frame."""
    frame_index: int
    crop_path: str


class GalleryManifest(BaseModel):
    """Manifest listing all crop images for a tracked object."""
    object_id: str
    project_id: str
    thumbnail_path: str = ""
    crops: list[ObjectCrop] = Field(default_factory=list)


# ─── Video Metadata ──────────────────────────────────────────────────────────

class VideoMetadata(BaseModel):
    """Metadata extracted from source video via ffprobe."""
    width: int
    height: int
    fps: float
    duration_seconds: float
    total_frames: int
    codec: str
    has_audio: bool
    audio_codec: str | None = None
    file_size_bytes: int = 0
    file_path: str = ""


# ─── Scene ───────────────────────────────────────────────────────────────────

class SceneInfo(BaseModel):
    """A detected scene within the video.

    Frame indexing: zero-based, start_frame and end_frame are INCLUSIVE.
    """
    scene_id: int
    start_frame: int        # inclusive, zero-based
    end_frame: int          # inclusive, zero-based
    start_time_sec: float
    end_time_sec: float
    duration_sec: float
    frame_count: int


class SceneStatus(str, Enum):
    PENDING = "pending"      # Chưa làm
    DRAFT = "draft"          # Đang sửa
    APPROVED = "approved"    # Đã duyệt


class SceneDetail(BaseModel):
    """Extended scene info with status and audio path."""
    scene_id: int
    start_frame: int
    end_frame: int
    start_time_sec: float
    end_time_sec: float
    duration_sec: float
    frame_count: int
    status: SceneStatus = SceneStatus.PENDING
    audio_path: str = ""         # relative path to scene audio file
    notes: str = ""


# ─── Selection ────────────────────────────────────────────────────────────────

class SelectionInput(BaseModel):
    """User selection on a frame — point or bounding box.

    Coordinates are in pixel units (origin = top-left of frame).
    frame_index is zero-based, absolute within the scene.
    """
    mode: SelectionMode
    frame_index: int            # Absolute frame index in the scene (zero-based)
    x: float                    # Point x or bbox top-left x (pixels)
    y: float                    # Point y or bbox top-left y (pixels)
    width: float | None = None  # Bbox width (only for bbox mode, pixels)
    height: float | None = None # Bbox height (only for bbox mode, pixels)


# ─── Motion Data ──────────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Axis-aligned bounding box in pixel coordinates."""
    x: float
    y: float
    width: float
    height: float


class Anchor(BaseModel):
    """Anchor point for compositing (0.0–1.0 relative to bbox)."""
    x: float = 0.5  # 0.0 = left edge, 1.0 = right edge
    y: float = 0.5  # 0.0 = top edge, 1.0 = bottom edge


class FrameMotion(BaseModel):
    """Motion data for a single frame.

    Coordinate system: pixel coordinates, origin at top-left.
    Rotation unit: degrees (from cv2.minAreaRect, normalized to [-90, 90]).
    Scale: relative to reference_bbox (1.0 = same size as selection frame).
    Confidence: 0.0–1.0, tracking confidence (1.0 = certain).
    Visibility: True if object is considered present (mask area > threshold).
    Occluded: True if object is known to be behind another object.
    Needs_review: True if tracking quality is uncertain.
    Mask_path: relative path to the binary mask PNG for this frame.
    """
    frame_index: int                # zero-based
    centroid_x: float               # pixels
    centroid_y: float               # pixels
    bbox: BoundingBox               # pixels
    scale_x: float = 1.0            # relative to reference
    scale_y: float = 1.0            # relative to reference
    rotation_deg: float = 0.0       # degrees, [-90, 90]
    opacity: float = 1.0            # 0.0–1.0, fill ratio of bbox
    visibility: bool = True         # object present in frame
    area: float = 0.0               # mask area in pixels
    confidence: float = 1.0         # 0.0–1.0, tracking confidence
    occluded: bool = False          # behind another object
    needs_review: bool = False      # uncertain tracking quality
    mask_path: str | None = None    # relative path to mask PNG


class SceneMotion(BaseModel):
    """Aggregated motion data for an entire scene."""
    scene_id: int
    frames: list[FrameMotion] = Field(default_factory=list)
    reference_bbox: BoundingBox | None = None  # Bbox at selection frame
    tracking_backend: str = "unknown"  # "sam2", "contour", etc.
    model_version: str = ""            # e.g. "sam2.1_hiera_l"
    anchor: Anchor = Field(default_factory=Anchor)


# ─── Object Tracking ─────────────────────────────────────────────────────────

class TrackedObject(BaseModel):
    """An object being tracked across a scene."""
    object_id: str
    name: str
    kind: ObjectKind = ObjectKind.CHARACTER
    selection: SelectionInput
    scene_id: int
    replacement_image: str | None = None  # Path to replacement PNG
    crop_path: str | None = None  # Path to cropped thumbnail PNG
    motion: SceneMotion | None = None
    replacement_config: ReplacementConfig | None = None


# ─── Task Status / Channel Workspace ──────────────────────────────────────────

class TaskStatus(str, Enum):
    DRAFT = "draft"                # ⚪ Bản Nháp
    IN_PROGRESS = "in_progress"    # 🟡 Đang Xử Lý
    READY_TO_STITCH = "ready_to_stitch"  # 🔵 Sẵn sàng ghép
    COMPLETED = "completed"        # 🟢 Hoàn thành


class ChannelWorkspace(BaseModel):
    """A channel workspace grouping related projects."""
    channel_id: str = ""
    name: str = ""
    target_lang: str = "en"
    default_preset_id: str = ""
    created_at: str = ""


# ─── Durable Channel DTOs (S03-T01) ──────────────────────────────────────────

class ChannelRole(str, Enum):
    """Approved channel roles (PERSISTENCE_DOMAIN_CONTRACT §4)."""
    SOURCE = "source"
    PRODUCTION = "production"


class ChannelStatus(str, Enum):
    """Approved channel lifecycle states (contract §4)."""
    ACTIVE = "active"
    ARCHIVED = "archived"


class ChannelData(BaseModel):
    """API DTO for a durable Channel row.

    Never exposes ORM objects or absolute paths.  ``workspace_id`` is the
    explicit ownership key; ``revision`` is the optimistic-concurrency
    token required by every business update (AC4).
    """
    channel_id: str
    workspace_id: str
    name: str
    role: ChannelRole
    description: str = ""
    color: str | None = None
    avatar_artifact_id: str | None = None
    target_language: str | None = None
    default_output_profile: str | None = None
    status: ChannelStatus = ChannelStatus.ACTIVE
    archived_at: str | None = None
    created_at: str
    updated_at: str
    revision: int = 1

    @classmethod
    def from_row(cls, row: Any) -> ChannelData:
        """Map a repository read record (DTO boundary: no ORM escape)."""
        return cls(
            channel_id=row.id,
            workspace_id=row.workspace_id,
            name=row.name,
            role=ChannelRole(row.role),
            description=row.description or "",
            color=row.color,
            avatar_artifact_id=row.avatar_artifact_id,
            target_language=row.target_language,
            default_output_profile=row.default_output_profile,
            status=ChannelStatus(row.status),
            archived_at=_dt_iso_optional(row.archived_at),
            created_at=_dt_iso(row.created_at),
            updated_at=_dt_iso(row.updated_at),
            revision=row.revision,
        )


class ChannelCreate(BaseModel):
    """Create payload (AC1/AC3)."""
    name: str = Field(min_length=1, max_length=200)
    role: ChannelRole = ChannelRole.SOURCE
    description: str = ""
    color: str | None = None
    avatar_artifact_id: str | None = None
    target_language: str | None = None
    default_output_profile: str | None = None

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value


class ChannelUpdate(BaseModel):
    """Update payload — must carry the expected revision (AC4).

    Nullable metadata fields distinguish **omitted** (no change) from
    explicit JSON ``null`` (clear the stored value) via
    ``model_fields_set``.  ``revision`` is required (optimistic
    concurrency).
    """
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    color: str | None = None
    avatar_artifact_id: str | None = None
    target_language: str | None = None
    default_output_profile: str | None = None
    revision: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("name must not be blank")
        return value


class ChannelArchiveRequest(BaseModel):
    """Archive payload — expected revision required (atomic CAS, AC4/AC5)."""
    revision: int = Field(ge=1)


class ChannelListResponse(BaseModel):
    """List response: ``active_only`` excludes archived by default (AC5)."""
    workspace_id: str
    active_only: bool = True
    channels: list[ChannelData] = Field(default_factory=list)


def _dt_iso(value: Any) -> str:
    """Serialize a REQUIRED timestamp as an ISO-8601 UTC string.

    SQLite may return naive datetimes; normalize to UTC-aware so the wire
    format is always ``...Z``-equivalent (``+00:00`` suffix).
    """
    if getattr(value, "tzinfo", None) is None:
        from datetime import UTC

        value = value.replace(tzinfo=UTC)
    return str(value.isoformat())


def _dt_iso_optional(value: Any) -> str | None:
    """Serialize an OPTIONAL timestamp: None → JSON null (never "")."""
    if value is None:
        return None
    return _dt_iso(value)


# ─── Project ──────────────────────────────────────────────────────────────────

#: Approved durable Project lifecycle states (PERSISTENCE_DOMAIN_CONTRACT §4).
PROJECT_STATUS_VALUES = (
    "draft",
    "active",
    "needs_review",
    "rendering",
    "completed",
    "archived",
)


class ProjectStatus(str, Enum):
    """Approved project statuses (contract §4)."""

    DRAFT = "draft"
    ACTIVE = "active"
    NEEDS_REVIEW = "needs_review"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DurableProjectData(BaseModel):
    """API DTO for a durable Project row.

    Never exposes ORM objects or absolute paths.  ``workspace_id`` is the
    explicit ownership key; ``revision`` is the optimistic-concurrency
    token required by every business update (AC4).  Channel references are
    exposed as plain ids (``source_channel_id`` / ``production_channel_id``).
    """

    project_id: str
    workspace_id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.DRAFT
    source_channel_id: str | None = None
    production_channel_id: str | None = None
    default_output_profile: str | None = None
    resume_step: str | None = None
    archived_at: str | None = None
    created_at: str
    updated_at: str
    revision: int = 1

    @classmethod
    def from_row(cls, row: Any) -> DurableProjectData:
        """Map a repository read record (DTO boundary: no ORM escape)."""
        return cls(
            project_id=row.id,
            workspace_id=row.workspace_id,
            name=row.name,
            description=row.description or "",
            status=ProjectStatus(row.status),
            source_channel_id=row.source_channel_id,
            production_channel_id=row.production_channel_id,
            default_output_profile=row.default_output_profile,
            resume_step=row.resume_step,
            archived_at=_dt_iso_optional(row.archived_at),
            created_at=_dt_iso(row.created_at),
            updated_at=_dt_iso(row.updated_at),
            revision=row.revision,
        )


class ProjectCreate(BaseModel):
    """Create payload (AC1/AC2)."""

    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    source_channel_id: str | None = None
    production_channel_id: str | None = None
    default_output_profile: str | None = None
    resume_step: str | None = None

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value


class ProjectUpdate(BaseModel):
    """Update payload — must carry the expected revision (AC4).

    Nullable fields distinguish **omitted** (no change) from explicit
    JSON ``null`` (clear the stored value) via ``model_fields_set``.
    Channel references are nullable/clearable (AC3).
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus | None = None
    source_channel_id: str | None = None
    production_channel_id: str | None = None
    default_output_profile: str | None = None
    resume_step: str | None = None
    revision: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("name must not be blank")
        return value


class ProjectArchiveRequest(BaseModel):
    """Archive payload — expected revision required (atomic CAS, AC4/AC5)."""

    revision: int = Field(ge=1)


class ProjectListResponse(BaseModel):
    """List response: ``active_only`` excludes archived by default (AC5)."""

    workspace_id: str
    active_only: bool = True
    projects: list[DurableProjectData] = Field(default_factory=list)


# ─── Durable Video Item DTOs (S03-T03) ──────────────────────────────────────

#: Approved durable Video Item pipeline states
#: (PERSISTENCE_DOMAIN_CONTRACT §4 ``video_item``).
VIDEO_PIPELINE_STATUS_VALUES = (
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


class VideoItemStatus(str, Enum):
    """Exact approved Video Item pipeline states (contract §4)."""

    IMPORTED = "imported"
    ANALYZING = "analyzing"
    OBJECTS_READY = "objects_ready"
    MAPPING_REQUIRED = "mapping_required"
    DEMO_REQUIRED = "demo_required"
    DEMO_APPROVED = "demo_approved"
    APPLYING_RESKIN = "applying_reskin"
    NEEDS_REVIEW = "needs_review"
    READY_TO_EXPORT = "ready_to_export"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class VideoItemData(BaseModel):
    """API DTO for a durable Video Item row.

    Never exposes ORM objects or absolute paths.  ``workspace_id`` is
    the explicit ownership key; ``revision`` is the optimistic-
    concurrency token required by every business update (AC4).  Probe
    metadata (``duration_ms``, ``width``, ``height``, ``fps_num``,
    ``fps_den``) is read-only in this task (S05 owns import/probing).
    """

    video_item_id: str
    project_id: str
    workspace_id: str
    title: str
    position: int
    status: VideoItemStatus = VideoItemStatus.IMPORTED
    source_artifact_id: str | None = None
    source_channel_id: str | None = None
    duration_ms: int | None = None
    width: int | None = None
    height: int | None = None
    fps_num: int | None = None
    fps_den: int | None = None
    resume_step: str | None = None
    archived_at: str | None = None
    created_at: str
    updated_at: str
    revision: int = 1

    @classmethod
    def from_row(cls, row: Any) -> VideoItemData:
        """Map a repository read record (DTO boundary: no ORM escape)."""
        return cls(
            video_item_id=row.id,
            project_id=row.project_id,
            workspace_id=row.workspace_id,
            title=row.title,
            position=row.position,
            status=VideoItemStatus(row.status),
            source_artifact_id=row.source_artifact_id,
            source_channel_id=row.source_channel_id,
            duration_ms=row.duration_ms,
            width=row.width,
            height=row.height,
            fps_num=row.fps_num,
            fps_den=row.fps_den,
            resume_step=row.resume_step,
            archived_at=_dt_iso_optional(row.archived_at),
            created_at=_dt_iso(row.created_at),
            updated_at=_dt_iso(row.updated_at),
            revision=row.revision,
        )


class VideoItemCreate(BaseModel):
    """Create payload (AC1/AC2).  Position is assigned automatically.

    Probe metadata (``duration_ms``, ``width``, ``height``, ``fps_num``,
    ``fps_den``) is read-only in this task (S05 owns import and media
    probing) and therefore NOT part of the public create payload; the
    request model forbids unknown fields so a client that tries to write
    probe data gets an explicit 422 instead of silent acceptance.  The
    fields remain in the read DTO (``VideoItemData``) for later S05
    population.
    """

    model_config = {"extra": "forbid"}

    title: str = Field(min_length=1, max_length=240)
    source_channel_id: str | None = None
    resume_step: str | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class VideoItemUpdate(BaseModel):
    """Update payload — must carry the expected revision (AC4).

    Nullable fields distinguish **omitted** (no change) from explicit
    JSON ``null`` (clear the stored value) via ``model_fields_set``.
    Generic PATCH can never enter or leave ``archived`` (archive is the
    only removal path); ``status: archived``/``status: active`` from an
    archived row are 422/409 respectively.
    """

    title: str | None = Field(default=None, min_length=1, max_length=240)
    status: VideoItemStatus | None = None
    source_channel_id: str | None = None
    resume_step: str | None = None
    revision: int = Field(ge=1)

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be blank")
        return value


class VideoItemArchiveRequest(BaseModel):
    """Archive payload — expected revision required (atomic CAS, AC4/AC5)."""

    revision: int = Field(ge=1)


class VideoItemReorderRequest(BaseModel):
    """Atomic full-list reorder payload (AC3/AC4).

    Carries the expected Project revision (the Project row is bumped
    once per accepted reorder) and the COMPLETE set of active Video Item
    ids exactly once, in the desired order.  Missing/extra/duplicate or
    cross-project ids are rejected before any write (no partial writes).
    """

    project_revision: int = Field(ge=1)
    video_item_ids: list[str] = Field(min_length=0)


class VideoListResponse(BaseModel):
    """List response: ordered by position; archived excluded by default."""

    project_id: str
    workspace_id: str
    active_only: bool = True
    videos: list[VideoItemData] = Field(default_factory=list)


# ─── Project Summary DTOs (S03-T04) ──────────────────────────────────────────

#: Exact 13-state Video Item pipeline (contract §4) — reused as the
#: ``by_status`` map keys, including zeroes (read-model contract).
VIDEO_SUMMARY_STATUS_VALUES = VIDEO_PIPELINE_STATUS_VALUES


class NextActionCode(str, Enum):
    """Semantic next-action codes returned by the backend (never prose).

    Codes are stable and state-driven; the UI owns localization.  ``none``
    is the honest default when no action is actionable (archived Project,
    no active videos, everything complete).
    """

    NONE = "none"
    ANALYZE_VIDEO = "analyze_video"
    MAP_OBJECTS = "map_objects"
    CREATE_DEMO = "create_demo"
    APPLY_RESKIN = "apply_reskin"
    REVIEW_WORK = "review_work"
    EXPORT_VIDEO = "export_video"
    RETRY_FAILED = "retry_failed"


class NextActionBlocker(str, Enum):
    """Blocker codes for disabled future capabilities (capability honesty).

    Backend returns codes only; unavailable future capabilities remain
    disabled with an explicit blocker instead of being advertised as
    enabled (AC4).
    """

    QC_UNAVAILABLE = "qc_unavailable"
    OUTPUT_UNAVAILABLE = "output_unavailable"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"


class NextActionData(BaseModel):
    """One deterministic semantic next action (AC4)."""

    code: NextActionCode = NextActionCode.NONE
    video_item_id: str | None = None
    enabled: bool = False
    blocker: NextActionBlocker | None = None


class ChannelSummaryData(BaseModel):
    """Display-only Channel reference (id + name; no role revalidation).

    Archived referenced Channels remain visible (AC8); the summary never
    revalidates a channel role or status.
    """

    channel_id: str
    name: str
    role: str
    status: str


class VideoCountsData(BaseModel):
    """Video Item counts with all 13 statuses including zeroes (AC3).

    ``completion_percent`` is ``completed / active * 100`` and is zero
    when there are no active videos (CORRECTION P1.3) — the DTO never
    invents ordinal pipeline progress.
    """

    active: int = 0
    archived: int = 0
    total: int = 0
    completed: int = 0
    attention: int = 0
    completion_percent: float = 0.0
    by_status: dict[str, int] = Field(default_factory=dict)


class ActiveJobData(BaseModel):
    """A bounded newest-first active Job owned by the Project or its
    Video Items (AC5).  Exposes no internal/error JSON."""

    job_id: str
    job_type: str
    owner_type: str
    owner_id: str
    state: str
    progress: float = 0.0
    created_at: str | None = None


class StorageData(BaseModel):
    """Known managed storage for the Project's owned Artifacts (AC6)."""

    total_bytes: int = 0
    artifact_count: int = 0
    ready_count: int = 0
    missing_count: int = 0
    trash_count: int = 0
    unknown_size_count: int = 0


class ProjectSummaryData(BaseModel):
    """Read-only Project summary for the dashboard (AC1/AC2).

    Never exposes ORM objects, internal JSON, absolute paths, or
    sensitive job errors.  ``workspace_id`` is the explicit ownership
    key; ``revision`` is the optimistic-concurrency token.
    """

    project_id: str
    workspace_id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.DRAFT
    revision: int = 1
    created_at: str
    updated_at: str
    archived_at: str | None = None
    source_channel: ChannelSummaryData | None = None
    production_channel: ChannelSummaryData | None = None
    video_counts: VideoCountsData
    next_action: NextActionData
    active_jobs: list[ActiveJobData] = Field(default_factory=list)
    active_job_count: int = 0
    last_activity_at: str | None = None
    storage: StorageData

    @classmethod
    def from_record(cls, record: Any) -> ProjectSummaryData:
        """Map a repository read record (DTO boundary: no ORM escape)."""
        return cls(
            project_id=record.project_id,
            workspace_id=record.workspace_id,
            name=record.name,
            description=record.description or "",
            status=ProjectStatus(record.status),
            revision=record.revision,
            created_at=_dt_iso(record.created_at),
            updated_at=_dt_iso(record.updated_at),
            archived_at=_dt_iso_optional(record.archived_at),
            source_channel=_channel_summary(record.source_channel),
            production_channel=_channel_summary(record.production_channel),
            video_counts=VideoCountsData(
                active=record.video_counts.active,
                archived=record.video_counts.archived,
                total=record.video_counts.total,
                completed=record.video_counts.completed,
                attention=record.video_counts.attention,
                completion_percent=record.video_counts.completion_percent,
                by_status=record.video_counts.by_status,
            ),
            next_action=NextActionData(
                code=NextActionCode(record.next_action),
                video_item_id=record.next_action_video_item_id,
                enabled=record.next_action_enabled,
                blocker=(
                    NextActionBlocker(record.next_action_blocker)
                    if record.next_action_blocker is not None
                    else None
                ),
            ),
            active_jobs=[
                ActiveJobData(
                    job_id=job.job_id,
                    job_type=job.job_type,
                    owner_type=job.owner_type,
                    owner_id=job.owner_id,
                    state=job.state,
                    progress=job.progress,
                    created_at=_dt_iso_optional(job.created_at),
                )
                for job in record.active_jobs
            ],
            active_job_count=record.active_job_count,
            last_activity_at=_dt_iso_optional(record.last_activity_at),
            storage=StorageData(
                total_bytes=record.storage.total_bytes,
                artifact_count=record.storage.artifact_count,
                ready_count=record.storage.ready_count,
                missing_count=record.storage.missing_count,
                trash_count=record.storage.trash_count,
                unknown_size_count=record.storage.unknown_size_count,
            ),
        )


def _channel_summary(
    record: Any,
) -> ChannelSummaryData | None:
    """Map a Channel display record (None stays None)."""
    if record is None:
        return None
    return ChannelSummaryData(
        channel_id=record.channel_id,
        name=record.name,
        role=record.role,
        status=record.status,
    )


class ProjectSummaryListResponse(BaseModel):
    """Collection response with deterministic ordering/pagination (AC7).

    ``active_only`` reflects the default filter (archived excluded);
    ``limit``/``offset`` echo the request so the client can paginate
    deterministically.  ``total`` is the number of rows on the requested
    page, and ``has_more`` is ``True`` only when the page is full (a
    bound, not an estimate).
    """

    workspace_id: str
    active_only: bool = True
    status: str | None = None
    limit: int
    offset: int
    total: int
    has_more: bool = False
    summaries: list[ProjectSummaryData] = Field(default_factory=list)


class ProjectData(BaseModel):
    """Top-level project state, serializable to JSON.

    Version history:
    - 1.0.0: Initial schema (Milestone 0)
    - 2.0.0: Added confidence, occluded, needs_review, mask_path,
              anchor, tracking_backend, model_version
    """
    version: str = "2.0.0"
    name: str
    source_video: str
    video_metadata: VideoMetadata | None = None
    scenes: list[SceneInfo] = Field(default_factory=list)
    scene_details: list[SceneDetail] = Field(default_factory=list)
    objects: list[TrackedObject] = Field(default_factory=list)
    channel_id: str = ""
    task_status: str = "draft"
    created_at: str = ""
    updated_at: str = ""


# ─── Job ──────────────────────────────────────────────────────────────────────

class JobInfo(BaseModel):
    """Status of a background processing job."""
    job_id: str
    state: JobState = JobState.QUEUED
    progress: float = 0.0
    message: str = ""
    result_path: str | None = None
    error: str | None = None
    job_type: str = ""


# ─── Audio Dubbing ──────────────────────────────────────────────────────────

class DubbingConfig(BaseModel):
    """Configuration for dubbing a scene."""
    source_lang: str = "vi"
    target_lang: str = "en"
    whisper_model: str = "base"  # tiny/base/small/medium
    tts_voice: str = "en-US-AriaNeural"


class DubbingResult(BaseModel):
    """Result of dubbing a scene."""
    vocal_track: str = ""
    bgm_track: str = ""
    original_srt: str = ""
    translated_srt: str = ""
    final_audio: str = ""
    segments: list[dict[str, object]] = Field(default_factory=list)


# ─── Migration ────────────────────────────────────────────────────────────────

def migrate_v1_to_v2(data: dict[str, object]) -> dict[str, object]:
    """Migrate a v1.0.0 project dict to v2.0.0.

    Adds default values for new fields without breaking existing data.
    """
    version = data.get("version", "1.0.0")
    if not isinstance(version, str) or version >= "2.0.0":
        return data  # Already v2+

    data["version"] = "2.0.0"

    objects = data.get("objects", [])
    if isinstance(objects, list):
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            motion = obj.get("motion")
            if isinstance(motion, dict):
                motion.setdefault("tracking_backend", "unknown")
                motion.setdefault("model_version", "")
                motion.setdefault("anchor", {"x": 0.5, "y": 0.5})
                frames = motion.get("frames", [])
                if isinstance(frames, list):
                    for frame in frames:
                        if not isinstance(frame, dict):
                            continue
                        frame.setdefault("confidence", 1.0)
                        frame.setdefault("occluded", False)
                        frame.setdefault("needs_review", False)
                        frame.setdefault("mask_path", None)
            obj.setdefault("replacement_config", None)

    return data
