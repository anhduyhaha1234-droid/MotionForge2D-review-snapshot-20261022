# S03-T01 - PM Review

**Decision:** APPROVED
**Reviewer:** PM/Codex
**Approved:** 2026-08-04

## Review history

- Round 1 requested changes for active-only name uniqueness, atomic optimistic
  concurrency, guarded archive, workspace ownership, nullable clear semantics,
  one-transaction create, DTO null behavior, avatar metadata, and forbidden
  legacy-route edits.
- Round 2 requested changes for ORM/migration index parity, actionable avatar
  validation, non-null PATCH semantics, concurrent archive behavior, and
  migration FK/ancestry evidence.
- Round 3 requested changes for identity-map-safe archive re-read, concurrent
  rename conflict mapping, and future-safe Alembic head tests.
- After Hermes' final correction, PM found the archive race test still did not
  force a stale identity-map object. PM added `populate_existing=True` and a
  deterministic strong-cache regression test. This is the only PM code hotfix.

## Approval evidence

- Durable API provides list/read/create/update/archive with explicit workspace
  ownership and no hard-delete or JSON dual-write.
- Active channel names are atomically unique by workspace/role using
  `lower(name)` and an active-only partial unique index. ORM and migration DDL
  match; archived names can be reused.
- PATCH and first archive use database CAS; stale writes return 409. Concurrent
  create/rename/archive cases have regression coverage.
- Archive is idempotent and reference-preserving. Nullable metadata supports
  explicit clear; required fields have defined null behavior.
- Invalid avatar references return actionable 422 and cannot cross workspace.
- S02-to-S03 migration preserves rows/references, leaves foreign keys enabled,
  and passes `foreign_key_check`; S02 ancestry is proven dynamically.
- `app/api/routes/projects.py` has zero diff. No scratch production DB remains.
- `channels.json` SHA256 remains
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`.
- PM targeted rerun: 3 race tests PASS; combined relevant suite 68 PASS.
- PM independent baseline `20260804-022946`: **7/7 PASS**.
- Ruff, mypy, and `git diff --check`: PASS.

## Decision

S03-T01 meets its acceptance criteria and is approved for checkpoint. S03-T02
may start from this baseline.
