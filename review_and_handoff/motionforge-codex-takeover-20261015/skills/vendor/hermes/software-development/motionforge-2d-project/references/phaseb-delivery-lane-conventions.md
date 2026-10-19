# Phase B delivery lanes (MF-END 28-task DAG) — packet & lane conventions

Session evidence: takeover delivery 2026-09-27/28. Every convention below was executed
and verified; the cross-cutting budget/transport mechanics live in
`independent-evidence-verification/references/iteration-budget-exhaustion-and-finish-packets.md`
(160-cap finish packet, alembic-head guards, transport conflicts, protected-test
pre-registration). This file is the MotionForge-specific packet boilerplate.

## 1. Every UI task launch packet MUST embed the user's UI convention block

The user has complained twice about dark-theme buttons lacking readable helper text.
Embed this verbatim in any packet whose write-set touches `frontend/**`:

> Mỗi nút/điều khiển dark-theme: **helper text tiếng Việt ngắn NGAY DƯỚI nút**, màu
> **`text-gray-400` hoặc sáng hơn** (gray-500 KHÔNG đọc được trên gray-900), cỡ **≥11px**.
> Chuỗi UI cho người dùng: tiếng Việt. Bám palette hiện có của `frontend/`.

Applied to MF-END-10/24/25 packets in this run. Do not rely on the worker re-deriving
it from context — packets are the delivery mechanism for standing user preferences.

## 2. Standard launch-packet envelope (all tasks)

Sections, in order: (0) BẮT BUỘC — read `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
fully → report `RULES_LOADED`, plus the task's own packet + relevant plan sections;
(1) **Manager guard đo trước** — per-path `{exists, bytes, sha256}` for the write-set
(existing ⇒ bounded preimage patch; missing ⇒ NEW), porcelain=0, `alembic heads` when
migrations are involved, plus any measured facts from earlier tasks the worker must
reuse (prompt ids, shas, GPU receipts, capacities); (2) scope + acceptance from the
original packet (acceptance is the hard boundary); (3) gate order micro → acceptance +
negative controls → focused/static → ONE broad wave gate; `commands.jsonl` UTC with
exit codes; byte before/after; local commit only on exact allowlist; no push; terminal
line `TASK_SUBMITTED · QUALITY_ACCEPTED=0`; (4) retry/budget — provider-flap stop rule
+ budget advisory for large tasks ("commit + REPORT by ~110 calls").
Keep each packet ≤ ~35 lines; it is a pointer-plus-envelope, not a re-specification.

## 3. Manager per-task loop (what "verified" means)

1. Wait for the launcher's exit; read the log tail for the terminal line.
2. `git log --oneline -1` + `git show --stat` — commit scope must equal the write-set
   (plus any pre-registered protected file); parent must be the transport base.
3. **Re-run the task's test file yourself** on the committed tree (`-q -p no:cacheprovider`)
   — record the count as the independent verification line in the ledger.
4. `git status --porcelain` must be empty.
5. Append one ledger row (append-only, prefix-immutable) with: task, session, commit,
   manager_verify string (scope + test count + porcelain), state. Then dispatch the
   next dependency-ready task and report to the user in the same turn.

## 4. Ledger/ops conventions learned here

- Worktrees: `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/<TaskID>`,
  branch `codex/mf-end-NN-0928`; base = previous task commit + `merge --no-ff` per
  extra dependency; re-check porcelain AFTER the merge and update the guard's `head`.
- Monitors: one background `monitor_phaseb_<x>.py` per pair of active lanes, 8-min
  cadence; when lanes change, `sed` a new log name and re-launch (never edit a running
  file's LANES — the process loaded it at start). Stale lanes show STALL_AUDIT flags —
  verify against `git log`/tests before acting.
- Big integration tasks (19/23) hit the 160-turn cap at ~36–56 min; the finish-packet
  recovery is the proven answer (see cross-ref above).
- When both dependency slots free at once, dispatch a pair from the SAME base commit
  (e.g. 24+26 from `4444f8c`) — staggered by ~45 s; keep ≤2 workers + Manager.
