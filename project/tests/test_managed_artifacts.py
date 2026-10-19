"""Targeted tests for S01-T03 managed artifact filesystem helpers.

Covers AC1-AC5 of S01-T03:

- AC1: valid paths resolve inside the managed root; every path escape form
  (absolute, drive/UNC, empty, ``..``, symlink/junction, database file) is
  rejected.
- AC2: atomic byte/stream writes expose only final or prior content and clean
  staging files after failure.
- AC3: hash/size evidence is returned and an expected-checksum mismatch cannot
  publish.
- AC4: Trash move is recoverable, collision-safe, manifest-backed and cannot
  cross managed boundaries.
- AC5: restore refuses overwrite and validates both original and Trash
  containment.

Every test uses only pytest ``tmp_path`` directories — never production
output/projects/presets.  The helpers under test are pure filesystem helpers;
they do not touch the database, ORM models or any runtime service.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from app.persistence.artifacts import (
    ArtifactWriteError,
    ManagedPathError,
    ManagedRoot,
    TrashManifest,
    hash_file,
    is_within,
    normalize_managed_path,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def managed(tmp_path: Path) -> ManagedRoot:
    """A ManagedRoot bound to a fresh temporary directory."""
    return ManagedRoot(tmp_path / "managed")


@pytest.fixture()
def protected_managed(tmp_path: Path) -> ManagedRoot:
    """A ManagedRoot whose database file is protected (never an artifact)."""
    db = tmp_path / "motionforge.db"
    return ManagedRoot(tmp_path / "managed", database_path=db)


def _write(root: ManagedRoot, rel: str, data: bytes) -> tuple[str, int]:
    """Write a file through the managed root (bypasses atomic helpers)."""
    target = root.resolve(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hash_file(target), len(data)


# ── AC1: path resolution and containment ─────────────────────────────────────


def test_valid_relative_paths_resolve(managed: ManagedRoot) -> None:
    """Normal relative paths resolve inside the managed root."""
    assert managed.resolve("a/b.mp4") == managed.root / "a" / "b.mp4"
    assert managed.resolve("b.mp4") == managed.root / "b.mp4"
    assert managed.resolve("a/./b.mp4") == managed.root / "a" / "b.mp4"
    # Backslashes normalize to POSIX separators.
    assert managed.resolve("a\\b\\c.mp4") == managed.root / "a" / "b" / "c.mp4"


def test_root_itself_is_contained() -> None:
    """The root directory counts as inside itself for boundary checks."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        root.mkdir()
        assert is_within(root, root)
        assert is_within(root / "file.bin", root)


def test_empty_path_rejected(managed: ManagedRoot) -> None:
    with pytest.raises(ManagedPathError, match="empty"):
        normalize_managed_path("")
    with pytest.raises(ManagedPathError, match="empty"):
        managed.resolve("")


def test_dot_path_rejected(managed: ManagedRoot) -> None:
    with pytest.raises(ManagedPathError):
        managed.resolve(".")
    with pytest.raises(ManagedPathError):
        managed.resolve("./")


def test_absolute_path_rejected(managed: ManagedRoot) -> None:
    with pytest.raises(ManagedPathError, match="absolute"):
        managed.resolve("/etc/passwd")
    with pytest.raises(ManagedPathError, match="absolute"):
        managed.resolve(str(managed.root / "escape.mp4"))


def test_drive_path_rejected(managed: ManagedRoot) -> None:
    with pytest.raises(ManagedPathError, match="drive"):
        managed.resolve("C:/windows/system32/evil.dll")
    with pytest.raises(ManagedPathError, match="drive"):
        managed.resolve("c:\\windows\\evil.exe")


def test_unc_path_rejected(managed: ManagedRoot) -> None:
    with pytest.raises(ManagedPathError, match="UNC"):
        managed.resolve("//server/share/evil.mp4")
    with pytest.raises(ManagedPathError, match="UNC"):
        managed.resolve("\\\\server\\share\\evil.mp4")


def test_parent_traversal_rejected(managed: ManagedRoot) -> None:
    for evil in ("../secret.txt", "a/../../secret.txt", "a/../..", ".."):
        with pytest.raises(ManagedPathError, match="parent traversal|must name"):
            managed.resolve(evil)


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    """A symlink inside root pointing outside must be rejected."""
    root = tmp_path / "managed"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    root.mkdir()
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    mr = ManagedRoot(root)
    with pytest.raises(ManagedPathError, match="escapes"):
        mr.resolve("link/secret.txt")


