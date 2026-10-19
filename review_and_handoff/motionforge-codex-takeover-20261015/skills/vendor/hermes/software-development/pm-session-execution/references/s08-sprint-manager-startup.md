# S08 Full-Sprint Manager Startup — verified evidence (2026-08-05)

Manager orchestration of Sprint S08 (Object Discovery and Curation) on
worktree `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
`codex/s08-integration`. All findings below are from real command output.

## 1. Document discovery — PRD/Master Plan epic IDs live in MAIN, not the worktree

The sprint prompt required reading "các phần E05, WS-04 và G3 trong
PRD/Master Plan".

- `search_files(pattern="E05|WS-04", path=<worktree>/docs)` → 0 matches.
- `search_files(pattern="E05|WS-04|WS04|G3", path=<worktree>/docs/PRODUCT_REQUIREMENTS_V2.md)` → 0.
- `search_files(pattern="E05|WS-04", path=<MAIN>/docs/pm/ROADMAP.md)` → 0 (!!).
- Terminal `grep -n "E05" docs/pm/ROADMAP.md` (MAIN) → found immediately
  (line 155: `## EPIC E05 - Object Intelligence`, Sprint S08 rows at 162-175).
- Terminal `grep -n "WS-04|G3" docs/MASTER_PLAN_V1.md` → line 840
  (`## WS-04 Object Intelligence`), line 1198 (`### G3 - Object-first reskin alpha`).

**Lesson:** never conclude "section not found" from search_files alone —
fall back to terminal `grep -rn` when the pattern is expected. Also: the
worktree's `docs/pm/ROADMAP.md` had the S08 rows but NO epic headers; the
authoritative epic/PRD sections were only in MAIN (`docs/pm/ROADMAP.md`,
`docs/MASTER_PLAN_V1.md`). For Sprint S08 the worktree copies of
SESSION_PROTOCOL.md / CODEX_PM_HANDOFF.md are present but the prompt points
at MAIN copies — read the MAIN ones.

## 2. Baseline reconciliation — 93 vs 100 dirty entries

P00 `MANAGER_STATE.md` recorded INTEG worktree `git status --short` count =
93. Fresh count at sprint start = 100. Not drift: 100 = 93 + 6 files of the
S08-P00 packet (TASK.md, PM_REVIEW.md, MANAGER_STATE.md, REPORT.md, LOG.md,
START_PROMPT.md) + 1 `docs/pm/sprints/S08-SPRINT_CONTRACT.md`. Always
account for known packet/contract additions before flagging unexpected
changes.

Protected baseline snapshot taken before T01 launch:
- MAIN `channels.json` SHA-256 (`certutil -hashfile channels.json SHA256`):
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`
- MAIN `data/motionforge.db`: 311296 bytes, mtime 2026-08-04 18:24
- MAIN `git status --short` count: 45
- INTEG worktree count: 100

## 3. Competing-writer check — self-match produces phantom writers

`powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object
{ $_.CommandLine -match 'hermes chat' } | Select-Object ProcessId,
ParentProcessId, CommandLine | Format-List"` returned **4 PIDs** that looked
like live writers. All 4 were the bash wrappers of the check command ITSELF
(the eval string contains the literal text `hermes chat`, so the wrapper
matches its own filter; PIDs 35216→34156 chain = parent/child of the grep).
Before concluding "competing writer exists": read the full CommandLine of
each hit and check ParentProcessId; a self-match has the filter text inside
its own command line.

## 4. Model smoke test — exact model id

`curl -s -X POST http://127.0.0.1:20128/v1/chat/completions -d
'{"model":"ocg/deepseek-v4-flash",...}'` → 200, content "OK". Use the EXACT
model id the launcher will use, never `/v1/models`.

## 5. Launcher + watcher tooling verification (NOT pytest)

Created per task:
- `output/run-s08-t01-fresh.ps1` (worktree) — copied from
  `templates/run-hermes-task-fresh.ps1`; prompt without double quotes; all
  contract detail in packet files; `--max-turns 300 --provider custom
  --model ocg/deepseek-v4-flash --pass-session-id --checkpoints`; Tee-Object
  append log.
- `scripts/watch-s08-t01.sh` (MAIN) — live-log-watcher pattern: SRC=worktree
  `output/s08-t01-hermes.log`, DST=MAIN `output/hermes-task-logs/`, 10s sync,
  UTF-16LE→UTF-8 tail into `<task>-LIVE.txt`.

Verification used: PowerShell `Parser::ParseFile` → "SYNTAX OK"; `bash -n` →
"WATCHER SYNTAX OK"; functional proof = worker process alive, log growing
(59KB→64KB between samples), LIVE.txt synced. pytest is the WRONG gate for
these files (they are orchestration tooling, not Python) and running it on
the worktree while the writer is active would race the writer's own test runs
on mid-edit state — single-writer handshake keeps the manager read-only until
the writer exits.

## 6. Post-launch tripwire

30s after launch: MAIN count stayed 45, INTEG count stayed 100, log mtime
fresh, tail showed tool-call lines (read_file / grep on conftest.py,
lifecycle.py). This is the misplaced-write detection baseline; any MAIN
change inside the run window = incident.
