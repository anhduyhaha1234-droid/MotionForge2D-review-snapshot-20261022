# Isolated-worktree full-sprint — exact recipe (S11-T02..T06, 2026-09-03)

19 tasks / 14 waves / 3 parallel groups (W6=4, W9=2, W12=2 workers), ~13.5h,
zero merge conflicts, final remote == local, every push non-force + verified.

## Manager preflight checklist (before wave 1)

1. `git rev-parse --abbrev-ref HEAD` == expected branch; `git rev-parse HEAD` ==
   activation SHA == `git ls-remote origin <branch>`; `git status --porcelain | wc -l` == 0.
2. Zero stray workers; port check: only the 9Router node process on 20128.
3. `env | grep -i MOTIONFORGE` → nothing (DB guard unset).
4. `python -m alembic heads` → exactly 1 head.
5. Parse binding plan: N unique IDs in order, wave sequence, parallel groups
   only at allowed waves (script: `re.findall(r"^### (W\d+) · (T\d{2}[A-Z0-9]+) ")`).
6. Protected-hash pins (S10 route/test, T01 engine/handler) match.
7. Create external evidence root
   `C:\Users\Admin\MotionForge2D-evidence\<sprint>\manager\{ledger,gates,exit}`.
8. Baseline manifest per task (see below) + OpenAPI zero-dup materialization.

## Per-wave dispatch

```bash
cd /c/Users/Admin/MotionForge2D-worktrees
TOKEN=<task>-<token>
git -C s11-integration branch codex/s11/$TOKEN <WAVE_BASE_SHA>
git -C s11-integration worktree add "C:/Users/Admin/MotionForge2D-worktrees/s11-$TOKEN" codex/s11/$TOKEN
git -C $TOKEN rev-parse HEAD   # must == WAVE_BASE
git -C $TOKEN status --porcelain | wc -l   # must be 0
```

Baseline manifest (before dispatch): for every allowed-exists + protected file
write `{sha256, bytes, lines, mtime}` to
`<evidence>/<TASK>/<token>/baseline_manifest.json`; note alembic head at
dispatch time; note which allowlist paths are NEW (absent before).

Dispatch (background, notify_on_complete, cwd = task worktree):
```bash
hermes chat -q "$(cat '<evidence>/<TASK>/<token>/prompt.md')" \
  -m <exact model> --provider custom -Q > '<evidence>/<TASK>/<token>/dispatch.log' 2>&1
```
Packet must carry the binding task block VERBATIM (all 8 fields: Outcome,
Depends-on, Write-set, Forbidden, Tests, Session rule, Acceptance, Trace) —
no summarization; plus WORKDIR GUARD, byte-safe write rules (patch-only on
existing files, whole-file only for NEW allowlist paths), model route, submit
protocol (commit allowlist + `docs/pm/sessions/<TASK>/**` on local task
branch, TASK_SUBMITTED, no push).

## Post-exit manager verification

```bash
git -C <wt> log --oneline -3
git -C <wt> diff --numstat <WAVE_BASE>   # zero deletions outside allowed changes
git -C <wt> status --porcelain | wc -l   # 0 (worker committed)
env -u MOTIONFORGE_DATABASE_URL python -m pytest <test files> \
  -p no:cacheprovider --basetemp=C:/Users/Admin/AppData/Local/Temp/<task>_mgr_r1 -q
ruff check --select F <files>
```
Then grep raw dispatch.log for forbidden write patterns (write_file / "w"
open on existing protected files) and verify scope grep (e.g. old enum names).

## Integration owner (INT01) — one persistent session

Create once with a charter; resume (`--resume <session_id>`) for every wave.
Each merge task instructs:
1. porcelain == 0 and `git ls-remote origin <branch>` == local HEAD (base).
2. serial wave: `git merge --ff-only <task-branch>`; parallel wave: ff first
   branch, then `git merge --no-ff --no-edit <sibling>` for each sibling.
3. any conflict → `git merge --abort`, evidence, BLOCKED_INTEGRATION_CONFLICT
   (never resolve manually).
