"""Preset character asset importer workflow (S06-T02).

Imports pre-existing preset pose assets into a new draft Character pack:

- Copies files into managed storage (``artifacts/characters/``) without ever
  mutating the original preset source files.
- Registers a managed ``Artifact`` row (state ``ready``) for every copied file
  with its SHA-256 checksum and byte size.
- Creates a draft ``Character`` plus its first ``CharacterPackVersion`` (v1).
- Attaches every available pose asset to its ``pose_slot`` (``front``,
  ``three_quarter``, ``side``, ``back``, ``sitting``, ``walking``).

The caller owns transaction commit; this service only flushes so the returned
records and artifact IDs are usable before commit.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.persistence.artifacts import ManagedRoot
from app.persistence.characters import (
    CharacterRecord,
    CharacterRepository,
    PackVersionRecord,
    _ensure_workspace,
)
from app.persistence.models import CORE_POSE_SLOTS, Artifact

#: Image extension → MIME type used for registered Artifact rows.
_MIME_BY_SUFFIX: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

#: Extensions probed when no explicit pose mapping entry is provided.
_POSE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp")


class CharacterPresetImporter:
    """Imports preset character image directories into workspace character packs."""

    def __init__(self, session: Session, storage_root: Path | None = None) -> None:
        self._session = session
        self._storage_root = storage_root or Path("artifacts")

    def import_preset(
        self,
        workspace_id: str,
        name: str,
        code: str,
        preset_dir: Path,
        pose_mapping: dict[str, str] | None = None,
        character_type: str = "character",
        symmetry: str = "symmetric",
        description: str | None = None,
    ) -> tuple[CharacterRecord, PackVersionRecord]:
        """Import a directory of pose images into a new draft Character pack.

        Args:
            workspace_id: Target workspace ID.
            name: Character display name.
            code: Unique character code.
            preset_dir: Directory containing preset pose image files.
            pose_mapping: Optional map of pose_slot -> filename (e.g.
                ``{'front': 'pose_0.png'}``). Defaults to ``<slot>.png`` /
                ``.jpg`` / ``.jpeg`` / ``.webp`` discovery.
            character_type: ``'character'``, ``'prop'``, or ``'other'``.
            symmetry: ``'symmetric'`` or ``'asymmetric'``.
            description: Optional character description.

        Returns:
            Tuple of (CharacterRecord, PackVersionRecord) with attached assets.

        Raises:
            FileNotFoundError: if *preset_dir* does not exist.
            CharacterCodeConflictError: if *code* is already active in the
                workspace.
        """
        if not preset_dir.is_dir():
            raise FileNotFoundError(f"Preset directory {preset_dir} does not exist")

        _ensure_workspace(self._session, workspace_id)
        repo = CharacterRepository(self._session)
        managed = ManagedRoot(self._storage_root)

        # 1. Create draft Character
        char_record = repo.create_character(
            workspace_id=workspace_id,
            name=name,
            code=code,
            character_type=character_type,
            symmetry=symmetry,
            description=description,
        )

        # 2. Create draft Pack Version 1
        ver_record = repo.create_pack_version(char_record.id, workspace_id)

        # 3. Process pose slots
        mapping = pose_mapping or {}
        for slot in CORE_POSE_SLOTS:
            src_file = self._find_pose_file(preset_dir, slot, mapping)
            if src_file is None:
                continue

            # Copy file into managed storage; the original is only read.
            dest_filename = f"{slot}_{uuid.uuid4().hex[:8]}{src_file.suffix}"
            rel_path = f"characters/{workspace_id}/{char_record.id}/{dest_filename}"
            with src_file.open("rb") as stream:
                sha256, size_bytes = managed.atomic_write_stream(rel_path, stream)

            # Register Artifact in state ready
            art = Artifact(
                workspace_id=workspace_id,
                kind="image",
                relative_path=rel_path,
                state="ready",
                sha256=sha256,
                size_bytes=size_bytes,
                mime_type=_MIME_BY_SUFFIX.get(
                    src_file.suffix.lower(), "application/octet-stream"
                ),
            )
            self._session.add(art)
            self._session.flush()

            # Attach asset to pose slot
            repo.attach_asset(
                version_id=ver_record.id,
                workspace_id=workspace_id,
                pose_slot=slot,
                artifact_id=art.id,
            )

        # Refetch pack version with attached assets
        updated_ver = repo.get_pack_version(ver_record.id, workspace_id)
        return char_record, updated_ver

    def _find_pose_file(
        self, preset_dir: Path, slot: str, mapping: dict[str, str]
    ) -> Path | None:
        """Locate the preset source file for a pose slot, if present."""
        candidate_name = mapping.get(slot)
        if candidate_name:
            candidate = preset_dir / candidate_name
            if candidate.is_file():
                return candidate
            return None
        for ext in _POSE_EXTENSIONS:
            candidate = preset_dir / f"{slot}{ext}"
            if candidate.is_file():
                return candidate
        return None
