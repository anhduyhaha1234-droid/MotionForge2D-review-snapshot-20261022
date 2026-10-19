# S10-C2 — CommandCode `Network connection lost` transient retry (verified 29/08 01:07-01:30)

Companion to `s10-c2-deepseek-route-and-inflight-402.md` + `s10-c2-t01c-meta-max-continuation.md`.
Session `20260828_180654_be71b5`, worktree `s08-integration`, owner `20260828_011920_b79bd6` (T03-C2).

## Observed shape
Dispatch via Meta-max `--provider custom -m meta --yolo` (verified pong 00:47):

```
proc_64f17996e2a5 00:48 → 01:07  output/s10/c2/t03-c2/dispatch-meta.log  90 B
  [CommandCode error: {"type":"server_error","message":"Network connection lost."}]
  EXIT=0
proc_f643822204cf 01:08 → 01:29  output/s10/c2/t03-c2/dispatch-meta-r2.log  90 B  (same body, retry collapsed)
```

90 B payload, wrapper reports `EXIT=0` (outer bash echo), but worker never flushed any real output — `bash: no job control in this shell` only. Two consecutive retries collapsed to same 90 B line.

## How to tell it apart
- Not a 402: no `in_flight_budget_exhausted` / `Prompt tokens limit exceeded` line.
- Not compression silence: no leaf PYTHON pid under hermes.exe, no CPU creeper — total abort, not streaming.
- Infrastructure still green: `ping 1.1.1.1 0% loss`, `hermes -z ping --yolo pong`, `netstat :20128 ESTABLISHED`.

## Rule (Rules §7)
`Network connection lost` is **intermittent** → wait + retry SAME owner / SAME provider+model / SAME prompt file. Never open a new session for a transient retry. Treat wrapper `EXIT=0` as meaningless for this lane; gate on real log bytes and pytest output. If same owner collapses 3× in a row with identical 90 B body, escalate to `BLOCKED_NETWORK` and require explicit manager/user instruction — don't loop forever.

## Recommended one-liner to log the retry
```
01:08 +07 — T03-C2 R1 network drop: CommandCode Network connection lost (90 B, wrapper EXIT=0, no worker output; ping 1.1.1.1 0% loss, 9Router pong OK) — not product failure, upstream transient per §7 — retrying same owner
01:08 +07 — T03-C2 R2 dispatched — proc_f64... — resume 20260828_011920_b79bd6 --provider custom -m meta — log dispatch-meta-r2.log — chờ notify
```
