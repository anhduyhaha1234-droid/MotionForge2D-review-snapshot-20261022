# S11-C4-R2 Independent PM/Code Rereview — 2026-09-05

## Verdict

`S11-C4-R2 = CHANGES_REQUESTED / NOT_APPROVED`  
`S11 = NOT_CLOSED`  
`S12/S13 = BLOCKED`

The R2 production mechanism is materially correct: a fresh Codex probe placed
the rendezvous inside the explicit-registration critical section and proved
that the second caller remained blocked, the failed caller rolled back, the
successful caller completed, and the final registry was the exact ten-detector
snapshot without a repair call. Fresh KeyboardInterrupt/SystemExit probes also
rolled back and propagated the original type. Closure is nevertheless blocked
because the committed durable race test does not exercise that contention and
repairs state before its final assertion. The submission also violated the
single-owner contract and is not supported by the required closure-grade raw
packet.

No production or test bytes were changed by this review.

## Review boundary

- Time: 2026-09-05 23:43 +07.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Branch/HEAD: `codex/s11-integration` at
  `11dd50a467f5832ad372ceb1f50a61252e0462ee`.
- Local equals `origin/codex/s11-integration`; porcelain is empty.
- R2 implementation commit:
  `938d75905740cb6afa7792eb881c302321b5b268`, integrated by merge
  `8918f4a7cc2128990176c76f9bf6fc15dbad2709`; final INT01 docs commit is
  `11dd50a`.
- Exact accepted route remains provider `muse`, custom 9Router,
  `cmc/meta/muse-spark-1.3-contributor`, reasoning max, fallback OFF.
- Read-only Hermes state identifies intended owner
  `20260905_192221_6da09b` and competing owner
  `20260905_192249_150b51`, both on the exact accepted model and same R2
  worktree. Neither currently has an OS writer process, but both DB rows retain
  `ended_at = NULL`.

## Positive independent evidence

- Fresh three-module T03G on canonical: `151 passed`, 293 warnings,
  183.95 seconds, exit 0.
- Fresh T05A consumers: `14 passed`, 21 warnings, 20.97 seconds, exit 0.
- Fresh targeted T12 twice on distinct basetemp roots: `1 passed` +
  `1 passed`, both exit 0.
- Ruff `--select F` on the R2 binding paths, two-file binding mypy and
  `git diff --check 7751598..HEAD` all pass.
- Alembic reports the sole head `f9a0b1c2d3e4`.
- Direct OpenAPI materialization reports 274 paths, 340 operations and zero
  duplicate operation IDs.
- Stronger process-only true-contention reproduction:
  - caller A paused inside `contact_break.register()` while holding the
    production `_BOOTSTRAP_LOCK`;
  - caller B started and was observed blocked before A was released;
  - A returned `RunQcChecksError / QC_RUN_BOOTSTRAP_CONFLICT` with
    `RuntimeError` cause;
  - B succeeded with ten revisions;
  - pre-state equaled final state before any repair call.
- Fresh KeyboardInterrupt and SystemExit reproductions each restored the exact
  four-field snapshot and propagated the original exception type.
- Manager-retained T06 12, T01 64, S10 270 and S10 API 71 logs are green. They
  are retained supporting evidence, not a waiver for the open rows below.

## Findings

### P1 — durable race test is sequential and masks final state with repair

Locations: `tests/test_s11_t03g_qc_check_c4r1.py:315-357` and
`:417-430`.

Contract: two live callers must rendezvous at the contested production
bootstrap transaction; one fails, one succeeds, joins are bounded, and the
registry immediately after both callers finish must equal the exact expected
snapshot/band without a cleanup or retry hiding corruption.

Actual test structure:

- the two threads rendezvous only at an outer barrier;
- the supposed successful caller then executes
  `f_failed.wait(timeout=30)` at line 331, so it does not call production
  bootstrap until the failed caller has fully returned and set the event;
- the test therefore executes two sequential transactions rather than two
  contending transactions;
- `restored_ghost` is recorded by the failed caller but never asserted;
- lines 355-356 call `ensure_full_band_registered()` again before the final
  registry assertions, so that clean repair can hide a bad post-thread state.

