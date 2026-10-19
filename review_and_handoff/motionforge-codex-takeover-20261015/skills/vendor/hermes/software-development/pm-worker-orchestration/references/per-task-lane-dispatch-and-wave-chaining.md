# Per-task lane dispatch and wave chaining (delivery mode)

Context: a 28-task delivery where each task packet becomes its own lane under one delivery root.
Measured on the MotionForge2D delivery, 2026-09-28 (Phase B wave 1 + wave 2). Records the
mechanics that kept verified throughput high; complements the full-sprint worktree playbook.

## 1. One worktree per task, branched from an immutable wave SHA

- Task root: `<delivery-root>/<TaskID>`; branch `codex/<task>-<date>`; create with
  `git worktree add -b <branch> <path> <base-sha>` from the integration repo.
- **Base = the previous wave's tested commit** (wave-1's verified output becomes wave-2's base).
  Record that SHA in the ledger as the immutable wave SHA, and record `HEAD == base-sha` +
  `porcelain == 0` measured BEFORE dispatch.
- **When a task depends on ONE specific task, branch from that dependency's OUTPUT COMMIT** — not
  merely the wave base — so the dependency's code is physically in the tree (measured:
  MF-END-12 branched from MF-END-11's `8fa87b8`, MF-END-13 from MF-END-12's `50a50a6`). Note the
  chosen base + reason in the ledger row. A task whose tests import its dependency's modules will
  otherwise fail at collection and burn a round discovering it.
- Keep the evidence root OUTSIDE the worktree (`<RUN>/tasks/<TaskID>/…`). That is deliberate: the
  task tree stays porcelain-0 and the repo only ever contains allowlisted paths. When a worker
  notes "evidence root is outside the tree", that is design, not a defect.

## 2. Before-guard JSON (Manager, pre-dispatch)

Per task, write `manager/guards/<TaskID>_before.json`:

```json
{"task": "...", "head": "<sha>", "porcelain": 0,
 "paths": {"<write-set path>": {"exists": true, "bytes": N, "sha256": "..."}}}
```

plus the baseline test counts you actually ran at that commit (e.g. focused task file and one
cheap suite: `49 passed / 1 skipped`).

**Guard findings must be pushed INTO the launch packet when they change the work.** Two measured
cases: (a) a task whose write-set listed files that ALREADY existed → the packet must say "patch
bounded with preimage; not whole-file generation"; (b) a task whose target directory did not exist
at all → "create per allowlist". A worker that assumes (b) when (a) holds can overwrite a
protected module.

## 2b. Pins the Manager resolves by hand are claims — resolve them with the owning tool

Measured (2026-09-28): a guard pinned a migration `<live_head_child>` from a hand-rolled regex
scan of `migrations/versions/*.py` → `f7a8b9c0d1e2`. The real sole head, measured by the worker
with `python -m alembic heads`, was `d4e5f6a7b8c9` — the regex had missed a `down_revision` form,
so the pin was STALE. The worker chained the new migration to the MEASURED head and disclosed the
stale pin (correct behaviour). The Manager then fixed the method: the guard JSON now records
`alembic_heads` straight from `python -m alembic heads` (verified on the next task:
`f8b9c0d1e2f3 (head)`).

Rules:
- Any value the Manager pins by parsing files (migration head, schema version, model filename,
  current port) must come from the owning tool's own command, and the guard JSON must carry that
  command's raw output. A hand-rolled scan is a hypothesis, not a pin.
- When a worker overrides a Manager pin with a measured value, verify the measurement, accept it,
  log a `manager_guard_correction` row in the ledger, and change the method so the next task's
  guard cannot repeat it. Do not treat the override as a deviation.
- Migrations: assert a SINGLE head (`alembic heads` prints one line) before pinning; the new
  migration's `down_revision` chains that head; never leave two heads in one tree.

## 3. Launch packet = wrapper, not a replacement for the task packet

Pin in the wrapper: model/provider/fallback-off, worktree path + base SHA, evidence root, and an
explicit mandate to read the ORIGINAL task packet (acceptance / micro-jobs / write-set are the hard
boundary). Then **transfer the verified facts the worker would otherwise rediscover** — for a graph
task: the measured registered-vs-missing node list and the exact path of a graph that already ran
on this runtime. That turned "research the template" into "reuse and verify".

Retry clause in every packet: on API error stop clean and print the log line; Manager waits ≥5 min,
then resumes the SAME session/model/scope. Also state the payload discipline (see §6).

## 4. Wave selection

- Pick tasks with **disjoint write-sets**; record the shared-file audit in the ledger even when it
  comes back empty.
- Cap = Manager + 2 workers (the Manager's own stream counts).
- **If no dependency-ready disjoint task exists, leave the slot idle and record the reason**
  ("all other tasks depend on L0, still running"). Do not manufacture busywork to fill a slot and
  do not start a task whose dependency is only "probably fine".
- Dependency layers are not automatically parallel waves: L0 alone in wave 1; L1 fans out in wave 2
  once L0's commit is the base. A layer with one member is still a wave.

## 5. Verify on exit, then dispatch the next task in the same turn

Worker exit → verify before believing anything:

1. commit exists; `git show --stat` == exactly the allowlist paths (count files);
2. `git branch -r --contains HEAD | wc -l` == 0 (not pushed);
3. re-run the task's focused test file AND the broad suite in that tree yourself; quote your counts;
4. `git status --porcelain` afterwards.

Then immediately dispatch the next dependency-ready task into the freed slot (report + chain in one
turn). Dead time between a verified exit and the next dispatch is the main throughput waster in
this mode.

## 6. Last-step failures after the work already landed

Provider flaps can kill a worker on its LAST step — after artifacts, gates and assembly are on disk
and only the REPORT/LEDGER appends remain. Measured: HTTP 422 `messages.<n>.tool.content.str`, 502
`ERR_HTTP2_STREAM_ERROR`, 503 — two consecutive deaths with all GPU outputs present.

- Before relaunching anything, **open the disk**. If every listed artifact exists and only the
  doc/report appends are missing, relaunch a SHORT finish-only packet (docs + index refresh) against
  the same session — never re-run the round.
- Payload discipline to write into every packet: print ≤200 chars per command, write files via
  scripts, never `cat` large files. Oversized tool payloads are the visible correlate of the 422
  family.
- After two flaps on the same packet, check whether the third attempt should be split (finish-only)
  rather than retried whole — the retry was succeeding only when the tool payloads shrank.

## 7. Ledger rows per event

One append-only row per event: dispatch (packet/log/receipt paths, base SHA, guard file), worker
report (commit, gate counts, disclosures), verify (what YOU re-ran and the counts), gate close.
Row-prefix immutability (snapshot + append) holds across the whole delivery.
