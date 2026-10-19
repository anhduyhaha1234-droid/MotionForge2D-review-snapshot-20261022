---
name: windows-dev-server-diagnosis
description: "Use when dev server fails on Windows. Port or crash issues."
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [debugging, windows, dev-server, port-conflict]
    related: [terminal-engineering-discipline, systematic-debugging]
---

# Windows Dev Server Diagnosis

## When to Load
- User reports "Failed to fetch", 405 Method Not Allowed, or connection refused
- Backend/frontend not responding
- Tests fail with "No ffmpeg" or "port already in use"

## Diagnosis Flow

### Step 1: Identify what's on the port
```bash
# Check if correct app is serving
curl -s http://localhost:PORT/openapi.json 2>&1 | python -c "import json,sys; print(json.load(sys.stdin).get('info',{}))"

# Check listeners
netstat -ano | grep ":PORT.*LISTENING"
```

If wrong app title → another process owns the port.

### Step 2: Port conflict resolution
On Windows, zombie uvicorn `--reload` processes outlive their parents. `taskkill /PID X /F` often says "not found" while netstat still shows the PID.

**Preferred fix:** Use a different port (8002 instead of 8000). Update `frontend/.env.local`.

### Step 3: FFmpeg PATH
WinGet symlinks not in MSYS PATH:
```bash
export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"
```

### Step 4: Backend crash recovery
```bash
# Health check
curl -s http://127.0.0.1:8002/health

# Restart
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

### Step 5: Frontend down — check BOTH ports before assuming
"Server sập / can't open app" often means the FRONTEND (port 3000) died while the backend (8002) is still alive. Check both listeners:
```bash
netstat -ano | grep ":3000.*LISTENING"   # frontend
netstat -ano | grep ":8002.*LISTENING"   # backend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```
If 3000 is missing but 8002 is fine → restart frontend only:
```bash
cd frontend && npm run dev
```
Verify: `curl -s http://localhost:3000 | head -1` returns `<!DOCTYPE html>`.

### Step 6: Background agent task "stopped" — check PID file + log before trusting anything
When the user asks "task có còn chạy ko / thấy dừng rồi" about a Hermes/Codex CLI batch task:
1. Scope: `process(action='list')` shows ONLY Hermes-managed bg processes of THIS session — empty ≠ nothing runs. Tasks launched via `run-*.ps1` scripts live outside it.
2. Task dirs (e.g. worktree `output/`) carry `run-<task>.ps1` + `<task>.pid` + `<task>-hermes.log`.
3. PID alive check: `PID=$(cat output/<task>.pid)` then `tasklist //FI "PID eq $PID"` — DOUBLE slash, MSYS mangles single `/FI`. Empty output ⇒ dead. Or `powershell -NoProfile -Command 'Get-Process -Id <PID> -ErrorAction SilentlyContinue'`.
4. Log mtime = death timestamp: `stat -c "%y" output/<task>.log`; a log that stopped growing while the task "should run" pinpoints when it died.
5. Tee-Object logs are UTF-16LE — `grep`/`tail` show `\u0000` between chars and match nothing. Strip nulls first: `tail -c 2000 output/<task>.log | tr -d '\0' | grep -aE "Error|failed|Resume"`.
6. Hermes CLI death signature (model/provider failure, not task logic):
   ```
   API call failed (attempt 1/3) ... InternalServerError [HTTP 502]
   API failed after 3 retries: HTTP 502: [provider/model]
   Resume this session with: hermes --resume <session_id>
   ```
   Router can be alive (port listening, `curl /v1/models` → 200) while the model behind it times out (`fetch connect timeout`). Don't rerun the whole task — resume the session: `hermes --resume <session_id>` (optionally smoke-test the model with a tiny prompt first).
