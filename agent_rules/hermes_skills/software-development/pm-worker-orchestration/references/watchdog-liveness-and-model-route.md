# Watchdog liveness + model-route hygiene (PM-gated worker sprints)

Class-level pattern: workers stall silently (wrapper exit 0 but no terminal),
gateway-off kills cron, and stale model rows look like live violations.

## 1. Two-layer watchdog (cron + in-session loop)

- Cron no-agent job (hermes cron create "*/10 * * * *" --script <name>.py
  --no-agent --deliver origin): empty stdout = silent (correct when OK).
- In-session loop fallback while gateway is off: while true; do sleep 570;
  python <script>; done as background process. Kill once gateway is on.
- Per-lane read-only checks: dispatch.log mtime, worktree tip, session quiet
  minutes. STALL = log frozen >30m AND session quiet/absent.
- On STALL: detached hermes chat --resume <exact-sid> -m <model> --provider
  <provider> -q <short nudge> -Q, max 2 nudges per tip; third strike needs
  Manager. Never open new worker sessions; never touch git state.
- Persist watchdog_state.json + append watchdog.log one line per tick.

## 2. Wrapper-exit vs worker-done

- Wrapper EXIT=0 only means the CLI returned; ground truth is disk: terminal
  marker in dispatch.log tail + tip advanced + porcelain — not exit notices.
- After 2 nudges with no terminal, Manager verifies directly from disk.

## 3. Model-route forensics

- Query state.db session_model_usage per session ordered by last_seen; an old
  last_seen row is history, not a live violation.
- billing_provider=auto + task=approval/compression rows are system-initiated;
  exclude from route accusations.
- Pin -m/--provider on EVERY dispatch AND nudge; pause superseded heartbeat
  cron jobs on route change; note in registry.

## 4. Proactive lane-exit reporting

- On any worker EXIT report in the same turn BEFORE verification: lane,
  terminal marker, tip/porcelain, raw counts.
- ETA: lead with status + anchored expected/worst table; on slip report
  immediately with reason.
