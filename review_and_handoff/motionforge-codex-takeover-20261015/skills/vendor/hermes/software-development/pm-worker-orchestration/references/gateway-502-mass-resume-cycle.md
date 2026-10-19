# Gateway 502 mass-death → same-session resume cycle

Proven on S12-R7 (2026-09-16): upstream flapped twice (deaths ~17 min apart), killing ALL running
Hermes-CLI lanes within one 19-second window each wave. Every lane was recovered by resuming the
SAME session — zero work lost, zero redo.

## Failure signature
`API call failed after 3 retries: HTTP 503: [<provider>/<model>] [502]: fetch connect timeout`
→ worker turn dies with exit 1. Per autopilot rules §7 this is TRANSIENT, never terminal:
loop `wait ≥5 min → liveness probe → resume same session/route/scope` (unlimited while transient).
Do NOT treat as auth/quota/config error; do NOT switch model/route; fallback stays OFF.

## 1) Detection (fast triage, per lane)
- bg exit notice arrives, or console mtime stalls.
- Console markers: append `echo "RESUME<N>_EXIT=$?" >> console` after every dispatch/resume —
  `grep -c "RESUME2_EXIT" <console>` = how many times that lane died; exact death time = console mtime.
- Which lanes are LIVE right now (extract session id from process cmdline):
```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'chat -q' } | ForEach-Object { if ($_.CommandLine -match '-r (2026091[0-9_a-z]+)') { Write-Output $Matches[1] } else { Write-Output 'NEW' } }
```
  This also reveals OTHER managers' lanes (in two-manager waves) — observe only, never touch.

## 2) Byte-safety audit BEFORE resume (per dead lane)
- `git status --short` in each worktree:
  - committed + clean → check `git log`; usually only the final report is missing.
  - `M`/`??` entries → uncommitted work is INTACT; session continues in the same worktree (single writer preserved). Do not fix, do not stash, do not reconstruct.
- Record per-lane verdict in the incident doc; never "paper" the state from memory.

## 3) Liveness probe
`timeout 150 hermes chat -q "Reply exactly: PROBE_OK" -m <model> --provider custom -Q --max-turns 2`
- Healthy ≈ 20–25 s. Hangs/timeout (e.g. 240 s) = still down → wait more, re-probe (don't burn a resume).
- The probe creates a NEW disposable session (session id printed; record + ignore). Probe sessions do NOT prove lane health — only route health.
- Local gateway `GET /models` HTTP 200 does NOT mean completions are healthy (upstream fetch timeout lives beyond the local gateway).

## 4) Resume
```bash
sleep 30; cd <worktree> && hermes chat -q "<continuation nudge>" -r <SAME_session> -m <SAME_model> \
  --provider custom -Q --yolo --accept-hooks --pass-session-id --max-turns <N> >> <same console file> 2>&1; \
  echo "RESUME<N>_EXIT=$?" >> <same console file>
```
- `>>` APPEND mode: one console per lane across all waves; count waves via RESUME markers.
- `sleep 30` guarantees the full ≥5-min wait is observed by the time the API call starts.

## 5) Continuation nudge template (worked 3/3 lanes, 2 waves)
- Open: `Tiếp tục làm việc đi.`
- Reassure: `Lượt trước bị ngắt bởi lỗi kết nối gateway tạm thời (HTTP 503/502) — KHÔNG phải lỗi của bạn; route/model/scope/allowlist không đổi.`
- State pointer: enumerate exactly which files are modified/new (copy from `git status`) + tag `uncommitted`.
- Directive: `Verify nhanh state rồi tiếp tục đúng work order từ điểm dừng — <next steps>. Không làm lại phần đã xong. Không hỏi lại.`
- Report-only remainder: say it explicitly (`Chỉ còn thiếu REPORT cuối...`).

## 6) Incident doc (one file per day/incident, append waves)
Record: wave #, lane + death timestamp, byte-safety verdict, probe result + latency, resume time,
observed flap interval. Budget ETA buffers from real flap cadence (R7: ~5–10 min cost per wave).

## Pitfalls hit during this cycle
- Nested `$(grep -c ...)` inside quoted strings → command parser hard-block; keep incident commands flat (separate calls, no nested substitutions).
- PowerShell inline regex with escaped backslashes (`'B\\B01|...'`) → `Unrecognized escape sequence`; simplify to plain session-id extraction (shown above).
- Exit notices arrive LATE (minutes); always reconcile against real state (console mtime + process table), never against the notice alone.
