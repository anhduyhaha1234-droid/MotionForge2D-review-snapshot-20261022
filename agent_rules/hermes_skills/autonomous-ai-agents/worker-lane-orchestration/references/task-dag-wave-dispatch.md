# Task-DAG wave dispatch (Phase B of a delivery takeover) — measured 2026-09-28

Context: after a PROOF_GATE passes, a 28-task feature DAG (each task = `NEW_SESSION_ONE_TASK`, one exclusive
write-set, binary acceptance) is executed by 2 worker slots + the orchestrator (cap 3 streams). This file records the
loop that worked and the numbers measured on the MotionForge delivery (tasks MF-END-01 … MF-END-18).

## The loop, per task

1. **Read the task's dependency line from the board, then branch the worktree from the DEPENDENCY's commit — not from
   the wave base.** Measured: MF-END-12 depends on MF-END-11, so its worktree was created at `8fa87b8` (MF-END-11's
   commit) so the dependency is PHYSICALLY present in the tree; tasks whose only dependency is the L0 contract used the
   L0 commit (`3602eb2`) as base. Record the base sha in the ledger row. (`git worktree add -b codex/<task>-<date>
   <path> <base-sha>`.)
2. **Before-guard JSON** (one file per task under `manager/guards/<TASK>_before.json`): `head`, `porcelain`,
   per-write-set-path `{exists, bytes, sha256}` — plus the tool-authoritative derived values (`python -m alembic heads`
   for migration tasks). The guard answers two questions the packet must not guess: which paths are NEW (whole-file
   generation allowed) vs EXIST (bounded patch with preimage), and what the baseline tests are. Measured pattern: two
   of five write-set paths already existed (`object_extraction.py` 135,297 B; `segmentation_service.py` 2,792 B) while
   the rest were new — the launch packet states each explicitly.
3. **Launch packet** = wrapper over the task packet: model pin line, worktree + base sha, evidence root
   (`RUN/tasks/<TASK>/**`), the guard facts, the gate order (micro → acceptance/negative → focused → ONE broad gate),
   and — critically — **every capability fact your earlier probes measured, verbatim** (e.g. "`Sam2Segmentation` not
   registered; sam2/sam3 weights missing → probe REAL and record BLOCKED_DEPENDENCY with evidence, do NOT claim SAM3
   applied"). Without this the worker re-discovers or silently substitutes an absent path.
   **UI/frontend tasks get one more packet block, verbatim:** the project's UI conventions (for MF2D:
   Vietnamese helper text under EVERY dark-theme control, `text-gray-400` or brighter, ≥11px — a
   twice-repeated user complaint, so it is an acceptance criterion; bank:
   `motionforge-2d-project → references/frontend-ui-conventions.md`). The worker reads the packet, not your
   chat — a UI rule that lives only in the conversation does not exist. Also verify a UI task with the repo's
   frontend build/lint when one exists; a clean pytest run says nothing about `.tsx` files, and an unlooked-at
   UI stays `NOT_VISUALLY_APPROVED`. Repo-level git stderr noise to expect while verifying commits in these
   worktrees (bad-object refs / geometric repack on a SUCCESSFUL commit): judge by `rev-parse`/`log`/`porcelain`,
   never by stderr — `motionforge-2d-project → references/git-noise-and-commit-verification.md`.
4. **Dispatch one task per new session** (no `--resume`), stagger ~45 s, then resolve the actual session id by
   first-message match against the packet head. One session per task; a correction resumes that task's exact session.
5. **Independent verify on exit** (orchestrator, read-only): commit scope == exactly the allowlisted paths;
   `branch -r --contains HEAD` == 0 (not pushed); re-run the task's OWN test file in the lane's interpreter; when cheap,
   re-run the broad suite. Measured counts from this delivery (each re-run by the orchestrator, not copied from the
   lane): MF-END-01 → 49 passed; MF-END-11 → 78 passed (broad `tests/product_delivery` 127 passed/1 skipped);
   MF-END-18 → 28 passed; MF-END-08 → 29 passed; MF-END-02 → 13 passed; MF-END-03 → 39 passed (route-level
   ingest); MF-END-04 → 31 passed; MF-END-12 → 22 passed; MF-END-13 → 19 passed; MF-END-14 → 34 passed
   (GPU-anchor graph). A lane can also land a correction commit over the same allowlist (MF-END-18 `bc87fa3`
   after `72e3c15`) — verify BOTH commits cover only the allowlist, not just the tip.
