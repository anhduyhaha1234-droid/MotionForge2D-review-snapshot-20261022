"""Read-only legacy JSON inventory and import preview (S01-T04).

Pure read-only inspection of an explicitly supplied legacy root.  It never
touches repo-root data by default: the caller must pass the legacy root, the
channels file and the project root explicitly.  Nothing here creates a
database, writes any source file, follows references outside the supplied
legacy root, or imports ORM/engine modules.

Design anchors (see ``docs/architecture/LEGACY_IMPORT_PREVIEW.md``):

- Explicit inputs only; no implicit repo-root discovery.
- Defensive parsing: one corrupt item becomes an issue, never an abort.
- Stable issue model: severity/code/location/message; blockers separated
  from warnings.
- Deterministic proposed identity mappings (uuid5 over the legacy id).
- Unknown JSON fields are collected into audit data, never dropped.
- SHA-256 and mtime are recorded per source before and after preview;
  repeated previews must be byte-identical.
- Serialization to JSON is caller-controlled via ``to_json()``.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

__all__ = [
    "BLOCKER",
    "INFO",
    "WARNING",
    "LegacyPreviewError",
    "LegacyPreview",
    "LegacyPreviewer",
    "PathCheck",
    "PathIssue",
    "PreviewIssue",
]

# ── Issue severities ──────────────────────────────────────────────────────────

BLOCKER = "blocker"
WARNING = "warning"
INFO = "info"

# ── Issue codes ───────────────────────────────────────────────────────────────

CODE_CHANNELS_NOT_LIST = "CHANNELS_NOT_LIST"
CODE_CHANNEL_ITEM_NOT_OBJECT = "CHANNEL_ITEM_NOT_OBJECT"
CODE_CHANNEL_MISSING_ID = "CHANNEL_MISSING_ID"
CODE_CHANNEL_DUPLICATE_ID = "CHANNEL_DUPLICATE_ID"
CODE_PROJECT_DIR_NO_JSON = "PROJECT_DIR_NO_JSON"
CODE_PROJECTS_ROOT_UNSAFE = "PROJECTS_ROOT_UNSAFE"
CODE_PROJECT_JSON_INVALID = "PROJECT_JSON_INVALID"
CODE_PROJECT_SCHEMA = "PROJECT_SCHEMA"
CODE_PROJECT_PATH_UNSAFE = "PROJECT_PATH_UNSAFE"
CODE_PROJECT_SOURCE_ABSOLUTE = "PROJECT_SOURCE_ABSOLUTE"
CODE_PROJECT_SOURCE_MISSING = "PROJECT_SOURCE_MISSING"
CODE_PROJECT_REFERENCE_UNSAFE = "PROJECT_REFERENCE_UNSAFE"
CODE_PROJECT_REFERENCE_MISSING = "PROJECT_REFERENCE_MISSING"
CODE_PROJECT_CHANNEL_UNKNOWN = "PROJECT_CHANNEL_UNKNOWN"
CODE_PROJECT_DUPLICATE_OBJECT_ID = "PROJECT_DUPLICATE_OBJECT_ID"
CODE_PROJECT_DUPLICATE_SCENE_ID = "PROJECT_DUPLICATE_SCENE_ID"
CODE_PROJECT_SCENE_RANGE = "PROJECT_SCENE_RANGE"

#: Known project.json root fields (v2.0.0 schema; anything else is unknown).
PROJECT_KNOWN_FIELDS = {
    "version",
    "name",
    "source_video",
    "video_metadata",
    "scenes",
    "scene_details",
    "objects",
    "channel_id",
    "task_status",
    "created_at",
    "updated_at",
}

# ── Deterministic identity mapping ────────────────────────────────────────────

#: Namespace for legacy identity mapping; stable across machines.
_LEGACY_ID_NAMESPACE = "motionforge:legacy-import"


def _legacy_id_key(kind: str, legacy_id: str) -> str:
    return f"{kind}:{legacy_id}"


def _proposed_id(kind: str, legacy_id: str) -> str:
    """Deterministic proposed UUID for a legacy id (uuid5, never reused)."""
    return str(uuid5(NAMESPACE_URL, _legacy_id_key(kind, legacy_id)))


# ── Small records ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PreviewIssue:
    """A stable, actionable inventory issue."""

    severity: str
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass(frozen=True)
class PathCheck:
    """Checksum + mtime evidence for one source file."""

    path: str
    sha256: str
    size_bytes: int
    mtime_ns: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
        }


@dataclass(frozen=True)
class PathIssue:
    """A referenced path inside the legacy root and its safety result."""

    kind: str
    raw: str
    exists: bool
    inside_root: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "raw": self.raw,
            "exists": self.exists,
            "inside_root": self.inside_root,
        }


# ── Main result ───────────────────────────────────────────────────────────────


@dataclass
class LegacyPreview:
    """Deterministic read-only inventory result."""

    legacy_root: str
    channels: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    issues: list[PreviewIssue] = field(default_factory=list)
    source_checksums: list[PathCheck] = field(default_factory=list)
    source_checksums_after: list[PathCheck] = field(default_factory=list)
    unknown_fields: dict[str, list[str]] = field(default_factory=dict)
    referenced_files: list[PathIssue] = field(default_factory=list)
    #: Per-project object ID mapping; project-scoped so identical legacy
    #: object IDs in different projects never collide (PM correction 4).
    object_id_mapping: dict[str, dict[str, str]] = field(default_factory=dict)

    #: Backwards-compatible accessors for callers/tests written against the
    #: ``legacy_ids``/``id_mapping`` shape.  Kept as properties so the
    #: serialized DTO stays exactly as the architecture doc defines it.
    @property
    def legacy_ids(self) -> dict[str, list[str]]:
        """Aggregate legacy ids grouped by kind (channels/projects/objects)."""
        return {
            "channels": [c["legacy_id"] for c in self.channels],
            "projects": [p["legacy_id"] for p in self.projects],
            "objects": [
                o["legacy_id"] for p in self.projects for o in p["objects"]
            ],
        }

    @property
    def id_mapping(self) -> dict[str, dict[str, str]]:
        """Aggregate proposed mapping grouped by kind."""
        return {
            "channels": {c["legacy_id"]: c["proposed_id"] for c in self.channels},
            "projects": {p["legacy_id"]: p["proposed_id"] for p in self.projects},
            "objects": {
                o["legacy_id"]: o["proposed_id"]
                for p in self.projects
                for o in p["objects"]
            },
        }

    @property
    def blockers(self) -> list[PreviewIssue]:
        """Only blocker-severity issues (separated from warnings)."""
        return [i for i in self.issues if i.severity == BLOCKER]

    @property
    def warnings(self) -> list[PreviewIssue]:
        """Only warning/info-severity issues."""
        return [i for i in self.issues if i.severity != BLOCKER]

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serializable DTO (caller controls serialization)."""
        return {
            "legacy_root": self.legacy_root,
            "channels": self.channels,
            "projects": self.projects,
            "issues": [i.as_dict() for i in self.issues],
            "source_checksums": [c.as_dict() for c in self.source_checksums],
            "source_checksums_after": [
                c.as_dict() for c in self.source_checksums_after
            ],
            "unknown_fields": dict(sorted(self.unknown_fields.items())),
            "referenced_files": [p.as_dict() for p in self.referenced_files],
            "object_id_mapping": {
                str(project_id): dict(sorted(objects.items()))
                for project_id, objects in sorted(self.object_id_mapping.items())
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the DTO to JSON (caller-controlled, deterministic)."""
        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
        ) + "\n"


class LegacyPreviewError(RuntimeError):
    """Raised for invalid explicit inputs (never for data content)."""


# ── Core class ────────────────────────────────────────────────────────────────


class LegacyPreviewer:
    """Builds a read-only legacy inventory preview.

    All inputs are explicit.  ``legacy_root`` is the containment boundary:
    references are only ever reported, and unsafe references are blockers
    that are never followed.  No file inside ``legacy_root`` is modified and
    no database is created.
    """

    def __init__(
        self,
        legacy_root: str | Path,
        channels_file: str | Path | None = None,
        projects_root: str | Path | None = None,
    ) -> None:
        if not legacy_root:
            raise LegacyPreviewError("legacy_root must not be empty")
        self._legacy_root = Path(legacy_root)
        try:
            self._legacy_root_resolved = self._legacy_root.resolve()
        except OSError as exc:
            raise LegacyPreviewError(
                f"Cannot resolve legacy root {self._legacy_root}: {exc}"
            ) from exc
        if not self._legacy_root_resolved.is_dir():
            raise LegacyPreviewError(
                f"Legacy root does not exist or is not a directory: "
                f"{self._legacy_root_resolved}"
            )
        # Defaults resolve inside the explicit legacy root (never repo root).
        self._channels_file = (
            Path(channels_file)
            if channels_file is not None
            else self._legacy_root_resolved / "channels.json"
        )
        self._projects_root = (
            Path(projects_root)
            if projects_root is not None
            else self._legacy_root_resolved / "projects"
        )
        #: Per-project object ID mapping (project legacy id -> object mapping).
        self._object_id_mapping: dict[str, dict[str, str]] = {}
        # Per-run mutable state (reset by run()).
        self._referenced_file_records: list[PathIssue] = []
        self._pending_issues: list[PreviewIssue] = []
        self._unknown_fields: dict[str, list[str]] = {}
        self._known_channels: set[str] = set()

    # ── Public API ──────────────────────────────────────────────────────────

    def run(self) -> LegacyPreview:
        """Inventory the legacy root and return a deterministic preview."""
        self._referenced_file_records = []
        self._pending_issues = []
        self._unknown_fields = {}
        self._known_channels = set()
        self._object_id_mapping = {}
        before = self._checksum_sources()
        channels, ch_issues, ch_unknown = self._inventory_channels()
        self._known_channels = {c["legacy_id"] for c in channels}
        projects, pr_issues, pr_unknown = self._inventory_projects()
        issues = ch_issues + pr_issues + self._pending_issues
        issues.sort(key=lambda i: (i.severity, i.code, i.location, i.message))
        unknown_fields = {**ch_unknown, **pr_unknown, **self._unknown_fields}
        for kind in unknown_fields:
            unknown_fields[kind] = sorted(set(unknown_fields[kind]))
        # Deterministic ordering of referenced files.
        referenced_files = sorted(
            self._referenced_file_records,
            key=lambda p: (p.kind, p.raw),
        )
        return LegacyPreview(
            legacy_root=str(self._legacy_root_resolved),
            channels=channels,
            projects=projects,
            issues=issues,
            source_checksums=before,
            source_checksums_after=self._checksum_sources(),
            unknown_fields=unknown_fields,
            referenced_files=referenced_files,
            object_id_mapping=self._object_id_mapping,
        )

    # ── Source integrity ────────────────────────────────────────────────────

    def _channels_source_safe(self) -> bool:
        """True iff the channels source may be read (exists and is contained).

        A missing file is safe (read would fail with an empty inventory
        anyway); a file that resolves outside the legacy root is never read.
        """
        if not self._channels_file.exists():
            return False
        return self._path_inside_root(str(self._channels_file))

    def _checksum_sources(self) -> list[PathCheck]:
        """SHA-256 + size + mtime for every source file (byte-identical proof).

        Source files are never followed outside the legacy root: a symlinked
        ``channels.json`` or ``project.json`` is a blocker, never read.
        The projects root itself is containment-checked before any
        enumeration, so an explicit or symlinked outside root is never
        enumerated either (PM correction 2).
        """
        issues: list[PreviewIssue] = []
        sources: list[Path] = []
        if self._channels_source_safe():
            sources.append(self._channels_file)
        elif self._channels_file.exists():
            issues.append(
                PreviewIssue(
                    BLOCKER,
                    CODE_CHANNELS_NOT_LIST,
                    str(self._channels_file),
                    "Channels file resolves outside the legacy root",
                )
            )
        projects_dir = self._projects_root
        if self._projects_root_safe():
            for proj_dir in sorted(projects_dir.iterdir()):
                if not proj_dir.is_dir():
                    continue
                candidate = proj_dir / "project.json"
                if not candidate.exists():
                    continue
                if self._path_inside_root(str(candidate)):
                    sources.append(candidate)
                else:
                    issues.append(
                        PreviewIssue(
                            BLOCKER,
                            CODE_PROJECT_JSON_INVALID,
                            str(candidate),
                            "project.json resolves outside the legacy root",
                        )
                    )
        elif projects_dir.exists():
            issues.append(
                PreviewIssue(
                    BLOCKER,
                    CODE_PROJECTS_ROOT_UNSAFE,
                    str(projects_dir),
                    "Projects root resolves outside the legacy root; "
                    "never enumerated or read",
                )
            )
        checks: list[PathCheck] = []
        for path in sources:
            stat = path.stat()
            checks.append(
                PathCheck(
                    path=str(path),
                    sha256=self._sha256(path),
                    size_bytes=stat.st_size,
                    mtime_ns=stat.st_mtime_ns,
                )
            )
        self._pending_issues.extend(issues)
        return checks

    def _projects_root_safe(self) -> bool:
        """True iff the projects root may be enumerated.

        The path must be a directory that resolves inside the legacy root.
        A symlinked outside root (which ``Path.is_dir()`` would happily
        follow) is therefore never enumerated.
        """
        return self._projects_root.is_dir() and self._path_inside_root(
            str(self._projects_root)
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    # ── Channels ────────────────────────────────────────────────────────────

    def _inventory_channels(
        self,
    ) -> tuple[list[dict[str, Any]], list[PreviewIssue], dict[str, list[str]]]:
        if not self._channels_source_safe():
            # Reject before any read: a source that resolves outside the
            # legacy root (e.g. a symlink) must never be opened (PM
            # correction 1); the blocker is already recorded by
            # _checksum_sources().
            return [], [], {}
        issues: list[PreviewIssue] = []
        unknown: dict[str, list[str]] = {}
        try:
            raw = json.loads(self._channels_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(
                PreviewIssue(
                    BLOCKER,
                    CODE_CHANNELS_NOT_LIST,
                    str(self._channels_file),
                    f"Channels file is not valid JSON: {exc}",
                )
            )
            return [], issues, unknown
        except UnicodeDecodeError as exc:
            issues.append(
                PreviewIssue(
                    BLOCKER,
                    CODE_CHANNELS_NOT_LIST,
                    str(self._channels_file),
                    f"Channels file is not valid UTF-8: {exc}",
                )
            )
            return [], issues, unknown

        if not isinstance(raw, list):
            issues.append(
                PreviewIssue(
                    BLOCKER,
                    CODE_CHANNELS_NOT_LIST,
                    str(self._channels_file),
                    "Expected a JSON list of channel objects",
                )
            )
            return [], issues, unknown

        known = {"channel_id", "name", "target_lang", "default_preset_id", "created_at"}
        seen: set[str] = set()
        channels: list[dict[str, Any]] = []
        for index, item in enumerate(raw):
            location = f"{self._channels_file}[{index}]"
            if not isinstance(item, dict):
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_CHANNEL_ITEM_NOT_OBJECT,
                        location,
                        f"Channel entry {index} is not an object; skipped",
                    )
                )
                continue
            legacy_id = item.get("channel_id", "")
            if not isinstance(legacy_id, str) or not legacy_id:
                issues.append(
                    PreviewIssue(
                        BLOCKER,
                        CODE_CHANNEL_MISSING_ID,
                        location,
                        "Channel entry has no non-empty string channel_id",
                    )
                )
                continue
            if legacy_id in seen:
                issues.append(
                    PreviewIssue(
                        BLOCKER,
                        CODE_CHANNEL_DUPLICATE_ID,
                        location,
                        f"Duplicate channel_id {legacy_id!r}",
                    )
                )
                continue
            seen.add(legacy_id)
            extra = sorted(set(item) - known)
            if extra:
                unknown.setdefault("channel", [])
                unknown["channel"].extend(extra)
            channels.append(
                {
                    "legacy_id": legacy_id,
                    "proposed_id": _proposed_id("channel", legacy_id),
                    "name": str(item.get("name", "")),
                    "target_lang": str(item.get("target_lang", "")),
                    "default_preset_id": str(item.get("default_preset_id", "")),
                    "created_at": str(item.get("created_at", "")),
                }
            )
        for kind in unknown:
            unknown[kind] = sorted(set(unknown[kind]))
        return channels, issues, unknown

    # ── Projects ────────────────────────────────────────────────────────────

    def _inventory_projects(
        self,
    ) -> tuple[list[dict[str, Any]], list[PreviewIssue], dict[str, list[str]]]:
        issues: list[PreviewIssue] = []
        unknown: dict[str, list[str]] = {}
        if not self._projects_root_safe():
            # Never enumerate/read an outside or symlinked projects root
            # (PM correction 2); the blocker is already recorded by
            # _checksum_sources().
            return [], issues, unknown

        projects: list[dict[str, Any]] = []
        for proj_dir in sorted(self._projects_root.iterdir()):
            if not proj_dir.is_dir():
                continue
            proj_json = proj_dir / "project.json"
            location = str(proj_json)
            if not proj_json.exists():
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_PROJECT_DIR_NO_JSON,
                        location,
                        "Project directory has no project.json; skipped",
                    )
                )
                continue
            if not self._path_inside_root(str(proj_json)):
                # Already blocked in _checksum_sources; never read a source
                # that resolves outside the legacy root.
                continue
            try:
                data = json.loads(proj_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(
                    PreviewIssue(
                        BLOCKER,
                        CODE_PROJECT_JSON_INVALID,
                        location,
                        f"project.json is not valid JSON: {exc}",
                    )
                )
                continue
            except UnicodeDecodeError as exc:
                issues.append(
                    PreviewIssue(
                        BLOCKER,
                        CODE_PROJECT_JSON_INVALID,
                        location,
                        f"project.json is not valid UTF-8: {exc}",
                    )
                )
                continue
            if not isinstance(data, dict):
                issues.append(
                    PreviewIssue(
                        BLOCKER,
                        CODE_PROJECT_SCHEMA,
                        location,
                        "project.json root must be a JSON object",
                    )
                )
                continue

            # Project-root unknown fields are preserved in audit data.
            root_extra = sorted(set(data) - PROJECT_KNOWN_FIELDS)
            if root_extra:
                self._unknown_fields.setdefault("project", [])
                self._unknown_fields["project"].extend(root_extra)

            legacy_id = proj_dir.name
            scenes_raw = data.get("scenes")
            objects_raw = data.get("objects")
            scene_count = len(scenes_raw) if isinstance(scenes_raw, list) else 0
            object_count = len(objects_raw) if isinstance(objects_raw, list) else 0
            entry: dict[str, Any] = {
                "legacy_id": legacy_id,
                "proposed_id": _proposed_id("project", legacy_id),
                "name": str(data.get("name", "")),
                "task_status": str(data.get("task_status", "draft")),
                "channel_id": str(data.get("channel_id", "")),
                "created_at": str(data.get("created_at", "")),
                "updated_at": str(data.get("updated_at", "")),
                "version": str(data.get("version", "")),
                "scene_count": scene_count,
                "object_count": object_count,
                "scenes": [],
                "objects": [],
                "source": {
                    "video": str(data.get("source_video", "")),
                    "inside_root": False,
                    "exists": False,
                    "checksum": None,
                    "mtime_ns": None,
                },
            }

            # Source video reference (may be absolute in production data).
            source_raw = data.get("source_video", "")
            if not isinstance(source_raw, str):
                source_raw = str(source_raw)
            source_info = self._inspect_path("source_video", source_raw)
            if source_info.inside_root and source_info.exists:
                try:
                    stat = (self._legacy_root_resolved / source_info.raw).stat()
                    entry["source"]["exists"] = True
                    entry["source"]["checksum"] = self._sha256(
                        self._legacy_root_resolved / source_info.raw
                    )
                    entry["source"]["mtime_ns"] = stat.st_mtime_ns
                except OSError:
                    entry["source"]["exists"] = False
            entry["source"]["inside_root"] = source_info.inside_root
            self._record_path(source_info)
            if not source_raw:
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_PROJECT_SOURCE_MISSING,
                        location,
                        "source_video is empty; cannot be checked",
                    )
                )
            elif not source_info.inside_root:
                issues.append(
                    PreviewIssue(
                        BLOCKER,
                        CODE_PROJECT_SOURCE_ABSOLUTE,
                        location,
                        f"source_video is not inside the legacy root: "
                        f"{source_raw!r}",
                    )
                )
            elif not source_info.exists:
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_PROJECT_SOURCE_MISSING,
                        location,
                        f"Referenced source video missing: {source_raw!r}",
                    )
                )

            # Scene checks (scenes may be null/scalar/object; never crash).
            scenes_raw = data.get("scenes")
            scene_ids: set[int] = set()
            scene_ok = True
            if isinstance(scenes_raw, list):
                for scene in scenes_raw:
                    if not isinstance(scene, dict):
                        scene_ok = False
                        break
                    scene_id = scene.get("scene_id")
                    start = scene.get("start_frame")
                    end = scene.get("end_frame")
                    if (
                        not isinstance(scene_id, int)
                        or not isinstance(start, int)
                        or not isinstance(end, int)
                        or start < 0
                        or end < start
                    ):
                        scene_ok = False
                        break
                    if scene_id in scene_ids:
                        issues.append(
                            PreviewIssue(
                                WARNING,
                                CODE_PROJECT_DUPLICATE_SCENE_ID,
                                location,
                                f"Duplicate scene_id {scene_id!r}",
                            )
                        )
                    scene_ids.add(scene_id)
                if not scene_ok:
                    issues.append(
                        PreviewIssue(
                            WARNING,
                            CODE_PROJECT_SCENE_RANGE,
                            location,
                            "Scene list contains an invalid entry (non-object, "
                            "negative or inverted frame range, or duplicate "
                            "scene_id); scene validity not guaranteed",
                        )
                    )
            else:
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_PROJECT_SCENE_RANGE,
                        location,
                        "scenes is not a list",
                    )
                )

            # Object checks (objects may be null/scalar/object; never crash).
            objects_raw = data.get("objects")
            object_ids: set[str] = set()
            if isinstance(objects_raw, list):
                for obj in objects_raw:
                    if not isinstance(obj, dict):
                        continue
                    object_id = obj.get("object_id", "")
                    if not isinstance(object_id, str) or not object_id:
                        continue
                    if object_id in object_ids:
                        issues.append(
                            PreviewIssue(
                                WARNING,
                                CODE_PROJECT_DUPLICATE_OBJECT_ID,
                                location,
                                f"Duplicate object_id {object_id!r}",
                            )
                        )
                    object_ids.add(object_id)
                    obj_entry = self._inventory_object(
                        legacy_id, object_id, obj, location
                    )
                    entry["objects"].append(obj_entry)
                    self._object_id_mapping.setdefault(legacy_id, {})[
                        object_id
                    ] = obj_entry["proposed_id"]
            else:
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_PROJECT_SCHEMA,
                        location,
                        "objects is not a list",
                    )
                )

            projects.append(entry)

        # Cross-check project → channel references against inventory.
        known_channels = self._known_channels
        for entry in projects:
            channel_id = entry["channel_id"]
            if channel_id and channel_id not in known_channels:
                issues.append(
                    PreviewIssue(
                        WARNING,
                        CODE_PROJECT_CHANNEL_UNKNOWN,
                        entry["legacy_id"],
                        f"Project references unknown channel {channel_id!r}",
                    )
                )
        return projects, issues, unknown

    def _inventory_object(
        self, project_id: str, object_id: str, obj: dict[str, Any], location: str
    ) -> dict[str, Any]:
        """Inventory a single tracked object and its referenced paths.

        Proposed identity is project-scoped: two projects may both contain
        ``object_id="object_1"`` and still receive different deterministic
        IDs (PM correction 4).
        """
        known = {
            "object_id",
            "name",
            "kind",
            "selection",
            "scene_id",
            "replacement_image",
            "crop_path",
            "motion",
            "replacement_config",
        }
        extra = sorted(set(obj) - known)
        if extra:
            self._unknown_fields.setdefault("object", [])
            self._unknown_fields["object"].extend(extra)

        refs: list[dict[str, Any]] = []
        for kind, key in (
            ("replacement_image", "replacement_image"),
            ("crop_path", "crop_path"),
            ("asset_path", "replacement_config.asset_path"),
        ):
            raw = self._nested_get(obj, key)
            if not isinstance(raw, str) or not raw:
                continue
            path_info = self._inspect_path(kind, raw)
            self._record_path(path_info)
            refs.append(
                {
                    "kind": kind,
                    "raw": raw,
                    "inside_root": path_info.inside_root,
                    "exists": path_info.exists,
                }
            )
            if not path_info.inside_root:
                self._add_issue(
                    BLOCKER,
                    CODE_PROJECT_REFERENCE_UNSAFE,
                    location,
                    f"{kind} reference escapes the legacy root: {raw!r}",
                )
            elif not path_info.exists:
                self._add_issue(
                    WARNING,
                    CODE_PROJECT_REFERENCE_MISSING,
                    location,
                    f"{kind} reference missing: {raw!r}",
                )

        motion = obj.get("motion")
        frame_count = 0
        if isinstance(motion, dict):
            frames = motion.get("frames", [])
            if isinstance(frames, list):
                frame_count = len(frames)
                for frame in frames:
                    if isinstance(frame, dict):
                        mask_path = frame.get("mask_path")
                        if isinstance(mask_path, str) and mask_path:
                            path_info = self._inspect_path("mask_path", mask_path)
                            self._record_path(path_info)
                            refs.append(
                                {
                                    "kind": "mask_path",
                                    "raw": mask_path,
                                    "inside_root": path_info.inside_root,
                                    "exists": path_info.exists,
                                }
                            )
                            if not path_info.inside_root:
                                self._add_issue(
                                    BLOCKER,
                                    CODE_PROJECT_REFERENCE_UNSAFE,
                                    location,
                                    f"mask_path reference escapes the legacy "
                                    f"root: {mask_path!r}",
                                )
                            elif not path_info.exists:
                                self._add_issue(
                                    WARNING,
                                    CODE_PROJECT_REFERENCE_MISSING,
                                    location,
                                    f"mask_path reference missing: {mask_path!r}",
                                )

        return {
            "legacy_id": object_id,
            "proposed_id": _proposed_id("object", f"{project_id}:{object_id}"),
            "name": str(obj.get("name", "")),
            "kind": str(obj.get("kind", "character")),
            "scene_id": str(obj.get("scene_id", "")),
            "references": refs,
            "frame_count": frame_count,
        }

    # ── Shared helpers ──────────────────────────────────────────────────────

    def _path_inside_root(self, raw: Any) -> bool:
        if not isinstance(raw, str) or not raw:
            return False
        try:
            candidate = (self._legacy_root_resolved / raw).resolve()
        except OSError:
            return False
        try:
            common = os.path.commonpath([str(candidate), str(self._legacy_root_resolved)])
        except ValueError:
            return False
        return common == str(self._legacy_root_resolved)

    def _inspect_path(self, kind: str, raw: str) -> PathIssue:
        """Inspect a raw reference.  Never follows it outside the root."""
        inside = self._path_inside_root(raw)
        exists = False
        if inside:
            exists = (self._legacy_root_resolved / raw).is_file()
        return PathIssue(kind=kind, raw=raw, exists=exists, inside_root=inside)

    def _record_path(self, info: PathIssue) -> None:
        self._referenced_file_records.append(info)

    @staticmethod
    def _nested_get(obj: dict[str, Any], dotted: str) -> Any:
        current: Any = obj
        for part in dotted.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _add_issue(
        self, severity: str, code: str, location: str, message: str
    ) -> None:
        self._pending_issues.append(PreviewIssue(severity, code, location, message))
