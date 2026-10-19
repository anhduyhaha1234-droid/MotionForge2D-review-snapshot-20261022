# Cross-lane type contracts + pre-code inventory freeze (S12-R7, 2026-09-16)

Two manager-side rules from a two-manager parallel correction wave, each of which
prevented a failed or cross-contaminated lane.

## 1. A new error/type must subclass the base its catcher already maps

A lane that introduces a NEW exception class which will escape through ANOTHER
lane's file (or a shared dispatcher/classifier) must make it subclass the base
error that the existing mapping already handles — inside its OWN allowlist, via
the lazy-import pattern already present in that module. Then the existing typed
mapping holds and the other lane needs **no write at all**.

Case: the VAL lane added `PublicationInProgressError` for "claim arrived while a
publication section is held". The manager froze the rule that it must subclass
`app.persistence.s12_export.S12ExportError`, imported lazily inside the function
(the module already did this at five existing call sites). Every existing
`except S12ExportError` chain therefore yields the typed 4xx, and the `claim_run`
caller living in the RETRY lane's `app/workflow/s12_export_jobs.py` needed zero
change.

Manager procedure before freezing such a rule:

1. **Read the ACTUAL catch chain** of the path the error escapes through; do not
   assume it. In this case the manager's first hypothesis (the HTTP route's
   `except` handler) was WRONG — the real claim path is the durable-worker
   classifier. The frozen mandate survived because it was strictly compatible,
   and the owner proved `issubclass(...) is True` at runtime. Record the
   correction rather than silently keeping a wrong rationale.
2. **Prefer the resolution requiring zero writes in another lane.** A cross-lane
   edit needs its own minimal proposal first — never a silent patch.
3. **Require the owner to prove the mapping** (read the chain, plus a small test
   showing the typed outcome) in its turn report.

## 2. Freeze the executable inventory BEFORE any code

Before a correction turn may write, each owner submits:

- exact executable node IDs, including every parametrized variant;
- param IDs per variant;
- expected typed status plus the all-row/file delta per variant;
- raw output destination;
- proof that each new file does not already exist.

The manager re-hashes the submission, freezes it (`INVENTORY_FREEZE.json`), and
the node set may not shrink afterwards; missing rows are listed, never silently
skipped. This converts "did you fix it?" into a finite checklist both sides can
audit, and makes omission detectable.

Scale that this enables: RETRY 58 nodes (46 retained + 12 new) + VAL 36 (28
retained + 8 new) = 94 frozen, then 298 node instances re-run by the manager on
the frozen bytes — reported as 0 failures / 0 new skips / 0 weakened assertions,
a measured fact rather than a claim.

## 3. Assert write-set disjointness on the ACTUAL commits

Do not prove disjointness from the allowlist text. After both lanes commit, diff
each lane's branch against the wave base and assert zero overlapping paths, and
re-confirm the read-only protected file (here `app/persistence/s12_export.py`
was READ-ONLY for one lane while the other owned only its lease/claim portions).
Grep the protected file's diff for the other lane's semantic keywords — e.g.
`lineage|identity|orphan|sibling|generation` returning zero added lines is the
proof that lease-only changes did not bleed into identity semantics.

## 4. Disclosure beats a clean narrative

Both an upstream 502 that cut two turns and a self-reported non-destructive stray
path by one owner were recorded as incidents in the handoff rather than smoothed
over. One non-destructive, self-disclosed scope deviation does not justify owner
replacement; a second destructive or out-of-scope violation in the same lineage
does. Put fact corrections (including corrections to the manager's own earlier
analysis) in the handoff JSON so a reviewer can see the reasoning was tested.
