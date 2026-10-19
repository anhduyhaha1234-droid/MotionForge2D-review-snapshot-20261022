"""Managed artifact filesystem helpers for MotionForge 2D.

This module is the containment-safe filesystem contract for all managed media
writes and removals (S01-T03).  It deliberately does NOT import the database
engine, ORM models, repositories or any runtime service: helpers here return
explicit results and never commit database sessions or mutate ``Artifact``
rows.  Callers (future services/repositories) are responsible for persisting
the returned evidence.

Contract highlights (see ``docs/architecture/MANAGED_ARTIFACT_CONTRACT.md``):

- Every path is a normalized relative path resolved inside the configured
  managed root.  Absolute paths, drive/UNC paths, empty paths, ``..``,
  symlink/junction escapes and the database file are rejected up front.
- Atomic writes use a same-directory unique staging file, flush + ``fsync``,
  ``os.replace``, optional SHA-256 verification and cleanup on failure.
- Trash moves stay under the configured Trash root, use collision-safe names
  and write a recovery manifest (original relative path / checksum / time).
- Restore validates containment and never overwrites an existing destination.

All byte/hash helpers are dependency-free (``hashlib``, ``os``, ``pathlib``).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import secrets
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import BinaryIO, TypeAlias

__all__ = [
    "ArtifactWriteError",
    "ManagedPathError",
    "ManagedRoot",
    "RestoreResult",
    "TrashManifest",
    "TrashMoveResult",
    "hash_file",
    "is_within",
    "normalize_managed_path",
]

#: Relative path inside the managed tree; always POSIX-style.
ManagedRelativePath: TypeAlias = str

#: Default staging suffix used by atomic writes (same directory).
STAGING_SUFFIX = ".staging"

#: Default Trash directory name under the managed root.
TRASH_DIRNAME = ".trash"

#: Recovery manifest name inside a trash entry directory.
TRASH_MANIFEST_NAME = "manifest.json"

#: Size of the random component in collision-safe trash names (hex chars).
_TRASH_RANDOM_HEX = 16


class ManagedPathError(ValueError):
    """Raised when a path is not a valid contained managed path."""


class ArtifactWriteError(OSError):
    """Raised when an atomic write or verification cannot publish safely."""


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TrashManifest:
    """Recovery manifest written next to a trashed artifact."""

    original_relative_path: str
    sha256: str
    size_bytes: int
    trashed_at: str
    trashed_name: str

    @classmethod
    def load(cls, path: Path) -> TrashManifest:
        """Load and validate a manifest written by :meth:`ManagedRoot.trash`."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ArtifactWriteError(
                f"Cannot read recovery manifest {path}: {exc}"
            ) from exc
        try:
            return cls(
                original_relative_path=str(raw["original_relative_path"]),
                sha256=str(raw["sha256"]),
                size_bytes=int(raw["size_bytes"]),
                trashed_at=str(raw["trashed_at"]),
                trashed_name=str(raw["trashed_name"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ArtifactWriteError(
                f"Malformed recovery manifest {path}: {exc}"
            ) from exc


@dataclass(frozen=True)
class TrashMoveResult:
    """Explicit result of a Trash move (never touches the database)."""

    trashed_relative_path: str
    manifest_relative_path: str
    manifest: TrashManifest


@dataclass(frozen=True)
class RestoreResult:
    """Explicit result of a Trash restore."""

    restored_relative_path: str
    sha256: str
    size_bytes: int


@dataclass
class _WritePolicy:
    """Internal knobs for atomic writes (defaults are the safe contract)."""

    fsync: bool = True
    verify_sha256: bool = True
    expected_sha256: str | None = None


# ── Pure helpers ─────────────────────────────────────────────────────────────


def normalize_managed_path(relative_path: str | Path) -> ManagedRelativePath:
    """Validate *relative_path* and return its normalized POSIX form.

    Raises:
        ManagedPathError: if the path is empty, absolute, contains a drive
            or UNC prefix, contains ``..``, or is otherwise not a clean
            relative path inside a managed tree.
    """
    raw = relative_path.as_posix() if isinstance(relative_path, Path) else relative_path
    if raw is None or raw == "":
        raise ManagedPathError("managed relative path must not be empty")
    raw = raw.replace("\\", "/")
    if len(raw) >= 2 and raw[1] == ":":
        raise ManagedPathError(f"drive path is not allowed: {raw!r}")
    if raw.startswith("//"):
        raise ManagedPathError(f"UNC path is not allowed: {raw!r}")
    if raw.startswith("/"):
        raise ManagedPathError(f"absolute path is not allowed: {raw!r}")
    if raw in (".", "./"):
        raise ManagedPathError(f"managed relative path must name a file: {raw!r}")
    normalized = PurePosixPath(raw).as_posix()
    if normalized == ".":
        raise ManagedPathError(f"managed relative path must name a file: {raw!r}")
    if ".." in normalized.split("/"):
        raise ManagedPathError(f"parent traversal is not allowed: {raw!r}")
    if normalized.startswith("/"):
        raise ManagedPathError(f"absolute path is not allowed: {raw!r}")
    return normalized


def is_within(path: Path, root: Path) -> bool:
    """Return True iff *path* is *root* itself or strictly inside it.

    Uses ``os.path.commonpath`` semantics so that a sibling like
    ``C:/data/root_evil`` is never considered inside ``C:/data/root``.
    """
    try:
        root_resolved = root.resolve()
    except OSError:
        root_resolved = root.absolute()
    try:
        path_resolved = path.resolve()
    except OSError:
        path_resolved = path.absolute()
    try:
        os.path.commonpath([str(root_resolved), str(path_resolved)])
    except ValueError:
        return False
    return path_resolved == root_resolved or root_resolved in path_resolved.parents


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the lowercase hex SHA-256 of *path* (streaming)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


# ── ManagedRoot ──────────────────────────────────────────────────────────────


class ManagedRoot:
    """Filesystem helpers bound to one configured managed root.

    The root is resolved once at construction.  Every operation re-validates
    containment against the resolved root, so an attacker-controlled path can
    never escape even if the root or the target moves between calls.

    Args:
        root: Managed root directory (created on first use).
        trash_dirname: Name of the Trash directory under the root.
        database_path: Optional database file that must never be written as a
            managed artifact (e.g. the SQLite file owning ``Artifact`` rows).
    """

    def __init__(
        self,
        root: str | Path,
        trash_dirname: str = TRASH_DIRNAME,
        database_path: str | Path | None = None,
    ) -> None:
        if (
            trash_dirname is None
            or trash_dirname == ""
            or "/" in trash_dirname
            or "\\" in trash_dirname
        ):
            raise ManagedPathError(f"invalid trash dirname: {trash_dirname!r}")
        self._root = Path(root).resolve()
        self._trash_dirname = trash_dirname
        self._database_path = (
            Path(database_path).resolve() if database_path is not None else None
        )
        if self._database_path is not None and self._database_path == self._root:
            raise ManagedPathError("database path must not be the managed root")

    # ── Containment ─────────────────────────────────────────────────────────

    @property
    def root(self) -> Path:
        """The resolved managed root."""
        return self._root

    @property
    def trash_dirname(self) -> str:
        """Name of the Trash directory under the managed root."""
        return self._trash_dirname

    @property
    def database_path(self) -> Path | None:
        """Optional protected database file (never a managed artifact)."""
        return self._database_path

    def trash_dir(self) -> Path:
        """Absolute path of the Trash directory (created on demand)."""
        path = self._root / self._trash_dirname
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _trash_root(self) -> Path:
        """Resolved Trash root path — never creates the directory.

        Validation must not have filesystem side effects, so containment
        checks resolve the configured Trash root without materializing it.
        """
        return (self._root / self._trash_dirname).resolve()

    def resolve(self, relative_path: str | Path) -> Path:
        """Validate *relative_path* and return its absolute path inside root.

        Raises:
            ManagedPathError: if the path is not contained (including
                symlink/junction escapes and the protected database file).
        """
        normalized = normalize_managed_path(relative_path)
        candidate = self._root / normalized
        candidate_resolved = candidate.resolve()
        if candidate_resolved != self._root and self._root not in candidate_resolved.parents:
            raise ManagedPathError(
                f"path escapes the managed root: {relative_path!r}"
            )
        if self._database_path is not None and candidate_resolved == self._database_path:
            raise ManagedPathError("database file is not a managed artifact")
        return candidate_resolved

    def relative_path_of(self, absolute_path: str | Path) -> ManagedRelativePath:
        """Return the normalized relative path of *absolute_path* inside root.

        Raises:
            ManagedPathError: if *absolute_path* is not contained in root.
        """
        path = Path(absolute_path).resolve()
        if path != self._root and self._root not in path.parents:
            raise ManagedPathError(
                f"path is outside the managed root: {absolute_path!r}"
            )
        return path.relative_to(self._root).as_posix()

    # ── Atomic write ─────────────────────────────────────────────────────────

    def atomic_write_bytes(
        self,
        relative_path: str | Path,
        data: bytes,
        *,
        fsync: bool = True,
        verify_sha256: bool = True,
        expected_sha256: str | None = None,
        encoding: str | None = None,
    ) -> tuple[str, int]:
        """Atomically write *data* and return ``(sha256, size_bytes)``.

        The staging file is created in the same directory as the target with
        a unique name, flushed/fsynced, then moved into place with
        ``os.replace`` (same filesystem, atomic on POSIX and Windows).
        On any failure the staging file is removed and the prior content (if
        any) is left untouched.

        Args:
            relative_path: Managed relative target path.
            data: Bytes to write.
            fsync: Flush the staging file to disk before publishing.
            verify_sha256: Hash the staged bytes before publishing.
            expected_sha256: When given, the write FAILS unless the staged
                bytes hash to this value (checked before publish).
            encoding: When given, *data* is encoded from str with this
                encoding before writing.

        Returns:
            ``(sha256, size_bytes)`` of the published content.
        """
        if encoding is not None:
            if not isinstance(data, str):
                raise TypeError("encoding requires str data")
            data = data.encode(encoding)
        if not isinstance(data, bytes):
            data = bytes(data)
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        policy = _WritePolicy(
            fsync=fsync, verify_sha256=verify_sha256, expected_sha256=expected_sha256
        )
        staging = self._unique_staging_path(target)
        try:
            with staging.open("xb") as handle:
                handle.write(data)
                if policy.fsync:
                    handle.flush()
                    os.fsync(handle.fileno())
            if policy.verify_sha256:
                actual = hash_file(staging)
                if policy.expected_sha256 is not None and actual != policy.expected_sha256:
                    raise ArtifactWriteError(
                        f"SHA-256 mismatch for {relative_path!r}: expected "
                        f"{policy.expected_sha256}, got {actual}"
                    )
            os.replace(staging, target)
        except BaseException:
            staging.unlink(missing_ok=True)
            raise
        return hash_file(target), target.stat().st_size

    def atomic_write_stream(
        self,
        relative_path: str | Path,
        stream: BinaryIO,
        *,
        fsync: bool = True,
        verify_sha256: bool = True,
        expected_sha256: str | None = None,
    ) -> tuple[str, int]:
        """Atomically copy *stream* to *relative_path*.

        Same contract as :meth:`atomic_write_bytes`; the stream is read in
        chunks into a same-directory staging file and verified/published only
        after the full copy succeeds.
        """
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        policy = _WritePolicy(
            fsync=fsync, verify_sha256=verify_sha256, expected_sha256=expected_sha256
        )
        staging = self._unique_staging_path(target)
        try:
            with staging.open("xb") as handle:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                if policy.fsync:
                    handle.flush()
                    os.fsync(handle.fileno())
            if policy.verify_sha256:
                actual = hash_file(staging)
                if policy.expected_sha256 is not None and actual != policy.expected_sha256:
                    raise ArtifactWriteError(
                        f"SHA-256 mismatch for {relative_path!r}: expected "
                        f"{policy.expected_sha256}, got {actual}"
                    )
            os.replace(staging, target)
        except BaseException:
            staging.unlink(missing_ok=True)
            raise
        return hash_file(target), target.stat().st_size

    def _unique_staging_path(self, target: Path) -> Path:
        """A unique same-directory staging path for *target*."""
        for _ in range(100):
            candidate = target.with_name(
                f".{target.name}.{uuid.uuid4().hex}{STAGING_SUFFIX}"
            )
            if not candidate.exists():
                return candidate
        raise ArtifactWriteError(
            f"could not allocate a unique staging file for {target.name!r}"
        )

    # ── Trash ────────────────────────────────────────────────────────────────

    def trash(self, relative_path: str | Path) -> TrashMoveResult:
        """Move a managed file into Trash under a collision-safe name.

        The move never crosses managed boundaries: source and destination are
        both validated inside the resolved root.  A recovery manifest is
        written next to the trashed file recording the original relative path,
        checksum and time, so restore is deterministic.

        Returns:
            :class:`TrashMoveResult` with the trashed path, manifest path and
            manifest content.
        """
        source = self.resolve(relative_path)
        if not source.exists():
            raise ArtifactWriteError(
                f"cannot trash missing file: {relative_path!r}"
            )
        if not source.is_file():
            raise ArtifactWriteError(
                f"cannot trash non-file path: {relative_path!r}"
            )
        if source == self._root or self._root not in source.parents:
            raise ManagedPathError(
                f"source escapes the managed root: {relative_path!r}"
            )
        if self._database_path is not None and source == self._database_path:
            raise ManagedPathError("database file is not a managed artifact")

        original_rel = self.relative_path_of(source)
        trash_root = self.trash_dir()
        entry = trash_root / f"{original_rel}-{secrets.token_hex(_TRASH_RANDOM_HEX // 2)}"
        entry.mkdir(parents=True, exist_ok=True)
        trashed_name = f"{source.name}-{secrets.token_hex(_TRASH_RANDOM_HEX // 2)}"
        trashed_file = entry / trashed_name
        try:
            os.replace(source, trashed_file)
        except OSError as exc:
            shutil.rmtree(entry, ignore_errors=True)
            raise ArtifactWriteError(
                f"trash move failed for {relative_path!r}: {exc}"
            ) from exc

        size_bytes = trashed_file.stat().st_size
        checksum = hash_file(trashed_file)
        manifest = TrashManifest(
            original_relative_path=original_rel,
            sha256=checksum,
            size_bytes=size_bytes,
            trashed_at=datetime.now(UTC).isoformat(),
            trashed_name=trashed_name,
        )
        manifest_path = entry / TRASH_MANIFEST_NAME
        try:
            manifest_path.write_text(
                json.dumps(manifest.__dict__, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            os.replace(trashed_file, source)
            shutil.rmtree(entry, ignore_errors=True)
            raise ArtifactWriteError(
                f"trash manifest write failed for {relative_path!r}: {exc}"
            ) from exc

        return TrashMoveResult(
            trashed_relative_path=trashed_file.relative_to(self._root).as_posix(),
            manifest_relative_path=manifest_path.relative_to(self._root).as_posix(),
            manifest=manifest,
        )

    def restore(
        self,
        manifest_relative_path: str | Path,
        *,
        verify_checksum: bool = True,
    ) -> RestoreResult:
        """Restore a trashed artifact from its recovery manifest.

        Validates that the manifest, the trashed file and the original
        relative path all stay inside the configured Trash root / managed
        root (no cross-boundary restore) and never overwrites an existing
        destination.

        Args:
            manifest_relative_path: Managed relative path of the recovery
                manifest (as returned by :meth:`trash`).
            verify_checksum: Reject the restore when the trashed bytes no
                longer match the manifest checksum.

        Returns:
            :class:`RestoreResult` with the restored path, checksum and size.
        """
        manifest_path = self.resolve(manifest_relative_path)
        manifest_path_resolved = manifest_path.resolve()
        trash_root = self._trash_root()
        if manifest_path_resolved == trash_root or trash_root not in manifest_path_resolved.parents:
            raise ManagedPathError(
                f"manifest is not inside the Trash root: {manifest_relative_path!r}"
            )
        manifest = TrashManifest.load(manifest_path)
        original_rel = normalize_managed_path(manifest.original_relative_path)
        destination = self.resolve(original_rel)
        if destination.exists():
            raise ArtifactWriteError(
                f"refusing to overwrite existing destination: {original_rel!r}"
            )
        trashed_file = manifest_path.parent / manifest.trashed_name
        trashed_resolved = trashed_file.resolve()
        if trashed_resolved == trash_root or trash_root not in trashed_resolved.parents:
            raise ManagedPathError(
                f"trashed file escapes the Trash root: {manifest.trashed_name!r}"
            )
        if trashed_resolved.parent != manifest_path.parent.resolve():
            raise ManagedPathError(
                f"trashed file must live in the manifest entry: {manifest.trashed_name!r}"
            )
        if not trashed_file.exists() or not trashed_file.is_file():
            raise ArtifactWriteError(
                f"trashed file missing: {manifest.trashed_name!r}"
            )
        if verify_checksum:
            actual = hash_file(trashed_file)
            if actual != manifest.sha256:
                raise ArtifactWriteError(
                    f"checksum mismatch restoring {original_rel!r}: expected "
                    f"{manifest.sha256}, got {actual}"
                )
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(trashed_file, destination)
        with contextlib.suppress(OSError):
            manifest_path.unlink()
        with contextlib.suppress(OSError):
            manifest_path.parent.rmdir()
        return RestoreResult(
            restored_relative_path=original_rel,
            sha256=manifest.sha256,
            size_bytes=manifest.size_bytes,
        )
