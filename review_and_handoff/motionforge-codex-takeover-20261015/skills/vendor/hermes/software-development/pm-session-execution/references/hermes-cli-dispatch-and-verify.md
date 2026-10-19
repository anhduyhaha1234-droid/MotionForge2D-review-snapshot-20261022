# Hermes CLI worker dispatch & Manager verification (proven recipes)

Verified 2026-09-02/03 on MotionForge2D S10-C6H C15/R1 (Hermes v0.19.0, Windows git-bash, provider `custom` 9Router). All commands run from the worktree with `DB` env UNSET.

## 1. Probe before dispatch (exact model route)
```bash
export HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900
hermes -z "Reply with exactly: PROBE_OK" --provider custom -m ocg/deepseek-v4-flash --yolo --no-restore-cwd > probe.log 2>&1; echo "EXIT:$?"
```
Verify BOTH: log contains `PROBE_OK` AND state.db latest session row shows exact model (bare alias ≠ equivalent). Wrong/unavailable route → BLOCKED_MODEL_ROUTE, never fallback.

## 2. Dispatch / resume
- Fresh worker: `hermes -z "$(cat packet.txt)" --provider custom -m <exact-model> --yolo --no-restore-cwd > worker.log 2>&1`
- Resume (correction, same task): `hermes --resume <requested_session_id> ... -z "$(cat packet.txt)" ...`
- `-z "$(cat file)"` is SAFE for multi-KB packets: quotes/backticks/dollar signs inside the file are literal bytes (only NUL and trailing newline are stripped). Prefer it over manual escaping; if prompt >8KB split into two files.
- Run with `background=true` + `notify_on_complete=true`; `process(wait)` is clamped to 180s per call → loop `wait 180s` chunks, checking progress between chunks.

## 3. Resume CREATES a new effective session ID
`--resume X` records a NEW session row (parent=None). Query read-only immediately and log BOTH IDs:
```python
import sqlite3
con = sqlite3.connect("file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro", uri=True)
cur.execute("SELECT id, model, model_config, started_at, message_count, tool_call_count, end_reason FROM sessions ORDER BY rowid DESC LIMIT 3")
```
Record requested vs effective in the session registry BEFORE the worker's first write; same Task ID, single writer.

## 4. Progress signals (log file lies)
The `-z` CLI log file stays **0 bytes until the final report** is written at exit. Do NOT tail it mid-run (chat-mode `-q` consoles behave differently — they stream live; see §15). Real progress signals:
- state.db `message_count` / `tool_call_count` growth for the session row;
- evidence-dir file mtimes (red logs, gate logs appear as the worker finishes each phase);
- source SHA changes (patch landing) — but don't over-poll each 180s chunk.

## 5. RUNTIME_CONFIG_GAP (state row ≠ requested config)
CLI oneshot/resume records `model_config={"max_iterations": 90, "reasoning_config": null, "max_tokens": 16384}` even when config/prompt requests reasoning max + 300 iterations (interactive desktop sessions DO record `reasoning_config: {enabled, effort:max}`). Never claim "reasoning max" from intent — prove it from the state row. If null/90: log `RUNTIME_CONFIG_GAP` with exact command + row values, continue on the SAME model route with extra Manager verification. Do not switch models.

## 6. Iteration ceiling (90) is NOT terminal
Worker exits EXIT:0 with an honest final report (done vs not-done). Typical leftover: LOG/REPORT sections, `*_done.json` evidence, STATUS line. ALSO common: the worker wrote a PREMATURE claim into LOG ("STATUS: TASK_SUBMITTED", "evidence: X.json") BEFORE actually creating the files. Manager must:
1. verify each claimed evidence file EXISTS (`ls`/hash) before believing any STATUS;
2. resume the latest effective session with a SHORT evidence-only packet (fix LOG header/placeholder, append REPORT section, write done.json, set real STATUS, stop);
3. append `SUPERSEDED/PREMATURE` correction lines rather than rewriting history.

## 7. Owner transfer (repeat forbidden writes)
state.db `messages` table proves who wrote what: `SELECT id, session_id, role, substr(content,1,300) FROM messages WHERE id IN (...)` — Codex cites message IDs where a session switched to Python read/replace/write on a protected file ("patch tool fails → switch to script writer" is the tell). Repeated occurrence ⇒ `OWNER_TRANSFER_REQUIRED=<reason>` in registry; freeze ALL sessions of that lineage; open exactly ONE fresh recovery worker for the SAME Task ID; never two owners.

