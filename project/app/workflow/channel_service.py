"""Channel workspace service — manage channels and project assignments."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.schemas import ChannelWorkspace


class ChannelService:
    """CRUD for channel workspaces."""

    def __init__(
        self,
        config: AppConfig,
        channels_file: Path | None = None,
    ) -> None:
        self._config = config
        # Test isolation hook: tests may inject a temporary channels file.
        # Default preserves the production behavior (root channels.json).
        self._channels_file = channels_file or (config.project_root / "channels.json")

    def _load_all(self) -> list[dict[str, Any]]:
        if not self._channels_file.exists():
            return []
        data = json.loads(self._channels_file.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Invalid channels file (expected a JSON list): {self._channels_file}")
        return data

    def _save_all(self, channels: list[dict[str, Any]]) -> None:
        self._channels_file.write_text(
            json.dumps(channels, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def create_channel(
        self,
        name: str,
        target_lang: str = "en",
        default_preset_id: str = "",
    ) -> ChannelWorkspace:
        """Create a new channel workspace."""
        channels = self._load_all()
        channel = ChannelWorkspace(
            channel_id=uuid.uuid4().hex[:12],
            name=name,
            target_lang=target_lang,
            default_preset_id=default_preset_id,
            created_at=datetime.now(UTC).isoformat(),
        )
        channels.append(channel.model_dump())
        self._save_all(channels)
        return channel

    def list_channels(self) -> list[ChannelWorkspace]:
        """List all channels."""
        return [
            ChannelWorkspace.model_validate(c)
            for c in self._load_all()
        ]

    def get_channel(self, channel_id: str) -> ChannelWorkspace | None:
        """Get a channel by ID."""
        for c in self._load_all():
            if c.get("channel_id") == channel_id:
                return ChannelWorkspace.model_validate(c)
        return None

    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel."""
        channels = self._load_all()
        original_len = len(channels)
        channels = [c for c in channels if c.get("channel_id") != channel_id]
        if len(channels) < original_len:
            self._save_all(channels)
            return True
        return False

    def get_projects_for_channel(
        self, channel_id: str, project_root: Path,
    ) -> list[dict[str, Any]]:
        """List all projects belonging to a channel."""
        projects_dir = project_root / "projects"
        if not projects_dir.exists():
            return []

        results: list[dict[str, Any]] = []
        for proj_dir in projects_dir.iterdir():
            if not proj_dir.is_dir():
                continue
            project_json = proj_dir / "project.json"
            if not project_json.exists():
                continue
            try:
                data = json.loads(project_json.read_text(encoding="utf-8"))
                if data.get("channel_id") == channel_id:
                    results.append({
                        "project_id": proj_dir.name,
                        "name": data.get("name", ""),
                        "task_status": data.get("task_status", "draft"),
                        "created_at": data.get("created_at", ""),
                        "scene_count": len(data.get("scenes", [])),
                        "object_count": len(data.get("objects", [])),
                    })
            except Exception:
                continue
        return results
