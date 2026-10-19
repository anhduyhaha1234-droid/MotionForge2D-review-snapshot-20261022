# Continuous Execution & Proactive Reporting — PM-gated worker sprints

Trigger: user says "làm liên tục / chạy liên tục / sao cứ dừng", asks
"tiến độ / bao giờ xong / có đang làm không", or a Manager holds lanes
across long worker waits. Companion to `references/s11c1-watchdog-terminal-marker-design.md`
(watchdog mechanics) and `references/s11-isolated-worktree-full-sprint-playbook.md`
(sprint transport).

## 1. Never stop mid-task

- Every response either contains tool calls that make progress or delivers a
  final result. Never end a turn with only a promise ("sẽ làm", "đợi worker").
- After any dispatch, keep the chain moving in the SAME turn: verify the
  exited lane, then launch the next dependent node immediately.
- Worker EXIT (especially BLOCKED / NEEDS_* / TASK_SUBMITTED) is reported in
  the turn it arrives, BEFORE running the follow-up verify — one lead line
  with date, lane, terminal verbatim, tip SHA, and next step. Silent verify
  then "user has to ask" is the failure mode this file exists to prevent.

## 2. Status + ETA format

- Lead with status, then an ETA table anchored to a real `date` call:
  `date` → per-leg Expected / Worst → SPRINT_SUBMITTED Expected / Worst.
- ETAs carry buffer for worker death + max-reasoning latency. Scope growth →
  say plainly that the ETA pushes and why.
- No artifact = no progress. ETA-only updates without a new commit, gate
  count, or raw log path do not count as progress and must be labeled as such.

## 3. Heartbeat that actually reaches the user

- 30-minute fixed heartbeat + instant notify on done/blocker.
- Cron sessions with `chat_id=None` (gateway off) NEVER deliver to desktop
  chat — so the heartbeat must be a terminal background process (or
  notify_on_complete background task), never cron-only. A cron watchdog
  without a loop backup is a known silent gap.
- Watchdog itself stays SILENT unless it acts (nudge / BLOCKED signal);
  prove silence with consecutive OK log lines, not with claims.

## 4. Route pinning (no silent model drift)

- Every dispatch/resume pins provider + model + reasoning + fallback OFF +
  TTFB timeout explicitly. A resume missing the pin silently runs the
  profile-default model instead of the session's configured one.
- Connection/502/503/504/disconnect → log raw, wait ≥5 min, retry the SAME
  session once. Unknown model/auth/quota → `BLOCKED_MODEL_ROUTE`. Never
  fallback, never switch models, never open a replacement owner to dodge
  a route error.

## 5. Parallelism without collisions

- "Song song được thì chạy" = read-only gates + pre-stage the next node
  mid-flight (prompts, FF-ability checks, evidence dirs). Never run a broad
  suite over a scope a worker is actively editing.
- Maximum safe concurrency is stated per wave; dependency-serial lanes
  (integration → consumer) stay serial even under "run continuously" pressure.

## 6. Owner identity before dispatch

- Verify durable task/session ownership via a read-only state-DB query
  before first dispatch (first user message of each candidate session is
  ground truth: task ID + worktree + branch).
- A misrouted session is frozen from the task, disclosed honestly in
  LOG/REGISTRY (never rewrite history to hide it); only the exact owner
  writes the remaining work.

## 7. Write-set guard discipline

- One multi-path guard capture per preflight: repeated single-path captures
  OVERWRITE the manifest (last file wins). Pass all `--path` flags in a
  single invocation and assert the entry count after.
- Byte snapshot + manifest before any writer starts; `verify` after every
  lane; destructive shrink / scope drift → freeze the writer immediately.

## Anti-patterns (seen in S11-C1, do not repeat)

- Working silently after worker EXIT and only reporting when asked.
- ETA tables without a `date` anchor or without buffer for worker death.
- Cron-only watchdog while gateway is off (fires nowhere).
- Judging "stall" without reading the lane's terminal marker first
  (false BLOCKED after SUBMITTED).
- Single-path guard captures that silently discard earlier files.
- Falling back to another model when the pinned route errors.
