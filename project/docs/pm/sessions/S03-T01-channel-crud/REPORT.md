# S03-T01 - Implementation Report

**Status:** SUBMITTED (correction round 3 — final allowed attempt)
**Task:** Durable Channel CRUD API (list/read/create/update/archive)
**Session:** docs/pm/sessions/S03-T01-channel-crud
**Review:** REQUEST_CHANGES round 3 — all 3 blocking findings corrected;
all round-1 and round-2 fixes retained.

## Summary

The three round-3 blockers are fixed with deterministic repository-level
tests: (1) the post-CAS re-read is a fresh database SELECT (identity-map
`session.get` removed), (2) the UPDATE-time active-name partial unique-index
violation is mapped to `NameConflictError`/HTTP 409 without masking other
integrity errors, and (3) durable-job head tests resolve the current Alembic
head dynamically and prove S02 ancestry instead of hard-coding S03 as the
permanent head.

## Evidence per PM round-3 finding

### R3-1 Fresh read after zero-row archive CAS
- `archive_channel` re-read after a lost CAS now uses an explicit
  `SELECT ... WHERE id AND workspace` (`scalar_one_or_none`), which
  bypasses the session identity map — `session.get` would return the
  caller's stale in-session ACTIVE object, so the idempotent-200 path
  could never trigger.
- Deterministic repository-level interleaving test
  `test_archive_interleaving_both_callers_read_active_then_cas`:
  - two independent sessions both `get_channel` (read ACTIVE),
  - both pause on a `threading.Barrier(2)` BEFORE their CAS UPDATE,
  - A archives → `archived, revision 2` (one bump),
  - B's CAS matches zero rows → fresh SELECT → returns the archived row
    idempotently → `archived, revision 2` (no bump),
  - final DB state: `archived`, `revision == 2`.
  This fails on the old identity-map re-read because B's session would
  return its stale ACTIVE object (then raise 409).

### R3-2 UPDATE-time unique-index violation → NameConflictError
- `update_channel` wraps the CAS UPDATE in `try/except IntegrityError`;
  only `"UNIQUE constraint failed"` (the
  `uq_channel_active_workspace_role_name` partial index) maps to
  `NameConflictError` (route → HTTP 409); every other integrity error
  (e.g. avatar FK) propagates unmasked.
- Deterministic concurrent two-channel rename-to-one-free-name test
  `test_concurrent_rename_to_one_free_name_exactly_one_wins`:
  - seeds two active channels (A, B), two sessions both read active,
  - both pause on a barrier, then both rename to `"THE SAME NAME"` with
    the same expected revision,
  - the test instruments `_find_active_by_name` and asserts BOTH pre-checks
    saw **no blocker** (proving the loser's failure comes from the
    UPDATE-time index backstop, not the pre-check),
  - exactly one `:ok` and one `:conflict`; exactly one active row holds
    the name.

### R3-3 Future-safe durable-job head tests
- `tests/test_durable_job_persistence.py::test_head_revision_is_durable_job_schema`
  now resolves the CURRENT head via
  `ScriptDirectory.get_current_head()`, asserts the upgraded DB version
  equals it, and proves `JOB_HEAD_REVISION` (`23b308b1fd0b`) is an
  ancestor via `walk_revisions`.
- `tests/test_durable_job_api.py::test_initialize_existing_s01_db_backs_up_before_upgrade`
  likewise compares the post-initialize revision to the dynamically
  resolved current head.
- The hard-coded `S03_HEAD_REVISION = "1c9f2a4b7d8e"` constant was
  removed; a NOTE explains that future migrations must not be hard-coded
  here.

## Required revalidation — real output

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_channel_crud.py` | **28 passed** |
| `python -m pytest -q tests/test_channel_crud.py tests/test_persistence_bootstrap.py tests/test_channel_workspace.py tests/test_durable_job_api.py::test_initialize_existing_s01_db_backs_up_before_upgrade tests/test_durable_job_persistence.py::test_head_revision_is_durable_job_schema` | **67 passed** |
| `python -m ruff check app tests` | All checks passed! |
| `python -m mypy app` | Success: no issues found in 55 source files |
| `git diff --check` | exit 0 |
| `git diff --stat app/api/routes/projects.py` | empty (zero-diff) |
| Full pytest gate-2 marker | **424 passed, 8 skipped, 7 deselected** (262.94s) |
| quality baseline (7 gates) | OVERALL PASS — run `20260804-022303` |

## Data-safety evidence

- `channels.json` SHA256
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` —
  unchanged.
- `docs/architecture/UI_UX_DESIGN_STANDARD.md` untouched.
- `docs/pm/sessions/S03-T01-channel-crud/PM_REVIEW.md` restored from HEAD
  (review history preserved).
- No `data/` directory — no scratch production database.
- `app/api/routes/projects.py` zero-diff.

## Changed files (correction round 3)

- MODIFIED `app/persistence/channels.py` — fresh SELECT re-read after
  zero-row archive CAS; IntegrityError→NameConflictError backstop on
  UPDATE
- MODIFIED `tests/test_channel_crud.py` — 2 new deterministic
  repository-level interleaving tests (archive race, rename race)
- MODIFIED `tests/test_durable_job_persistence.py` — dynamic current-head
  + S02 ancestry proof; removed S03_HEAD_REVISION constant
- MODIFIED `tests/test_durable_job_api.py` — dynamic current-head compare
- MODIFIED `docs/architecture/CHANNEL_API.md`, LOG.md, REPORT.md

## Deviations / limitations

1. Migration remains non-reversible (contract §7; backup restore).
2. The rename-race test instruments the pre-check (`_find_active_by_name`)
   via monkeypatch to prove the failure mode; it restores the original in
   a `finally` block.

## PM finalization

PM added one post-submission identity-map regression fix:
`populate_existing=True` on the lost-archive-CAS re-read, plus
`test_archive_loser_refreshes_a_strongly_cached_active_row`. Independent PM
validation then passed 3/3 focused race tests, 68/68 combined relevant tests,
and quality baseline run `20260804-022946` at 7/7. Final decision: APPROVED.

## Status

SUBMITTED — final correction round.  No commit, no roadmap/PRD edits.
