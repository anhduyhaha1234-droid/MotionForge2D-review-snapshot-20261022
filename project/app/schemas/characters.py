"""Pydantic schemas for the Character Library API (S06-T01)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CharacterCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=64)
    character_type: str = Field("character", pattern="^(character|prop|other)$")
    symmetry: str = Field("symmetric", pattern="^(symmetric|asymmetric)$")
    description: str | None = None


class CharacterUpdateRequest(BaseModel):
    revision: int = Field(..., ge=1)
    name: str | None = Field(None, min_length=1, max_length=200)
    code: str | None = Field(None, min_length=1, max_length=64)
    character_type: str | None = Field(None, pattern="^(character|prop|other)$")
    symmetry: str | None = Field(None, pattern="^(symmetric|asymmetric)$")
    description: str | None = None


class CharacterArchiveRequest(BaseModel):
    revision: int = Field(..., ge=1)


class SetDefaultVersionRequest(BaseModel):
    revision: int = Field(..., ge=1)
    version_id: str | None = None


class AttachAssetRequest(BaseModel):
    pose_slot: str = Field(..., min_length=1, max_length=64)
    artifact_id: str = Field(..., min_length=1, max_length=36)


class PublishVersionRequest(BaseModel):
    revision: int = Field(..., ge=1)


class AssetData(BaseModel):
    id: str
    pack_version_id: str
    workspace_id: str
    pose_slot: str
    artifact_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_record(cls, record: Any) -> AssetData:
        return cls(
            id=record.id,
            pack_version_id=record.pack_version_id,
            workspace_id=record.workspace_id,
            pose_slot=record.pose_slot,
            artifact_id=record.artifact_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class PackVersionData(BaseModel):
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
    assets: list[AssetData]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_record(cls, record: Any) -> PackVersionData:
        return cls(
            id=record.id,
            character_id=record.character_id,
            workspace_id=record.workspace_id,
            version=record.version,
            status=record.status,
            validation_json=record.validation_json,
            published_at=record.published_at,
            revision=record.revision,
            created_at=record.created_at,
            updated_at=record.updated_at,
            archived_at=record.archived_at,
            assets=[AssetData.from_record(a) for a in record.assets],
        )


class CharacterData(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_record(cls, record: Any) -> CharacterData:
        return cls(
            id=record.id,
            workspace_id=record.workspace_id,
            name=record.name,
            code=record.code,
            character_type=record.character_type,
            symmetry=record.symmetry,
            status=record.status,
            default_version_id=record.default_version_id,
            description=record.description,
            revision=record.revision,
            created_at=record.created_at,
            updated_at=record.updated_at,
            archived_at=record.archived_at,
        )


class CharacterListResponse(BaseModel):
    workspace_id: str
    limit: int
    offset: int
    total: int
    characters: list[CharacterData]
