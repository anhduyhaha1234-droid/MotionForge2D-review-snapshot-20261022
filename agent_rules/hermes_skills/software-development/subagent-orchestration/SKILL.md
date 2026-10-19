---
name: subagent-orchestration
description: "Orchestrate subagents for parallel work with proper delegation patterns"
tags: [delegation, subagent, orchestration, parallel]
---

# Subagent Orchestration

## When to Use

- Delegating implementation work to Claude Code or Codex subagents
- Running multiple independent tasks in parallel
- Managing background processes and their lifecycle
- Coordinating subagent results and synthesizing output

## Key Patterns

### Parallel Delegation
Dispatch independent subagents concurrently using `delegate_task`. Do NOT batch them in a `tasks` array — the runtime waits for ALL to finish before returning. Instead, dispatch each individually so each return triggers the next dispatch immediately.

### Parallel Backend + Frontend Delegation (Full-Stack Features)
When a feature touches both backend (Python) and frontend (TypeScript), dispatch two subagents in parallel:

1. **Backend subagent**: schemas, services, API endpoints, unit tests, ruff, pytest
2. **Frontend subagent**: components, store updates, API client additions, tsc, build

Each subagent gets FULL context:
- Schema shapes (field names, types, defaults)
- Endpoint signatures (method, path, request/response shapes)
- Existing file contents (read before dispatching)
- Explicit constraints: "Do NOT modify backend files" / "Do NOT modify frontend files"

Verification after both complete:
```bash
python -m ruff check app/ tests/ && python -m pytest tests/ -q
cd frontend && npx tsc --noEmit && npx next build
```

Common integration issues to fix after both complete:
- Field name mismatches (snake_case backend vs camelCase frontend)
- Missing imports between backend/frontend changes
- Schema field additions not reflected in API response serialization

### Subagent Selection
- **Claude Code** (`claude -p`) — implementation, refactoring, feature-building, code review. Default builder.
- **Codex** (`codex exec`) — test writing, batch issue fixing, repo-scoped edits. Lighter weight.

### Timeout Guidance
- Default: 600s (10 min)
- Quick edits/reviews: 120–300s
- Large multi-file builds: 1800–3600s
- Never set timeout to a fixed huge value — scale to the task's real size.

### Background Processes
- Use `terminal(background=true, notify_on_complete=true)` for long-running processes
- Use `process(action='poll')` to check status
- Use `process(action='kill')` to stop processes
- Use `close_terminal()` to drop the tab view when the process is no longer needed

### Subagent Result Handling
- Subagent summaries are SELF-REPORTS, not verified facts
- Always verify subagent output yourself before trusting it
- Run tests, check files, confirm outputs exist

## Common Pitfalls

1. **Sibling subagent file overwrites.** When multiple subagents run in parallel, they can silently overwrite each other's files. The write_file tool emits a warning `"_warning": "...modified by sibling subagent 'sa-N-...' but this agent never read it"` — treat this as a **critical signal**. After ALL subagents finish, scan for these warnings in tool output and re-read any flagged files to confirm they contain YOUR intended content, not the sibling's. If a file was clobbered, rewrite it and clear `__pycache__` for that package (`rm -rf <pkg>/__pycache__`). Common symptom: a stub/placeholder file gets replaced with real implementation code by an overzealous sibling, causing import errors or wrong behavior at runtime.
   - **Sequential dispatch overlap (worse than parallel).** When you dispatch a NEW subagent while an OLD one is still running, the old one can finish AFTER the new one and overwrite its work with stale content. This is especially dangerous when the old subagent was told to create stubs and the new one was told to create real implementations — the old one's late finish reverts the real code back to stubs. **Mitigation:** Before dispatching a replacement, KILL the old subagent's background processes (`process(action='kill')`) and wait for its delegation to fully complete or cancel. If that's not possible, after the new subagent finishes, check the old subagent's live transcript for late writes and re-verify all critical files on disk.
