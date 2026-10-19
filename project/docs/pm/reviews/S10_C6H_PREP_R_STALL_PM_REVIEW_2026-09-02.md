# S10-C6H PREP-R stall — independent Codex PM review

Review time: 2026-09-02 Asia/Bangkok

## Binary verdict

`S10-C6H = AUTHORIZED_TO_DISPATCH / PREP_R_STALLED / NOT_APPROVED`

This is not a new implementation failure and there is no evidence of a new
destructive write. It is an orchestration stall before worker dispatch. C15 has
not started, so no C6H implementation or validation claim is accepted.

## Independently reproduced facts

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch/HEAD: `codex/s08-integration` at
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`
- Current reconstructed test SHA-256 remains
  `DAD70AE304D123227F9646B501461ED7FD8E6337DADB024269075A8CE63A4591`.
- Frozen route SHA-256 remains
  `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`.
- `output/s10/c6h` contains only the preserved VSS ancestor copy. Required
  guards, source ledger, retained-57 matrix, worker launch record and C15
  evidence are absent.
- The S10 registry has no C15 dispatch append and no fresh worker session ID.
- Process inspection found Hermes desktop/service infrastructure but no live
  Hermes CLI worker for C15. The read-only heartbeat is not a task worker.
- Manager session `20260902_100134_89bbc9` is resumable, but its last response
  stopped after reporting PREP-R progress. It must be resumed; do not create a
  replacement Manager session.

## Exact location of the PREP-R blocker

The Manager stopped while deriving the retained 57-test authority set. The
remaining disposition is deterministic from the existing read-page and patch
chronology evidence:

- 48 unique non-C6G tests are directly proven by authoritative pre-destruction
  read pages.
- Add these nine patch/contract-proven retained tests:
  1. `test_minimal_submit_omits_legacy_authority_succeeds`
  2. `test_client_legacy_authority_tamper_fails_closed_zero_run_job`
  3. `test_v1_checkpoint_reapproval_required_zero_mutation`
  4. `test_tampered_v2_checkpoint_blocked`
  5. `test_cross_project_v2_blocked`
  6. `test_stale_checkpoint_hash_blocked`
  7. `test_unsupported_route_never_coerced`
  8. `test_cancel_idempotent_repeat_route`
  9. `test_c6e_lifecycle_terminal_active_contradiction_fails_closed`
- Exclude obsolete
  `test_c6e_replay_vs_retry_barrier_at_most_one_active`: it was added in patch
  operation/message `145447`, explicitly removed/replaced in `145471`, is absent
  from all authoritative read pages and is superseded by
  `test_c6e_replay_vs_retry_barrier_fail_closed`, visible in late reads
  `146000`, `146518` and `146695`.
- Keep the first current definition of
  `test_submit_distinct_on_changed_checkpoint`; classify the second definition
  as a stale reconstruction duplicate. The pre-C14 read evidence contains one,
  not two.

This yields exactly 57 retained contracts. Adding the five C6G contracts yields
the required 62 unique tests. Manager may document this disposition but must
not edit the test module; only fresh worker C15 may apply the bounded patch.

## Remaining technical risk

PREP-R being resolvable does not mean the suite is almost green. The current
candidate still references `_C10BoomService` without a definition and the known
baseline is 58 failed / 5 passed. C15 must repair authority helpers and then
perform the C6G implementation/closure gates. Old regenerated `.pyc` files are
not byte authority.

## Session opening decision

Resume Manager session `20260902_100134_89bbc9` with the companion continuation
prompt. Do not resume C14 sessions `20260902_013803_4d5ce5` or
`20260902_102609_ee5195`. After persisting the complete source ledger, retained
matrix and guards, Manager must probe exact `comboBAI` / `custom` / `max` with
fallback off, create exactly one fresh compact `S10-T01C-C15` worker, record the
returned session ID before its first write, and continue through the original
C6H terminal gates. If the next continuation cannot persist the deterministic
57/57 mapping, it must terminate as `BLOCKED_REBASELINE_SPEC`; another ETA-only
report is not acceptable.

