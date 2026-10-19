---
name: worker-lane-orchestration
description: "Use when running parallel resumable CLI worker lanes."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [orchestration, workers, provenance, ledgers, verification]
    related_skills: [worker-orchestration, pm-worker-orchestration, background-worker-orchestration, terminal-engineering-discipline]
---

# Worker Lane Orchestration

Running a **fleet**: N long-lived CLI agent sessions ("lanes"), each owning one Task ID, resumed across rounds, whose
evidence must stay auditable long after the agents are gone. This is the fleet layer — for delegating a single subtask,
use the plain delegation tools instead.

## When to use

- Several worker lanes run concurrently (2–5+) against pinned trees, with a shared evidence root per run.
- Lanes are **resumed** across rounds (`--resume <parent>`), so session ids, packets and receipts must be reconciled.
- A reviewer will later re-derive *which session produced which bytes*, and whether a run actually finished.

## Hard rules

1. **One packet file per lane per round.** The cheapest durable proof of lane identity is
   `first-user-message == head-of-packet`. A merged/shared packet destroys that proof (all lanes' first messages become
   byte-identical) — if you must merge, record dispatch-order→session as INFERRED, never as proven.
2. **`--resume` semantics depend on the CLI shape.** `-z --resume` MINTS a successor id; `chat -q … --resume` CONTINUES
   the same row in place (measured 2026-09-27: msgs 196→247, api 90→114, `end_reason` stays null) — so a same-id mapping
   must still be PROVEN from the DB, never assumed from the shape. The id you dispatched with is a *request*, not the writer. Every ledger row
   carries `parent_session`, `actual_session` and `actual_session_proven_by`; resolve actuals from the read-only session
   DB by first-message match (newest wins), never from dispatch order or start-time ordering.
3. **Heartbeat the ACTUAL session, not the parent.** A parent's last message ages for hours while its continuation works —
   reading the parent manufactured a false "341 min idle, probably stalled" alarm. Resolve, cache, then measure age.
