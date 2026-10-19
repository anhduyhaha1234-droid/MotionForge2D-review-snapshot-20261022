# S10-C6G C14 test-destruction incident — Codex PM decision

**Review time:** 2026-09-02 +07  
**Reviewer:** Codex Project PM / BA / independent reviewer  
**Decision:** `S10-C6G = INCIDENT_RECOVERY_REQUIRED / NOT_SUBMITTED / NOT_APPROVED`  
**Chosen recovery:** option 2, with a recovery-only first phase and exact-owner safeguards

## 1. Independent facts

- Canonical rules were read in full in this turn from
  `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`:
  193 logical lines, SHA-256
  `C6AD775A98B9FEEDCDD435932A0B6659B0EF991B0D43F492E47379CC5ED20089`.
- Target remains
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
  `codex/s08-integration`, HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`. No current C14 writer or task
  listener was found and `MOTIONFORGE_DATABASE_URL` was unset.
- Hermes message `146796` contains a `write_file` call against
  `tests/test_s10_full_apply_api.py`; message `146797` records 14,891 bytes
  written and warns that the file had only been read through pagination.
  The preserved destroyed copy is 278 lines, SHA-256
  `086F793D6FB5D7F66EB40205CA78D3180A40124335130412A0E2225829AD4678`.
- The current reconstructed main test is 2,692 lines, SHA-256
  `DAD70AE304D123227F9646B501461ED7FD8E6337DADB024269075A8CE63A4591`.
  It is not the reviewed C6F baseline, whose SHA-256 was
  `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`.
- The reconstruction contains 64 textual `def test_` declarations but pytest
  collects 63 nodes. `test_submit_distinct_on_changed_checkpoint` is defined
  twice and `_C10BoomService` is referenced repeatedly but is not defined.
- Codex ran the complete reconstructed API module on a fresh short basetemp:
  **58 failed, 5 passed** in 68.12 seconds. The common failures include an
  invalid recovered checkpoint helper (`stored checkpoint_hash does not match
  recomputed content hash`) and missing recovered symbols. Therefore the
  Manager statement “9 tests fail” materially understates the current state.
- The original 538,546-byte clean pytest pyc claimed by the recovery report was
  not preserved at review time. Current pycs were generated from reconstructed
  or overwritten bytes and cannot serve as the old source authority.
- Read-only Hermes DB inspection shows the actual C14 writer session is
  `20260902_013803_4d5ce5` (88 messages, 41 tool calls). The registry instead
  names `20260901_230235_b80d4b`, which has only four messages and one tool call.
  Recovery must resume the actual C14 owner and correct the ledger; resuming the
  stale ID would create another owner lineage.
- Current C14 route SHA-256 is
  `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`.
  It must be frozen during test-authority recovery.

## 2. Decision on the three proposals

1. **Manager deterministic alignment — rejected.** The canonical role split
   forbids Manager edits to production tests. The emergency Manager rewrite is
   retained as evidence but must not continue.
2. **Resume worker C14 — selected with controls.** Only the actual C14 writer
   may restore the test. Its first continuation is forensic recovery only:
   state.db read-only, candidate reconstruction outside the main test, no
   memory rebuild, no `write_file`/redirection/copy-over of the main test, and
   only verified `apply_patch` hunks after an exact baseline candidate exists.
3. **Codex semantic reconstruction — rejected.** Codex is the independent
   reviewer and must not become the implementation writer; accepting a
   non-byte-identical rewrite would erase the test authority being reviewed.

The actual owner is high-risk but this is the first recorded catastrophic
write in that session. One tightly guarded resume is allowed. A second direct
overwrite, memory reconstruction, scope violation, or inability to retain the
recovery contract is repeated context-health evidence and must terminate with
`BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`; no third attempt is allowed.

## 3. Recovery and continuation gate

- First reconstruct a candidate for the exact pre-C14 test from chronological
  state.db tool payloads/results and prior patch evidence. The candidate must
  match baseline SHA-256 `963ED50E...` before it can replace the main test.
- Persist every extraction script/query/result under new C6G evidence; `%TEMP%`
  is not acceptable as the only copy. The state database is read-only and must
  not be vacuumed, copied over, or modified.
- Once the exact 57-node baseline is restored, add/update only the C6G tests by
  bounded `apply_patch`; require 57 retained node IDs plus five C6G node IDs,
  no duplicate definitions and no unresolved helpers.
- Manager independently verifies restoration before production work resumes.
  Only then may the same owner finish the original 14-row C6G contract.
- If the exact baseline cannot be recovered, stop
  `BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION`; do not disguise a semantic
  rewrite as restoration and do not run broad closure gates.

## 4. Session Opening Proposal — AUTHORIZED_TO_DISPATCH

- Resume exact actual C14 owner `20260902_013803_4d5ce5`; do not resume
  `20260901_230235_b80d4b` or any older T01C lineage and do not create a new
  worker.
- Phase A exclusive write-set: `tests/test_s10_full_apply_api.py`, append-only
  T01C records, and new `output/s10/c6g/t01c-c14/recovery-t3/**`. Route and all
  production files are frozen.
- After Manager proves exact test-authority recovery, Phase B may reopen only
  `app/api/routes/s10_full_apply.py` plus the recovered test and finish the
  original C6G matrix. One writer only; read-only readers start after terminal.
- Worker route remains exact selector `comboBAI`, provider `custom`, reasoning
  `max`, Hermes external fallback OFF, TTFB 900.
- Authority is `AUTHORIZED_TO_DISPATCH` for this bounded recovery/continuation
  only. S11/S12/S13 production remains blocked.

Binding continuation prompt:
`docs/pm/prompts/S10_C6G_C14_T3_FORENSIC_TEST_AUTHORITY_RECOVERY_MANAGER_2026-09-02.md`.
