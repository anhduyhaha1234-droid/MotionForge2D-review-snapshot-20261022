---
name: hermes-session-reminder
description: "Cron resume nudges to keep an idle Hermes session alive."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [cron, reminder, resume, watchdog, heartbeat, session-keepalive]
---

# Hermes Session Reminder (cron resume nudge)

## When to use
- User asks to periodically nudge a Hermes session (manager/worker) that tends to stall: "cứ 10-15p nhắc nó tiếp tục làm việc đi", "nhắc liên tục đến khi tôi bảo dừng".
- Keeping a long-running manager session alive over hours.

## Setup (verified pattern, Windows + bash)
1. **Script must be PYTHON, not .sh.** The cron scheduler on Windows mangles the joined path when running .sh (`C:\...` → `C:Users...` → "No such file"). .py scripts run via Python and handle Windows paths fine.
2. Script body — the one command that matters:
   ```
   hermes.exe chat -q "<cụm nhắc ngắn>" -r <SID> -m <MODEL> --provider <PROVIDER> -Q
   ```
   **ALWAYS pass `-m` and `--provider` explicitly.** Resuming without them uses the profile DEFAULT model (seen: `model=meta` via 9Router — a banned/wrong route) even though the session's `model_config` says something else.
3. **Read MODEL/PROVIDER from `state.db`** (`sessions.model_config` of the target SID) each time the user says "tôi đổi model rồi" — the DB is the source of truth; the user's shorthand may omit segments (`cmc/muse...` vs `cmc/meta/muse...`).
4. Cron job: `no_agent=true`, `script` = bare filename (resolves under `~/AppData/Local/hermes/scripts/`), `schedule` `*/N * * * *`, `deliver=origin`. Script must be silent on success (stdout empty) — no-agent jobs deliver stdout verbatim, and desktop chat has no delivery channel anyway.

## Logging every nudge's reply (so progress can be reported later)
- `subprocess.run(cmd, capture_output=True)` **SWALLOWS hermes chat output** — the log ends up with only `start/exit` frames and no manager reply. Use:
  ```python
  with open(LOG, "a", encoding="utf-8", errors="replace") as f:
      rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
  ```
- Expected quirk: the reply text may appear BEFORE the `=== start ===` line in the file. Cause: the file handle buffers Python writes while subprocess writes go straight to the fd. Content is complete, order is shifted — do NOT "fix" it.
- Keep one log per managed session (`remind_s11_3.log`, etc.) so histories don't mix.

## Template
- `templates/remind_session_template.py` — ready-to-copy script: retry 1x on exit 1/2, start/exit/end frames with flush, silent on success.

## Verification when user asks "nhắc chưa?"
- Read the remind log blocks + cron list `last_status` **AND** grep `agent.log` for the target session:
  - `conversation turn: ... msg='tiếp tục làm việc đi'` — nudge actually entered the session.
  - `API call #N: model=<real model> provider=<real provider>` / `Turn ended ... model=...` — confirm the ACTUAL route used (never trust cron `job.model`, it shows null unless set elsewhere).
- Evidence of a live manager: new `tool`/`assistant` messages in `state.db` after the nudge time.

## User preferences (VN MotionForge2D user — embed, don't re-negotiate)
- Progress/report tables MUST carry a **"giờ nhắc" column** (the script start time of each nudge). User complained once: "sao trong bảng ko có giờ nhắc?"
- The nudge message stays the **exact short phrase** ("tiếp tục làm việc đi") — NEVER append task lists, todos, or context. User: "chỉ cần nhắc nó tiếp tục làm việc thôi ko cần đưa list lại".
- Cron cannot deliver into the desktop chat (gateway off: scheduler logs `deliver=origin but no origin or home channels — skipping delivery`). Worse: with the gateway down, cron jobs do NOT fire at all — `hermes cron status` prints `Gateway is not running — cron jobs will NOT fire`, so even the script never runs and no log lines appear. Always check `cron status` right after creating the job: if the gateway is off, tell the user plainly (`hermes gateway install` to enable, or fall back to a terminal background watchdog process) instead of claiming "heartbeat đã dựng xong". Give the user a live view instead: background `tail -f <log>` process + `focus_pane(terminal)`, and answer every "báo cáo" ask by reading the log.
- Pre-create checklist (new sprint = new reminder): `cronjob list` FIRST — if an older reminder targets the SAME session (e.g. S11 reminder still nudging the manager session now running S12), `pause` it before creating the new one. Two active reminders on one session = double-nudge every cycle, confusing progress reports.