6. **Fill the freed slot with the next DAG-READY task** (all its dependencies' commits are in its base). If no task is
   dependency-ready, the slot stays idle and the ledger records why — never start a task whose dependency chain is
   incomplete to keep a slot warm.
6b. **Recompute the ready-set over the WHOLE DAG after every archive — a side-branch task can be ready while you track
   only the critical chain.** Measured near-miss 2026-09-28: `MF-END-09`'s four dependencies (03/04/08/18) had ALL landed
   by ~15:00, yet the orchestrator kept reporting "next ready: <critical-path task>" and only discovered 09 was ready at
   17:31 when composing an ETA — it dispatched at 18:03, ~3 h late. Operational shape: keep one table
   `task → deps → each dep's commit → READY?` and recompute it at every verify-loop (costs one parenthetical query),
   not just when a slot frees. When several tasks are ready, prefer the one that unblocks the longest downstream chain
   (or the one whose base sha is already materialized), and note the choice + why in the ledger row. A tool-lane branch
   (02→07→10) and a core-lane branch run in parallel from the same wave; walking one chain serially while the other
   branch is ready is the failure mode this bullet exists to prevent.

## Multi-dependency bases: bring the second dep in with a transport merge

A task can depend on two (or more) tasks whose commits live on DIFFERENT branches with no shared linear history
(measured 2026-09-28: MF-END-14 depends on MF-END-08 + MF-END-13). Branching from one dep's commit leaves the other
dependency absent from the tree — the worker would then guess an interface it cannot read.

Recipe (measured, conflict-free because the two write-sets are disjoint):

1. `git worktree add -b codex/<task>-<date> <path> <dep-A-commit>` — start from the deeper/longer chain.
2. Inside the worktree: `git merge --no-ff <dep-B-commit> -m "transport <TASK> (<name>) into the <TASK> base"`.
3. Assert `git status --porcelain` == 0, then list the dependency's own paths (e.g. `app/media_workflows/…`) to prove
   they are physically present. Record the RESULTING base sha (not dep-A's sha) in the guard + ledger row, e.g.
   `"transport": "merged 1ce1a4b (MF-END-08) --no-ff"`.
4. Later tasks that depend on either dep inherit the merge for free (MF-END-16 branched at `88ef530`, which already
   contained 08+11+12+13+14).

Do this as the orchestrator at guard time — never ask the worker to merge; a worker merging into its own tree makes
the dependency provenance unverifiable from outside.

## Orchestrator context economy across a multi-hour wave (measured practice)

A 28-task wave ran ~12 h inside ONE orchestrator context. What kept it operable:

* **One verify-and-dispatch cycle per exit, in the SAME turn.** Exit notification → `tail` the log → `git log/show
  --stat` the commit chain → orchestrator re-runs the task's test file → write the next launch packet → dispatch →
  bookkeeping. Never leave a freed slot idle waiting for a later turn, and never report an exit without the next
  dispatch in the same reply.
* **Batch the bookkeeping into ONE terminal call.** Resolve the new session id (first-message match against the packet
  head, read-only DB) + write the ledger JSON + rewrite the monitor's `LANES` line happen in a single `python -c`
  invocation; the `append_ledger` call and the next dispatch go in the next (or same) call. Measured effect: per-archive
  overhead stayed at ~2 tool calls over 20+ dispatches.
* **Packets are a fixed template; only the task-specific block changes** (task id, base sha, guard facts, capability
  facts, budget line). Rewriting prose per task burns the same context you need for verification.
* **Heartbeat ticks get one-line replies.** A bounded monitor fires every ~8 min; treat each tick as a status digest
  (lane msgs/api/age, `end=None` vs terminal), not as a place to re-derive the plan. Stale-lane rows in a monitor that
  predates the last lane-set change are EXPECTED (see traps) — verify against the DB before reacting.
* **Keep the ledger row schema constant** (`event, task, round, actual_session, grade, commit/base/guard, state`) so a
  later reviewer can query the whole wave with one filter; append-only, prefix-hash asserted.

## Traps that bit (all measured)

* **`app/media_workflows/` may not exist in an older base** — a task whose write-set adds a file there must create the
  directory under its allowlist; note it in the packet so it is not read as scope creep.
* **One task can legitimately produce a follow-up transport commit**: MF-END-08 landed `1ce1a4b` then `fedd33b`
  (manifest determinism: `generated_at_utc` derived from the frozen receipt instead of wall clock; two runs
  byte-identical). Verify BOTH commits cover only the allowlist; a correction commit is fine, a second write-set is not.
* **A BLOCKED row can be the correct outcome**: MF-END-18's real-server smoke stayed `BLOCKED` by guard design (no live
  Comfy call in that task) — that is a PASS-shaped disclosure, not a failure; keep it visible in the ledger row.
* **Migration head pins go stale between waves** (see SKILL.md rule 26): resolve with `alembic heads` at guard time for
  every task that touches migrations, and re-resolve after each migration lands.
* **The proof lane's own "next step" proposals drift** (see SKILL.md rule 24): the packet, not the worker's closing
  report, decides the next variable — measured when a lane proposed continuing into a challenger whose weights were
  already measured absent.
* **A running monitor binds its lane list at process start — editing the script does NOT update it.** Measured
  2026-09-28: after each lane change the old instance kept polling the dead lane set and printed `STALL_AUDIT>8min`
  for lanes that had already exited 0 (false positives reading exactly like stalls in the heartbeat log). Every
  lane-set change needs a NEW instance (new script name + new log file); leave obsolete instances to expire or kill
  them by exact PID — never reuse one live monitor across lane sets.
* **Lane gate rows vs orchestrator test counts are two different units.** The lane reports its frozen ROW count
  (e.g. "16/16 PASS"), the orchestrator re-runs the TEST FILE and reports `N passed` (e.g. 49, 78). Both are true;
  quote them as rows vs tests so a reviewer does not read one as contradicting the other.
* **A protected test outside the write-set can be changed LEGITIMATELY — verify the mechanism, not the file.** Measured
  2026-09-28 (MF-END-05): a task that changes an authority (cast completeness now dispatches on `pack_contract_version`;
  a migration head re-point) can break a *previously-green* test owned by an EARLIER task. The correct mechanism — which
  the worker used and the orchestrator accepted — is: write `writeset_guard_protected_test_change.json` (impacted
  assertion + writer attribution + reason) **BEFORE** patching, then patch, then keep the guarded test passing. Verify
  three things on exit: (a) the pre-registration file's mtime/hash predates the patch, (b) porcelain == allowlist + the
  ONE disclosed protected file and nothing else, (c) the protected test still passes when you re-run it yourself. Also
  require the disclosure to carry any PRE-EXISTING failures measured on the base (MF-END-05 disclosed "5 fails are red on
  base too, re-measured") so a reviewer never reads inherited red as new damage.
* **Iteration-budget advisories belong in the packet, calibrated per task size — and the fallback half is what saves
  the commit.** After the wave's biggest task hit the hard 160-turn ceiling with work uncommitted (SKILL.md rule 4,
  fourth shape), every subsequent launch packet carried a TWO-PART line: (1) a call budget — `~70 calls` for a focused
  tool task, `~85–95` for a core task that may touch a GPU job; (2) a commit-early fallback — "if you approach ~120
  calls and are not finished: commit exactly the allowlist + close REPORT/final_gate, then stop; do not start new
  scope." A budget number alone is diagnostic for the orchestrator (a lane landing at 0.9× budget is the one to
  suspect) but does nothing for the worker, which cannot see the 160 ceiling coming.
