---
name: fullstack-scaffolding
description: "Scaffold a full-stack project (backend API + static SPA frontend) from scratch with no existing codebase. Covers FastAPI/Express backends, static HTML/CSS/JS frontends, settings CRUD, SSE streaming, dark glassmorphism UI, and ad-hoc verification when no test suite exists. Use when building a new project from zero with API + frontend + config persistence."
version: 1.0.0
metadata:
  hermes:
    category: software-development
    tags: [fullstack, fastapi, spa, scaffolding, glassmorphism, verification]
---

# Full-Stack Scaffolding

See `references/adhoc-verification.md` for the ad-hoc verification script template.
See `references/multi-phase-project-template.md` for the multi-phase incremental building template (Phase 1 scaffold → Phase 2 features → Phase 3 media engine → Phase 4 external app integration → Phase 5 AI speech → Phase 6 mining).
See `references/external-app-integration.md` for CapCut draft JSON structure, two-engine architecture, and GUI automation patterns.
See `references/preview-before-upload-modal.md` for the preview→compare→confirm modal pattern (upload replacement files only after explicit user confirmation).
See `references/nextjs-build-gates-and-shared-layout-trap.md` for the Next.js App Router build failure whose error names a route but whose culprit is a shared layout component, plus the correct gate set for a UI-only commit (build/tsc/eslint/playwright-states + a scoped backend pytest as regression control).

## When to Use

- Building a new project from scratch with a backend API + frontend SPA.
- Building incrementally across multiple phases (adding modules/features phase by phase).
- No existing test suite — need ad-hoc verification to prove it works.
- FastAPI (Python) or Express (Node) backend with static HTML/CSS/JS frontend.

## Procedure

### 1. Plan the structure

```
project/
├── backend/
│   ├── app/
│   │   ├── api/v1.py       # Route handlers
│   │   ├── core/config.py   # Settings CRUD (JSON file)
│   │   ├── core/logger.py   # SSE log streaming
│   │   └── main.py          # FastAPI app + CORS + startup
│   ├── data/settings.json   # Persisted config
│   └── requirements.txt
├── frontend/
│   ├── index.html           # SPA shell
│   ├── styles.css           # Dark glassmorphism theme
│   └── app.js               # Tab switching, API calls, SSE
└── phase1_review.md         # Document endpoints + launch steps
```

### 2. Build backend first

- Start with `__init__.py` files (empty) for all packages.
- `config.py`: JSON read/write with merge semantics. `_ensure_file()` creates defaults if missing.
- `logger.py`: In-memory log buffer + `asyncio.Queue` subscriber pattern for SSE.
- `v1.py`: APIRouter with health, settings CRUD, SSE stream endpoint.
- `main.py`: FastAPI app, CORS middleware (`allow_origins=["*"]`), router include, startup event.

### 3. Build frontend

- Single `index.html` with sidebar nav + tab panels + settings modal + terminal console.
- CSS: dark glassmorphism (`backdrop-filter: blur(20px)`, `rgba(255,255,255,0.05)` surface, `#0a0a0f` bg, `#6c5ce7` accent).
- JS: IIFE with tab switching (`dataset.tab`), health poll, settings load/save, SSE EventSource with auto-reconnect.

### 4. Verify with ad-hoc script

Write a self-contained Python script (see `references/adhoc-verification.md`) that:
1. Checks all files exist
2. Validates data defaults
3. Starts backend on a non-default port
4. Hits every endpoint and validates responses
5. Checks frontend source content via string matching
6. Restores mutated state, kills server, deletes script

### 5. Document

Write `phase1_review.md` with directory tree, endpoint table, curl examples, launch instructions, and feature checklist.

## Multi-Phase Incremental Building

When a project is built across multiple phases (e.g. Phase 1: scaffold, Phase 2: downloaders, Phase 3: media engine), follow this pattern for each phase:

### Delegation with Full-Codebase Context
Before dispatching a subagent for phase N, **read ALL existing files** and provide their complete content in the subagent's context. This prevents the subagent from:
- Overwriting existing functionality with stubs/placeholders
- Creating incompatible imports or naming
- Breaking existing API contracts