## 8. Manager independent verification ladder
Never trust the worker report alone:
1. re-run `sha256sum` + `wc -l` + def/unique/dup counts on the two critical files;
2. `diff <pre-edit snapshot> <current>` — bounded-hunk audit: expect ONLY authorized regions; a single pure-append hunk (`2810a2811,3153`) proves test additions touched nothing existing;
3. re-run U/micro + matrix + full module + focused ×2 + broad ×2 on fresh short basetemp `%TEMP%/mfc*`, `-p no:cacheprovider`, capture EXIT + elapsed into `manager/` logs;
4. static: ruff `--select F`, mypy on affected prod files, `git diff --check`, alembic heads + fresh-DB upgrade smoke, OpenAPI op-id dup check, process/port quiescence (`ps`, `netstat`);
5. spot-check worker classification claims against ACTUAL source lines (read the referenced lines yourself);
6. count deltas must be explained by node IDs (62 retained + 6 new = 68; 282 + 6 = 288).

## 9. Manager terminal vocabulary (hard rule)
Manager NEVER writes `APPROVED`, `CLOSED`, or `SPRINT_CLOSED` — Codex explicitly flagged a prior manager packet with `APPROVED / SPRINT_CLOSED` as ROLE-INVALID (finding P2). The only positive Manager terminal:
`S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`
Final review packet rules:
- create it ONLY after every cited gate log exists AND has been hashed;
- its mtime must be LATER than all cited gate logs (`stat -c "%y %n"` to prove);
- supersede role-invalid statements via append-only registry/LOG rows (`SUPERSEDED: ... role-invalid`), never delete.

## 10. Windows/MSYS hardline-blocked commands (recurring)
The terminal tool's parser BLOCKS certain innocuous commands: empty grep patterns (`grep -c ""`), complex `$(...)` substitution combined with nested quotes, `grep -o '"[^}]*}'`-style char classes. Fix: split into simple commands, avoid empty patterns (use `wc -l`), run `$(...)` and quoting in separate calls, use fixed-string greps. Don't retry the same shape — reformulate.

## 11. Killed/paused worker: session ID recovery (2026-09-03 S11 run)
`session_id:` prints ONLY on normal exit. A killed `hermes chat -q` process leaves no ID anywhere in its log. Recovery:
- `hermes sessions list` — the `--workspace` filter did NOT match killed runs; filter by title instead (title = prompt first line; cron rows interleaved).
- Resolve the ID from the list BEFORE any `--resume`. A wrong-ID resume injects the wrong prompt into the wrong session's context (observed: T02B ID used on a T03B resume — killed within seconds). Never guess.
- Killed sessions resume with FULL context; uncommitted drafts survive a task-branch fast-forward; resumed worker re-scans drafts against the corrected contract.

## 12. Stale background-exit notifications
After a long multi-worker sprint, `[IMPORTANT: Background process ... completed normally]` notifications keep arriving for every historical bash wrapper (minutes/hours after real completion). They are cleanup noise: confirm terminal state stays unchanged, reply one line, do NOT re-verify or re-run anything.

## 13. Liveness signals under long silent phases (2026-09-04 S11-C2 run)
The user reads multi-call silence as idleness ("có đang làm ko thế?", "thế nào rồi?"). Every turn must contain at least one real tool call with real output — never end a turn on promises alone. During long blocked/forensic phases: lead with one-line status + `date`, keep worker/verify commands running in background with notify, and report raw evidence paths (not ETA-only). Silence >2 turns always triggers a user ping; a turn with a live check never does.

## 14. CLI session identity forensics (2026-09-04 T05A/T04D misroute proof)
`sessions` table rows use `id` = CLI session ID (`hermes sessions list` shows it in the last column). Durable task identity lives in `messages.session_id` first user row: `SELECT role, substr(content,1,200) FROM messages WHERE session_id=? ORDER BY timestamp ASC LIMIT 2` — the prompt first line names the exact Task ID (e.g. `# S11-T05A ...` vs `# S11-T04D ...`). Query the LIVE `state.db` read-only via URI (`file:...state.db?mode=ro`); never copy the DB first (copies go stale mid-sprint and `-shm`/`-wal` sidecars pollute evidence dirs — delete them if created). `hermes sessions export --session-id X` exports ALL sessions to a file literally named `X` (392MB for 884 sessions) — avoid; query SQLite directly instead.

