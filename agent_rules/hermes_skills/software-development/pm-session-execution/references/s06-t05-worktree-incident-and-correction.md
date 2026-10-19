# S06-T05 Wrong-Worktree Incident & PM Correction Protocol (2026-08-05)

Verified end-to-end on MotionForge2D. This is the authoritative playbook for
the class "hermes worker wrote to the wrong repo" AND "PM issued a correction
round for a corrupted worktree".

## Timeline

1. `run-s06-t05-deepseek.ps1` had `Set-Location` into worktree
   `s06-t01-review`, but the `hermes chat` CLI session executed with cwd =
   MAIN repo (`C:\Users\Admin\MotionForge2D`) because the Hermes desktop
   daemon's cwd won. Agent wrote backend/frontend/tests/LOG/REPORT into MAIN.
   Evidence: worktree `REPORT.md` stayed IN_PROGRESS (mtime 12:23) while MAIN
   got SUBMITTED at 00:18; agent log shows `ls -d /c/Users/Admin/MotionForge2D/...`.
2. First "fix" (WRONG): manager copied the 12 changed files + fixtures from
   MAIN → worktree, after backing up worktree originals to
   `output/backup-pre-copy/`. `diff -q` showed 0 differences, pytest passed.
   Looked fine — but it was NOT fine.
3. PM correction arrived: "The current review worktree was corrupted by
   copying older main-tree character files. output/backup-pre-copy contains
   the pre-incident approved S06/R02 state." The MAIN-tree files were
   OLDER/weaker than the approved worktree state — the copied versions
   replaced approved R02 routes with nested publish/image endpoints and
   dropped the approved content/validation endpoints. The "0 differences"
   check only proved MAIN == worktree, not worktree == approved state.

## Why "copy from MAIN to fix placement" is wrong

- MAIN is often NOT newer than the worktree. S06/T05 worktrees carry approved
  R02 state that MAIN never had.
- `diff -q` between the two repos proves sync, NOT correctness.
- A task that ran in MAIN may also have quarantined/removed approved code,
  or added tests against its own wrong endpoints (`test_pack_publish_ux.py`
  tested the forbidden nested endpoints — a corruption artifact).

## PM correction protocol (what the worker must do, verbatim shape)

1. Verify `pwd` + `git rev-parse --show-toplevel` == expected worktree root.
   If not → `BLOCKED: WRONG_WORKTREE`, write nothing, exit.
2. Read: SESSION_PROTOCOL, prior TASK/REPORT/PM_REVIEW, R02 contracts, the
   incident report.
3. Compare every current file against `output/backup-pre-copy/`.
4. Restore EXACTLY the overwritten approved files from the backup (never
   copy directories; preserve unrelated files).
5. Verify the ORIGINAL approved regression suite passes BEFORE any new work
   (S06/R02: 90 tests; mandatory files: test_character_read_api.py,
   test_publish_rejection.py, test_character_domain.py,
   test_character_validator.py, test_character_preset_importer.py).
6. Reimplement the task only on top of the restored approved state;
   frontend-only unless a concrete new blocker is reported; use the existing
   flat publish endpoint and typed contracts (content_url/validation).
7. Remove the weaker nested image endpoint; do NOT replace R02 routes.
8. Do not add artifact-id attachment/upload controls.
9. Add focused frontend interaction tests: confirmation, success/refetch,
   422, 409, immutable state.
10. Desktop + 390px visual QA.
11. Run the ACTUAL `scripts/quality-baseline.ps1` and record its Run ID
    (do NOT report "gates executed individually" as a baseline).
12. REPORT = SUBMITTED, never APPROVED. Never write PM_REVIEW.

## Quarantine pattern for corrupt tests

Tests written against forbidden/removed endpoints are NOT deleted and NOT
kept in the suite — move them to `output/quarantine-<task>-corrupt/` and say
so in LOG/REPORT. Keeps evidence while removing false-green.

## Manager gates before the next task (queue protocol)

PM queue (e.g. S05: T03→T04→T05→T06→exit) — do not open the next task until:
worker exited; REPORT=SUBMITTED; manager reviewed diff + ran targeted tests
independently; recorded MANAGER_VERIFIED_PENDING_SPRINT_REVIEW. After a
worker starts, check `git status` of BOTH worktree and MAIN within 60s;
snapshot MAIN baseline (`git status --short | wc -l`) BEFORE launching.

## E2E hang on long-lived Next dev server

Playwright `page.goto("/characters")` hung → suite timed out at 600s, twice
(T04 review and S06-T05 correction). The long-lived `next dev` server
(port 3010) is the culprit. Fix: kill the QA dev server, start a fresh one,
probe `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010/characters`
→ 200 before re-running Playwright. Kill stale servers with
`MSYS_NO_PATHCONV=1 taskkill /PID <pid> /F` (bare `//PID` is mangled by MSYS).

## Manager-side incident report deliverable

Write `docs/pm/sessions/<ID>/INCIDENT_REPORT_*.md` with: what happened, root
cause, disk evidence table (mtime per file, both repos), fix actions, current
state, decisions Codex must make (keep/clean main copies, delete backup dir,
approve SUBMITTED). Give the user the exact one-liner to send Codex.
