# Worker iteration-budget exhaustion → finishing-packet recovery (measured 2026-09-28)

## Failure mode
A CLI worker (hermes chat) can hit its **iteration budget (160/160 turns)** on the largest
integration tasks. Observed on MF-END-19 (MF2D Phase B):
- Launcher exits **0**; log tail prints `Iteration budget reached (160/160) — response may be incomplete`.
- `git log` still shows the transport/base commit — **NO task commit**.
- But the work is usually on disk: porcelain shows exactly the write-set files (M + new) and the
  task's own test file already passes.

## Recovery (worked; 5m46s to close)
1. **Measure disk before anything** (never trust the exit code):
   - `git status --porcelain` in the worktree → compare against the packet write-set.
   - Run the task's test file directly: `python.exe -m pytest tests/product_delivery/<test>.py -q`.
     (MF-END-19: 31 passed → proved implementation was complete.)
   - Check the evidence dir (`tasks/<ID>/`) for raw/report artifacts.
2. **Resume the SAME session** (never mint a new one; `--resume <session_id>` keeps the id) with a
   tight *finishing packet* — 4 steps only:
   1) re-run 2 test commands (focused + public_chain), capture rc;
   2) close evidence: REPORT / raw/final_gate.json / append commands.jsonl (no big new artifacts);
   3) commit EXACTLY the measured allowlist paths (no `git add -A`), no push, no amend;
   4) print the terminal line (`TASK_SUBMITTED · QUALITY_ACCEPTED=0 · commit <sha> · không push`).
   Cap the packet at **≤40 tool calls**, no GPU, no scope expansion.
3. **Verify after**: commit stat == write-set only; porcelain clean; independent re-run of the test.
   MF-END-19 result: commit `2dbb590`, 6 paths +2,697; Manager re-run 32 passed.

## Prevention (write into every large-task dispatch packet)
- “Budget ~70–80 tool calls; if ~120 and not done → **commit the allowlist + REPORT first**, then stop.”
- Ordering rule: package + commit before the last quarter of the budget; never leave commit/evidence
  for the very end of a big integration task.
