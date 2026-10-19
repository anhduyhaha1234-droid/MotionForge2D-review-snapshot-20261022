# Multi-Phase Full-Stack Project Template

Reference structure from a real 6-phase project (Goha MMO Clone). Each phase adds backend modules + API endpoints + frontend UI while preserving existing functionality.

## Phase 1: Foundation (Scaffold)
```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/__init__.py, v1.py          # Health, Settings, SSE Logs
│   │   ├── core/__init__.py, config.py, logger.py
│   │   └── main.py                          # FastAPI + CORS + StaticFiles
│   ├── data/settings.json
│   └── requirements.txt
├── frontend/
│   ├── index.html      # Sidebar (8 tabs) + Tab panels + Settings modal
│   ├── styles.css      # Dark glassmorphism (#0a0a0f, #6c5ce7 accent)
│   └── app.js          # Tab switching, health poll, settings, SSE
└── phase1_review.md
```

## Phase 2: Feature Modules (Downloaders + Task Queue)
Adds:
```
backend/app/
├── downloaders/
│   ├── __init__.py
│   ├── cookie_manager.py    # JSON + Netscape format
│   ├── crawler.py           # Playwright (patchright) real browser
│   └── youtube.py           # yt-dlp subprocess wrapper
└── tasks/
    ├── __init__.py
    └── task_manager.py      # asyncio.Task tracking with progress %
```

New API endpoints: `POST /downloader/fb/scan`, `POST /downloader/youtube/scan`, `POST /downloader/download`, `GET /tasks`

Frontend updates: FB Reels form + grid, YouTube URL input + results, Task Queue with polling

## Phase 3: Media Engine (FFmpeg)
Adds:
```
backend/app/media/
├── __init__.py
├── editor.py           # Crop, speed, flip, audio mix, normalize, GPU NVENC
├── frame_extractor.py  # Interval/count/fps modes → .zip
├── joiner.py           # Concat demuxer + auto-resolution normalization
└── watch_folder.py     # Polling loop + preset config
backend/output/         # Generated .mp4, .zip files
```

New API endpoints: `POST /media/edit`, `POST /media/extract-frames`, `POST /media/join`, `GET/POST /media/watch-folder`

Frontend updates: Media Studio tab with 4 sub-tabs (Quick Edit, Frame Extract, Video Join, Watch Folder)

## Phase 4: External App Integration (CapCut PC)
Adds:
```
backend/app/capcut/
├── __init__.py
├── draft_io.py          # Find, read, backup, write external app config files
├── draft_editor.py      # Engine 1: Direct JSON manipulation (flip, speed, watermark, audio, transitions)
├── gui_automation.py    # Engine 2: pyautogui/pywinauto/pynput GUI control with F10 emergency stop
└── render_fast.py       # Fast preview render via FFmpeg (bypass external app's renderer)
backend/test_data/       # Sample draft JSON for testing when external app is not installed
```

New API endpoints: `GET /capcut/projects`, `POST /capcut/draft/edit`, `POST /capcut/e2/auto-caption`, `POST /capcut/e2/export`, `POST /capcut/e2/stop`, `GET /capcut/e2/status`, `POST /capcut/render-fast`

Frontend updates: AutoCapCut Pro tab with 4 sub-tabs (Projects, Engine 1 Draft Editor, Engine 2 GUI Automation, Render Fast)

Key pattern: **Two-engine architecture** — Engine 1 (JSON/direct, reliable, no external app needed) vs Engine 2 (GUI automation, fragile, needs app running). Engine 2 always needs FAILSAFE + emergency stop.

See `references/external-app-integration.md` for CapCut draft JSON structure and GUI automation patterns.

