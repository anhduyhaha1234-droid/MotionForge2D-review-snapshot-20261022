# MotionForge2D overnight manager — autonomous continuation protocol

Use when you are the overnight/background manager for MotionForge2D with authority to keep the
PM-gated sprint moving without a user present, until a hard cutoff time. Also applies to any long
autonomous run over a worktree.

## Authority & model rules

- Single worktree allowed: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
  `codex/s08-integration`, HEAD pinned. MAIN `C:\Users\Admin\MotionForge2D` is read-only/protected —
  never migrate MAIN or a user DB, no commit/push/merge/reset/clean/stash/restore/checkout.
- Everything (code writers AND read-only reviewers) runs `ocg/deepseek-v4-flash` @ provider
  `custom` (9Router 127.0.0.1:20128), reasoning `max` (config-only — no CLI flag). Never Muse Spark,
  never fallback. One code writer at a time; never reuse a closed session for a new task.
- Writer session verification: confirm the model from `state.db` newest `source='tool'` row
  (`.model` column), not from the log head. Record session id + model in MANAGER_STATE/REPORT.
- On 502/disconnect: RESUME the same new session; never spawn a second writer; record outage/
  recovery; distinguish active-model time vs total wall-clock.

## Queue & phase gating (overnight)

- PHASE 1 = current correction (e.g. S08-A02-T01-R1-C1). PHASE 2 = downstream (e.g. R2 schema/API)
  ONLY after PHASE-1 manager verification fully passes. PHASE 3 = read-only planning/audit after
  code finishes or blocks. Logged no-code: renderer/dense flow/video regen/frontend/S07/S09/etc.
- No new code writer after the code cutoff (e.g. 06:00+07). Finish a near-done bounded task, never
  open the next packet. 06:00→07:00 = verification/regression/baseline/handoff work only.
- At or before handoff time send OVERNIGHT HANDOFF: completed/blocked tasks, exact session ids +
  model/provider/reasoning, active duration, wall-clock, downtime/recovery, files per packet, scope
  deviations, writer vs manager test counts, baseline Run ids, protected hashes, Codex status,
  outstanding findings, planning paths, recommended next action.

## Packet-first bookkeeping (between writers)

- Append the prior task's Codex verdict + any timestamp correction to its REPORT BEFORE creating
  the next packet (append-only; never silently edit history — see
  `references/s08-a02-r1-c1-semantic-correction.md` for the UTC-offset pitfall).
- Update MANAGER_STATE only between writers (before launch / after exit / between packets) — never
  while a writer is running. Do not write MANAGER_STATE during another writer's active window.
- Snapshot before launch: git status, production file hashes, protected MAIN hashes, process/
  listener state, local + UTC timestamps (derive UTC with `TZ=UTC date`, never hand-offset).
- Create the full packet (TASK/START_PROMPT/LOG/REPORT) with an exact write allowlist + forbidden
  list BEFORE launching the writer. Forbidding the same categories every round (schemas/API/
  frontend/S07/S09/8 head-bump test files/MAIN) keeps recovery rounds from widening scope.

## Parallel read-only reviewer lanes

- While a code writer runs, up to 2 reviewer threads may run in parallel (identical model).
  READ-ONLY absolute: no filesystem writes, no migrations, no server starts, no MANAGER_STATE
  edits, no commits, never becomes a writer.
- RO-1: independent code/contract review of the writer's areas (state machine, ownership, CAS,
  idempotency, negative-test gaps) → findings list to the manager, never self-fixes.
- RO-2: preparation/design for the NEXT task (e.g. T02 wiring), no code.
- Launch via delegate_task background lanes; they inherit the mandated model and stay read-only by
  explicit instruction in the goal/context.

## Heartbeat / recovery cadence

- While a writer is active: heartbeat ≤ every 5 min naming session id, phase, last real progress,
  running test, blocker. No-progress 8 min → check process, log tail, provider/listener, pending
  input; 10 min silence is the max. No long blocking sleeps; long tests run as bounded background
  procs with logs. Remember: a one-shot `hermes chat -q` writer has NO user notify channel — poll
  its REPORT/LOG status and surface BLOCKED/DECISION_NEEDED yourself (see
  `references/s08-writer-blocked-scope-audit.md`).
- User check-ins are heartbeat opportunities, not interruptions. The user WILL ask "bao cao tien do"
  (status), "bao lau nua thi xong" (how much longer), "xong chua" (done yet?) mid-overnight. Answer
  IMMEDIATELY (same turn) with a compact status table: writer session id + uptime, phase, files/tests
  done so far, current test/proc, and a real ETA derived from the writer's pace and remaining
  validation steps. Proactively push progress rather than waiting to be asked — the user explicitly
  complained ("sao block lại ko có heartbeat để thông báo?") when the manager went quiet while a
  writer sat BLOCKED. A blocked writer must be surfaced as a decision request at the same cadence, in
  the user's language (Vietnamese).

## Manager verification discipline

- Never trust the writer REPORT alone: re-run import, focused suites, regression, ruff/mypy,
  diff --check, migration parity/round-trips, fresh 7/7 baseline, protected hashes, no-listeners.
- Bounded correction cycles: same model, same scope, ≤2 cycles, each with finding/fix/test/
  evidence. After 2 failures → BLOCKED, no downstream phase; pivot remaining threads to read-only
  planning (keep working usefully, never idle).
- Pass state for a correction (e.g. C1):
  `MANAGER_VERIFIED_FOR_OVERNIGHT_CONTINUATION_PENDING_CODEX_REVIEW` — then PHASE 2 may launch.
