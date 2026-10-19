"""Tests for channel workspace service.

All tests use an isolated temporary channels.json (never the production-root
file) via the ``channels_file`` injection hook on ``ChannelService``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import AppConfig
from app.schemas import ChannelWorkspace, TaskStatus
from app.workflow.channel_service import ChannelService


@pytest.fixture
def isolated_channels_file(tmp_path) -> Path:
    """Function-scoped temporary channels.json (isolated per test, order-free)."""
    return tmp_path / "channels.json"


@pytest.fixture
def svc(isolated_channels_file) -> ChannelService:
    return ChannelService(
        AppConfig(project_root=isolated_channels_file.parent),
        channels_file=isolated_channels_file,
    )


class TestChannelCRUD:
    def test_create_channel(self, svc: ChannelService) -> None:
        """Create a channel returns valid workspace."""
        ch = svc.create_channel("Test Channel", target_lang="en")
        assert ch.channel_id
        assert ch.name == "Test Channel"
        assert ch.target_lang == "en"
        assert ch.created_at

    def test_list_channels(self, svc: ChannelService) -> None:
        """List returns created channels."""
        svc.create_channel("Channel A")
        svc.create_channel("Channel B")
        channels = svc.list_channels()
        assert len(channels) >= 2

    def test_get_channel(self, svc: ChannelService) -> None:
        """Get by ID returns correct channel."""
        ch = svc.create_channel("Find Me")
        found = svc.get_channel(ch.channel_id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_nonexistent_channel(self, svc: ChannelService) -> None:
        """Get nonexistent channel returns None."""
        assert svc.get_channel("nonexistent") is None

    def test_delete_channel(self, svc: ChannelService) -> None:
        """Delete removes channel."""
        ch = svc.create_channel("Delete Me")
        assert svc.delete_channel(ch.channel_id) is True
        assert svc.get_channel(ch.channel_id) is None

    def test_delete_nonexistent(self, svc: ChannelService) -> None:
        """Delete nonexistent returns False."""
        assert svc.delete_channel("nonexistent") is False


class TestTaskStatus:
    def test_task_status_values(self) -> None:
        """TaskStatus enum has expected values."""
        assert TaskStatus.DRAFT == "draft"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.READY_TO_STITCH == "ready_to_stitch"
        assert TaskStatus.COMPLETED == "completed"


class TestChannelWorkspace:
    def test_default_values(self) -> None:
        """ChannelWorkspace has correct defaults."""
        ch = ChannelWorkspace()
        assert ch.channel_id == ""
        assert ch.name == ""
        assert ch.target_lang == "en"


class TestIsolation:
    def test_service_writes_isolated_file_only(self, svc: ChannelService) -> None:
        """CRUD writes only the injected temp file, never production channels.json.

        Regression for S00-T01: root channels.json must be untouched by tests.
        """
        root_channels = Path.cwd() / "channels.json"
        before = root_channels.read_bytes() if root_channels.exists() else None

        svc.create_channel("Isolated Channel")
        svc.create_channel("Isolated Channel B")
        assert len(svc.list_channels()) == 2

        after = root_channels.read_bytes() if root_channels.exists() else None
        assert after == before, "root channels.json was modified by the service"

    def test_isolated_file_is_temporary(
        self, svc: ChannelService, isolated_channels_file
    ) -> None:
        """The injected channels file lives under pytest tmp, not the repo."""
        import tempfile

        tmp_root = Path(tempfile.gettempdir()).resolve()
        assert str(isolated_channels_file.resolve()).startswith(str(tmp_root))
        svc.create_channel("Temp Check")
        assert isolated_channels_file.is_file()
        data = json.loads(isolated_channels_file.read_text(encoding="utf-8"))
        assert any(c["name"] == "Temp Check" for c in data)
