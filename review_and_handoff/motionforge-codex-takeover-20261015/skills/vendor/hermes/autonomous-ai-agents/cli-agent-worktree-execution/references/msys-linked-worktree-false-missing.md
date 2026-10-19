# MSYS git-bash linked-worktree false "not a git repository" (verified 2026-09-17)

## Symptom

`git -C /c/Users/Admin/MotionForge2D-worktrees/<wt> rev-parse HEAD` fails with:

```
fatal: cannot change to '/c/Users/Admin/MotionForge2D-worktrees/<wt>': No such file or directory
```

…while the directory plainly EXISTS (`ls` shows it, `.git` file present).

## What it is

Recurring MSYS path-resolution quirk with linked worktrees (`.git` is a
`gitdir:` pointer file, not a directory). It is NOT a missing worktree, NOT a
dead owner, and NOT a reason to declare BLOCKED work. The existing skill
pitfall already covers the `git -C <abs>` form; this file records the full
recovery sequence proven on 2026-09-17 for two trees at once.

## Recovery sequence (in order)

1. `ls -la <wt>` — confirm the tree exists on disk.
2. `cat <wt>/.git` — expect `gitdir: C:/Users/Admin/MotionForge2D/.git/worktrees/<name>`.
   A pointer file (not a directory) confirms this quirk, not data loss.
3. `cd <wt> && git rev-parse HEAD` — plain relative git after `cd` works.
   Verify `git branch --show-current` and `git status --porcelain` the same way.
4. Never `rm` / re-clone / re-add the worktree on the basis of the `git -C`
   error alone.

## Verified instance

QA tree `s12-lc3-luna-qa` and INT tree `s12-lc3-luna-integration` both failed
via `git -C <abs>`; after `cd`, both returned the exact expected HEADs
(`5947088e…` / `2594de06…`), clean porcelain, correct branches.
