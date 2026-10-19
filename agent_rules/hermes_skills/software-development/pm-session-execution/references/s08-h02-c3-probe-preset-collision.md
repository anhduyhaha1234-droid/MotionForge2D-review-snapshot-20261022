# S08-H02-C3 — bounded subprocess + preset containment + slug collision (verified 2026-08-19)

Codex kept peeling security layers across FOUR H02 rounds (original → C1 → C2 → C3).
Manager must NEVER assume one validation round closes the sprint — every round
carries its own session policy, findings, validation order, and fresh 7/7 baseline.

## Three new finding classes + how to close them

### 1. Bounded subprocess with CONCURRENT drain
`_run_ffprobe` used `subprocess.run(capture_output=True)` (C2 → replaced by a
bounded runner) but the C2 runner STILL read `proc.stdout` then `proc.stderr`
SEQUENTIALLY via blocking `readline()`. Codex repro: timeout requested 0.2s,
actual elapsed 3.016s, `deadline_enforced=False` — a blocked readline (no
newline in output, or one pipe filling) blocks past the deadline.

Correct shape, fail-closed:
- `Popen` + drain stdout AND stderr CONCURRENTLY (threads or select loop).
- Enforce deadline AND a COMBINED output cap, even when output has no newline or
  one pipe fills first.
- Kill/reap the FULL child process on timeout/cap.
- Query only required fields + first relevant streams (`-select_streams v:0/a:0`
  + `-show_entries`), parse-ceiling on stream count, JSON-shape validation.

Mandatory REAL subprocess tests (spawn an actual `python -c` child), not only
monkeypatch:
- child sleeps 3s; timeout 0.2s must return/raise in UNDER 1s
- child fills stderr before writing stdout — no deadlock
- child writes an over-cap line WITHOUT newline — fails within bounded time

### 2. Directory-level symlink/junction containment
`base = Path(presets_dir).resolve(); target.resolve().is_relative_to(base)`
PASSES when `<project>/presets` ITSELF is a junction/symlink pointing outside —
because the resolved base IS the outside directory, so containment is proven
relative to the escaped root.

Correct shape:
- Anchor BOTH the unresolved AND resolved presets root to the already-validated
  project dir (`pwf._project_dir` + `_assert_contained`), never to a root that
  the client can have relocated.
- Save/apply return stable 422 with zero side effects.
- Test a DIRECTORY junction/symlink escape, not only a file-symlink test (skip
  only if host lacks the privilege; the resolve-strict-False containment is the
  real enforcement).

### 3. Slug collision silently overwrites
Distinct display names collapsing to the same slug (`A!` and `A?` → both
`a.json` after `re.sub("[^a-z0-9_-]+","_",...)`) silently overwrite an existing
preset.
- Either use a server-owned UNIQUE filename, or reject an existing/colliding
  target explicitly with 409.
- NEVER silently overwrite an existing preset.
- Tests: normal save → list → apply STILL succeeds; collision preserves the
  first preset byte-identical (no overwrite).

## Codex C3 manager protocol (differs from prior rounds — honor the current brief)

- **Session policy:** Codex may mandate a NEW session even for a correction
  (H02-C3: "Do not resume the old 20260818 session. Use a new run/session ID").
  The CURRENT brief governs session reuse — do NOT blindly follow the
  same-session default from earlier rounds.
- **Run timestamps:** record in the packet — `run_started_at_local`
  (ISO-8601 +07:00), `run_started_at_utc` (Z), `run_finished_at_local/utc`, and
  monotonic `elapsed_seconds`. Never infer current run time from a reused
  session ID.
- **Manager heartbeat:** real heartbeat every ≤ 5 min (NOT a file written only
  at end). Don't run the writer in an unattended detached launcher.
- **Final delivery:** when the writer exits, IMMEDIATELY send a user-facing
  final message with exit code, local finish time +07:00, duration, test result
  and report path. Task is NOT COMPLETE until `FINAL_REPORTED_TO_USER=true` is
  recorded. If final delivery fails, remain active and retry — do not silently
  exit.
- Set PowerShell/console output explicitly to UTF-8 where used.

## LOG/REPORT consistency pitfall (forced-stop, verified H02-C1 recovery)

A worker killed mid "Let me append to REPORT.md" leaves LOG.md claiming the
REPORT append happened when it did NOT. On recovery the manager MUST verify
REPORT content independently against LOG's claims (the LOG entry was written,
the REPORT tail was not), then repair BOTH docs and the real code gap. Log file
tail in UTF-16 may show the interrupted sentence as the death marker.

## Manager verification for security rounds (fresh, independent)

- Re-run focused → full → +test_api → cross-suite (golden+h02+extraction_api+
  r01) with fresh basetemps `C:/Users/Admin/AppData/Local/Temp/<task>-mgr-*`.
- Golden vertical re-run under a FRESH manager run id (`S08T06_RUN_ID=mgr-…`) so
  worker evidence dirs are never overwritten.
- Migration round-trip in an isolated subshell: VERIFY ROW PRESERVATION by
  SEEDING rows first (fresh temp DB), then upgrade→downgrade→re-upgrade and
  count rows after each (a fresh DB with 0 rows proves nothing).
- Real isolated app smoke: health 200 / untrusted state-changing Origin 403 /
  trusted ACAO without credentials / hostile identifier 4xx.
- Scope audit via mtime window on `app tests migrations docs output` only
  (never `find frontend` wholesale — times out on node_modules/.next).
