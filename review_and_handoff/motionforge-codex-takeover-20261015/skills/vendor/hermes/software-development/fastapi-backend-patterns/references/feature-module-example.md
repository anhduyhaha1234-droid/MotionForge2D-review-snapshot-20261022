# Feature Module Example: Channel Workspace

Concrete example of the 4-layer pattern from the MotionForge2D project.

## Layer 1: Schema additions

```python
# In app/schemas/__init__.py — add BEFORE the main ProjectData model

class TaskStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY_TO_STITCH = "ready_to_stitch"
    COMPLETED = "completed"

class ChannelWorkspace(BaseModel):
    """A channel workspace grouping related projects."""
    channel_id: str = ""
    name: str = ""
    target_lang: str = "en"
    default_preset_id: str = ""
    created_at: str = ""

# In ProjectData, add fields with safe defaults:
#   channel_id: str = ""
#   task_status: str = "draft"
```

## Layer 2: Service class

```python
# app/workflow/channel_service.py
from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime        # ← alphabetical: UTC before datetime
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.schemas import ChannelWorkspace


class ChannelService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._channels_file = config.project_root / "channels.json"

    def _load_all(self) -> list[dict[str, Any]]:
        if not self._channels_file.exists():
            return []
        return json.loads(self._channels_file.read_text(encoding="utf-8"))

    def _save_all(self, channels: list[dict[str, Any]]) -> None:
        self._channels_file.write_text(
            json.dumps(channels, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def create_channel(self, name: str, **kw) -> ChannelWorkspace:
        channels = self._load_all()
        channel = ChannelWorkspace(
            channel_id=uuid.uuid4().hex[:12],
            name=name,
            created_at=datetime.now(UTC).isoformat(),  # ← NOT timezone.utc
            **kw,
        )
        channels.append(channel.model_dump())
        self._save_all(channels)
        return channel

    def list_channels(self) -> list[ChannelWorkspace]:
        return [ChannelWorkspace.model_validate(c) for c in self._load_all()]

    def get_channel(self, channel_id: str) -> ChannelWorkspace | None:
        for c in self._load_all():
            if c.get("channel_id") == channel_id:
                return ChannelWorkspace.model_validate(c)
        return None

    def delete_channel(self, channel_id: str) -> bool:
        channels = self._load_all()
        original_len = len(channels)
        channels = [c for c in channels if c.get("channel_id") != channel_id]
        if len(channels) < original_len:
            self._save_all(channels)
            return True
        return False
```

## Layer 3: Route additions (append to existing router)

```python
# At end of app/api/routes/projects.py

class CreateChannelRequest(BaseModel):
    name: str
    target_lang: str = "en"

@router.post("/channels")
def create_channel(body: CreateChannelRequest) -> dict:
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415
    config = get_config()
    svc = ChannelService(config)
    return svc.create_channel(body.name, target_lang=body.target_lang).model_dump()

@router.get("/channels")
def list_channels() -> list[dict]:
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415
    return [c.model_dump() for c in ChannelService(get_config()).list_channels()]

@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: str) -> dict:
    from app.workflow.channel_service import ChannelService  # noqa: PLC0415
    if not ChannelService(get_config()).delete_channel(channel_id):
        raise HTTPException(404, "Channel not found")
    return {"ok": True}
```

## Layer 4: Tests

```python
# tests/test_channel_workspace.py
from __future__ import annotations
import pytest
from app.config import config as app_config
from app.schemas import ChannelWorkspace, TaskStatus
from app.workflow.channel_service import ChannelService

@pytest.fixture
def svc() -> ChannelService:
    return ChannelService(app_config)

class TestChannelCRUD:
    def test_create_channel(self, svc):
        ch = svc.create_channel("Test", target_lang="en")
        assert ch.channel_id and ch.name == "Test" and ch.created_at

    def test_get_channel(self, svc):
        ch = svc.create_channel("Find Me")
        assert svc.get_channel(ch.channel_id).name == "Find Me"

    def test_delete_channel(self, svc):
        ch = svc.create_channel("Delete Me")
        assert svc.delete_channel(ch.channel_id) is True
        assert svc.get_channel(ch.channel_id) is None

class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.DRAFT == "draft"
        assert TaskStatus.COMPLETED == "completed"
```