def test_database_file_rejected(protected_managed: ManagedRoot, tmp_path: Path) -> None:
    """The configured database file must never be a managed artifact."""
    db = tmp_path / "motionforge.db"
    db.write_text("sqlite", encoding="utf-8")
    with pytest.raises(ManagedPathError, match="database"):
        protected_managed.resolve(str(db))


def test_sibling_root_is_not_inside() -> None:
    """A sibling with a shared name prefix must not count as inside."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "data" / "root"
        sibling = Path(tmp) / "data" / "root_evil"
        root.mkdir(parents=True)
        sibling.mkdir()
        assert is_within(sibling / "x.bin", root) is False


# ── AC2: atomic writes ───────────────────────────────────────────────────────


def test_atomic_write_bytes_publishes_content(managed: ManagedRoot) -> None:
    digest, size = managed.atomic_write_bytes("a/b.bin", b"hello world")
    target = managed.root / "a" / "b.bin"
    assert target.read_bytes() == b"hello world"
    assert digest == hash_file(target)
    assert size == len(b"hello world")


def test_atomic_write_no_staging_leftovers(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("x.bin", b"payload")
    leftovers = [
        p
        for p in managed.root.rglob("*")
        if p.is_file() and (p.name.endswith(".staging") or p.name.startswith("."))
    ]
    assert leftovers == []


def test_atomic_write_overwrites_prior_content(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("x.bin", b"old")
    digest, _ = managed.atomic_write_bytes("x.bin", b"new")
    assert managed.root.joinpath("x.bin").read_bytes() == b"new"
    assert digest == hash_file(managed.root / "x.bin")


def test_atomic_write_creates_parent_dirs(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("deep/nested/dir/x.bin", b"data")
    assert (managed.root / "deep" / "nested" / "dir" / "x.bin").read_bytes() == b"data"


def test_atomic_write_stream_publishes(managed: ManagedRoot) -> None:
    digest, size = managed.atomic_write_stream(
        "clip.mp4", io.BytesIO(b"\x00" * 3000)
    )
    assert (managed.root / "clip.mp4").read_bytes() == b"\x00" * 3000
    assert size == 3000
    assert digest == hash_file(managed.root / "clip.mp4")


def test_atomic_write_failure_cleans_staging(
    managed: ManagedRoot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When publishing fails, the staging file is removed and prior content stays."""
    managed.atomic_write_bytes("x.bin", b"prior")

    def boom(src: str, dst: str) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="simulated replace failure"):
        managed.atomic_write_bytes("x.bin", b"new")

    assert (managed.root / "x.bin").read_bytes() == b"prior"
    staging_files = [
        p for p in managed.root.rglob("*") if p.is_file() and p.name.endswith(".staging")
    ]
    assert staging_files == []


