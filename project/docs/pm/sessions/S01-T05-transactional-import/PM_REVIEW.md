# S01-T05 - PM Review

**Decision:** APPROVED
**Reviewed:** 2026-08-03 18:41 +07:00
**Reviewer:** PM/Codex

## Blocking finding

`LegacyImporter._revalidate_before_transaction()` verifies the live source, but
`_live_project_data()` subsequently reopens `project.json` from the legacy root
inside the database transaction. A concurrent edit between those operations can
therefore import bytes that do not match the approved preview or immutable backup.
The implementation report explicitly acknowledges this race, but AC1/AC2 require
the imported rows to be derived from the approved, backed-up generation.

## Required correction

1. Populate imported project metadata/scenes from the verified immutable backup,
   not by reopening mutable legacy files after the final revalidation.
2. Add a deterministic regression test that mutates the live `project.json` after
   revalidation and proves the committed database rows still match the approved
   preview/backup generation (or that the import refuses before DB writes).
3. Update architecture/report/limitations so they no longer claim the known race.
4. Re-run targeted persistence tests and the mandatory 7/7 quality baseline.

## Final verification

The correction reads project metadata and scenes exclusively from the verified
backup manifest after the final live-source check. The deterministic race test
passes and the original source remains outside the transaction's read path.

- T05 targeted tests: 18 passed.
- S01 persistence suite: 117 passed.
- Ruff and mypy: PASS.
- Quality baseline run `20260803-184034`: 7/7 PASS.
- Root `channels.json` user change remains unstaged and untouched.
