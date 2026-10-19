# Demo-lane dispatch verification, exact-model resolution, bounded watchdog, ETA shape (2026-09-08, MF-DEMO-V3-R2 T00)

Session-specific lessons from dispatching an evidence-only worker on a dirty demo tree in parallel with an independent lane. All verified live this session.

## 1. Zero-byte dispatch.log does NOT mean a dead worker

Dispatch was `hermes -z "$(cat prompt.txt)" -m <id> --yolo >> dispatch-T00-R1.log 2>&1` in background. After 2+ min the log was still 0 bytes, yet the worker was healthy: process `hermes` PID alive, a NEW session id appeared in `hermes sessions list`, and real evidence files landed in the task evidence dir (DB copy, probes, manifest, snapshots with fresh mtimes).

Triage order before any kill/retry decision:
1. `wc -c dispatch.log` + `ls --time-style=full-iso` (is it truly 0/stale?).
2. Process liveness: `ps aux | grep hermes` — wrapper PID from the background start still present?
3. `hermes sessions list` — did a NEW session id appear after dispatch time? That is the worker's own session and the strongest start proof.
4. Disk truth: `ls -lt` the task evidence dir — growing files with fresh mtimes = working despite buffered log.
5. Only if ALL of process/session/disk are silent past the startup window (~2 min for new session, longer for big-session resume) treat the lane as not-started.

Never kill on log silence alone. The existing TRUNCATED-DISPATCH-LOG rule covers mid-run truncation; this is its zero-byte startup variant (stdout buffered until first flush).

## 2. Exact worker model id comes from the manager session's turn_context, not the user's typed string

User ordered "workers use the same model as this chat". The user-typed id (`ocgfree/muse-spark-contributor-1.3-free`) had transposed segments vs the session's real id (`ocgfree/muse-spark-1.3-contributor-free`) — both probed pong, but dispatch MUST use the exact session id. Resolution recipe:
1. `grep "agent.turn_context" ~/AppData/Local/hermes/logs/agent.log | grep <manager-session-id>` → pin `model=` + `provider=`.
2. Probe the exact pair (`hermes -z "ping" -m <exact-id> --yolo` → pong, record EXIT).
3. Dispatch with the exact id; record a probe matrix (user-string result vs exact-id result) in the registry as route evidence.
4. Never retro-apply the model to other lanes' sessions (Lunar, S12).

## 3. "Run continuously" = bounded run-watchdog, NOT a 24/24 watcher

Standing rules forbid permanent watchers/automation. The compliant pattern used: a BOUNDED background poll loop (90 min, sleep 60, `notify_on_complete=true`) watching for the task's terminal marker (`STATUS:` in `T00/REPORT.md`), exiting 0 on marker or 2 on timeout, with its START row in `commands.jsonl`. No polling loops by hand while the worker runs (preserves the worker's in-flight budget); the notify wakes the manager to chain the next DAG step in the same turn.

## 4. ETA answer shape for "bao lâu thì xong"

Lead with live status (phase + newest disk evidence + process proof), then a table with DATE-ANCHORED ETAs, each row carrying its dependency condition. Every ETA already includes worker-death + reasoning-max buffer; a slip is reported immediately in-turn with the reason, never discovered by the user asking again. Heartbeat ≤20 min or instant on worker EXIT.
