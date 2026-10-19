# Gateway 502 worker-death recovery (temp connection errors, mid-turn)

Recovery cycle for workers killed mid-turn by upstream fetch timeouts through a local
gateway/proxy (opencode-go style). Verified S12-R6 2026-09-15: one 502 burst killed 3 of
4 lane turns within 2 minutes; all recovered same-route without losing verified work.

## Signature

Console tail (per killed lane):

    API call failed after 3 retries: HTTP 503: [<upstream>/<model>] [502]: fetch connect timeout (reset after Ns)
    session_id: <same session id>
    EXIT=1

Process gone; in-flight model generation lost; completed tool work on disk intact.

## Recovery cycle (per lane, per policy §7 "temporary connection error")

1. **Partial-write audit BEFORE anything else.** In each affected worktree:
   `git status --short` + compare against expected write-set. Read the console tail to
   see the phase it died in (design/reading = nothing written; mid-write = inspect the
   exact files it was touching). S12-R6: all three worktrees clean/only-expected.
2. **Wait >= 5 minutes** from the failure timestamp (console mtime / EXIT line). Do NOT
   fire resumes inside the window.
3. **Liveness-probe the route** with a trivial completion through the same path:
   `hermes chat -q "Reply with exactly: PROBE_OK — nothing else. Do not use any tools." -m <model> --provider <p> --max-turns 2`
   Compare latency against known-good (S12-R6: 57s vs ~9.5s normal = upstream degraded
   but reachable → expect repeat failures; keep cycling).
4. **Resume the SAME session id, SAME model/provider/config** with a SHORT prompt:
   acknowledge the interruption ("lượt trước bị ngắt bởi lỗi kết nối tạm thời — không
   phải lỗi của bạn; route/scope không đổi"), instruct: check current state (git status,
   files already created in evidence/runtime dirs), continue from the stop point per the
   work order, do not redo finished work, do not ask back.
5. **Record**: incident md (signature, affected sessions, first-failure timestamps,
   probe result+latency, resume times, route unchanged) + registry rows
   `RUNNING_RETRY_WAIT → RESUMED`. Report the incident to the user immediately
   (do not wait for the next heartbeat).
6. **Cycle unlimited** while failures are temporary-class; each cycle = wait 5 min →
   probe → resume. Never: switch model/provider, restart from scratch, or declare
   terminal on internal-retry exhaustion (the `after 3 retries` message is NOT a
   terminal state).

## Stale exit-notice trap (complements the recovery)

Background-process completion notices can arrive VERY delayed (tens of minutes) and OUT
OF ORDER relative to the events they describe. A notice tail pointing at
`work-turn1-console.txt` may land after you already diagnosed + resumed that lane.
Before acting on ANY notice: reconcile against ground truth — console file mtime/size,
live process list (pin the exact PIDs), worktree git state. Stale notice = log it, no
action. (Also: a lane that survived the burst lives on normally — don't "fix" it.)

## What NOT to conclude

- Upstream 502s are environment-transient — never record "provider/model broken" in
  memory or skills; the durable lesson is this wait/probe/resume cycle.
- EXIT=1 from internal retry exhaustion says nothing about the worker's code quality.
