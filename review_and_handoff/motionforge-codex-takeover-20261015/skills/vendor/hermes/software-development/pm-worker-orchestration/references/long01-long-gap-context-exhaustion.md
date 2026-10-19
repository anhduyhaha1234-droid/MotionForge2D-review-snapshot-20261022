# Long-gap resume, worker context-exhaustion, hard quotas (verified 2026-10-07, LONG01)

Session: Manager resumed the MotionForge2D pipeline after a 5+ week gap. The
S10 sprint this chat had left mid-C1-correction was long `CODEX_APPROVED / CLOSED`
and a different long task (MF-DEMO-LONG-01 video run) was active. Raw evidence
extracts below; the distilled rules live in the SKILL.md section of the same name.

## 1. Recon order that caught the divergence

```
date                                  # 07/10 — 5 weeks past the chat's last state
git -C <worktree> log --oneline -15   # found "4cec376 feat(s10): checkpoint approved full-apply sprint"
                                      # (commit the old session never saw), above d3f6f79
ls -lat docs/pm/prompts/ reviews/     # newest: S11_C4_R5_... (06/09), S10_C6H_R3 (03/09)
head -n 80 docs/pm/CODEX_PM_HANDOFF.md  # "Current execution — 2026-10-07: USER_STOP..."
cat <RUN>/manager/registry/SESSION_REGISTRY.json
tail -n 8 <RUN>/manager/DISPATCH_LEDGER.jsonl
```

Worker's final RESUME_STATE.md (its own self-checkpoint) said:
`Block 3 ĐANG RENDER: S0031..S0041 xong; S0043 đang chạy; còn S0044` and
`usable_contiguous_prefix: 3899f/30 shot` — i.e. mid-flight, far from done.

## 2. Worker death by context exhaustion (looks like exit 0)

Receipt `LONG01_receipt_W2r.json`:
```json
{"exit_code": 0, "timed_out": false, "log_bytes": 3035409,
 "model": "cmc/deepseek/deepseek-v4.1-flash",
 "utc_start": "2026-10-06T17:46:26Z", "utc_end": "2026-10-07T09:10:38Z"}
```

`worker_W2r.log` tail — the real payload:
```
⚠️ custom stream drop (APIError) after 309.5s — reconnecting, retry 2/3
⚠️  API call failed (attempt 1/3): BadRequestError [HTTP 400]
   📝 Error: HTTP 400: This model's maximum context length is 1048576 tokens.
      However, you requested 1049030 tokens (917958 in the messages,
      131072 in the completion).
   ⏱️  Elapsed: 18.35s  Context: 1531 msgs, ~767,910 tokens
❌ Max compression attempts (3) reached.
Resume this session with:
  hermes --resume 20261005_235131_0caeab
Session:        20261005_235131_0caeab
Duration:       15h 24m 5s
Messages:       1530 (5 user, 1524 tool calls)
```

Interpretation: invocation limit, not completion. Rules §0.4 — resume the SAME
owner with a compact continuation packet; do not restart, do not re-feed history.
The `Resume this session with:` line is proof the old writer already exited.

## 3. False "worker alive" from a reused PID

`HEARTBEAT.jsonl` rows (stale, ~1h behind the wall clock at read time):
```json
{"exact_child_pids_recorded": [49016, 6284, 30064, 47672, 4632, 47972, 46332, 43104],
 "exact_child_pids_alive": [4632], "worker_alive_exact": true,
 "log_grew": false, "sec_since_growth": 4970, "stall_8min": true,
 "port_listen": "TCP 127.0.0.1:8188 ... PID 39004"}
```

Identity check on PID 4632 via `Get-CimInstance Win32_Process -Filter "ProcessId=4632"`:
```
Name: conhost.exe   CreationDate: 10/7/2026 12:48:41 AM   CommandLine: \??\C:\Windows\system32\conhost.exe 0x4
```
`conhost.exe`, not the worker — the console host outlived the dead child, so
"worker_alive_exact: true" was a false positive. The heartbeat's true signals
were the log fields: `log_grew: false`, `sec_since_growth: 4970`, `stall_8min: true`.

## 4. Hard quota shape (no retry loop)

Earlier same pipeline (Aug 28): `API call failed after 3 retries: HTTP 404:
[commandcode/meta/muse-spark-1.2-contributor] [429]: {"success":false,
"error":{"code":"RATE_LIMITED","status":429,"message":"You've reached your
weekly usage limit for your plan. Your limit resets at 2026-09-02T19:07:10.382Z."}}`

Rules §7 carve-out: quota/auth/config are NOT transient — report BLOCKED with the
exact payload + reset time, keep the checkpoint, never silently switch route.
Route changes come from the user's newest directive (here: `cmc/deepseek/deepseek-v4.1-flash`,
provider `custom`, api_mode `chat_completions`, fallback OFF).

## 5. Process/port sanity commands that worked (git-bash on Windows)

```bash
# Current processes with full command lines (single-quote the outer payload so bash
# does NOT eat $_ in the PS script):
powershell -NoProfile -Command 'Get-CimInstance Win32_Process | Where-Object { $_.Name -match "python|ffmpeg|node|hermes" } | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine | Format-Table -AutoSize | Out-String -Width 400'

# ComfyUI queue / history (empty queue = GPU idle, no pending render)
curl -s "http://127.0.0.1:8188/queue"        # {"queue_running": [], "queue_pending": []}
curl -s "http://127.0.0.1:8188/history?max_items=2"

# GPU
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
# -> NVIDIA GeForce RTX 5070, 5565, 12227, 2   (idle-ish, ~5.5GB residual)
```

Gotcha: `ps aux` is not available in this MSYS bash; `ps -o pid,comm` also fails
("unknown option -- o"). Use PowerShell `Get-CimInstance` instead.

## 6. Dispatch ledger read pattern

The ledger mixes real rows with harness policy tests. Row 17:45:52Z carried a
`test_note` marking rows 17:39:28Z..17:40:00Z as FAKE-CHILD tests (stall-kill
policy verification), not real dispatches. Always read the tail for `test_note`
rows before counting dispatches, and prefer the newest `action: dispatch` row
with `resume_session_requested` for the true last owner + packet SHA.
