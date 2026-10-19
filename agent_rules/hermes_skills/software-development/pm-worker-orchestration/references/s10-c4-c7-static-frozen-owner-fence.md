# S10-C4 T01C-C7-STATIC — frozen-owner lint fence (verified 2026-08-30)

Context: C4 §8 demanded a LITERAL static acceptance — mypy exact-9-file
`Success: no issues found in 9 source files` AND Ruff `--select F` zero on
the nine production files plus ALL eight actual `tests/test_s10*.py`
(test_s10_chunk_plan, full_apply_api, full_apply_domain, full_apply_migration,
full_apply_workflow, multi_role_apply, partial_recompute, structural_compare).

## What happened

Worker T01C-C7 (owner `20260828_003035_859fe5`, `-m ocg/deepseek-v4-flash`,
same full prompt, static-only scope) reached:

- mypy exact 9-file: **literal PASS** — EXIT 0, "Success: no issues found in
  9 source files", no flags, no config weakening. Carry-forward from
  T03/T04A had been closed by their own owners in J2/J3 exactly as routed.
- targeted pytest ×2 fresh basetemp: 32 passed ×2.
- full `tests/test_s10*.py`: **197 passed**.
- git diff-check 0, status 45 allowlist+pre-existing, alembic single head,
  J1-v4 13/13, OpenAPI phantom 261/327/0dup — all green.
- Ruff F* on 9 prod + 8 tests: **EXIT 1, exactly ONE error**:
  `F841 Local variable 'sf' is assigned to but never used` →
  `tests/test_s10_full_apply_domain.py:172` in
  `test_cross_project_checkpoint_rejected` (`sf = _session_factory(db)` is
  never used; the test uses `Sf2 = _session_factory(db)` on the next line).

## Why it deadlocked

`tests/test_s10_full_apply_domain.py` is in **T01A's exclusive write-set**
(SESSION_REGISTRY line 13; T01A created the file at R0). T01A was NOT in the
C4 resume list (C4 §1 froze T01A/T01B/T02/T04B; only T01C/T03/T04A/T04C were
resumable). The C4 §8 text only said "errors in T03/T04A files must return to
those exact owners before J4" — it never anticipated an error in a FROZEN
owner's test file. The F841 is pre-existing (it was already counted inside
C3's "6 errors" review line) and was always going to block the literal §8
acceptance once the other five errors were closed by C6/J2/J3.

## Correct behaviors observed (encode these)

1. **Worker did NOT cross ownership** for a trivial 1-line fix. It reported
   `STATUS: BLOCKED_WITH_FINDINGS`, named the exact file:line, identified the
   owner from the registry (T01A), proposed the fix, and explicitly said it
   would not touch the file. This is the desired outcome — a 1-line P2 in a
   frozen owner's file is still that owner's file.
2. **Manager verified independently before routing**: ran
   `ruff check --select F tests/test_s10_full_apply_domain.py` alone
   (confirming the single error and that no other F* remains anywhere),
   checked the 9-prod+8-tests aggregate (exactly 1 error), and read the
   culprit lines to confirm the dead store.
3. **Manager did NOT unilaterally resume the frozen owner.** Options given
   to user/Codex: (a) authorize resuming T01A exact owner
   `20260827_234001_9d7f39` to delete the one line and re-verify, then J4 →
   T04C; or (b) `BLOCKED_SCOPE_EXPANSION` and wait. No self-fix, no silent
   scope expansion, no waiver.

## Manager-side preflight rule this exposes

When a correction prompt promises a LITERAL zero-error acceptance across ALL
S10 test files, do the SET-OWNERSHIP AUDIT at preflight, not at the gate:

- map each `tests/test_s10*.py` to its owning lane (registry write-set
  column or grep the lane TASK.md);
- if ANY test file belongs to a frozen owner, grep it for pre-existing lint
  debt (F401/F841/type-ignore) and surface the deadlock in the first
  heartbeat — ask for a narrow authorization (resume frozen owner for a
  static-only 1-line fix) BEFORE dispatching the static lane, so the run
  cannot end blocked on a known-foreseeable item.

## Commands used for the audit

```
python -m ruff check --select F tests/test_s10_full_apply_domain.py
python -m ruff check --select F <9 prod files> <8 test files>   # tail: Found 1 error.
sed -n '165,178p' tests/test_s10_full_apply_domain.py           # confirm dead store
python -m mypy <9 files> --ignore-missing-imports               # literal Success
```