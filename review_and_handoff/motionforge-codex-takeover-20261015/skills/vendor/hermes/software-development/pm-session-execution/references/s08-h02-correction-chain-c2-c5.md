# S08-H02 local-API security correction chain — C2 → C5 (recovery-manager notes)

Full per-round evidence from the S08-H02 correction chain (2026-08-18/19),
worktree `s08-integration`, branch `codex/s08-integration`. Session lineage,
pass shapes, and the manager-verify recipe for each round.

## Session-mode rule (the #1 lesson of this chain)

Read the Codex decision text to know WHICH mode, every round:

| Round | Codex mode | Launcher shape |
|---|---|---|
| C1 (recovery) | resume OWN session `20260818_020323_151164` | `hermes chat --resume <id>` |
| C2 preset | resume OWN session (same as C1) | `--resume <id>` |
| C3 probe/preset-root | NEW session (do NOT resume old) | `--query` (no --resume) |
| C4 atomic/bounds | NEW session, new Run ID | `--query` |
| C5 atomic-cap/budget | RESUME SAME TASK + SAME SESSION `20260819_105751_c6c6a1` | `--resume <id>`**

** Even after C3/C4 used NEW sessions, C5 explicitly mandated RESUME of the C4
session. Always check the decision text; never assume a fixed model.

## C3/C4 "corrected manager protocol" — the exact acceptance list

When Codex appends "Keep the corrected manager protocol", it demands:
1. NEW session and run ID when the decision says so (C3/C4) or RESUME exact
   session when it says so (C5) — never invent a third mode.
2. ISO timestamps with local +07:00 AND UTC "Z", plus `elapsed_seconds`
   (monotonic). Record started_* at launch, finished_* + elapsed at end, in
   BOTH LOG.md and REPORT.md. Never infer current run time from a reused id.
3. Real heartbeat ≤5 min (not a file written only at end); persist
   `output/MANAGER_STATE.md` (last_progress_at, writer session/PID, current
   action, last completed, next action, blocker, launch/resume command).
4. Do not run the writer in an unattended detached launcher (manager stays in
   bounded-wait + liveness loop).
5. FINAL_REPORTED_TO_USER=true ONLY after sending the final user-facing
   message: exit code, local finish time +07:00, duration, test result, report
   path. If delivery fails, remain active and retry; never exit silently.
6. Set PowerShell/console output explicitly to UTF-8.

## Finding → fix → test map (security chain)

| Finding | Fix | Proof |
|---|---|---|
| C2: client preset name/path traversal (project.json overwrite) | central `safe_preset_output_path`/`safe_preset_path`; server slug filename; hostile→422 before write; containment under `<project>/presets`; bounded ffprobe | 13 new tests; focused 20→50→75; cross-suite 77 |
| C3-1: sequential stdout→stderr `readline` blocks past deadline | concurrent `_PipeReader` threads + combined-cap abort Event + tight deadline poll + `_kill_proc` full reap | real child sleep-3s/timeout-0.2 → raised 0.203s (<1s) |
| C3-2: presets root itself a symlink/junction outside | `_assert_presets_root_contained` anchors unresolved+resolved root to validated project dir | directory-junction test RAN not skipped → 422 zero side-effect |
| C3-3: A! / A? both slug to a.json | server unique filename + `_stored_preset_name`; 409/reject on collision | collision test |
| C4-1: concurrent preset overwrite (check-then-write) | `os.open(O_CREAT\|O_EXCL)` suffix-retry loop (a.json, a-2.json…); no process-local exists() dependency | real 2-thread + barrier test → two distinct files |
| C4-2: byte cap counted decoded chars (text=True) | capture BINARY bytes; count len(bytes) before decode; overshoot ≤ chunk; decode after proc terminates + cap passed | real multibyte UTF-8 >1 MiB raises ProbeOutputTooLargeError |
| C4-3: EOF reap granted second full timeout window | every wait/join uses max(0, deadline - monotonic()); no budget → kill+reap | real child close-pipes-near-deadline → <0.30s with timeout 0.2 |
| C4-4: flaky concurrency test (every return = applied) | capture returned created/applied bool; True=applied False=replayed; keep asserts | concurrency test 20/20 isolated runs PASS=20 FAIL=0 |
| C5-1: combined pipe cap not atomic (two readers overshoot >1 chunk) | `_CaptureState.accept()` makes keep/reject decision under one lock; abort once; no append after abort; overshoot ≤1 chunk | two-reader barrier test + real dual-stream subprocess |
| C5-2: cleanup grants fixed 5s windows (`proc.wait(5.0)`, joins 5.0) | one `remaining_budget(deadline)`; kill direct child; close pipe handles; non-blocking reap; don't mask original exception | real close-pipes-near-deadline + no-5s-window test + no-process-leak |

## Manager verification traps (each cost a real round of rework)

1. `set -u` + unset env var in a manager verify script = instant abort before
   any section runs. Always `${VAR:-UNSET}` inside scripts that echo env vars.
   Symptom: verify log shows only the header "=== WORKTREE ===" then nothing.
2. Migration row-preservation check: workspaces table is SINGULAR `workspace`
   (`__tablename__`); `SELECT COUNT(*) FROM workspaces` → "no such table" even
   though the round-trip succeeded. Verify table names from models.py first.
3. Never trust worker "ports NO_LISTENERS": S08-H02-C4 worker claimed free but
   leftover uvicorn `app.main:app` still LISTENING on 8027 (PID 15692). Manager
   `netstat -ano | grep -E ':(3012|8888|8000|3000|5173|8027) ' | grep -i
   listening` caught it. Never rely on the worker's port-clean claim; run your
   own netstat and identity-verify before Stop-Process.
4. Watcher-kill `Stop-Process` matching the script path can be flagged for
   approval and TIME OUT (BLOCKED, "user has NOT consented"). Do NOT retry the
   kill via a different command. Leave the idle watcher (harmless — syncs a
   frozen log) and spawn a fresh watcher for the new round's log path.
5. On RESUME with a NEW log path, the old round's watcher watches the OLD log —
   spawn a fresh `watch-<new>.sh` pointed at the new SRC; don't reuse the old
   one (LIVE.txt would go stale).

## Pass shape observed (C4 final, manager-verified independently)

- C4 focused `-k 'c4 or preset or probe or deadline or collision'`: 29 passed
- full H02: 63 passed; H02 + test_api: 88 passed; object_correction: 34 passed
- concurrency test x20 loop: PASS=20 FAIL=0 (deterministic)
- cross-suite (golden + h02 + extraction_api + r01): 90 passed; golden metrics
  regenerated under fresh Run ID
- ruff app tests / mypy app / git diff --check: all clean
- fresh 7/7 baseline Run `20260819-114525` OVERALL PASS
- protected MAIN unchanged (channels dd7aae…555, DB 311296 B / 67d5c7…e6,
  SAM2 898083611 B / 2647878…318)
- final git status 173 (packet evidence in scope)

## Golden cross-suite env (repeatable)

Cross-suite golden invocation needs its env vars; from the LOG:
`S08T06_RUN_ID=<fresh-run-id> GOLDEN_TMP_ROOT=C:/Users/Admin/AppData/Local/Temp/
<fresh-tmp> python -m pytest tests/test_s08_golden_object_intelligence.py
tests/test_object_extraction_api.py tests/test_s08_r01_queued_cancel_lifecycle.py
-q -p no:cacheprovider --basetemp=<shallow-tmp>`
Contract SHA `f008c027095c8534bd29d71a884cc5850878a10d0ef536c7b2738c0fb8edf323`
must stay frozen; thresholds never tuned after observing results.