## Key Patterns
Adds:
```
backend/app/capcut/
├── __init__.py
├── draft_io.py          # Find/read/backup/write CapCut draft_content.json
├── draft_editor.py      # Engine 1: Direct JSON manipulation (flip, speed, watermark, audio, transition)
├── gui_automation.py    # Engine 2: pyautogui/pywinauto GUI control + F10 emergency stop
└── render_fast.py       # FFmpeg render from draft JSON (preview without opening CapCut)
backend/test_data/
├── capcut_draft_sample/draft_content.json
└── capcut_projects_sample/
    ├── project_tiktok_viral/draft_content.json
    ├── project_instagram_reel/draft_content.json
    └── project_youtube_short/draft_content.json
```

New API endpoints: `GET /capcut/projects`, `POST /capcut/draft/edit`, `POST /capcut/e2/auto-caption`, `POST /capcut/e2/export`, `POST /capcut/render-fast`

Frontend updates: AutoCapCut Pro tab with 4 sub-tabs (Projects, Engine 1 Draft Editor, Engine 2 GUI, Render Fast)

### Test Data Scaffolding Pattern
When the external app (CapCut) is NOT installed on the dev machine:
1. Create realistic sample config files in `backend/test_data/`
2. Engine 1 (JSON manipulation) tests against sample configs — always works
3. Engine 2 (GUI automation) returns graceful error when app not found
4. API endpoints accept optional `base_dir` parameter to override default paths
5. Document in review: "App X not installed — tested with sample data"

## Phase 5: AI Speech Engine & Video Studio Sync
Adds:
```
backend/app/ai/
├── __init__.py
├── stt.py              # faster-whisper Speech-to-Text (base/small/medium models)
├── tts.py              # edge-tts / ElevenLabs Text-to-Speech with SRT generation
└── translator.py       # Gemini/OpenAI SRT subtitle translation
backend/app/studio/
├── __init__.py
└── sync_engine.py      # Sync video clips to TTS voice timeline, render master video
```

New API endpoints: `POST /ai/stt`, `POST /ai/tts`, `GET /ai/voices`, `POST /ai/translate`, `POST /studio/sync`

Frontend updates: Video Studio tab (voice+SRT+clips sync), AI Voice tab with 3 sub-tabs (TTS Create, STT Extract, Translate)

Requirements add: `edge-tts`, `faster-whisper`, `requests`

## Phase 6: Comment Mining & Trend Finding
Adds:
```
backend/app/mining/
├── __init__.py
├── comment_miner.py    # yt-dlp --write-comments extraction + CSV export
└── trend_finder.py     # yt-dlp search (ytsearch, bilisearch) with view/date filtering
backend/output/         # Generated CSV files
```

New API endpoints: `POST /mining/trends`, `POST /mining/comments`

Frontend updates: Hunt Trends tab with 2 sub-tabs (Trend Search → video cards grid, Comment Mining → sortable table with CSV export)

Key pitfall: yt-dlp `--write-comments` on popular videos times out — always use `--extractor-args "youtube:max_comments=N"` to limit at source.

Requirements add: `yt-dlp` (already present from Phase 2)

## Key Patterns

### requirements.txt Evolution
```
# Phase 1
fastapi, uvicorn[standard], pydantic>=2.0

# Phase 2 adds
playwright>=1.49, yt-dlp>=2025.5.22

# Phase 3 adds
imageio-ffmpeg

# Phase 4 adds (GUI automation for desktop apps)
pyautogui, pywinauto, pynput

# Phase 5 adds (AI speech engines)
edge-tts, faster-whisper, requests
```

### Frontend Serving
Mount frontend as static files in `main.py` so the backend serves everything:
```python
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
```

### Shared Instances Pattern
Create shared instances at module level in `v1.py`:
```python
cookie_mgr = CookieManager()
fb_crawler = FBCrawler(cookie_mgr)
yt_downloader = YouTubeDownloader()
video_editor = VideoEditor()
capcut_gui = CapCutGUI()
```

### Real Test Videos
For testing video processing, download a short Creative Commons video:
```bash
yt-dlp --no-playlist -o "test_video.mp4" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
