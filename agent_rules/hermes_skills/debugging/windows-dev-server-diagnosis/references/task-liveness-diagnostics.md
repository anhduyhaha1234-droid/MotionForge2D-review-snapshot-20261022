# Task Liveness & Death Diagnosis — Working Transcript (2026-08-04)

Real case: user asked "có đang chạy ko" then "task thấy dừng 10p rồi" about a
MotionForge2D worktree batch task (S06-T05, Hermes CLI + `ocg/mimo-v2.5`).

## Full diagnostic sequence that worked

```bash
# 1. Hermes-managed bg processes (EMPTY here — misleading; task ran via run-.ps1)
process(action='list')          # -> {"processes": []}

# 2. Ports + process map
netstat -ano | grep LISTENING | grep -E ":(8000|8002|9495|3000|8080|5000|5173)\b"
wmic process where "ProcessId=121396 or ProcessId=100008" get ProcessId,CommandLine
#   -> 3000: next dev (MotionForge2D frontend)
#   -> 8002: uvicorn --app-dir .../s06-t01-review (backend being reviewed)
#   -> 8888: second uvicorn --reload (stale; user said leave it for Codex)

# 3. CPU/start time to tell alive-but-idle from dead
powershell -NoProfile -Command 'Get-Process -Id 9372 | Select Id,ProcessName,CPU,StartTime,Responding | Format-Table -AutoSize'

# 4. Find task artifacts in worktree output/
ls -lt MotionForge2D-worktrees/s06-t01-review/output/
#   -> run-s06-t05-mimo.ps1, s06-t05-mimo.pid (126068), s06-t05-mimo-hermes.log

# 5. PID alive? (tasklist //FI with DOUBLE slash)
PID=$(cat output/s06-t05-mimo.pid); tasklist //FI "PID eq $PID"   # empty => DEAD

# 6. Log mtime = death time
stat -c "%y %s bytes" output/s06-t05-mimo-hermes.log
#   -> 22:05 vs now 23:25 => died ~1h20m ago, NOT 10 min ago (user's estimate wrong)

# 7. Read the UTF-16 log (Tee-Object => UTF-16LE, grep sees \u0000 garbage)
tail -c 2000 output/s06-t05-mimo-hermes.log | tr -d '\0' | grep -aE "Error|failed|Resume"
```

## Death signature found

```
Error: HTTP 502: [opencode-go/mimo-v2.5] [502]: fetch connect timeout (reset after 21s)
API call failed (attempt 1/3): InternalServerError [HTTP 502]
Retrying in 2.4s...
API call failed (attempt 2/3): InternalServerError [HTTP 502]
Retrying in 5.6s...
API call failed (attempt 3/3): InternalServerError [HTTP 502]
API failed after 3 retries: HTTP 502: [opencode-go/mimo-v2.5]
Resume this session with: hermes --resume 20260804_215215_39cac1
Duration: 12m53s   Messages: 14 (1 user, 13 tool calls)
```

Key insight: the opencode router on :20128 was ALIVE (`curl /v1/models` → 200,
PID 143644 node.exe) while the model behind it (mimo-v2.5) kept 502ing on connect.
Router alive ≠ model healthy — check both before blaming the task.

## Why user's "10 minutes" estimate was wrong
User said "dừng 10p rồi"; log mtime proved 1h20m. Always verify with the log
mtime / PID liveness — never accept the user's time estimate as ground truth,
and report the REAL timestamp as evidence.

## PowerShell-via-bash quoting trap (hit twice this session)
`powershell -NoProfile -Command "... $_ ..."` broke:
- `$_.ProcessName` became `.ProcessName` → bash treated it as a command
- `foreach($id in ...)` got mangled by `$()` / `$id` expansion
Fix: wrap the ENTIRE PowerShell command in single quotes:
`powershell -NoProfile -Command 'foreach($id in 126068,42008){ Get-Process -Id $id -ErrorAction SilentlyContinue }'`

## Also useful
- `wmic process where "Name='python.exe'" get ProcessId,CommandLine` — find all
  instances of a binary with their launch commands (identified the 3 python
  servers + hermes desktop + hermes serve in one shot).
- `tasklist | grep -iE "codex|node|python"` — quick name scan; `codex.exe` here
  was the desktop app-server, NOT a `codex exec` task (no exec tasks running).
- PID file content check: `cat output/<task>.pid` (6 bytes, e.g. "126068").
- run script pattern (PowerShell): `& hermes chat --query $prompt --source cli
  --max-turns 260 --provider custom --model ocg/mimo-v2.5 --pass-session-id
  --checkpoints 2>&1 | Tee-Object -FilePath ... -Append` — the `--checkpoints`
  + `--pass-session-id` flags are what make `--resume <session_id>` possible.
