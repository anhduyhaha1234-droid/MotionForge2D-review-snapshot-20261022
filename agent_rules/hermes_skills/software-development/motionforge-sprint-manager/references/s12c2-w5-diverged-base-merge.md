# S12-C2 W5 — diverged owner branch: INT01 merge wave-base INTO the owner branch

Session: 2026-09-09 S12-C2, W4→W5 handoff (T05 frontend lane).

## Topology that breaks ff-only

- Canonical advanced to `48dea7e` (T03C addendum: result/media endpoints merged).
- T05 owner committed `f02055d` on the OLD base `1d6e5ad` (parent == base before
  the addendum). T05 worktree was clean, but its branch had DIVERGED from
  canonical: both `f02055d` and `48dea7e` share merge-base `1d6e5ad`.
- `git merge --ff-only 48dea7e` on the T05 branch → exit 128 (not a file
  conflict — a topology impossibility). INT01 correctly kept the failed
  ledger row (seq 123) as evidence, left the branch untouched, and reported
  two options instead of guessing.

## The authorized move (prompt §3 basis)

Rules §8.1 / S12-C2 prompt §3 explicitly allow the integrator to
"merge a pushed dependency wave-base into a clean existing owner branch,
verify the allowed base delta, then let that owner patch". So:

1. INT01 verifies canonical clean local==remote (`48dea7e`).
2. Owner branch must be CLEAN at its tip (`f02055d`, porcelain 0).
3. `git merge --no-ff 48dea7e` ON the owner branch → merge commit
   `fb59215`, conflict-free when the file-sets are disjoint
   (T05 delta = frontend/e2e + docs; addendum delta = routes/s12_export.py
   + REPORT_C2 + a new test file). Verify `git diff --check` 0 after.
4. DO NOT push the owner branch after the base merge (transport-local).
5. Owner then runs its finalize turn (positive C22 case) on the merged
   base; W5 wave transport later merges the new tip into canonical the
   normal way (`48dea7e` is now an ancestor of the T05 tip → clean).

## Pitfalls

- **ff-only failure on a diverged branch is NOT a conflict to abort-and-alarm**;
  it is a topology report. Classify first: same merge-base + both sides moved
  = diverged; different merge-base = real fork (investigate).
- **INT01 stops and asks** when its instruction said "ff" but topology makes
  ff impossible — it correctly did NOT self-decide to merge. Manager answers
  with the exact command (`git merge --no-ff <canonical-SHA>` on the branch)
  citing §3, since the alternative (skip prep entirely) also works but
  forces the owner to run finalize on a stale base.
- Expected conflict-free because file-sets are disjoint — verify with
  `git diff --stat`/`git diff --check` after merge, never assume.
- Order matters: base merge BEFORE the owner's finalize turn, so the
  positive product case is proven against the real (now-present) endpoints.