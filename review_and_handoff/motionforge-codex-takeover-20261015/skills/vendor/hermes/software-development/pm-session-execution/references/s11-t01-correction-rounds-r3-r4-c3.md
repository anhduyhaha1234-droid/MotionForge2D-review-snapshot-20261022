# S11-T01 correction rounds R3/R4 + C3 — finding/evidence trail (2026-08-22)

Session-level detail behind `correction-cycle-lessons.md` §20–§23.
Worktree: MotionForge2D-worktrees/s08-integration @ a43b20da (unchanged).
Owner sessions: T01B 20260821_160614_40b90e, T01C 20260821_214021_cbc36d,
T01D 20260822_003041_b18319. Engine `original_audio_remux.py` hash stayed
`47833d53` through every round — all fixes were test/handler-side.

## Round 3 findings

P1 (T01B) machine-wide ffmpeg scan cross-blame:
- `tests/test_s11_original_audio_remux.py:439–445` `_ffmpeg_pids()` scanned
  ALL machine processes by name; two suites running concurrently with
  separate basetemps each saw the sibling's live ffmpeg as its own orphan →
  both failed.
- Fix: `_owned_ffmpeg_pids(marker)` requires BOTH signals — pid ∈ recursive
  descendants of current pytest AND managed-root path appears in cmdline.

P2 (T01D) diag-tail dropped stderr:
- `_run_suite()` captured both streams but the assertion payload tail came
  from stdout only (`result.stdout[-25:]`) → child failures surfacing on
  stderr produced empty diagnostics. Fix: `_diag_message(code, out_tail,
  err_tail)` embeds both bounded tails; also moved acceptance leak-gate to
  process-tree ownership and added `_inner_suite_lock()` (msvcrt range-lock
  file in tempfile.gettempdir()) to serialize nested five-file suite runs —
  T01C's leak test was still machine-wide pid-diff and outside T01D's
  write-set, so scheduling serialization was the only legal fix; zero
  assertions weakened.

## Round 4 findings

P1 (T01C) source integrity — size-only checkpoint validation:
- `app/workflow/original_audio_handler.py:495–513` `_source_evidence_valid()`
  checked only relative_path + is_file() + size_bytes; same-size mutation
  reproduced True via a standalone probe before dispatch.
- Worker fix (all inside handler, engine untouched):
  - evidence-valid re-hashes disk and compares recorded sha256;
  - resolve-phase hash gate raises stable `SOURCE_NOT_READY`;
  - post-engine check compares engine `source_sha256` +
    `post_remux_source_sha256` against evidence;
  - pre-publication gate compares engine-reported, post-remux, and
    disk-now hashes vs recorded; drift dict in error details of
    `ATTACH_VALIDATION_FAILED`; drift cleanup rmtree's THIS run's staging
    engine dir only.
- Regressions: test_13 mutates source same-size between phases → job FAILED,
  zero artifact rows, artifact tree byte-for-byte unchanged, staging empty;
  test_14 walks all checkpoints written during a run asserting no absolute
  managed-root paths / drive-letter patterns.

P2 (T01B) re-parent gap:
- Descendants-only scan at assert time missed orphans whose parent died
  mid-run (Windows re-parents; pid leaves the descendant set).
- Fix: `_OwnedPidRecorder` context manager wraps engine `subprocess_popen`
  to record ffmpeg/ffprobe pids AT SPAWN + 50 ms sampler thread during the
  run; `_assert_no_orphans(marker, known_pids=…)` polls exactly that fixed
  set via psutil.Process(pid) with name-guard (alive pid must still be an
  ffmpeg/ffprobe binary, else PID-reuse counts as exited), bounded deadline,
  no fixed sleeps. Cross-run isolation regression kept passing concurrently.

## C3 — OUTER↔INNER pytest PIPE deadlock found by manager

Discovery path (worth copying for any "suite hangs" report):
1. Frozen five-file run exceeded 600 s tool cap repeatedly; psutil showed
   two python.exe pytest processes alive for 80+ minutes.
2. psutil cpu-times delta over 5–8 s ≈ 0 for both → true idle, not slow.
3. Open-files showed INNER holding its integration.db but no children.
4. `pip install py-spy`; `py-spy dump --pid <inner>` → MainThread idle at
   `_pytest/config/__init__.py:254 _console_main` = tests DONE, process not
   exiting; outer dump showed `_run_suite_tracked` poll loop line 192.
5. Conclusion: stdout/stderr=PIPE never drained while polling (communicate()
   only called after exit) + no total deadline → classic full-pipe deadlock.
   Manager killed inner pid; outer then unwound.

Fix (T01D write-set): reader threads drain both streams into chunk lists
during the poll loop; one hard wall-clock deadline (1800 s) for the whole
child; on timeout kill + partial tails + "[harness] child killed at Ns"
marker appended to err_tail so the failure is self-diagnosing.

Expectation ripple routed properly: scenario 3(c) in
tests/test_s11_original_audio_integration.py asserted ENGINE_FAILED for a
same-size mutated source; after T01C's earlier preflight the job now fails
at source phase with SOURCE_NOT_READY (still fail-closed, zero publication,
clean staging). Manager verified semantics preserved, then mini-correction
resumed the OWNING T01D session to update the assertion + comment — worker
never touched the other lane's file itself.

## Manager independent gates (final state)

- remux serial ×2: 20/20 (23.82s/23.76s); concurrent two-invocation with
  separate basetemps: 20/20 + 20/20 simultaneously (24.89s/24.90s)
- attach focused: 14/14 (19.49s); mypy handler clean; ruff clean
- integration alone: 9/9 (13.70s); acceptance long-basetemp 2/2 (130.98s);
  two acceptance invocations in parallel: 198.02s + 262.80s both green
- frozen five-file suite single command: 56 passed / 0 failed (205.04s)
- ruff across all S11 files clean; git diff --check clean (pre-existing
  frontend CRLF warning only); FFMPEG_LEAKS NONE; PRAGMA foreign_key_check
  NONE on alembic-upgraded temp DB; MAIN HEAD unchanged
- Hashes chốt: engine 47833d53, remux-test e8cac817, attach-test 70ed749e,
  integration 3fd43a78, acceptance 8a8b912b

Known pre-existing (out of scope, left for Codex):
tests/test_durable_job_persistence.py::test_no_worker_or_api_cutover_tables
expects a table list missing S07's own project_cast_mapping migration.
T01C worker wrote a one-line proposed patch at
docs/pm/sessions/S11-T01C-durable-audio-job/PROPOSED_FIX_guard_tables.md
for the owning session instead of editing out-of-scope files.

Evidence dirs: output/s11-t01b/r4p2-*/, output/s11-t01c/r4p1-20260822-1357/,
output/s11-t01d/c3-20260822-hang-fix/.
