# Task dispatch guards and wave bases (per-task CLI-agent delivery)

Field-verified 2026-09-28 on a 28-task delivery where each task = one NEW session = one
worktree, dispatched one at a time into a 3-stream cap (Manager + 2 workers).
Complements the full-sprint loop in `references/isolated-worktree-full-sprint.md` — this file
covers the *per-task* mechanics: which base to branch from, what to freeze before dispatch,
and what to verify after exit.

## 1. Base selection: branch from the DEPENDENCY'S OUTPUT COMMIT

A wave base is only correct while the dependency is not yet done. Once task A lands its
commit, any task that depends on A must branch from **A's commit** — otherwise the dependency
is absent from the tree and the worker re-invents or stubs the interface.

```
git worktree add -b codex/mf-end-12-<token> "C:/.../mf-delivery-<date>/MF-END-12" 8fa87b8
#                                                                    ^^^^^^^ = MF-END-11's commit
```

Record the chosen base SHA in the launch packet AND the ledger row
(`worktree: ... (base <sha> = <task> output so the dependency is physically present)`).
Tasks whose dependency is the *wave root* share the wave base (`3602eb2` in the observed run:
MF-END-11, MF-END-18, MF-END-02 all branched from MF-END-01's commit).

Also note which dependency the base does **not** include: a sibling task's output is not
required by the DAG, so do not drag it in — keep the tree's diff surface minimal.

## 2. Freeze a before-guard OUTSIDE the worktree

Write `manager/guards/<TaskID>_before.json` (never inside the task tree) containing:

* `head` (full sha), `branch`, `porcelain` count;
* for **every** write-set path: `{exists, bytes, sha256}` — and classify:
  * `exists: false` → whole-file generation allowed inside the allowlist;
  * `exists: true` → the worker MUST patch with a preimage (bounded), never overwrite the
    file wholesale. State this in the launch packet per file (the observed run pinned
    `models.py` 163,231 B sha `55005dd6…`, `object_extraction.py` 135,297 B sha `78b1fd74…`);
* baseline test counts at that base (`pytest <focused> -q` + the broad wave suite) so the
  post-exit re-run has a reference.

Do this BEFORE writing the packet — the guard result changes the packet's wording
(e.g. "scene_detection.py + source_locked_timeline.py ALREADY EXIST → patch preimage").

## 3. Resolve-and-pin contract placeholders BEFORE dispatch

A task packet may contain placeholders like `<live_head_child>` (one migration filename
resolved from the current sole head). The worker must not guess. Resolve it yourself and pin
the literal in the launch packet:

```python
# FALLBACK ONLY — prefer `python -m alembic heads` in the worktree (authoritative).
# This regex scan missed a head form in the field and pinned a STALE revision (see below).
revs, down = {}, set()
for f in os.listdir('migrations/versions'):
    t = open(os.path.join(d, f), encoding='utf-8').read()
    m = re.search(r"revision\s*[:=]\s*['\"]([^'\"]+)", t)
    dn = re.search(r"down_revision\s*[:=]\s*['\"]([^'\"]+)", t)
    if m: revs[m.group(1)] = f
    if dn: down.add(dn.group(1))
heads = [r for r in revs if r not in down]          # must be exactly 1
```

**Use `python -m alembic heads` as the authority; the regex scan above produced a STALE head.**
Observed: the regex scan over 21 migrations reported sole head `f7a8b9c0d1e2`, but the worker's
`alembic heads` measurement in the SAME tree showed the real sole head `d4e5f6a7b8c9`. The worker
chained the new migration (`f8b9c0d1e2f3`) to the MEASURED head and disclosed the stale pin in its
evidence — that is correct behaviour, not a defect: a pinned placeholder is a best-effort input,
and the worker must MEASURE and DISCLOSE rather than obey a stale literal. The guard was switched
to `python -m alembic heads` for all later tasks (verified: sole head `f8b9c0d1e2f3`). Two heads
after the task = a broken chain, so the pin is load-bearing, not cosmetic.

## 4. Launch packet = operational envelope only

The task packet (acceptance / micro-jobs / exclusive write-set) stays the authority and is
referenced by path — never re-summarised. The launch packet adds only:

1. `RULES_LOADED` requirement (read the full rules file in THIS turn) + the exact packet path;
2. model/provider pin + fallback OFF + `--max-turns`/budget;
3. worktree path + base SHA + evidence root (`RUN/tasks/<TaskID>/**`, OUTSIDE the worktree);
4. the before-guard facts from §2 and the pinned values from §3;
5. gate order (micro → acceptance/negatives → focused/static → ONE broad wave gate), the
   `commands.jsonl` field list (UTC start/end/duration/exit/source HEAD), PASS/FAIL/BLOCKED/
   NOT_RUN per micro-job, byte before/after per file;
6. retry rule: on an API/connection error stop clean and print one log line; Manager waits
   ≥5 min then resumes the SAME session/model/scope;
7. payload hygiene: print ≤200-char confirmations, write files via scripts (a giant tool
   payload can be rejected as a provider 422 and kill the run at the last step).

## 5. Post-exit verification (Manager, independent)

```bash
git show --stat --format='%h' <commit>      # scope = exactly the allowlisted paths
git branch -r --contains HEAD | wc -l       # 0 = not pushed
git status --porcelain                      # clean
python -m pytest tests/product_delivery/<task_test>.py -q -p no:cacheprovider
python -m pytest tests/product_delivery -q -p no:cacheprovider   # broad wave suite
```

Observed counts across five tasks: 49p/1s, 78p, 28p, 29p, (broad) 127p/1s — always re-run,
never cite the worker's numbers. `git -C` on an MSYS path can spuriously fail while the tree
exists (see SKILL.md pitfall) — `cd` first, then plain git.

**Correction commits on the same branch are legitimate** if they touch only allowlisted
paths: the observed run had `72e3c15` (main) + `bc87fa3` ("the refusal now EXISTS, not just in
the docstring"). Verify BOTH commits' stats; do not flag a follow-up as scope creep.

**Session-id resolution at launch:** the launcher receipt has no id until exit. Query
`state.db` (read-only) for sessions started after T0 and match the **first user message**
against the packet title — that maps session ↔ task unambiguously. `end_reason` stays null
for `chat --resume` runs, so never use it for liveness; use launcher-process presence +
message-count deltas.

**Gate-freshness tracker quirk:** a worker's own verification tracker may count only DIRECT
pytest invocations, so its suite run through a harness (`run_cmd.py`) looks "stale" while the
bytes are identical. Re-run the suite directly to refresh evidence, and note the reason in
the ledger instead of treating it as a red flag.

## 6. RUN layout used (reusable)

```
RUN/manager/{packets,logs,receipts,guards,tools}/   # Manager-owned; guards land here
RUN/tasks/<TaskID>/{REPORT.md,commands.jsonl,results.json,raw/...}   # worker evidence
RUN/bench|demo/...                                  # read-only verifiers' own write-sets
RUN/proof/...                                       # proof lane (writer-owned)
```

One writer per tree; read-only verifiers never share a write-set with a writer, and never run
while a writer is live on the same root (see `independent-evidence-verification`
`references/live-writer-and-payload-flaps.md`).

## 7. Multi-dependency tasks: TRANSPORT the other deps with `git merge --no-ff`

A task whose DAG parents are several completed tasks has its dependency commits on different
branches, so no single SHA contains all of them. Do not cherry-pick and do not delay the task:
base the new worktree on ONE dependency commit, then merge each remaining dependency commit with
`git merge --no-ff` and record the transports in the guard JSON.

```bash
git worktree add -b codex/mf-end-15-<token> "C:/.../MF-END-15" 2d7a328          # dep A (MF-END-05)
cd "C:/.../MF-END-15"
git merge --no-ff 88ef530 -m "transport MF-END-14 (shot_anchor_v1) into MF-END-15 base"
git merge --no-ff bc87fa3 -m "transport MF-END-18 (comfy adapter) into MF-END-15 base"
git rev-parse HEAD && git status --porcelain    # new merge tip + porcelain 0
```

Observed transports (all conflict-free): MF-END-14 = `4500af7` + merge `1ce1a4b` (08);
MF-END-15 = `2d7a328` + merge `88ef530` (14) + merge `bc87fa3` (18); MF-END-19 = `9b10d1e` (15) +
merge `a2d7cc8` (16). Disjoint write-sets make the merges clean — check the DAG's write-sets for
overlap BEFORE merging, and if two deps touched the same file, resolve the conflict yourself and
record it rather than dispatching on an unresolved tree. The guard JSON gains
`"transport": "<sha> (<task>) + merge <sha> (<task>) ..."` so the base is auditable later.
Verify BEFORE dispatch that each merged dependency's test file exists in the tree
(e.g. `ls tests/product_delivery/test_mf_end_14.py`) — presence, not the merge message, is proof.

## 8. Protected-test changes: pre-register BEFORE patching

A worker may need to touch a file outside its write-set because another task's test pins the old
head/value it changed. The mechanism that made this legitimate in the observed run:

1. Worker writes the change declaration FIRST —
   `raw/writeset_guard_protected_test_change.json` naming the file, the exact impacted assertion
   and the writer attribution — BEFORE the patch lands.
2. Worker then patches, re-runs the guarded test, and reports both in the write-set table with a
   `(**protected — có disclosure**)` marker and byte before/after.
3. Manager accepts only if (a) the declaration predates the patch, (b) the guarded test passes
   after (`test_mf_end_02.py` → 13 passed), and (c) the worker also discloses pre-existing
   failures honestly — the observed run re-measured its 5 protected-suite failures ON THE BASE and
   showed they were red before its change. Re-measure that claim yourself if it is load-bearing.

A protected file changed WITHOUT the pre-registration is scope creep even when the suite is green.

## 9. Long-running lane monitors: editing the script does NOT retarget the running process

Lane monitors (a Python script with a `LANES = {"<Task>": "<session-id>", ...}` dict, sleeping
between ticks) load that dict at import. Editing the file to point at new lanes leaves the RUNNING
instance reporting the OLD sessions — ticks show terminal lanes as `STALL_AUDIT>8min` (a false
positive: a finished session's message count stops advancing by definition).

Rule: after changing `LANES`, launch a FRESH monitor instance with a NEW log filename
(`monitor_phaseb_e.py` → `sed 's/_e.log/_f.log/'` → `monitor_phaseb_f.py`) and let the old one
finish its ticks; never interpret a stale instance's stall flags as evidence about the new lanes.
Also prefer one monitor per lane-set generation over patching in place — the pid you cite in the
heartbeat must run the script version you think it does.
