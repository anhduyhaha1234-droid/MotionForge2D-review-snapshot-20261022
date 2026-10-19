# Hermes Manager Liveness Incidents

This append-only record captures orchestration failures that must influence
future Hermes manager prompts. Reported observations are distinguished from
verified root causes.

## 2026-08-17 — Manager remained idle until user message

- **Reported by user:** The Hermes manager remained idle for approximately ten
  hours and resumed only after the user sent a chat message.
- **Impact:** Approximately ten hours of avoidable project delay.
- **Verified cause:** Not established. Do not assume the coding writer, task
  implementation, or user caused the pause without additional evidence.
- **Process failure:** The manager had no effective bounded wait/liveness
  recovery behavior and implicitly depended on user interaction to resume.
- **Permanent prompt requirements:** No indefinite waits; maximum 10-minute wait
  interval; liveness check after each timeout; treat 20 minutes without progress
  while work remains as an incident; send a heartbeat at least every 30 minutes;
  attempt recovery immediately; emit a precise blocker after three failed
  recoveries; never require a user message merely to wake an authorized run.
- **Concurrency invariant:** Liveness recovery never permits a second writer on
  the same worktree. Read-only helpers remain non-writing and bounded.

