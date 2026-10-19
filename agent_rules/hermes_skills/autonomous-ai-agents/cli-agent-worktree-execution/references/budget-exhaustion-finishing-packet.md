# Budget-exhausted worker → finishing-packet recovery (verified 2026-09-28)

Trigger: a big integration task's launcher exits 0 (or its log tail says
`Iteration budget reached (160/160) — response may be incomplete`) and the
worktree HEAD is still the base/transport commit — **no task commit exists**.
The worker burned its whole turn budget before the packaging step.

Observed: MF-END-19 (FullApply → shot-level render), 36m15s, 345 tool calls,
160/160 turns, `git log --oneline -1` = the transport commit only.

## Rule: measure disk BEFORE deciding anything

Do NOT re-dispatch the task, do NOT write the commit yourself, do NOT assume
the work is lost. In the observed case ~100% of the work was already on disk;
only commit + evidence closure were missing. Measure in this order:

1. `git status --porcelain` in the worktree — expect `M` files inside the
   write-set plus `??` new files. Note each new file's byte size.
2. **Run the task's test file yourself** (fresh process, `-p no:cacheprovider`).
   A passing suite against the on-disk tree is the proof the implementation is
   real, not a stub. Observed: 31 passed before any recovery action.
3. `ls` the evidence dir — a partially filled evidence root (raw/, managed/,
   TARGET.md, …) usually means the worker died at the report/commit step.

If touched files ⊆ allowlist and tests pass → recovery, not redo.

## Finishing packet shape (resume the SAME session)

Resume the exact owner session (`--resume <session_id>`) with a short packet
(`<TaskID>-finish.md`). Keep it under one screen; the 4 steps, nothing else:

1. **State the measured disk truth verbatim** — the porcelain listing with
   byte sizes, your own test result counts, and what the evidence dir already
   holds. Prefix it "TÌNH TRẠNG ĐO ĐƯỢC (Manager)" so the worker trusts it and
   does not re-derive: "CHƯA có commit cho <TaskID> (HEAD = `<sha>` transport)".
2. Exactly four steps: (a) re-run two named test commands and record rc;
   (b) close evidence — REPORT / final_gate.json / append commands.jsonl with
   this run's UTC row; (c) commit EXACTLY the measured paths, message notes
   "(finish pass: commit + evidence closure)"; (d) print the terminal line
   `TASK_SUBMITTED · QUALITY_ACCEPTED=0 · commit <sha> · không push` + evidence root.
3. Explicit caps: **≤40 tool calls this run**, no GPU, no scope expansion, no
   new files beyond the measured allowlist, no amend, no push.
4. Ban re-derivation: "đừng mở rộng, tránh hết budget lần nữa".

Result: exit 0 in **5m46s**, commit landed with exactly the 6 write-set paths,
independent re-run 32 passed, porcelain clean. Compare: re-sending the whole
contract would re-derive hours of work and risk a second budget burn.

## Prevention (put it in every later packet)

Add a budget line to the launch packet's retry section:

> Budget ~80 tool calls; nếu tới ~120 mà chưa xong → ưu tiên commit đúng
> allowlist + REPORT trước khi kết thúc.

Also: size the task. If the packet's write-set has 5-6 files including 1,000+
line new modules, the 160-turn budget is the binding constraint — the worker
should commit incrementally rather than at the end.

## Record it as an incident row

Append one ledger row so the next reviewer sees both the failure and the
repair: `{event: "BUDGET_EXHAUSTED_AND_RECOVERY_DISPATCHED", task, round,
actual_session, observed: "<exit line + no commit>", disk_state_measured:
"<porcelain + test count + evidence dir>", recovery: "<finish packet path +
proc id>", lesson: "<one line>"}`.

## Variant: driver-side death vs worker-side budget

- Worker-side budget (`Iteration budget reached`) → the session is healthy,
  resumable; the finishing packet above is the fix.
- Driver-side wrapper death (`bash: no job control`, truncated log) → treat as
  a flap; wait, then resume the same owner/model/scope.
- Either way the first action is the same: measure disk, don't trust the exit
  notice's implication that the task failed.
