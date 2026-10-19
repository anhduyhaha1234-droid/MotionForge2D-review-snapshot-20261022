# Turn-Chaining Playbook — rescuing a worker after "no final response" / mid-turn cuts

Companion of SKILL.md dispatch/monitor sections. Session-proven on S10-C6B
(2026-08-31 → 09-01): T01C-C9 cut mid-flight, rescued in 2 chain turns;
T04B-C3 chained through a 16/20 first full run to 20/20; T04C-C5 chained
through a blocked prevalidation discovery. S10-C6C (2026-09-01) T01C-C10
chained 5 turns: exit-2 ×2 (zero-land, partial-land), exit-1 with landed RED
tests, exit-0 implement-then-cut, exit-0 gates-only — one chain pattern
absorbed all four shapes without ever opening a new session.

## When to chain vs when to block

- `WORKER_EXIT=1` ("no final response was produced") OR `WORKER_EXIT=2` with an
  EMPTY dispatch.log, but the write-set/LOG tail shows REAL landed work → chain
  (same session, resume) after a resume-form liveness probe passes. Exit 2 hit
  twice consecutively in C6C (T1 zero-land, T2 partial-land) and both chained
  fine — empty-log exit codes on long owner sessions are rescue triggers, not
  evidence of session corruption. Do NOT report BLOCKED; do NOT create a new
  session.
- Worker exits 0 but its final message ends with an explicit "Chưa làm /
  Còn lại / KẾ HOẠCH CHO TURN KẾ" list and no terminal STATUS → chain, feeding
  its own plan back as the next prompt.
- Chain indefinitely is allowed by iteration rules (same owner session) — the
  limit that matters is evidence progress per turn, not turn count.

## Chain-turn prompt recipe (proven, short ≤20 lines)

1. Header: `# <TASK>-C? CONTINUATION (turn N — bạn bị cắt giữa chừng / theo đúng kế hoạch bạn vừa ghi)`.
2. "Trạng thái đã verify (Manager):" — enumerate what the Manager INDEPENDENTLY
   verified (grep symbol, mtimes, gate codes), so the worker does not re-read
   everything from scratch (context-compression is what killed it).
3. Numbered steps = the worker's own remaining list, verbatim where possible,
   in its own order (validation plan, fix suggestions, fallback if race X).
4. Guards section repeated compactly (worktree/branch/HEAD/no-git-ops/DB env
   UNSET/allowlist/model = exact packet-ordered selector).
5. Anti-loss instruction: append LOG.md after EACH completed step group (a
   worker that logs as it goes can be resumed by anyone mid-flight).

## Mid-chain verification narrows the next prompt (C6C T4→T5)

Between chain turns, spend one cheap Manager probe on the landed bytes instead
of re-deriving the plan: (1) grep landed symbols + mtimes, (2) re-run the PREP
repro script, (3) run a focused `-k`-filtered test probe. In C6C, after the
worker's implement turn the repro flags had FLIPPED (orphan run → coherent
`failed`; false-reuse-200-zero-job → repair creating the exact queued job;
attempt-2 pending → `failed` non-active) and the focused suite showed 57
passed. That evidence let the next continuation prompt shrink to exactly the
remaining gates ("shakeout ×2 fresh roots → static → REPORT TASK_SUBMITTED")
instead of restating the full mandate — shorter prompts also survive context
compression better. Land-verification detail: a cut turn can land RED tests
(RED-first mandate) — a `-k` probe showing 2 failed / 1 passed is the CORRECT
mid-chain state; feed the landed line numbers + RED status back so the worker
implements against them instead of rewriting the tests.

## Manager housekeeping on every chain dispatch

- Registry line per turn: result of previous turn (honest — include exit 1s)
  + new dispatch (session id, pid, prompt file).
- Heartbeat cron: prefer a PID-LESS prompt (key on the dispatch log's
  WORKER_EXIT marker + log mtime + write-set mtimes) so a chain that
  re-dispatches with a new pid every turn never carries a stale pid making
  every tick report a false 'WORKER EXIT'. If the prompt does embed a pid,
  re-arm it on EVERY chain dispatch (C6C left one stale pid across 3
  re-dispatches before noticing). Cron jobs also expire after their repeat
  count — recreate + immediately pin the model via CLI (next section).
- Keep notify_on_complete=true so the chain continues the moment a turn ends,
  including instant reporting of turn 1 exit-1 events.

## Related lessons stored as one-liners here (details in SKILL.md)

- Long-basetemp WinError 206 (path too long in worktree) → run pytest with
  short basetemp under %TEMP% (mktemp -d style), e.g. `$(cygpath -m
  "$TEMP")/mfc9j6c_r1`. Fixture uses `\\?\` long-path form internally but the
  pytest basetemp itself must be short.
- `hermes cron edit <id> --model <exact-selector> --provider custom` is the
  only way to pin a cron job's model (cronjob tool schema has no model field;
  without this the job runs on model.default which is meta). The worker
  selector is PACKET-DRIVEN per correction round, never a standing constant:
  C6B ordered `comboBAI`, C6C ordered direct `BAI/glm-5.3-flash` with explicit
  `--provider custom` (comboBAI forbidden that packet). Probe the exact
  selector fresh AND on the resume-owner session before dispatching; wrong
  route = BLOCKED_MODEL_ROUTE.
- Worker final response is the cheapest source of the next prompt: it always
  contains an honest "Còn lại" list + risk callouts + recommended resume
  command. Quote it back verbatim instead of re-deriving the plan.

## Longest node chains are the NORM, not the exception (C6B final data)

Per-node turn counts from the full sprint: T01C-C9 = 3 turns (death-recovery →
fences → shakeout), T04B-C3 = 3 (16/20 → mirror → docs), T04C-C5 = 4 (prep →
prevalidation-block → fixture patch → bundle-sync+runs+docs). Plan and message
ETAs around 3-4 chain turns per heavyweight node, not 1 — a "one dispatch does
everything" assumption is what produced the ETA drift the user called out. The
chaining mechanics (feed the worker's own handoff list back, one registry line
per turn, re-arm cron pid, keep prompts short) scale fine to 4+ turns; the
failure mode to avoid is re-sending the full original prompt, which re-triggers
context compression on long owner sessions. C6C raised the ceiling again:
T01C-C10 = 5 turns for a 2-finding correction under the GLM selector
(exit-2 ×2 → exit-1 RED tests → exit-0 cut-after-implement → exit-0
gates-only) — plan 3-5 chain turns per correction node when the packet orders
`BAI/glm-5.3-flash`, and price the ETA accordingly.

## The anti-"delay" answer format (C6C, "sao cứ delay suốt thế")

When the user asks "xong chưa / bao giờ thì xong / sao cứ delay", the reply
shape that landed (no complaint afterward):

1. **Lead with what LANDED since the last check-in** — a small table of chain
   turns with the concrete verified output each produced (tests RED, repro
   flipped, 57 passed, shakeout ×2). This reframes "delay" as per-turn
   evidence progress instead of idleness; it only works because the Manager
   verifies landed bytes (mtimes/greps/repro) rather than trusting reports.
2. **Name the cause plainly** ("GLM bị context-compression kill giữa turn,
   mỗi lượt 30-60'") — no vague "complications". The user is technical.
3. **ETA table anchored to a fresh `date`**, with an explicit worst-case row
   (+1 resume buffer per remaining chain turn), and honor it by reporting
   INSTANTLY when a turn completes (notify_on_complete → run the next gate in
   the same turn) — a finished turn sitting unreported is what actually reads
   as "delay" to this user.