4. Manager then runs the wave gate in a disposable detached verifier worktree
   (`git worktree add --detach ... <sha>`; remove after: `git worktree remove
   --force <name>`).
5. Only after gate green: `git push origin HEAD:refs/heads/<branch>` (no
   force) + `git ls-remote` must equal local HEAD — becomes next wave base.
6. Local-ahead: if ls-remote differs ONLY by INT01's own earlier push, Manager
   may explicitly authorize; foreign drift → BLOCKED_REMOTE_DRIFT.

## Defect cascade pattern (verified with T02A enum defect)

1. A verified task's contract values are wrong (QC_REASON_CODES names vs
   binding): verification missed it because tests were green against the
   wrong enum. Downstream detector workers hit the wall mid-run.
2. PAUSE parallel dependents immediately (process kill by session id) BEFORE
   they commit code against the wrong contract — resumed sessions keep context,
   so analysis already done is not lost.
3. ff the defective task branch to canonical HEAD (writer stopped, clean):
   `git -C <task-wt> merge --ff-only <canonical-sha>`.
4. Realize the defect cascades: OTHER verified tasks can also carry the wrong
   literal (fixtures/manifests/tests). Run the cumulative gate on the fixed
   integrated HEAD and route EVERY red owner an exact-owner bounded correction,
   in parallel when write-sets are disjoint.
5. After corrections merge+push, ff each paused dependent branch to the new
   canonical, then resume its exact session with a short context note
   ("enum fixed to <values>; branch now at <sha>; continue your task").
6. Fix the verification gap: enumerate constants byte-for-byte vs the binding
   plan during review, not just presence/tests.

## Exit gate (frozen bytes, zero writers)

- Cumulative fresh pytest of ALL sprint test files (one command).
- Impacted protected suites (e.g. S10 71/71, T01 64/64) fresh.
- Alembic: single head; real round-trip via
  `python -m alembic -x db_url=sqlite:///<tmp> upgrade head` →
  `downgrade <prev-rev>` → `upgrade head`; `PRAGMA foreign_key_check` == [];
  `PRAGMA integrity_check` == ok. NOTE: downgrade to the CURRENT head is a
  no-op — target the previous revision to prove a real round-trip.
- OpenAPI: materialize; zero duplicate operationIds; zero removed paths vs the
  pre-sprint baseline paths file (keep one from the first wave's evidence).
- Static: `ruff check --select F` all sprint+protected files; mypy on changed
  production files (route residual errors to exact owners — parallel when
  write-sets disjoint); `git diff --check`; collect-only for dup/lost audit.
- Frontend: `npx tsc --noEmit`, scoped `eslint`, `next build --webpack` (see
  junction pitfall), Playwright specs on task-owned ports/roots — verify no
  `frontend/test-results/.last-run.json` leak into canonical (mtime check vs
  activation time if present).
- Leak: tasklist ffmpeg/ffprobe survivors == 0; DB env unset; workers exited.
- Protected hash compare: LF-normalized pins; record deliberate hash changes
  (authorized EXTEND) separately from drift.
- Coordination docs (SESSION_REGISTRY + SPRINT_REPORT) authored by Manager,
  committed by INT01 as coordination-only bytes, one final push.

## Session-id recovery after kill

Killed `hermes chat -q` runs do not print `session_id` (no graceful exit).
Find them with `hermes sessions list --limit 15` (plain list; the
`--workspace` filter can return "No sessions found" for CLI runs). Match by
title prefix (`# S11-T03B — ...`) and dispatch-time window. Resume with
`--resume <exact-id>`. Verify the id belongs to the RIGHT task before resuming
— a mis-resumed session receives the wrong prompt (kill immediately if that
happens).

## Transient 502 on INT01/worker resumes

`API call failed after 3 retries: HTTP 502 ... connect timeout` inside a
resume log → per rules: state RUNNING_RETRY_WAIT, wait 5 minutes, resume the
SAME session with the same model/provider (no fallback, no new session).
Record the retry in evidence; usually succeeds on first retry.