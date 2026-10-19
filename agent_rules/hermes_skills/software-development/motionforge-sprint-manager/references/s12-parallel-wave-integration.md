# S12 W2 parallel integration + pre-staging (2026-09-07)

Session-specific detail for the Sprint Manager skill. Sprint S12 (4K export),
wave W2 = T02 || T03A || T04A from pushed T01 checkpoint `0d04673`.

## What happened

1. T02 (`be1def0`, 28 tests) and T04A (`c375b87`, 26 tests) both reached
   TASK_SUBMITTED. Two merge commits (`0aedb22` T04A, `2618e8f` T02) appeared
   on `s12-integration` via INT01 transport while the Manager's context was
   compacted — first misread as foreign, then self-attributed via
   `git log --format='%h %ci %s'` vs own session messages (no INT01/writer
   session existed in state-DB).
2. Manager re-verified instead of re-merging: task-dir gates (T02 28/28,
   T04A 26/26 + ruff), `git merge-tree $(git merge-base A B) A B`
   conflict-free, T01 regression 15 passed, combined integration gate at
   `2618e8f`: **69 passed (15+28+26) in 25.51s + ruff clean**.
3. Push said `Everything up-to-date` but `git ls-remote` timed out
   (github.com:443, exit 128) → recorded local-verified / remote-unverified,
   retry at W2 gate, disclosed in REGISTRY + packet.
4. User ordered "dispatch early if parallelizable". DAG (§7) still blocked
   T03B (deps T02+T03A+T04A integrated; T03A running). Manager PRE-STAGED
   T03B: worktree @ `2618e8f` + 5-file guard CAPTURE + `prompt.md` headed
   `PRE-STAGED, CHƯA DISPATCH` with exact firing condition — no DAG
   violation, dispatch fires automatically at gate.

## Reusable commands

```bash
git merge-tree $(git merge-base <TIP_A> <TIP_B>) <TIP_A> <TIP_B>
git log --format='%h %ci %s' -5            # self-attribution of merges
git ls-remote origin <branch>              # remote proof; push up-to-date ≠ proof
git -C <int-tree> status --porcelain -uall # must be empty before/after merge
```