## Pitfalls
- **Job stuck `already running`:** if a nudge run lasts longer than the schedule, the scheduler marks the job running and skips every later tick (`cron.scheduler: Job '...' already running — skipping` in agent.log). Fix: `cronjob pause` → `cronjob resume` (resets the flag), then `cronjob run` to confirm.
- **NEVER use agent-mode (`no_agent=false`) for the reminder**: the cronjob tool cannot set a model (`job.model` stays null in list) so the LLM job runs the profile DEFAULT model (seen: `meta` via 9Router — wrong/banned route) and delivery is skipped anyway. Always `no_agent=true` + a pure script.
- **Desktop UI does NOT auto-refresh message injected by CLI resume**: the nudge exists in `state.db` but the open desktop session does not show it → user says "sao ko thấy nhắc". Explain: reload/reopen the session, or point at the log — the nudge IS running.
- **Switching target session** (user: "đổi sang session này"): patch `SID` (from user), re-read `MODEL`/`PROVIDER` from `state.db`, use a NEW log file per session (`remind_s11_3.log`), then run once by hand and verify via `agent.log` `Turn ended ... model=<real>` before trusting cron.
- **FreeUsageLimitError HTTP 502** (e.g. `ocgfree/...-free`): provider rate limit, often for many minutes. In-script retry doesn't help — wait or switch route. Not a script bug.
- **Concurrent resumes of the same session** (cron nudge + desktop turn + manager→worker nudge) can transiently fail: `turn was stopped because session storage could not be written`. Check disk (usually plenty), DB journal_mode WAL fine → it is a temporary SQLite lock; the next tick or a manual retry succeeds.
- **App restarts:** cron table can lose jobs or leave stale state — after a restart, `cronjob list` to confirm the reminder still exists and is scheduled; recreate if gone.
- **Schedule updates:** `next_run_at` may lag one tick after `update` — verify with `list`, and check the log for the first fire of the new cadence.
- Don't `killall` python (Hermes itself runs on it) — kill the exact PID of the orphaned nudge subprocess if needed.
- **Wrapper failure ≠ worker failure — verify ground truth before retrying.** The `-Q` resume wrapper can time out (Manager-side 180s) or exit 1 with `API call failed after 3 retries: Connection error` WHILE the prompt already entered the session (visible as a new `user` row in `state.db`) and the worker still executes (bytes land in the worktree minutes later). Rule: after ANY non-zero wrapper exit, check ground truth BEFORE retrying — (a) newest messages in `state.db` for that SID, (b) fresh bytes in the WT (`git status --porcelain`). If either moved → do NOT retry, do NOT double-prompt; just monitor. A blind retry stacks two overlapping orders on the worker.
- **Direct-write escalation for context-reading stalls.** When a worker reads context for >~20–30 min with zero bytes (WT pristine, messages only survey/reading, no `write_file` calls), generic nudges ("báo trạng thái + viết tiếp") don't break the loop. Escalate to a DIRECT-WRITE order: name the exact files + their structural skeleton, forbid reading any further file ("đọc thêm là vi phạm lệnh"), demand byte counts back in the same turn. Proven: one worker went 0 → 647 lines (conftest 455 + test-F 192) in a single turn after this order.