def test_atomic_write_stream_failure_cleans_staging(
    managed: ManagedRoot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing stream copy must not leave a partial artifact or staging file."""
    class ExplodingStream(io.BytesIO):
        def read(self, size: int = -1) -> bytes:
            raise OSError("stream read failed")

    with pytest.raises(OSError, match="stream read failed"):
        managed.atomic_write_stream("clip.mp4", ExplodingStream(b"data"))
    assert not (managed.root / "clip.mp4").exists()
    staging_files = [
        p for p in managed.root.rglob("*") if p.is_file() and p.name.endswith(".staging")
    ]
    assert staging_files == []


# ── AC3: hash/size evidence and checksum gating ──────────────────────────────


def test_atomic_write_returns_hash_and_size(managed: ManagedRoot) -> None:
    payload = b"evidence bytes" * 100
    digest, size = managed.atomic_write_bytes("e.bin", payload)
    assert digest == hash_file(managed.root / "e.bin")
    assert size == len(payload)


def test_atomic_write_encoding_parameter(managed: ManagedRoot) -> None:
    digest, size = managed.atomic_write_bytes("note.txt", "héllo", encoding="utf-8")
    assert (managed.root / "note.txt").read_text(encoding="utf-8") == "héllo"
    assert digest == hash_file(managed.root / "note.txt")
    assert size == len("héllo".encode())


def test_expected_checksum_mismatch_cannot_publish(managed: ManagedRoot) -> None:
    """A wrong expected checksum must fail without publishing anything."""
    with pytest.raises(ArtifactWriteError, match="SHA-256 mismatch"):
        managed.atomic_write_bytes(
            "x.bin", b"content", expected_sha256="0" * 64
        )
    assert not (managed.root / "x.bin").exists()
    staging_files = [
        p for p in managed.root.rglob("*") if p.is_file() and p.name.endswith(".staging")
    ]
    assert staging_files == []


def test_expected_checksum_match_publishes(managed: ManagedRoot) -> None:
    payload = b"checksummed"
    expected = __import__("hashlib").sha256(payload).hexdigest()
    digest, _ = managed.atomic_write_bytes(
        "x.bin", payload, expected_sha256=expected
    )
    assert digest == expected
    assert (managed.root / "x.bin").read_bytes() == payload


def test_checksum_mismatch_preserves_prior_content(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("x.bin", b"prior")
    with pytest.raises(ArtifactWriteError, match="SHA-256 mismatch"):
        managed.atomic_write_bytes("x.bin", b"new", expected_sha256="f" * 64)
    assert (managed.root / "x.bin").read_bytes() == b"prior"


# ── AC4: Trash ───────────────────────────────────────────────────────────────


def test_trash_moves_file_into_trash_with_manifest(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("media/clip.mp4", b"video-bytes")
    before_hash = hash_file(managed.root / "media" / "clip.mp4")

    result = managed.trash("media/clip.mp4")

    assert not (managed.root / "media" / "clip.mp4").exists()
    trashed = managed.root / result.trashed_relative_path
    assert trashed.exists()
    assert trashed.read_bytes() == b"video-bytes"
    assert result.manifest.original_relative_path == "media/clip.mp4"
    assert result.manifest.sha256 == before_hash
    assert result.manifest.size_bytes == len(b"video-bytes")
    manifest_path = managed.root / result.manifest_relative_path
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["original_relative_path"] == "media/clip.mp4"


def test_trash_is_recoverable_via_restore(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("media/clip.mp4", b"recoverable")
    result = managed.trash("media/clip.mp4")

    restored = managed.restore(result.manifest_relative_path)

    assert restored.restored_relative_path == "media/clip.mp4"
    assert restored.sha256 == result.manifest.sha256
    assert (managed.root / "media" / "clip.mp4").read_bytes() == b"recoverable"
    assert not (managed.root / result.manifest_relative_path).exists()


def test_trash_names_are_collision_safe(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("a.mp4", b"one")
    managed.atomic_write_bytes("b.mp4", b"two")
    first = managed.trash("a.mp4")
    second = managed.trash("b.mp4")
    assert first.trashed_relative_path != second.trashed_relative_path
    assert first.manifest.trashed_name != second.manifest.trashed_name
    # Both trashed files must exist simultaneously.
    assert (managed.root / first.trashed_relative_path).exists()
    assert (managed.root / second.trashed_relative_path).exists()


def test_trash_missing_file_fails(managed: ManagedRoot) -> None:
    with pytest.raises(ArtifactWriteError, match="missing"):
        managed.trash("ghost.mp4")


def test_trash_directory_fails(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("dir/keep.txt", b"x")
    with pytest.raises(ArtifactWriteError, match="non-file"):
        managed.trash("dir")


def test_trash_cannot_cross_managed_boundary(tmp_path: Path) -> None:
    """A relative path resolving outside root must be rejected before any move."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.bin").write_bytes(b"secret")
    root = tmp_path / "managed"
    root.mkdir()
    mr = ManagedRoot(root)
    with pytest.raises(ManagedPathError):
        mr.trash(str(outside / "secret.bin"))
    assert (outside / "secret.bin").read_bytes() == b"secret"


def test_trash_rejects_database_file(protected_managed: ManagedRoot, tmp_path: Path) -> None:
    db = tmp_path / "motionforge.db"
    db.write_text("sqlite", encoding="utf-8")
    with pytest.raises(ManagedPathError, match="database"):
        protected_managed.trash(str(db))