4. **Exit codes are not verdicts — in either direction.** `exit 0` with a 125-byte log = a connection flap that did nothing;
   `exit 1` with `no final response was produced` = a run that still landed its commit, report and evidence. A third shape:
   `exit 0` after the budget window with the gates green and the log tail **self-declaring the remaining steps** (e.g.
   "CHƯA XONG (3 việc): REPORT.md + MATRIX.md; run <deliverables script>; local commit") = the run ended on its TURN
   BUDGET. For that shape resume the same actual session with a SHORT **finishing packet** that: enumerates the log's own
   remaining-steps list verbatim as numbered steps; forbids touching anything outside the write-set — a failing test that
   lives OUTSIDE the write-set is disclosed with its resolution options left to the reviewer, never edited to go green;
   and requires the shrink-guard byte/line delta alongside the commit. Decide from disk (log payload + `git log`/porcelain
   + report + evidence count), then say which shape you measured. A fourth shape, measured 2026-09-28 on the biggest
   integration task of a 28-task wave: the tail prints `⚠ Iteration budget reached (160/160) — response may be incomplete`,
   exit is 0, `git log` still shows only the base/transport commit — **the work exists on disk but was never committed**
   (`porcelain` = the task's modified files + `??` new files, and re-running the task's OWN test file yourself passes).
   Protocol for this shape: **measure disk BEFORE writing the finish packet** (porcelain listing, orchestrator-run pytest
   of the task's test file, evidence-dir inventory), then resume the SAME session with a 4-step packet — (1) re-run 2 test
   commands, (2) close missing evidence (REPORT/final_gate/commands.jsonl appendix), (3) commit **exactly the measured
   path list**, (4) terminal line — and **cap the packet at ≤40 tool calls** (`no GPU, no scope expansion`) or the retry
   burns the budget again. Keep every task that DEPENDS on the unfinished one queued until the finish commit lands; do
   not fill the freed slot with a dependent task whose dependency is not yet committed. Preventive half: after the first
   such incident, every new dispatch packet carries an explicit call-budget line (~70–95 calls) — the hard 160-turn
   ceiling is hit by exactly the largest integration tasks, and the worker cannot see it coming. Pair the number with a
   commit-early fallback ("approaching ~120 calls and not finished → commit exactly the measured path list + close the
   report, then stop; do not start new scope") — without it the worker spends its last turns polishing and dies
   uncommitted. Give each resume round its OWN log/receipt filenames (`<TASK>-finish.log` / `<TASK>-finish.json`) so
   the truncated round's receipt survives as its record. **Order the recovery checks so the cap message ALONE never
   triggers a packet:** read `git log -1` + porcelain + evidence-dir inventory FIRST — a cap reached AFTER the commit
   and the evidence closure (measured: the 160/160 message printed in the lane's final summary turn while the task
   commit and a ~9 KB REPORT were already on disk, porcelain clean) is a COMPLETE lane; verify it like any other exit
   and dispatch nothing. Only the missing-commit variant gets the finishing packet (two measured recoveries now:
   5m46s and 3m28s, each landing a commit whose parent is the untouched transport/base commit).
5. **Enforce the concurrency cap with an audit trail.** When a lane slips past the cap, stop the NEWEST chain (least
   invested) by exact PID **leaf→root**, prove zero collateral (diff the interpreter's pid set before/after), keep its packet
   written and hashed for re-dispatch, and append a row whose outcome literally reads `STOPPED_OVER_CAP` with the reason.
   Queued, never deleted. Never `taskkill /T`, never name/port-wide kills.
6. **Copying a tool suite into a new run root carries the old absolute paths.** Grep every carried-over tool for the previous
   run id and fix ALL of them before the first dispatch. And: a launcher still inside its `sleep` has **not** refused
   anything — poll it to completion before declaring the chain stopped, or you will dispatch a duplicate and end up with two
   writers on one Task ID.
7. **Guard before you trust.** A post-writer guard needs (a) its preflight baseline JSON and (b) a per-lane write-set
   manifest to exist; with either absent it dies with `FileNotFoundError` and reads like a lane failure. Lanes that are
   still writing legitimately appear as "protected tree drift" — exclude the live ones, say so in the verification note,
   and keep the guard strict for everyone else rather than weakening it.
8. **Your gate expectations are hypotheses.** Two final-gate "failures" were my own wrong filename expectations; the
   deliverables were elsewhere (one in the lane's `REPORT.md`, one canonical copy in the repo under
   `docs/pm/sessions/<SPRINT-INT01>/` while the evidence root held only `raw/<name>.json`). List the directory and re-read
   the lane's own deliverable list before declaring anything missing — correct the CHECK, not the artifact.
9. **Hash what you quote.** A hash copied from a worker's prose matched no file among 61,206 scanned; the real digest came
   from computing it myself. Recompute every hash that enters your own report/review, and if a published number later
   proves wrong, correct the document **with a disclosed correction note**.
10. **Timing honesty.** Sum of worker durations is *aggregate worker time* (parallel lanes overlap); program elapsed is
    last-receipt-minus-first-dispatch. Report them as separate numbers and label the aggregate as such.
11. **Read-only session DB, always.** Open with `mode=ro`, never mutate/vacuum, and fetch `rows = list(cur.execute(...))`
    before querying inside the loop — reusing one cursor truncates the scan and turns every match into "UNRESOLVED".
12. **Terminal vocabulary.** Lanes end `TASK_SUBMITTED`; only an independent reviewer writes `APPROVED`/`CLOSED`. An
    orchestrator that declares its own success has removed the reviewer's job.
13. **An empty stdout log is NOT a stall — liveness comes from the DB + disk.** Measured: lanes ran 25+ minutes with
    **0-byte logs** while the read-only session DB showed 30–77 messages and the worktrees were already patched; the log
    only ever received a 124/125-byte flap payload at exit. Heartbeat from per-session `messages` count + last-message
    age + `api_call_count`, plus an evidence-root file inventory and the worktree porcelain count. Empty log + growing
    rows = healthy lane.
14. **One NEW packet per RESUME, carrying measured disk state.** After a flap: wait the mandatory 5 minutes, resume the
    ACTUAL session (not the parent; after a second flap, the NEWEST actual — resumes chain), and write a new packet file —
    reusing the old packet makes both sessions' first messages byte-identical and destroys the mapping proof. The resume
    packet lists what landed with numbers, the exact failing rows, and "do not restart finished work". Work parked in
    `%TEMP%` is not durable evidence: require the owner to apply it into the tree (bounded patch-with-preimage) and
    re-create every raw artifact under the evidence root. **After the resume lands, re-point EVERY probe, monitor and
    heartbeat at the new actual id** — a monitor left polling the dead session keeps printing `end=agent_close / +0msg`
    and reads exactly like a lane failure in your own heartbeat log; give the replacement monitor its OWN log file so
    stale and fresh rows never mix in one evidence file. A third flap class is PAYLOAD-shaped: the provider can reject a
    run for an oversized tool message (`HTTP 422 … messages.<N>.tool.content.str` after 3 retries — measured at ~275k
    context / 424 msgs), often followed by a 502 on the retry. The fix is preventive and belongs in every long-lane
    packet: write files via short scripts, print ≤200-char confirmations, never `cat` large blobs into tool output.
    When the user asks why a lane stopped, answer in three lines — measured cause class · what already landed on disk
    with numbers · the relaunch being issued now — and issue that relaunch in the same turn.
15. **Append-only ledgers: assert the immutable PREFIX, never the whole file.** Snapshot pre-append bytes next to the
    ledger; refuse to append when the prefix hash drifts; after each append assert `prefix_sha256` unchanged and
    `rows == prefix_rows + appended`. The whole-file hash is valid only BEFORE the first append. Corrections are new
    events citing the old row number — never edit or delete old rows.
16. **Heartbeat cadence: bounded monitor + `watch_patterns`, not `notify_on_complete`.** `notify_on_complete` fires only
    at exit. A bounded read-only monitor that prints one line per poll and is launched with `watch_patterns=['iter ']`
    wakes you every poll interval (≤20-min heartbeat, >8-min stall audit) without becoming an unsupervised watcher.
    Setting both flags silently drops `watch_patterns`.
17. **A long-lived orchestrator session at the turn-budget ceiling is EVIDENCE-ONLY — audit it, never mint a duplicate.**
    Measured 2026-09-27: the canonical Manager session sat at 451/450 `api_call_count` with `end_reason=null` and 1,223
    message rows — resuming it would die mid-turn, and message count alone never proves death. When the user bridges the
    next prompt into a fresh chat, THAT chat performs the role: append one `context_health_and_bridge` event (message
    count, api_call_count, the ceiling reading, the decision, and why no new manager lineage was created) and keep the
    canonical id for registry/ledger lineage only. The bridge is a documented act of the user, not a recovery the
    orchestrator grants itself; a duplicate lineage is worse than a recorded bridge.
18. **The post-writer guard must prove the DECLARED row set actually exists — and every static gate must be non-vacuous.**
    Four cheap Manager checks, each caught real exposure in the 2026-09-27 round: (a) count `def test_<frozen-prefix>` in
    the worker's new test file and compare against the count YOU froze in the matrix — a worker can report "8/8 green"
    while the file defines fewer runners, and the reverse (extra names) means the row map drifted; (b) re-run the static
    gate yourself and REJECT `All checks passed!` when the tool resolved zero files — a linter invoked from the wrong cwd
    prints exactly that banner with rc 0 (a worker self-disclosed this after auditing its own gate script; the fix is to
    assert the version banner AND the absence of `No such file`/resolution errors, or count the files claimed); (c) keep a
    PRE-EXISTING untracked list per tree so the porcelain-vs-allowlist check does not flag files that were already there
    before dispatch — a phantom scope violation is the same bug class as a phantom pass; (d) re-run the frozen micro set
    AND its retained predecessors yourself in the lane's own interpreter, and record the counts as MANAGER verification —
    measured 2026-09-27: `pytest test_gate_identity_race_r27.py test_durable_resolve_d.py` => `23 passed in 1.87 s`
    (8 new race rows + 15 retained) and the VIDEO lane's new file => `13 passed in 1.05 s`. It is the cheapest
    independent execution of the lane's own contract and it catches a "green" that came from a differently-scoped run.
19. **A green row carrying an OPEN finding is a delivery shape, not a contradiction — route it, never fix it from the
    orchestrator seat.** Measured 2026-09-27: a worker's row went green on the ENFORCED contract while pinning 4 checks plus
    a typed runtime event that flag an unfixed P1 whose repair lives in a file outside its write-set; the worker asked
    (a) accept with routed delta, or (b) extend the write-set. Correct call is (a): an orchestrator does not widen a
    write-set granted by the authorizing prompt. Record the finding as a NAMED delta for the reviewer with the exact
    file:line/symbol and the run that proves it, require the row to keep pinning the defect (typed event + checks) so it
    cannot regress silently, and state in the report that the adapter-side "make it loud" half was done while the
    storage-side half stays open. The worker proposing the extension is expected; granting it is not the worker's or the
    orchestrator's call.
20. **Accept deliverables by READING them, not by their presence — and don't panic at a harness mutation warning.**
    Two mirrors of one rule, both measured 2026-09-27: (a) a lane's harness printed
    `File-mutation verifier: 1 file(s) were NOT modified this turn ... [patch] Found 4 matches` — the un-patched file was
    the lane's own generator script, while every DELIVERABLE was on disk with real substance (`REPORT.md` 21,292 B,
    `MATRIX.md` 7,990 B, `RAW_EVIDENCE_INDEX.md` 21,550 B, `results.json` 7,869 B and `json.loads`-parses with the
    expected keys incl. `media_generated:false`). Decide from the artifacts the round promised, not from the tool that
    was supposed to write them; state the warning in the ledger row rather than silently dropping it. (b) The reverse:
    `ls` showing a file exists is not acceptance — open it, parse it, and check the fields against the round's claims
    (a 0-byte or stub deliverable passes an existence check and fails a reader).

21. **Copy evidence-root paths VERBATIM; a retyped path silently splits the evidence.** Measured 2026-09-27: the packet
    root was spelled `c-v-th-c-h-i-n` while the canonical run dir is `c-v-th-c-hi-n` (one hyphen fewer) — both workers
    created a NEW parallel tree at the typo path and wrote their first 6 artifacts there; nothing failed, nothing warned.
    Containment: stop the writers by exact PID leaf→root; snapshot the stray bytes (hash-verified) and LEAVE them in
    place; patch the packet with the canonical path plus a short INCIDENT NOTE instructing the owner to COPY its stray
    files into the canonical root under `raw/incident_wrong_root/` with a README; relaunch as `-r2`. After EVERY dispatch,
    list the intended root and confirm where writes actually landed — pull the path string from the packet source, never
    retype it from memory (a directory listing showing fewer files than expected is the tell).
22. **Lane liveness = launcher/agent processes + receipt, not session-row age.** Under `chat -q --resume` a FINISHED lane
    keeps `end_reason=null` in its session row (same row, no terminal stamp), so an age-based monitor prints
    `STALL_AUDIT>8min` for a lane whose launcher already exited 0. Before escalating any stall (or trusting a monitor's
    "running" row), check for the launcher/agent process and the receipt file; when the lane set changes, rebuild the
    monitor with only the live lanes and give each rebuild its OWN log file so stale rows never mix into fresh evidence.
23. **Verify media gates on the PIXELS, and treat pad/resolution deltas as pipeline items.** Measured 2026-09-27: GPU
    proof liveness was confirmed by `nvidia-smi` (VRAM 11.6/12.2 GiB, util 100%) while `output/` was still empty — the
    cheap way to distinguish "prep" from "actually sampling". Then the Manager viewed each generated anchor against its
    source frame with native vision: structure matched (roles, holder, book-closed first-frame state, partial edge person)
    while two deltas needed explicit policy — latent padding made renders 640×368 instead of the source's 640×360
    (assembly must crop back to the declared bbox or the timeline drifts), and the source watermark was dropped
    (defensible, but it must be a DECLARED policy, not a silent side effect). A visual pass is an observation record,
    never a quality acceptance.
24. **The successor packet must re-pin measured capability verbatim — a worker's own \"next step\" drifts to the research ideal.** Measured 2026-09-27: after the lane's own P0 pass proved certain node classes unregistered and some weights groups absent, its closing report still proposed continuing into that missing path (naming the uninstalled challenger by name, because the research doc lists it as preferred). The correct next packet re-states the measured constraint (\"the challenger this round = the INSTALLED one, not the one whose weights are absent\") and repeats the BLOCKED_DEPENDENCY list. Rule: every capability fact your own P0/registry measurement produced goes into every later packet that could depend on it, verbatim — otherwise the worker spends a round rediscovering it, or worse, silently substitutes a path you already know is absent.

25. **Never attribute a performance delta to a config change when a cold/warm restart coincides.** Measured 2026-09-28:
    a lane reported a 15.5× speedup (596.95 → 38.67 s per output-second) immediately after a graph fix — the real cause
    was COLD vs WARM server state on the SAME config (the fixed graph's own first run was still cold). Publish BOTH
    numbers per profile (cold = first run after server start; warm = subsequent runs), label them in every cost table and
    ETA, and only claim an improvement when a controlled A/B isolates one variable. An ETA built on the warm number must
    also price one cold run per server start. (The same discipline applies to any first-run-vs-repeat measurement:
    cache on/off and chunk-overlap variants here produced PIXEL-IDENTICAL output — max_abs 0 — with different file shas,
    i.e. container-level only; say that explicitly rather than implying a quality delta.)

26. **Pin guard values from the tool's own authority command; a worker-measured correction IS the fix.** Measured
    2026-09-28: my hand-rolled regex scan of migration `down_revision` chains resolved a STALE head (`f7a8b9c0d1e2`) and
    I pinned it in a launch packet; the worker measured the real sole head (`d4e5f6a7b8c9`) with alembic, chained the new
    migration correctly and disclosed the stale pin in its evidence. Rule: before pinning any derived value in a dispatch
    packet (migration head, node class name, weights path, port, sole-head filename), obtain it from the authoritative
    tool — `python -m alembic heads`, the live `/object_info`, a directory listing — never from your own text-scan of
    source. If a worker reports your pin was wrong: record a `manager_guard_correction` ledger row, switch the guard
    `manager_guard_correction` ledger row, switch the guard method for all later tasks, and keep the worker's measured value.

27. **Verify the whole commit CHAIN `<base>..HEAD`, not just the tip — and bank the exit phase before it starts.** Two
    measured shapes from the same 2026-09-28 wave. (a) Correction commits legitimately extend a task's history (MF-END-18
    `72e3c15`+`bc87fa3`; MF-END-20 `2e403fc`+`df4e3d4` ruff-E501 wrap), so the verification unit is
    `git log --oneline <base>..HEAD` with a per-commit `git show --stat` scope check — a green tip can sit on top of a
    commit that touched an outside path. (b) When the DAG is ~75%+ archived and EVERY remaining task transits one still-
    running node, no task is dependency-ready: keep the other slot idle and record why (never warm a slot with an
    out-of-order task), and spend the window writing the exit-phase plan — topo `merge --no-ff` transport order, ONE broad
    wave on the merged tree, freeze the candidate SHA, then run DEMO E2E and produce the demo artifact through the PUBLIC
    APIs **on that candidate**, then the review packet back to the USER at the chat with an explicit do-not-open list
    (`APPROVED`/`CLOSED`/`QUALITY_ACCEPTED>0`/push/next-sprint stay with the reviewer). Shape + measured numbers:
    `references/task-dag-wave-dispatch.md` § "Wave tail → exit phase".

28. **Post-freeze, the demo E2E is the integration instrument — budget N delta rounds and route each finding as
    its own delta.** Measured 2026-09-28/29 (28-task wave): after the single-tree proof and the freeze, the
    real-run demo surfaced live seams that every green unit suite could not see, and each re-run removed one
    fault and exposed the next behind it — R1 → F1/F2 (persistence projection + media-kind bucket), R2 → F4
    (producer/consumer key-space: route keyed `role_id`, worker read `layer_id`), R3 → F5 (a declared pad
    transform invisible to the QC consumer). Budget rounds R1…R4 up front; branch every delta **from the frozen
    candidate sha** (never from the originating task's base); embed the finding's raw evidence paths (failing
    run/job ids, captured payloads) in the delta packet; advance the freeze label per merged delta and re-run
    the full wave each time. The delta's test fixture must be built **BY THE REAL PRODUCER** (captured run
    artifacts / route-built payloads) — a hand-rolled fixture freezes the author's key-space assumption and
    stays green while the real seam dies (measured: 6/6 green, real run dead at chunk 0, 0 GPU). Full recipe +
    measured numbers: `independent-evidence-verification →
    references/iteration-budget-exhaustion-and-finish-packets.md` §7 (also §4d-ter deferred generated-artifact
    regen — do it once after the LAST `app/**` change, in the advancing commit — and §7c: never write a
    40-hex sha you did not measure).

29. **A usage ledger keyed `(session, api_call_no)` silently DROPS every resumed round — and the route proof
    needs the log, not the launch flag.** Measured 2026-09-29, two defects in the same tool. (a) The daily ledger
    deduped on `(session_id, api_call_no)`; because `--resume` RESTARTS call numbering at `#1`, the entire second
    round collided with round one and vanished — the tool printed `rows_added=0` while the raw log plainly held new
    requests, which reads exactly like "the provider stopped logging". Key per REQUEST instead:
    `(session, api_call_no, model, at_local_timestamp)`, then make reconciliation a hard gate — parse the raw log for
    the distinct set and assert `missing == 0 and extra == 0`, printing per-session counts (measured after the fix:
    `truth 120 = have 120, missing 0 extra 0`, split 59 + 61; before it: `truth 119, missing 15`). Never rewrite the
    buggy ledger: emit `usage-ledger.v2.jsonl` beside v1 and state which file is authoritative. (b) When the user
    mandates a NEW model for resumed lanes, `state.db.sessions.model` is stale (it records the CREATION model) — the
    proof is the per-request receipt `agent.conversation_loop: API call #N: model=… provider=… in=… out=… cache=X/Y`.
    Grep by `model=`, NOT by session id: one resumed session's log held 100 calls on the old model plus 60 on the new
    one, so a session-id grep mixes routes and proves nothing. Genuine route switch = new `model=` string AND the
    `API call #` counter restarting at `#1`. Prove fallback-OFF separately with `hermes fallback list`
    (`No fallback providers configured`); report both rounds' call counts instead of crediting the whole session to
    the new route. Full recipe + the `Path("")`/`Path(".")` monitor crash and the `job.status`→`job.state` column
    trap: `independent-evidence-verification → references/model-route-receipt-and-usage-ledger.md`.

## Standard loop

`preflight (trees/ports/GPU/processes) → freeze the finite matrix → write per-lane packets → dispatch with stagger →
resolve actual sessions → heartbeat actual sessions → on terminal: byte guard → verify claims on disk → recompute the
DAG ready-set → fill the freed slot → repeat → final gate → deliver the packet, stop at the review boundary.`

## Support files

- `references/lane-dispatch-recipes.md` — copy-pasteable shapes: dispatch-ledger row schema, read-only session resolver,
  cap-enforcement row, guard/manifest checklist, timing accounting, and the incident record for a duplicate dispatch.
- `references/live-progress-and-flap-recovery.md` — empty-log progress probe fields, the 502-flap resume checklist,
  bounded-monitor cadence, and the append-only ledger prefix verifier.
- `references/task-dag-wave-dispatch.md` — the per-task wave loop for a dependency DAG (28-task class): worktree from the
  dependency's commit, **multi-dependency bases via `merge --no-ff` transport**, before-guard JSON, independent verify
  counts (rows vs tests), filling the freed slot by DAG-readiness, monitor rebuilds per lane-set change, **wave
  close-out** (complementary-addition transport conflicts → keep both sides; tip-coverage integration batching;
  the 827-passed single-tree proof gate before freeze; the Windows escaped-argv ceiling; both finishing-packet
  recoveries), and the measured Phase-B numbers from the 2026-09-28 delivery.
