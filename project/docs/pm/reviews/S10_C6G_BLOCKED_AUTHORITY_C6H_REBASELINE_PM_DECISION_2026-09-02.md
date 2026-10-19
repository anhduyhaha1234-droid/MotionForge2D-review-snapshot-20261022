# S10-C6G blocked authority / S10-C6H semantic rebaseline — Codex PM decision

**Decision time:** 2026-09-02 +07  
**Reviewer:** Codex Project PM / BA / independent reviewer  
**C6G terminal:** `BLOCKED_TEST_AUTHORITY / SUPERSEDED_BY_S10-C6H / NOT_APPROVED`  
**C6H authority:** `AUTHORIZED_TO_DISPATCH / NOT_APPROVED`

## Decision

Codex selects proposal 1 only as a **formal semantic-authority rebaseline**.
The current `DAD70AE3...` reconstruction is evidence/input, not an accepted
test authority and not a restoration. Phase B may start only after a fresh
worker and Manager pass the bounded C6H authority gate.

Proposal 2 was exhausted read-only before this decision. Three VSS snapshots
from 2026-08-30 13:03 contain the same real ancestor of the test:

- SHA-256 `5B312719C7D7349670C9E17DCA87682820ED5A885C55122B8335D923E5FCD6F6`;
- 24,542 bytes, 444 lines, 13 test definitions;
- source path under each shadow:
  `Users\Admin\MotionForge2D-worktrees\s08-integration\tests\test_s10_full_apply_api.py`.

It is not the pre-C14 57-test target. No exact copy was found in the other
MotionForge worktrees/repositories, OneDrive, VS Code history, File History or
Recycle Bin. An independent replay from that VSS ancestor and the successful
post-snapshot DB patch diffs still lacked 19 predecessor changes made through
other execution paths; it did not reach target SHA
`963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`.
The guarded C14-T3 forensic run independently reached the same authority
block: 344 source lines were absent from all full read pages.

Proposal 3 is rejected as the product terminal. Byte-exact history is lost,
but the product contract can be re-established with stronger executable and
independently reviewed semantic evidence. The historical incident remains
closed as blocked; it is never relabeled as exact recovery.

## Why the current reconstruction is not accepted directly

- Current test SHA is
  `DAD70AE304D123227F9646B501461ED7FD8E6337DADB024269075A8CE63A4591`.
- It has 64 textual test definitions, 63 unique names/collected nodes, one
  duplicate `test_submit_distinct_on_changed_checkpoint`, and unresolved
  `_C10BoomService` references.
- Codex's complete fresh run was 58 failed / 5 passed. Helper-generation and
  source-order mismatches make it unsuitable as an authority.
- Similar names, compilation, partial passing or matrix prose cannot make this
  file authoritative.

## C6H authority contract

1. Preserve the VSS ancestor, DAD reconstruction, destroyed backup, forensic
   candidates and state.db exports as immutable incident evidence.
2. Open new Task ID `S10-T01C-C15` in one fresh compact worker session. Do not
   resume either destructive C14 session `20260902_013803_4d5ce5` or its
   tool-limited continuation `20260902_102609_ee5195`.
3. Rebaseline semantics from the union of the exact 13-test VSS ancestor,
   retained accepted C6D/C6E/C6F contracts, C6G's locked 14-row matrix,
   chronological read/patch evidence and real route/SQL behavior. Current
   production implementation is never an oracle for weakening expected results.
4. Rebaseline final arithmetic is 57 retained collected contracts plus five
   C6G contracts = exactly 62 unique nodes. Every retained node must map to a
   binary behavior row or an explicitly stronger replacement; no silent drop,
   duplicate definition, unresolved helper, skip, xfail or broad-status waiver.
5. During the authority phase the production route is frozen at
   `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`.
   Test-harness defects must be separated from credible production RED.
6. Existing source/test files are patch-only. Whole-file overwrite, copy-over,
   redirection, generated replacement or destructive shrink is forbidden.
7. Manager independently gates the authority before reopening Phase B. One
   combined correction turn is permitted; repeated piecemeal cycles are not.
8. Phase B closes the original 14-row ambiguity/resolver/Retry ownership
   contract, then runs focused and broad gates on frozen final bytes.

## Session Opening Proposal — AUTHORIZED_TO_DISPATCH

- Manager may continue orchestration, but must create exactly one new worker
  for `S10-T01C-C15` and record its returned session ID before any write.
- Worker route: exact selector `comboBAI`, provider `custom`, reasoning `max`,
  Hermes fallback OFF, TTFB 900. No silent provider/model substitution.
- One writer only. Read-only verification lanes may run in parallel only after
  writer terminal and with isolated DB/root/basetemp/output/cache.
- Allowed implementation files are only
  `tests/test_s10_full_apply_api.py` and
  `app/api/routes/s10_full_apply.py`; the route stays frozen until R-GATE.
- S11/S12/S13 production remains blocked. C6H may end only at
  `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW` or an explicit
  truthful blocker.

Binding prompt:
`docs/pm/prompts/S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`.

