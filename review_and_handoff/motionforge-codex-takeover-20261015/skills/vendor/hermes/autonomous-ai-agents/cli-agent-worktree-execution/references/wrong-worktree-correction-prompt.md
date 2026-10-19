# Wrong-worktree correction prompt (template, verified 2026-08-05)

Adapted from the S06-T05 correction issued by Codex/PM after files landed in
the MAIN repo instead of the review worktree. Use this shape when a recovery
agent must undo a misplacement and redo the task on the approved base.

```
<WORKDIR GUARD> (see SKILL.md — pwd + git rev-parse --show-toplevel, stop
WRONG_WORKTREE without writing if it differs from the expected root)

<TASK> CORRECTION — WRONG WORKTREE RECOVERY

Expected root:
<C:\...\worktrees\<wt>>

First verify Get-Location and git rev-parse --show-toplevel. If either differs
from the expected root, stop WRONG_WORKTREE without writing.

Read:
- docs/pm/SESSION_PROTOCOL.md
- <dependency task> PM_REVIEW/REPORT
- <approved API task> TASK/REPORT
- <this task> TASK
- <this task>/INCIDENT_REPORT_WORKTREE_MAIN.md (if present)

The current review worktree was corrupted by copying older main-tree
<module> files. output/backup-pre-copy contains the pre-incident approved
<Sprint>/R<xx> state.

Do not reset, checkout, clean, delete or touch main. Do not copy directories.

Finite correction:
1. Compare every current file against output/backup-pre-copy.
2. Restore exactly the N overwritten approved files from backup-pre-copy,
   preserving all unrelated files.
3. Verify the original M-test <suite> passes before <task> work.
4. Reimplement <task> only on top of that restored approved state.
5. <scope-only> unless a new concrete blocker is reported. Use the existing
   <flat endpoint> and typed API/content_url/validation contracts.
6. Remove the new weaker <nested endpoint> and do not replace <approved> routes.
7. Do not add <forbidden controls>.
8. Add focused <frontend> interaction tests for <confirmation, success/refetch,
   422, 409 and immutable state>.
9. Run desktop and 390px visual QA.
10. Run the actual scripts/quality-baseline.ps1 and record its Run ID.
11. REPORT=SUBMITTED, never APPROVED.

Mandatory regression:
<tests/test_a.py>
<tests/test_b.py>
plus the focused <task> frontend tests.
```

Key mechanics that made this work:
- The WORKDIR GUARD is the FIRST instruction — it forces the recovery agent to
  prove it is in the right tree before any write.
- The backup (`output/backup-pre-copy/`) was taken BEFORE the bad copy — always
  snapshot the target tree before any cross-tree copy.
- The correction explicitly forbids copy-over from main ("Do not copy
  directories") — the wrong tree is not the source of truth.
- Quarantine corrupt artifacts (a test written against forbidden endpoints was
  moved to output/quarantine-t05-corrupt/) rather than kept.
- The regression list names exact test files; the Run ID from
  quality-baseline.ps1 must be recorded as evidence.