## 15. `hermes chat -q` dispatch pattern (S12-R6 run, 2026-09-15, Hermes v0.19.0)
Canonical dispatch for Manager + workers on an exact route (`ocg/deepseek-v4.1-flash`, provider `custom`, fallback OFF):
```bash
cd <worktree> && hermes chat -q "$(cat prompt.txt)" \
  -m "ocg/deepseek-v4.1-flash" --provider custom \
  -Q --yolo --accept-hooks --pass-session-id --max-turns 400 \
  > "evidence/work-turnN-console.txt" 2>&1; echo "EXIT=$?" >> "evidence/work-turnN-console.txt"
```
- Launch via `terminal(background=true, notify_on_complete=true)`; `-q "$(cat file)"` is safe for multi-KB prompts (same rule as `-z`).
- `-Q` quiet suppresses banner/spinner, but assistant text + thinking traces STILL stream into the redirected console file → it grows live (block-buffered ≈8KB; mtime can lag 8+ min during long generations — NOT a hang). Liveness = process alive + `git status` of the write-set + process-list scan. (This supersedes §4's "0 bytes until final report" for chat-mode runs — that was `-z` behavior.)
- `--pass-session-id` puts the session id in the worker's system prompt (worker can self-report); the CLI also prints `session_id: 2026...` right before exit → capture from console into the registry.
- Observed: `hermes chat ... -r <id>` resume prints the SAME session id on later turns — one stable ID per Task owner across the whole task.
- One dispatch = one turn (up to `--max-turns` tool iterations). Worker stops → resume same session with a SHORT "tiếp tục làm việc đi + re-check state" nudge; never resend the whole packet.

## 16. Readiness-first two-phase dispatch (before any write authority)
Dispatch a short read-only readiness turn first (`--max-turns 30`): worker runs `pwd` / `git rev-parse HEAD` / branch / `git status --short` / `git log -2` / `ls <allowlist dir>` / `python.exe --version`, reports session id + model + RAW outputs + "READINESS_OK — zero writes". Only then dispatch the work turn (resume the same session). Capture the readiness console as evidence; every owner proves alive+correct-route BEFORE its first write.

## 17. Temporary-connection-error resume cycle (502/503 fetch timeouts)
Upstream hiccup → turn dies with `API call failed after 3 retries: HTTP 503 ... 502 fetch connect timeout` + EXIT=1 (often 3 lanes in the same window, one survivor). NOT terminal:
1. Byte-safety check FIRST per affected worktree: `git status --short` (design-phase deaths usually leave the tree clean; confirm no partial source edits).
2. Wait ≥5 min after the failure timestamp (policy minimum; do not retry earlier).
3. Liveness probe: tiny `hermes chat -q "Reply with exactly: PROBE_OK..." -m <route>`; log latency (57s probe = degraded upstream → expect repeat failures; keep cycling).
4. Resume the SAME session/same route with a short note: "previous turn died from a temporary connection error — not your fault; route/scope/allowlist unchanged; verify current state (git status + your evidence files), continue from the stop point, do not redo completed work."
5. Record failure times, affected sessions, partial-write findings, probe result + latency in an `INCIDENT_*.md`; registry row `RUNNING_RETRY_WAIT → RESUMED`. Cycle `wait 5min → probe → resume` without limit.

## 18. Byte-guard baselines vs sanctioned lane merges (false "protected changed")
Pre-dispatch guards go STALE when a lane does its sanctioned `git merge --ff-only <wave-base>`: protected files legitimately become the wave-base version → `protected_file_changed` / `guarded_file_missing` for exactly those paths. Before calling a violation:
1. Compare each flagged path LANE-worktree vs CANDIDATE-worktree (integration tree at wave base): byte-identical ⇒ merge-induced, benign (missing on BOTH sides = file relocated by design).
2. Not identical? EOL check: `tr -cd '\r' < f | wc -c` (CR count) + `tr -d '\r' < f | sha256sum` (LF-normalized hash) + `git rev-parse HEAD:<path>` (blob). Same blob / same normalized hash with a CR-count delta = checkout EOL artifact, NOT a violation (64-byte size diff ≈ 64 CRLF↔LF lines).
3. Record proof JSON (`all_merge_explained: true`) + capture NEW `guard-*-postmerge.json` baselines for the correction phase.
4. Cross-OS-owned worktrees (`.git` owned by e.g. CodexSandboxOffline): use `git -c safe.directory='*' …` per invocation; NEVER write global git config.

## 19. Manager acceptance verify per lane commit (checklist proven on 4 lanes)
Before marking MANAGER_VERIFIED: `git show --stat --format="%H %P%n%s" <sha>` (parent == wave base; file list ⊆ write-set); `git status --porcelain` clean; `git diff --check <base> <sha>` exit 0; `ruff check --select F` on changed .py files; **Manager re-runs the worker's own new suite** (parity check on reported counts — reproduced 85/79/17/11 exactly); guard-allow verify with `--allow-change <all allow paths>`; protected merge-explained (§18). Worker commits are transport checkpoints, not approval.

## 20. Visible heartbeat without cron (desktop chat)
Cron heartbeat does not deliver to desktop chats; chain a bg process instead: `sleep 1140; powershell -File heartbeat_collect.ps1; echo CYCLE_DONE` with `notify_on_complete=true` — each completion wakes the Manager for a status turn; re-arm immediately in the same turn. The collector appends per-lane console size/mtime + live worker-process count to `manager/HEARTBEAT.md` (durable evidence). ≈19-min spacing keeps the ≤20-min rule with margin. Stale exit-notices for old wrappers keep arriving after — one-line ack, verify state, do not re-run.

## 21. Wave-1 CPU/GPU dispatch mechanics (MF-RESKIN-MODEL-UPGRADE, 2026-09-22)

Adds to §3/§5/§6/§18 from a 3-worker-wave + 2-round continuation run on `ocg/deepseek-v4.1-flash`.

**21a. The iteration ceiling is SOFT — do not size a continuation off the number 90.**
`-z` rounds on this route finished with `tool_call_count` of **110 / 122 / 126** (measured in
state.db after `agent_close`), not 90. Consequence: (a) a single narrow packet can carry far more
work than §6 assumes — plan for 1–2 rounds per task, not 4; (b) the cap is still real, so the
"exit 0 ≠ deliverable" rule stands: read the worker's own honest `RUNNING` vs `TASK_SUBMITTED`
line, then verify every claimed artifact on disk yourself. A round that ends at the cap with a
truthful "evidence set incomplete, nothing committed" is a NORMAL outcome, not a defect; the
continuation packet should then consist of the worker's own numbered next-step list, verbatim.

**21b. Build the protected baseline by SUBTRACTING each task's exclusive write-set.**
Symptom: `mfv1_guard.py verify` returns `FAILED` with exactly N `protected_file_changed` rows whose
paths are the *running writer's own allowlist* files. Cause: the task's implementation files were
listed in the protected manifest as well as in the task write-set. Fix, in this order:
1. Read the failure report before reacting — if the flagged paths are the live task's allowlist, it
   is a manifest-classification bug, not a worktree violation. Do NOT freeze the writer.
2. Emit a corrected manifest that removes those paths (`protected-baseline-corrected.json`) and
   record a `reclassification` block naming the moved paths, count and reason.
3. Re-run verify on the corrected manifest → expect `VERIFIED, failures 0`.
4. Guard the moved paths separately against the task's own preimage manifest, and run a **shrink
   check**: every flagged file must have grown or be byte-identical — any dropped line count is a
   real incident. (All 8 files here grew: adapter 442→739 L, lease 208→442, gpugate 140→263.)
This is distinct from §18 (merge-induced change): §18's paths move because a lane merged the wave
base; §21b's paths are the active writer's own edits.

**21c. Snapshot the worker's dirty/untracked bytes BEFORE dispatching its continuation.**
A cap-hit round leaves the worktree DIRTY and uncommitted. Snapshot every `git status --porcelain`
path byte-for-byte into the evidence root, hash-verify the copies, and write the manifest
(`<task>-rN-dirty-snapshot.json`) before the next dispatch. It is recovery evidence only — never
copy it back over the implementation, and never let it substitute for the worker's own commit.
Costs seconds; recovers a whole round if the resumed worker destroys its own bytes.

**21d. Verifying a worker-produced download/model manifest.**
- **Read one record's key names first** (`print(list(d['files'][0].keys()))`) instead of guessing
  field names — guessed keys raise `TypeError`/`KeyError` mid-format and waste a turn.
- For a multi-GB set, do not re-hash everything: **spot-hash the smallest files** with your own
  hasher and compare against the manifest's `actual_sha256`. (Here: 3 files of 91 MB / 253 MB /
  253 MB from a 76.66 GB set, all matched → manifest trustworthy; the worker's full pass is
  reported as its own cost/time row.)
