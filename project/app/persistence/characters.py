"""Durable Character Library persistence service and repository (S06-T01).

Implements workspace-scoped Character, Pack Version, and Asset CRUD and publishing
under the S06-T01 domain contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.persistence.models import (
    CORE_POSE_SLOTS,
    Artifact,
    Character,
    CharacterAsset,
    CharacterPackVersion,
)


class CharacterError(Exception):
    """Base exception for Character Library operations."""


class CharacterNotFoundError(CharacterError):
    """Character row not found in workspace."""


class CharacterConflictError(CharacterError):
    """CAS revision mismatch or stale state."""


class CharacterCodeConflictError(CharacterError):
    """Active character code collision in workspace."""


class PackVersionNotFoundError(CharacterError):
    """Pack version not found."""


class PackVersionConflictError(CharacterError):
    """Pack version CAS revision or version collision."""


class PackVersionImmutableError(CharacterError):
    """Attempted modification of a published, immutable Pack Version."""


class PublishValidationFailedError(CharacterError):
    """Publish gate rejected due to missing Core slots or invalid assets."""

    def __init__(self, message: str, missing_slots: list[str]) -> None:
        super().__init__(message)
        self.missing_slots = missing_slots


@dataclass(frozen=True)
class AssetRecord:
    id: str
    pack_version_id: str
    workspace_id: str
    pose_slot: str
    artifact_id: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PackVersionRecord:
    id: str
    character_id: str
    workspace_id: str
    version: int
    status: str
    validation_json: str | None
    published_at: datetime | None
    revision: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    assets: list[AssetRecord]


@dataclass(frozen=True)
class CharacterRecord:
    id: str
    workspace_id: str
    name: str
    code: str
    character_type: str
    symmetry: str
    status: str
    default_version_id: str | None
    description: str | None
    revision: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


def normalize_character_code(code: str) -> str:
    """Trim and validate character code."""
    normalized = code.strip()
    if not normalized:
        raise ValueError("Character code cannot be empty")
    if len(normalized) > 64:
        raise ValueError("Character code cannot exceed 64 characters")
    return normalized


def _map_asset(asset: CharacterAsset) -> AssetRecord:
    return AssetRecord(
        id=asset.id,
        pack_version_id=asset.pack_version_id,
        workspace_id=asset.workspace_id,
        pose_slot=asset.pose_slot,
        artifact_id=asset.artifact_id,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _map_version(version: CharacterPackVersion) -> PackVersionRecord:
    return PackVersionRecord(
        id=version.id,
        character_id=version.character_id,
        workspace_id=version.workspace_id,
        version=version.version,
        status=version.status,
        validation_json=version.validation_json,
        published_at=version.published_at,
        revision=version.revision,
        created_at=version.created_at,
        updated_at=version.updated_at,
        archived_at=version.archived_at,
        assets=[_map_asset(a) for a in (version.assets or [])],
    )


def _map_character(char: Character) -> CharacterRecord:
    return CharacterRecord(
        id=char.id,
        workspace_id=char.workspace_id,
        name=char.name,
        code=char.code,
        character_type=char.character_type,
        symmetry=char.symmetry,
        status=char.status,
        default_version_id=char.default_version_id,
        description=char.description,
        revision=char.revision,
        created_at=char.created_at,
        updated_at=char.updated_at,
        archived_at=char.archived_at,
    )


def _ensure_workspace(session: Session, workspace_id: str) -> None:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from app.persistence.models import Workspace
    session.execute(
        sqlite_insert(Workspace)
        .values(id=workspace_id, name=workspace_id)
        .on_conflict_do_nothing(index_elements=[Workspace.id])
    )


class CharacterRepository:
    """Read/write repository for Character Library within one Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_character(
        self,
        workspace_id: str,
        name: str,
        code: str,
        character_type: str = "character",
        symmetry: str = "symmetric",
        description: str | None = None,
    ) -> CharacterRecord:
        _ensure_workspace(self._session, workspace_id)
        norm_code = normalize_character_code(code)
        norm_name = name.strip()
        if not norm_name:
            raise ValueError("Character name cannot be empty")

        # Check code collision among active characters
        existing = self._session.scalar(
            select(Character).where(
                Character.workspace_id == workspace_id,
                func.lower(Character.code) == norm_code.lower(),
                Character.status != "archived",
            )
        )
        if existing is not None:
            raise CharacterCodeConflictError(
                f"Active character code {norm_code!r} already exists in workspace"
            )

        char = Character(
            workspace_id=workspace_id,
            name=norm_name,
            code=norm_code,
            character_type=character_type,
            symmetry=symmetry,
            status="draft",
            description=description,
            revision=1,
        )
        self._session.add(char)
        self._session.flush()
        return _map_character(char)

    def list_characters(
        self,
        workspace_id: str,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CharacterRecord], int]:
        query = select(Character).where(Character.workspace_id == workspace_id)
        if not include_archived:
            query = query.where(Character.status != "archived")

        total = self._session.scalar(
            select(func.count(Character.id)).where(
                Character.workspace_id == workspace_id,
                *( [] if include_archived else [Character.status != "archived"] )
            )
        ) or 0

        query = query.order_by(Character.created_at.desc(), Character.id.asc())
        rows = self._session.scalars(query.offset(offset).limit(limit)).all()
        return [_map_character(c) for c in rows], int(total)

    def get_character(self, character_id: str, workspace_id: str) -> CharacterRecord:
        char = self._session.scalar(
            select(Character).where(
                Character.id == character_id,
                Character.workspace_id == workspace_id,
            )
        )
        if char is None:
            raise CharacterNotFoundError(f"Character {character_id!r} not found")
        return _map_character(char)

    def update_character(
        self,
        character_id: str,
        workspace_id: str,
        revision: int,
        name: str | None = None,
        code: str | None = None,
        character_type: str | None = None,
        symmetry: str | None = None,
        description: str | None = None,
    ) -> CharacterRecord:
        char = self._session.scalar(
            select(Character).where(
                Character.id == character_id,
                Character.workspace_id == workspace_id,
            )
        )
        if char is None:
            raise CharacterNotFoundError(f"Character {character_id!r} not found")

        if char.revision != revision:
            raise CharacterConflictError(
                f"CAS revision mismatch: expected {char.revision}, got {revision}"
            )

        if code is not None:
            norm_code = normalize_character_code(code)
            if norm_code.lower() != char.code.lower():
                existing = self._session.scalar(
                    select(Character).where(
                        Character.workspace_id == workspace_id,
                        func.lower(Character.code) == norm_code.lower(),
                        Character.status != "archived",
                        Character.id != character_id,
                    )
                )
                if existing is not None:
                    raise CharacterCodeConflictError(
                        f"Active character code {norm_code!r} already in use"
                    )
                char.code = norm_code

        if name is not None:
            norm_name = name.strip()
            if not norm_name:
                raise ValueError("Character name cannot be empty")
            char.name = norm_name

        if character_type is not None:
            char.character_type = character_type
        if symmetry is not None:
            char.symmetry = symmetry
        if description is not None:
            char.description = description

        char.revision += 1
        self._session.flush()
        return _map_character(char)

    def archive_character(
        self, character_id: str, workspace_id: str, revision: int
    ) -> CharacterRecord:
        char = self._session.scalar(
            select(Character).where(
                Character.id == character_id,
                Character.workspace_id == workspace_id,
            )
        )
        if char is None:
            raise CharacterNotFoundError(f"Character {character_id!r} not found")

        if char.status == "archived":
            return _map_character(char)

        if char.revision != revision:
            raise CharacterConflictError(
                f"CAS revision mismatch: expected {char.revision}, got {revision}"
            )

        char.status = "archived"
        char.archived_at = datetime.now(UTC)
        char.revision += 1
        self._session.flush()
        return _map_character(char)

    def create_pack_version(
        self, character_id: str, workspace_id: str
    ) -> PackVersionRecord:
        _ensure_workspace(self._session, workspace_id)
        char = self._session.scalar(
            select(Character).where(
                Character.id == character_id,
                Character.workspace_id == workspace_id,
            )
        )
        if char is None:
            raise CharacterNotFoundError(f"Character {character_id!r} not found")

        max_ver = self._session.scalar(
            select(func.max(CharacterPackVersion.version)).where(
                CharacterPackVersion.character_id == character_id
            )
        ) or 0

        next_ver = max_ver + 1
        version = CharacterPackVersion(
            character_id=character_id,
            workspace_id=workspace_id,
            version=next_ver,
            status="draft",
            revision=1,
        )
        self._session.add(version)
        self._session.flush()
        return _map_version(version)

    def list_pack_versions(
        self, character_id: str, workspace_id: str
    ) -> list[PackVersionRecord]:
        versions = self._session.scalars(
            select(CharacterPackVersion)
            .options(joinedload(CharacterPackVersion.assets))
            .where(
                CharacterPackVersion.character_id == character_id,
                CharacterPackVersion.workspace_id == workspace_id,
            )
            .order_by(CharacterPackVersion.version.asc())
        ).unique().all()
        return [_map_version(v) for v in versions]

    def get_pack_version(
        self, version_id: str, workspace_id: str
    ) -> PackVersionRecord:
        version = self._session.scalar(
            select(CharacterPackVersion)
            .options(joinedload(CharacterPackVersion.assets))
            .where(
                CharacterPackVersion.id == version_id,
                CharacterPackVersion.workspace_id == workspace_id,
            )
        )
        if version is None:
            raise PackVersionNotFoundError(f"Pack version {version_id!r} not found")
        return _map_version(version)

    def attach_asset(
        self,
        version_id: str,
        workspace_id: str,
        pose_slot: str,
        artifact_id: str,
    ) -> AssetRecord:
        _ensure_workspace(self._session, workspace_id)
        version = self._session.scalar(
            select(CharacterPackVersion)
            .options(joinedload(CharacterPackVersion.assets))
            .where(
                CharacterPackVersion.id == version_id,
                CharacterPackVersion.workspace_id == workspace_id,
            )
        )
        if version is None:
            raise PackVersionNotFoundError(f"Pack version {version_id!r} not found")

        if version.status == "published":
            raise PackVersionImmutableError("Cannot attach assets to a published Pack Version")

        artifact = self._session.scalar(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.workspace_id == workspace_id,
            )
        )
        if artifact is None or artifact.state != "ready":
            raise ValueError(f"Artifact {artifact_id!r} is invalid or not in ready state")

        existing_asset = next(
            (a for a in version.assets if a.pose_slot == pose_slot), None
        )
        if existing_asset is not None:
            existing_asset.artifact_id = artifact_id
            existing_asset.updated_at = datetime.now(UTC)
            self._session.flush()
            return _map_asset(existing_asset)

        asset = CharacterAsset(
            pack_version_id=version_id,
            workspace_id=workspace_id,
            pose_slot=pose_slot,
            artifact_id=artifact_id,
        )
        self._session.add(asset)
        self._session.flush()
        return _map_asset(asset)

    def publish_pack_version(
        self, version_id: str, workspace_id: str, revision: int
    ) -> PackVersionRecord:
        version = self._session.scalar(
            select(CharacterPackVersion)
            .options(joinedload(CharacterPackVersion.assets))
            .where(
                CharacterPackVersion.id == version_id,
                CharacterPackVersion.workspace_id == workspace_id,
            )
        )
        if version is None:
            raise PackVersionNotFoundError(f"Pack version {version_id!r} not found")

        if version.revision != revision:
            raise PackVersionConflictError(
                f"CAS revision mismatch: expected {version.revision}, got {revision}"
            )

        if version.status == "published":
            return _map_version(version)

        present_slots = {a.pose_slot for a in version.assets}
        missing_slots = [slot for slot in CORE_POSE_SLOTS if slot not in present_slots]

        if missing_slots:
            raise PublishValidationFailedError(
                f"Cannot publish pack version: missing Core pose slots {missing_slots}",
                missing_slots=missing_slots,
            )

        version.status = "published"
        version.published_at = datetime.now(UTC)
        version.validation_json = json.dumps({
            "validated_at": datetime.now(UTC).isoformat(),
            "core_slots": list(CORE_POSE_SLOTS),
            "asset_count": len(version.assets),
        })
        version.revision += 1
        self._session.flush()

        # Update character status to ready if it was draft
        char = self._session.scalar(
            select(Character).where(Character.id == version.character_id)
        )
        if char is not None and char.status in ("draft", "needs_review"):
            char.status = "ready"
            if char.default_version_id is None:
                char.default_version_id = version.id
            char.revision += 1
            self._session.flush()

        return _map_version(version)

    def set_default_version(
        self, character_id: str, workspace_id: str, version_id: str | None, revision: int
    ) -> CharacterRecord:
        char = self._session.scalar(
            select(Character).where(
                Character.id == character_id,
                Character.workspace_id == workspace_id,
            )
        )
        if char is None:
            raise CharacterNotFoundError(f"Character {character_id!r} not found")

        if char.revision != revision:
            raise CharacterConflictError(
                f"CAS revision mismatch: expected {char.revision}, got {revision}"
            )

        if version_id is not None:
            version = self._session.scalar(
                select(CharacterPackVersion).where(
                    CharacterPackVersion.id == version_id,
                    CharacterPackVersion.character_id == character_id,
                    CharacterPackVersion.workspace_id == workspace_id,
                )
            )
            if version is None or version.status == "archived":
                raise PackVersionNotFoundError(
                    f"Version {version_id!r} not found or is archived"
                )

        char.default_version_id = version_id
        char.revision += 1
        self._session.flush()
        return _map_character(char)
