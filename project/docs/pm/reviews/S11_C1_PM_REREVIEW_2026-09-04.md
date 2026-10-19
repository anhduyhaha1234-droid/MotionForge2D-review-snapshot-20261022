# S11-C1 — Codex Independent PM/BA/Code Rereview

**Review date:** 2026-09-04 (+07)  
**Reviewed local tree:** `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`  
**Local branch / HEAD:** `codex/s11-integration` @ `c9d5453b429fd96957860cd7ed27eddcf18e2ead`  
**GitHub remote HEAD:** `4d7ad8196c3f7a21af744906ef4174690159d889`  
**Submission claim:** `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`  
**Codex verdict:** `CHANGES_REQUESTED / NOT_APPROVED / S11_NOT_CLOSED`

## 1. Decision

S11-C1 materially improved the original implementation, but it does not close
the two P1 findings. The local tree is clean and the submitted focused/broad
tests are green; nevertheless, three fresh real-DB adversarial probes expose
uncovered authority failures, and the new restart test does not execute the
targeted correction/recompute path that the contract requires.

The correction also violated durable task ownership by resuming the T04D
session as T05A. Finally, the integration tree was deliberately left 14 commits
ahead of GitHub and a background watchdog remains active after terminal submit.
S12 and S13 remain unopened.

## 2. Positive evidence retained

- The local integration worktree is porcelain-clean at `c9d5453`.
- `git diff --check 7751598214eedb6b72e3783e39a2a408721abe40..HEAD`
  exits 0; the original whitespace finding is cleared.
- Full-scope filtering and a ten-detector band were added; the original single
  audio-only false-ready probe is now rejected.
- Codex independently reran:
  - T03G job/API modules: `44 passed, 89 warnings in 59.26s`;
  - T05A readiness/next-action modules: `14 passed, 21 warnings in 20.83s`;
  - submitted T06C restart node: `1 passed, 2 warnings in 5.75s`.
- Manager reports a broad S11 suite of 326/326, outer acceptance 11/11, T01
  64/64 and S10 71/71. These counts are credible as regression evidence but do
  not waive the missing binary rows below.
- Read-only Hermes usage records show the correction turns did route through
  `ocgfree/muse-spark-1.3-contributor-free`; the base session model field alone
  is stale and was not used to reject the route.

## 3. Findings

### [P1] Full-run completion still fails open and unrelated audio history can evict valid authority

**Locations**

- `app/persistence/qc_check_runs.py:248-266`
- `app/persistence/qc_check_runs.py:304-327`
- `app/persistence/qc_check_runs.py:366-403`

The new coverage validator converts absent `summary.errors` and
`summary.checks_skipped` to zero. It also does not compare completion-level
evidence/policy identity to the manifest/current authority, and it does not
prove `checks_requested == checks_run == 10`, non-cancelled/non-deadline state,
or an exact non-empty detector revision envelope.

Separately, `list_jobs(limit=50)` is applied before filtering to full scope.
Therefore 50+ newer audio-only jobs can hide a valid completed full run and
incorrectly return `never_run`.

Codex ran a fresh Alembic-head SQLite probe against current bytes:

```text
missing_required_summary_counts:
  actual_run_state=completed
  expected=failed

completion_manifest_identity_mismatch:
  actual_run_state=completed
  expected=failed_or_stale

full_authority_after_51_newer_audio_runs:
  actual_run_state=never_run
  actual_job=None
  expected_run_state=completed
  expected_job=<original full job>
```

The first two cases can create false `ready`; the third creates false
`not_run`. Existing 44 tests omit all three adversarial rows.

**Exact owner:** S11-T03G session `20260903_170546_0d42f6`.

### [P1] T06C restart test restarts full QC, not targeted correction/recompute

**Locations**

- `tests/test_s11_t02_t06_acceptance.py:1070-1080`
- `tests/test_s11_t02_t06_acceptance.py:1411-1540`

