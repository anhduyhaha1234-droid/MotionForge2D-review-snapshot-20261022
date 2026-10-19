# Manager Verification of a Taxonomy/Migration Task — S08-A01 Runbook

Verified 2026-08-19 on MotionForge2D S08-A01 (Source-Locked 2D Role Taxonomy
Bridge). Use as the manager post-writer-exit checklist for any task whose ACs
touch a DB migration + canonical enum + API + frontend filter surface.

## Sequence that worked (in order)

1. **Tree-stable check before touching anything**: `git branch --show-current`,
   `git rev-parse HEAD`, `git status --short | wc -l` — confirm against the
   packet's recorded baseline (+ expected packet files). Then `wmic process`
   grep for the writer's session tag to confirm the worker really exited.
2. **Audit changed files vs allowlist** by mtime window, not `git diff`:
   `find app tests migrations frontend/src docs/pm sessions -newermt "<writer_start>" ! -newermt "<writer_end>" -type f`.
   The worktree is dirty by design (hundreds of pre-existing sprint entries), so
   `git diff` is noise; mtime-window is the only precise attribution.
3. **Read REPORT.md fully but verify independently** — especially the migration
   round-trip and the out-of-allowlist change list (pitfall 12).
4. **Independent migration round-trip** on a fresh temp DB (see below).
5. **Independent pytest** — focused new suite first (fast fail), then full
   sprint set, then cross-sprint regressions. Each >180s run goes to
   `terminal(background=true, notify_on_complete=true)`.
6. **Frontend**: `npx tsc --noEmit`, `npx eslint` on touched paths, `npm run
   build` (background), Playwright `.last-run.json` `status=passed`, then
   VERIFY THE SCREENSHOTS with vision_analyze (don't trust file presence).
7. **Protected hashes** before AND after; **ports** NO_LISTENERS after.
8. Append manager verdict to LOG.md + REPORT.md; status exactly
   `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` (or PENDING_BRIDGE_REVIEW).
   Never APPROVED.

## Migration round-trip recipe (SQLite + Alembic, fresh temp root)

```python
# Build a faithful PRE-migration DB at the OLD head, seed real rows, copy it
# as "the existing DB", then upgrade -> checksum -> downgrade -> checksum ->
# upgrade -> checksum. Rows must be byte-identical every step.
```

- **Seed REAL rows before copying.** Print per-table `SELECT COUNT(*)` for the
  object tables after seeding. If the printed row counts are all 0, the seed
  silently failed (columns guessed wrong / inserts swallowed) — FIX before
  trusting any "round-trip OK". A vacuous empty-DB round-trip still prints OK.
- **Introspect columns, don't assume the ORM shape**: `PRAGMA table_info
  (<table>)` on the migrated DB (e.g. `video_item` had no `source_kind`;
  `object_role_artifact` had no `sha256`/`size_bytes`). Use the actual columns.
- **Checksum every row of every object table** with `ORDER BY rowid`; assert
  equal before/after upgrade and before/after downgrade. `e3b0c442…` = empty.
- Use `MOTIONFORGE_DATABASE_URL=sqlite:///<abs>` inline for each alembic run,
  then `unset` + verify `echo $VAR` prints empty. A leaked env var silently
  redirects every later alembic invocation (see project skill).

## Summary of verified results (S08-A01)

- Migration `f7a8b9c0d1e2` (after `f6a7b8c9d0e1`) = surgical `PRAGMA
  writable_schema` CHECK-literal edit, deliberately NOT `batch_alter_table`
  (a batch rebuild converts a column-level FK into table-level, which SQLite
  3.45 refuses to DROP COLUMN on downgrade → breaks the chain). Round-trip OK.
- Focused 63 passed / full S08 set 294 passed / cross-sprint 357 passed;
  tsc/eslint/build 0; Playwright 7/7; baseline 7/7 (Gate 2: 1119 passed).
- Deviation: 3 files outside literal allowlist, all AC4/AC5-required, minimal,
  correct — escalated non-blocking (pitfall 12).
