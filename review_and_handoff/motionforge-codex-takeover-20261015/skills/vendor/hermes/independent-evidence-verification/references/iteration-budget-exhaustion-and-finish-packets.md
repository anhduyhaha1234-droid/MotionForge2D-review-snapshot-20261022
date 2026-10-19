# Iteration-budget exhaustion, finish-packets & wave transport chains

Session evidence: MF-END Phase B (MotionForge2D delivery, 28-task DAG, 2 worker lanes).
All patterns below were executed and verified on disk, not theorised.

See also: `motionforge-2d-project/references/phaseb-delivery-lane-conventions.md` —
the project-side packet boilerplate for the same run (MUST-embed UI helper-text
convention for `frontend/**` packets, guard envelope, per-task Manager verify loop,
monitor succession). That SKILL.md is at its 100k cap, so this cross-link is the
discoverable pointer until the curator splits it.

## 1. Worker hits the 160/160 iteration budget with the work DONE but UNCOMMITTED

Symptom: launcher exits `exit=0`, but the log ends with
`⚠ Iteration budget reached (160/160) — response may be incomplete`,
and `git log` in the task worktree still shows only the transport/parent commit.

**Diagnosis order (never trust the log tail alone):**

1. `git status --porcelain` in the task worktree — list Modified/Untracked.
2. Run the task's own test file yourself (Manager): `python -m pytest tests/.../test_<task>.py -q`.
   In one measured case this returned **31 passed** — the work was finished; only the
   commit/report step was lost.
3. `ls` the evidence dir — see which artifacts landed.

**Recovery = resume the SAME session with a ≤40-call finishing packet.**
Do NOT relaunch a full task (it re-reads everything and re-hits the budget).
Finishing packet contents (verbatim 4 steps, this recovered in 5m46s):

1. Re-run exactly 2 test commands (task file + `public_chain`) and print rc.
2. Close missing evidence only: REPORT.md if thin, `raw/final_gate.json`, append this
   round's rows to `commands.jsonl` (UTC, exit, duration) — no new large artifacts.
3. `git commit` EXACTLY the measured allowlist paths (list them in the packet with
   byte sizes from your own `git status` measurement). No push, no amend, no extra adds.
4. Terminal line: `TASK_SUBMITTED · QUALITY_ACCEPTED=0 · commit <sha> · không push`.

The packet must include the Manager's measured disk state (porcelain list + test result)
so the resumed agent spends zero calls rediscovering it.

## 1a. Occurrence log — 3 hits; TRIAGE BY WHERE THE CAP LANDED

The cap kills the turn, not the work — the disk decides what (if anything) to recover:

| # | Wall before cap | Cap landed | Disk state at detection | Action |
|---|---|---|---|---|
| 1 | ~36 min | before commit | 4 M + 2 ??; test **31 passed** | finish packet, 5m46s |
| 2 | 55m42s | before commit | 4 M + 1 ??; test **14 passed**; REPORT missing | finish packet, 3m28s |
| 3 | 35m22s | AFTER commit + evidence | porcelain 0; REPORT.md present; test **9 passed** | verify normally — nothing to recover |
| 4 | 37m58s (delta lane) | AFTER commit + evidence | porcelain 0; REPORT.md present; test **12 passed** | verify normally — nothing to recover |
| 5 | 27m57s (delta lane, F5) | AFTER commit + evidence | porcelain 0; REPORT.md present; test **12 passed**; commit `63c2600` on disk | verify normally — nothing to recover |

- **Pre-commit cap** (HEAD still = transport/base commit): the finish packet is
  LOAD-BEARING — resume SAME session, ≤40 calls, listed above.
- **Post-commit cap** (banner fires in the final summary turn): treat exactly like a
  normal exit — verify the commit scope + re-run tests as usual.
- The §2 advisory ("commit the allowlist first at ~120 calls") was present in hits 2
  AND 3 — it held at 3 but NOT at 2. Keep it (it is cheap), but never rely on it: on
  every `exit=0` check the log tail for the budget banner and measure the disk before
  deciding anything.

Reusable packet skeleton: `templates/finish-packet.md` (fill the `<...>` from your own
porcelain/test/evidence measurement before dispatch).

## 2. Prevention: budget advisory in every large packet

For task packets above ~4 write-set paths or integration scope, add:

> Budget ~80 tool calls; if you reach ~120 and are not done, **commit the allowlist +
> write REPORT first**, then continue. Never end a round with uncommitted work.

This is now standard in this delivery's launch packets.

## 3. Migration-head guards: regex scanning is stale-prone — use alembic itself

Manager guard initially pinned `down_revision=f7a8b9c0d1e2` by regexing migration files;
the worker MEASURED the real sole head (`d4e5f6a7b8c9`) with alembic and disclosed the
stale pin. Fix now standard in guards:

```python
r = subprocess.run(['python.exe','-m','alembic','heads'], cwd=worktree, capture_output=True, text=True)
g['alembic_heads'] = (r.stdout or r.stderr).strip()[:160]
```

Verified working on subsequent tasks (guard showed the sole head `f8b9c0d1e2f3`).
Rule: if a pin can be MEASURED by a tool, measure it; regexes over source text are a
fallback, and a worker correcting a Manager pin is normal — record it as a
`manager_guard_correction` ledger row, not a defect.

## 4. Wave transport chains (multi-dependency tasks)

Task base = previous wave commit + one `git merge --no-ff <dep_commit>` per dependency
not already in that chain. Pattern per dispatch:

```
git worktree add -b codex/<task>-0928 <path> <prev_task_commit>
cd <path> && git merge --no-ff <dep_commit_A> -m "transport <TASK-A> into <TASK> base"
# repeat per dep; then require porcelain == 0 BEFORE guard/dispatch
```

Record in the ledger: `base: <sha> = <prev> (task) + merge <sha> (task) + merge ...`.
The porcelain check after merge is mandatory evidence.

### 4a. Transport CONFLICTS do happen (first one: ~12 transports in) — recipe

Observed at MF-END-25: `git merge --no-ff 4d60a2f` failed with exactly ONE conflicted
file, `app/workflow/job_handlers.py` — both chains had ADDED a handler registration
in the same block (task-15 `register_shot_anchor_handler(worker)` on HEAD vs task-09
`register_reference_asset_handler(worker)` incoming). `git status` showed `UU` for that
one file and 20 other staged paths; the worktree was in a half-merged state.

Resolution recipe (mechanical additions only):

1. `git diff --name-only --diff-filter=U` — enumerate conflicts; stop and re-plan if
   more than a trivially small set or the hunks encode a LOGIC choice.
2. Resolve a both-lines-added hunk by **keeping BOTH sides** (they are complementary,
   not alternatives) — strip the markers programmatically, assert no `<<<<<<<` remains.