The test genuinely recreates `JobService` over the same DB/root, which is an
improvement. However, the persisted operation is created by
`submit_run_qc_checks(..., scope=SCOPE_FULL)`. The test never calls the
correction bridge, never creates/resumes a `RECOMPUTE_OBJECTS` successor, and
never compares affected versus unaffected artifact rows, hashes or bytes.

Assertions C1B-01..10 cover one full QC run, QCItem uniqueness and blocked
readiness. They do not prove affected-segment-only recompute, untouched ready
scenes, no full-timeline rerun, or exactly one correction resolution. The
docstring and comments overclaim those properties.

**Exact owner:** S11-T06C session `20260903_223530_b90853`. If a correct
executable correction-restart test reveals a production defect, route only that
defect to exact T04B owner `20260903_183246_706d31`.

### [P1] T05A correction was written by the durable T04D session

**Evidence**

- Binding C1 prompt pins T05A owner to `20260903_203404_4a4548`.
- Hermes state DB first message for `20260903_203404_5b3841` assigns that
  session to S11-T04D.
- `s11-c1/lanes/c2-t05a/prompt.md` instead labels `...5b3841` as the exact T05A
  owner and resumes it to create commit `3beee0d` on the T05A branch.

This is a direct one-task/one-session identity violation. The code is not
rejected merely because of authorship, but the wrong session must be frozen from
T05A and all remaining T05A work must resume the real owner
`20260903_203404_4a4548`. The incident and accepted/replaced bytes must be
recorded explicitly; history must not be rewritten to hide it.

### [P1] Required remote durability gate was knowingly skipped

The binding prompt requires final local HEAD to equal remote after non-force
push. Current local is `c9d5453`, while GitHub remains `4d7ad81`; the branch is
14 commits ahead. `EXIT_VERDICT.md` explicitly says local-only and not pushed.
This is not an approved alternative to the prompt and prevents closure. Because
code findings remain, the next correction must retain the known local/remote
pair, finish fixes, then perform one final non-force push and verify the remote.

### [P2] Terminal cleanup is incomplete

Two live bash processes still run the `s11c1_watchdog.py` loop and continue
writing `watchdog.log/state.json` after Manager terminal. The last observed
write was after the exit packet. The next Manager must stop/remove this exact
watchdog before dispatch and use native bounded monitoring without leaving a
background loop.

## 4. Quality assessment

The Muse correction was fast and produced useful code, especially the full-band
split and real service recreation. Its weakness here is contract precision: the
implementation and tests satisfy the happy shape but not absence/tamper/history
pressure, while the restart test proves a neighboring workflow instead of the
required workflow. Broad green counts therefore overstate closure.

## 5. Session Opening Proposal

**Authority:** `AUTHORIZED_TO_DISPATCH` for bounded `S11-C2`; S12/S13 remain
blocked.

- Open one new compact Manager session; retire the S11-C1 Manager and stop its
  watchdog before any writer.
- Parallel wave maximum two:
  - resume exact T03G `20260903_170546_0d42f6` for completion authority;
  - resume exact T06C `20260903_223530_b90853` for true correction/recompute
    restart acceptance.
- T04B `20260903_183246_706d31` is conditional on a minimal executable product
  failure from T06C.
- After T03G integration, resume the real T05A owner
  `20260903_203404_4a4548` dependency-serial. Never resume T04D owner
  `20260903_203404_5b3841` for T05A again.
- Resume exact INT01 `20260903_112116_35051c` for conflict-free transport and
  the final non-force push only after all gates are green.
- Every resumed turn uses custom 9Router model
  `ocgfree/muse-spark-1.3-contributor-free`, reasoning `max`, fallback OFF,
  TTFB 900.
- T03G and T06C are highly compacted, so each receives one guarded bounded
  correction with a compact current-contract handoff. Any second scope miss,
  unsafe write or unusable turn stops at
  `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`.

Binding prompt:
`docs/pm/prompts/S11_C2_COMPLETION_AUTHORITY_TARGETED_RESTART_OWNER_EXIT_MANAGER_2026-09-04.md`.