Include in the subagent context:
1. Every existing `.py`, `.js`, `.html`, `.css` file content (full, not truncated)
2. The existing `requirements.txt`
3. The directory tree
4. Specific constraints: "Don't break Phase 1/2 functionality"
5. Real test data (e.g. path to a downloaded video file for testing)

### Phase Review Pattern
Each phase should produce its own `phaseN_review.md` documenting:
- New modules created
- New API endpoints with real test output (curl responses)
- Real output files (videos, images, zip archives) with file sizes
- Launch instructions

### API Logs Pattern
For phases that process media or have complex API interactions, produce `phaseN_api_logs.json` with real request/response data including status codes and execution times.

## Frontend Sub-Tabs Pattern

When a main tab needs multiple sub-views (e.g. Media Studio with Quick Edit, Frame Extract, Video Join, Watch Folder), use nested tab navigation:

```html
<section class="tab-panel" id="panel-media-studio">
  <div class="glass-card">
    <h2>🎬 Media Studio</h2>
    <div class="sub-tabs">
      <button class="sub-tab active" data-subtab="quick-edit">✂️ Quick Edit</button>
      <button class="sub-tab" data-subtab="frame-extract">🖼️ Frame Extract</button>
      <button class="sub-tab" data-subtab="video-join">🔗 Video Join</button>
      <button class="sub-tab" data-subtab="watch-folder">📁 Watch Folder</button>
    </div>
    <div class="sub-panel active" id="sub-quick-edit">...</div>
    <div class="sub-panel" id="sub-frame-extract">...</div>
  </div>
</section>
```

CSS:
```css
.sub-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
.sub-tab { padding: 8px 16px; background: transparent; border: 1px solid var(--border); border-radius: 8px; color: var(--text-dim); cursor: pointer; font-size: 13px; transition: all .2s; }
.sub-tab:hover { background: var(--bg-card); color: var(--text); }
.sub-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.sub-panel { display: none; animation: fadeIn .3s ease; }
.sub-panel.active { display: block; }
```

JS (add to the main IIFE, after tab switching):
```javascript
document.querySelectorAll('.sub-tab').forEach(btn => {
    btn.addEventListener('click', () => {
        const card = btn.closest('.glass-card');
        card.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
        card.querySelectorAll('.sub-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('sub-' + btn.dataset.subtab).classList.add('active');
    });
});
```

## Pitfalls

