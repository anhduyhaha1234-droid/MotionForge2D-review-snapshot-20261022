# S08-H02 C3 / C4 / C5 correction rounds — protocol evolution + verified pass shapes

Context: S08 correction cycle on MotionForge2D, local-API security family
(H02). Codex rejected the sprint repeatedly (C1 → C5 on the same task family).
Each round's brief is the contract; the observable protocol shifted round to
round. Reflect the current brief, not the previous round.

## Session-mode flip (the #1 trap)

- C1, C2: "resume OWN session" (the S05/C1 convention).
- C3: "Do not resume the old 20260818 session. Use a new run/session ID."
- C4: "NEW session ... never reuse an old session id."
- C5: "MODE: RESUME SAME TASK + SAME WRITER SESSION ... Resume EXACT Hermes
  session 20260819_105751_c6c6a1. Do not create a new Task ID / writer session."

Manager action: grep the brief for `resume|new session|do not resume`; build the
launcher accordingly (`--resume <id>` vs a fresh `--query` `hermes chat`). Do
not port the previous round's mode. C5 was a *backflip* to resume — the same
session carried C4 then C5 sequentially (314 messages, exit 0).

## ISO run-timestamp protocol (C3, C4, C5)

Record in packet header (LOG + REPORT):
- run_started_at_local: e.g. 2026-08-19T09:59:13+07:00
- run_started_at_utc:     2026-08-19T02:59:13Z
- run_finished_at_local / run_finished_at_utc (writer fills at end)
- elapsed_seconds: finished_epoch - started_epoch (monotonic)

Manager writes started values at packet materialization; writer appends
finished/elapsed. Never infer the run time from a reused session id (Codex
explicitly demanded this after C2's approximate timestamp).

## FINAL_REPORTED_TO_USER gate (C3+)

- Task is NOT COMPLETE until the manager sends a user-facing final message with:
  exit code, local finish time +07:00, duration, test result, report path.
- Record FINAL_REPORTED_TO_USER=true in MANAGER_STATE.md + tracking.
- If final delivery fails, stay active and retry; never silently exit.
- Persist MANAGER_STATE.md (last_progress_at, writer session/PID,
  current/last/next action, blocker, exact resume command).
- Real heartbeat at the brief's interval (C3/C4/C5: <=5 min — tighter than the
  skill's default 30-min floor). Emit after every completed gate too.

## Manager must re-verify ports (verified C4)

Worker self-reported "ports NO_LISTENERS", yet a leftover QA uvicorn
(`app.main:app`, same worktree, port 8027, PID 15692) was still LISTENING.
Manager's own `netstat` caught it; verified the CommandLine identity matches
the worktree before `Stop-Process`; re-verified NO_LISTENERS on all QA ports.

Lesson: never treat a worker "ports free" line as proof. Re-run `netstat`/
`Get-CimInstance` yourself at the manager gate. (This is why the C4 branch of
the skill's H02 checklist must include an independent port sweep.)

## Verify-script hygiene

- `set -u` + unset `MOTIONFORGE_DATABASE_URL` aborts the script at the first
  `echo ${MOTIONFORGE_DATABASE_URL}`. Use `${VAR:-UNSET}` in every expansion
  (or `set +u`).
- Row-preservation checks need the real table name from `models.py`
  (`__tablename__`, e.g. `workspace` NOT `workspaces`). A "no such table" in the
  manager's own query is a manager-query bug, not a migration failure — the
  gate is UPGRADE/DOWNGRADE/REUPGRADE all exit 0 + `alembic_version` head
  unchanged + rows preserved (seed 2 rows, check count after each step).
- Verify-script candidate tables: `workspace`, `project`, `object_role`,
  `object_role_artifact` (has `superseded_by_id`), `object_correction`.

## Force-stop-mid-append recovery (verified C1 on 2026-08-19)

A killed worker can leave LOG.md claiming "REPORT.md appended CORRECTION C1"
while REPORT.md actually lacks the section (killed mid "Let me append to
REPORT.md."). The manager MUST verify BOTH files:
- `grep -nE "^# CORRECTION C1|Status:" REPORT.md` — section present?
- LOG entry says appended? → compare.
Repair = append the real section to REPORT (root cause, final implementation,
per-acceptance evidence, files changed, exact tests+results, deviations,
protected-state, lineage) + a RECOVERY entry to LOG, both matching, preserving
all C1..C(prev) history. State the stale claim was fixed.

## Audit class: publish-then-metadata rollback (video source)

Replacement-image rollback being covered does NOT imply video-source rollback
is covered. Audit `upload_video`:
- old shape: `staging.replace(proj_dir / stored_name)` inside try, then
  `pwf.set_video(project_id, stored_name)` AFTER the try/finally → a set_video
  failure leaves the just-published `source_<uuid>.mp4` as an orphan.
- safe shape: wrap set_video; on failure `(proj_dir / stored_name).unlink()`
  and re-raise; previous source stays present and SELECTED; project.json
  byte-identical; GET project 200; no staging/publish-temp orphan.
- Required test: `test_video_metadata_update_failure_rolls_back_file_and_state`
  (inject set_video failure after a successful second publish → 500, new source
  removed, only previous source remains, previous still SELECTED, no orphan).

## REAL subprocess / concurrency tests (Codex demands, C3-C5)

The briefs escalated beyond monkeypatch-only suites:
- real child sleeping 3s, timeout 0.2s must raise in <1s (observed 0.203s);
- real child writing to stderr before stdout — no deadlock;
- real child over-cap line without newline — bounded fail;
- deterministic two-thread barrier test (A! / A? preset save racing, asserting
  two distinct files, no silent overwrite);
- atomic preset reservation via `os.open(O_CREAT|O_EXCL)` suffix-retry
  (a.json, a-2.json...) instead of check-then-write `exists()`;
- combined pipe byte cap counted on RAW BYTES before decode (UTF-8 multibyte
  >1 MiB must raise), with atomic accept/reject under one lock so overshoot
  <= one 8192-byte reader chunk and no append after abort;
- every `wait`/`join` uses `max(0, deadline - monotonic())` — never a fixed
  5 s window after the deadline.

When the brief says "real subprocess test" / "not only monkeypatch", bake that
verbatim into the packet. A monkeypatch-only suite fails Codex review.

## Observed pass shapes (fresh roots, -p no:cacheprovider, shallow basetemps)

C3: focused 23/23, full H02 57/57, +test_api 82/82, cross-suite 84/84,
baseline 20260819-041116 7/7.
C4: focused 29/29, H02 63/63, +test_api 88/88, object_correction 34/34,
concurrency x20 PASS=20 FAIL=0, cross-suite 90/90, baseline 20260819-114525 7/7.
C5: focused 26/26, H02 71/71, +test_api 96/96, object_correction 34/34,
cross-suite 27/27, baseline 20260819-133623 7/7.
Each round's worker self-report (SUBMITTED, "all green") was re-verified
independently by the manager with fresh basetemps before declaring
MANAGER_VERIFIED_PENDING_SPRINT_REVIEW. Protected MAIN unchanged every round
(channels dd7aae…555, DB 311296 B / 67d5c7…e6, SAM2 898083611 B /
2647878…318).
