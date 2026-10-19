# Watch Folder Automation Pattern

Auto-process video files dropped into a monitored directory.

## Pattern

```python
import asyncio
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}

class WatchFolderManager:
    def __init__(self, editor, config_path: str):
        self._editor = editor
        self._config_path = config_path
        self._config = {}           # loaded from config_path
        self._processed = set()     # set of already-processed file paths
        self._running = False
        self._task = None           # asyncio.Task

    async def _watch_loop(self):
        input_dir = Path(self._config["input_dir"]).resolve()
        output_dir = Path(self._config["output_dir"]).resolve()
        interval = self._config.get("poll_interval", 5)

        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        while self._running:
            try:
                for f in input_dir.iterdir():
                    if f.suffix.lower() in VIDEO_EXTENSIONS and str(f) not in self._processed:
                        await self._process_file(str(f), str(output_dir))
                        self._processed.add(str(f))
            except Exception as e:
                # Log error but keep watching
                pass
            await asyncio.sleep(interval)
```

## Key Design Decisions

1. **Track processed files by path** — simple `set` of already-processed paths. Survives in-memory across polls but not server restarts. For persistence, write paths to a JSON file.

2. **Polling vs inotify/watchdog** — polling is simpler and cross-platform. `watchdog` library provides filesystem events but adds a dependency and has platform-specific quirks. Use polling for MVP; switch to watchdog if latency matters.

3. **Config persistence** — store watch folder config in a JSON file (e.g. `data/watch_folder.json`) separate from the main app settings. The config includes: `input_dir`, `output_dir`, `preset` (edit parameters), `enabled`, `poll_interval`.

4. **Preset dict** — the edit preset is a dict of parameters to pass to the editor (crop, speed, flip, normalize, etc.). This avoids a separate schema; the editor already validates these.

5. **Start/stop from API** — expose `POST /media/watch-folder` to update config and toggle watching. The API starts/stops the asyncio task based on the `enabled` flag.

## FastAPI Integration

```python
# In v1.py
watch_folder_mgr = WatchFolderManager()

@router.get("/media/watch-folder")
async def get_watch_folder():
    return watch_folder_mgr.get_config()

@router.post("/media/watch-folder")
async def set_watch_folder(body: WatchFolderConfig):
    return watch_folder_mgr.update_config(**body.model_dump())
```

**Pitfall:** The watch loop starts an `asyncio.Task` via `loop.create_task()`. If called before the event loop is running (e.g. during module import), it will raise `RuntimeError`. Gate startup on server startup event or check `asyncio.get_event_loop().is_running()`.
