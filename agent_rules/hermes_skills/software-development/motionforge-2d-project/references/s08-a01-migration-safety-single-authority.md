# S08-A01 / A01-C1 — SQLite migration safety + single-authority taxonomy

Session-verified techniques from widening `ObjectRole.kind`
`character|prop|other` → seven Source-Locked 2D kinds
(S08-A01) then hardening it after Codex CHANGES_REQUESTED (A01-C1).

## 1. Surgical `writable_schema` CHECK-literal edit (NOT batch_alter_table)

Widening a column CHECK on SQLite through Alembic:
- **Do NOT use `batch_alter_table`** for this. A batch rebuild recovers the
  table via reflection and converts the COLUMN-level FK added by an earlier
  RAW `ALTER TABLE ADD COLUMN` (e.g. `f2a3b4c5d6e7` added `source_job_id
  REFERENCES job(id)`) into a TABLE-level `FOREIGN KEY(...)` constraint.
  SQLite 3.45 then refuses that table's historical `DROP COLUMN
  source_job_id` (f2 downgrade) with `unknown column ... in foreign key
  definition` — breaking the WHOLE downgrade chain.
- Instead: surgical single-string edit of `sqlite_master.sql`:
  1. `SELECT sql FROM sqlite_master WHERE type='table' AND name='<t>'`
  2. **Assert the needle CHECK literal appears EXACTLY ONCE** — `count(needle)
     != 1 → raise` (never let `str.replace` silently replace multiple).
  3. `PRAGMA writable_schema = ON` → `UPDATE sqlite_master SET sql=:sql` →
     `PRAGMA writable_schema = OFF`.
  4. Bump `schema_version` (`PRAGMA schema_version`) so SQLite re-parses the
     edited DDL immediately.
  5. Run `PRAGMA integrity_check` (expect `ok`) + `PRAGMA foreign_key_check`
     (expect 0 rows) after EVERY mutation decision path.

## 2. Fail-closed downgrade (F1)

A downgrade that narrows a CHECK is data-unsafe if any row now violates the
narrower CHECK:
- `downgrade()` runs the guard query FIRST, BEFORE any schema/data mutation:
  `SELECT COUNT(*) FROM <t> WHERE kind NOT IN (<legacy kinds>)` → if > 0,
  raise → `alembic downgrade` exits non-zero, revision/DDL/rows/indexes/FKs
  stay byte-identical.
- NEVER silently coerce a new value to a legacy one (`source_overlay` → `other`).
- Tests: (a) legacy-3-kind DB round-trips upgrade→downgrade→upgrade
  byte-identical; (b) a DB with new-kind rows is REFUSED on downgrade
  atomically (version stays the 7-kind head, DDL/rows unchanged, integrity
  ok); (c) after removing the offending row, downgrade succeeds.

## 3. Single runtime authority for a taxonomy (F3)

- Keep ONE canonical tuple in `app/persistence/models.py`
  (`OBJECT_KINDS = (character, prop, background, foreground, graphic,
  source_overlay, other)`).
- Derive BOTH the ORM CHECK literal (`OBJECT_KIND_CHECK_SQL =
  "kind IN (" + ",".join("'"+k+"'" for k in OBJECT_KINDS) + ")"`) and the
  validation regex (`OBJECT_KIND_PATTERN = "^(" + "|".join(re.escape(k) for k
  in OBJECT_KINDS) + ")$"`) from that constant. Then Pydantic schemas import
  the derived PATTERN — no hardcoded regex literal duplicated across files.
- The MIGRATION keeps its own frozen literal snapshot (migrations must be
  immutable/independent) — the C1 test asserts the runtime-derived checksum
  equals the frozen `_NEW_CHECK` so the two cannot drift.
- Remove secondary "default" copies of a policy constant when every caller can
  pass the canonical one (e.g. drop `REMOVAL_ONLY_KINDS_DEFAULT` and make the
  kwarg REQUIRED).

## 4. Shared invariant between execute and preview (F2)

A "preview must fail like execute" requirement is best served by ONE helper
(`merge_kind_conflict_message(...)`) imported by BOTH the executing repository
(`apply_merge`) and the impact-preview path (`compute_impact`) — the message
and the refusal condition live in exactly one place, so execute and preview
cannot drift. Preview must be strictly read-only (zero durable mutation — no
pending correction/operation row created on the reject path).

## Manager verification notes

- Independent F1 proof is a standalone script (fresh DB @head → insert a
  new-kind row with full valid FK chain → `alembic downgrade` must rc≠0 with
  the refusal message; verify version/DDL/rows/integrity unchanged and FK
  violations = 0 → delete the row → downgrade must rc=0 back to 3-kind).
- Driving alembic from a script: pass `["python","-m","alembic","upgrade",
  "head"]` as separate argv items (a joined `"upgrade head"` string exits
  rc=2 silently). Seed FK parents with CHECK-valid enum values (a bad
  `status` makes `INSERT OR IGNORE` drop the row → phantom `foreign_key_check`
  violations blamed on the migration, not your seed).
