# MF2D lessons — SQLite/Alembic constraint changes + stale guard pins

Measured 2026-09-28 (MF-END-02). Reusable for any MF2D migration task.

## 1. batch_alter_table CANNOT rebuild a table that has child rows (FK pragma ON)

`op.batch_alter_table(...)` with `create_check_constraint` (or anything SQLite
can't ALTER natively) forces a copy-and-move rebuild. The rebuild does
`DROP TABLE <t>` — and under the domain contract's `PRAGMA foreign_keys=ON`
(on every connection via `create_engine_for_path`), the implicit delete
fails with `IntegrityError: FOREIGN KEY constraint failed` as soon as any
child row references `<t>` (measured on `character_pack_version` with
`character_asset.pack_version_id` + `character.default_version_id`).

Gotchas discovered while proving this:
- batch `add_column` ALONE succeeds — alembic passes it through as native
  `ALTER TABLE ADD COLUMN`, NO rebuild. Only the CHECK forces the rebuild.
  A probe that omits the CHECK will falsely "prove" batch is safe.
- The failed batch leaves the table intact (DDL + rows unchanged); no
  leftover `_alembic_tmp_*` table in the measured case.

**Safe pattern (house technique, f7a8b9c0d1e2 precedent):**
1. `op.add_column` ×N — native, no rebuild.
2. Append CHECKs via surgical `PRAGMA writable_schema` edit of the stored
   DDL: anchor on the single tail constraint + `)`; assert needle count == 1;
   fail closed on ambiguity; bump `PRAGMA schema_version`; then assert
   `PRAGMA integrity_check` == ok + `foreign_key_check` empty.
3. Downgrade: remove the exact appended block (count == 1) FIRST, then
   `op.drop_column` ×N. Native DROP COLUMN restores the stored DDL
   byte-identical (SQLite 3.45) and preserves rows.
4. Fail-closed pre-checks both ways: existing rows must satisfy the new
   CHECKs before the edit; downgrade must refuse (zero mutation) when rows
   carry data the dropped columns would orphan.

## 2. Keep model ↔ migration CHECK literals byte-identical

`models.py` derives `*_CHECK_SQL` from a single-authority tuple with NO space
after commas (`"x IN ('a','b')"`). The migration freezes the same literal so
the writable_schema needle matches EXACTLY ONCE. Divergence = silent
"needle not found" failures later.

## 3. MF2D launch guard pins can be STALE — always measure, then disclose

MF-END-02 launch pinned `down_revision = f7a8b9c0d1e2` ("sole head") and a
baseline of "127 passed/1 skipped" for `tests/product_delivery`. Measured
truth: sole head = `d4e5f6a7b8c9` (task tree AND PRODUCT tree, via
`alembic heads`), baseline = 49 passed/1 skipped (twice, incl. a
`git archive HEAD` base tree; the dir does not even exist at PRODUCT base).
Rules applied:
- Follow the ACCEPTANCE ("one revision chains the live head"), keep the
  pinned filename/revision id verbatim, chain the MEASURED head, and write
  the conflict into the migration docstring + REPORT §discrepancies.
- Never "fix" a stale pin by silently editing it — measure, decide by the
  binary acceptance, disclose with raw evidence.

## 4. Evidence-ledger hash staleness

An append-only `commands.jsonl` gains a row AFTER every harnessed command,
so a pinned sha256 for it in `results.json` is always one row stale by
design. Index it by ROW COUNT + a note, and regenerate `results.json` as the
LAST harnessed step (reports go stale the moment a later command runs —
same family as discipline pitfall #50).

## 5. Regression proof without touching the worktree

To decide "pre-existing vs regression" for tests outside the gate:
`git archive HEAD | tar -x -C <temp>` gives the exact base bytes; run the
same test files in BOTH trees and compare counts. `5 failed/51 passed ==
5 failed/51 passed` is a clean pair; a single run cannot answer the question.
