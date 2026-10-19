# S02-T05 - PM Review

**Decision:** APPROVED
**Reviewer:** PM/Codex

**Reviewed:** 2026-08-04 00:24 +07:00

## Blocking findings

1. The claimed 7/7 baseline did not finish: run `20260803-233647` contains only
   Gate 1 and `overall.status=RUNNING`.
2. `scripts/debug_repro.py` is an out-of-scope temporary artifact and must be
   removed before submission.
3. `deps.py` constructs `JobService()` at import; its constructor creates the
   database parent directory/engine. Import must have zero filesystem/runtime
   side effects. Make durable service/engine construction lifecycle-lazy.
4. Automatic startup upgrade of an existing on-disk database does not create a
   verified backup first, contrary to the approved S01 migration policy. Missing
   DB may bootstrap directly; existing pending-revision DB needs backup+fsync+
   checksum evidence before Alembic upgrade and must fail closed on backup error.
5. The legacy callable compatibility shim retains an unreconstructable closure
   registry. The approved contract says the shim is removed after cutover. Remove
   callable submission from runtime authority and migrate tests to explicit
   registered synthetic job types/manifests.

## Final decision

All five blockers are closed: baseline completed, temp artifact removed, import
is side-effect free, pending-revision startup upgrades are backup-first and
verified, and callable closure submission is removed. PM independently ran 16
targeted tests, Ruff, mypy and baseline `20260804-000921`; all 7 gates PASS.

S02 exit is approved.
