"""Transactional legacy JSON import with backup and audit (S01-T05).

This module implements the S01-T05 transactional import contract:

- An import requires an explicit :class:`LegacyPreview` (S01-T04), an
  initialized SQLite session factory, an explicit workspace ID, a managed
  backup root and a confirmation token derived from preview content.
- Preflight refuses previews with blockers, changed source checksums/mtime,
  unsafe or missing referenced files, a wrong confirmation token or an
  unsupported schema version — all before any database business write.
- Before any DB business rows, all inventoried source JSON and safe
  referenced files are copied into a collision-safe immutable backup
  directory using atomic writes; a manifest records source locator,
  checksum, size and backup relative path.
- Source checksums are revalidated immediately before the transaction.
- One transaction creates/reuses the workspace and imports channels,
  projects, one legacy VideoItem per project, valid scenes, source
  Artifact rows/owners and one LegacyImport audit row.
- Legacy IDs and deterministic proposed IDs from the preview are preserved;
  no replacement IDs are invented during import.
- Re-importing the same completed preview/source generation is a no-op
  (idempotent): no duplicate rows, no second backup.
- Any row/import failure rolls back the whole transaction; the backup
  remains available; source bytes/mtime remain unchanged.
- No runtime route is cut over: this is an explicit library API only.

The module never touches repo-root production data: every path (legacy
root, backup root, database) is caller-supplied.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.artifacts import ManagedRoot, hash_file
from app.persistence.legacy_preview import LegacyPreview
from app.persistence.models import (
    Artifact,
    ArtifactOwner,
    Channel,
    LegacyImport,
    Project,
    Scene,
    VideoItem,
    Workspace,
)

__all__ = [
    "BACKUP_MANIFEST_NAME",
    "BackupEntry",
    "BackupManifest",
    "ImportResult",
    "LegacyImportError",
    "LegacyImportRefused",
    "LegacyImportRefusedError",
    "LegacyImporter",
    "backup_manifest_name",
    "confirmation_token",
]

#: Source kind recorded on the ``legacy_import`` audit row.
SOURCE_KIND = "legacy_json"

#: Supported legacy project schema version (from the preview fixture).
SUPPORTED_SCHEMA_VERSION = "2.0.0"

#: Backup manifest file name inside each immutable backup directory.
BACKUP_MANIFEST_NAME = "manifest.json"

#: Token salt prefix (stable, public; token itself is derived from content).
_TOKEN_PREFIX = "motionforge-legacy-import-v1"


# ── Public errors ─────────────────────────────────────────────────────────────


class LegacyImportError(RuntimeError):
    """Base error for the transactional importer."""


class LegacyImportRefusedError(LegacyImportError):
    """The import was refused during preflight (no DB business writes).

    ``reasons`` is a stable, ordered list of human-readable refusal
    messages; ``reason_codes`` is the stable machine-readable counterpart.
    """

    def __init__(
        self,
        message: str,
        *,
        reasons: list[str] | None = None,
        reason_codes: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.reasons: list[str] = reasons or []
        self.reason_codes: list[str] = reason_codes or []


#: Backwards-compatible alias (S01-T05 API uses the ``Refused`` name).
LegacyImportRefused = LegacyImportRefusedError


# ── Small records ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BackupEntry:
    """One backed-up source/reference file."""

    source_locator: str
    sha256: str
    size_bytes: int
    backup_relative_path: str


@dataclass(frozen=True)
class BackupManifest:
    """Immutable backup directory manifest."""

    backup_root: str
    backup_id: str
    created_at: str
    source_kind: str
    entries: list[BackupEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_root": self.backup_root,
            "backup_id": self.backup_id,
            "created_at": self.created_at,
            "source_kind": self.source_kind,
            "entries": [
                {
                    "source_locator": e.source_locator,
                    "sha256": e.sha256,
                    "size_bytes": e.size_bytes,
                    "backup_relative_path": e.backup_relative_path,
                }
                for e in sorted(self.entries, key=lambda e: e.source_locator)
            ],
        }


@dataclass(frozen=True)
class ImportResult:
    """Explicit success result of a transactional import."""

    backup_id: str
    backup_manifest_path: str
    legacy_import_id: str
    workspace_id: str
    channel_ids: tuple[str, ...]
    project_ids: tuple[str, ...]
    video_item_ids: tuple[str, ...]
    scene_ids: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    owner_count: int
    skipped_reason: str | None = None

    @property
    def idempotent_skipped(self) -> bool:
        return self.skipped_reason is not None


# ── Helpers ───────────────────────────────────────────────────────────────────


def confirmation_token(preview: LegacyPreview) -> str:
    """Deterministic confirmation token derived from preview content.

    The token binds the caller's explicit confirmation to the exact preview
    content: any change to the preview (channels/projects/checksums) yields
    a different token, so a stale or foreign preview cannot be confirmed.
    """
    payload = json.dumps(
        {
            "channels": preview.channels,
            "projects": preview.projects,
            "source_checksums": [c.as_dict() for c in preview.source_checksums],
            "source_checksums_after": [
                c.as_dict() for c in preview.source_checksums_after
            ],
            "referenced_files": [p.as_dict() for p in preview.referenced_files],
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = __import__("hashlib").sha256((_TOKEN_PREFIX + payload).encode("utf-8"))
    return digest.hexdigest()  # type: ignore[no-any-return]


def backup_manifest_name(backup_id: str) -> str:
    """Relative name of the manifest inside a backup dir (``manifest.json``)."""
    return BACKUP_MANIFEST_NAME


# ── Main class ────────────────────────────────────────────────────────────────


class LegacyImporter:
    """Transactional legacy preview importer (library API, no runtime cutover).

    Args:
        preview: Explicit preview built by :class:`LegacyPreviewer` (S01-T04).
        session_factory: Initialized SQLAlchemy session factory bound to a
            schema-upgraded SQLite database.
        workspace_id: Explicit workspace ID.  When a workspace with this ID
            already exists it is reused; otherwise it is created.
        backup_root: Managed root for immutable backup directories.
        token: Confirmation token; must equal
            :func:`confirmation_token` of this exact preview.
    """

    def __init__(
        self,
        preview: LegacyPreview,
        session_factory: sessionmaker[Session],
        workspace_id: str,
        backup_root: str | Path,
        token: str,
    ) -> None:
        if not preview:
            raise LegacyImportError("preview must be an explicit LegacyPreview")
        if not session_factory:
            raise LegacyImportError("session_factory must be an initialized factory")
        if not workspace_id or not isinstance(workspace_id, str):
            raise LegacyImportError("workspace_id must be a non-empty string")
        if not token:
            raise LegacyImportError("token must be a non-empty confirmation token")
        self._preview = preview
        self._session_factory = session_factory
        self._workspace_id = workspace_id
        self._backup_root = ManagedRoot(backup_root)
        self._token = token

    # ── Public API ──────────────────────────────────────────────────────────

    def run(self) -> ImportResult:
        """Execute the transactional import and return explicit evidence.

        Order of operations (each gate is a hard stop):

        1. Refuse immediately when the preview has blockers, a changed
           source checksum/mtime, unsafe/missing references, an unsupported
           schema version or a wrong confirmation token (no DB writes).
        2. Copy every inventoried source JSON + safe referenced file into a
           fresh immutable backup directory with atomic writes, then write
           the manifest (atomic) and fsync the directory.
        3. Revalidate all source checksums immediately before the
           transaction.
        4. In one DB transaction: reuse/create workspace, insert channels,
           projects, one VideoItem per project, scenes, source Artifacts +
           owners, and the LegacyImport audit row.  Any failure rolls back
           the whole transaction (backup remains valid and untouched).
        5. A completed (source_kind, source_sha256) is idempotent: the
           import is skipped with a no-op result, no second backup.
        """
        self._refuse_blocked_or_stale()
        self._refuse_wrong_token()
        existing = self._existing_completed_import()
        if existing is not None:
            return self._idempotent_result(existing)
        backup_id = self._new_backup_id()
        backup_path = self._backup_root.resolve(f"backups/{backup_id}")
        manifest = self._write_backup(backup_path)
        self._revalidate_before_transaction(manifest)
        result = self._import_transaction(manifest)
        if result is None:
            return self._idempotent_result(
                self._existing_completed_import()  # type: ignore[arg-type]
            )
        return result

    def _idempotent_result(self, existing: LegacyImport) -> ImportResult:
        """No-op result for a completed import (no duplicate rows/backup)."""
        backup_id = ""
        try:
            summary = json.loads(existing.summary_json or "{}")
            backup_id = str(summary.get("backup_id", ""))
        except (TypeError, ValueError):
            backup_id = ""
        return ImportResult(
            backup_id=backup_id,
            backup_manifest_path=(
                f"backups/{backup_id}/{BACKUP_MANIFEST_NAME}" if backup_id else ""
            ),
            legacy_import_id=existing.id,
            workspace_id=self._workspace_id,
            channel_ids=(),
            project_ids=(),
            video_item_ids=(),
            scene_ids=(),
            artifact_ids=(),
            owner_count=0,
            skipped_reason=(
                "a completed import for this source generation already exists"
            ),
        )

    # ── Preflight: blockers, staleness, token ───────────────────────────────

    def _refuse_blocked_or_stale(self) -> None:
        """Refuse previews with blockers or stale/changed sources.

        This gate runs before any backup write and before any DB write.
        """
        reasons: list[str] = []
        codes: list[str] = []

        blockers = self._preview.blockers
        if blockers:
            for issue in blockers:
                reasons.append(
                    f"blocker {issue.code} at {issue.location}: {issue.message}"
                )
            codes.append("BLOCKERS")

        if not self._preview.source_checksums:
            reasons.append("preview has no source checksums; nothing to import")
            codes.append("NO_SOURCES")

        for check in self._preview.source_checksums:
            if not check.path or not check.sha256 or len(check.sha256) != 64:
                reasons.append(f"invalid checksum record for {check.path!r}")
                codes.append("INVALID_CHECKSUM_RECORD")

        for issue in self._preview.issues:
            if issue.code in _UNSAFE_REFERENCE_CODES:
                reasons.append(
                    f"unsafe reference {issue.code} at {issue.location}: "
                    f"{issue.message}"
                )
        if any(
            issue.code in _UNSAFE_REFERENCE_CODES for issue in self._preview.issues
        ):
            codes.append("UNSAFE_REFERENCES")

        for project in self._preview.projects:
            version = str(project.get("version", ""))
            if version and version != SUPPORTED_SCHEMA_VERSION:
                reasons.append(
                    f"project {project.get('legacy_id', '?')!r} has unsupported "
                    f"schema version {version!r} (supported: "
                    f"{SUPPORTED_SCHEMA_VERSION!r})"
                )
                codes.append("UNSUPPORTED_SCHEMA")

        if reasons:
            raise LegacyImportRefused(
                "legacy import refused: " + "; ".join(reasons),
                reasons=reasons,
                reason_codes=codes,
            )

        # Live-source staleness: every source file must still match the
        # preview's recorded sha256 + mtime.  This runs BEFORE any backup so
        # a stale preview never even reaches the filesystem copy.
        stale: list[str] = []
        for check in self._preview.source_checksums:
            path = Path(check.path)
            if not path.is_file():
                stale.append(f"source missing: {check.path!r}")
                continue
            if hash_file(path) != check.sha256:
                stale.append(f"source checksum changed: {check.path!r}")
                continue
            if path.stat().st_mtime_ns != check.mtime_ns:
                stale.append(f"source mtime changed: {check.path!r}")
        if stale:
            raise LegacyImportRefused(
                "legacy import refused: " + "; ".join(stale),
                reasons=stale,
                reason_codes=["SOURCE_CHANGED"],
            )

    def _refuse_wrong_token(self) -> None:
        """Refuse when the confirmation token does not match this preview."""
        expected = confirmation_token(self._preview)
        if self._token != expected:
            raise LegacyImportRefused(
                "legacy import refused: wrong confirmation token",
                reasons=["wrong confirmation token"],
                reason_codes=["WRONG_TOKEN"],
            )

    # ── Backup ──────────────────────────────────────────────────────────────

    def _new_backup_id(self) -> str:
        """Collision-safe immutable backup id (timestamp + random hex)."""
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{secrets.token_hex(8)}"

    def _inventory_backup_files(self) -> list[tuple[str, Path]]:
        """Collect ``(source_locator, absolute_path)`` for every file to copy.

        Source JSON: channels file + every project.json.  References: every
        ``referenced_files`` entry with ``inside_root and exists``, mapped
        through the preview's legacy root.  All paths are proven inside the
        legacy root by the previewer; nothing outside is ever copied.
        """
        root = Path(self._preview.legacy_root)
        files: list[tuple[str, Path]] = []
        for check in self._preview.source_checksums:
            files.append((str(check.path), Path(check.path)))
        for ref in self._preview.referenced_files:
            if ref.inside_root and ref.exists:
                files.append((ref.raw, root / ref.raw))
        # Deduplicate by absolute path, keep stable order.
        seen: set[str] = set()
        unique: list[tuple[str, Path]] = []
        for locator, path in files:
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            unique.append((locator, path))
        return unique

    def _write_backup(self, backup_path: Path) -> BackupManifest:
        """Copy all inventoried files into *backup_path* (immutable, atomic).

        Layout::

            <backup_root>/backups/<backup_id>/
                source/...            # every inventoried source JSON file
                files/...             # every safe referenced file
                manifest.json         # written last, atomically

        The directory is created fresh (``mkdir`` fails if it already
        exists, guaranteeing collision-safe immutability); every file is
        written with an atomic same-directory staging + replace, then the
        whole directory is fsynced.  On any failure the partial directory
        is removed so no incomplete backup can ever be observed.
        """
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.mkdir(parents=False)
        entries: list[BackupEntry] = []
        try:
            for index, (locator, source_path) in enumerate(
                self._inventory_backup_files()
            ):
                digest = hash_file(source_path)
                stat = source_path.stat()
                rel = self._backup_rel_path(locator, index, source_path)
                self._backup_root.atomic_write_bytes(
                    f"backups/{backup_path.name}/{rel}",
                    source_path.read_bytes(),
                    expected_sha256=digest,
                )
                entries.append(
                    BackupEntry(
                        source_locator=locator,
                        sha256=digest,
                        size_bytes=stat.st_size,
                        backup_relative_path=rel,
                    )
                )
            manifest = BackupManifest(
                backup_root=str(self._backup_root.root),
                backup_id=backup_path.name,
                created_at=datetime.now(UTC).isoformat(),
                source_kind=SOURCE_KIND,
                entries=entries,
            )
            self._backup_root.atomic_write_bytes(
                f"backups/{backup_path.name}/{BACKUP_MANIFEST_NAME}",
                (json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n").encode(
                    "utf-8"
                ),
            )
            self._fsync_dir(backup_path)
            return manifest
        except BaseException:
            import shutil

            shutil.rmtree(backup_path, ignore_errors=True)
            raise

    def _backup_rel_path(
        self, locator: str, index: int, source_path: Path
    ) -> str:
        """Stable collision-safe relative path inside the backup directory.

        ``source/`` mirrors the legacy-relative source path; ``files/`` uses
        a hash-based name so identical references in different projects
        never collide and no path can escape the backup directory.
        """
        legacy_root = Path(self._preview.legacy_root).resolve()
        try:
            rel = source_path.resolve().relative_to(legacy_root).as_posix()
        except ValueError:
            rel = ""
        if rel and not rel.startswith("..") and not PurePosixPath(rel).is_absolute():
            return f"source/{rel}"
        return f"files/{index:04d}-{secrets.token_hex(4)}"

    def _backup_payload(
        self, manifest: BackupManifest, source_locator: str
    ) -> dict[str, Any] | None:
        """Read a backed-up project.json payload from the immutable backup.

        ``source_locator`` is the absolute path recorded in the manifest
        (``PathCheck.path`` for project.json).  The file is read only from
        the backup directory — never from the live legacy tree — so the
        payload is byte-exactly the approved generation the manifest
        preserved.
        """
        for entry in manifest.entries:
            if entry.source_locator != source_locator:
                continue
            backup_file = (
                self._backup_root.root
                / "backups"
                / manifest.backup_id
                / entry.backup_relative_path
            )
            try:
                data = json.loads(backup_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
            if not isinstance(data, dict):
                return None
            return data
        return None

    def _backup_scenes(
        self, manifest: BackupManifest, project: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validated scene list from the backed-up project.json (never live)."""
        proj_path = self._project_json_locator(project)
        data = self._backup_payload(manifest, proj_path)
        if data is None:
            return []
        scenes = data.get("scenes", [])
        if not isinstance(scenes, list):
            return []
        return [s for s in scenes if isinstance(s, dict)]

    def _project_json_locator(self, project: dict[str, Any]) -> str:
        """Absolute source locator of a project's project.json (manifest key)."""
        return str(
            Path(self._preview.legacy_root)
            / "projects"
            / project["legacy_id"]
            / "project.json"
        )

    @staticmethod
    def _fsync_dir(path: Path) -> None:
        """Best-effort directory fsync (no-op where unsupported)."""
        try:
            fd = path.open("r", encoding="utf-8")
        except OSError:
            return
        try:
            import os

            os.fsync(fd.fileno())
        except OSError:
            pass
        finally:
            fd.close()

    # ── Revalidation ────────────────────────────────────────────────────────

    def _revalidate_before_transaction(self, manifest: BackupManifest) -> None:
        """Re-validate every source checksum immediately before the transaction.

        A source that changed after backup aborts the import before any DB
        write; the immutable backup remains valid and untouched.  The live
        file is NEVER reopened for import data after this gate: project
        metadata/scenes are read exclusively from the verified immutable
        backup.
        """
        for check in self._preview.source_checksums:
            path = Path(check.path)
            if not path.is_file():
                raise LegacyImportRefused(
                    f"source changed before import: {check.path!r} is missing",
                    reasons=[f"source missing: {check.path!r}"],
                    reason_codes=["SOURCE_CHANGED"],
                )
            actual = hash_file(path)
            if actual != check.sha256:
                raise LegacyImportRefused(
                    f"source changed before import: {check.path!r} sha256 "
                    f"{actual} != preview {check.sha256}",
                    reasons=[f"source checksum changed: {check.path!r}"],
                    reason_codes=["SOURCE_CHANGED"],
                )
            stat = path.stat()
            if stat.st_mtime_ns != check.mtime_ns:
                raise LegacyImportRefused(
                    f"source mtime changed before import: {check.path!r}",
                    reasons=[f"source mtime changed: {check.path!r}"],
                    reason_codes=["SOURCE_CHANGED"],
                )
            # Hard proof the backup holds the same approved bytes: compare
            # the backed-up file's hash against the preview record.
            backup_entry = self._find_backup_entry(manifest, check.path)
            if backup_entry is None:
                raise LegacyImportRefused(
                    f"backup missing entry for source {check.path!r}",
                    reasons=[f"backup missing entry: {check.path!r}"],
                    reason_codes=["BACKUP_INCONSISTENT"],
                )
            backup_file = (
                self._backup_root.root
                / "backups"
                / manifest.backup_id
                / backup_entry.backup_relative_path
            )
            if not backup_file.is_file():
                raise LegacyImportRefused(
                    f"backup file missing for source {check.path!r}",
                    reasons=[f"backup file missing: {check.path!r}"],
                    reason_codes=["BACKUP_INCONSISTENT"],
                )
            if hash_file(backup_file) != check.sha256:
                raise LegacyImportRefused(
                    f"backup checksum mismatch for source {check.path!r}",
                    reasons=[f"backup checksum mismatch: {check.path!r}"],
                    reason_codes=["BACKUP_INCONSISTENT"],
                )

    def _find_backup_entry(
        self, manifest: BackupManifest, source_locator: str
    ) -> BackupEntry | None:
        """Manifest entry for a source locator (None when absent)."""
        for entry in manifest.entries:
            if entry.source_locator == source_locator:
                return entry
        return None

    # ── Transaction ─────────────────────────────────────────────────────────

    def _existing_completed_import(self) -> LegacyImport | None:
        """Read-only idempotency probe (no writes)."""
        with self._session_factory() as session:
            return session.execute(
                select(LegacyImport).where(
                    LegacyImport.source_kind == SOURCE_KIND,
                    LegacyImport.source_sha256 == self._source_sha256(),
                    LegacyImport.status == "completed",
                )
            ).scalars().first()

    def _import_transaction(self, manifest: BackupManifest) -> ImportResult | None:
        """One transaction: workspace + rows + audit.  None = idempotent skip."""
        with self._session_factory() as session:
            source_sha = self._source_sha256()
            with session.begin():
                existing = session.execute(
                    select(LegacyImport).where(
                        LegacyImport.source_kind == SOURCE_KIND,
                        LegacyImport.source_sha256 == source_sha,
                        LegacyImport.status == "completed",
                    )
                ).scalars().first()
                if existing is not None:
                    return None

                workspace = session.get(Workspace, self._workspace_id)
                if workspace is None:
                    workspace = Workspace(id=self._workspace_id, name="Local Workspace")
                    session.add(workspace)

                channel_by_legacy: dict[str, Channel] = {}
                for channel in self._preview.channels:
                    legacy_id = channel["legacy_id"]
                    row = session.execute(
                        select(Channel).where(
                            Channel.workspace_id == self._workspace_id,
                            Channel.legacy_id == legacy_id,
                        )
                    ).scalars().first()
                    if row is None:
                        row = Channel(
                            id=channel["proposed_id"],
                            workspace_id=self._workspace_id,
                            legacy_id=legacy_id,
                            role="source",
                            name=channel["name"] or legacy_id,
                            description="",
                            target_language=(
                                channel["target_lang"] or None
                            ),
                            default_output_profile=(
                                channel["default_preset_id"] or None
                            ),
                            status="active",
                        )
                        session.add(row)
                    channel_by_legacy[legacy_id] = row

                project_rows: list[Project] = []
                video_rows: list[VideoItem] = []
                scene_rows: list[Scene] = []
                artifact_rows: list[Artifact] = []
                owner_rows: list[ArtifactOwner] = []
                for project in self._preview.projects:
                    legacy_id = project["legacy_id"]
                    project_row = session.execute(
                        select(Project).where(
                            Project.workspace_id == self._workspace_id,
                            Project.legacy_id == legacy_id,
                        )
                    ).scalars().first()
                    if project_row is None:
                        project_row = Project(
                            id=project["proposed_id"],
                            workspace_id=self._workspace_id,
                            legacy_id=legacy_id,
                            name=project["name"] or legacy_id,
                            description="",
                            status=self._project_status(project.get("task_status", "")),
                            source_channel_id=(
                                channel_by_legacy[project["channel_id"]].id
                                if project.get("channel_id")
                                and project["channel_id"] in channel_by_legacy
                                else None
                            ),
                        )
                        session.add(project_row)
                    project_rows.append(project_row)

                    video_id = self._video_item_id(project)
                    video_row = session.execute(
                        select(VideoItem).where(
                            VideoItem.project_id == project_row.id,
                            VideoItem.legacy_id == legacy_id,
                        )
                    ).scalars().first()
                    live = self._backup_payload(
                        manifest, self._project_json_locator(project)
                    )
                    if live is None:
                        live = {}
                    if video_row is None:
                        video_row = VideoItem(
                            id=video_id,
                            project_id=project_row.id,
                            legacy_id=legacy_id,
                            title=project["name"] or legacy_id,
                            position=0,
                            status="imported",
                            source_artifact_id=None,
                            source_channel_id=(
                                channel_by_legacy[project["channel_id"]].id
                                if project.get("channel_id")
                                and project["channel_id"] in channel_by_legacy
                                else None
                            ),
                            duration_ms=self._duration_ms(live),
                            width=self._video_metadata_int(live, "width"),
                            height=self._video_metadata_int(live, "height"),
                            fps_num=self._fps_num(live),
                            fps_den=self._fps_den(live),
                        )
                        session.add(video_row)
                    video_rows.append(video_row)

                    for scene in self._backup_scenes(manifest, project):
                        legacy_scene_id = scene.get("scene_id")
                        scene_row = session.execute(
                            select(Scene).where(
                                Scene.video_item_id == video_row.id,
                                Scene.legacy_scene_id == legacy_scene_id,
                            )
                        ).scalars().first()
                        if scene_row is None:
                            scene_row = Scene(
                                video_item_id=video_row.id,
                                legacy_scene_id=legacy_scene_id,
                                position=int(scene.get("position", len(scene_rows))),
                                start_frame=int(scene["start_frame"]),
                                end_frame=int(scene["end_frame"]),
                                start_time_ms=int(scene.get("start_time_ms", 0)),
                                end_time_ms=int(scene.get("end_time_ms", 0)),
                                status="pending",
                            )
                            session.add(scene_row)
                        scene_rows.append(scene_row)

                artifact_by_rel: dict[str, Artifact] = {}
                for entry in manifest.entries:
                    source_path = Path(entry.source_locator)
                    if not source_path.is_absolute():
                        source_path = Path(self._preview.legacy_root) / entry.source_locator
                    rel = self._managed_rel_for(entry, source_path)
                    artifact = session.execute(
                        select(Artifact).where(
                            Artifact.workspace_id == self._workspace_id,
                            Artifact.relative_path == rel,
                        )
                    ).scalars().first()
                    if artifact is None:
                        artifact = Artifact(
                            workspace_id=self._workspace_id,
                            kind=self._kind_for(source_path),
                            relative_path=rel,
                            state="ready",
                            sha256=entry.sha256,
                            size_bytes=entry.size_bytes,
                            mime_type=self._mime_for(source_path),
                        )
                        session.add(artifact)
                    artifact_rows.append(artifact)
                    artifact_by_rel[rel] = artifact

                # Artifact public ids are Python-side defaults: flush so the
                # owner links can reference real ids before the insert.
                session.flush()

                # Wire source_artifact_id for every project's source video
                # and create ArtifactOwner links (project + video_item).
                for project, project_row, video_row in zip(
                    self._preview.projects, project_rows, video_rows
                ):
                    source = project.get("source", {})
                    source_raw = source.get("video", "")
                    rel = self._managed_rel_for_locator(source_raw)
                    artifact = artifact_by_rel.get(rel)
                    if artifact is not None and video_row.source_artifact_id is None:
                        video_row.source_artifact_id = artifact.id
                    if artifact is not None:
                        for owner_type, owner_id in (
                            ("project", project_row.id),
                            ("video_item", video_row.id),
                        ):
                            owner = ArtifactOwner(
                                artifact_id=artifact.id,
                                owner_type=owner_type,
                                owner_id=owner_id,
                                purpose="source",
                            )
                            session.add(owner)
                            owner_rows.append(owner)

                import_row = LegacyImport(
                    source_kind=SOURCE_KIND,
                    source_locator=str(Path(self._preview.legacy_root)),
                    source_sha256=self._source_sha256(),
                    status="completed",
                    summary_json=json.dumps(
                        {
                            "channels": len(self._preview.channels),
                            "projects": len(self._preview.projects),
                            "videos": len(video_rows),
                            "scenes": len(scene_rows),
                            "artifacts": len(artifact_rows),
                            "owners": len(owner_rows),
                            "backup_id": manifest.backup_id,
                            "backup_manifest_path": (
                                f"backups/{manifest.backup_id}/{BACKUP_MANIFEST_NAME}"
                            ),
                        },
                        sort_keys=True,
                    ),
                    error_json=None,
                    completed_at=datetime.now(UTC),
                )
                session.add(import_row)

            return ImportResult(
                backup_id=manifest.backup_id,
                backup_manifest_path=str(
                    self._backup_root.root
                    / "backups"
                    / manifest.backup_id
                    / BACKUP_MANIFEST_NAME
                ),
                legacy_import_id=import_row.id,
                workspace_id=self._workspace_id,
                channel_ids=tuple(r.id for r in channel_by_legacy.values()),
                project_ids=tuple(r.id for r in project_rows),
                video_item_ids=tuple(r.id for r in video_rows),
                scene_ids=tuple(r.id for r in scene_rows),
                artifact_ids=tuple(r.id for r in artifact_rows),
                owner_count=len(owner_rows),
            )

    # ── Mapping helpers ─────────────────────────────────────────────────────

    def _source_sha256(self) -> str:
        """Source-generation checksum: sha256 of channels + project.json bytes.

        Matches the idempotency boundary ``(source_kind, source_sha256)``;
        reference-file bytes are not part of the generation identity (their
        checksums are recorded per-file in the backup manifest).
        """
        digest = __import__("hashlib").sha256()
        for check in self._preview.source_checksums:
            digest.update(check.sha256.encode("ascii"))
            digest.update(b"\n")
        return digest.hexdigest()  # type: ignore[no-any-return]

    def _video_item_id(self, project: dict[str, Any]) -> str:
        """Deterministic VideoItem public id: uuid5 over project legacy id.

        The preview's deterministic proposed project id is preserved; the
        single VideoItem per project derives from the same identity so a
        re-import (after rollback) never invents a new id.
        """
        return str(
            __import__("uuid").uuid5(
                __import__("uuid").NAMESPACE_URL,
                f"motionforge:legacy-import:video:{project['legacy_id']}",
            )
        )

    def _project_status(self, task_status: str) -> str:
        """Map legacy task status to the approved project status enum."""
        mapping = {
            "in_progress": "active",
            "pending": "draft",
            "review": "needs_review",
            "rendering": "rendering",
            "done": "completed",
            "completed": "completed",
            "archived": "archived",
        }
        return mapping.get(task_status, "draft")

    def _duration_ms(self, project: dict[str, Any]) -> int | None:
        metadata = project.get("video_metadata")
        if isinstance(metadata, dict):
            seconds = metadata.get("duration_seconds")
            if isinstance(seconds, (int, float)) and seconds >= 0:
                return int(seconds * 1000)
        return None

    def _video_metadata_int(self, project: dict[str, Any], key: str) -> int | None:
        metadata = project.get("video_metadata")
        if isinstance(metadata, dict):
            value = metadata.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                return int(value)
        return None

    def _fps_num(self, project: dict[str, Any]) -> int | None:
        metadata = project.get("video_metadata")
        if isinstance(metadata, dict):
            fps = metadata.get("fps")
            if isinstance(fps, (int, float)) and fps > 0:
                return int(round(fps))
        return None

    def _fps_den(self, project: dict[str, Any]) -> int | None:
        metadata = project.get("video_metadata")
        if isinstance(metadata, dict):
            fps = metadata.get("fps")
            if isinstance(fps, (int, float)) and fps > 0:
                if float(fps).is_integer():
                    return 1
                return 1000
        return None

    def _managed_rel_for(self, entry: BackupEntry, source_path: Path) -> str:
        """Managed relative path of a backed-up file (mirrors backup layout)."""
        return entry.backup_relative_path

    def _managed_rel_for_locator(self, source_raw: str) -> str:
        """Resolve a legacy source-video locator to its managed relative path."""
        if not source_raw:
            return ""
        root = Path(self._preview.legacy_root)
        candidate = root / source_raw
        root_resolved = root.resolve()
        if (
            candidate.resolve() != root_resolved
            and root_resolved not in candidate.resolve().parents
        ):
            return ""
        rel = candidate.resolve().relative_to(root.resolve()).as_posix()
        return f"source/{rel}"

    @staticmethod
    def _kind_for(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}:
            return "video"
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
            return "image"
        if suffix in {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"}:
            return "audio"
        if suffix in {".json", ".txt", ".md", ".csv"}:
            return "document"
        return "other"

    @staticmethod
    def _mime_for(path: Path) -> str | None:
        return {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".json": "application/json",
        }.get(path.suffix.lower())


#: Issue codes that indicate a reference escaping the legacy root; these are
#: always refused (never copied, never followed).
_UNSAFE_REFERENCE_CODES = {
    "PROJECTS_ROOT_UNSAFE",
    "PROJECT_PATH_UNSAFE",
    "PROJECT_SOURCE_ABSOLUTE",
    "PROJECT_REFERENCE_UNSAFE",
}
