# C3 stale-seed vs production lesson (S11-C3, 2026-09-05)

Session-specific detail for `pm-worker-orchestration`. Read this when a worker
stalls on a stale/failed/not_run semantic mismatch after a production
envelope change.

## 1. Stop nudging after 3 unproductive rounds — read production yourself
- B9→B14 (5 nudges) produced zero commits. Manager broke the loop by reading
  `app/persistence/qc_check_runs.py` directly on both trees (INT vs T05A).
- Rule: after 3 nudges with no `git log` movement, do read-only production
  diff yourself, then dispatch ONE directive with the exact mechanism cited
  (file:line), not another open-ended "fix it" nudge.

## 2. The C3A1 stale mechanism (exact)
- `latest_check_run_state` (INT `qc_check_runs.py:614-703`):
  - coverage gate compares manifest fp against CURRENT evidence RECOMPUTED
    WITH THE MANIFEST'S OWN generation (`:685-690`);
  - stale/ready split compares manifest fp against CALLER-supplied current
    evidence (`:702`).
- Correct stale seed = manifest pins OLD generation (fp genuine → coverage OK)
  + caller reads NEW generation (mismatch → STALE).
- Fake fp (`"z"*64`) always fails coverage → `failed`, never `stale`.
  Fixing the expect line to `failed` on the OLD tree is wrong; fixing the seed
  to a fake fp on the NEW tree is wrong. Match seed to mechanism.

## 3. Scope guard — never copy production across task branches
- Worker copied C3A1 production into T05A tree (+228/-23 in
  `app/persistence/qc_check_runs.py`). Manager reverted it:
  `git checkout -- app/persistence/qc_check_runs.py`, keeping only the owned
  test file.
- Rule: each task branch touches ONLY its owned files. Cross-tree production
  sync happens via INT01 merge, never by copying production into a task tree.
- Check `git diff --stat` after every worker EXIT; revert production drift
  before verifying tests.

## 4. Worktree/branch/tip guard before every dispatch
- One dispatch `cd`'d into `s11-integration` instead of `s11-t05a-0903w12`
  and fast-forwarded the T05A branch to the INT merge commit. Fixed with
  `git reset --hard <task-tip>` + porcelain check.
- Rule: every dispatch prompt starts with worktree path + branch + expected
  tip SHA, plus "CAM merge/fetch, CAM touch other worktree". Verify
  `git log --oneline -1` + `git status --porcelain` after EXIT.

## 5. Merge-then-gate evidence beats worker claims
- Worker claimed "gate ran before merge so RED is stale". M2 log proved
  `merge db14de3 no-ff → 778a1ce` BEFORE gate RED (1 failed). Quote the log
  line back at the worker; never accept timing excuses without the log.