- Re-run the worker's own validator/verifier and its test file yourself, and confirm the manifest
  counts (`VALIDATED` vs `UNVALIDATED`) rather than trusting the summary line.

**21e. Per-round receipt + 60 s sampling monitor (heartbeat fuel without cron).**
Launcher writes a receipt JSON per round beside the log: `packet`, `packet_sha256`, `packet_bytes`,
`cwd`, `model`, `argv_shape`, `started/ended_at_utc`, `duration_seconds`, `exit_code`, `pid`. A tiny
foreground-free monitor loop samples every 60 s into `manager/logs/monitor.log`: worker python
process count (subtract the Manager's OWN `hermes desktop` + `hermes serve` pids), `nvidia-smi`
used/util, listening ports of interest, and per-task `log_bytes` + `receipt` existence; it exits when
all expected receipts exist. This is the desktop-chat equivalent of §20 and doubles as the 8-minute
liveness audit: an all-zero `log_bytes` with a rising `tool_call_count` in state.db is normal for
`-z` (§4), never a hang.

**21f. A static gate can report a FALSE PASS when it examined nothing.**
Observed while verifying a worker's write-set on Windows: `ruff check --select F <9 files>
/c/Users/.../dir` emitted `warning: Failed to lint C:\c\Users\...: The system cannot find the path
specified` and then, on the next line, `All checks passed!` — having linted **zero** files. The
MSYS-vs-native path mismatch turned the gate into a no-op whose output still reads green. Rules for
§8 step 4 and for every lint/check/validate gate:
- Pass **native `C:/...`** paths to Windows executables (`python.exe`, `ruff`, `git -C`); a leading
  `/c/` is silently mangled into `C:\c\...`.
- Never quote a green check as evidence without proving the tool inspected the expected items:
  count the files/rows in the output, or scope the command to a set you can enumerate.
- When a checker prints BOTH a warning about a path and a success line, treat it as a FAILED gate
  and re-run with corrected arguments — a no-op gate is worse than a red one because it hides a
  real defect.
Prefer scoping such gates to the changed-files list (`git diff --name-only <base> <sha> -- '*.py'`)
so the expected count is knowable and mismatches are visible.

**21g. Verifying a worker's evidence matrix instead of reading its summary line.**
Worker reports ("40 rows: 35 pass / 4 n-a / 1 fail", "10/10 negative controls proved") are claims.
Re-derive them from the artifact: load the JSON and `Counter(row["disposition"])`, then check
`rows_undispositioned == 0` and that every `not-applicable` row carries a *reason* (not a blank).
Two signals to treat as POSITIVE, not as defects:
- a **self-disclosed `fail` row** whose note names the damage and why the bytes are not
  recoverable (proves the worker ranked honesty over a clean table) — record it, do not demand a
  retry that would fabricate the lost evidence;
- a **`not-applicable` row that says "UNPROVEN this round, carried as open item"** — an honest
  unproven path is better than a claimed pass; carry it forward in the registry's open-gaps list.
Conversely, a **negative-control table** only counts if each row names the deliberately-broken
input it must catch (`frame_count_exact ← TAIL_TRUNCATE`) and the assertion flips to FAIL on it.
An assertion without a failing control is an unproven assertion, and `UNKNOWN`/`UNMEASURED` is
never a pass. Also re-run the worker's own reviewer command end-to-end and hash the evidence tree
before/after: entries that change are the ones YOUR run wrote (e.g. a command transcript), so a
"30/31 byte-identical" result is the expected shape, not drift.