2. **Batching subagents in tasks array** — the runtime waits for ALL to finish before returning, causing idle gaps. Dispatch individually instead.
3. **Trusting subagent summaries without verification** — subagents can misreport. Always verify with your own commands.
3. **Insufficient timeout** — default 10min may be too short for large builds. Scale up explicitly.
4. **Forgetting to check subagent logs** — if a subagent fails silently, check `C:\Users\Admin\AppData\Local\hermes\cache\delegation\live\<delegation_id>\task-0.log`.
5. **Background process leaks** — always clean up background processes when done. Use `process(action='kill')` or `close_terminal()`.
6. **Not reading subagent output** — the subagent's result is a summary. Read the actual tool output to verify.
7. **Empty response after terminal command** — after running a terminal command, ALWAYS provide a substantive response that reads and acts on the output. Never return an empty message. This is the most common failure mode.
8. **Subagent defaults to stubs/mocks when prompt is ambiguous.** If the user demands real implementations (real API calls, real downloads, real browser automation), the subagent prompt must explicitly and repeatedly say "NO mock data, NO stub, NO placeholder — use real X". A single mention gets buried in context. Put the constraint in the goal, in the constraints section, AND in the specific module instructions. If the subagent still produces stubs, check its output immediately and rewrite the file yourself rather than dispatching another subagent (which risks the sequential overlap pitfall above).

9. **Multi-phase sequential delegation pattern.** When building a project across N phases (Phase 1→2→3→...), each phase dispatches a single subagent with full codebase context. Key rules:
   - **Always read ALL existing files** before dispatching the next phase — the subagent gets these as context, not as files on its disk.
   - **Phase N must preserve Phase 1..N-1** — include explicit "don't break existing X/Y/Z" constraints.
   - **Wait for FULL completion** before dispatching next phase. Use `sleep + tail` on the live transcript to poll. Don't start Phase N while Phase N-1 is still writing files.
   - **Verify the previous phase's deliverables on disk** before dispatching the next phase — check that review files, output files, and module files actually exist.
   - **Port conflicts cascade** — when a new phase restarts the server, the old process may still hold the port. Always `taskkill` or `process(kill)` before starting fresh.

### Subagent-Specific Tool Quirks (learned from multi-phase builds)

**edge-tts SubMaker API (v7.x+):** The `SubMaker` class uses `get_srt()` to generate subtitles, NOT `generate_subs()` or `create_sub()`. The correct pattern:
```python
submaker = edge_tts.SubMaker()
async for chunk in comm.stream():
    if chunk["type"] == "audio":
        audio_chunks.append(chunk["data"])
    elif chunk["type"] == "WordBoundary":
        submaker.feed(chunk)  # feed the raw chunk dict
srt_content = submaker.get_srt()  # NOT generate_subs()
```
If the subagent gets this wrong, it will produce empty .srt files. Always verify the SRT file has >0 bytes after TTS generation.

**yt-dlp comment extraction on popular videos:** Videos with millions of views (e.g. Rick Astley) can cause yt-dlp to hang for minutes downloading ALL comments. Always pass `--extractor-args "youtube:max_comments=N"` and set a process timeout (60-90s). Without this, the API endpoint will timeout and the frontend will hang.

**MSYS bash `taskkill` syntax:** In git-bash/MSYS, `taskkill //F //PID 1234` fails with "Invalid argument/option". Must use: `cmd.exe /c "taskkill /F /PID 1234"`. The subagent will repeatedly hit this if not warned.

**Python file path in MSYS:** `python /c/Users/Admin/script.py` fails with "can't open file" because python.exe gets `C:\c\Users\...`. Must use Windows-native paths: `python 'C:\Users\Admin\script.py'` or `python -c "exec(open('C:/Users/Admin/script.py').read())"`.

### CLI Worker Launch (hermes chat / claude -p via script) — cwd guard
Launching `hermes chat --query ...` (or any CLI agent) from a PowerShell script
with `Set-Location` does NOT reliably give the worker that cwd when the Hermes
desktop daemon is running — the worker session may run with cwd = daemon's cwd
(often the MAIN repo), silently writing task files to the WRONG repository.
Verified 2026-08-05: S06-T05 agent wrote all code into
`C:\Users\Admin\MotionForge2D` (main) instead of the worktree; REPORT.md ended
up SUBMITTED in main and IN_PROGRESS in the worktree.

