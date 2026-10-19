# Launcher hygiene & session-ops for multi-lane CLI worker runs

Four failure modes measured on a real orchestrated run (2026-09-24, MotionForge2D round D, 9 lanes / 23 receipts).
Each one produced a *plausible-looking* state that a hurried operator would have accepted.

---

## 1. A copied launcher toolkit keeps the OLD run root — sweep paths BEFORE the first dispatch

When you copy `manager/tools/*` (append_dispatch, launcher, guards, heartbeat, watchdog) into a fresh run root, every
hard-coded absolute path comes with it. Symptoms seen:

```
REFUSED: packet missing: …/<OLD-RUN>/manager/packets/<PACKET>.md     # exit 2 → `&&` chain stops
```

**The trap:** the launch command was wrapped in `sleep 90` (stagger), so that launcher had not refused *yet* when the
Manager read the refusal from an earlier poll. The path fix landed, the sleeping launcher woke up, and it **did**
dispatch — producing a **duplicate session for the same task** (two writers, one write-set) on top of the re-issued
launch.

Rules:
1. Before the first dispatch: `grep -rn '<old-run-id>' tools/` and replace **every** hit; then
   `grep -rn '<old-run-id>' tools/ | head` must be empty.
2. A refusal notice is not final until the launcher process has **exited** — poll the process handle.
3. A staggering `sleep` is part of the command, so "it errored instantly" is unverifiable from the first poll.

### Recovery for a duplicate dispatch (one task, two sessions)

* Identify each live chain **by packet name in the cmdline**, not by launch order:
  `Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'hermes.exe' -and $_.CommandLine -like 'hermes -z*' }`
  then print the first ~190 chars of each `CommandLine` to map chain → packet.
* Keep the session with **more progress**; stop the newer chain **leaf→root, exact pids only** (never `/T`,
  never by name/port). Prove zero collateral by diffing the interpreter's pid set (see §2).
* Record the incident append-only in the ledger: it is **not** a task result. Disclose the **receipt/log name
  collision** — both launches wrote the same receipt path, so the receipt alone cannot identify the surviving session;
  the surviving session is proven by first-message == packet head instead.
* Re-hash the shared write-set at the end of the kept lane's round and disclose any file whose origin is unattributable.

---

## 2. PowerShell `$pid` is read-only — a stop-loop that uses it stops NOTHING, silently

```powershell
foreach ($pid in @(33592,34280,35952)) { Stop-Process -Id $pid -Force }   # ✗
# Cannot overwrite variable PID because it is read-only or constant.
# …and the script still printed its before/after counters, so the kill looked like a clean no-op.
```

Use `$procId`. Always **measure** the result rather than claiming it:

```powershell
$before = (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' }).ProcessId
foreach ($procId in @(<child>,<hermes>,<parent>)) { try { Stop-Process -Id $procId -Force -EA Stop } catch {} }
Start-Sleep 3
$after  = (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' }).ProcessId
"python before=$($before.Count) after=$($after.Count) gone=$(($before | ? { $_ -notin $after }) -join ',')"
"targets_alive=$((Get-CimInstance Win32_Process | ? { $_.ProcessId -in @(<child>,<hermes>,<parent>) }).Count)"
```

Accept only: `targets_alive=0` **and** `gone` == exactly the chain's pids. Anything else is collateral damage.

---

## 3. `exit 1` from `hermes -z` can mean "no final response", with the work fully landed

Measured: a lane exited **1** after 86 min, log = 72 bytes:

```
hermes -z: no final response was produced; treating the run as failed.
```

…yet the tree held a new commit, `porcelain=0`, `REPORT.md` and 25 evidence files. The same lane family also produces
`exit 0` when it merely ran out of turns. **Neither exit code is a verdict.**

Decision procedure when a launcher returns non-zero or the log looks like a flap:
1. `wc -c` the log. ~70–130 B with an API/CLI error line = infrastructure; several KB = a real report.
2. Measure the disk: `git log -1 --format=%h %s`, `git status --porcelain`, evidence-file count.
3. If the work is complete → accept it, record the exit-code caveat in the ledger, do **not** re-run.
4. If partially landed (dirty paths inside the allowlist, mid-list of TODO steps) → resume with a short *finish* packet
   quoting the lane's own remaining-steps list.

---

## 4. Judge liveness on the RESOLVED actual session id, never the requested parent

`--resume <parent>` mints a **new** session id. Querying the parent for "last activity" therefore reports the *old*
run's age and a healthy lane reads as a stall:

```
CONTRACT   rows= 76 age=341.3m   ← parent session (finished hours ago)
…after resolving:
CONTRACT   rows=157 age=  0.1m   ← actual continuation, actively working
```

Keep a resolver: for every session started after the wave began, read its **first user message** and match it against the
packet head (one packet per lane ⇒ the match is a proof, not an inference). Then:
* point heartbeat/liveness at the resolver's output;
* write the mapping (requested parent → actual id, with the proof method) into the session registry, so no later reader
  mistakes the parent id for the writer;
* if a worker self-reports an id, treat it as a claim — resolve from the read-only `state.db` first.

---

## 5. Cap enforcement is a process count, not a dispatch count

Four `hermes -z` processes can be alive while the bookkeeping says "3 dispatched" (a flap-retry plus a freshly queued
lane). Count the processes; when over the cap, stop the **newest** chain (least invested), log the row as
`STOPPED_OVER_CAP` with the reason, and keep the stopped lane's packet hashed on disk so re-dispatching costs one command.
See `references/verifying-a-new-lane-without-baseline.md` for the wave-level version of this recovery.
