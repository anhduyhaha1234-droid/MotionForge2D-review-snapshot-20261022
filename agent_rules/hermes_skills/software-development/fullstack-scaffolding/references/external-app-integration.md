# External App Integration Pattern (CapCut PC)

Pattern for integrating with desktop apps that have no public API — use direct config file editing (Engine 1) and GUI automation (Engine 2) as two complementary approaches.

## Two-Engine Architecture

```
┌─────────────────────────────────────────────────┐
│  API Layer (FastAPI)                             │
│  ┌───────────────┐  ┌──────────────────────┐    │
│  │  Engine 1     │  │  Engine 2            │    │
│  │  JSON Editor  │  │  GUI Automation      │    │
│  │  (reliable)   │  │  (fragile)           │    │
│  │               │  │                      │    │
│  │ • Read/write  │  │ • pyautogui          │    │
│  │ • Backup      │  │ • pywinauto          │    │
│  │ • Transform   │  │ • pynput (F10 stop)  │    │
│  │ • No app reqd │  │ • Needs app running  │    │
│  └───────────────┘  └──────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │  Fast Renderer (FFmpeg bypass)           │    │
│  │  Reads config → extracts paths → renders │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## CapCut PC Draft JSON Structure

CapCut stores projects in `%LOCALAPPDATA%/CapCut/User Data/Projects/com.lveditor.draft/<project_id>/`.

Each project folder contains `draft_content.json` with this structure:

```json
{
  "canvas_config": {"height": 1920, "width": 1080, "ratio": "9:16"},
  "duration": 10000000,       // microseconds
  "fps": 30.0,
  "id": "unique-project-id",
  "name": "Project Name",
  "materials": {
    "audios": [...],
    "texts": [...],
    "videos": [
      {
        "id": "video-001",
        "path": "C:/path/to/video.mp4",
        "duration": 10000000,
        "width": 1920, "height": 1080,
        "speed": 1.0, "volume": 1.0
      }
    ],
    "speeds": [...]
  },
  "tracks": [
    {
      "id": "track-video-001",
      "type": "video",
      "segments": [
        {
          "id": "segment-001",
          "material_id": "video-001",   // links to materials.videos[].id
          "source_timerange": {"duration": 10000000, "start": 0},
          "target_timerange": {"duration": 10000000, "start": 0},
          "speed": 1.0,
          "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": false, "vertical": false},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0}
          },
          "volume": 1.0,
          "visible": true
        }
      ]
    }
  ]
}
```

Key relationships:
- `tracks[].segments[].material_id` → `materials.videos[].id`
- `duration` values are in **microseconds** (1 second = 1,000,000)
- Speed change requires updating `target_timerange.duration = source_timerange.duration / speed`
- Adding watermark/audio creates new materials + new track of matching type

## Engine 1: Draft JSON Editor

Operations: `flip`, `speed`, `watermark`, `audio`, `transition`

Pattern: `apply_operation(draft, op_name, params)` dispatcher calls specific methods.

```python
class DraftEditor:
    def apply_operation(self, draft, operation, params):
        dispatch = {
            "flip": lambda d: self.flip_clip(d, **params),
            "speed": lambda d: self.change_speed(d, **params),
            "watermark": lambda d: self.add_watermark(d, **params),
            "audio": lambda d: self.add_audio(d, **params),
            "transition": lambda d: self.add_transition(d, **params),
        }
        handler = dispatch.get(operation)
        if handler is None:
            raise ValueError(f"Unknown: {operation}. Available: {', '.join(dispatch)}")
        return handler(draft)
```

API workflow: `read_draft()` → `backup_draft()` → apply ops → `write_draft()`

## Engine 2: GUI Automation

Libraries: `pyautogui` (mouse/keyboard), `pywinauto` (window management), `pynput` (F10 listener)

```python
class CapCutGUI:
    def __init__(self):
        pyautogui.FAILSAFE = True  # move mouse to corner = abort
        self._stop_flag = False
        # F10 emergency stop via pynput background listener
        self._listener = keyboard.Listener(on_press=self._on_key)
        self._listener.daemon = True
        self._listener.start()

    def focus_capcut(self):
        # Tier 1: pywinauto (best window control)
        # Tier 2: pyautogui.getWindowsWithTitle() fallback
        # Tier 3: return error dict
```

**Critical rules for Engine 2:**
- Always set `pyautogui.FAILSAFE = True`
- Always implement F10 emergency stop
- Always return error dicts (never raise) when app not found
- Document in UI: "Takes control of mouse/keyboard. Move mouse to corner to abort."

## Fast Renderer Pattern

Reads draft JSON, extracts video paths from materials, applies transforms from segments via FFmpeg (the existing VideoEditor), joins if multiple clips. This bypasses the external app's renderer entirely.

## Test Data Pattern

When the external app is NOT installed:
1. Create `backend/test_data/<app_name>/` with realistic config files
2. Create multiple sample projects with different structures (1 segment, 2 segments, etc.)
3. All Engine 1 tests run against sample data (they modify JSON, not the app)
4. Engine 2 tests verify graceful failure with clear error messages
5. API endpoints accept optional `base_dir` query param to override default install paths

## Verification Pitfalls

- **State leakage between tests.** If test N sets a flag (e.g., emergency stop), test N+1 must reset it. In verification scripts, explicitly reset shared state between tests: `obj._flag = False`.
- **Backup files in test data.** Clean up `.bk.*` files after verification runs so test data stays pristine for reproducibility.
- **Video file references in sample data.** Sample draft JSON references non-existent video paths. Engine 1 doesn't need them (it edits JSON). Fast renderer correctly returns 422 "No renderable video segments" when paths don't exist.
