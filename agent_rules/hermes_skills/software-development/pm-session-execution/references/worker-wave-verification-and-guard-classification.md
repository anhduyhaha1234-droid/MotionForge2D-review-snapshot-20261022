# Worker-wave verification, guard classification, and liveness signals

Session-derived recipes for a Manager dispatcher: how to turn a worker's "done" into
something you actually verified, how to run a write-set guard without false alarms, and how
to read progress when the log looks empty. All examples are real measurements, not sketches.

## 1. Turn "worker says done" into verified facts

Run these in order; each one has caught a real discrepancy.

| Check | Command shape | What it proves |
|---|---|---|
| Commit + lineage | `git -C <wt> log --oneline -3`; `git -C <wt> rev-parse HEAD^` | the claimed SHA exists and the parent is the expected base (no history rewrite) |
| Clean state | `git -C <wt> status --porcelain` (count must be 0 for a closed round) | nothing left uncommitted behind a `TASK_SUBMITTED` |
| Allowlist | `git -C <wt> show --stat --oneline HEAD` | every path is inside the task's exclusive write-set |
| Not pushed | `git -C <wt> rev-parse --abbrev-ref --symbolic-full-name @{u}` (fails = no upstream) and `git -C <wt> branch -r --contains <sha>` (empty = on no remote) | "local commit, not pushed" is true, not assumed |
| Re-run their own review command | the exact command the worker wrote in its report, run by you, timed and exit-coded | the report's headline numbers are reproducible |
| Determinism | hash the whole evidence tree before and after your re-run; diff | expect **only** the command-transcript file to change; everything else byte-identical proves the artifact is deterministic |
| Huge artifacts | full-file sha256 on the smallest N files + one mid-size file, compared to the manifest's `actual_sha256` | a 70 GB download set is validated without re-hashing all of it |
| The worker's own tests | run their test file yourself; read the negative-control output, not the summary | each negative control must report FAIL on the deliberately broken input, otherwise the assertion is vacuous |
| Route probe | hit the model/provider endpoint yourself and check the returned model id | the dispatch really used the ordered model, fallback never silently engaged. **Reasoning-model trap:** probed with a tiny `max_tokens` a reasoning model can return `content: ''` with every completion token spent on reasoning — that reads exactly like a dead route but is not. Re-probe with a generous cap (a few hundred tokens) and check the response's own `model` field before declaring `BLOCKED_MODEL_ROUTE`; a wrong-route verdict is a stop condition, so it needs a real failure behind it. |

Extra rules that paid off:
- **Attribute every failing item before escalating.** A guard or gate that says FAILED is a
  lead, not a conclusion: open the report and classify each entry (task-owned vs protected,
  signal vs artifact-of-your-own-setup) before writing an incident report.
- **A worker's self-disclosed failure is worth more than a green summary.** Keep the
  disclosure row in the final packet (`disposition: fail` with the note), never smooth it out.
- **Distinguish `RUNNING` from a blocker.** An agent CLI that hits its per-run tool cap must
  report `RUNNING` honestly with the artifact list; exit 0 alone means nothing.

## 2. Write-set guard without false alarms

The guard baseline has two distinct classes of file and they must not be mixed:

1. **protected** — source media, other tasks' trees, canonical docs, quarantine bytes. Baseline
   with SHA-256 / bytes / lines / mtime and re-verify: `status == VERIFIED`, `failures == 0`.
2. **task-owned** — the live task's exclusive write-set. Guard it with a **separate preimage
   manifest** (path, tracked/untracked/dirty, sha256, size, lines, mtime) plus byte snapshots.

Failure mode seen in practice: one manifest contained both classes, so after the writer did its
job the guard reported **7 `protected_file_changed` failures** that were entirely legitimate
edits by the task that owned those files. Correct handling:

- do **not** silently edit or delete the original manifest — write a
  `*-corrected.json` with the task-owned entries removed plus a `reclassification` block
  (moved paths, count, reason), re-verify against it, and publish both reports;
- every path the writer changed must be checked for **destructive shrink** (line/byte count
  must not drop). Growing files are the expected shape of a fix; a shrinking file is a stop
  condition;
- before dispatch, byte-snapshot any dirty/untracked file the task may touch and assert
  `snapshot_sha256 == source_sha256`. Snapshot is recovery evidence only — the Manager never
  copies it back over the implementation.

## 3. Liveness when the log is empty

