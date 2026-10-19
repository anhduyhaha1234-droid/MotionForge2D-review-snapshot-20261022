---
name: pm-session-execution
description: "Use when executing PM-gated sessions (LOG/REPORT) or acting as Hermes Manager dispatching workers. CLI dispatch/verify recipes: references/hermes-cli-dispatch-and-verify.md."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [pm, protocol, session, reporting, scope, acceptance-criteria]
---

# PM-Gated Task Session Execution

## Trigger
User provides `SESSION_PATH: docs/pm/sessions/<ID>` (or similar) and a task prompt describing the protocol: required reading, allowed write scope, validation commands, acceptance criteria, stop conditions.

## Mandatory sequence
1. **Read in exact order**: `SESSION_PROTOCOL.md` → `TASK.md` → every file in TASK.md's "Required reading". Do NOT read PRD/Master Plan/milestone docs that aren't listed.
2. **`git status --short` BEFORE any change**; identify every pre-existing user change (modified AND untracked) and protect them — snapshot `git diff` of user-modified files so preservation is verifiable at the end.
3. **Write baseline LOG.md** at the session path: required-reading checklist, protected user changes, baseline commands+results, plan (≤7 steps).
4. **Confirm in chat (short)**: Task ID, outcome, allowed write scope, forbidden scope, validation commands, plan.
5. **Implement within allowed scope only.** Never touch forbidden files even to "help" — record out-of-scope findings in REPORT.md instead.
6. **LOG.md is append-only**: corrections are NEW entries; never rewrite or delete old entries.
7. **Run required validation**; record real command output verbatim (hash before/after, tests run twice, `git diff --check`, `git status --short`).
8. **Fill REPORT.md** → status `SUBMITTED` with: evidence per acceptance criterion, exact commands+results, changed-files list, deviations/limitations, out-of-scope findings, test pass/fail/not-run.
9. **STOP for PM review**: no self-`APPROVED`, no `PM_REVIEW.md` edits, no commit/push, no starting the next task.

## Evidence patterns that satisfy reviewers
- **Pollution proof**: SHA256 of the data file (e.g. `channels.json`) before/after TWO test runs — identical hashes prove isolation. On Windows: `certutil -hashfile <file> SHA256` (equivalent to `Get-FileHash`; `Get-FileHash` is the PowerShell form).
- **Asset safety**: per-file `sha256sum` snapshot of a production dir (file set + content) before/after.
- **User changes preserved**: `git diff --stat` of user files at start vs end; grep for user-added symbols.
- Record ACTUAL numbers (test counts, exit codes, durations) — never "passed" without the summary line.

## Test-isolation patterns (proven in S00-T01)
- **Constructor DI hook**: add an optional path param (e.g. `channels_file: Path | None = None`) defaulting to production behavior; tests inject `tmp_path` paths. Minimal, backward-compatible, no global monkeypatch.
- **Function-scoped fixtures, not session-scoped**: shared session storage makes tests order-dependent (CRUD counts collide). `tmp_path` per test = order-free.
- **Read-only snapshot regression**: snapshot production dir (filename → sha256) BEFORE, generate on a tmp root, assert snapshot unchanged AFTER. Never construct a write-capable object pointed at production inside tests.
- **Route-level isolation**: use the conftest client fixture that patches `deps._config` to a temp root — a local unpatched `TestClient(app)` lets routes hit the production singleton (a latent write path even when assets happen to exist).
- **NEVER bare `TestClient(app)` — lifespan migrates the MAIN production DB (verified 2026-08-16, S08-T03):** a worker debugging a 500 with a bare `TestClient(app)` (outside the conftest client fixture) started the FastAPI lifespan, which ran alembic against the DEFAULT database URL and upgraded MAIN `data/motionforge.db` in place (311296 → 417792 B). The protected-data gate caught it. Recovery recipe (manager re-verified independently):
  1. Restore source: the backup-policy file `data/motionforge.db.bak-<ts>-<hash>` (auto-created at app start) — pick the one whose size == baseline.
  2. Prove byte-exact: `certutil -hashfile` of the restored DB == SHA of the backup file (not just size).
  3. Prove content: `alembic_version` == pre-incident head, expected table list (e.g. 17 tables, NO `object_role`), byte size == baseline.
  4. `channels.json` SHA unchanged.
  5. Enforce in every subsequent task prompt: all backend repros/tests go through pytest fixtures (isolated temp DB); bare `TestClient(app)` is forbidden. Full transcript + evidence table: `references/s08-t03-main-db-migration-incident.md`.

## Launching & monitoring background session runs (run-*.ps1 convention)

MotionForge2D-style sessions are launched by `output/run-<task>.ps1` scripts that pipe
`hermes chat --query ... --source cli --max-turns N --provider custom --model <id> --pass-session-id --checkpoints`
through `Tee-Object -Append`. They produce:
- `output/<task>-hermes.log` — **UTF-16LE** (PowerShell `Tee-Object`); in bash read via `tr -d '\0'` or `iconv -f UTF-16LE -t UTF-8`
- `output/<task>.pid` — runner PID

Starter template for a fresh per-task worker (hard guard + read/implement/
verify/report contract baked in, verified 2026-08-05):
`templates/run-hermes-task-fresh.ps1` — copy, fill TASK_ID/REPO_ROOT/PROMPT,
syntax-check, launch in background with notify_on_complete.

Correction-round template (resume SAME session, findings
verbatim, verified 2026-08-17): `templates/run-hermes-task-correction.ps1` —
copy, fill TASK_ID / SESSION_ID / MODEL / PROMPT. The model DEFAULTS to the
one the session was created with (flash sessions resume flash, pro resume
pro), but a LATER user directive overrides it for not-yet-started resumes —
edit `--model` in the launcher accordingly and record the reversal (see
Mid-sprint model change).

Liveness diagnosis (never assume — check all three):
1. PID file → `powershell -NoProfile -Command 'Get-Process -Id <pid> -ErrorAction SilentlyContinue'`; empty = DEAD
2. Log mtime (`stat -c %y`) vs now — a log that stopped growing = task stopped
3. Log tail — grep for `Resume this session with: hermes --resume <ID>` (death marker; the ID is the recovery handle), `API failed after 3 retries`, `HTTP 502`, `fetch connect timeout`

Model smoke test BEFORE relaunch — a 200 on `/v1/models` proves nothing; test the EXACT model id the run will use:
```bash
curl -s -X POST http://127.0.0.1:20128/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"ocg/deepseek-v4-flash","messages":[{"role":"user","content":"Say OK"}],"max_tokens":20}' --max-time 60
```
A 502/connect-timeout here means the run will die again — pick a working model (ask the user if the run script's model choice matters to them; e.g. "chạy lại bằng deepseek" = use DeepSeek id, not mimo).

Relaunch: write a FRESH `run-<task>-<model>.ps1` (never edit the dead one in place), syntax-check it:
```powershell
$errs = $null   # REQUIRED — see false-green pitfall below
[System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$null,[ref]$errs)
if ($errs.Count -eq 0) { 'PS SYNTAX OK' } else { $errs | % { $_.Message } }
```
**PowerShell Parser false-green (verified 2026-08-17, S08-T03-C1):** calling
ParseFile with an UNINITIALIZED `[ref]$errs` throws "cannot be applied to a
variable that does not exist" — and because `$errs` is null afterwards,
`$errs.Count -eq 0` still evaluates true and prints "PS SYNTAX OK". Always
initialize `$errs = $null` BEFORE the call, or the syntax check reports a false
pass on a broken launcher.
launch in background, then verify ACTIVE work — log grows between two samples ~20s apart AND tail shows tool-call lines, not just startup headers.

**Launcher prompt quoting — keep it SHORT, no double quotes (verified 2026-08-05, S05-C04):**
- A ~7KB prompt embedded in the .ps1 fails with exit 2 and NO agent output in
  the log (only the prompt echo). A shorter prompt that still contains `"`
  characters (e.g. a quoted status string like `"Status: READY"`) breaks
  argument parsing through bash→PowerShell:
  `hermes: error: unrecognized arguments: READY while TASK.md...` — the
  quotes get consumed and the remainder becomes extra argv.
- Fix: put ALL task detail in packet files (TASK.md / START_PROMPT.md /
  Codex findings doc) and make the launcher prompt only say: hard guard →
  read the packet completely → follow exactly → stop at SUBMITTED. The
  worker reads the packet itself; the prompt does not need to carry the
  contract.
- Diagnostic: `hermes: error: unrecognized arguments:` + a fragment of your
  own prompt text in the log = quoting failure, not a task failure. Rewrite
  the prompt (no quotes, shorter), do NOT relaunch the same file.
- **Surgical fix for a single offending quote (verified 2026-08-17, S08-T06-C1):** the rule above says rewrite the whole prompt, but a long prompt that fails ONLY because of ONE stray `"` (e.g. a quoted phrase like `no "job service not initialized" loop` inside the here-string body) can be fixed by deleting just that quote (`no job-service-not-initialized loop`) and relaunching the SAME file — no packet-file rewrite needed. The one-error-unrecognized log will name the exact token after the failing quote (`unrecognized arguments: service not initialized loop. 6. Separate metrics...`), so you know precisely which quote to remove.
- **PRE-LAUNCH QUOTE SCAN (verified 2026-08-17):** after writing any run-*.ps1, scan the $prompt body for residual double-quotes before launching — the ONLY allowed `"` are the here-string delimiters `@"` / `"@`. Bash one-liner:
  ```bash
  sed -n '6,33p' run-<task>.ps1 | grep -n '"' | grep -v '@"'
  ```
  Any hit is a future `unrecognized arguments` failure. The T06-C1 launcher was the ONLY one in the cycle that failed because every other launcher had zero quotes in the body — one invisible character cost a full fail→diagnose→fix→relaunch loop.

**One background instance only — file-lock on shared log (verified 2026-08-05, S05-C04):**
Running a second instance of the same launcher (e.g. a foreground smoke test
while the background instance is live) makes both Tee-Object to the same log
path → `IOException / FileOpenFailure` (exit 127). Launch exactly ONE
background instance; if you must smoke-test the launcher, do it BEFORE the
background launch or with a distinct log path. When a process-poll shows a
wrapper PID "DEAD" but the log has content, check for the real `hermes.exe` /
`python.exe` worker process (wrapper may exit after spawning the daemon-side
session); verify with `Get-CimInstance Win32_Process | Where CommandLine
-match "chat"`.

**CLI worker background-child death — exit 0 but NOTHING written (verified 2026-08-06, S08-T01):**
A `hermes chat --source cli` worker that launches a sub-agent (Codex, Claude
Code) as a SESSION-SCOPED background process (`terminal(background=true)`) and
then ENDS ITS TURN to "wait for the notification" kills the child the moment
the CLI session exits — a CLI session ends when the turn ends; it does NOT keep
background children alive like the desktop app. Verified: S08-T01 worker exited
"normally" (exit 0, 14m24s, log tail printed `Resume this session with: hermes
--resume <id>`) having written NOTHING — worktree git-status count unchanged,
REPORT.md still NOT_STARTED — because its Codex child (`proc_a4ab082b8cdf`)
was gone from `process(action='list')` at poll time. The worker's brief had
been written to a temp file for Codex, but no implementation ever landed.
- **Prevention (bake into EVERY worker prompt):** implementation sub-agents
  MUST run in FOREGROUND blocking mode inside the worker's own tool call
  (e.g. `codex exec …` with a bounded timeout that blocks until it finishes).
  NEVER spawn a background process and end the turn before it completes; never
  end the turn while work is pending.
- **Never trust exit code 0 for CLI workers** — after ANY exit, verify
  artifacts: worktree `git status` count changed? REPORT != NOT_STARTED? LOG
  has validation entries? Exit 0 + untouched worktree = non-completion exit.
- **Recovery for a non-completed Task ID (NOT a CHANGES_REQUESTED):** RESUME
  the exact stored session ID — same Task ID = same session, never a fresh
  session: `hermes chat --resume <session_id> --query "<recovery prompt>"
  --source cli --max-turns N --provider custom --model <id> --pass-session-id
  --checkpoints`. The recovery prompt must state the root cause explicitly
  (evidence: worktree count unchanged, REPORT status), demand foreground-only
  execution, and require completion through REPORT=SUBMITTED before exiting.
  Record the incident + resume lineage in the sprint tracking file so Codex
  sees the same-session continuation. Full timeline/evidence:
  `references/s08-t01-cli-background-child-incident.md`.

## User visibility: logs must be watchable in Hermes desktop

The user monitors task logs from the Hermes desktop app and the MAIN project folder
(e.g. `C:\Users\Admin\MotionForge2D`), NOT worktree `output/` dirs. When asked to
"bring the logs up" (e.g. "đưa log lên desktop / hiện tôi ko thấy cái nào"):
1. Create `output/hermes-task-logs/` in the MAIN repo and copy all `*-hermes.log` there
2. Run the background watcher `scripts/live-log-watcher.sh` (10s sync + UTF-8 tail for preview)
3. `focus_pane('files')` + `open_preview(<...>-LIVE.txt)` so the user actually sees it — do NOT stop at "files are in the folder"
4. ONE watcher per task, named per task (e.g. `watch-s05-t04.sh`); kill the old
   watcher when its task exits — stale watchers pile up silently. On a RESUME
   with a new log path (e.g. `s08-t01-resume-hermes.log`), kill the old
   watcher and start a fresh one pointed at the NEW log, then reopen the
   preview on the new `<task>-LIVE.txt` — the watcher's SRC is hard-coded.
5. CLI-background workers do NOT appear as new chat sessions in the desktop UI —
   if the user asks "sao không thấy session mới / có chắc đang chạy không",
   answer with live evidence (process alive, log mtime fresh, tail showing
   tool-call lines) and point at the LIVE.txt preview + sessions pane, and
   explain the worker session is a CLI session tracked in the sprint tracking
   file, not a chat window.

## Run placement verification & incident reporting (verified 2026-08-05)

**Critical pitfall**: `hermes chat` launched from a PowerShell run script does NOT
reliably inherit `Set-Location $repoRoot` when the Hermes desktop daemon is
running — the agent session may execute with cwd = the daemon's cwd (often the
MAIN repo), silently writing ALL task files to the wrong repository. Verified:
S06-T05 agent wrote backend/frontend/tests/LOG/REPORT into
`C:\Users\Admin\MotionForge2D` (main) while the task belonged in worktree
`s06-t01-review`; REPORT.md ended up SUBMITTED in main and IN_PROGRESS in the
worktree. The agent's own log showed it navigating with MAIN-repo paths
(`ls -d /c/Users/Admin/MotionForge2D/docs/pm/...`).

