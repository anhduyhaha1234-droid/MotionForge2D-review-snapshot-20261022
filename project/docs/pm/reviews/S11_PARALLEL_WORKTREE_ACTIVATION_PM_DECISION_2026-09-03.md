# S11 Parallel-Worktree Activation — PM Decision — 2026-09-03

## Decision

`S11-T02..T06 = PRODUCTION_DISPATCH_AUTHORIZED` from a clean, pushed,
sprint-specific integration branch. The previous dirty-tree one-writer limit is
superseded for S11 implementation; the S10 worktree remains read-only evidence.

## Verified checkpoint

- Approved-scope commit: `4cec376bd7589bfd5bbd8c2260fdd63b751aca73`.
- Remote verified: `origin/codex/s08-integration` equals that commit.
- Staged scope: 88 approved source/migration/test/harness/session files.
- Excluded: `.codex-review`, `.playwright-cli`, generated Playwright report and
  test-results, ad-hoc probes, cache/pyc, `.bak`, destroyed and reconstructed
  test copies.
- Backend: 290 tests passed in the broad run; the only failure was Windows
  `WinError 206` caused by an overlong 87-character basetemp before application
  logic. The exact long-path test passed with a 48-character basetemp, so the
  reviewed behavior total is 291/291.
- Frontend: `tsc --noEmit` and scoped S10 ESLint passed.

## Clean S11 activation

- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Branch: `codex/s11-integration`.
- Remote/local activation HEAD:
  `7751598214eedb6b72e3783e39a2a408721abe40`.
- Porcelain: clean.
- Sprint contract SHA:
  `591FAB3F9354DC9EF869FEDE5F2FA4AD760B04EF9334F558BACFA06CBB3558CF`.

## Safe maximum concurrency

- W6: T03B/T03C/T03D/T03E, four isolated implementation workers.
- W9: T04A/T06B, two isolated implementation workers.
- W12: T04D/T05A, two isolated implementation workers.
- Other waves: one worker because of direct dependencies.
- Every Task ID has one branch, clean worktree and new Hermes session at the
  same immutable wave base. Corrections resume the exact owner/branch.
- One operational owner `S11-INT01` performs only fast-forward/conflict-free Git
  integration. It cannot edit code or resolve conflicts manually. Canonical is
  pushed only after a green combined wave gate.

## Session Opening Proposal

- Authority: `AUTHORIZED_TO_DISPATCH`.
- Open one new S11 Manager chat and one new Git-only `S11-INT01` session.
- Open W1 `S11-T02A` in a new task worktree from activation HEAD. W2-W5 remain
  dependency-blocked; W6 opens all four owners together once T03A is verified
  and integrated.
- Manager, integrator and all new product workers use custom
  `ocg/deepseek-v4-flash`, requested reasoning `max`, fallback disabled, TTFB
  900 seconds. A correction never creates a replacement owner.
- Binding prompt:
  `docs/pm/prompts/S11_T02_T06_FULL_SPRINT_MANAGER_2026-09-03.md`, SHA
  `57E9434AC7E8DF3A71C2437F9B100F72F024DDC8CC2566C95AF50F433B5E363E`.

## Non-blocking Git note

`git fetch/fsck` sees one unrelated local Codex turn-capture ref whose content
is the zero object ID. It was preserved rather than deleted. Direct GitHub
`ls-remote` and push verification succeeded for both checkpoint branches; this
does not affect the S11 canonical branch or product bytes.