- Launch long-running CLI workers with `PYTHONUNBUFFERED=1`. Python block-buffers stdout when
  redirected to a file, so a **0-byte log for many minutes is normal**, not a stall.
- Judge liveness from side channels, in this order: process table (is the launcher/agent process
  alive?), the tool's own **read-only** state DB (`message_count`, `tool_call_count`,
  `ended_at` / `end_reason`), artifact counts and mtimes on disk, and coarse resource deltas
  (e.g. free disk dropping 476 GB → 398 GB independently proved ~71 GB of weights had really
  been downloaded). Never from log size.
- `ended_at = NULL` in a session DB proves only that no close was recorded — it is **not**
  proof of liveness. Conversely a background-process completion notice can arrive late; poll
  state instead of blocking on the notification.
- A 60-second sampling monitor that appends one JSON row per tick (process count, GPU used,
  listeners, per-task log bytes, receipt presence) makes heartbeats cheap and gives a timeline
  to quote in the report. Keep it separate from the workers.
- Per-round budget: an agent CLI caps tool calls per run (order of ~90 for `hermes -z`), so one
  task legitimately needs 2–3 narrow rounds. Plan each dispatch as a round, and require the
  worker to commit + write evidence incrementally so a cap leaves recoverable bytes.

## 4. Owner lineage and the dispatch ledger

- `--resume <session-id>` **mints a new session id**; the old one is closed with
  `end_reason=agent_close`. Record parent → actual immediately in the session registry.
- Keep one append-only dispatch ledger row per worker round: task id, **actual** session id,
  packet path, packet sha256, packet bytes, model, argv shape, cwd, log path, receipt path,
  dispatch time. The receipt the launcher writes (exit code, duration, packet hash) plus the
  ledger is what makes "which owner did this round" answerable later without guessing.
- Corrections resume the **exact** owning session; a new task gets a new session. When a task
  has several rounds, the registry row reads `R1 → R2 → R3 (live)` so the chain is auditable.

## 5. Stale registry = no evidence

A registry written by a previous wave (hours or a power loss ago) describes history, not
current state. Re-derive every row at dispatch time: process table, listeners, GPU used,
worktree HEAD/branch/dirty, session DB rows. Report the reconciliation explicitly (including
any entry you had to correct, e.g. a declared path that does not exist) rather than quietly
dropping it.

## 6. Narrative vs artifact: reconcile, never accept either

A worker's chat summary and the artifact it wrote in the same run can disagree, and the
**artifact is the authority**. Real case: the final message claimed `SHUTDOWN_CONFIRMED` while
`SHUTDOWN.md` (same mtime as the JSON it contradicted) ended with `verdict:
SHUTDOWN_UNPROVEN` and `COLLATERAL DAMAGE — INCIDENT: [21092]`. Both cannot stand in one
evidence set, so neither may be reported as fact.

Procedure:

1. Take the strictest reading until evidence upgrades it: `SHUTDOWN_UNPROVEN` stays.
2. Confirm the **physical** end state yourself — it tells you which claim is even possible
   (`connect_ex` on the port, listener table, VRAM used, `tasklist` for the processes you must
   never kill).
3. Mine the worker's own dumps for the classification instead of asking it to explain.
   Here `listeners_before` held `127.0.0.1:64381 → 8210 ESTABLISHED 21092`, which proved
   PID 21092 was the worker's own client script — so the "collateral" was mis-classified by the
   worker's own classifier, not a real incident.
4. Dispatch a **narrow correction round** (evidence integrity only: no GPU job, no engine
   start, no media byte changed). It must rewrite the artifact so the verdict line matches the
   evidence, keep the superseded verdict as an in-file block, and add the correction to the
   report. Do not let the Manager silently edit a worker-owned artifact either.
5. Add the classification vocabulary to the artifact itself (`collateral_removed: []` plus a
   separate classified field) so the next reader cannot re-derive a false incident.

## 7. Freeze before you evaluate

Do not dispatch the evaluator on an artifact its owner is about to regenerate. In this session
the current clip was correct-but-superseded (the owner's next round re-exported it to fix the
audio window and container PTS), so scoring it immediately would have (a) produced rows for an
intermediate artifact and (b) violated "only frozen candidates get evaluated".

Rule: sequence **owner correction → byte snapshot of the final artifact → then evaluator**.
Announce the sequencing and its reason in the report, including the harness command already
staged for the evaluator (`run_dryrun.py --steps candidate --candidate <final> --source-clip
<source> --window-tag <TAG>`), so the wait reads as deliberate rather than as idle time.