- **MSYS paths on Windows.** Use Windows-native paths (`C:/Users/...`) for `subprocess.Popen` cwd. Use `write_file` tool (not shell heredocs) to create files — heredocs break on JS template literals. For running Python scripts from MSYS shell: `python /c/Users/...` FAILS (Python resolves it as `C:\c\Users\...`). Use `TMPFILE=$(cygpath -w /path/to/script.py) && python "$TMPFILE"` instead. The `write_file` tool's `resolved_path` gives the Windows-native path directly.
- **`__pycache__` stale bytecode after file restoration.** When a file gets overwritten (e.g. by a sibling subagent) and you restore it, Python may still import the old bytecode from `__pycache__/`. Always `rm -rf <pkg>/__pycache__` after restoring any `.py` file, or your "fix" won't take effect.
- **Background server for verification.** Instead of `subprocess.Popen` in the verification script, use `terminal(background=true, watch_patterns=["Application startup complete"])` to start the server, then run the verification script in a separate `terminal()` call, then `process(action='kill')` to clean up. This avoids orphan processes and gives better output capture.
- **Port conflicts.** Use non-default ports (8001, 8002) for verification to avoid colliding with dev servers.
- **HTML attr vs JS accessor.** When checking frontend JS handles an HTML feature, verify the JS property name (`dataset.tab`) not the HTML attribute (`data-tab`).
- **Settings mutation in tests.** POST tests change config — restore defaults at end of verification script.
- **SSE stream testing.** SSE endpoints hold the connection open. Open, check status + content-type, close immediately. Don't wait for data.
- **`on_event("startup")` deprecation.** FastAPI newer versions prefer `lifespan` context manager. Use `on_event` for V1 speed, note the migration path.
- **Subagent file conflicts in multi-phase builds.** When dispatching a new subagent for Phase N while Phase N-1's subagent is still running, the old subagent may finish AFTER the new one and overwrite its work. This is especially dangerous when the old subagent was told to create stubs and the new one creates real implementations. Mitigation: kill old subagent's processes before dispatching, or verify all critical files on disk after both finish. See `subagent-orchestration` skill pitfall #1 for full details.
- **Subagents default to stubs if context is ambiguous.** When the user demands real implementations (real API calls, real downloads, real browser automation), the subagent prompt must explicitly say "NO mock data, NO stub — use real X" in the goal AND in the constraints section AND in the specific module instructions. A single mention gets buried in context.
- **`__pycache__` cleanup between phases.** Always `find . -type d -name __pycache__ -exec rm -rf {} +` before starting a new phase's server, especially after restoring files from sibling subagent overwrites.
- **Verification script state leakage.** When tests share a singleton object (e.g., a GUI automation instance), state set in test N carries into test N+1. If test N calls `stop()` which sets `_stop_flag = True`, test N+1's `auto_caption()` returns "Emergency stop active" instead of the expected error. Fix: explicitly reset shared state at the start of each test that depends on clean state: `obj._stop_flag = False`.
- **External app integration without the app installed.** When building integration with CapCut, Premiere, or other desktop apps that may not be on the dev machine: (1) Create `backend/test_data/<app_name>/` with realistic sample config files (draft JSON, project manifests), (2) Engine 1 (JSON/config manipulation) always works against sample data, (3) Engine 2 (GUI automation) returns graceful error `{\"error\": \"App not found\", \"step\": \"focus\"}` — never crashes, (4) API endpoints accept optional `base_dir` parameter to override default install paths, (5) Document in `phaseN_review.md` what was tested with sample data vs real app.
- **Next.js corrupted `.next` cache produces phantom module errors.** A Runtime Error like `Cannot find module '@file:\`tanstack/react-query'` (with a weird `@file:` prefix in the module name) means the compiled dev cache is corrupted — the SOURCE imports are fine (`grep -rn "@file:" src/` returns nothing). The fix is NOT editing source: stop the dev server, `rm -rf .next`, kill the old `next dev` process (`taskkill /PID <pid> /F` after `netstat -ano | grep ":3000.*LISTENING"`), then restart `npm run dev`. Verify by curling the page for a 200 + real HTML, not just the dev-server startup banner. Also: Next dev can silently pick a different port (e.g. 3001) when 3000 is taken — check which port actually serves your app before blaming the backend. This is distinct from the backend stale-code 405 (restart uvicorn) — the symptom lives in the browser console and the fix is a cache wipe.
- **Windows dev-server process mapping: bash wrapper PID ≠ serving child PID.** Hermes `terminal(background=true)` returns the `bash.exe` wrapper PID, but the actual server is a child (`node.exe` for Next, `python.exe` for uvicorn). `netstat -ano | grep ":3000.*LISTENING"` shows the CHILD PID, and `process(action='list')` shows the WRAPPER — don't conclude "server died" because the PIDs differ; cross-check with `tasklist /FI "PID eq <pid>"` to see the real process name. Also, when the old server is still alive and you start a new one, Next prints `⚠ Port 3000 is in use by process <old>, using available port 3001` then exits with `⨯ Another next dev server is already running` — that "process exited" notification refers to the NEW attempt, NOT the working server. Kill the true listener (`taskkill /PID <pid> /F` where `<pid>` = the netstat PID) and restart once. A full smoke script (health + list + crop + delete + scenes) run against the live server is the strongest proof both layers work.\n- **yt-dlp comment extraction timeouts on popular videos.** `yt-dlp --write-comments --skip-download --dump-json` on videos with millions of comments (e.g. 1B+ view videos) can hang for minutes and eventually time out. Fix: pass `--extractor-args "youtube:max_comments=N"` to limit extraction at the source. In the Python wrapper, compute N from the user's `max_comments` parameter (e.g. `min(max_comments * 2, 200)`) and pass it via subprocess args. Without this, yt-dlp downloads ALL comments before Python can filter — which is O(minutes) for viral videos.