3. `git add <resolved files>` + `git commit --no-edit` (keeps the transport message).
4. Re-check `git status --porcelain` == 0; update the guard JSON's `head` to the MERGE
   commit sha (the guard written before the merge now points at the wrong base).
5. Ledger: a `transport_with_mechanical_conflict` row stating file, sides, and the
   "kept BOTH" rule — a conflicted transport must never look conflict-free in the log.

If the conflict encodes a real behavioural choice (not purely additive), do NOT resolve
by fiat: stop, route it as a delta question, and keep the dependents queued.

### 4b. FINAL integration of a finished wave: merge the minimal TIP SET, not every task

When the DAG finishes, you do NOT need one merge per task. Each task tip already contains its
own dependencies (chains + transports), so a small set of tip branches covers the whole union.
Measured on the 28-task MotionForge wave: the 27 finished tasks collapsed to **6 tip merges** —
`fda3df1` (01-04), `3844ac8` (05-07), `fedd33b` (08), `29bc006` (08,11-14,16,17), `bc87fa3`
(18), `b1965ad` (09,10,19-27) — onto the frozen base `2c405f3e`; all six `--no-ff`,
**zero conflicts, porcelain 0**. (The one earlier mechanical conflict was already resolved
inside `b1965ad`'s history — exactly why tip-minting beats per-task merges: you inherit their
resolutions instead of replaying them.)

Recipe:
1. List every task tip sha; mark which earlier tips each already contains (inspect chains and
   transport-merge parents). Keep the minimal set whose union covers all tasks; prefer the
   newest tips.
2. `git worktree add -b <integration-branch> <path> <frozen-base>`, then merge the tips in
   chronological order with `--no-ff` and a uniform message form.
3. After EACH merge: `git status --porcelain` must be 0 (record it per merge).
4. Then ONE broad wave on the merged tree (full test roots + an import smoke of the new
   top-level modules), not full suites per merge — that keeps integration minutes, not hours.

### 4c. Serial chains: idle slots are deliberate gating, not lost capacity

