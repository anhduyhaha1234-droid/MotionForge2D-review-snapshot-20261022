# Long-run invocation lifecycle: stall-kills, detached work, continuation (2026-10-08)

Context: multi-hour delivery runs (MF-DEMO-LONG-01 recovery W4→W7, then correction C1/C2).
Manager dispatches worker invocations via a harness with `max_turns=80` (invocation boundary),
`HERMES_MAX_TOKENS=16384` (child env), and `stall_kill_seconds=3600` (kills the child when the
log shows NO growth for 60 min). Receipts + an append-only dispatch ledger record every round.

## Stall-kill forensics — "invocation terminal" ≠ "work stopped"
Measured C1#1: receipt `exit_code=1, timed_out=true`; the log ends mid-turn ("preparing terminal…"
with no tool echo). The worker's last action had actually SUCCEEDED: the detached renderer
(`c1_rest.py all`) was still producing clips 60+ min after the LLM child was killed.
Checklist before assuming loss or re-dispatching:
1. Read log tail → find the last action.
2. Verify whether that action took effect: process table (runner alive?), Comfy queue, output/
   receipt counts + mtimes.
3. Only then decide. Detached runners legitimately outlive the LLM; adopt them, never relaunch
   duplicates ("adopt running work" instruction in the continuation packet).
4. A stall-kill is NOT a work failure and NOT a clean yield → do NOT transfer owner / open a
   recovery session. Session/context are healthy: resume the SAME SID with a continuation packet.
5. Append a ledger row (`continuation_after_stall_kill`) with cause hypothesis + disk-state
   evidence + the resume decision.

## Anti-stall discipline to embed in every long-run worker packet (the fix)
- Hard rule: NO single tool call may block silently >45 min (harness kills at 60'). For long
  waits: detached runner + SHORT polls (≤5–10 min), each poll printing progress (clip counts,
  queue size, receipt rows) so the log keeps growing.
- Interleave useful work between polls (write QC/assembly scripts, evidence rows) instead of
  sitting inside one blocking call.
- Progress must be observable without the LLM: per-shot receipts (`receipts/*.jsonl`), output
  file mtimes, queue state.

## Continuation packet shape (worked for W5/W6/W7/C2)
- Compact; "read checkpoint FIRST, do not dump history"; state = exact disk facts (counts,
  hashes, newest outputs); ordered next actions; restate write-set + protected; invocation
  boundary (checkpoint before ~turn 60–65, then yield with
  `CONTINUE_REQUIRED — next action: …; resume SID <sid>; evidence: <paths>`).
- After an abnormal terminal add: "adopt running work — do not relaunch duplicates" + the
  anti-stall rule above.
- Keep a user expectation note: the operator runs long jobs 24/7 and nudges ("sao lại đừng rồi")
  when the agent looks idle. Every long dispatch should arm (a) dispatch-notify on terminal,
  (b) an explicit stall/terminal monitor, (c) heartbeat rows — so progress and failures surface
  without being asked.

## Receipt/log classifier v2.2 — latest-occurrence-wins
Measured bug: a forward-looking plan line containing `SELF_REVIEW_PASS_PENDING_CODEX` beat the
real terminal `CONTINUE_REQUIRED` under list-order precedence. Fix: classify by the LATEST
occurrence position of any marker in the tail; ties break by list order. Also:
- session_id: prefer the CLI exit banner (`Session: <sid>` / `--resume <sid>`), LAST match —
  a packet echo can contain OTHER session ids earlier in the log.
- compactions: count event banners (`summarizing earlier conversation`), not every line
  containing the word (the agent's own text false-counts).
- Re-tested on 3 historical logs (W2r→CONTEXT_EXHAUSTED; W4/W5/W6/W7→CONTINUE_REQUIRED).

## Manager-side monitors (read-only, notify-on-exit)
- Settle-waiter (`_wait_render.py` pattern): settle = queue empty AND runner gone, sustained
  2 checks; cross-check completion against receipts (2d/doco shots legitimately have no runner
  rows). Prints a compact JSON summary; exit 0 on settle, 2 on timeout cap.
- Stall/terminal monitor (`templates/stall-terminal-monitor.py` in this skill): watches worker
  pid + log growth + SECONDARY progress (output/receipt mtimes, queue). A quiet log during a
  long render is normal — only "no log growth AND no secondary progress AND empty queue" is a
  stall. Exits with notify on WORKER_GONE / STALL_ALERT / cap.
- CORRECTION (measured C2, 2026-10-08): aggregate/secondary progress RESETS a stall timer and
  therefore HIDES an LLM stall — the detached renderer keeps writing clips while the worker's
  tool-call hangs; the old design stayed silent for the full 60 min. Arm the alert on the
  SESSION LOG alone: `log silent >= 20 min while pid alive` → LLM_SILENT alert (fires long
  before the 60-min harness kill, so you can audit and pre-stage the continuation packet).
  Keep secondary-progress logic only for SETTLE waiters ("is the work finished?"), not for
  liveness. Measured: monitor_c2 alerted at 24 min silence; the worker then WOKE on batch
  completion (44 min quiet) and finished cleanly — treat the alert as an audit trigger,
  never as a kill signal.
- Kill/stop actions always by exact verified PID (leaf→root), never by name patterns.
