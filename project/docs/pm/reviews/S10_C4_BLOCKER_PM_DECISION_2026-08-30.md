# S10-C4 — Codex PM blocker decision (2026-08-30)

## Verdict

`S10-C4 = CONTINUATION_AUTHORIZED / NOT_APPROVED`.

Hermes correctly stopped at `BLOCKED_SCOPE_EXPANSION`: the only current J4
failure is in the exclusive write-set of frozen owner S10-T01A, while the active
T01C static owner had no authority to edit that file. Codex does not waive the
binary Ruff gate and authorizes the smallest ownership-correct correction:
resume exact S10-T01A owner session `20260827_234001_9d7f39`, remove the one
dead assignment, re-run J4, and continue to T04C-C3 only if J4 is exactly green.

This is a scope decision inside C4, not an S10 approval and not a new correction
sprint. S11/S12/S13 production remains unopened.

## Independent live-state evidence

- Integration authority:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
  `codex/s08-integration`, HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; dirty S10 write-set retained.
- MAIN remains protected at branch `master`, HEAD
  `f0ee4bd11f83fb6fed8c9a8f3924e85b903c3d3b`.
- `MOTIONFORGE_DATABASE_URL=UNSET`; no relevant S10/Hermes writer process was
  found during the decision audit.
- Direct source inspection confirms
  `tests/test_s10_full_apply_domain.py:172` assigns
  `sf = _session_factory(db)` and never reads that local; the test creates and
  uses `Sf2` at lines 174-181.
- Independent exact Ruff rerun over the nine S10 production files plus all
  eight `tests/test_s10*.py` files returned one and only one error:
  `F841` at `tests/test_s10_full_apply_domain.py:172`.
- Independent focused behavior check on a fresh isolated basetemp,
  `test_cross_project_checkpoint_rejected`, passed `1 passed` in 5.71s. This
  confirms the dead assignment does not supply test behavior or setup authority.
- Session Registry row 13 assigns
  `tests/test_s10_full_apply_domain.py` to S10-T01A. The registry dispatch log
  resolves that task's exact owner as `20260827_234001_9d7f39`.
- C4 evidence shows the exact nine-file mypy gate already reports
  `Success: no issues found in 9 source files`, targeted T01C tests passed
  32/32 twice, and the current full S10 manager run passed 197 tests. Those
  retained results are not treated as final Codex sprint approval; all required
  exit gates must be rerun after the one-line correction and T04C-C3.

## Finding and required correction

### P2 — foreign-owned dead assignment blocks the literal J4 gate

- **File:** `tests/test_s10_full_apply_domain.py:172`
- **Actual:** local `sf` is assigned but unused; exact Ruff gate exits 1.
- **Expected:** Ruff `--select F` exits 0 over the frozen nine-production plus
  eight-test file set, with no waiver or config weakening.
- **Impact:** no product behavior defect, but C4 cannot truthfully open T04C or
  claim sprint exit while a frozen binary gate is red.
- **Owner:** S10-T01A, exact session `20260827_234001_9d7f39`.
- **Correction:** delete only the dead assignment at line 172. Do not rename
  `Sf2`, rewrite the test, change assertions, or touch production code.
- **Verification:** focused domain test twice on fresh roots; exact Ruff gate;
  exact nine-file mypy; full S10 gate; diff-check; ownership/status audit.

## Downstream decision

After the T01A correction, Hermes must:

1. mark J4 green only if Ruff is literally zero and all retained static/test
   gates remain green;
2. resume exact T04C owner `20260828_023122_76b87e` for two new C4 vertical
   runs under the current build, without direct DB writes/requeue helpers;
3. route any in-scope product defect to its exact existing owner, never patch it
   in the Manager or T04C harness session;
4. rerun the complete C4 exit matrix and stop at
   `S10-C4 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`.

The bounded continuation prompt is:
`docs/pm/prompts/S10_C4A_T01A_STATIC_UNBLOCK_AND_EXIT_MANAGER_2026-08-30.md`.
