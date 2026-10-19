"""Tests for Character Pack Validation Engine (S06-T03)."""

from __future__ import annotations

from pathlib import Path

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.characters import CharacterRepository
from app.workflow.character_validator import is_pack_publishable, validate_character_pack


def _session():
    service = deps._job_service
    assert service is not None
    return service._session_factory()


def test_validation_fails_on_missing_slots(_patch_project_root: Path) -> None:
    with _session() as session:
        repo = CharacterRepository(session)
        char = repo.create_character(DEFAULT_WORKSPACE_ID, "Test Char", "test_char")
        ver = repo.create_pack_version(char.id, DEFAULT_WORKSPACE_ID)

        errors = validate_character_pack(ver)
        assert len(errors) > 0
        assert "Missing required core pose slots" in errors[0]
        assert not is_pack_publishable(ver)