* **The finishing-packet recovery is now VALIDATED end-to-end — reuse the exact shape.** Measured 2026-09-28, MF-END-19:
  the original run died at 160/160 with `git log` showing only the transport commit, while `porcelain` held 4 modified
  + 2 new files and the orchestrator's own run of the task test file passed (31 passed). The 4-step packet — (1) re-run
  2 test commands (task file + public_chain), (2) close missing evidence (REPORT/final_gate/commands.jsonl appendix),
  (3) commit **exactly the porcelain path list measured before the resume**, (4) print the terminal line — finished in
  **5m46s**: commit landed with exactly the 6 measured paths, orchestrator re-run 32 passed, porcelain clean, no push.
  Operational details that matter: dispatch it as a NEW packet file + `--resume <same session>`; name the round's log
  and receipt `<TASK>-finish.log` / `<TASK>-finish.json` so the truncated round's receipt is NOT overwritten; append one
  ledger incident row named `BUDGET_EXHAUSTED_AND_RECOVERY_DISPATCHED` carrying the measured disk state (porcelain list,
  the test count you ran yourself, evidence-dir inventory) and the recovery dispatch id; keep every DEPENDENT task
  queued until the finish commit lands.

## Wave tail → exit phase (measured plan, 2026-09-28 ~19:20, 22/28 archived)

At 22/28 archived the ready-set table showed **every remaining task (24,25,26,27,28) transiting the one running
node (MF-END-23)** — 24/26 need 23 directly, 25 needs 10+24, 27 needs 20+25+26, 28 needs 18+25+26+27. Consequences
and the shape that followed:

* **Second slot stays IDLE and the ledger records why** (bullet 6 above). Do not dispatch an out-of-order task to
  keep the slot warm; the correct fill is orchestrator-side prep.