Late in a DAG the remaining tasks can ALL transit through one running task (here: 24,25,26,27,28
each required the then-running task-23 commit). With a 2-worker cap that leaves slots idle by
design. Do NOT force-dispatch unrelated work or bypass a dependency to fill a slot. Record the
reason in the ledger row (\"slot idle: all remaining tasks transit through <running task>\") so
the gap reads as gating, not as a stall when the audit trail is reviewed later.

### 4d. The union broad wave WILL catch tree-pinned GENERATED artifacts — budget one integration-only fix

Measured on the same 28-task wave, first full verify of frozen candidate #4:
`tests/product_delivery/test_mf_end_28.py::test_28_2_builder_is_deterministic` = **1 failed /
755 passed on the UNION tree**, while the very same test was 11/11 green in task-28's own
worktree minutes earlier.

Root-cause class (reusable): a task that COMMITS a generated artifact pinning hashes of the
tree (here `packaging/demo/inventory.json` carrying `app_tree_sha256`) built that artifact on
a base that does NOT contain every earlier task. Task bases are the union of a task's
DECLARED deps only — they never guarantee in-between tasks. Concrete chain: task-27's history
never absorbed task-17's tip (`29bc006`), so task-28's base (`b1965ad`) lacked task-17's
files; the committed hash (`466e1b4a…`) was stale vs the union tree's fresh hash (`d9e5ffb6…`).

Diagnosis (2 checks, both cheap):
1. Run the failing test alone; read WHICH side of the compare differs — fresh-vs-committed
   hash of the same generated file (the assertion message usually names the builder to re-run).
2. Prove the file delta with git, not with prose:
   `git diff --stat <task-tip> <union-tip> -- <subtree>/` → files present only in the union
   tree (here: task-17's `controlled_shot_v1.json` + `.manifest.json` + its test file).

Fix (integration-side; NEVER hand-edit a generated artifact):
- Re-run the repo's OWN builder on the union tree (e.g.
  `python packaging/demo/build_demo_package_inventory.py`), read its guardrail output
  (`secrets=0 absolute_paths=0`), commit it as
  `integration: regenerate <artifact> on the union tree (...)`, re-run the test → green.
- Ledger row names BOTH the defect (which task's base lacked which earlier task) and the fix,
  so the frozen-candidate sha advances with its reason attached.

Rules:
- Expect ≥1 integration-only failure in any wave that commits generated/manifest artifacts;
  the union broad wave exists to surface it BEFORE demo/review, not after.
- A green task-worktree test is NOT evidence the artifact survives the union — always
  re-verify on the merged tree AFTER the last tip merge, then freeze.

### 4d-bis. Second occurrence — regen on EVERY candidate advance, bundle it into the advancing commit

Measured again at candidate #5 (#4 + DELTA-F1/F2 merged): the SAME
`test_28_2_builder_is_deterministic` failed a second time, because the deltas themselves changed
`app/**` (new column, adapter edits) — the committed generated artifact is invalidated by ANY change
to the subtree it hashes, not only by the first union merge. Rules measured:
- Whenever a candidate advance changes the hashed subtree (task merge, delta merge, integration fix),
  re-run the repo builder and commit the regen IN THE SAME integration commit that advances the
  candidate — before dispatching the verify wave, not after it fails.
- Cheap pre-flight: `git diff --stat <old_candidate> <new_candidate> -- <hashed_subtree>` — non-empty
  ⇒ regen required.

### 4d-ter. Third occurrence + the read-only-demo deferral rule (count FAILED rows in §4e arithmetic)

Measured again when DELTA-F4 merged (candidate #6 verify: `859 passed, 1 failed` — the 1 failure was the
SAME inventory test, because F4 changed `app/**` and the `db238390` advance carried no regen). Arithmetic
check that reconciles it: **859 + 1 = 860 collected** (= #5's 856 + F4's 4). When validating §4e, add the
FAILED rows to the collected total — a "lower than expected" passed-count is often just the known stale
artifact, not a collection defect.

The wrapper that justified DEFERRING rather than bundling: a read-only demo lane was running on that tree
(§7 envelope). Regenerating mid-run writes to the tree and pollutes the demo's own final
`porcelain == 0` check. Rules measured:
- No reader active → regen INSIDE the advancing commit (§4d-bis).
- Read-only lane active on the tree → DEFER, write a `pending regen` ledger row naming the reason, and fold
  the regen into the NEXT advancing commit — after the LAST `app/**` change of the batch. Do it ONCE at the
  end, not once per round: a delta loop (F5, F6, …) keeps invalidating it until the edits stop.
- Never let the deferred regen outlive the batch: the candidate the review packet cites must carry a fresh
  artifact with its test green.

### 4e. Wave-count arithmetic is a free correctness check

Full-wave totals must equal the previous candidate's total + the new rows. Measured: #4 = 838,
the delta pair adds 18 rows (6 F1 + 12 F2), so the #5 wave read **856 passed / 3 skipped / 0 failed
(9m49s)**. A total BELOW expectation means part of the tree was not collected (rerun before
concluding); ABOVE usually means a duplicated test root in the invocation. Put both numbers
(previous + delta) in the ledger row so a reviewer can re-derive the expectation.

## 5. Protected-test changes: pre-registration is what makes it legal

A worker needing to touch a protected test must write
`writeset_guard_protected_test_change.json` (impacted assertions + writer attribution)
**BEFORE** patching. Observed working instance (MF-END-05 patching `test_mf_end_02.py`):
guard VERIFIED, the protected test still passed 13/13 after, and the commit was accepted
with the extra path disclosed. If the file is missing or written after the fact, treat the
commit as out-of-write-set.

### 5a. A later migration MOVES the head → pre-registered re-pin of an older task's protected test

Measured at candidate #5: DELTA-F1 appended migration `b3c4d5e6f7a8` ABOVE task-05's revision, so
`test_mf_end_05` failed twice on pins that had been green since task-05:
(a) micro repro pinned `get_heads() == ["e5f6a7b8c9d0"]` (the old sole head);
(b) the refused-downgrade test pinned `version_after == version_before == [("e5f6a7b8c9d0",)]`.

Fix recipe (Manager-side — the test belongs to another lane, so pre-register, never silently edit):
1. Write the pre-registration record FIRST: `manager/.../protected_test_change_<task>.json` with
   impacted assertions + line refs, writer attribution (which delta's migration moved the head), and
   the invariant preserved (only the revision pin moved; fail-closed behaviour untouched).
2. Re-pin with the MEASURED chain, not just the number: `heads == [new_head]`; keep the parent/child
   asserts; ADD the child-of-old-head assertion (`children_of_05 == ["b3c4d5e6f7a8"]`) so the chain
   link is still proven.
3. For a refused-downgrade test, split the pin into TWO facts: `version_before == [new_head]` (state at
   upgrade) and `version_after == [old_revision]` — the refused downgrade first rolls back the NEW
   additive step, then stops at the task's revision when THAT one refuses. The zero-mutation asserts on
   the task's own DDL + rows stay unchanged (measured still true).
4. Commit the re-pin as an integration commit (bundled with the artifact regen of §4d-bis), then
   re-run BOTH the task's own file and the full wave — measured: task file 20 passed, wave 856/3/0.

Diagnosis is free: the failure output prints BOTH compared values
(`[('e5f6a7b8c9d0',)] == [('b3c4d5e6f7a8',)]`), which names the new head and the stop-at revision —
no scratch-DB bisect needed.

## 6. Honest-disclosure patterns to EXPECT and preserve (do not "fix" them)

- `accepted_seconds = 0` ⇒ cost per accepted second stays **UNDEFINED** (no fabricated denominator).
- `RAM NOT MEASURED` stays a numbered failure row, never 0.
- Challenger activation `SKIPPED_NOT_NEEDED` must carry `counts_as_test_pass=false`.
- Failures reproduced on the BASE (pre-existing) are disclosed, not attributed to the task.

## 7. Phase C: demo/review lane runs on the FROZEN candidate under a stricter envelope

Dispatched 2026-09-28 after the union wave (838 passed / 3 skipped) and the freeze; **ran to completion
(48m30s)** — measured outcome in §7a. The envelope below held exactly as written, and every rule in it
is grounded in an already-verified pattern above or in the proof runs.

- **Code tree is READ-ONLY.** Point the demo worker at the frozen-candidate worktree and forbid
  product-code edits: anything it finds becomes an `OPEN_FINDING` + evidence, never a fix. A demo-lane
  commit on the candidate would invalidate the sha the review packet advertises.
- **Hand over instead of rediscovering:** the packaging/launcher produced by the packaging task
  (`scripts/*launcher*`, `packaging/**`), the proof's measured engine parameters (graph steps/cfg/
  shift, geometry, cache default, seed), and where the demo inputs already live. Same principle as
  finish packets: the worker spends zero calls rediscovering facts you already measured.
- **Real-API discipline:** require at least one real HTTP 2xx per journey milestone (create project,
  submit render, poll status, export) — in-process shortcuts do not count as "the app runs".
- **Fix the evidence set up front, in the packet:** REPORT + `commands.jsonl` + per-job receipts
  (server epoch, job id, prompt id) + `ffprobe` of the demo media + sha256 manifest + one preview
  sheet + `POST_STOP_VERIFIED` for the engine server.
- **GPU policy unchanged:** isolated server, ONE job at a time, clean shutdown, read-only proof of the
  engine tree. Budget advisory ~110 calls with the commit-before-130 rule (§1/§2) — the phase is long
  by nature, so the cap is expected, not exceptional.

### 7a. Measured outcome — the demo lane WORKS (app runs, GPU renders, video exists)

- App up FROM the frozen candidate tree: uvicorn ready **4.37 s**; `GET /health 200`; isolated runtime root.
- HTTP milestones all real 2xx: project **201** · video **201** · structural lock **201/200** · cast pins **200** · approval **201/200** · full-apply submit **202**.
- **3/3 shots rendered on the real GPU** (~130–138 s each, one prompt id per shot) on an isolated ComfyUI 0.37 (own port, `--reserve-vram 1.0`, 1 job at a time); attempt dedupe verified live (re-call → `MF_COMFY_ATTEMPT_ALREADY_TERMINAL`, zero re-POST).
- **12 s demo video produced** from the 3 server-side clips (concat `-c copy` + source-audio remux): 640×368 h264 30/1, 360 f, 12.001 s, PTS monotonic, full decode rc=0, sha256 + contact sheet in evidence.
- Confirm-by-disk was essential twice in this lane: the app "running" claim is only real if /health answered, and the video claim only if ffprobe + full-decode + sha are on disk.

### 7b. Seam classes a real-run demo WILL find (green tests cannot) — expect and route as deltas

**Class A — persistence projection silently drops a planner field.** Planner emits `member_layer_ids` on
group chunks; the persistence model has no column; the worker fail-closes on read-back → EVERY run of
that backend dies at chunk 0 BEFORE any GPU work (typed `S10_FULL_APPLY_FAILED … carries no member_layer_ids`),
and all downstream steps answer typed refusals (QC 422 `EVIDENCE_STALE`, export 409 `FULL_APPLY_MISSING`).
Signature: terminal run `failed`, zero GPU time, typed fail-closed worker error naming the field.
Lesson: trace every planner-computed field planner → model column → read-back before trusting a green
lane; unit tests passing in-memory objects never exercise the DB projection.

**Class B — declared media kind vs the REAL server's publish bucket.** App pinned `video → bucket
"videos"`; ComfyUI 0.37 `SaveVideo` actually publishes under key `images` (+`animated=[true]`), so the
adapter rejected a render whose prompt status was **success** (`ARTIFACT_MISSING actual_kind=images vs
expected_kind=videos`). Lesson: engine-kind maps must be pinned from the LIVE server's history payload —
a fake-transport test that fabricates the expected bucket stays green forever while the real seam is dead.

**Class C — filename length, not just root depth.** Under a deep evidence root the engine's reservation
filename reached **276 chars** → `FileNotFoundError` (WinError-206 family). Workaround: run the engine
under a SHORT managed root (`%TEMP%/<short-name>`) and copy receipts back to the evidence root. A
long-path-capable volume does not save you — the FILENAME component itself can exceed MAX_PATH.

**Class C-bis — the OTHER Windows ceiling: escaped-argv length (measured by task-23's probe).**
Not the raw string length — the ESCAPED length of the argv the runner builds. Measured: escaped
25,001 B spawns; escaped 32,501 B → `WinError 206` (≈2 KB escaping overhead). Consequences for
payload-bearing pipelines: (a) transport large payloads via FILES (a `payload_path`-style argument)
instead of argv; (b) a size-policy on the transport should CASCADE/drop oversized entries rather
than raise mid-pipeline, and the consuming gate must re-verify from rows (task-23 shipped exactly
that and re-verified from persisted rows). Both ceilings (filename length, escaped argv) show up
only under deep evidence roots with long ids — test the demo path early under a SHORT root.

**Class D — producer/consumer KEY-SPACE mismatch across sibling code paths.** The route built the job
manifest's `replacement_assets` map keyed by **role_id** (`assets[role_id] = …`, `s10_full_apply.py:165`),
while the group-engine worker looked entries up by **`layer_id`** (the occurrence-segment id carried in
`member_layer_ids`, `s10_full_apply_jobs.py:1040`) — every run died at chunk 0, **0 GPU**, typed
`replacement_assets missing entry for layer '<segment-uuid>'` (job `error_json`), while the persisted
manifest's keys were all `role-*`. The LEGACY per-layer path already had the translation adapter
(`asset_key = mapping_entry.get("role_id") or layer_id`) — the newer group path was added WITHOUT it.
Lesson: when two code paths consume the same artifact, diff the OLD path for a translation/adaptation
step the NEW path skipped; key-space identity (role vs layer vs segment id) is a model invariant, not a
seed artifact. Verify by joining the DB: segment `<id>` → `role_id='role-…'`, then compare with the
manifest keys actually persisted on the failing run.

**Class E — a DELIBERATE geometry transform (pad/crop) must be declared to EVERY downstream consumer.**
Measured at R3 (candidate #6, run `a94d76d9`): the render profile legitimately pads the 640×360 source to
640×368 (4+4 rows; Wan dims need /16), so chunks and the app-stitched publication are 640×368 — but the QC
evidence path compares the render frame against the SOURCE frame and requires identical geometry
(`QC_EVIDENCE_MALFORMED: source frame (360,640) and render frame (368,640) have different geometry`;
guards `qc_evidence/observe.py:96`, `measure.py:173`). The QC submit schema has no geometry override, so
QC can never pass → readiness stays `not_run` → export answers 409. Signature: a typed 422 that NAMES BOTH
shapes on the first submit after an otherwise successful publication, with a 409 export trailing as a
consequence (not a cause). Fix options, in preference order: (a) conform back to source geometry before
publication (strip the pad DECLARED by the profile — never hardcode the strip), (b) teach the consumer the
profile's pad (crop the declared region before comparing), (c) pin the plan's output geometry to the
video_item and let the graph pad internally. Lesson: pad/scale stages are invisible to every consumer that
compares against the source; before trusting a render profile, trace its declared
`native_output_dims`/`pad` into the FIRST step that compares render vs source.

Anti-fabrication pattern from the same run (disclose, don't paper over): no public upload route existed
for the durable source item, so the import step was seeded harness-style and DISCLOSED in the report,
with every other milestone driven by real HTTP.

### 7c. Packet hygiene: never fabricate a 40-hex sha — write only MEASURED revs

The demo packet quoted the frozen candidate as `951543664e3b…` — a 40-hex hand-extended from the 10-char
short form. The worker ran `git rev-parse --verify <sha>^{commit}` (→ fatal: no such object) and disclosed
the drift, proceeding on the real HEAD `951543664ed10e0d…`.
Rule: in packets and ledgers, cite either the short sha exactly as git printed it, or paste an actual
`rev-parse` output captured in the same turn you write it. If the full sha matters, measure it — never
extrapolate.

### 7d. Delta fixes from demo findings: branch from the FROZEN candidate, disarm vacuity with captured evidence

When the demo reports seam classes (§7b), the findings are TWO-TASK seams, not one-task bugs — route them as
DELTA tasks (dispatched in parallel when their write-sets are disjoint), never as edits inside the demo lane.

Recipe (measured 2026-09-28, DELTA-F1 persistence-members vs DELTA-F2 media-kind bucket):

1. **Base = the frozen candidate sha itself**, not the originating task's base:
   `git worktree add -b codex/<delta>-0928 <path> <FROZEN_SHA>` — the delta must fix the exact tree the
   demo/review will cite.
2. **Bounded write-set naming the measured chain**, file:line refs lifted verbatim from the finding
   (e.g. planner `:637` → persistence `:555` → worker read-back `:1023`). The packet embeds the finding's
   raw evidence paths (captured server history JSON, the failing run/job ids) so the fixer never
   re-derives them.
3. **Non-vacuity is part of the packet contract**: the delta's test must be RED on base and GREEN after.
   For a server-shape seam, the fixture is the CAPTURED real payload (the demo's history JSON), plus a
   negative discriminator (e.g. `images` WITHOUT `animated` must not read as video) — do not invent a
   synthetic payload that would have been green on base.
4. Terminal rules identical to task lanes (allowlist commit, no push, `QUALITY_ACCEPTED=0`), budget
   advisory as usual; F1/F2 ran in parallel on disjoint write-sets (persistence chain vs adapter file),
   staggered dispatch, one monitor lane.
5. **Candidate-advance bookkeeping**: merging deltas into the integration tree ADVANCES the frozen sha.
   Re-label the candidate (`#4` → `#4b`), keep the pre-delta sha in history, and require the final review
   packet to state WHICH sha each demo run used. Never overwrite the old freeze record — append the new
   one with the reason (which findings it fixes).
6. Nothing in a delta packet may loosen a gate the demo proved closed (fail-closed worker reads stay
   fail-closed; only the persistence projection gains the field).

### 7e. Merging the delta pair onto the candidate — measured (candidate #4 → #5)

Both deltas landing is NOT the end: the pair must merge into the integration tree and the merged
tree re-verified BEFORE the re-run demo is dispatched (the demo must run on what the review cites).

Recipe (measured 2026-09-28, F1+F2):
1. `git merge --no-ff <DELTA-1 tip>` then `git merge --no-ff <DELTA-2 tip>` into the integration
   worktree — a 2-tip merge on the frozen candidate, never a rebuild. Porcelain 0 after each.
2. On the merged tree, run BOTH delta test files together (measured **18 passed** = F1 6 + F2 12).
   Cross-running matters: each lane only proved itself against its own base.
3. `python -m alembic heads` on the MERGED tree — the delta migration must be the sole head
   (measured `b3c4d5e6f7a8`). A per-lane test cannot prove the chain; only the merged tree can.
4. Advance the candidate label with the measured sha — #4 `951543664ed10e0d…` → #5
   `82c84a890349fd2d2251b753d00c5f03f798063d` — and the re-run demo packet must say
   "verify bằng `git rev-parse HEAD`; CHỈ ghi SHA đo được" (§7c) so the worker re-measures
   instead of trusting the quoted sha.
5. A delta lane may land as a MULTI-commit chain: main commit + self-initiated correction commit
   (F1: main `34c1374` + correction `0f2cde6` tightening the read to all-or-nothing — never a
   silently reduced cast — plus a corruption case). Re-verify on the TIP, and let the final review
   packet cite the tip sha, not the first commit.

### 7f. Fixture provenance: a lane's own green test can encode the WRONG contract

Measured at the F4 round (demo R2 on candidate #5): delta-F1's test fabricated the manifest's
`replacement_assets` keyed by the member layer ids themselves (`assets[lid] = …`), so it proved
"members persisted" while staying BLIND to the route's real role-keyed manifest — **6/6 green, the
real run dead at chunk 0**. The fixture had frozen the author's key-space assumption, which was
exactly the thing under test. The seam only surfaced because the demo drove the REAL route.

Rules for every seam-delta's non-vacuity fixture:
- Build the fixture **BY THE REAL PRODUCER** — call the route/service that builds the artifact, or
  replay its captured persisted output — never hand-roll the intermediate artifact's shape.
- When the defect spans a producer→consumer seam, at least one test must drive the REAL producer
  and the REAL consumer in one test (route-built manifest → worker lookup), not two stubbed halves
  that agree with each other.
- The fixture fix may not relax production fail-closed behaviour: a missing role entry must still
  refuse typed. (Same rule as §7d point 3, now with the measured counter-example.)

### 7g. The demo loop is ITERATIVE — budget N rounds, route each finding to the file where the seam lives

Measured arc: R1 surfaced F1+F2 → deltas merged → candidate #5 → R2 verified BOTH fixes live
(run `90319e92`: chunk-0 row now carries real `member_layer_ids_json`; F2's bucket accepted via the
engine path) **and** surfaced F4 one layer deeper in the same call chain. Each round removes one
fault and exposes the next behind it; the worker's raw DB harvest (run/job/chunk tables copied out
at shutdown) is what made the "fix verified live" claim checkable.
- Budget for R1 → deltas → R2 → deltas → R3; do not promise a single demo round.
- Route each finding as its own delta on the file its write-set covers (F4 → the delta-F1 file
  `s10_full_apply_jobs.py`), with the finding's raw evidence paths embedded; advance the freeze
  label and re-run the FULL wave each time (§4e arithmetic).
- A fix "verified live" claim must cite a DB row or server payload captured on disk — not a log line.

### 7h. F4 round measured (same-file delta, fixture shipped with the fix, freeze #6, cross-run arithmetic)

Continued from §7g (measured 2026-09-29):
- **F4 landed as `f0a3866`**: the worker now translates occurrence-layer→role before the manifest
  lookup (mirroring the legacy `_stage_layer_asset` adapter; `s10_full_apply_jobs.py` +24) AND the
  fixture rebuild ships IN THE SAME COMMIT — `test_delta_f1.py` rebuilt to build its manifest FROM the
  real route (222 changed lines) plus a new `test_delta_f4.py` (168 lines). Rule reinforced: when a
  finding is a fixture-provenance defect (§7f), the test rebuild is part of the code fix, never a
  follow-up task. In-lane verify: 10 passed, porcelain 0.
- **Merge → candidate #6 `db238390dd18751080c1aee1f2a718fa9ca04f5c`** (`--no-ff`, porcelain 0).
  Cross-run of ALL delta files on the merged tree: **22 passed** (F1 6 + F2 12 + F4 4) — this
  cross-run total is the row-count basis for the next wave arithmetic (§4e): expect the #6 wave =
  856 (measured on #5) + 4 = **860**; a lower read means part of the tree was not collected.
- R3 re-dispatched on #6 with the §7 envelope plus an EXPLICIT expectation line in the packet
  ("publication → QC 2xx → export 2xx + product video via the app path"); any shortfall must come
  back as typed refusals with evidence — never smoothed over.
- Freeze bookkeeping across delta rounds: keep every earlier freeze record (names each demo run's
  sha + which findings it fixes), append the new one; the review packet must state WHICH sha each
  demo round used (§7d point 5, now exercised across #4→#4b→#5→#6).

### 7i. R3 round measured — three rounds, three deltas (R1→F1/F2, R2→F4, R3→F5)

Measured 2026-09-29 on candidate #6 `db238390…` (run `a94d76d9-8156-4ed2-a717-dd5fb2d733ad`):

- **Every earlier finding verified CLOSED LIVE through the real worker path** (not harness-only):
  F4 — chunks 0/1/2 all `completed/verified`, ZERO `missing entry` errors in DB/job; F1 —
  `member_layer_ids_json` present on chunk rows (4/1/1 members) in the DB harvest; F2 — 3/3 engine
  evidences `validated` with bucket `images` + `proven_animated`, three real prompts at 133–141 s.
- **Publication now produced BY THE APP**: `stitch_shot_chunks.mp4` (= `raw/export/demo_final.mp4`)
  sha256 `6de96ac723db…`, 3,766,511 B, 640×368, 360 f / 12.0 s, PTS monotonic, decode rc=0, contact
  sheet 9 frames. Disclosed gap: NO audio — the mux belongs to the export step, still blocked
  downstream; a "product video exists" claim must state whether audio is in it.
- **NEW F5 = Class E** (§7b): QC 422 `QC_EVIDENCE_MALFORMED` → readiness `not_run` → export 409,
  with the full chain measured (profile `native_output_dims`/`pad` → chunk dims → publication dims →
  source dims → exact consumer guard lines → no schema override).
- DELTA-F5 dispatched on the frozen sha (priority (a) conform-before-publication) with the §7f fixture
  rule restated in the packet: tests build from the REAL publication of run `a94d76d9` — no
  hand-rolled shapes.
- Plan-with pattern: **each demo round closes the previous findings AND exposes exactly one seam
  deeper in the chain** (render → persistence → key-space → geometry). Budget rounds R1…R4 up front,
  keep each delta anchored to the file where the seam lives, and re-advance the freeze label with the
  §4e arithmetic after every merge.

### 7j. F5 round measured — freeze #7 and the deferred-regen fold executed (R4 dispatched)

Measured 2026-09-29, continuing §7i:

- **DELTA-F5 landed `63c2600`** ("publication conforms to the SOURCE geometry via the profile's own pad
  declaration"): fix + fixture rebuild shipped IN ONE COMMIT — `s10_full_apply_jobs.py` +218 and a
  626-line test whose fixtures are **four REAL MP4s captured from run `a94d76d9`** (3 chunk outputs +
  `source_12s.mp4`). This is §7f done right: the fixture is the captured real artifact, never a
  hand-rolled shape. In-lane verify **12 passed**, porcelain 0; cap hit AFTER commit (occurrence log
  row 5) — verify normally, no finish packet.
- **Merge → the DEFERRED regen was folded immediately** (this is §4d-ter executed): `merge --no-ff
  63c2600` → builder re-run on the tree (`secrets=0 absolute_paths=0`) → commit
  `integration: regenerate demo inventory after DELTA-F5` → **candidate #7 =
  `dfdad73457d499a83e36a887ff64cd35c6f5d929`**, porcelain 0. Note the batch discipline: the regen ran
  once, AFTER the last `app/**` change of the F-round, not per merge.
- **Arithmetic trail across the delta batch** (re-derivable from the ledger): #4 838 → +18 (F1/F2) → #5
  856 → +4 (F4) → #6 859 passed/1 failed (the known stale artifact, 860 collected) → regen fix `4313cf4`
  → 856+... → #7 wave launched. Keep every intermediate number — a reviewer re-derives the expectation
  from them („previous + new rows", §4e).
- **R4 packet restated the two hard rules that cost prior rounds**: §7c (write only `git rev-parse`-measured
  SHAs; worker re-measures HEAD) and §7f (fixtures from real artifacts), plus the §7-envelope (read-only
  tree, real HTTP 2xx per milestone, short managed root, 1 GPU job, commit-before-130 advisory).
- Loop-state at this writing: R1→F1/F2 · R2→F4 · R3→F5 · R4 running on #7 — i.e. **four demo rounds,
  four seam deltas**; budget for a fifth round if R4 exposes one more layer, and never advertise a
  completion before the chain's terminal step answers 2xx WITH its product media (audio included).

### 7k. R4 round measured — F5 fully closed live; the round exposed the EVIDENCE-COMPOSER and AUDIO-PROVENANCE layers

Measured 2026-09-29 on candidate #7 `dfdad734…` (run session `20260929_024739_0c8cc6`, 33m52s):

- **F5 verified CLOSED LIVE through the app path**: publication `stitch_shot_chunks.mp4` = **640×360×360f / 12.0 s** carrying `frame_metadata.conform = {applied: true, declaration: "centered (4+4 rows over 640x360)", render_dims: [640,368], source_dims: [640,360]}`; **QC geometry refusals GONE**. `original-audio-attach` → **202 + job completed** (first time — the seed needed an `artifact_owner(video_item, purpose='source')` to match the product model). Annotation producer driven via real routes (6 cast mappings + occlusion 201 + contact 201); 3/3 real renders again. A conform claim is only checkable if the publication's metadata names BOTH dims — require that field, not just the file's dimensions.
- NEW seams this round; routing = ONE delta per seam on the file where it lives, branched from the frozen sha, parallel when write-sets are disjoint:
  - **Class F — budgeted-window starvation in evidence composition (F-R4-1, P1, `app/services/qc_evidence/*`).** `compose.py:1325` does `indices = sorted(wanted)[:MAX_WINDOW_FRAMES]` (24) over the UNION of per-boundary windows (3-scene video → 75 indices); the cap keeps −1..22 so boundary 120's span `[108,131]` has **0 measurable pairs** ⇒ 422 `no_measurable_frame_pair` — while MAD(119→120)=**80.82** proves a real cut on disk (neighbour pairs ~0.2–4). Widening the window (RAM probe) moves the refusal to a SECOND layer in series (`no_distinguishable_cut`, `CUT_DOMINANCE_FACTOR=2.0`). Signature: any ≥2-boundary video refuses on the SECOND boundary with a span named; a single-scene video passes (boundary 0 is special-cased `frame <= 0`). Rules: a global cap over unioned windows starves boundaries left-to-right — budget per window, not per union; and never believe a "no measurable pair" refusal before replaying it against the pixel MAD matrix (here: `top10` cut list from a read-only probe).
  - **Class C-ter — the escaped-argv ceiling strikes the QC composer's OWN payload (F-R4-2, P1).** `identity_drift` composed args = **63,327 B** (frames block 23,403; 6-role pin dossier 10,217) vs the already-measured **32,500/32,700 B** spawn ceiling (Class C-bis) ⇒ typed refusal. Same fix family as task-23's precedent: **file-based payload transport** (or trim the largest block), with the gate re-verifying from persisted rows. Signature: `QC_EVIDENCE_MALFORMED … argument set is 62960 B, but the detector child process can only receive ~32500 B`.
  - **Class G — audio provenance: export probes the WRONG artifact (F-R4-5, P1, forecast-then-fix).** The full-apply publication is written by `write_frames_mp4` (**video-only**); export resolves original audio from the publication artifact (`_source_artifact_path → authority.source_artifact_id`) ⇒ probe `present:false` "no audio stream (a:0)" ⇒ media would be **honestly-but-wrongly silent** even though the source audio was attached (202, completed). Options: (a) remux source audio into the publication during stitch, or (b) export resolves audio from the source artifact / attached `original_audio`. Rules: for any pipeline that attaches media out-of-band, ffprobe WHICH artifact each downstream step probes — correct code can still probe the wrong artifact; and an attach that returns 202 is not proof the export consumes it.
  - **P2 dependency refusals that are DATA-RICHNESS, not code (F-R4-3/4).** `edge_halo` needs a rendered-side mask artifact with a `video_item/purpose='mask'` owner link (producer gap — disclosed, routed separately); `z_order_error` needs TWO DISTINCT per-role mask artefacts with overlap + exclusive areas (the seed used ONE shared mask → refusal). Rule: when a dependency refusal NAMES an artifact shape, check whether the SEED can produce it before routing the finding as a code bug; richness gaps go into the next demo seed and stay disclosed as such — never silently dropped.
- Delta pair dispatched (staggered 45 s, disjoint write-sets): **F6** QC composer (window budget + file-based transport) and **F7** audio provenance (export/stitch resolution). Both inherit the §7f fixture rule (fixtures = captured real artifacts) and the red-on-base / green-after / negative-contract.
- Loop-count law after this round: R1→F1/F2 · R2→F4 · R3→F5 · R4→F-R4-1/F-R4-2/F-R4-5 (+2 P2 seed gaps). Seam layering so far: render-success → persistence projection → key-space → geometry-conform → **evidence-window/transport → audio provenance**. Budget a fifth round; the honest-completion bar stays: the terminal export answers 2xx WITH its product media INCLUDING audio.

### 7l. F6/F7 landed — freeze #8; R5 dispatched with the seed-enrichment item (loop continues)

Measured 2026-09-29, continuing §7k:

- **DELTA-F6 landed `c043845`** ("QC composer — cut-window starvation + measured identity transport"):
  `qc_evidence/compose.py` +556, `measure.py` +18, test +397 — and the fixture is the CAPTURED R4
  publication (`tests/fixtures/delta_f6/r4_publication_640x360_360f.mp4`, 3.84 MB), i.e. §7f executed
  again by a different owner. Manager re-ran the lane test independently: **5 passed**, porcelain 0;
  log tail shows NO budget banner (normal exit — occurrence-log row 3/4/5 flow, no finish packet).
- **DELTA-F7 landed `0738ae1`** ("export media carries the ORIGINAL audio (publication is video-only)"):
  `s12_export/publication.py` +22, `s12_export_jobs.py` +226, test +609, fixtures = three captured R4
  artifacts (`publication.mp4`, `source_12s.mp4`, `audio_receipt.json`). Verify **7 passed**, porcelain 0.
- **Merge both + regen → freeze #8 = `a52fca897906fd61a088016dd802718fdf06d217`**: two `--no-ff`
  merges (F6 then F7), then the builder re-run folded into the SAME advancing batch (§4d-ter: once,
  after the last `app/**` change of the round) → porcelain 0. Cross-run of the two delta files on the
  merged tree = **12 passed (5+7)** — the row basis for the #8 wave arithmetic (§4e): expectation =
  #7's **872** + 12 = **884** (wave launched, not yet read at this writing; reconcile before citing).
- **R5 dispatched on #8** with the §7-envelope + §7c/§7f hard rules plus ONE new explicit item: the
  demo seed itself must be ENRICHED per the P2 data-richness findings (per-role mask artifacts + a
  rendered-side mask carrying the `video_item/purpose='mask'` owner link). Rule this pins down:
  **seed enrichment is legal work INSIDE the read-only demo lane** — it is the harness's own data,
  not product code — but if the producer path still cannot publish the required shape, it returns as
  an OPEN_FINDING with evidence, never faked (same anti-fabrication line as §7b).
- Loop-count law update: R1→F1/F2 · R2→F4 · R3→F5 · R4→F6/F7 (+2 P2 seed gaps) · R5 running.
  Six deltas, five demo rounds, freeze chain #4→#4b→#5→#6→#7→#8. Completion bar unchanged.
- **Tooling pitfall measured this round (Manager side):** a ledger rows-JSON written with a
  `../`-RELATIVE path resolves against the shell's cwd, which shifts between terminal calls — the
  subsequent `append_ledger_delivery.py ../ledger_*.json` then failed `FileNotFoundError` and the row
  was silently absent until rewritten with an ABSOLUTE path. Rule: write ledger row files with
  absolute paths, and treat a missing rows-file as "row not yet recorded", re-write + re-append
  before moving on (the append tool itself is append-only and idempotent per file, so re-appending
  the corrected file is safe).

## 8. Budget landed BEFORE the structured terminal record — RECORD-FIRST (measured 2026-10-12, MF-DEMO-LONG-01 R5)

Variant of §1/§1a for pipelines that use a per-invocation STRUCTURED terminal record:

Symptom: dispatcher receipt `outcome_class=NEEDS_RECONCILIATION`, error
`[WinError 2] ... evidence/terminal/<invocation>.json`; launcher exit=0 and the log's last
prose says `CONTINUE_REQUIRED`. Root cause: the 80/80 iteration budget fired immediately
BEFORE the worker wrote its record — the work was done, the RECORD was missing. The
fail-closed validator behaved exactly as designed: no record = no terminal (prose is never
authority). Lease released clean (children DEAD + queue quiet) — nothing was left running.

Triage (one batch): (1) log tail for `⚠ Iteration budget reached (N/N)`;
(2) `ls evidence/terminal/` — THIS invocation's record absent, earlier invocations' present;
(3) the worker's own final message usually lists exactly what remains — reuse it verbatim as
the continuation packet's work list; (4) scope scan for files newer than the dispatch start
(1484 files in the measured case) — prove the work is really on disk.

Reconcile rules: do NOT backfill the closed invocation's record (immutable history; the NR
receipt stands as-is); write an `<ROUND>_RECONCILE.json` (receipt error verbatim + measured
accomplishments + worker's remaining list + the decision); resume the SAME SID with a
corrective continuation packet.

RECORD-FIRST prevention — put this in EVERY continuation packet:
1. Write the record SKELETON at invocation START (status CONTINUE_REQUIRED, remaining_work =
   current next command, artifacts = what exists, matrix honest UNKNOWN).
2. Refresh the SAME record at each milestone (cluster closed, trial run, keys batch) —
   same invocation_id.
3. At ~65-70 of N turns: refresh checkpoint + remaining file + record, THEN keep working.
4. A record already on disk when the turn ends = the invocation always has an authoritative
   terminal, even on budget exhaustion.

Measured live: the invocation WITHOUT the rule burned one full Manager reconcile cycle
(resume packet + evidence + registry update); the next invocation had its skeleton record
within ~1 minute of dispatch.

Duty-cycle numbers from the same run (size continuation packets accordingly): a
foundation+calibration round used ~50/80 turns (19 min, 127 tool actions); the follow-up
(masks + keys + 3-shot propagation + new infra) used all 80 (88 min, 184 tool actions).
Checkpoint milestones in the packet, not just the final state.

## 8a. RECORD-LAST — the refresh must be the FINAL write of the invocation (measured 2026-10-12, R5 inv #3)

RECORD-FIRST (§8) fired correctly, but a second failure mode followed one round later:

Symptom: the invocation HAD a record (skeleton + milestone refresh worked), yet the
dispatcher still returned NEEDS_RECONCILIATION — this time `artifact hash mismatch: <kind>`.
Cause: the worker refreshed its record at a milestone and THEN kept working, APPENDING rows
to an append-only receipt (`*_RUNS.jsonl`) that the record lists as an artifact; the recorded
sha256 went stale against the newer bytes. The error names only the KIND (`other`) — triage =
recompute EVERY artifact hash yourself and diff record-vs-disk (measured: 12/13 matched,
exactly one stale file named the culprit).

Protocol addendum (put it in every continuation packet NEXT TO record-first):
1. The record refresh must be the ABSOLUTE LAST write before the turn ends — after it, reads
   only. If anything writes after a refresh, refresh the record AGAIN last.
2. Mid-flight records: list only STABLE artifacts (checkpoint .md, scripts, sheets .png).
   Keep volatile append-only receipts (`*_RUNS.jsonl`, rolling manifests) OUT of the artifact
   list until the final record — or accept rule 1 for their hashes.
3. The final TASK_SUBMITTED record is written after ALL writes stop, hashes recomputed at
   that moment.
4. Both failure modes keep historical fidelity: a closed invocation's record is NEVER
   backfilled (missing record in one round, stale hash in the next — both stood as-is); each
   got a `<ROUND>_RECONCILE.json` (receipt error verbatim + measured work + decision) and a
   same-SID resume.
5. A dedicated finalize-only invocation is cheap and isolates the close: copy Manager-owned
   evidence in + set the last matrix row + RECORD-LAST ran 1m54s (00:53:17→00:55:11Z) and
   produced TASK_SUBMITTED with 18 artifacts — the producing invocation's record stayed
   untouched.

## 8b. THIRD failure mode — the refresh landed on ANOTHER invocation's filename (measured 2026-10-12, R6b)

Symptom: dispatcher NR with `[WinError 2] .../evidence/terminal/<THIS invocation id>.json`;
`ls evidence/terminal/` shows only EARLIER invocations' records — and one of them was just
REFRESHED (mtime == this round's close; its `invocation_id` field still names the OLD
invocation, i.e. self-consistent). Root cause: the resumed worker refreshed invocation #1's
record file while working FOR its own invocation — post-compaction context lost the new
`{{INVOCATION_ID}}` and the worker reused the id it remembered. RECORD-FIRST/LAST govern
WHEN/HOW the record is written; this failure is about its NAME.

Protocol addendum #3 (state it CRUDELY in every continuation packet, not merely as a token):
1. "The record of THIS invocation MUST be at `evidence/terminal/{{INVOCATION_ID}}.json` — copy
   the id from THIS packet. The `invocation_id` JSON field must equal the filename. Do NOT
   refresh or edit any other invocation's record file."
2. Self-check before ending the turn: `ls evidence/terminal/` contains a file whose name ==
   this invocation's id; open it, compare the field, confirm hashes postdate the last write.
3. Long queue-bound batch phases (vision sheets, SAM2/keygen batches — measured: one round ran
   3h43m of batch work and still hit 80/80 turns) need MORE frequent milestone refreshes: a
   wrong-named refresh near the end still burns a full Manager reconcile cycle.

Triage of the wrong-file case: the foreign refreshed record is self-consistent — leave it
(never revert it, never backfill the missing one; history stays immutable); NR receipt stands;
reconcile JSON quotes the receipt error verbatim + "refreshed wrong record file"; the fix is
purely forward (next packet carries the naming rule + self-check).

Record failure-mode taxonomy — all measured; extend, don't re-learn:
| # | mode | symptom | prevention |
|---|------|---------|------------|
| 1 | missing record (budget hit pre-write) | WinError 2 + log banner `N/N` | RECORD-FIRST skeleton + milestone refresh (§8) |
| 2 | stale artifact hash | `artifact hash mismatch: <kind>` | RECORD-LAST; volatile append-only receipts out of mid-flight lists (§8a) |
| 3 | wrong record filename | WinError 2, only foreign records present, one freshly refreshed | naming rule + `ls`/field self-check in packet (§8b) |
| 4 | duplicate artifact path inside the record | `one file cannot impersonate multiple deliverables` | dedupe before write; `len(paths)==len(set(paths))` self-check (§8c) |

## 8c. FOURTH failure mode — the same path listed TWICE in `artifacts` (measured 2026-10-12, R6c)

Symptom: the record exists at the CORRECT invocation filename (the §8b fix worked), status
`CONTINUE_REQUIRED`, and the round had NO budget banner — yet the dispatcher returns
NEEDS_RECONCILIATION with `one file cannot impersonate multiple deliverables`. Cause: the
`artifacts` list contained the same absolute path twice (measured: `receipts/R6_LEDGER_VALIDATION.json`
listed as kind `other` on two rows). The validator checks path distinctness before hashes, and a
file that legitimately serves two narrative roles must appear ONCE with one kind.

Prevention (add to every packet's record checklist):
1. Dedupe by normalized absolute path immediately before writing the record.
2. Self-check: `paths = [a["path"].lower() for a in artifacts]; assert len(paths) == len(set(paths))`.
3. At TASK_SUBMITTED additionally assert exactly one `master`/`comparison`/`matrix`/`checkpoint`/`receipts`,
   remainder kind `other`.

Triage: receipt stands; record NOT backfilled; forward fix only. After the fix the next round's
record validated cleanly (29 artifacts, 29 distinct) — mode-4 is cheap to prevent, expensive to
discover (one full reconcile cycle).

## 8d. CADENCE beats milestones — third mode-1 occurrence + the batch must finish INSIDE the turn (measured 2026-10-12, R6e)

Mode 1 (budget hit pre-record) recurred AFTER §8's RECORD-FIRST was in every packet: a resumed
worker doing queue-bound batch work (vision sheets → SAM2 → keygen) ran 3h43m and consumed all
80 turns; another ran 2h15m and stopped exactly at 80/80 with the record still unwritten. Milestone
refreshes are not enough when a single milestone (a batch chain) can exceed the remaining budget.

Protocol that follows (state it in EVERY continuation packet):
1. **Refresh the record after EACH completed batch** (masks batch, keys batch, propagate batch,
   assemble, QA, matrix) — not only at milestones; at ~turn 55 refresh regardless of batch state.
2. **A background chain spawned in-turn does NOT survive the turn.** Measured: a worker left its
   terminal batch running as a bg process (keygen for 2 gap shots, pid recorded in its own notes)
   and hit the budget; by the next reconcile the pid was gone and both shots' outputs were ZERO
   (`work/<shot>/blend` empty). Drive every batch to its receipt INSIDE the turn (poll to
   completion) or leave an explicit next-command in the record. During reconcile, measure the
   batch's OUTPUTS on disk (blend/key counts) — never trust the launch note that it "is running".
3. **Distinguish voluntary stop from budget stop before diagnosing.** Grep the log for the
   `Iteration budget reached (N/N)` banner. A round can end voluntarily right after its record
   (no banner) — then the NR (if any) is a DIFFERENT mode (e.g. §8c), and "budget" is the wrong fix.

Reconcile bookkeeping that held across all four modes: verbatim receipt error + measured
accomplishments + the worker's own remaining list + a `<ROUND>_RECONCILE.json` — and the SAME
SID resumed with a corrective continuation packet. No record was ever backfilled; each closed
receipt stands as-is. Keep a per-round NR count visible to the reviewer: every occurrence burned
exactly one Manager reconcile cycle, which is the argument for the cadence rule.

See also: `background-worker-orchestration/references/controller-race-rendezvous-and-stall-audit.md` —
the dispatcher-side twins of this file (true two-controller race proof + row algebra, stall-audit
precedence vs the venv shim re-exec chain, packet probe false-positive simulation, and the
legacy-harness rerun isolation rule that produced the frozen-evidence drift incident — that
incident is ALSO a record-fidelity case: manifests must hash after the last write).
