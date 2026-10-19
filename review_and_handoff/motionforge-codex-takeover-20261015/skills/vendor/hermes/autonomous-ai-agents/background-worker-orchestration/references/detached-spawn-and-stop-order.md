# Long workers must survive the parent app dying — and must stop in dependency order

Measured 2026-10-06 (same MF-DEMO-LONG-01 run). Two process-lifecycle failures and
their fixes; both cost real GPU hours when missed.

---

## 1. A worker spawned from the agent's terminal dies when the desktop app restarts

The launcher was started with `terminal(background=true)`. When the Hermes desktop
app restarted (user-side), **the whole descendant tree was killed**: launcher,
worker child AND the heartbeat monitor. Symptoms that confirm "killed by parent
tree teardown" rather than a task failure:

- Worker log stops growing mid-line, **no exit trailer** (`Resume this session with:`
  block missing — the CLI writes it on every graceful/truncation exit).
- The launcher receipt was never finalized (`exit_code: None`, `utc_end: None`).
- Whole PID list of Hermes/python processes changed at once (new desktop tree set).
- The heartbeat's last row predates the stop; no terminal row follows.

Fix: spawn the launcher **detached from the app tree** via WMI, so it survives
desktop restarts:

```powershell
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = 'cmd.exe /c C:\...\manager\tools\run_w<N>.cmd'
} | Select-Object ProcessId,ReturnValue
```

where `run_w<N>.cmd` wraps the launcher and appends all output to a log file:

```bat
@echo off
cd /d <RUN_ROOT>
"<venv>\python.exe" -B manager\tools\dispatch_long.py manager\packets\W<N>.md ... >> manager\w<N>_stdout.log 2>&1
```

Same pattern for the heartbeat monitor (`run_heartbeat.cmd`). Verify after spawn:
`tasklist /FI "PID eq <new pid>"` and a fresh ledger `child_spawned` row.

Also note: the `terminal(background=true)` handle can die with the app too —
`process(action='list')` returning empty after a restart is expected, not evidence
about the worker.

---

## 2. Stop a worker tree in DEPENDENCY ORDER — a watchdog respawns the runner

This run had three layers: `watchdog_wan.py` (self-healing, spawns the runner if
not alive) → `p4_wan_run.py` (GPU chunk runner, resumable) → ComfyUI server.
Plus the worker (`hermes chat --resume ...`), its launcher, and the manager heartbeat.

**Killing the runner while the watchdog lives = the watchdog restarts it within one
cycle (5 min).** Correct stop order, exact PIDs, each layer verified before the next:

1. **Watchdog first** (the only layer that can resurrect others).
2. **Runner** (the GPU job producer).
3. **Worker** (`hermes.exe` child) — after this, nothing remains that could respawn the others.
4. **Launcher + heartbeat.**
5. **ComfyUI server** (listener PID *and* its venv wrapper PID; both exist).
6. Cancel/record any in-flight Comfy queue job; the killed-runner chunk is discarded
   and will simply be re-rendered on resume (runner skips completed chunks).

After each step: query the process table by cmdline pattern, not by PID alone:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'watchdog_wan|p4_wan_run|dispatch_long|heartbeat_long' } |
  ForEach-Object { '{0} | {1}' -f $_.ProcessId, $_.Name }
```

Empty result = layer gone. Do the same sweep for `0caeab`-style session ids to catch
any worker the desktop itself re-parented.

Also watch for spawn wrappers: a venv `python.exe` **launcher** and a base-interpreter
**child** both appear (e.g. `2640` child + `21464` wrapper for the Comfy server) —
kill both, then verify the LISTENING socket (`netstat -ano | grep 8188`) is closed.

---

## 3. Freeze + record everything before/while stopping (review handoff)

The stop was a USER STOP for review; the deliverable had to be reviewable immediately:

1. Write a state snapshot BEFORE killing: `evidence/USER_STOP_<date>.json` with last
   progress row, counts (chunks/frames/done/total), output file inventory, in-flight
   job id.
2. Capture the in-flight Comfy queue (`/queue`) to evidence — it names the chunk that
   was mid-render and will be redone on resume.
3. Build the review artifact from COMPLETED units only (concatenate finished chunks +
   original audio span; label `LONG_PARTIAL_<a>s-<b>s.mp4` with explicit coverage %).
4. Sample frames → contact sheet → vision self-check (state that it is frame sampling,
   not continuous review; UNKNOWN stays UNKNOWN).
5. Write `FINAL_STATE.json` with terminal `USER_STOP`, coverage numbers, artifact
   sha256/sizes, and the one-line resume recipe; append a `user_stop` row to the
   dispatch ledger; update the session registry status.
6. Report to the user with: what stopped, coverage %, the partial artifact path,
   what resume needs, and the open review items.

Rule: a stop is only "clean" when the process sweep is empty AND the disk state
(snapshot + ledger rows + partial) exists. Both halves get quoted in the report.
