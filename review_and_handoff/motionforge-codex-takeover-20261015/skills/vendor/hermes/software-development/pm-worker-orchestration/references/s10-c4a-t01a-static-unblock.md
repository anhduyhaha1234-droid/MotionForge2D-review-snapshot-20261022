# S10-C4A — T01A static unblock via Codex decision (verified 2026-08-30)

## Context
S10-C4 J3/C7 deadlocked on exactly one Ruff F841 in `tests/test_s10_full_apply_domain.py:172`
(`sf = _session_factory(db)` dead assignment; test uses `Sf2`), a file owned by frozen
lane S10-T01A (registry row 13, exact session `20260827_234001_9d7f39`). Worker T01C
correctly refused to touch it; Manager stopped `BLOCKED_SCOPE_EXPANSION` and asked
user/Codex. User: "để codex quyết định đi".

## Codex decision packet shape (`reviews/S10_C4_BLOCKER_PM_DECISION_2026-08-30.md`)
- Verdict: `S10-C4 = CONTINUATION_AUTHORIZED / NOT_APPROVED` (inside C4, not C5, not approval).
- Independent evidence: Codex ran the exact Ruff 17-file set themselves → one and only
  one error (F841 @:172); focused `test_cross_project_checkpoint_rejected` passed 1-in-5.71s
  on fresh basetemp (proves the dead line carries no behavior/authority).
- Correction: delete ONLY line 172; "Do not rename `Sf2`, rewrite the test, change
  assertions, or touch production code."
- Downstream: mark J4 green only if Ruff literally zero + all retained static/test gates
  green → resume T04C `20260828_023122_76b87e` → full C4 exit matrix →
  `S10-C4 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`.
- Bounded continuation prompt also saved as `prompts/S10_C4A_T01A_STATIC_UNBLOCK_AND_EXIT_MANAGER_*.md`.

## Manager execution that closed the loop
1. Required reading = full rules re-read (dedup confirmed SHA
   `987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`, 180 lines) +
   decision packet + full T01A TASK/LOG/REPORT (first time this lane's docs were read —
   the frozen lane's packet must be read before resuming it).
2. Preflight C4A (all measured): worktree `codex/s08-integration` HEAD
   `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7` 45 dirty; MAIN `master` `f0ee4bd…` 80 dirty
   (foreign, untouched); MOTIONFORGE_DATABASE_URL UNSET; zero S10 writer (proc_audit.ps1:
   only hermes desktop 5628 + serve 5280); J1-v4 13/13 + EOL PASS (scripts/j1v4_rehash.py);
   alembic single head a10b11c12d3e.
3. Baseline proof per prompt §3.6: literal 9-file mypy
   `Success: no issues found in 9 source files`; exact 17-file Ruff =
   **exactly the one known F841 @:172**, nothing new. (grep -c zero-exit trap in sweep
   chains: append `|| true` or split gates.)
4. Prompt `output/s10/c4a/t01a-static-unblock/prompt.txt`: exclusive implementation write =
   `tests/test_s10_full_apply_domain.py` ONE line deletion; forbiddens = no `Sf2` rename,
   no reformat/rewrite, no assertion/fixture/behavior change, no `app/**`, no other test,
   no migration/model/frontend; acceptance = git diff shows only that line gone + focused
   domain ×2 fresh roots + migration ×1 + exact Ruff 17-file zero + literal mypy zero +
   full `tests/test_s10*.py` green + diff-check 0 + alembic/J1 retained.
5. Dispatch (same full-model-id route, no provider flag):
   `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume 20260827_234001_9d7f39 -z "$(cat output/s10/c4a/t01a-static-unblock/prompt.txt)" -m ocg/deepseek-v4-flash --yolo`
   background, notify_on_complete, log `dispatch.log`.

## Reusable rules
- A frozen-owner deadlock is NOT a manager decision: escalate with a precise
  one-finding packet (file:line, owner from registry, proposed one-line fix, no
  self-fix, no silent frozen resume).
- When Codex authorizes, the decision packet IS the new authority — read it fully,
  preflight-verify its cited baseline yourself, and pin the edit even more narrowly
  than Codex did (explicit forbiddens for collateral touches).
- The corrected one-line test change can flip `0 failed` suites; always re-run the
  full S10 gate after the static fix, not just the focused file.

## Owner/session ledger (C4A)
- T01A frozen owner resumed: `20260827_234001_9d7f39` (route `ocg/deepseek-v4-flash`).
- Upstream verified: J1 (T01C-C6) 179 full S10, J2 (T03-C4) 18×2 + 78 retained, J3
  (T04A-C4) 54×2 + 96 retained.
- C7 static was green except the one foreign F841 (mypy literal zero, 197 full S10).
- Next: J4 gate → T04C-C3 (`20260828_023122_76b87e`) → C4 exit matrix.