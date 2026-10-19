# S08-H02 C2/C3 security correction rounds (verified 2026-08-19)

Codex issued TWO successive security CHANGES_REQUESTED on MotionForge2D S08-H02
after the C1 security round was fully manager-verified. Each round was a NEW
packet session dir with its OWN session (C2 resumed `20260818_020323_151164`;
C3 was MANDATED to use a NEW session `20260819_033728_0a3c30`). Full command
/ result evidence is in each packet's LOG.md/REPORT.md; this file distils the
repeatable finding classes and the fix shapes that cleared them.

## Round C2 — preset path containment + bounded ffprobe

Findings (both reproduced by Codex in an isolated temp project):

1. **Save preset renamed into a path:** `save_project_preset` did
   `output_path = presets_dir / f"{body.name.lower().replace(' ', '_')}.json"`.
   A name of `..\project` escaped `<project>/presets` and overwrote
   `project.json` (Codex repro: 322 B -> 118 B).
2. **Apply preset path param unvalidated:** `apply_preset` did
   `preset_path = proj_dir / "presets" / preset_filename` with no validation or
   containment → Windows backslash traversal could read `project.json` or any
   file outside presets.

Fix shapes that passed:
- `body.name` became DISPLAY-ONLY metadata; the FILE name is a strict
  server-owned slug (`slugify_preset_name`). `_reject_hostile` rejects
  slash/backslash/`..`/dot-only/absolute/drive-qualified/control-byte/reserved
  names with 422 BEFORE any write (control bytes detected BEFORE null-stripping
  so `a\x00b` is refused, never silently sanitized).
- `safe_preset_output_path` / `safe_preset_path` in `preset_service.py` return
  `target.resolve(strict=False)` and prove it stays under the presets root;
  reserved slug (`project.json` case-insensitive) -> 422.
- Apply requires a single safe segment ending `.json`; hostile -> 422, missing
  -> 404, never 500.

## Round C3 — probe deadline, preset junction-rotation, slug collision

1. **Probe deadline not enforced:** `_run_ffprobe` read stdout via
   `_read_bounded` then stderr SEQUENTIALLY; `_read_bounded` checked the
   deadline only at loop top then did a BLOCKING `readline()`. A quiet pipe (or
   one pipe filling) blocked past the deadline. Codex repro: requested timeout
   0.2 s, actual 3.016 s, `deadline_enforced=False`.
   Fix: `_PipeReader` threads drain stdout/stderr CONCURRENTLY with a shared
   `_OutputState` (combined byte cap + `threading.Event` abort); the MAIN thread
   owns both enforced conditions in a tight poll loop — on `abort` ->
   `ProbeOutputTooLargeError`, on deadline -> `subprocess.TimeoutExpired`, both
   via `_kill_proc` (kill + bounded wait) to reap the FULL child. Killing the
   child closes the pipe write-end, unblocking any in-flight `read()`.
   Mandatory REAL subprocess tests (not monkeypatch):
   - child sleeps 3 s, timeout 0.2 -> raised at 0.203 s (< 1 s requirement);
   - child fills stderr before stdout -> no deadlock;
   - over-cap line without newline -> bounded failure.
   Also `-select_streams v:0/a:0` + `-show_entries` restrict output; separate
   audio probe; `PROBE_MAX_STREAMS` parse ceiling + JSON-shape validation;
   fail-closed -> route 415, no media published.
2. **Preset ROOT junction escape:** protecting the file target was not enough —
   if `<project>/presets` ITSELF is a junction/symlink outside the project,
   `base = Path(presets_dir).resolve()` moves outside and the per-file
   containment check passes for outside targets. Fix: `_assert_presets_root_
   contained(presets_dir, project_dir)` anchors BOTH the unresolved and resolved
   root to the VALIDATED project dir; save+apply -> 422, zero side effects.
   New DIRECTORY-level test (`mklink /J`) — asserted RAN not skipped (host
   supports junctions); existing file-symlink test kept green.
3. **Slug collision:** `A!` and `A?` both slugged to `a.json` -> silent
   overwrite of an existing preset. Fix: server-owned unique filename OR
   explicit reject of existing/colliding target with 409;
   `_stored_preset_name` best-effort reads the existing file's `name`, and an
   unreadable/foreign file is conservatively treated as a collision (never
   clobbered).

## Manager drill (both rounds)

- Confirm each finding ON DISK (read the exact vulnerable line) before writing
  the packet — never dispatch on the brief's word alone.
- One writer; manager stays read-only while writer is live; independent
  verification after exit (focused -k tests -> full file -> +test_api ->
  cross-suite incl. golden vertical -> ruff/mypy/diff -> migration head ->
  protected MAIN -> ports).
- A code-only security round must NOT change the migration head — assert head
  unchanged as scope evidence.