Prevention (HARD WORKTREE GUARD — put at TOP of the worker prompt):
1. Worker must run `pwd`, `git rev-parse --show-toplevel`, `git status --short`
   BEFORE any write. If toplevel != expected root → write nothing, emit
   `BLOCKED: WRONG_WORKTREE`, exit immediately.
2. Manager must check `git status --short` of BOTH the expected worktree AND
   the MAIN tree ~60s after launch. New MAIN-tree changes caused by the worker
   → stop worker and log an incident.
3. After the run: verify placement — `git status` in both repos + mtimes.
   A task claiming SUBMITTED but leaving the worktree REPORT.md untouched is
   misplaced.
4. Recovery if misplaced: back up the worktree originals to
   `output/backup-pre-copy/`, copy the changed files (verify with `diff -q`
   per file), re-run focused pytest in the worktree. Do NOT dir-copy/robocopy.
5. Write a durable `INCIDENT_REPORT_*.md` in the task packet so the reviewer
   sees the recovery and decides on leftover MAIN-tree files.

### User visibility: mirror worker logs into a watched folder
The user wants to track worker progress live on the desktop. For every CLI
worker launched in the background, mirror its log into the main project folder
(e.g. `C:\Users\Admin\MotionForge2D\output\hermes-task-logs\`) and run a
10s watcher daemon that also produces a UTF-8 `-LIVE.txt` tail (`iconv -f
UTF-16LE -t UTF-8 | tail -300`) — Hermes logs are UTF-16 and unreadable raw.
Then `open_preview` the LIVE.txt + `focus_pane('files')`. Note: CLI workers do
NOT appear as desktop chat sessions; preview pane is the visibility mechanism.

### Verification must match artifact type
For changed `.ps1`/`.sh` launchers, `pytest` does NOT apply. Use PowerShell
`Parser.ParseFile` for `.ps1`, `bash -n` for `.sh`, and a functional diff
(watcher output vs source tail) for scripts. Prove launcher behavior: syntax
OK + spawned process alive with right args + side-effect file updating. Don't
run heavy suites concurrently with a live worker in the same worktree (races
`.pytest_cache`/test files) — re-run independently AFTER the worker exits.

### Long-lived dev servers break Playwright E2E
A `next dev` server running for hours makes `page.goto()` hang; Playwright
exits 124 after ~600s. NOT a test failure. Fix: kill the old dev server, start
fresh, verify with `curl -o /dev/null -w "%{http_code}"`, re-run E2E.

### PM-gated task queue (manager verification between tasks)
When the user (PM) dictates a strict task queue (e.g. Sprint S05-T03 → T04 →
T05 → T06 → Sprint Exit), never open the next task before ALL of:
1. The worker process has EXITED (poll/notify, not assumed).
2. Its REPORT = SUBMITTED (grep the actual file, never APPROVED — no
   self-approval).
3. The manager has independently reviewed `git diff` AND run targeted tests
   (do NOT trust the worker's self-reported test results — re-run them).
4. Status recorded as `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`.

After the final queue task: stop all writers, run a fresh 7/7 baseline, write
a `SPRINT_EXIT_REPORT`, and hand the sprint to the reviewer (Codex) — the
manager does not approve sprints. Use a FRESH compact session per task; never
resume old worker sessions with large context.

### Autonomous multi-agent pipeline to delivery (No intermediate user pauses)
When the user directs an end-to-end delivery pipeline to run autonomously through to the app and output media without stopping for user approval between milestones:
1. **Decompose into disjoint scoped sub-agent tasks** (e.g., core provenance, asset reuse, event timing, gate conformance, GPU excerpts, pilot assembly, app slices) with explicit exclusive write allowlists.
2. **Mandate internal self-verification at every boundary.** Each sub-agent or stage must prove its deliverables against a finite negative/positive matrix and disk ground truth (`SELF_VERIFIED`). Do not advance to expensive downstream steps (e.g., full rendering or UI integration) if an internal criterion fails.
3. **Do not stop between milestones to ask permission.** When the authorizing prompt or user grants autonomous execution through the backlog, advance directly to the next dependent task once the predecessor's self-verification passes. Only stop on a genuine external blocker or at the final independent review gate.
4. **Durable checkpointing & real continuation across context boundaries.** Because LLM desktop chats are turn-based, never claim work is 'running continuously in background' unless an actual OS daemon is executing. Maintain deterministic disk checkpoints (`STATE.json`, `CHECKPOINT.json`, `RESUME.md`, and hashed manifests) so that when context compresses or a new session takes over, execution resumes from verified disk truth rather than narrative assumptions.

### Supervised long-running worker sessions (overnight sprints)

When a correction/sprint runs unattended for hours, don't poll by hand — arm a
watchdog and let `notify_on_complete` wake you. Full script + command
templates: `references/supervised-worker-watchdog.md`.

1. **Dispatch detached.** Write the worker/manager prompt to a temp file, then:
   `PROMPT=$(cat prompt.txt) && hermes chat --resume <owner_session> --provider custom --model alpha -q "$PROMPT" --yolo --pass-session-id --max-turns 150 --source tool > output/<task>/worker.log 2>&1` with `terminal(background=true, notify_on_complete=true)`.
   Corrections RESUME the owner session; only new tasks get new sessions.
2. **Arm an mtime watchdog.** Poll the newest mtime across the task's log globs every 60s; exit `STALL_ALERT` when idle exceeds a threshold, `DONE` when the supervised process disappears. Tune the threshold to the workload: 8 min suits fast pytest loops, but long Playwright/E2E suites legitimately sit silent 15–60+ min (a real-vertical suite ran 1.3h). Repeated false alarms mean RAISE the threshold, never kill the worker.
3. **A quiet log ≠ dead worker.** Audit in order: process alive (CPU delta over ~20s) → log tail → Hermes lifecycle markers. On big resumed sessions (~230K tokens) `🗜️ Compacting context` blocks output for minutes — normal, wait. A new `request_dump_*.json` in `$HERMES_HOME/sessions/` proves a connection error occurred; policy is wait 5 min → resume SAME session/SAME model, unlimited cycles for transient network errors (400/401/quota errors are blockers, not retry candidates).
4. **Iteration budget exhaustion.** `⚠ Iteration budget reached (N/N)` ends the session mid-work (often while still polling a child process); the closing lines print `Session: <id>` — resume THAT id to continue. If a MANAGER died at budget while its worker still runs, take over verification directly (run the gates yourself) instead of re-dispatching a manager.
5. **Worker died before SUBMITTED.** Record `BLOCKED_LIVENESS` with hard evidence (log last-mtime+size, PID gone from process list, packet LOG/REPORT untouched), then resume the owner session with a self-contained continuation prompt. Never create a second owner session. If the worker finished code+tests but died before appending LOG/REPORT, the SUPERVISOR may append the packet entry — but must attribute provenance explicitly (which route/model did the original work, which did the completion) and re-run all gates independently before claiming done.
6. **Two node/Playwright runners racing** (orphan from a timed-out foreground run holding ports + a fresh background run) hang forever. Kill BOTH trees, confirm ports free via `netstat -ano | grep LISTENING`, rerun exactly ONE instance.
7. **Report progress on demand with real evidence** — stat mtimes/sizes, quote the log tail; never estimate. Users ask "bao giờ xong?" — answer with phase-based estimates anchored to observed durations, updated after each milestone.

## Verification Checklist

- [ ] Subagent dispatched with appropriate timeout
- [ ] Subagent result verified with independent command
- [ ] Background processes cleaned up
- [ ] No stray files from subagent work
- [ ] Checked for sibling subagent file overwrite warnings — re-read flagged files
- [ ] Cleared `__pycache__` if any file was restored after sibling overwrite
- [ ] All tests pass after subagent changes