* **Prep artifact written while waiting: `manager/S12_INTEGRATION_PLAN.md`.** Contents that made the exit phase
  mechanical — (a) per-task branch/commit table for 01…28; (b) topo `merge --no-ff` transport order from the wave
  base, asserting `porcelain == 0` and re-running the focused + `public_chain` suites after each merge; (c) ONE broad
  wave on the merged tree (`pytest tests/product_delivery tests/product_p1 -q` + ruff + py_compile) with rc/counts
  recorded; (d) freeze the candidate SHA; (e) run DEMO E2E and produce the demo artifact **through the PUBLIC APIs,
  on the frozen candidate** — not from worktree shortcuts; (f) S12 review packet returned to the USER at the chat
  (orchestrator never self-approves); (g) an explicit do-not-open list: `APPROVED` / `CLOSED` / `QUALITY_ACCEPTED>0`
  / push / next-sprint gates all stay with the reviewer.
* **Commit-chain verification (generalized from the trap list):** the unit is `git log --oneline <base>..HEAD` plus a
  per-commit `--stat` scope check — correction commits are expected and legitimate (MF-END-18 `72e3c15`+`bc87fa3`;
  MF-END-20 `2e403fc`+`df4e3d4` ruff wrap), each must stay inside the allowlist; `branch -r --contains HEAD` must
  stay 0 (nothing pushed) through the whole wave.

## Wave close-out: transports, conflicts, and the single-tree proof (measured 2026-09-28 late — 28/28 archived)

* **Conflict class in transports = complementary additions — keep BOTH sides.** Through ~25 transports only ONE was not
  conflict-free: merging MF-END-10 into the MF-END-25 base conflicted in `app/workflow/job_handlers.py` because BOTH
  sides only ADD one handler registration (MF-END-15 `register_shot_anchor_handler` vs MF-END-09
  `register_reference_asset_handler`). Resolution = keep both blocks verbatim, `git add` the file, commit the merge,
  and append a `transport_with_mechanical_conflict` ledger row naming the file + both sides + the rule used. Never
  `-X ours/theirs` over new content; a resolution made inside a task chain then lets the final integration absorb that
  branch cleanly (this one did).
* **Integration batching: merge the LATEST tips that transitively contain earlier tasks, not all N branches.** For 28
  task branches, 6 `merge --no-ff` transports into an `INTEGRATION` worktree cut from the wave base covered everything
  (tips: `fda3df1` 01-04 · `3844ac8` 05-07 · `fedd33b` 08 · `29bc006` 08,11-14,16,17 · `bc87fa3` 18 · `b1965ad`
  09,10,19-27). Measured: **6/6 zero-conflict, porcelain 0, HEAD `656359fd`.** Verify the tip-coverage claim before
  merging by walking each tip's ancestry once (`git log --oneline <tip> | head`), and record the mapping in the ledger.
* **The single-tree proof is the exit gate before any freeze:** `python -m pytest tests/product_delivery
  tests/product_p1 -q` on the merged tree = **827 passed, 3 skipped, 0 failed in 550.60 s**, plus an import smoke of
  5 representative modules (`shot_reskin`, `media_workflows`, `shot_reskin_executor`, `series_batch`,
  `s12_export.preflight`) and `porcelain == 0`. Log it with rc + counts + candidate sha (`manager/logs/
  INTEGRATION-broad-wave.log`, ledger event `INTEGRATION_BROAD_WAVE_PASS`). Only after this green does the
  freeze/demo phase start — a freeze taken on an unmerged or partially-merged tree proves nothing.
* **Both finishing-packet recoveries now measured:** MF-END-19 (5m46s, commit over an untouched transport parent) and
  MF-END-23 (3m28s, commit `4444f8c`, 5 allowlist paths, porcelain [] post-commit); the third cap sighting
  (MF-END-26) needed NO packet because the commit + evidence had already landed — see SKILL.md rule 4's "order the
  recovery checks" clause. Pattern to reuse: `porcelain` list → orchestrator runs the task test file → 4-step packet
  (2 test commands, close evidence, commit exactly the measured paths, terminal line) → new `<TASK>-finish.*`
  log/receipt names → incident ledger row → dependents stay queued until the finish commit exists.
* **Windows argv ceiling, measured while shipping a large generated test through a worker tool:** escaped-argv length
  ~25.0 KB spawns fine, ~32.5 KB dies with `WinError 206` (fixed overhead ≈2 KB). Long payloads (fixtures, generated
  scripts, JSON) must be written to FILES and invoked by path; a tool that assembles them on the command line needs a
  size policy that cascade-drops instead of raising, and the gate should re-verify its own result from the rows.