- Protected MAIN baseline (unchanged every round): channels.json SHA
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`,
  data/motionforge.db 311296 B / `67d5c773...f2e6`, SAM2.1
  898083611 B / `2647878d...dd318`.
- Pass counts observed: C2 focused 20 + full 50 + test_api 75 + cross-suite 77;
  C3 focused 23 + full 57 + test_api 82 + cross-suite 84; fresh 7/7 baseline
  each round (`20260819-015528`, `20260819-041116`).

## C3 manager protocol (Codex-mandated)

- In the packet record `run_started_at_local` (+07:00), `run_started_at_utc`
  (Z), `run_finished_at_local/utc`, monotonic `elapsed_seconds`. Never infer
  current run time from a reused session ID.
- Real heartbeat every ≤5 minutes (log mtime + PID + tail), not a state file
  written only at end.
- Do not run the writer unattended-detached and walk away.
- On writer exit send IMMEDIATELY a user-facing final message: exit code, local
  finish time +07:00, duration, test results, report path.
- Task NOT COMPLETE until `FINAL_REPORTED_TO_USER=true` recorded (MANAGER_STATE
  + tracking row). If final delivery fails, remain active and retry.
- Set PowerShell/console output explicitly to UTF-8.
- Stop at SPRINT_SUBMITTED; never APPROVED/CLOSED; do not start S07/S09.

## Round C4 — atomic preset write, exact probe byte cap, deadline budget, flaky concurrency test

Codex rejected S08 a fourth time. Same C3 manager protocol applied (NEW session
`20260819_105751_c6c6a1`, split run_started 09:59:13+07:00, finished
11:57:52+07:00, elapsed 7118 s). Findings + fix shapes:

1. **Check-then-write preset race (P1):** `unique_preset_output_path` used
   `while candidate.exists()` and `save_preset` wrote LATER; two concurrent
   saves `A!` and `A?` both picked `a.json`, only one survived (Codex repro:
   same_target=True, files=['a.json'], errors=[]).
   Fix: ATOMIC exclusive reservation — `os.open(O_CREAT|O_EXCL)` inside a
   suffix-retry loop (`a.json`, `a-2.json`, ...). Exactly one save owns a given
   filename; every loser exclusively owns the next suffix. No process-local
   `exists()` dependency. Same-name re-save still updates its own file in place.
   Mandatory REAL concurrent test (2 threads + barrier): two simultaneous saves
   both successful → two DISTINCT files, both JSON valid with correct display
   names, no partial file, no silent overwrite (or one explicit conflict).
2. **Byte cap counted DECODED characters:** pipes opened `text=True`, reader
   did `state.add(len(chunk))` on str — a multibyte UTF-8 stream passed the
   cap uncaught (Codex repro: cap 1048576 B, actual 1400000 B,
   ProbeOutputTooLargeError NOT raised).
   Fix: capture stdout/stderr as BINARY bytes; count combined `len(bytes)`
   BEFORE decode with bounded overshoot ≤ reader chunk size; decode
   UTF-8/errors=replace ONLY after the process is terminated and the byte cap
   has passed. REAL subprocess test: multibyte UTF-8 output > 1 MiB must raise
   ProbeOutputTooLargeError.
3. **EOF-reap re-granted a full timeout window:** after both readers hit EOF,
   `proc.wait(timeout=max(0, min(10, timeout)))` gave the child a FRESH `timeout`
   even after most of the deadline elapsed (Codex repro: run 0.2 s timeout,
   child closes pipes near deadline then continues, actual 0.407 s).
   Fix: every `wait`/`join`/`kill-reap` uses `max(0, deadline - monotonic())`;
   zero remaining budget → kill + reap immediately; cleanup never grants a
   second full window. REAL subprocess test: child sleeps ~0.18 s, closes
   stdout/stderr, keeps sleeping; timeout 0.2 s finishes in a tight window
   (asserted < 0.30 s).
4. **Flaky concurrency TEST (test-only fix):** `test_concurrent_confirm_exactly_one_wins`
   treated every non-exception return as "applied", but `confirm_correction`
   may return `created=False` directly after the other thread commits.
   Fix: capture the returned created/applied boolean; True = applied, False =
   replayed; keep the invariant asserts (exactly one recompute job, occurrence
   moved exactly once); do NOT weaken product concurrency semantics. Prove
   determinism by running ≥20 isolated repetitions.

### Manager drill additions (C4)

- **Independently re-verify ports even when the worker claims NO_LISTENERS.**
  C4 worker reported ports free, but a leftover QA uvicorn (`app.main:app` on
  port 8027, PID 15692, CommandLine matching the same worktree) was still
  LISTENING. Manager netstat caught it, verified identity, killed it, and
  re-verified NO_LISTENERS on 3012/8014/8015/8025-8028. Record the deviation
  in the tracking row for Codex.
- **Re-run the concurrency ×20 yourself** with `-p no:cacheprovider` and fresh
  basetemps — a loop `for i in $(seq 1 20); do pytest ::test_... --basetemp=$\
  BT/conc$i; done`, print `PASS=n FAIL=n`. C4 observed PASS=20 FAIL=0.
- Pass counts observed (C4): focused 29 + full H02 63 + test_api 88 +
  object_correction 34 + concurrency ×20 20/20 + cross-suite 90. Fresh 7/7
  baseline `20260819-114525`.
- Finding class progression to expect (each was a separate Codex round):
  traversal/joins (C2) → deadline/junction/slug (C3) → atomicity & exact
  bounds & test determinism (C4). Next plausible rounds attack deeper variants
  of the same axes (e.g. atomic image/replacement publish, decode-time caps,
  per-file vs combined caps) — preempt them with atomic exclusive publication +
  byte-accurate limits + deterministic tests in the FIRST security round.
