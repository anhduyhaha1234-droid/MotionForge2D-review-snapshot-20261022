# Repo git noise vs commit truth (MotionForge2D worktrees)

Measured repeatedly across the 2026-09-28 Phase-B wave: in these worktrees `git commit` / `git merge` /
`git pull` can print to stderr things like

- `fatal: bad object refs/codex/turn-diffs` (and similar bad-object refs), and
- geometric-repack / duplicate-ref noise,

**while the operation actually SUCCEEDS.** Workers disclosed this in at least three tasks (MF-END-06,
MF-END-08, MF-END-15 canonicals: "log bad-object/geometric-repack là pre-existing, commit OK").

## Rules

1. **Judge git results by state, never by stderr presence.** For every claimed commit read:
   `git log --oneline -2`, `git rev-parse HEAD^`, `git show --stat HEAD`, `git status --porcelain`.
   A commit is real iff the SHA exists with the expected parent and the porcelain is clean.
2. **A worker that discloses the noise ("pre-existing, commit OK") is behaving correctly** — keep the
   disclosure line in your ledger row / report. Do NOT spend a round "fixing" refs mid-wave, and do not
   let the noise inflate a failure grade.
3. **A commit that genuinely did not land is a different failure class:** `rev-parse` parent mismatch or a
   missing SHA. Handle it with shape-4 recovery (see `worker-lane-orchestration` SKILL.md rule 4 / its
   `references/task-dag-wave-dispatch.md` finishing-packet recipe): measure `porcelain` + the task's own
   test file yourself BEFORE assuming any work was lost, then resume the same session with a small packet.
4. Do not record "git is broken" anywhere; record the disclosure and the state check you performed instead.

## Where this bites

- Independent verify of a lane's commit (`git show --stat`) is the moment the noise appears; if you only
  grep stderr for "fatal" you will false-fail a green task.
- Same for the orchestrator's own transport merges (`git merge --no-ff <dep>` inside a new worktree): the
  merge can print repack noise and still create the merge commit — verify with `rev-parse HEAD` +
  `status --porcelain == 0` before writing the base sha into the guard JSON.
