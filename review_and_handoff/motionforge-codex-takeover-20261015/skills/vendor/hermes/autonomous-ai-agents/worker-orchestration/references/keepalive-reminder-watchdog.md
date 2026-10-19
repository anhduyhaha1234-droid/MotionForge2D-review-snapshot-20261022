# Keepalive Reminder Watchdog for a Stalled Manager/Worker Session

Context: the user's manager session (e.g. `S11-2-muse`) keeps stopping between
turns. Fix: a cron job (every 10 min — the user's default heartbeat cadence;
30 min proved too slow, 15 min still stalled) that resumes the session with a
nudge message and logs the manager's response. Proven 2026-09-04 (S11-C1 C2).

## Working script (`.py`, lives in `%LOCALAPPDATA%/hermes/scripts/`)

```python
# remind_<lane>.py — cron no_agent, silent on success
import datetime, subprocess, sys, time

HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
SID = "<SESSION_ID>"
MODEL = "<model e.g. ocgfree/muse-spark-1.3-contributor-free>"
PROVIDER = "custom"
MSG = "tiếp tục làm việc đi"
LOG = r"C:\Users\Admin\AppData\Local\hermes\logs\remind_<lane>.log"

def run(logf):
    cmd = [HERMES, "chat", "-q", MSG, "-r", SID, "-m", MODEL, "--provider", PROVIDER, "-Q"]
    return subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode

with open(LOG, "a", encoding="utf-8", errors="replace") as f:
    f.write(f"=== {datetime.datetime.now():%F %T} start ===\n")
    rc = run(f)
    f.write(f"exit={rc}\n")
    if rc in (1, 2):                      # retryable exits: one retry after 20s
        f.write("--- retry after 20s ---\n")
        time.sleep(20)
        rc = run(f)
        f.write(f"retry exit={rc}\n")
    f.write(f"=== {datetime.datetime.now():%F %T} end ===\n")

if rc != 0:
    print(f"REMIND_FAIL exit={rc} - xem log: {LOG}")   # stdout non-empty -> cron alert
    sys.exit(rc)
```

Cron job: `no_agent=true`, `script=remind_<lane>.py`, `schedule=*/10 * * * *`,
`deliver=origin` (unused — see below). The script redirects ALL hermes output
into the log, so stdout is empty on success = silent watchdog.

## Hard rules (each was paid for in blood)

1. **PIN the model on resume.** `hermes chat --resume <SID>` with no `-m/
   --provider` uses the profile DEFAULT model — NOT the session's stored
   `model_config`. Observed: manager pinned to Muse fell back to `meta` via
   the old 9Router combo (a forbidden route). Always pass
   `-m <MODEL> --provider custom`; verify the run via agent.log
   (`API call ... model=<MODEL> provider=custom`) before trusting it.
2. **Cron `.sh` scripts fail on Windows paths.** The scheduler builds the
   script path with backslashes and runs it through bash, which swallows
   them → `C:UsersAdminAppDataLocal...: No such file or directory` (exit
   127). Use `.py` — Python handles Windows paths natively.
3. **`capture_output=True` swallows the manager's response.** The log then
   shows only start/exit markers and you lose the progress report. Use
   `stdout=<open-log-file>` instead. Side effect: fd-direct writes land in
   the file BEFORE the buffered `start` line flushes — the manager's
   response appears above its own `=== start ===` line. This is buffering
   order skew, not corruption; read by content.
4. **No model pinning via the cronjob tool.** The `cronjob` tool accepts no
   `model/provider` args, so an agent-mode cron job runs the profile default
   (observed `meta`, forbidden). Keep watchdogs `no_agent` + script-only so
   no model is involved at all — the script pins the model itself.
5. **`deliver='origin'` never reaches the desktop chat when the gateway is
   off.** Scheduler log: `deliver=origin but no origin or home channels —
   skipping delivery (output saved in last_output)`. Don't fight it — the
   log file IS the delivery channel; report to the user each time they ask,
   and put a **NUDGE TIME column** (the script's start block time) in every
   status table — the user complained when the table lacked the nudge hour.
   The manager's own `date` inside its response can skew 1–7 min vs the
   machine clock (WSL-ish drift); trust the script start time instead.
6. **`402/502 FreeUsageLimitError` = provider rate limit, not a script bug.**
   Free-tier providers (ocgfree/muse-spark-1.3-contributor-free) return
   `HTTP 502 {"error":{"type":"FreeUsageLimitError"...Rate limit
   exceeded...}}` after heavy use; 3 in-process retries still fail. The cron
   simply retries next tick and self-heals when the limit resets. Report the
   cause honestly; never silently swap the route — the user decides model
   changes.
7. **Only stop the cron on an explicit "dừng".** "m ko nhac nua a?" or
   "nhắc chưa?" are QUESTIONS about state — answering with a stopped
   watchdog cost trust ("t có bảo m dừng đâu"). Ask or keep running; stop
   only on a clear stop order.
8. **Cadence follows the user.** 30 min → manager still stalled; 15 min →
   still stalled; 10 min stuck. The user's standing preference is 10-minute
   heartbeats for sprint monitoring.

## Observability

- `%LOCALAPPDATA%/hermes/logs/remind_<lane>.log` — script runs + the
  manager's full response per nudge (start/exit/end blocks).
- `%LOCALAPPDATA%/hermes/logs/agent.log` — ground truth:
  `grep <SESSION_ID>` → `API call #N: model=... provider=custom` + `Turn
  ended: reason=text_response ... model=...` proves route + liveness.
- state.db `messages` count for the session grows per nudge.
- `cronjob list` → `last_status`, `next_run_at`.

## Report format the user expects

| Giờ nhắc | Lane | Trạng thái thật |
|---|---|---|
| 13:30 | C2-A1 T03G | ✅ SUBMITTED @ <sha> + VERIFIED 98 passed |
| 13:30 | C2-A2 T06C | ✅ TASK_SUBMITTED @ <sha> — verify độc lập đang chạy |

Include the nudge time as the anchor column; pull status from the manager's
latest logged response, never from memory.