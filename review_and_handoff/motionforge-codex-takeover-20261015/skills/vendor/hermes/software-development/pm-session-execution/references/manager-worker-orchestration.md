# Manager-side orchestration of PM-gated worker sessions (Hermes CLI)

> NOTE: SKILL.md is near its 100KB size cap — this reference is the canonical
> manager-side playbook. Link it from worker prompts or read it directly when
> acting as dispatcher/monitor.

Lessons from live sprint management (MotionForge2D S09, Aug 2026) — dispatching,
monitoring, and resuming hermes-CLI worker sessions as the MANAGER agent.

## Liveness verdicts — trust nothing but log size + markers

- The ONLY reliable liveness signal is `stat -c%s` on the worker's dispatch.log
  sampled twice (≥40s apart) plus in-log markers (`EXIT=`, `session_id:`).
- Do NOT trust ps/tasklist/wmic PID mapping on Windows/MSYS — it maps wrong PIDs
  and has caused false "worker died" conclusions. Hermes background process list
  (`process(action='list')`) only shows Hermes-tracked procs.
- **Silent-death pattern** (observed twice in one night, likely provider/router
  connection drops): dispatch.log frozen at N bytes, zero python.exe processes
  in tasklist, NO wrapper `EXIT=` line appended. The wrapper's EXIT line is the
  tell: a clean exit always appends one; its absence means the whole shell tree
  was killed.

## Recovery protocol after silent death

1. Verify disk state yourself: which files did the worker actually write?
   Which test suites exist? Run the focused tests to measure real progress.
2. Write a **resume packet** file containing: verified done-state, exactly what
   remains, and the REPORT/STOP requirement. Point it at the specific half-done
   work ("you were patching X when you stopped").
3. Resume with `--resume <owner-session-id>` — NEVER create a replacement
   session; owner identity is a hard rule in most PM protocols.
4. Lost session IDs: query `C:/Users/Admin/AppData/Local/hermes/state.db`,
   table `sessions`, `ORDER BY started_at DESC`, then match each candidate's
   first user message against your task prompt text.
5. Workers that exit 0 *without* writing REPORT.md died mid-finalization —
   same recovery: resume packet that says "everything measured/done is on disk;
   only write REPORT.md + LOG append, do NOT re-run".

## Dispatch hygiene

- `mkdir -p` the log directory BEFORE `> path/dispatch.log` or bash dies before
  hermes even starts.
- Always dispatch with background=true + notify_on_complete. Foreground timeouts
  kill the parent shell while children keep running orphaned.
- Keep per-task evidence dirs separate (`t00-i02/`, `t01/`…) so write-set
  audits are trivial later.

## Baseline snapshots for additive-only proofs

Immediately at dispatch time, copy baseline versions of write-hot files (e.g.
models.py) into the task output dir. Later, `difflib.unified_diff` between
baseline and current proves "removed lines == 0" claims independently. Without
a pinned baseline this proof is impossible once workers start editing.

## Independent manager verification (never trust self-reports)

- Re-run focused test suites yourself: isolated basetemp under %TEMP%/mgr-*,
  `-p no:cacheprovider`, env guard unset (`env -u MOTIONFORGE_DATABASE_URL`).
- ×2 consecutive runs whenever the acceptance gate demands determinism.
- ruff/mypy on the exact files the worker touched, not the whole repo.
- For benchmark/measurement tasks: recompute hashes yourself (frozen SHA must
   match banner output), diff two result JSONs after stripping declared
   non-deterministic fields, and hash reference media yourself before believing
   "VERIFIED" status.
- Read the worker's REPORT.md tail for STATUS marker; grep dispatch.log for the
  final `session_id:` line to close the lineage chain.

## Parallel waves

- Parallel writers are safe ONLY when write-sets are fully disjoint AND each has
  isolated basetemp/output. One migration-chain task = single writer.
- Expect cross-talk noise: a sibling writer publishing a new migration mid-run
  can break another writer's fixture setup (27 fails / 187 errors style). The
  correct worker behavior is bounded wait-loop ≤10min + re-probe; the correct
  manager behavior is to attribute the failure correctly in the registry rather
  than blaming either worker.

## Registry discipline

Append-only registry entries at safe boundaries (after exits, between waves):
timestamp (+07 local AND UTC), session id, proc id, exit code, verified state,
next action. When a prior entry is proven wrong (e.g. "worker died" later
discovered alive), write an explicit CORRECTION entry — never rewrite history.
