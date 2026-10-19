# S02-T02 - PM Review

**Decision:** APPROVED
**Reviewer:** PM/Codex

**Reviewed:** 2026-08-03 19:30 +07:00

## Blocking findings

1. `create_successor` clears `idempotency_key` on the terminal predecessor to
   satisfy a broad unique index. Terminal rows are contractually immutable.
   Implement uniqueness only for active/completed ownership of the logical key
   (partial index by state), retaining the predecessor key/generation unchanged.
2. Update the explicitly released S01 bootstrap assertions for the new S02 head;
   preserve a test that the S01 revision itself still has no Job tables.
3. Finish Ruff/mypy, architecture evidence, session report and mandatory 7/7.

## Correction round 2

4. `acquire_lease()` is a read-then-`merge` sequence, not an atomic guarded
   claim. Two sessions can both return a lease while the last commit overwrites
   the first. Implement a database-enforced CAS/conditional claim so only one
   claimant succeeds; expired/released reacquisition must monotonically bump
   lease version/revision and invalidate the old token.
5. Running/cancelling checkpoint/progress writes only validate fencing when a
   token is non-null. A missing token must be rejected just like a stale token.
   Audit every worker mutation path for mandatory fence enforcement.

## Final decision

Correction round 2 implements atomic CAS lease acquisition, live-lease conflict,
monotonic reacquisition and mandatory fence enforcement for worker mutations.
Real two-session race coverage proves exactly one claimant succeeds.

PM independently ran 47 targeted tests, 66 combined persistence tests, Ruff,
mypy and quality baseline `20260803-200936`; all PASS. S02-T03 is released.
