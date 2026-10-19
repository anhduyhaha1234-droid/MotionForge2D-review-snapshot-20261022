"""Tests for Character Preset Importer workflow (S06-T02).

Covers the S06-T02 contract:

- R1: original preset files are never mutated.
- R2: every copied asset has a registered SHA-256 checksum and byte size.
- R3: managed ``Artifact`` rows are registered in state ``ready``.
- R4: a draft ``Character`` and ``CharacterPackVersion`` (v1) are created.
- R5: available pose assets are attached to their ``pose_slot``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.artifacts import hash_file
from app.persistence.characters import CharacterCodeConflictError, CharacterRepository
from app.persistence.models import CORE_POSE_SLOTS, Artifact
from app.workflow.character_preset_importer import CharacterPresetImporter


def _session():
    service = deps._job_service
    assert service is not None
    return service._session_factory()


def _make_preset_dir(tmp_path: Path, files: dict[str, bytes]) -> Path:
    """Create a preset directory with the given filename -> bytes content."""
    preset_dir = tmp_path / "preset"
    preset_dir.mkdir()
    for filename, data in files.items():
        (preset_dir / filename).write_bytes(data)
    return preset_dir


def _artifacts_for(workspace_id: str) -> list[Artifact]:
    """Query the durable DB for image artifacts in the workspace."""
    with _session() as session:
        return (
            session.query(Artifact)
            .filter(Artifact.workspace_id == workspace_id)
            .order_by(Artifact.relative_path.asc())
            .all()
        )


def test_import_preset_copies_assets_and_attaches(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    # Create fake preset directory with pose images
    preset_dir = _make_preset_dir(
        tmp_path,
        {
            "front.png": b"fake front image bytes",
            "side.png": b"fake side image bytes",
            "back.png": b"fake back image bytes",
        },
    )

    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        char, ver = importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="Preset Stickman",
            code="preset_stickman",
            preset_dir=preset_dir,
            description="Imported stickman preset",
        )
        session.commit()

        assert char.name == "Preset Stickman"
        assert char.code == "preset_stickman"
        assert char.status == "draft"
        assert ver.version == 1
        assert len(ver.assets) == 3

        attached_slots = {a.pose_slot for a in ver.assets}
        assert attached_slots == {"front", "side", "back"}

    # Verify original preset files were not mutated
    assert (preset_dir / "front.png").read_bytes() == b"fake front image bytes"
    assert (preset_dir / "side.png").read_bytes() == b"fake side image bytes"


def test_artifacts_registered_ready_with_sha256_and_size(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    preset_dir = _make_preset_dir(
        tmp_path,
        {
            "front.png": b"front-bytes",
            "side.jpg": b"side-bytes",
            "back.webp": b"back-bytes",
        },
    )
    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        char, ver = importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="Artifact Check",
            code="artifact_check",
            preset_dir=preset_dir,
        )
        session.commit()

        assert len(ver.assets) == 3

    artifacts = _artifacts_for(DEFAULT_WORKSPACE_ID)
    assert len(artifacts) == 3

    # Every artifact: ready state, valid 64-char sha256, size matches bytes
    for art in artifacts:
        assert art.state == "ready"
        assert art.sha256 is not None and len(art.sha256) == 64
        assert art.size_bytes is not None and art.size_bytes > 0

    # Managed files exist on disk and match the originals byte-for-byte
    expected = {
        "front": ("front.png", b"front-bytes", "image/png"),
        "side": ("side.jpg", b"side-bytes", "image/jpeg"),
        "back": ("back.webp", b"back-bytes", "image/webp"),
    }
    by_slot = {a.pose_slot: a for a in _assets_for_version(ver.id)}
    for slot, (filename, content, mime) in expected.items():
        asset = by_slot[slot]
        art = next(a for a in artifacts if a.id == asset.artifact_id)
        assert art.mime_type == mime
        managed_file = managed_root / art.relative_path
        assert managed_file.is_file()
        assert managed_file.read_bytes() == content
        # sha256 registered equals the sha256 of the copied bytes
        assert art.sha256 == hash_file(managed_file)
        assert art.sha256 == hash_file(preset_dir / filename)
        assert art.size_bytes == len(content)


def _assets_for_version(version_id: str):
    """Return AssetRecord rows for a pack version (fresh query)."""
    with _session() as session:
        repo = CharacterRepository(session)
        record = repo.get_pack_version(version_id, DEFAULT_WORKSPACE_ID)
        return record.assets


def test_import_with_explicit_pose_mapping(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    preset_dir = _make_preset_dir(
        tmp_path,
        {
            "pose_0.png": b"front bytes",
            "pose_1.png": b"walking bytes",
            "unused.png": b"unused bytes",
        },
    )
    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        char, ver = importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="Mapped Pose",
            code="mapped_pose",
            preset_dir=preset_dir,
            pose_mapping={"front": "pose_0.png", "walking": "pose_1.png"},
        )
        session.commit()

        assert len(ver.assets) == 2
        assert {a.pose_slot for a in ver.assets} == {"front", "walking"}


def test_import_all_core_slots(tmp_path: Path, _patch_project_root: Path) -> None:
    preset_dir = _make_preset_dir(
        tmp_path,
        {f"{slot}.png": f"{slot} bytes".encode() for slot in CORE_POSE_SLOTS},
    )
    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        char, ver = importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="Full Pack",
            code="full_pack",
            preset_dir=preset_dir,
        )
        session.commit()

        assert len(ver.assets) == len(CORE_POSE_SLOTS)
        assert {a.pose_slot for a in ver.assets} == set(CORE_POSE_SLOTS)


def test_import_missing_preset_dir_raises(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        with pytest.raises(FileNotFoundError):
            importer.import_preset(
                workspace_id=DEFAULT_WORKSPACE_ID,
                name="Missing",
                code="missing",
                preset_dir=tmp_path / "does_not_exist",
            )


def test_import_empty_preset_creates_draft_pack(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    preset_dir = _make_preset_dir(tmp_path, {})
    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        char, ver = importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="Empty Pack",
            code="empty_pack",
            preset_dir=preset_dir,
        )
        session.commit()

        assert char.status == "draft"
        assert ver.version == 1
        assert ver.status == "draft"
        assert ver.assets == []


def test_import_never_mutates_original_files(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    originals = {
        "front.png": b"original front content",
        "back.jpg": b"original back content",
    }
    preset_dir = _make_preset_dir(tmp_path, originals)

    # Snapshot original hashes before import
    before = {name: hash_file(preset_dir / name) for name in originals}

    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="No Mutate",
            code="no_mutate",
            preset_dir=preset_dir,
        )
        session.commit()

    # Original files still exist with identical bytes
    after = {name: hash_file(preset_dir / name) for name in originals}
    assert before == after
    assert (preset_dir / "front.png").read_bytes() == originals["front.png"]
    assert (preset_dir / "back.jpg").read_bytes() == originals["back.jpg"]


def test_import_duplicate_code_raises_conflict(
    tmp_path: Path, _patch_project_root: Path
) -> None:
    preset_dir = _make_preset_dir(tmp_path, {"front.png": b"front bytes"})
    managed_root = tmp_path / "managed_artifacts"
    managed_root.mkdir()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        importer.import_preset(
            workspace_id=DEFAULT_WORKSPACE_ID,
            name="First",
            code="dup_code",
            preset_dir=preset_dir,
        )
        session.commit()

    with _session() as session:
        importer = CharacterPresetImporter(session, storage_root=managed_root)
        with pytest.raises(CharacterCodeConflictError):
            importer.import_preset(
                workspace_id=DEFAULT_WORKSPACE_ID,
                name="Second",
                code="dup_code",
                preset_dir=preset_dir,
            )