Prevention + post-run checks:
1. Put the absolute workdir INSIDE the prompt itself: "Your cwd for ALL commands
   MUST be C:\...\MotionForge2D-worktrees\<wt> — run `pwd` first and `cd` if needed."
2. After every run, verify placement: `git status --short` in BOTH main and the
   worktree; compare mtimes of changed files. A task that reports SUBMITTED but
   leaves the worktree's REPORT.md untouched is misplaced.
3. **WRONG recovery (verified 2026-08-05 — do NOT do this):** "fixing" a
   misplaced run by copying the misplaced files from MAIN into the worktree.
   This CORRUPTED the worktree: the MAIN-tree character files were OLDER/
   weaker than the approved S06/R02 worktree state (nested publish/image
   endpoints instead of the approved flat contract), and the PM issued a
   formal S06-T05 CORRECTION to undo it. The backup-then-copy pattern only
   works when MAIN is NEWER — never assume it is.
   **CORRECT recovery:** the manager takes `output/backup-pre-copy/` BEFORE
   any copy (preserve directory structure). If the task was misplaced, restore
   the pre-incident approved files FROM THAT BACKUP, verify the approved
   regression suite passes BEFORE reimplementing, quarantine tests written
   against wrong endpoints (move to `output/quarantine-*/`, don't keep them),
   then reimplement the task on top of the restored state. Never overwrite an
   approved worktree file with a MAIN-tree copy. Full protocol:
   `references/s06-t05-worktree-incident-and-correction.md`.
4. Write a structured `INCIDENT_REPORT_<topic>.md` into the task packet
   (`docs/pm/sessions/<ID>/`) so the next Codex review sees it: what happened,
   root cause, disk evidence table (mtime per file, both repos), fix actions,
   current state, and the specific decisions Codex must make (e.g. keep or
   clean main-repo copies, delete backup dir, approve SUBMITTED task).
   Tell the user the exact one-liner to send Codex pointing at the report.
5. Update `docs/pm/ROADMAP.md` status cells to match reality (e.g. T04 APPROVED,
   T05 SUBMITTED) so the next-task handoff is accurate.

## Manager verification gate (mandatory queue protocol)

PM-queued sprints (e.g. S05: T03 → T04 → T05 → T06 → sprint exit) forbid
opening the next task until the current one has ALL of:

1. Hermes worker process has EXITED (not killed — check exit code; a killed
   process with exit -15 is NOT completion, and a Playwright/next-dev hang
   inside the run is a known partial-completion mode — finish or relaunch).
2. `REPORT.md` = SUBMITTED (never APPROVED — no self-approval).
3. Manager (you) independently reviewed the diff AND ran targeted tests
   yourself — never trust the worker's self-report alone. Run the manager
   verification ONLY AFTER the writer has fully exited and the tree is
   stable (never while a writer is alive — two pytest processes on the same
   worktree race on shared files/cache/basetemp and corrupt each other's
   evidence; a live worker mid-fix is ordinary writer work, not a blocker,
   and the manager stays read-only). Use a NON-shared pytest cache:
   `python -m pytest <files> -q -p no:cacheprovider
   --basetemp=<WINDOWS-NATIVE-TEMP>` (see MSYS pitfall below).
4. State recorded as `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`.

## Read-only helper parallelization (RO-1/RO-2, verified 2026-08-17 S08)

User-mandated pattern to cut idle time between correction rounds: up to 2 READ-ONLY helper subagents (delegate_task) run WHILE the coding writer is live — they pre-build the next-gate readiness report and the validation plan so the manager gate after writer exit is fast. Non-negotiables (user protocol, verbatim intent):

1. Helpers are NOT coding sessions: no Task ID, no task status, no APPROVED/CHANGES_REQUESTED power, no acceptance-contract changes. Only ONE writer ever exists on the worktree.
2. Hard read-only guard baked into EVERY helper brief (rule: "nếu không chắc một thao tác có read-only không → BỎ QUA thao tác đó"):
   - Allowed tools: read_file, search_files, terminal ONLY for ls/stat/pwd.
   - Forbidden: write_file/patch, pytest/Playwright/npm/build/lint/mypy/ruff, starting app/worker/browser/server/model, opening SQLite at all, migrations, creating cache/output/log/evidence, git commit/push/merge/reset/checkout/restore/clean/stash, git diff/status comparisons of the live writer's changes.
   - Forbidden reads: app/**, frontend/**, tests/**, migrations/** (partial implementation), and the live writer's log (that is polling the writer).
3. Helper results return ONLY in chat; the manager verifies every claim on disk before acting. Never convert helper findings into corrections while the writer is live; never open the next task until writer exit + manager gate.
4. If read-only cannot be guaranteed for a proposed helper, do not create it.
5. Helper must end after ONE report — no background loops, no polling.

Split of duties: **RO-1 (NEXT-GATE READINESS)** = the readiness report described in the section below (stable contracts + packets of DONE tasks only). **RO-2 (VALIDATION & EVIDENCE PLANNER)** = reads sprint contract + packets + protected baseline (values GIVEN in the brief, never hashed/opened by the helper); plans only — every planned command uses absolute temp root/DB/output; marks artifact/cache isolation; separates true production-path evidence from deterministic QA; outputs the validation matrix (Targeted/Integration gates, Production-GPU/UI-Playwright/Security evidence, Isolation/Protected-state checks, Commands-to-run-later, Risks/gaps).

Dispatch shape: delegate_task batch ≤2 tasks; each brief fully self-contained (helpers have NO conversation context) — worktree+branch, live writer identity (task ID + session ID + launcher/log), approved dependency sequence, protected-data baseline VALUES, the exact report format, reply language = user's language. After the batch completes, check EACH result: `status=completed` AND a report body present.

Pitfalls (verified 2026-08-17):
- A read-only helper can die mid-run with `API failed after 3 retries — HTTP 502` AFTER consuming 15+ API calls; the delegation result arrives without a report. Re-dispatch a FRESH identical brief — the pattern is cheap and idempotent; never treat a 502'd helper's partial transcript as a report.
- Helpers catch contract drift the manager assumed: e.g. a sprint prompt said "architecture contracts listed in Required reading of TASK.md" but the TASK.md has NO Required reading section, and the Codex finding list for the next task exists NOWHERE in the repo. Consequence: the resume prompt must carry the finding list verbatim + a reading list + exact write-scope file list; otherwise the worker invents scope (BLOCK condition).
- Timeline estimation ground truth: log birth/mtime (`stat -c '%w'/'%y'`) + historical per-task durations from the tracking file + writer phase from log tail (implementation → writing tests → validation). "N/N green. Now adding the correction-specific tests" = near done. GPU smokes are the biggest pessimistic swing (+30-60m).

Full brief skeleton + RO-1/RO-2 report formats + the `READ-ONLY PARALLELIZATION ACTIVE` setup confirmation format + timeline recipe: `references/read-only-helper-parallelization.md`.

Per-task session tracking for Codex (user requirement "tách session ra để
codex review", verified 2026-08-05): keep `output/SPRINT_S0x_SESSIONS_TRACKING.md`
in the sprint worktree with one row per task — task id, worker session id
(from the run's `Resume this session with: hermes --resume <id>` line),
model, started/finished, manager-verify evidence (exact pytest commands +
counts), REPORT status. Each task MUST get a fresh compact session (`--model
ocg/deepseek-v4-flash`, never `--resume` old sessions); write the packet
(TASK/START_PROMPT/LOG/REPORT/PM_REVIEW) BEFORE launching the worker, and
point Codex at the tracking file when the sprint ends.

## Chain the queue: never end a turn between tasks (user-complaint verified 2026-08-17, S08)

After a writer exits and the manager gate passes, LAUNCH THE NEXT TASK'S WRITER
IN THE SAME TURN. Ending a turn at "I'm preparing the next prompt" left the
S08 correction cycle idle overnight (~10h wall-clock for 45m of real work)
and drew an explicit user complaint: "sao chạy task vừa rồi tận 5 6 tiếng mà
mới xong task 1 à?" Rules:

1. Report progress AND start the next writer in one turn — the report is the
   preamble, not the deliverable.
2. When the user asks for an ETA, separate real work time from idle gaps
   honestly (list actual task durations vs wall-clock), and own your own
   scheduling misses ("lỗi điều phối của tôi") rather than blaming the tasks.
3. Kill the old task's watcher, syntax-check the next launcher, and launch it
   — all before ending the turn. notify_on_complete keeps the chain moving
   without user pings.
4. **Parallel prep while verification runs (verified 2026-08-17, S08 T04-C1 →\n   H01):** the manager's independent verification is a background script\n   (notify_on_complete), so WHILE it runs you may read-only prep the NEXT\n   task: for a NEWLY-authorized Task ID, materialize the whole packet\n   (TASK.md + START_PROMPT.md + LOG.md stub + REPORT.md NOT_STARTED stub) and\n   write + PS-parse its run-*.ps1 launcher; for a resume, verify the sibling\n   launcher's --resume/--model/log-path. All of this is read-only vs the\n   finished writer, so it cannot race anything. When verification completes,\n   you only need to write the tracking row and hit launch — gate-pass → launch\n   lands in the same turn with zero idle.\n5. **ETA / progress queries get answered FIRST, immediately, in the same reply\n   — never defer them behind tool calls (user-complaint verified 2026-08-17,\n   S08):** the owner repeatedly asked \"bao cao di / estimate bao laau thi xong /\n   bao cao tien do\" and explicitly pushed back when the answer came late\n   (\"vẫn chưa trả lời được là sao còn bao lâu thì xong\"). Answer order in the\n   reply: (1) the NUMBER the user asked for — current Active Task, writer\n   count, last-progress mtime, and a concrete ETA (writer-phase estimate +\n   manager-gate + next task) in a compact table; (2) heartbeat/blocker line;\n   (3) only THEN the supporting evidence. Do NOT open with a long status\n   preamble or say \"let me check\" and end the turn with no number — if you\n   already know log mtime + task phase + historical per-task durations from the\n   tracking file, you can produce the estimate from what you hold without extra\n   tool calls; a single quick `stat -c` is fine before replying, but never\n   chain several verification waits before answering. Re-supply the estimate\n   every time it is asked (fresh numbers each time), and when the user asks a\n   sub-question inside a directive (e.g. \"estimate + đã bật watchdog chưa\"),\n   answer BOTH halves in one reply.


## Liveness policy: heartbeat, bounded waits, auto-recovery (user mandate, verified 2026-08-17)

After a ~10h manager idle incident the user issued a formal liveness protocol.
Non-negotiables: NEVER idle silently; NEVER depend on a new user message to
continue authorized work; every wait is BOUNDED (≤10 min per check) and must be
followed by ONE concrete action — continue bounded wait if the worker shows
progress, collect if finished, run the manager gate, recover the exact session
if the worker died, or report AUTOPILOT_BLOCKED with cause+evidence+minimal
user action if a real blocker exists. 20 min without verified progress while
runnable work exists = LIVENESS INCIDENT → recover immediately. After 3 failed
recovery attempts → AUTOPILOT_BLOCKED.

Heartbeat format (chat only — never touch LOG/REPORT while the coding writer
owns the task), sent after this prompt, at task transitions, at recovery
start, at blockers, and at least every 30 min on long runs:

```
S08 MANAGER HEARTBEAT
- Time:
- Active Task ID:
- Active Hermes session:
- Active writer count:
- Last verified progress:
- Current action:
- Next bounded check:
- Next gate:
- Liveness state: RUNNING | WAITING_BOUNDED | RECOVERING | BLOCKED
```

Recovery states A–E: (A) RUNNING_WITH_PROGRESS → keep one writer, bounded wait;
(B) RUNNING_WITHOUT_CONFIRMED_PROGRESS → heartbeat WAITING_BOUNDED, one more
liveness check, at 20 min total switch RECOVERING; (C) COMPLETED_NOT_COLLECTED
→ collect now (below); (D) IDLE_OR_TERMINATED_UNEXPECTEDLY → verify no writer
remains, resume the EXACT stored session, preserve dirty state, never
reset/checkout/restore/clean/stash/delete; (E) REAL_BLOCKER → AUTOPILOT_BLOCKED
immediately, no fake progress. Record per attempt: number, detected state, last
confirmed progress, recovery action, result.

**COMPLETED_NOT_COLLECTED detection (verified 2026-08-17, S08-T02-C1):** a CLI
worker can finish while the manager is idle. Confirmed-by-disk signals: log
tail shows the death marker (`Resume this session with: hermes --resume <id>`),
log mtime frozen, size stable across two samples, 0 matching `hermes chat`
processes, REPORT status = SUBMITTED. Then IMMEDIATELY: confirm tree stable →
manager review + independent verification → MANAGER_VERIFIED_PENDING_SPRINT_REVIEW
→ launch the next dependency in the same turn. Never wait for the user.

**Manager verification script pattern (verified 2026-08-17):** write ONE temp
script OUTSIDE both repos (`C:/Users/Admin/AppData/Local/Temp/verify-<task>.sh`)
with numbered sections — focused suites, GPU smoke, cross-task suites, S05/S02
regressions, migration round-trip in a subshell (upgrade→downgrade→upgrade +
`alembic current`), env-leak echo (`MOTIONFORGE_DATABASE_URL=[unset]`). Run
background + notify_on_complete; afterwards read the FULL log — exit 0 alone
proves nothing, read each section's pass counts.
- **Frontend-only corrections add TWO more sections:** (a) frontend gates —
  `npx tsc --noEmit` + `npx eslint <changed files> --max-warnings 0`; (b) an
  anti-pattern grep for whatever Codex banned (e.g. `grep -rn "Dự án 2D\|v-001\|fabricat\|placeholder data" frontend/src --include=*.tsx --include=*.ts | grep -v node_modules | wc -l`). CRITICAL: a non-zero hit count is NOT automatically a FAIL — classify every hit first. This session's H01 grep returned 5 hits that were ALL code comments containing the words "never fabricated" (e.g. `// NO fabricated rows, no mock projects`); those are proof-of-absence and count as PASS (0 real hits). Print the grep matches themselves, not just the count, so the manager can judge comment-vs-code. Only real fabricated-data code paths fail the gate.
- **Verification-script `set -u` + unset env = silent aborted gate (verified 2026-08-18, S08-H02-C1 recovery):** a `#!/bin/bash` + `set -u` verify script that echoes `${MOTIONFORGE_DATABASE_URL}` when the var is unset dies instantly with `unbound variable` at line 13 — before ANY section runs. Always guard env echoes inside user-set scripts as `${MOTIONFORGE_DATABASE_URL:-UNSET}`, never bare `${VAR}`. (The subshell env-leak pattern needs the var UNset to prove no leak, so this hits exactly when you most need the echo.)
- **"Rows preserved" migration proof needs a SEEDED db + real table names (verified 2026-08-18):** round-tripping a FRESH empty DB proves nothing — `SELECT COUNT(*) FROM workspace` → 0 both sides is not preservation. Seed 2 rows via plain SQL after the first `upgrade head`, then assert counts across downgrade/re-upgrade. Also: the table is `workspace` (singular) and `object_role_artifact` — grep `__tablename__` in `app/persistence/models.py` before guessing; a guessed plural name yields `no such table` which is a query bug in your check, NOT a migration failure.
- **"Test missing" from a full-name grep is not proof (verified 2026-08-18, S08-H02-C1):** a mandated test may exist under a NEAR name (`test_metadata_update_failure_rolls_back_file_and_state` vs the handoff's `test_video_metadata_update_failure_rolls_back_file_and_state`) — an exact-match grep returning 0 registers a false "gap". Grep loosely first (substring `rolls_back`, lowercase) and count, THEN decide whether the distinct path is actually covered or a genuinely separate test is needed.
- **Playwright config names are dash-less (verified 2026-08-18, S08-T06-C2):** the file is `playwright.s08t06.config.ts`, NOT `playwright.s08-t06.config.ts` — guessing with a dash fails to find the file. Enumerate first: `find frontend -maxdepth 1 -iname 'playwright*.ts'` and copy the exact basename into your verify script / --list command.
- **A scripted section exit≠0 is often a harness bug, not a tool failure (verified 2026-08-18, S08-T06-C2):** a verify-script section that ran `cd frontend` and ended without `cd ..` made the NEXT section's `cd frontend` fail with `cd: frontend: No such file or directory` (EXIT=1) while Playwright itself was fine. When any scripted section exits non-zero, re-run the UNDERLYING command standalone before blaming the tool — a `cd`/path/grep-pattern bug in the harness masquerades as a suite failure.
- **Manager re-run of a golden/evidence-producing test must use a DISTINCT run id (verified 2026-08-18, S08-T06-C2):** golden tests write `output/s08-sprint/<S08T06_RUN_ID>/golden-metrics.json` (and screenshot dirs hardcode run ids), so a manager re-run with the WORKER's run id silently clobbers the worker's evidence. Re-run manager-side with a fresh id (`S08T06_RUN_ID=mgr-t06c2 GOLDEN_TMP_ROOT=<fresh>`), then the metrics JSON proves the numbers without destroying the worker artifact.

Run
returns at 180s with `status: timeout`) — for a multi-minute verification
script, prefer notify_on_complete and continue other work, or chain bounded
`wait` calls instead of expecting one long block.

**Watcher script ≠ running watcher (verified 2026-08-17):** `scripts/watch-*.sh`
files can exist from an earlier manager session while NO watcher process runs
(LIVE.txt goes stale). Verify with `Get-CimInstance Win32_Process` matching
`watch-s08` in the CommandLine — each watcher shows 2–3 bash PIDs (wrapper +
real bash + script path). Only ONE watcher per ACTIVE task; watchers for
future tasks (e.g. watch-s08-t05c1.sh before T05 starts) are harmless but
verify their SRC target. After (re)launching a watcher, confirm LIVE.txt mtime
is fresh and reopen the preview.

**Sibling manager sessions leave stale launchers/watchers behind (verified 2026-08-17, S08 T05-C1):** after a long idle gap (or any handoff between manager sessions), the worktree `output/run-<task>-c*.ps1` and MAIN `scripts/watch-*.sh` may ALREADY EXIST from the earlier session — possibly with the OLD model (S08 T05-C1 launcher pre-existed with `--model ocg/deepseek-v4-pro` and had to be patched to flash per the user's reversal directive) or an outdated session id. Before launching ANY resume: (1) `read_file` the existing launcher and verify `--resume <id>` + `--model` match the CURRENT tracking file + latest user directive — never trust a sibling's file blindly; (2) when `write_file` warns "modified by sibling subagent '<id>'" on a path you're about to write, READ it first, then decide overwrite-vs-patch (overwriting a sibling's better version loses their work; patching preserves it); (3) after any edit, re-run the PS Parser syntax check; (4) a sibling's launcher may target a DIFFERENT log path — check the `Tee-Object` target matches your watcher's SRC, else the LIVE.txt preview watches a dead file.

**Stored session-ID can be TRUNCATED — `Session not found` on an otherwise-correct launcher (verified 2026-08-17, S08-T06-C1):** a resume launcher may pass the PS Parser and still fail at launch with `Session not found: <id>` because the id recorded in the tracking file / pre-dating session record had its trailing char(s) cut (`20260816_203312_e9f2b` vs the real `20260816_203312_e9f2b8`). This is distinct from the quoting failure — same "launcher dies before the agent does anything" symptom, different root cause; the log head will also show the benign venv-health noise, so read the FULL tail for the real error. Recovery (each attempt logged, per liveness policy):
1. Read the log — `Session not found:` + `Use a session ID from a previous CLI run (hermes sessions list)` is the signature; do NOT hand-append a guess digit, fetch the truth.
2. `hermes sessions list` (grep the task + model + date); copy the EXACT id — these are 24-char `YYYYMMDD_HHMMSS_<16hex>`, so a missing trailing char like `e9f2b` vs `e9f2b8` is a one-char truncation that `--resume` rejects.
3. `patch` the launcher's `--resume <id>` to the exact id; also `patch` the tracking file's session-id cells (the task row AND the correction-cycle row) so Codex sees the corrected lineage — leaving the wrong id in tracking silently corrupts the review trail.
4. Re-run the PS Parser check, relaunch, then confirm the log shows `Resumed session <id> (N messages)` — that confirmation line is the success proof, not just "no error".
Also: the log-head noise "A previous lazy-backend refresh may have left the venv unhealthy — running import-based package repair… Import probes unavailable — cannot confirm venv health. Leaving `.lazy-refresh-incomplete`" is BENIGN and appears at the top of essentially every launcher log; it does not by itself mean the run is broken. Only treat it as a blocker when it co-occurs with an argparse `usage:` / `Session not found:` line (which is the real failure to diagnose).

**STALE FAILED-ATTEMPT notifications — a completed/exit monitor is NOT the live writer (verified 2026-08-17, S08-T06-C1):** during recovery of a launcher that first failed (e.g. quote error → `Session not found`), notifications from the EARLIER dead attempts arrive AFTER the fixed relaunch is running healthy. When any "Background process completed/exited" notification lands mid-run, do NOT treat it as the current writer finishing: cross-check (a) the PID against the CURRENT active proc_* you monitor, and (b) live log mtime/size still growing + `Get-CimInstance ... -match 'resume <session_id>'` still returns the hermes process. A stale notification is just the recovery trail's ghosts closing out — acknowledge, confirm the real writer is alive, continue; no gate and no action.

**certutil in git-bash — use forward slashes (verified 2026-08-17):**
`certutil -hashfile "C:/Users/.../channels.json" SHA256` — escaped backslash
paths (`C:\\Users\\...`) fail with 0x80070002 ERROR_FILE_NOT_FOUND. Same rule
for any Windows tool invoked from git-bash.

## Env-var contamination in manager pytest (verified 2026-08-16, S08-T03)

The terminal tool persists exported env vars across calls. Exporting
`MOTIONFORGE_DATABASE_URL` for a manual alembic round-trip check made every
subsequent pytest run migrate into THAT database instead of the test's
`tmp_path` DB, producing mass "no such table: workspace" failures (18 failed)
that looked like a broken submission but were purely manager-side environment
pollution. After `unset MOTIONFORGE_DATABASE_URL` the same suite passed 25/25.
Rule: after exporting any env var for a one-off check, `unset` it in the SAME
command or immediately after; never leave exported vars active for later pytest
runs. When a suite fails with DB-missing errors right after a manual migration
check, suspect your own env contamination FIRST. Safest one-off pattern: run
the check in a SUBSHELL so the export dies with it —
`(export MOTIONFORGE_DATABASE_URL=sqlite:///C:/Users/Admin/AppData/Local/Temp/x.db && python -m alembic upgrade head && ...)` —
then `echo $MOTIONFORGE_DATABASE_URL` after the subshell to PROVE it did not leak.

## MSYS path pitfall in manager pytest (verified 2026-08-05): passing an MSYS
path to pytest's `--basetemp` (e.g. `--basetemp=/c/Users/...`) makes Python
resolve it as `C:\c\Users\...` → `FileNotFoundError` on the tmp_path fixture
→ dozens of ERRORs that look like code failures. Always use the Windows-native
form `--basetemp=C:/Users/...`; if you see mass FileNotFoundError with
`C:\c\` in the path, that is the cause, not the code.

## Correction-round session mode is CODEX-DICTATED (2026-08-19, S08-H02-C3→C5)

Read the Codex text each round: RESUME-same vs NEW-session. C3/C4 protocol: ISO timestamps local +07:00 AND UTC Z, heartbeat ≤5 min + MANAGER_STATE.md, FINAL_REPORTED_TO_USER after final user-facing message, PS console UTF-8. Finding→fix→test map C2–C5: `references/s08-h02-correction-chain-c2-c5.md`.

## Manager migration round-trip on MotionForge worktrees (verified 2026-08-16,
S08-T02):
(protection — a bare `alembic upgrade head` raises `RuntimeError: No database
URL configured`, which is CORRECT behavior, not a failure). `alembic -x
db_url=...` is rejected by this setup (`unrecognized arguments: -x`). The
working manager recipe against an isolated temp DB:
```bash
export MOTIONFORGE_DATABASE_URL=sqlite:///C:/Users/Admin/AppData/Local/Temp/<task>-mgr-migration.db
python -m alembic upgrade head && python -m alembic downgrade <prev-head> && python -m alembic upgrade head
```
then verify `alembic_version` + expected tables via sqlite3. Never point this
env var at MAIN `data/motionforge.db`.

MAIN-status tripwire self-noise guard (verified 2026-08-16, S08): the
manager's OWN watcher scripts live in MAIN `scripts/watch-s08-*.sh`, so the
raw `git status --short | wc -l` on MAIN rises with every new watcher and
false-alarms the misplaced-write check. Compute the REAL drift as
`git status --short | grep -vc 'scripts/watch-s08'` (or whatever the
manager's own artifact prefix is) and compare THAT to the pre-sprint
baseline; only a change in the non-watcher count is worker drift.

External-actor MAIN drift (verified 2026-08-17, S08 correction): a BATCH of
new MAIN files sharing ONE identical mtime (e.g. 4 docs/pm HERMES_*.md all at
10:10:50, mid-worker-window) is an external actor — owner/Codex/autopilot
cron — not the hard-guarded worker. Verify protected hashes (channels.json
SHA, DB size), record the observation + mtimes in the tracking file for Codex
visibility, and continue the sprint; do not stop for it and do not attribute
it to the worker. `stat -c '%y %n'` each file to confirm the shared timestamp.

Hard worktree guard — before ANY write, the worker must run and verify:
`pwd` / `Get-Location` + `git rev-parse --show-toplevel` + `git status --short`.
If the root differs from the expected worktree: write NOTHING, report
`BLOCKED: WRONG_WORKTREE`, exit immediately.

Within the first 60s of a worker run, the MANAGER must `git status` BOTH the
expected worktree AND the MAIN tree. If MAIN shows new worker changes, kill
the worker and report an incident. Snapshot MAIN `git status --short | wc -l`
as a baseline before launching any worker.

Worker config for PM-queued tasks: `--provider custom --model <id>`, fresh
compact session per task (NEVER resume old MiMo/DeepSeek sessions with large
context), bounded individual commands, no copy/robocopy whole-directory
recovery.

**Mid-sprint model change by user directive (verified 2026-08-16/17, S08):**
the user may override the worker model mid-sprint ("từ các task sau trở đi
session mới mở hãy dùng model X"). Rules: (1) apply the new model to NEW task
sessions only — a session already running keeps its model; (2) corrections
resume the task's OWN session/model (same-session rule wins over the new
model); (3) smoke-test the EXACT new model id against the gateway before the
first launch; (4) if the user asks for max reasoning, pin it via
`hermes config set agent.reasoning_overrides.<model-id> max` (the config file
itself is write-protected against the agent — the `hermes config set` CLI is
the supported path; the CLI prints a "not a recognized config key — saved
anyway" warning, but the override IS read: verify with `hermes config get
agent.reasoning_overrides`); (5) record the change + effective date in the
session tracking file and user memory so the per-task model column stays
accurate for Codex review.
- **Directives can REVERSE a prior directive (verified 2026-08-17):** user
  switched S08 workers back to flash+max ("đổi hết các session sau worker về
  lại model deepseek v4 flash max nhé ko dùng pro nữa") after an earlier
  pro-max directive. Apply the reversal the same way — subsequent launches
  (new sessions AND upcoming resumes of not-yet-started corrections) use the
  NEW model; an already-running session keeps its model; update memory
  (replace the old routing entry, don't append) and the tracking file row so
  the model column reflects the reversal date.

Known E2E pitfall: Playwright `page.goto` hangs against a LONG-LIVED Next dev
server (known from T04 review; S06-T05 correction hit it again — suite timed
out at 600s). Before E2E, kill the old dev server on its QA port (e.g. 3010)
and start a fresh one; probe `curl .../characters` → 200 before re-running.

E2E cancel/retry timing race (verified 2026-08-05, S05-C02): a cancel test
can fail because the durable chain completes TOO FAST (<8s), so the cancel
button hits an already-completed job. This is timing fragility, NOT a backend
bug — evidence: the same test passed in the previous round (C01) with the
same fixtures. Make cancel tests race-robust: wait for a mid-chain step to be
observably active before clicking cancel, use `.first()` for duplicated
badges (strict-mode violation), prefer wait-based assertions over exact
timing. Also: after fixing a frontend bug, re-run the WHOLE Playwright suite
cleanly — tests that started before the dev server hot-reloaded may have used
the old bundle and fail spuriously; tests 5-6 passing after recompile proves
the fix, but the full suite must be re-run for the record.

"Iteration budget reached (300/300) — response may be incomplete" at exit
does NOT mean the work is incomplete (verified 2026-08-05, S05-T05): the
banner fired while the fresh 7/7 baseline and REPORT=SUBMITTED were already
done — it only means the final summary message was cut by max-turns. Before
resuming/relaunching, verify the actual artifacts: grep REPORT for
`Status: SUBMITTED` and read the latest `output/quality-baseline/*/summary.json`
(OVERALL PASS). Only resume if a criterion is genuinely unmet.

## Forced-stop recovery: doc-append integrity + recovery packet (verified 2026-08-18, S08-H02-C1)

When ALL prior manager/writer processes were deliberately killed, a worker's
LOG entry can LIE about its own documentation: the S08-H02-C1 worker logged
"REPORT.md appended CORRECTION C1 section" but was force-killed mid-append
(log tail froze at "Let me append to REPORT.md.") — REPORT.md on disk had
NO C1 section. Division of verification:

1. **LOG is self-reported; grep the ARTIFACT.** A LOG entry claiming a
   REPORT append proves nothing — grep REPORT for the actual section heading
   (`grep -nE '^## CORRECTION C1' <REPORT>`) and read the UTF-16 launcher log
   tail (`tr -d '\0'`) for the mid-append death marker. "LOG has C1 entry,
   REPORT lacks C1 section" is the classic inconsistency signature of a
   mid-append kill. Do not trust 169-status-count + stale LOG alone.
2. **Verify the remaining-gap claim against code before dispatch.** A handoff
   §5 "mandatory audit" is often a REAL uncovered path, not a formality: the
   update/publish endpoint called `set_video` AFTER `staging.replace(...)`
   OUTSIDE try/finally, so a metadata failure left the freshly published
   `source_<uuid>.mp4` as an orphan and did not restore the previous
   source/state. A similar-named test existing was a red herring — it only
   exercised the sibling replacement-image path (`test_metadata_update_failure_...
   ` monkeypatches `update_object`), never the video-source publish path.
   Read the endpoint's control flow (post-publish steps, try/finally extent,
   success-path side effects) to find the true gap.
3. **Recovery writer contract (never recreate completed code):** materialize
   a `RECOVERY_PROMPT.md` IN the task's packet dir with: proven current
   state (guards + file list), the exact remaining defect (from your own code
   read), the mandatory-audit acceptance bullets VERBATIM, files in scope,
   forbidden ops, doc-repair requirements (append recovery entry to LOG,
   append the missing section to REPORT — preserve ALL history), the full
   validation list, and STOP condition (SUBMITTED, never APPROVED). Then a
   FRESH launcher `run-<task>-<round>-rec.ps1`: resume the SAME stored
   session id, SHORT prompt with ZERO double quotes that only says "read
   RECOVERY_PROMPT.md completely and follow it exactly", a NEW log path
   (Tee to a different file than the killed run so the watcher SRC is not a
   frozen log), PS Parser check + PRE-LAUNCH QUOTE SCAN before launch.
4. **Manager exit gate adds a doc-consistency check:** after the recovery
   writer exits, verify LOG and REPORT AGREE — the missing section heading is
   present in REPORT AND the LOG recovery entry reflects the same runs; a
   recovered REPORT that still lacks the round = writer exited without doc
   repair, resume again. Keep the single-writer rule: manager stays read-only
   while the recovery writer is live.

## Mid-sprint correction and recovery additions (verified 2026-08-16, S08-T01 C1)

- **502 exit after completing work:** a worker that dies with `API failed after
  3 retries — HTTP 502 fetch connect timeout` may have FINISHED the task first
  (the 502 often hits the final summary message on a ~234K-token context).
  Before resuming: grep REPORT for `Status: SUBMITTED`, check the log tail for
  completed validation gates, verify the worktree diff. Only resume if a
  criterion is genuinely unmet. A transient gateway 502 ≠ model down — smoke
  test the EXACT model id (`curl POST /v1/chat/completions` with the exact
  model string) before relaunching.
- **User correction mandate may require SAME-session resume:** the S05
  convention is a FRESH session per correction round, but a user mandate can
  explicitly demand the opposite ("Resume the SAME exact T01 worker session —
  do not create a replacement"). When present, that instruction overrides the
  fresh-session default: build `run-<task>-cN.ps1` using `hermes chat --resume
  <exact-session-id>`, number the finite findings in the prompt, append-only
  correction sections in LOG/REPORT, keep status SUBMITTED, record the C1
  lineage in the tracking file.
- **Protected-data check = content hash, not git cleanliness:** a protected
  file (e.g. MAIN `channels.json`) may legitimately appear as `M` in
  `git status --short` — pre-existing dirty state from before the sprint. The
  durable check is the SHA-256 of content (`certutil -hashfile`), not git
  status. Escalate only when the HASH changes; same for MAIN DB (size + mtime
  with content-verification caveat).
- **Manager scope audit for a correction round:** use the correction run's
  mtime window (`find app tests migrations -newermt '<start>' ! -newermt
  '<end>' | grep -v __pycache__`) to enumerate exactly which files the round
  touched — a clean small window (repo + route + tests) is strong scope
  evidence for the tracking row.

## Never let a CLI worker delegate to a background sub-agent (verified 2026-08-05/16, S08-T01)

A PM-queued `hermes chat --query` worker that spawns Codex/claude via
`terminal(background=true)` and then ENDS ITS TURN will exit the CLI session,
and the session-scoped background child is KILLED with it — the task silently
does nothing (REPORT stays NOT_STARTED) while the log shows the worker
confidently saying it is waiting for the notification. Verified: S08-T01 first
run spent 14m24s producing only a temp prompt file; zero implementation.

Rules:
1. Worker prompts must say: use sub-agents ONLY in FOREGROUND (blocking, inside
   the tool call); never spawn a background coding child and end the turn.
2. Manager must verify the worker's claim of completion against the disk:
   `git status` count in the worktree + REPORT status. A 14-minute exit-0 run
   with NOT_STARTED report and unchanged tree = the failure mode above.
3. Recovery: resume the SAME task session with a short prompt naming the root
   cause and the foreground-only rule; never open a fresh session for the same
   Task ID.
4. Also verified: a deep basetemp (>260 chars) breaks the S05 production-wiring
   test with MAX_PATH `open('xb')` failures — S05 suites must always use
   shallow basetemps under `C:/Users/Admin/AppData/Local/Temp/<task>-*`.

## Sprint-exit CHANGES_REQUESTED (Codex rejects the whole sprint)

Distinct from a per-task PM review round: Codex may reject the SPRINT EXIT
with concrete engineering blockers (verified 2026-08-05 — S05 rejected for:
(1) UI called legacy `POST /api/projects/{id}/ingest` instead of the approved
durable pipeline T02→T03→T04; (2) retry was only "rendered honestly" as 500
IdempotencyKeyInUse instead of a real successor-job path). Response pattern:
1. Verify each blocker on disk FIRST (grep the UI call, read the endpoint) —
   confirm it is real before building a correction.
2. Create a bounded correction packet (e.g. `S05-C01-...`) with the SAME
   packet structure, but include the Codex blockers verbatim as Context, and
   add a Required-evidence list mirroring EVERY rejected criterion
   (one-submission-drives-chain, successor retry with owner validation +
   idempotency, CFR+VFR, SHA/size/containment, stable IDs, cancel-during-
   active, restart/resume no-dup, orphan cleanup, Playwright desktop + 390px,
   no mock). Reuse approved job classes/dispatchers — do NOT rewrite services.
3. Launch a FRESH worker for the correction (new session, same hard guard).
4. After SUBMITTED: append honest correction sections to the affected task
   reports (never rewrite history) and update SPRINT_EXIT_REPORT.md.
5. Stop after SUBMITTED — Codex performs the sprint-exit review again.

## Sprint-exit CHANGES_REQUESTED can be a FULL correction CYCLE (verified 2026-08-16, S08)

Codex may reject a sprint exit with a multi-task correction cycle (S08 got
7 work items A–G), not a single round. Execution shape:

1. NEWLY AUTHORIZED Task IDs (e.g. S08-R01/H01) → materialize their
   TASK/START_PROMPT/LOG/REPORT packets from the Codex prompt BEFORE launch;
   brand-new sessions; record exact new session IDs.
2. EXISTING Task IDs → resume their EXACT stored session IDs (append
   correction rounds; never fresh sessions; keep each session's original
   model).
3. **Order is derived from the Codex packet's dependency statements, NOT task
   numbers** — S08 ran R01 → T02 → T03 → T05 → T04 → H01 → T06 (T04 gallery
   resumed only after the T02/T03/T05 backend contracts were verified).
4. New protected-asset classes may appear (read-only SAM2.1 checkpoint):
   add them to the protected baseline; QA smokes must be read-only + isolated.
5. One writer at a time; independent read-only validations may run
   concurrently ONLY with distinct temp roots/DBs/ports/output dirs.
6. Reporting rules Codex enforces verbatim: append-only history; record every
   Task/session/round/command/result/root/port/Run ID; list untested items +
   why; never call a configured-but-nonfunctional provider "production ready";
   never call metadata tiles "thumbnail rendering"; never call role-seeded
   tests a vertical extraction proof.

A–G checklist: `references/s08-correction-cycle-2026-08-16.md`.
C3–C5 protocol: `references/s08-h02-c3c4c5-correction-protocol.md`.

## Round-2 full correction cycle (C2) — SAME task sessions re-resumed (verified 2026-08-17, S08-C2)

Codex can issue a SECOND, equally-large correction cycle AFTER the first one
was fully verified. S08-C2 was another 7 work items (T02-C2 → T01-C2 → T03-C2
→ T04-C2 → H02 → T05-C2 → T06-C2) with wholly DIFFERENT finding content
(backend source authority, current-generation listing, origin/upload/media
security, E2E repair). This is a genuine EXTENSION of the single-round
pattern — do not mistake it for the S05 "CHANGES_REQUESTED round" shape:

- **Existing Task IDs resume the SAME stored sessions AGAIN** — the very same
  session C1 resumed (S08-T02-C2 resumed `20260816_140218_d4c20a` again; the
  session now carries C1 + C2 correction-history appended). This DIFFERS from
  the S05 pattern where each round gets a fresh session (see "Correction
  rounds CHAIN"). In the full-cycle sprint style, a per-task session is the
  durable Task ID handle and is reused across every round.
- **NEWLY authorized IDs each round** get a brand-new session + a materialized
  packet from THAT round's Codex prompt (C2 added S08-H02-local-api-origin-
  upload-safety: TASK.md/START_PROMPT.md/LOG stub/REPORT NOT_STARTED stub
  + `run-s08-h02-fresh.ps1`).
- **Order is re-derived from the C2 packet's dependency statements**, not C1's
  order and not task numbers. C2 ran T02 → T01 → T03 → T04 → H02 → T05 → T06
  (source-authority first, security mid-chain, E2E repair after, golden last).
- **Acceptance criteria go VERBATIM into the resume prompt** — a C2 packet
  enumerates per-task acceptance bullets (e.g. T02-C2: server resolves current
  source/SHA/generation from durable state, client hints are assertions that
  fail closed 409/422, media integrity pre-inference, deterministic rejected
  outside QA). Do not paraphrase; the worker's scope = the bullets.
- **Prep the next round's launchers while task 1 of the current round runs:**
  materialize H02's packet + write/PS-parse its launcher and the following
  resumes (T01-C2…) during T02-C2's runtime, so gate→launch stays same-turn.
  Quote-scan EVERY launcher (see PRE-LAUNCH QUOTE SCAN) — each C2 launcher is
  new text and can hide a stray `"`.
- **Watch for the same truncated-session-id trap in the C2 packet:** Codex's
  own list may restate the OLD truncated id (S08-T06-C2 listed
  `20260816_203312_e9f2b`, missing the real trailing `8`). Always verify via
  `hermes sessions list` before building the T06-C2 launcher — never trust the
  packet's id verbatim.
- Protected-data baseline items may GROW with fields (C2 added the SAM2.1
  checkpoint SHA-256 next to its byte size) — record the full tuple in the
  tracking file each round; verify every field at each gate.

## Round C3+ — current brief overrides session policy (2026-08-19, S08-H02-C3)

Codex can issue FURTHER CHANGES_REQUESTED rounds after C1/C2; EACH prompt is
the source of truth for session policy and can REVERSE the same-session default
(H02-C3: "Do not resume the old session. Use a new run/session ID"). Rules:
session policy from the CURRENT brief, never assumed (NEW session =
`--query` without `--resume`); record run timestamps (local +07:00 / UTC Z /
elapsed_seconds) when brief demands; manager heartbeat ≤5 min with IMMEDIATE
user-facing final message on writer exit (exit code, finish time, duration,
test result, report path) — NOT COMPLETE until `FINAL_REPORTED_TO_USER=true`;
forced-stop doc pitfall: worker killed mid "Let me append to REPORT.md" leaves
LOG claiming an append that never landed — verify REPORT independently, repair
both docs and the code gap. New C3 security finding classes + full manager
recipe: `references/s08-h02-c3-probe-preset-collision.md`.

## Local-API security hardening (H02 checklist, verified 2026-08-18)

A security finding round for the local API produced a repeatable, non-obvious checklist. When Codex rejects on origin/upload/media safety, bake these in:

1. **No wildcard CORS** — configurable allowlist for the real frontend origins (`app/config.py`); do NOT enable `credentials` unless the product actually uses cookie credentials.
2. **Origin-aware enforcement:** a state-changing request carrying an untrusted `Origin` or `Origin:null` → **403 BEFORE any side effect**; trusted configured origins work normally; CLI/native requests with NO Origin follow the local-app contract; `OPTIONS`/untrusted never receives a valid `ACAO`.
3. **Uploads stream with a hard byte limit** (video/replacement) — never buffer unbounded.
4. **Validate project/object identifiers BEFORE every filesystem join** and enforce managed-root containment. Test vector note (verified 2026-08-18): `httpx`/`TestClient` normalizes a literal `../` on the client side, so the endpoint test must use an identifier that survives client normalization (e.g. `a..b`) while the raw `../`/`..\` vectors are covered in the unit-level `validate_path_identifier` / `_assert_contained` tests — do not conclude the protection is missing just because an integration test with `../` is normalized away.
5. **Media/image type validated by CONTENT probe**, not filename/MIME.
6. **Temp staging cleaned up on error; atomic publish only after validation.**
6b. **Metadata-update rollback AFTER publish (verified 2026-08-18, S08-H02-C1):** a publish+metadata route has TWO atomicity requirements, and a rollback test for one upload path does NOT cover the other. `upload_replacement` already rolled back on `update_object` failure, but `upload_video` published `source_<uuid>.mp4` via `staging.replace(...)` then called `pwf.set_video(...)` AFTER the try/finally — a metadata write failure left the just-published file on disk as an orphan and did not restore the previous source/state. Audit EVERY publish+metadata endpoint's control flow (success-path side effects after the atomic publish, try/finally extent) and wrap the metadata call so a failure removes the just-published file and re-raises, preserving the prior source SELECTED + project.json byte-identical. Require a dedicated test (e.g. `test_video_metadata_update_failure_rolls_back_file_and_state`): inject the metadata failure after a successful publish → 500, new file removed, only previous file remains, project.json byte-identical, GET still 200, no staging/publish-temp orphan.
7. **Decoders bounded** — timeout + sane output/dimension/memory limits.
8. Required test set: trusted/untrusted origin, zero-side-effect (403 creates nothing), oversized upload, malformed media, traversal identifiers, cleanup-after-error. Boot smoke (real app): untrusted POST → 403, trusted GET → ACAO present with no credentials header.
- New protected baseline fields may GROW (SAM2.1 checkpoint gained a SHA-256 next to its byte size in the same round) — record the full tuple and verify every field each gate.

Pass shape (S08-H02): focused H02+test_api 47/47 + T01–T05 184/184 + R01 18/18 + S05 41/41 + S02 87/87, head `f6a7b8c9d0e1`, env unset. **H02-C2/C3/C4 security rounds (traversal, probe bounds, junction, collision, atomic O_EXCL, deadline-budget, deterministic concurrency) + NEW-session timestamped protocol + leaked-port catch**: `references/s08-h02-c2-c3-security-rounds.md`.

Full recovery detail — LOG/REPORT divergence after a force-stop, per-path
metadata-rollback scope (video-source vs replacement-image), and the
client-string→filename containment class (preset save/apply, S08-H02-C2):
`references/s08-forced-stop-recovery-and-rollback-scope.md`.

## E2E repair & project isolation (T05-C2 checklist, verified 2026-08-18)

E2E corrections are a distinct finding class from backend ones: the failure is that a spec no longer matches the CURRENT UI or that projects/evidence bleed together. Repeatable checklist:

1. **Selector must match the current UI** — e.g. expand the card BEFORE looking for correction actions (`RoleSummaryCard` expand control driven by button name/aria, not a stale deep-link). Reuse an existing helper (grep `export.*function expandRole` across `e2e/*` before writing a new one).
2. **Do NOT change product copy just to make old tests green** — unless that copy is an approved contract. Use **semantic role/state assertions** instead of brittle copy assertions when copy is not the contract.
3. **Project-level test isolation:** fix `testMatch` per project so the mobile project only picks that task's mobile specs — project-level `testIgnore`/`testMatch` REPLACES (not merges) top-level values, so stale visual/other-task specs silently re-enable. Verify with `npx playwright test --config playwright.<task>.config.ts --list` — it must contain ONLY this task's specs (no H01/T04 bleed).
4. **Evidence isolation:** screenshots/results go under a NEW Run ID (`output/s08-sprint/<new-run-id>/`); never hardcode a path into the OLD run dir (re-running the full suite would clobber prior evidence).
5. Run the FULL desktop + 390px suite, not just a manual happy path; reproduce and prove the specific failed tests fixed (name the failing spec before/after).
6. Keep semantic assertions + all prior guarantees (generation isolation, media canonical, retry/successor, no-orphan).

## Production provider + secure media-content corrections (verified 2026-08-17, S08-T02-C1/T03-C1)

When Codex demands a REAL production provider and a media content API (finding
B class), bake in this checklist — it is now the proven pass shape (T02-C1
cleared all 10 sub-items in one round):

1. **Client-supplied provider MUST be rejected (422)** at the route — provider
   choice is server/runtime policy (`MOTIONFORGE_EXTRACTION_PROVIDER`); the
   QA-only deterministic adapter can never be selected through request JSON.
2. **`available()` = real capability probe**, never a non-empty env string:
   import the model package, verify the locator/checkpoint path exists.
3. **Inference only inside the durable worker**; fail closed (stable error
   code, zero job rows) when import/config/checkpoint is absent; no download,
   no network fallback. Keep the interface pluggable; no version hardwire.
4. **Read-only GPU smoke as a separate gate:** repository-owned fixture +
   fresh temp root + read-only checkpoint (S08-T02-C1 measured: load 2.09s,
   inference 0.80s/2 frames, peak CUDA 1454 MB on RTX 5070, 2 non-empty masks;
   smoke test ran in 7.5s). Report perf/memory honestly; never touch MAIN.
5. **Image content endpoint checklist:** resolve ONLY through ManagedRoot
   (client never supplies a filesystem path); allowlisted image MIME;
   recorded size/hash verified against the LIVE file; `ETag` = artifact
   SHA-256 with 304 on If-None-Match; `X-Content-Type-Options: nosniff`;
   404 for missing/stale, 409 for non-ready artifacts.
6. **Durable role↔artifact association table** (stable IDs, purpose,
   generation, source job) via a FORWARD migration + round-trip/upgrade tests;
   preserve existing artifact rows. This becomes the media-authority surface
   the later correction rounds (T05-C1 canonical media) build on.
7. **Backend-authoritative current lookup** (`/extraction/current?video_item_id=
   &source_generation=`) + source-generation filters on list endpoints —
   browser storage must not be required; historical rows stay auditable but
   never mix with the current gallery/grouping run.
8. **Grouping policy metadata endpoint** (finding C): GET `/policy` exposes
   algorithm version, confidence semantics, review threshold, calibration
   version — the UI consumes backend policy instead of hardcoded 0.65/0.5.
9. **Stable identity in every suggestion/operation** — display name is never
   authority (duplicate-name + renamed-role + cross-generation + adversarial
   grouping tests are the required evidence set).

Manager verification recipe that cleared these rounds (independent re-runs):
focused (service+api+provider) incl. 2 REAL-model tests, the GPU smoke on its
own, T01+T03 combined, S05 41-suite shallow, S02 durable regressions,
migration round-trip in a subshell to the NEW head, plus code audit of items
1–9. S08-T02-C1 numbers: 45/45 + 1/1 GPU + 61/61 + 41/41 + 119/119, head
`f5a6b7c8d9e0`; T03-C1 (policy only, no schema): 34/34 + 80/80 + 160/160 +
41/41; T05-C1 (finding D, canonical correction media): 45/45 focused +
116/116 T01–T04 combined + 18/18 R01 + 41/41 S05 + 87/87 S02, head
`f6a7b8c9d0e1` (media supersession: `superseded_by_id` self-FK, replacement
association rows supersede old ones which stay auditable, gallery resolves
newest-valid). Full prompt skeleton + validation lists + measured numbers:
`references/s08-t02c1-t03c1-correction-recipes.md`.

## Backend source authority + provider gate (T02-C2 checklist, verified 2026-08-17)

A SECOND correction round on the same extraction code produced a distinct,
repeatable finding class: the API must not trust client-supplied identity.
Bake this checklist into any submit endpoint that takes generation/SHA hints:

1. **Server resolves current source artifact + SHA + generation itself** from
   durable backend state — client hints are NEVER authority.
2. If client hints are kept for compatibility, they are ASSERTIONS: mismatch
   fails closed 409/422 and creates NO Job.
3. **Never default `generation="1"`** when the backend current generation
   differs.
4. Manifest and idempotency key use backend-authoritative values only.
5. **Pre-inference media integrity check:** verify the selected managed media
   file still matches its Artifact row — ManagedRoot path containment, size,
   SHA-256. Byte-tampered media after submit fails BEFORE inference and
   publishes NO output (service-level AND API-level tests).
6. **QA providers gated by runtime mode:** deterministic /
   deterministic-identity resolve ONLY when runtime is genuinely QA/test with
   isolated roots; non-QA is `PROVIDER_UNAVAILABLE` (no Job/output) even when
   env or an internal caller selects it.
7. Required test set: spoof generation, omitted SHA, replaced source, media
   tamper, production deterministic rejection (no Job), QA deterministic
   success. Seed fixtures must now write REAL managed media payloads (the
   media gate validates actual files, so fake payloads fail).

Pass shape: focused 56/56 + T01–T05 combined 174/174 (incl. real SAM2
provider) + R01 18/18 + S05 41/41 + S02 87/87, migration head unchanged
(`f6a7b8c9d0e1`, code-only round), env unset. Test suites that seed media
payloads may need updates across sibling task suites (e.g.
`test_object_correction.py`) — that is a legitimate cross-suite consequence of
the media gate, disclose it in REPORT, don't hide it.

## Current-generation isolation (T01-C2/T03-C2/T04-C2 checklist, verified 2026-08-18)

When Codex rejects a round because stale-generation data leaks into current
views, the finding class is *current-generation isolation* and recurs across
role listing (T01-C2), grouping suggestions (T03-C2), and the gallery (T04-C2).
Repeatable checklist:

1. **Public list endpoints default to the current source generation only** —
   roles, suggestions, gallery all filter by the backend-authoritative current
   generation (from T02-C2's server-resolved source). Generation-1 rows must
   never appear when the source advanced to generation 2.
2. **Stale-target mutations fail closed, ZERO mutation** — apply/dismiss/merge/
   confirm/correct on a stale-role or stale-suggestion operation returns 4xx
   and creates no row (adversarial test per stale dimension).
3. **Historical inspection is an explicit SEPARATE contract** — add a
   generation-scoped / historical endpoint deliberately; do not mix history
   into the current list by accident. Current-only must be the DEFAULT.
4. **Frontend**: API passes/verifies current generation; **React Query keys
   carry videoItemId + generation** so switching source/generation does not
   reuse the stale cache; invalidate old keys on source change; do NOT render
   action controls for stale roles/suggestions.
5. Preserve prior-round guarantees while filtering (stable role IDs, policy
   metadata, read-only GET, no auto-confirm).

Cross-suite consequence: seeded fixtures across sibling task suites often carry
generation labels that must be normalized to the backend's canonical values
(e.g. `"gen-1"/"gen-2"` → `"1"/"2"`) and real source_sha256 on seeded source
jobs — disclose these as fixture alignments (no assertion weakened), never hide
them. Pass shape observed: T01-C2 45/45 focused + 183/183 combined; T03-C2
39/39 + 186/186; both keep head `f6a7b8c9d0e1` (code-only). Add the sibling
suite run (T01–T05 combined incl. real SAM2 provider) to every gate — a
current-generation filter in one task changes what downstream suites observe.

## RO-1 readiness report — read-only recon before opening the next task (verified 2026-08-17, S08)

Between correction rounds the manager may spawn a READ-ONLY helper whose ONLY
deliverable is a readiness report for the next task in the dependency
sequence. Contract: ZERO writes (no files, no test/build/lint/server, no
git-write, no sqlite), tools limited to read_file + search_files + read-only
terminal (`ls`/`stat`/`pwd`), single report in chat, then STOP (no
background, no polling). It must NOT recommend opening the next task while
the current writer is alive — readiness only, gated by the manager.

Procedure:
1. Read the enumerated docs in the given order; when a listed doc is absent
   in the worktree, check the MAIN tree before declaring it missing —
   `docs/pm/CODEX_PM_HANDOFF.md` lives ONLY under
   `C:\Users\Admin\MotionForge2D\docs\pm\`, not in sprint worktrees.
2. VERIFY parent-prompt assumptions against the filesystem. Example: prompts
   that say "architecture contracts listed in Required reading of TASK.md"
   may be FALSE — the S08 TASK.md packets have NO Required reading section
   (only S08-P00 does; grep `TASK.md` files for `Required reading`). Report
   the gap as a contract ambiguity; the resume prompt must supply the reading
   list explicitly.
3. Confirm the resume identity from the tracking file + REPORT/LOG: same Task
   ID correction = exact stored session ID (e.g. `20260816_151439_21e306`),
   never a fresh session; also re-confirm worktree/branch/HEAD.
4. Build the binary acceptance checklist from TASK.md required behavior +
   the task's own REPORT deviations (they are the probable finding targets),
   and CLEARLY mark which items depend on the manager-supplied finding list.
   Correction finding sub-items (e.g. "finding C") are often recorded NOWHERE
   in the repo — only in the manager's prompt. Missing findings list in the
   resume prompt = BLOCK condition, not a guess-able default.
5. Serialization analysis — the recurring high-risk items:
   - **Migration-chain adjacency**: consecutive tasks own consecutive
     revisions (T02 `f2a3b4c5d6e7` ↔ T03 `f3a4b5c6d7e8`); if the running
     correction adds a revision, the next task's migration parent and every
     head-string test expectation shift. Highest conflict risk — manager must
     record the new head before opening the next task.
   - **Head-expectation test files are multi-task touch points**:
     `test_persistence_bootstrap.py`, `test_durable_job_persistence.py`,
     `test_object_intelligence_domain.py` (+ task domain suites) get updated
     by EVERY task that adds a migration.
   - Shared `app/persistence/models.py`, `app/api/app.py` include_router
     block, and API namespace prefixes (`/api/v2/object-intelligence/...`).
   - Engine changes from a prior correction (e.g. S08-R01 touched
     config/job_service/durable_worker/job_reconciler/deps) mean every
     subsequent writer runs on the NEW engine — validation batteries must add
     the R01/new suites, not just the pre-R01 list.
   - Semantic coupling: a task's consumers (T03 grouping consumes T02
     roles/occurrences; T05 invalidation consumes T03 suggestions) must
     re-validate after the producer's correction — serialize and note it.
6. Never read the running writer's live artifacts (`output/<task>-c*-hermes.log`)
   or mid-write LOG.md appends; a packet listed as "stable approved" can be
   appended by the active writer — lean on REPORT.md for stable content.
   PM_REVIEW.md may be deliberately EXCLUDED from an allowed read list even
   though it sits in the packet dir — honor the enumerated list literally.

Report format (Vietnamese, single reply):
```
RO-1 READINESS REPORT
- Next Task ID:
- Required dependencies:
- Binary acceptance checklist:
- Likely scope conflicts:
- Contract ambiguities:
- Stop/block conditions:
- Recommendation: READY_AFTER_CURRENT_GATE hoặc BLOCKED (kèm lý do)
```
Required dependencies must include: current writer EXITED + manager gate
recorded `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` with stable evidence, new
migration head recorded, findings list verbatim in the resume prompt, pinned
exact write-scope file list, protected-data baseline re-verified, clean env
(no leaked `MOTIONFORGE_DATABASE_URL`). Worked example with the actual S08
findings: `references/s08-t03-readiness-report-2026-08-17.md`.

**Auditing a generic-engine fix (verified 2026-08-16, S08-R01):** when Codex
demands a fix at the GENERIC lifecycle level ("not only S08 handlers"), the
manager code-audit must confirm the fix lives in the shared engine (e.g. a
`drain` flag on the claim path in `durable_worker.py`, applied to every job
type), NOT per-handler patches in S08 services. Two more audit signals:
(1) allowed-scope files that were NOT touched (`app/lifecycle.py`,
`app/api/app.py`) are strong preservation evidence — verify with the
mtime-window find; (2) the manager rerun recipe for lifecycle work is
focused-new-tests + durable regressions (worker/reconciler/api/persistence)
+ pristine wiring suites (S05 production-wiring/lifecycle), all with
isolated basetemps — 18/18 + 121/121 + 4/4 was the S08-R01 pass shape.

Scope audit via mtime (verified 2026-08-05): when a UI/frontend task shows
backend files (e.g. `app/workflow/*`, `app/services/*`) as modified, do NOT
assume a scope breach — check the file mtime against the worker's start time.
Pre-existing changes from earlier tasks legitimately stay modified; a breach
is only when a forbidden file's mtime falls INSIDE the current task's run
window. `frontend/.env.local` API-URL edits are acceptable dev config, not
scope violations. **Frontend-only task = empty backend window (verified
2026-08-17, S08-T04-C1):** for a UI/gallery task, `find app tests migrations
-newermt '<start>' ! -newermt '<end>'` returning ZERO files IS the clean-scope
proof; pair it with `git status --short | grep frontend` to confirm the deltas
are all frontend/src + e2e specs. Report the empty-window result explicitly in
the tracking row — it is stronger evidence than a prose "no backend changes"
claim.

## Full-sprint manager startup (verified 2026-08-05, S08)

Ordered manager-side checklist before launching T01 (full evidence in
`references/s08-sprint-manager-startup.md`; per-task session lineage,
Codex-finding→fix mapping and the repeatable verification recipe in
`references/s08-sprint-progress-notes.md`):

1. Read MAIN `docs/pm/SESSION_PROTOCOL.md` + `docs/pm/CODEX_PM_HANDOFF.md`
   (MAIN copies, per sprint prompt), worktree sprint contract, P00/prior
   PM_REVIEW, EVERY task packet TASK.md + START_PROMPT.md.
2. PRD/Master Plan epic IDs (e.g. E05/WS-04/G3) live in **MAIN** docs
   (`docs/pm/ROADMAP.md`, `docs/MASTER_PLAN_V1.md`), NOT the worktree — grep
   MAIN. `search_files` returned 0 matches for `E05|WS-04` on files that
   contain them; terminal `grep -rn` found them immediately. NEVER conclude
   "section not found" from search_files alone — confirm with grep.
3. Worktree guard + protected baseline snapshot: channels.json SHA
   (`certutil -hashfile`), MAIN DB size/mtime, MAIN + INTEG `git status
   --short` counts. Reconcile count deltas against known new files (S08:
   93→100 = 93 + 6 P00 packet files + 1 sprint contract) before flagging drift.
4. Competing-writer check self-match: `CommandLine -match 'hermes chat'`
   matched the check command's OWN bash wrapper (4 phantom "writers", all
   self). Inspect full CommandLine + ParentProcessId before concluding a
   writer is live.
5. **Resume-id match returns 2 processes = ONE writer (verified 2026-08-17,
   S08-T05-C1):** `CommandLine -match '<session_id>'` legitimately matches
   BOTH `hermes.exe` (the writer) AND its child `python.exe` (the Hermes
   runtime the CLI spawns), ParentProcessId of the python child == the
   hermes PID. Do NOT declare two writers from a bare count of 2 — filter by
   `Name -match 'hermes'` (or check parent/child relationship) before
   raising a single-writer violation. The phantom-writer failure mode is
   self-match of the check's own bash wrapper; the child-runtime match is
   the false-positive on the other side.
5. Model smoke test with the EXACT model id the run will use (never
   `/v1/models` alone).
6. Create `output/SPRINT_S0x_SESSIONS_TRACKING.md` in the worktree BEFORE
   launching T01 (rows per task + protected baseline).
7. Launcher per task from `templates/run-hermes-task-fresh.ps1`: prompt
   WITHOUT double quotes, all contract in packet files, `--max-turns 300
   --provider custom --model <id> --pass-session-id --checkpoints`; PowerShell
   Parser syntax check; launch background + notify_on_complete.
8. Watcher per task: copy live-log-watcher.sh to MAIN `scripts/watch-<task>.sh`
   (SRC=worktree output log, DST=MAIN output/hermes-task-logs/); `bash -n`;
   launch long-lived silent; `focus_pane('files')` + `open_preview(<task>-LIVE.txt)`.
9. 30s after launch: MAIN status count MUST be unchanged (misplaced-write
   tripwire) + log mtime growing.

**Manager NEVER runs pytest while a writer is active on the same worktree** —
it races the worker's own test runs on mid-edit state and produces garbage
evidence; the single-writer handshake makes the manager read-only until the
writer exits. Verification of orchestration tooling (.ps1/.sh) = PowerShell
Parser + `bash -n` + functional proof (process alive, log growing, LIVE.txt
synced), NOT pytest. When an automated gate demands pytest for files that
are not Python (launchers/watchers), the correct response is: run the
correct verification above, cite CODEX_PM_HANDOFF ("Script `.ps1`/`.sh`
không phải module Python nên không chạy trực tiếp bằng pytest"), state the
single-writer blocker with live evidence (worker pid/uptime, log mtime), and
defer pytest to manager review after writer exit — do NOT race the writer.

## Sprint exit protocol (after last queued task passes manager gate)

After the final task (e.g. S05-T06) passes the manager gate:
1. **Stop ALL writers** — no new worker may launch; confirm no `hermes chat`
   process remains alive (killing a worker mid-run with `exit -15` is NOT
   completion).
2. Run ONE fresh `scripts/quality-baseline.ps1` on the final state — record
   the Run ID (7/7 required).
3. Write `SPRINT_EXIT_REPORT` — task-by-task summary, per-task session IDs
   from the tracking file, final baseline Run ID, incident notes, decisions
   still pending for Codex. Full required-section checklist + golden-contract
   recipe + what the S08 manager itself re-ran at exit:
   `references/s08-sprint-exit-report-template.md`.
4. **Ask the USER to call Codex review** — never self-approve, never mark the
   sprint done in your own voice. Give the user the exact one-liner to send
   Codex (pointing at the tracking file + exit report).
5. Update `docs/pm/ROADMAP.md` status cells (SUBMITTED tasks) and the
   `output/SPRINT_S0x_SESSIONS_TRACKING.md` rows with final session IDs.

## Adversarial verification (Codex CHANGES_REQUESTED round 2, verified 2026-08-05)

Codex rejects pipelines whose tests call helper/read endpoints that secretly
advance state ("Do not approve a pipeline merely because tests call
helper/read endpoints that secretly advance it. Read-only endpoints must not
mutate state."). Manager verification MUST be adversarial:

- **GET/read endpoints must cause ZERO database mutations** — repeated/
  concurrent GETs must not create job/artifact/scene rows. Write a test that
  calls GET N times and asserts no rows appeared.
- **One POST → whole durable chain progresses under worker/reconciler
  ownership**: browser closes immediately, no GET polling, API process
  restarts between steps — chain still completes. Test POST-once-no-GET and
  API-restart-after-import / after-proxy variants.
- **Chain progression lives in a focused durable orchestration service**, NOT
  in the route. Routes stay thin; never access JobService private members
  (`job_svc._...`) from routes.
- **Chain identity = immutable input evidence**: source SHA-256 + generation/
  version. Replacing the project source must NOT silently reuse the stale
  chain (same project, new video → new chain).
- **Concurrent advancement creates exactly one successor per step**
  (lease/fencing); failure/cancel successor retry stays idempotent.
- Never approve because "the worker said tests passed" — re-run independently
  and check the acceptance OUTCOME, not just green tests.

## Codex adversarial findings on domain-API tasks (verified 2026-08-16, S08-T01)

Codex's CHANGES_REQUESTED on the ObjectRole/ObjectOccurrence domain API named
5 findings that are a PREDICTIVE CHECKLIST for any mutation API in this class
— bake them in from the FIRST task so later tasks (merge/split/confirm, T03;
targeted correction, T05) never repeat the round:

1. **Route ownership fail-closed:** a nested PATCH like
   `/roles/{role_id}/occurrences/{occurrence_id}` must bind role_id, not
   discard it — a role-A URL can never read/update a role-B occurrence.
   Test: role-A URL vs role-B row (read AND update) → 404/409.
2. **Supersession/relationship target validation across ALL ownership
   dimensions:** before assigning a cross-reference (supersedes_role_id),
   validate the target exists AND matches workspace + project + video +
   source generation; reject self-reference and terminal targets. Codex
   reproduced cross-workspace supersession succeeding. Test each dimension
   separately (6 tests: cross-workspace/project/video/generation, self,
   terminal).
3. **Real atomic CAS, not read-compare-write:** UPDATE constrained by
   id + workspace + expected revision, `scalar_one()`/exactly-one-row; on
   NoResultFound read the CURRENT revision and raise the domain conflict.
   Plus a GENUINELY concurrent two-session/two-thread test with
   synchronization (both writers start from the same revision; exactly one
   wins). Sequential stale-revision tests are NOT sufficient.
4. **Idempotency collision semantics:** replaying a reused idempotency /
   natural key requires an EQUIVALENT canonical request; different
   project/video/generation or materially different payload must fail with a
   stable conflict — never return another resource as a "successful replay".
   Tests at repository AND API level.
5. **Preserve-all clause** on every correction round; no skips/ignores,
   no weakened constraints.

## CHANGES_REQUESTED round (PM review)
- Read `PM_REVIEW.md` fully; fix ONLY the listed items, in the same session.
- Append a `CORRECTION (PM review round N)` entry to LOG.md with the new validation results.
- Update REPORT.md evidence honestly; KEEP status `SUBMITTED` for re-review.
- Re-run the FULL required validation sequence (not just the changed tests).

## Correction rounds CHAIN (verified 2026-08-05: S05-C01 → S05-C02)

A CHANGES_REQUESTED round can itself be rejected with NEW blockers — plan for
2+ correction rounds, never assume one round closes the sprint:

1. Each round gets its OWN bounded correction packet (`S0X-C0N+1-<name>/`)
   AND its OWN fresh worker session (never resume the rejected round's
   session; the rejected session stays as review evidence in tracking).
2. Quote the PREVIOUS round's Codex blockers verbatim in the new packet's
   Context, then add the NEW blockers on top — the packet is the round's
   contract, and drift between rounds is the #1 reviewer complaint.
3. After each SUBMITTED round, append to the SAME tracking/ROADMAP files
   (new row per round: `S05-C01 SUBMITTED (CHANGES_REQUESTED → S05-C02)`),
   so the review trail shows the chain, not just the latest state.
4. **Worker `write_file` can SILENTLY CLOBBER REPORT.md history (verified
   2026-08-18, S08-T03-C2):** a worker that edits REPORT.md via `write_file`
   (whole-file overwrite) instead of `patch`/append can erase the earlier
   round's entries (the C2 worker overwrote REPORT, losing the C1 + C1-PASS-2
   sections; it restored them from the session transcript and disclosed it).
   Manager gate MUST verify multi-round REPORT integrity independently:
   `grep -cE '^#+ (CORRECTION|Outcome|Manager)'` <REPORT> == expected section
   count AND each round's heading present (e.g. C1, C1 PASS 2, C2) — a missing
   section heading is a silent history wipe even when Status=SUBMITTED.
   **Use `^#+ ` not `^## ` (verified 2026-08-18, S08-H02-C1):** this repo's
   reports author round sections at H1 (`# CORRECTION C1`, `# CORRECTION C2`),
   so a `^## `-anchored grep returns 0 and falsely reads a PRESENT section as
   MISSING — a false alarm that wastes a full manager re-check. Anchor on
   `^#+ ` (or grep the exact heading line) and confirm the missing-section
   suspicion with `grep -n '<heading text>'` before declaring loss.
   LOG.md must stay append-only; if the worker's LOG shows deletion/rewrite
   markers rather than appends, flag it. Worker prompts should say: append via
   `patch` on the current tail, never `write_file` over REPORT.md.
4. When a correction legitimately changes behavior that old tests encoded
   (e.g. tests that called GET-to-advance the chain must now call the
   orchestrator's `advance_once()` because GET is read-only), update those
   tests AND disclose it explicitly in REPORT.md ("test X was updated
   because it encoded the anti-pattern Codex flagged; assertions unchanged").
   Hiding the test edit reads as cheating; disclosing it reads as honest.
5. Flag out-of-scope production gaps the worker found but must not fix (e.g.
   orchestrator `start()` not yet wired into app lifespan — outside write
   scope) as a prominent "Production note" in REPORT for the PM/Codex
   decision, instead of silently expanding scope.
6. Manager re-verifies every round independently (pytest counts per round
   recorded in tracking), and only the FINAL round's baseline Run ID goes
   into the sprint-exit evidence.

## Correction rounds deepen by layer (verified 2026-08-05: S05-C01 → C02 → C03 → C04)

Each CHANGES_REQUESTED round attacks a DEEPER architectural layer; expect the
chain C01 → C02 → C03 → C04 and design each round's packet to absorb the next:

- **C01 (wiring layer):** UI called a legacy endpoint instead of the approved
  durable chain; retry was only honest-error-rendering, not a successor job.
  Fix = approved-pipeline orchestration + real successor retry.
- **C02 (ownership layer):** the fix used GET (read) endpoints that secretly
  advanced the chain; progression lived in the route touching JobService
  private members. Fix = read-only GET (zero mutations on repeat/concurrent),
  focused durable orchestration service, thin routes, chain identity bound to
  source SHA-256 + generation (source replacement must NOT reuse stale chain).
- **C03 (lifecycle layer):** the orchestrator only started via POST
  `ensure_started()`; the C02 "Production note" (out-of-scope gap: `start()`
  not wired into app lifespan) became the NEXT blocker. Fix = wire start/stop
  into the real FastAPI app lifespan — startup scans and resumes incomplete
  chains WITHOUT POST/GET/polling/manual advance; prove with a TRUE
  process-lifecycle test: POST once → import completes → fully shut down the
  first TestClient/app lifespan → fresh app/TestClient over the SAME database
  → issue NO analyze API request → proxy and scene jobs materialize and
  complete; repeat the restart after proxy. Source replacement gets an
  explicit VideoItem/version/supersession identity: old jobs/artifacts/scenes
  stay immutable, new source gets distinct outputs, chain state exposes only
  the current source.
- **C04 (production-wiring layer — the root cause of C01–C03):** the real
  production default path (`app.main:app`) was NEVER exercised because every
  test injected `deps._job_service` / `deps._lifecycle_db`. Defects: default
  `JobService()` constructor binds its DurableWorker to a placeholder factory
  that raises `RuntimeError("job service not initialized")` and
  `initialize()` never rebinds it; the analyze orchestrator fell back to a
  COMPETING factory when `JobService.session_factory is None` and cached the
  orchestrator by object identity, so a pre-initialization call permanently
  kept the wrong factory; `app.py` inferred private attributes. Fix = one
  explicit public lifecycle binding contract; orchestrator receives factory +
  managed root ONLY from the initialized public JobService binding; fail-
  closed before init; NO private reads/patches; and a **pristine
  production-wiring test**: temp isolated root only, real `app.main:app`,
  real FastAPI lifespan, no DI, no monkeypatch, subprocess-fresh module state
  per generation (two TestClient contexts over the same singleton is NOT a
  restart proof), with explicit stage-boundary assertions (gen1 import done +
  proxy=0/scene=0; gen2 proxy=1 + scene=0; gen3 scene completes; gen4 zero
  duplicates). See
  `references/s05-correction-rounds-c01-c04.md` for the full chain with
  Codex's verbatim findings and the pristine-test recipe.

**Root cause of the multi-round loop (the meta-lesson):** DI-injected tests
hide production wiring defects. All green DI tests + a broken default path =
every round of adversarial review peels one fake-test layer and exposes a new
real defect. Prevent by including a pristine default-path test from the FIRST
task of any sprint, and before SUBMITTED run a default-path smoke so the
production wiring is proven, not just the injected path.

Patterns that recur across all three rounds (bake into the packet upfront):
- Every round keeps GET read-only and preserves the previous round's
  guarantees — the packet must say "preserve ALL C0N guarantees" explicitly.
- Independent tests per round must include the adversarial variants the
  reviewer names (restart-between-steps, no-polling, concurrent-GET,
  source-replacement, one-successor-per-step, idempotent retry).
- A worker that flags an out-of-scope production gap in REPORT (e.g. "wiring
  `start()` into app lifespan is outside write scope") is handing the
  reviewer the next round's blocker — either fix it in-scope or expect it
  back. Note it in the tracking row for the round.

## Manager E2E verification tooling (verified 2026-08-16, S08-T04/T05)

- **Appending to LOG.md via `cat >> LOG.md << 'EOF'` can be blocked** by the
  terminal foreground guard (heredoc falsely classified as starting a
  long-lived server). Append manager/correction sections with the `patch` tool
  (anchor on the file's current tail) instead — it works fine for .md appends.
- **Manager E2E must not overwrite worker evidence.** Visual specs hardcode
  their screenshot dir (a `SHOT_DIR` constant in the spec), so re-running the
  full suite clobbers the worker's screenshots. Re-run ONLY interaction specs
  with `--grep-invert visual --output=<fresh temp dir>`, and validate the
  worker's visual evidence by mtime instead: count TS/TSX files newer than the
  visual run (`find frontend -type f \( -name '*.tsx' -o -name '*.ts' \)
  -newermt '<visual-run-time>' ! -path '*/node_modules/*' ! -path '*/.next/*'`);
  0 files ⇒ the visuals still apply to the final tree. Take ONE manager
  screenshot (browser tool) into a fresh manager evidence dir for the record.
- **Kill a stale QA dev server only after verifying its identity:**
  `powershell Get-CimInstance Win32_Process -Filter 'ProcessId=<pid>' | Select
  CommandLine` — kill only when the CommandLine shows the SAME worktree's next
  server (worker exited but node child survives). Then start fresh
  backend+frontend and probe BOTH with curl → 200 before Playwright.
- **One-off alembic round-trips belong in a SUBSHELL** so the env var cannot
  leak into later pytest runs (see env-contamination section):
  `(export MOTIONFORGE_DATABASE_URL=sqlite:///C:/Users/Admin/AppData/Local/Temp/<x>.db && python -m alembic upgrade head && python -m alembic downgrade <rev> && python -m alembic upgrade head)`.
  Verify `alembic_version` + expected tables via sqlite3 in the same subshell.
- **Broad `find -newermt` over the frontend tree times out** (node_modules /
  .next). For scope audits use `git status --short` counts plus `stat -c '%y
  %n'` on the specific modified files; use the mtime-window `find` only on
  `app tests migrations` (backend scope), never on `frontend/` wholesale.

## Sprint-exit golden + T06 audit lessons (verified 2026-08-16, S08-T06)

- **Playwright project-level `testIgnore` REPLACES the top-level value.** A
  sprint-exit config that sets `testIgnore: /mobile\.spec\.ts/` at top level
  but nothing per-project silently RE-ENABLES old visual specs in the desktop
  project (project-level testIgnore replaces, not merges) — they re-ran and
  regenerated screenshots into the T04/T05 run dirs. Fix: set the exclusion in
  EVERY project (or `testMatch` per project), and verify the final test list
  with `npx playwright test --list` before the evidence run. If old
  screenshots were regenerated from unchanged specs + deterministic data, say
  so honestly in the sprint report (byte-identical originals not recoverable
  from untracked output/), don't hide it.
- **QA backend launcher must set env INLINE and `cd` into its run root.** Env
  vars do not reliably inherit through PowerShell background launches, and the
  JobService managed root is CWD-relative. A launcher that neither sets
  `MOTIONFORGE_ROOT/OUTPUT/MODELS` inline nor `cd`s into the run root will
  (a) bootstrap+migrate the MAIN DB (see MAIN-DB incident) or (b) write
  uploads/staging strays into the WORKTREE root. The proven launcher shape:
  export the three MOTIONFORGE_* vars + `MOTIONFORGE_EXTRACTION_PROVIDER` +
  `cd "$RUN_ROOT"` + `exec python -m uvicorn app.main:app --app-dir <worktree>
  --port <qa-port>`.
- **Accidental deletion of a TRACKED file: restore byte-exact with
  `git restore --worktree <path>`.** When cleaning QA strays, a `rm -rf` can
  take a tracked file with it (S08-T06 deleted the tracked
  `artifacts/milestone_1a/openapi.json`). `git restore --worktree` on that one
  path is remediation of your own accident, not a destructive git op — do it
  immediately, verify `git status` clean for the path, and record the incident
  in the sprint report honestly (a hidden restore reads as cheating).
- **Golden sprint-exit recipe (deterministic evidence):** write the golden
  contract (dataset case list + metric thresholds) to a JSON with a frozen
  `contract_sha256` BEFORE running anything; tests assert
  thresholds-as-recorded == measured (never tune after observing). Metric set
  that satisfies the S08 contract: grouping precision/recall, proposal
  false-merge rate, executed false-split rate, review/low-confidence rate,
  post-curation false-merge/split rates, recompute scope ratio,
  runtime-per-scenario, repeatability (exact vector equality). Emit
  `golden-metrics.json` under the run dir and reference it from the sprint
  report table.
- **Verify a claimed 7/7 baseline by reading `summary.json` directly**
  (`json.load` + print each gate's status + `run_id`), never by trusting a
  prose claim. Same for golden metrics: load the JSON, not the report text.
- **Sprint-exit regression recipe used for S08:** S08-focused suite (all task
  suites + golden), S01/S02/S03 persistence suites, S05 41-suite + S06
  90-suite (shallow basetemps), ruff app+tests, mypy app, frontend
  tsc/eslint/build, Playwright desktop+390px on a FRESH isolated root with
  NEW screenshots, fresh 7/7 baseline with NEW Run ID, protected-data
  comparison (channels.json SHA, MAIN DB size, MAIN/S05/S06 status counts vs
  P00 baseline).

## Pitfalls
- **Manager-lane sprint orchestration (S09 full run):** worker early-exit dominates — verify disk state first, resume EXACT owner with finding-list packet; verify tests yourself ×2. More: `references/manager-lane-sprint-orchestration.md` + `references/manager-war-stories-s09.md` (terminal-honesty: open FAIL_OPEN_QUESTION ⇒ BLOCKED never VERIFIED; freeze-hash = SHA-256 over `path\x00content`; PEP 562 mypy trap; determinism recipe).
- **Do not re-litigate the pytest-verification nag every turn (verified 2026-08-16, S08):** respond ONCE with correct verification for .ps1/.sh (PowerShell Parser / `bash -n` + functional proof), blocker evidence, and deferral; on identical repeat flags, state the blocker in one compact sentence and continue.
- **MSYS mangles `taskkill //PID` (verified 2026-08-16, S08-T04):** in git-bash, `taskkill //PID <id> //F` fails with `Invalid argument/option - '//PID'` (MSYS path conversion eats the slashes). Kill specific Windows processes with `powershell -NoProfile -Command "Stop-Process -Id <pid> -Force"` — find surviving child PIDs via `netstat -ano | grep LISTENING` on the port first.
- **Failures are data**: when the task is to MEASURE a baseline, gate failures are recorded, NOT fixed — fixing source is a scope violation.
- Non-zero runner exit code is EXPECTED when the baseline has failures; the deliverable is the complete report, not a green run.
- `$LASTEXITCODE` capture: don't pipe the runner through `tail` (exit code is lost).
- A test that fails only when run with its file, but passes alone → shared state / order dependency; fix the fixture scope, not the assertion.
- Never weaken assertions, add skip/xfail, or delete user data to make tests pass.
- Baseline "known state" (e.g. `141 passed, 6 skipped`) must be re-measured, not assumed — the task says so explicitly.