def test_manifest_records_original_path_checksum_time(
    managed: ManagedRoot,
) -> None:
    managed.atomic_write_bytes("sub/f.bin", b"manifest-me")
    result = managed.trash("sub/f.bin")
    manifest = TrashManifest.load(managed.root / result.manifest_relative_path)
    assert manifest.original_relative_path == "sub/f.bin"
    assert manifest.sha256 == hash_file(managed.root / result.trashed_relative_path)
    assert manifest.size_bytes == len(b"manifest-me")
    assert manifest.trashed_at  # non-empty ISO timestamp


def test_trash_manifest_round_trip_after_rename(managed: ManagedRoot) -> None:
    """Restore works even when the trash entry dir is on the same root."""
    managed.atomic_write_bytes("x.bin", b"roundtrip")
    result = managed.trash("x.bin")
    restored = managed.restore(result.manifest_relative_path)
    assert (managed.root / "x.bin").read_bytes() == b"roundtrip"
    assert restored.sha256 == result.manifest.sha256


# ── AC5: restore safety ──────────────────────────────────────────────────────


def test_restore_refuses_overwrite(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("x.bin", b"original")
    result = managed.trash("x.bin")
    managed.atomic_write_bytes("x.bin", b"replacement")
    with pytest.raises(ArtifactWriteError, match="overwrite"):
        managed.restore(result.manifest_relative_path)
    # The replacement must be untouched.
    assert (managed.root / "x.bin").read_bytes() == b"replacement"


def test_restore_checksum_mismatch_rejected(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("x.bin", b"clean")
    result = managed.trash("x.bin")
    trashed = managed.root / result.trashed_relative_path
    trashed.write_bytes(b"tampered")
    with pytest.raises(ArtifactWriteError, match="checksum mismatch"):
        managed.restore(result.manifest_relative_path)
    # Trashed file remains for inspection; destination never created.
    assert trashed.read_bytes() == b"tampered"
    assert not (managed.root / "x.bin").exists()


def test_restore_without_checksum_verification(managed: ManagedRoot) -> None:
    managed.atomic_write_bytes("x.bin", b"content")
    result = managed.trash("x.bin")
    (managed.root / result.trashed_relative_path).write_bytes(b"changed")
    restored = managed.restore(result.manifest_relative_path, verify_checksum=False)
    assert (managed.root / "x.bin").read_bytes() == b"changed"
    assert restored.sha256 == result.manifest.sha256


def test_restore_rejects_manifest_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "managed"
    root.mkdir()
    outside_manifest = tmp_path / "fake-manifest.json"
    outside_manifest.write_text("{}", encoding="utf-8")
    mr = ManagedRoot(root)
    with pytest.raises(ManagedPathError):
        mr.restore(str(outside_manifest))


def test_restore_rejects_manifest_inside_root_but_outside_trash(
    managed: ManagedRoot,
) -> None:
    """A valid manifest + payload under managed root but outside .trash is rejected.

    Regression for PM correction: restore must require strict Trash-root
    containment, not merely managed-root containment.
    """
    managed.atomic_write_bytes("not-trash/manifest.json", b"")
    payload = b"payload-outside-trash"
    managed.atomic_write_bytes("not-trash/payload.bin", payload)
    entry = managed.root / "not-trash"
    manifest_path = entry / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "original_relative_path": "ok.bin",
                "sha256": hash_file(entry / "payload.bin"),
                "size_bytes": len(payload),
                "trashed_at": "2026-08-03T00:00:00+00:00",
                "trashed_name": "payload.bin",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ManagedPathError, match="Trash root"):
        managed.restore("not-trash/manifest.json")
    # The payload must remain untouched (no restore, no deletion).
    assert (entry / "payload.bin").read_bytes() == payload


def test_restore_rejects_trashed_file_outside_trash_root(managed: ManagedRoot) -> None:
    """A manifest under .trash whose payload resolves outside the Trash root is rejected."""
    entry = managed.trash_dir() / "evil-entry"
    entry.mkdir(parents=True)
    manifest_path = entry / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "original_relative_path": "ok.bin",
                "sha256": "0" * 64,
                "size_bytes": 1,
                "trashed_at": "2026-08-03T00:00:00+00:00",
                "trashed_name": "../managed/payload-outside-trash.bin",
            }
        ),
        encoding="utf-8",
    )
    # Payload lives inside managed root but outside the Trash root.
    managed.atomic_write_bytes("payload-outside-trash.bin", b"payload")
    with pytest.raises(ManagedPathError, match="must live in the manifest entry"):
        managed.restore(f"{managed.trash_dirname}/evil-entry/manifest.json")


