# Silent launch-call hang → 60-min stall-kill (2026-10-08, MF-DEMO-LONG-01 C1#1 + C2)

Class of failure, observed twice consecutively with the same signature:

- The worker's tool call that **launches a detached batch** (bash `&` / `nohup` /
  similar) **never returns**, because the spawned child **inherits the tool
  call's stdout/stderr pipe** and the call waits for pipe EOF forever.
- The session log goes silent mid-turn immediately after the launch; the batch
  itself runs fine on disk. A harness stall-watchdog then kills the child after
  N minutes of no log growth (`timed_out=true`, `exit_code=1` — NOT a task
  failure, NOT a completed run).
- **Detached work CONTINUES through the kill.** After the stall-kill, verify
  disk state (clips, receipts, logs, queue) before concluding any loss — in
  both incidents the detached render produced correct artifacts for ~1h after
  the LLM was already dead.

## Guardrails for worker packets

1. **Mandate the detach primitive:** `powershell Start-Process` with
   `-RedirectStandardOutput <file> -RedirectStandardError <file>` breaks handle
   inheritance so the tool call returns immediately. Never ship a packet that
   relies on bash `&` / nohup detach without first verifying the launch call
   returns < 60 s (test it once).
2. **Ban silent blocks:** no tool call may block silently > 45 min. Long waits
   must be *separate* poll calls of ≤ 5–10 min each that print progress (log
   keeps growing); interleave useful work (write QC rows, prep scripts) between
   polls. State the harness kill threshold explicitly in the packet.
3. **Log-liveness monitoring, not disk-liveness:** if you monitor worker
   progress, watch the **session log** for silence (≥ 20 min while the process
   is alive ⇒ alert), NOT the evidence/output directories. A detached renderer
   writing files every few minutes masks an LLM stall in any disk-growth-based
   monitor — the alert then never fires before the harness timer.
   Arm monitors as exit-only background jobs (bg + notify) so they ping once,
   when it matters (worker gone / log-silent / cap).
4. **Do not early-kill a silent worker whose batch is mid-flight.** One silent
   worker WOKE when its batch completed (44 min of quiet) and finished the run
   cleanly; the sanctioned stall-kill timer (~60 min) is the correct backstop.
   Only consider an early kill after confirming no in-flight work and no queue
   activity — and prefer waiting for the timer.
5. **Recovery when the stall-kill fires:** (a) audit disk artifacts the detached
   batch produced; (b) do NOT relaunch duplicates — adopt existing outputs and
   prompt ids; (c) resume the **same session id** with a continuation packet
   whose first step is "read the real state, continue from there"; (d) append
   append-only ledger rows for the incident (audit findings, root-cause
   hypothesis, launch timestamps + pids of the still-running detached batch,
   continuation decision). A stall-kill is a technical continuation, not an
   owner transfer — session/context may be perfectly healthy.
6. **Receipt semantics:** `exit_code=1, timed_out=true` = **STALL_KILLED**;
   classify it as its own class BEFORE reading log-marker outcome tokens (plan
   text can still contain CONTINUE_REQUIRED tokens — see
   `independent-evidence-verification/references/invocation-receipt-parsing-and-outcome-classifier.md`).
