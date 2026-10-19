# Continuous heartbeat & anti-stall — S09 lessons (2026-08-26 → 2026-08-27 C5)

## Cadence per phase (prompt-authoritative)
- Rules §7 default: heartbeat ≤20 min + audit 8 min. Prompt overrides win:
  - **S09-C4 Muse (26/08)**: user `heartbeat mỗi 5' đi tôi thấy coding chạy hơi chậm` → 5' until slow phase passed.
  - **S09-C4-META (27/08)**: user `nhớ heartbeat mỗi 30p để báo cáo kết quả ... hoặc khi có task xong/có vấn đề` → **30' + instant on lane exit/blocker** (prompt `S09_C4_META_COMPLETION_MANAGER_2026-08-27.md`).
  - **S09-C5 bounded correction (27/08, `S09_C5_FINAL_CORRECTION_MANAGER_2026-08-27.md` §5)**: `No blind sleep / Poll bounded / 8 min no-progress → one continuation / 20 min no-progress → inspect & recover same owner` + heartbeat ≤20 min while any lane active. **C5's 20' overrides C4-META's 30'** — always honor the current prompt's cadence.
- Every heartbeat: task/session, effective route (meta/alpha), phase, new progress, latest log, blocker, next action, slot usage/free. Run `date` first — never invent timestamps. Scope growth mid-sprint → say plainly, update ETA.

## Go-command + ETA (user frustration signal)
- User `chạy đi sao m cứ tự dừng xsuoost thế` (15:40 +07, 27/08) and `estimate bao gio xong` mid-DAG = FIRST-CLASS frustration skill signal, not just memory.
- When a go-command arrives together with an ETA question, answer BOTH in the **same first reply**: dispatch confirmation + status + concrete ETA table immediately. Do not defer the estimate to a later heartbeat.
- Manager must `monitor -> review -> correction/resume -> verify -> report` continuously to the authorized terminal; do not stop because one worker replied or a join is pending. J1/J2 are manager-owned verification — launch immediately after writer exits and writers are quiescent. Keep polling with `process wait` loops and resume same owner on any stall/exit; reply instantly with dispatch confirmation + ETA table. User `chạy 24/24` = continuous execution mandate — embed in skill, not just memory.

## Silence is not neutral
- User watches and WILL ask `sao thấy dừng rồi?` / `xong chưa` if no visible message. Silence has only three legitimate causes: workers running, waiting on a join gate, or parked at terminal awaiting Codex review — STATE WHICH ONE proactively in the heartbeat that closes a phase. After writing terminal, say explicitly that stopping is protocol, not idleness.

## Pipe truncation bug (2026-08-26)
- `hermes --resume ... | head -n 200` causes SIGPIPE killing worker after 200 lines → log not flushed, msg count flat. Fix: never pipe through head; redirect to file `> manager-c4-muse/t04-muse-dispatch.log` and `background=true`. Killed PID 29096, redispatched 22:37 correctly.

## Muse Spark / meta cold prefill
- `ocg/muse-spark-1.2-contributor` reasoning max + 150k-token prefill → TTFB cold 15-47 min; use `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`, don't kill early in 8' audit if ESTABLISHED.
- `meta` combo (round-robin `cmc/meta`+`ocg/muse-spark-1.2-contributor`, 27/08) same 900s requirement; probe `hermes -m meta -z "ping"` → pong 200.

## Freeze drift after wave
- J0-MUSE 21:43 MATCH 13/13 but after T04 00:32 DRIFT 7/13 (renderer files). Don't auto-pin v5 — stop `BLOCKED_FREEZE_DRIFT` per §4. Audit via `git show HEAD:file | sha256sum` vs disk vs manifest `ae92247b...`.
