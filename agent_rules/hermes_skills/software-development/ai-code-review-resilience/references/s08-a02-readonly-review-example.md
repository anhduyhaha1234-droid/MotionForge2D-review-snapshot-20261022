# Worked example: focused read-only review of the S08-A02 structural-evidence core

Session evidence 2026-08: independent READ-ONLY review of
`MotionForge2D-worktrees/s08-integration` covering
`app/persistence/models.py`, `app/persistence/structural_evidence.py`,
`migrations/versions/a0b1c2d3e4f5_s08_a02_structural_evidence.py`,
and three test files. Deliverable: a P0/P1/P2 findings list with
vector + why-it-matters + missing-negative-test per finding.

## How the P0 was found (the technique that paid off)

The migration still declared `ondelete="CASCADE"` for
`occurrence_segment.role_id` while the ORM had been updated to RESTRICT
(C1-F7). This was NOT found by running tests — it was found by grepping
`ondelete=` in BOTH the migration file and the ORM model and diffing the
two lists. A parity test (`test_migration_orm_parity`) compares FK options
via inspector, so this mismatch is a LIVE test failure on the next suite
run — exactly what makes it P0 rather than a latent gap.

Working diff command:
```bash
grep -n 'ondelete' migrations/versions/<rev>_*.py
grep -n 'ondelete' app/persistence/models.py
```
Compare per-FK. Any CASCADE vs RESTRICT asymmetry that the parity test
compares = P0.

## Findings shape (what a good finding looks like)

```
F0 — P0 — Migration still CASCADEs occurrence_segment.role_id; ORM says RESTRICT
- Vector: migrations/... line 156 `sa.ForeignKey("object_role.id", ondelete="CASCADE")`
  vs models.py line 1655 `ForeignKey("object_role.id", ondelete="RESTRICT")`
- Why it matters: every Alembic-built DB silently cascades role deletion into
  segment history; F11 parity test fails live.
- Missing negative test: none pins per-FK ondelete; parity test would catch it if run.
- Fix: change migration line 156 to RESTRICT.
```

## Recurring bug classes found in this core (mini checklist)

1. **idempotency equivalence helpers omitting identity fields** — segment
   helper compared ~25 fields incl. identity; motion/occlusion/contact
   helpers compared only payload/conf fields, omitting segment id, endpoint
   ids, contact_kind, start_frame. Replay with a different segment bound the
   key to the wrong row silently.
2. **generation `!=` instead of strict advance** — `supersede_segment` refused
   only equality; "must advance" message but code permits backward gens.
3. **range containment only at create, never re-validated on update** — shrink
   a segment after attaching motion/edge rows → orphaned out-of-range evidence.
4. **time containment missing entirely** — `_assert_range_within` took frames
   only; `start_time_ms`/`end_time_ms` never checked against the segment.
5. **ownership checks minimal on replay/update paths** — mask artifact checked
   for existence + workspace but not `kind='image'`/`state='ready'`.
6. **logical_id caller-arbitrary, not in the active-identity index** — two
   unrelated segments can share one lineage key; `get_segment_by_logical_id`
   conflates them.
7. **lineage walker silently dropping branches** — back-walk used `.scalar()`
   over `superseded_by_id == X`; two predecessors → one successor picks one
   arbitrarily.

## What was declared SOUND (close the review this way)

- F1/F8 CAS: stale revision refused with zero mutation, stable conflict.
- F3 partial unique index `uq_occurrence_segment_active_identity
  (WHERE superseded_by_id IS NULL)` enforced by SQLite 3.45.
- F4 generation authority delegated to the existing repository (SHA-aware),
  not a naive max+1 copy.
- F5 ownership chain validated BEFORE flush, zero rows on failure.
- F6 fail-closed JSON parsing (no default-on-failure).
- AC6 fail-closed downgrade: refuses before any DDL if rows exist.
- Test suite: 30 domain tests + migration parity + phone scenario were real
  and isolated (temp DBs, real SQLite FK/CHECK enforcement).

## Review logistics that worked

- Read files END-TO-END first (migration 661 L, models block, 2141-L repo,
  all three tests) — findings reference exact lines from fresh reads, not
  memory.
- Verify every quoted line by re-grepping the file (line numbers drift).
- Batch independent reads in one turn to cut round-trips.
- Check for absent APIs explicitly (grep `def delete|archive|trash|purge`)
  — a durable-delete policy with no delete method at all is itself a finding.
- Use a todo or numbered findings list; dense, actionable, no filler.