Impact: removing or weakening `_BOOTSTRAP_LOCK`, or leaving a stale rollback,
can escape this durable regression even though the current implementation is
correct. Under the four-layer closure rule the mechanism/reproduction layers
are green, but the test-structure layer remains open.

Required correction: resume intended owner `20260905_192221_6da09b`; patch
only the R2 test module so caller A pauses inside the production explicit-
registration operation while holding the lock, caller B is observed blocked,
then release A and assert both raw outcomes plus the immediate final snapshot.
No post-thread bootstrap/repair call is permitted. Add one durable subprocess
row covering both KeyboardInterrupt and SystemExit rollback/propagation so R2
row 3 is not represented only by an unindexed live probe.

### P1 — two owners were dispatched and the reported freeze was ineffective

The binding prompt authorized exactly one new recovery owner on one worktree.
Hermes state instead contains:

- intended implementation owner `20260905_192221_6da09b`;
- competing owner `20260905_192249_150b51`;
- both were assigned the same Task ID, model and
  `C:\Users\Admin\MotionForge2D-worktrees\s11-c4-r2`.

`REGISTRY.md` says the duplicate was detected/frozen at 19:55 +07 and did not
touch the write-set. Read-only DB message 176346 proves that session later ran
at 20:04:12 +07 and created the guard manifest plus four byte snapshots under
`docs/pm/sessions/S11-T03G/evidence/c4r2/`. At the review boundary the R2
worktree is dirty with those five untracked files. The intended owner did not
begin tracked patching until 21:02:58 +07 and used bounded patch calls, so no
tracked-byte collision or production-authority loss was found; nevertheless
the exact one-task/one-owner and effective-freeze claims are false.

Required correction: permanently freeze `20260905_192249_150b51`, preserve and
hash its five untracked files without deleting/modifying/staging them, and use
only exact owner `20260905_192221_6da09b` for the bounded test correction. A
new compact Manager must coordinate R3 so the duplicate-dispatch path is not
reused.

### P1 — final evidence packet does not meet its own closure contract

Final claimed root:
`C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-191900-R2-bootstrap`.

- It has no postimage manifest, raw guard result, final Git/local-remote log,
  quiescence log or command ledger.
- Its baseline manifest contains only four allowed files, not the protected
  set. The alternate transfer root has nine rows but omits logical line counts
  and has no complete final packet.
- Gate logs generally contain pytest/tool output only: no exact command,
  start/end timestamps, explicit exit or isolated resource tuple. The packet
  reports exit markers and roots that are absent from the underlying files.
- `matrix-t03g-151.log` retains a first run with `129 failed, 9 passed, 13
  errors` caused by missing DB tables; the packet indexes only the later green
  run and does not disclose this failed attempt.
- The packet says the competing owner was frozen before it wrote, contradicted
  by DB message 176346 and the five current untracked files.
- The prior R1 failed orchestration attempt required by the R2 prompt is not
  retained/indexed in the new root.

Impact: the packet cannot prove command ordering, resource isolation,
postimage guard integrity or truthful owner closure. Required correction is a
new immutable external R3 evidence root with a complete baseline/postimage,
raw guard results, full command envelopes, every failed attempt and a truthful
owner timeline.

## Session Opening Proposal

Status: `PROPOSED_ONLY / R3_TEST_AND_EVIDENCE_CORRECTION`.

- Use one new compact Manager; do not reuse the two R2 coordination loops.
- Permanently freeze competing session `20260905_192249_150b51`.
- Resume exact healthy implementation owner `20260905_192221_6da09b` for the
  same Task ID `S11-T03G-C4-R2-RECOVERY`; no new worker session.
- Maximum implementation wave: 1.
- Exclusive write-set: `tests/test_s11_t03g_qc_check_c4r1.py` plus append-only
  T03G LOG/REPORT. Production is frozen/read-only.
- Route remains exact `cmc/meta/muse-spark-1.3-contributor`, provider `muse`,
  reasoning max, fallback OFF.
- Protect and preserve the five untracked competitor evidence files. Do not
  clean or stage them.
- S12/S13 remain blocked until the R3 submission receives a fresh Codex
  approval.

Complete next prompt:
`docs/pm/prompts/S11_C4_R3_DURABLE_CONTENTION_EVIDENCE_CLOSURE_MANAGER_2026-09-05.md`.