7. PowerShell inline in MSYS bash: single-quote the whole command — `powershell -Command "... $_ ..."` lets bash expand `$_` (previous command's last arg) BEFORE PowerShell runs, so `$_.ProcessName` arrives as `.ProcessName` → "command not found".

Full working transcript with exact commands, the 502 death signature, and the bash-quoting trap: `references/task-liveness-diagnostics.md`.

## Common Pitfalls
- Never use port 8000 on this machine (zombie from Goha MMO Clone)
- `nvidia-smi` works from MSYS but `ffmpeg -encoders` needs PATH
- Test suite uses `conftest.py` PATH fix but some pytest versions collect before conftest runs
- When user says "Failed to fetch" — check backend FIRST, 90% of the time it crashed
- **"Can't open the app" ≠ backend crash.** Diagnose BOTH ports; a dead `npm run dev` (port 3000 no listener) with a healthy backend (8002 OK) is common after build/test runs kill the dev process. Restart the frontend; tell the user to hard-refresh (Ctrl+Shift+R).
- **Stale backend = fix on disk doesn't reach the running process.** A 405/route fix committed while uvicorn runs from before the commit stays broken until restart. Check the process start time (`process(action='list')` uptime) against the commit time; check the live access log for the failing status code; restart, then re-run the exact failing request to prove the fix.
- **Zombie frontend: port LISTENING but curl returns 000.** A hung `next dev` process can keep the port in LISTENING state while every request times out (`curl -s -o /dev/null -w "%{http_code}"` → `000`, exit 28). `netstat` looks fine, so it's easy to blame the network. If a healthy backend (8002 OK) + LISTENING 3000 + curl 000 coexist, the dev process is wedged — kill it hard: `netstat -ano | grep ":3000.*LISTENING"` → `taskkill /PID <pid> /F` → confirm the port is free → restart `npm run dev` → verify `curl` returns 200.
- **`npm run dev` silently moves to port 3001 and exits when 3000 is occupied.** If a stale process still holds 3000, a fresh `npm run dev` prints `⚠ Port 3000 is in use by process <pid>, using available port 3001 instead`, starts on 3001, then exits with `⨯ Another next dev server is already running.` The user's browser hits 3000 (the wedged process) and sees nothing. Fix: check the actual startup log (the background process output shows the real port), kill the stale 3000 holder, then restart. When a restart "fails" immediately, always read the process log rather than assuming the command itself broke.
- **"Project lost" panic is usually a list-endpoint lie, not data loss.** When the user says a project vanished, check the filesystem first (`ls projects/*/project.json`, read the JSON) before trusting the API. A `break` cap (`>= 30`) or recency-only sort hides old-but-real records behind a flood of new junk. Fix the list endpoint (remove cap, sort by scenes_count desc), don't touch the data.
- uvicorn does NOT hot-reload unless run with `--reload`. After any code change that adds/removes routes, restart the backend manually; Next.js dev auto-reloads but the FastAPI backend does not.
- **Next.js "Cannot find module '@file:`...'" = corrupted `.next` cache, not source.** A Runtime Error with a weird `@file:` prefix in the module name (e.g. `Cannot find module '@file:`tanstack/react-query'`) means the dev build cache is corrupted. Source is fine (`grep -rn "@file:" src/` returns nothing). Fix: stop `next dev`, `rm -rf .next`, kill the listener (`netstat -ano | grep ":3000.*LISTENING"` → `taskkill /PID <pid> /F`), restart `npm run dev`, then verify with `curl -s http://localhost:3000 | head -1` returning real HTML. Also check Next didn't silently move to port 3001 when 3000 was taken — the startup log prints the actual port.
- **Next.js Turbopack rejects a junctioned `node_modules` ("Symlink [project]/node_modules is invalid, it points out of the filesystem root").** When node_modules is shared read-only across worktrees via a directory junction (`powershell New-Item -ItemType Junction -Path <worktree>\frontend\node_modules -Target <archive>\frontend\node_modules` — `cmd //c mklink /J` silently fails under git-bash), `next dev` may work but `next build` (Turbopack default in Next 15) hard-fails with `TurbopackInternalError`. Fix: run `npx next build --webpack` — webpack mode tolerates the junction; verify `.next/BUILD_ID` exists afterwards. Only share node_modules when the `package-lock.json` hash matches the source tree's lock, and treat the shared tree as read-only (no npm install/ci/mutate).
- **Auto-segment `min_area` is measured on the DOWNSAMPLED frame.** When tuning OpenCV contour detection that downsamples (e.g. 0.5x) before finding contours, the area threshold is in downsampled pixels — a `min_area=300` on 0.5x means ~1200px at full resolution. If a user wants MORE objects detected, lowering the number increases sensitivity; raising it (e.g. 500→800) actually detects FEWER. Document the effective full-res threshold in the endpoint docstring so the number isn't misinterpreted.
