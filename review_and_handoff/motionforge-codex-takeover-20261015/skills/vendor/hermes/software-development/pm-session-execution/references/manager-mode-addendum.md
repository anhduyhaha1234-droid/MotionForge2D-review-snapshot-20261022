# Manager-Mode Addendum — S09 C1/C2 lessons (2026-08-25)

Condensed from the MotionForge2D S09-C2 correction cycle. These are MANAGER-side
lessons (Hermes acting as orchestrator dispatching/resuming worker sessions), as
opposed to the worker-side protocol in the main SKILL.md.

## 1. Terminal-state honesty is a first-class gate

- C1 ended with 2 `FAIL_OPEN_QUESTION` classes (f1_hard_cut, f5_group_occlusion)
  yet the manager recorded `TASK_MANAGER_VERIFIED`. Codex review correctly
  overturned it to `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`.
- Rule: if the sprint prompt says "required class fail/unknown/FOQ = blocker",
  then ANY unresolved FOQ forces the BLOCKED terminal regardless of how green
  everything else is. Never soften a terminal state to look done.
- Honest measured evidence (e.g. "f5 cannot be placed by frozen surface") is
  GOOD worker behavior — reward it, do not pressure workers into fake PASS.

## 2. Freeze handshakes must be machine-readable and re-verified

- C1 used an ad-hoc 3-file SHA string; the worker's derivation method was not
  recorded in its own log, so the manager had to brute-force combinations to
  reproduce the hash. Fix in C2: manager computes the manifest ITSELF.
- J1-C2 pattern that worked: recursive hash over behavior-critical globs →
  JSON manifest `{frozen_at, head, files: {path: sha256}}` written under the
  run dir; pin the MANIFEST's own SHA-256 in the registry. Worker must verify
  manifest BEFORE and AFTER every measured run; any drift invalidates all
  downstream evidence and requires a full re-run, never "just update the SHA".

## 3. Version-bump coordination is a recurring failure mode

- I03 bumped `SCHEMA_VERSION = 3` in code but left fixture thresholds.json at
  v2 → every subprocess test failed closed with one identical error. The fix
  was one line, but the manager caught it only because it ran tests itself.
- Rule: when resuming with "bump X", always enumerate BOTH sides of the
  version comparison (code constant AND data file) and forbid threshold/value
  tuning in the same breath.

## 4. Cross-task static-analysis debt

- A worker introduced PEP 562 lazy re-export (`__getattr__ -> object`) to break
  a circular import; a sibling task's static import then lost its type and mypy
  reported `"object" not callable`. Correction belongs to the OWNER of the file
  that introduced the pattern: add a `TYPE_CHECKING` branch re-importing the
  names so static imports keep types while runtime stays lazy.

## 5. Dispatch mechanics pitfalls (Windows/MSYS)

- Inline prompts containing apostrophes/quotes inside `$(printf '...')` can
  produce `unexpected EOF while looking for matching '` and exit code 2 — the
  worker NEVER RECEIVES the prompt and the session silently does nothing.
  Always write resume packets to `<rundir>/resume-*.txt` and dispatch via
  `$(cat file)` instead of inline quoting.
- Exit markers must be unique per attempt (`EXIT-WAVEB=`, `EXIT-FIX1=`) so
  grep can distinguish attempts appended to the same log.
- Liveness = log-size delta + unique EXIT marker; MSYS `ps` PID mapping is
  unreliable.

## 6. Wave orchestration shape that worked

- Max 5 parallel workers, disjoint write-sets, PREP workers stop at
  WAITING_JOIN before the freeze join; final binding runs happen after the
  measured decision exists (no stale-artifact fallback).
- Manager verification between every worker exit and the next wave: run the
  focused suites yourself ×2 with distinct basetemps, ruff/mypy yourself,
  check the actual artifact content (e.g. OpenAPI path counts, spec assertion
  greps) rather than trusting REPORT claims. Workers exit early or misreport
  more often than expected (~30% of exits needed a correction resume).
- Keep a single session registry file per correction cycle with: task → exact
  owner session id → proc handle → state → exclusive write-set → hashes →
  heartbeat log. This is what makes "resume the correct owner" auditable.
