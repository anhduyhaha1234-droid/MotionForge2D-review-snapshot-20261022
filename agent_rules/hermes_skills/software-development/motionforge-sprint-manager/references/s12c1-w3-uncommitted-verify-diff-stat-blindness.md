# Uncommitted-verify: `git diff --stat` is blind to untracked files (S12-C1 W3, 2026-09-08)

Observed: T03B worktree (`20260907_125027_0c90f3`) held a modified
`app/services/s12_export/runner.py` (+113) plus a NEW 457-line
`tests/s12/s12-t03b/test_c1_closure.py` (13 `def test` nodes, C10–C14).
`git diff --stat` reported **1 file changed** — the untracked test file was
invisible. Only `git status --porcelain=v1` showed the full truth:
`M runner.py` + `?? test_c1_closure.py`.

Rule: on UNCOMMITTED worker state, never verify with `diff --stat` alone.
Run the triple every time, in this order:

1. `git status --porcelain=v1 -uall` — allowlist check covers ` M` AND `??`.
2. `git diff --stat` — magnitude of tracked modifications.
3. File-level proof for each `??` test file: `wc -l` + `grep -c "^def test"`.

(`git diff --stat` / `git show --stat` remain complete on COMMITTED tips —
there are no untracked files by definition. The blindness applies only to
pre-commit verification.)

Pointer request for curator: one line under the Manager skill's verify
section referencing this file
(`references/s12c1-w3-uncommitted-verify-diff-stat-blindness.md`). Direct
SKILL.md patch avoided (100KB file, prior read-before-write refusal on
record — same reason as in `references/s12c1-w2w3-liveness-and-cli-path.md`).