def test_restore_rejects_payload_outside_manifest_entry(managed: ManagedRoot) -> None:
    """A manifest whose payload stays in Trash but outside its entry is rejected.

    Strict Trash containment means the payload must resolve inside the same
    Trash entry as the manifest.
    """
    entry = managed.trash_dir() / "entry-a"
    entry.mkdir(parents=True)
    # Payload in a different Trash entry (still inside Trash root).
    other_entry = managed.trash_dir() / "entry-b"
    other_entry.mkdir(parents=True)
    (other_entry / "payload.bin").write_bytes(b"payload")
    manifest_path = entry / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "original_relative_path": "ok.bin",
                "sha256": hash_file(other_entry / "payload.bin"),
                "size_bytes": 7,
                "trashed_at": "2026-08-03T00:00:00+00:00",
                "trashed_name": "../entry-b/payload.bin",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ManagedPathError, match="must live in the manifest entry"):
        managed.restore(f"{managed.trash_dirname}/entry-a/manifest.json")


def test_restore_validation_does_not_create_trash_dir(tmp_path: Path) -> None:
    """Validation itself must not create the Trash directory as a side effect."""
    root = tmp_path / "managed"
    root.mkdir()
    mr = ManagedRoot(root)
    assert not (root / ".trash").exists()  # trash dirname does not exist yet
    # A manifest outside root fails validation; Trash dir must stay absent.
    with pytest.raises(ManagedPathError):
        mr.restore(str(tmp_path / "nope.json"))
    assert not (root / ".trash").exists(), "restore validation created .trash"


def test_restore_rejects_escaped_original_path(managed: ManagedRoot) -> None:
    """A manifest whose original path escapes root must be rejected."""
    entry = managed.trash_dir() / "evil-entry"
    entry.mkdir(parents=True)
    trashed = entry / "f.bin"
    trashed.write_bytes(b"data")
    manifest_path = entry / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "original_relative_path": "../escape.bin",
                "sha256": hash_file(trashed),
                "size_bytes": 4,
                "trashed_at": "2026-08-03T00:00:00+00:00",
                "trashed_name": "f.bin",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ManagedPathError):
        managed.restore(f"{managed.trash_dirname}/evil-entry/manifest.json")


def test_restore_rejects_trashed_file_escape(managed: ManagedRoot) -> None:
    """A manifest pointing its trashed file outside root must be rejected."""
    entry = managed.trash_dir() / "evil-entry"
    entry.mkdir(parents=True)
    manifest_path = entry / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "original_relative_path": "ok.bin",
                "sha256": "0" * 64,
                "size_bytes": 1,
                "trashed_at": "2026-08-03T00:00:00+00:00",
                "trashed_name": "../outside.bin",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ManagedPathError):
        managed.restore(f"{managed.trash_dirname}/evil-entry/manifest.json")


def test_restore_malformed_manifest_rejected(managed: ManagedRoot) -> None:
    entry = managed.trash_dir() / "bad-entry"
    entry.mkdir(parents=True)
    (entry / "manifest.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ArtifactWriteError):
        managed.restore(f"{managed.trash_dirname}/bad-entry/manifest.json")


# ── Helper-level guarantees ──────────────────────────────────────────────────


def test_hash_file_matches_hashlib(managed: ManagedRoot) -> None:
    import hashlib

    payload = b"hash me" * 1000
    (managed.root / "h.bin").parent.mkdir(parents=True, exist_ok=True)
    (managed.root / "h.bin").write_bytes(payload)
    assert hash_file(managed.root / "h.bin") == hashlib.sha256(payload).hexdigest()


def test_normalize_rejects_nested_traversal(managed: ManagedRoot) -> None:
    with pytest.raises(ManagedPathError):
        normalize_managed_path("a/b/../../../etc/passwd")


def test_managed_root_never_touches_database(tmp_path: Path) -> None:
    """ManagedRoot construction/writes must not create any database file."""
    db = tmp_path / "motionforge.db"
    root = tmp_path / "managed"
    mr = ManagedRoot(root, database_path=db)
    mr.atomic_write_bytes("x.bin", b"data")
    assert not db.exists()
