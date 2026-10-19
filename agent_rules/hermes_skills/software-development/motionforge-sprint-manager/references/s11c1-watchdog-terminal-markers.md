# S11-C1 watchdog incident (2026-09-04) — false-BLOCKED lessons

Session-specific detail for the sprint-manager watchdog pattern. Class rule lives in
`terminal-engineering-discipline` pitfall 20; this file keeps the concrete case.

## What happened

Watchdog v1 marked a lane stalled on (log frozen + session quiet) without reading worker
terminal markers. C1-A had SUBMITTED the night before (commits `2712a5e`+`970cb27`,
porcelain clean) yet the watchdog paged `STALL persists after 2 nudges — needs manager
(BLOCKED?)` every 10 min for ~2h. Gateway was off so crons never delivered — the false
alarm fired in a forest with nobody hearing, and the manager (this session) had no
reminder to do the next step (verify) after workers finished.

## Matcher evolution (all three bugs were real, caught by live test)

1. No stop condition at all — only a hardcoded `done_tip` for one lane. Fix: `lane_terminal()`
   reads each dispatch log for a worker terminal line before any stall verdict.
2. Tail-window truncation — `TASK_SUBMITTED` + `EXIT=0` trailer sat outside the last 6000
   bytes. Fix: read the whole file (logs are ~40KB, cheap).
3. False NEEDS_T04B — REPORT cited the marker name in prose ("KHÔNG cần T04B
   (`NEEDS_T04B_PRODUCT_FIX`..."). Fix: match only head-anchored terminal lines, allow
   markdown/diff prefixes (`**`, `-`, `+`), ignore in-text citations.
4. Stale state — old `nudges[tip]=2` counts blocked re-evaluation after the fix. Fix: clear
   stale nudge counters when the matcher logic changes.

Worker terminal contract that made this work: exactly one line `TASK_SUBMITTED — ...` /
`NEEDS_T04B_PRODUCT_FIX ...` plus an `EXIT=/NUDGE*_EXIT=` wrapper trailer.

## Watchdog operating rules used here

- SILENT when all lanes DONE (verified: 3× `OK {DONE_SUBMITTED}` lines, zero false pages).
- Nudge goes to the EXACT owner session (`hermes chat --resume`), max 2 per tip, never a
  new worker, never touches git. Nudge route pinned `ocgfree/muse-spark-1.3-contributor-free`
  + `--provider custom` (user: Muse only, DeepSeek off; old DeepSeek rows in
  `session_model_usage` were stale history from the prior production round).
- Watchdog must also watch the MANAGER's own pending steps (verify/merge/dispatch-next):
  workers all-DONE with manager todos still pending for >60 min is itself a pageable stall.
  (Promised this session; implement as `manager_todos` check.)
- Cron + detached bg loop double coverage while gateway is off; kill the loop once the
  gateway delivers crons to avoid double-nudges.
