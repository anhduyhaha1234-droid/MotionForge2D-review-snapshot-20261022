---
name: independent-evidence-verification
description: Verify worker evidence against disk truth before a gate.
---

# Independent Evidence Verification

Verify claims against disk truth before any gate; never trust a REPORT.

Refs: probe-reruns-and-interface-deltas, unreachable-gate-asserted-control, packet-path-drift-and-relaunch, monitor-succession-and-lane-terminality, live-writer-and-payload-flaps, wave-dispatch-guards-and-session-identity, iteration-budget-exhaustion-and-finish-packets, model-route-receipt-and-usage-ledger, launch-path-foreign-worktrees-and-red-gate-triage, content-comparison-alignment-and-offset-probes, cross-lane-red-gates-and-unpushed-remote-refs, output-truncation-and-allowlist-grants, ledger-reconciliation-and-honest-fail-terminals, authority-doc-edits-and-proposed-only-loads, structured-terminal-recheck.

## Two verification rules

Self-pass check: `references/self-pass-product-scope-and-pixel-truth.md`.

**Aggregate strings are vocabulary, not verdicts.** When a summary word disagrees with per-row results, report both — never convert `UNMEASURED` into PASS or FAIL.

**Your packet makes claims about itself — machine-check them.** Run one final-gate script before
delivery and **re-run it after every edit to a deliverable**: documents exist and are not stubs;
freezes re-hash clean; a submitted packet's ledger prefix is unchanged; per tree `HEAD == expected`,
parent reachable, `branch -r --contains HEAD` empty; no self-approval token anywhere; state-claiming
docs name `NOT_APPROVED`/`NOT_CLOSED` or `QUALITY_ACCEPTED = 0`; the evaluation doc still carries its
`UNMEASURED` and `NOT_VISUALLY_APPROVED` rows; no markdown table row corrupted (`"\n||" not in text`).
This gate caught two real defects in the author's own documents in one run. Inventory, the
aggregate-string case study and cost-accounting rules: `references/evaluator-output-integrity.md`;
copyable script: `templates/final-gate-skeleton.py`.

> Worked example: `references/dv3-r2-t01-correction.md` — full transcript (false frame event, prose-vs-file wording, unread required reading, resume lineage, stale watchdog).
> Companion case: `references/dv3-r2-t02-partial-progress-resume.md` — connection death WITH landed artifacts: resume-to-finish on the same session, don't pivot/split (pivot is only for zero-artifact reading-phase deaths).
> Multi-lane waves: `references/multi-lane-wave-forensics.md` — N lanes killed by bursty transport: per-lane damage measurement, session-identity proof, exit-0-vs-stub-log, concurrency cut, freeze boundary; plus the **silent kill** (no log/receipt/notice, `ended_at=null` → stall check), and "finish, do not re-run" recovery for a lane that produced everything then died.
> Evaluator output integrity: `references/evaluator-output-integrity.md` — reading an evaluator's **aggregate verdict string** when it contradicts its own row map (a harness stamped `TECHNICAL_FAIL` on a run with 0 failed rows, because `UNMEASURED ∉ {PASS, NOT_APPLICABLE}`), an inventory of **honesty invariants to machine-check in your own final gate** (absence of self-approval tokens, presence of the required `UNMEASURED` / `NOT_*` claims, table integrity, per-tree HEAD/parent/not-pushed), and cost accounting that survives review.
> Artifact claims: `references/artifact-path-and-digest-verification.md` — locate a reported artifact by name glob + hash (a single path guess gives false MISSING; a nested run-root is a reporting defect), unreproducible digests, a stale "you wrote nothing" footprint statement, Windows temp-path traps in the verify commands themselves, and a **defect-shape checklist** for executing a crashed round's never-run code (swapped args, wrong-module import in a bare `except`, green-by-fallback filter, structurally-zero measure).

## 1. Pixel-diff event proof before any visual verdict

- A claimed frame event (e.g. state change at frame N) must be proven with byte/pixel diffs you run: extract the frames with ffmpeg, compute mean abs diff + pct-changed in the claimed ROI.
- Byte-identical neighbors (diff mean 0.0) = no event, regardless of what the report says. A step only at the true boundary confirms the corrected claim.
- White-pixel share or equivalent invariant measured identically across the claimed transition exposes static details misread as change.

## 2. Channel-order-aware mask measurement

- Overlays drawn in one channel order (e.g. RED (255,0,0) in BGR code) appear in another (BLUE in RGB pixels). Measure the correct channel or the mask reads 0% and you will false-pass or false-fail.
- Always check per-channel deltas (dR/dG/dB max + pct) before concluding a mask is empty or full.

## 3. Vision prose is not file truth

- Vision models can quote words (e.g. "standing") that exist only in prior vision prose, never in any file. Before opening a correction: `grep -rni` the exact string across evidence + new files, and re-prompt vision to quote every visible string in the image.
- If grep finds zero file hits, the defect is in your earlier prose, not the worker's files — record it as your own correction, not a worker finding.

## 4. Resume-lineage adoption

- A `hermes --resume` that mints a NEW session instead of continuing the owner is an ownership event, not a failure: adopt the lineage, record both IDs in the registry, and confirm single active writer (prior session terminal `agent_close`, no concurrent edits).

## 5. Stale-watchdog clearing

- A watchdog firing on an already-processed REPORT is STALE: compare REPORT mtime against the correction prompt, log STALE + clear in the command ledger, do not re-verify blindly.

## 6. Vision-blindness fallback and stub-file traps

- When the vision tool returns "[image omitted]" or refuses local files, do NOT stall the gate: split composite sheets into per-panel full-frames yourself (e.g. PIL crop of each 320x180 cell resized to frame size), then measure pixels directly — per-channel deltas, changed-mask bbox, outside/inside-mask mean diff. Pixel math plus render-code reading replaces the missing eye.
- Read the sheet-render code before measuring overlays: cells may be BGR→RGB pre-flipped (`src[:, :, ::-1]`) before a BGR-named color is applied, so RED-in-code appears BLUE-in-pixels and a naive red-channel read returns ~0%. Confirm channel mapping from code first, then measure the true channel.
- Verify a worker's RULES_LOADED bytes against the canonical file size, not mere presence: a nested stub with the same filename (e.g. 1873B/37-line stub vs 24345B/277-line canonical) makes the mandate line formally present but substantively void. Record stub-citation as a doc defect, verify substance independently, and require the canonical read on correction.

> Further worked example: `references/dv3-r2-t03-zero-artifact-deaths.md` — four consecutive zero-artifact worker deaths on one pose-composition task (R1/R2/R3/R4), five-session resume lineage, watchdog timeouts W4/W5/W6.

## 7. Zero-artifact early-death loop

- Signature: worker session ends `agent_close` with a trivially short last assistant message (<100 chars, e.g. "Continuing —", "TARGET checklist", "Baseline complete — moving to implementation."), message count well below a working session (65–150 vs 150+), BOTH allowlisted new files still absent, owned runtime dirs empty, dispatch log holding only the wrapper EXIT line. That is an infrastructure/connection death during preflight reading, not a verdict on the task — never gate on it.
- Before every resume in the loop, re-run the cheap guards yourself (frozen write-set manifest VERIFY, MAIN DB hash, lane HEAD + dirty count, S12 clean, T01/T02 consume-only hashes). They cost seconds and prove the dead worker wrote nothing.
- Resume the SAME owner session with the SAME prompt and SAME model per Rules §7 (5-minute wait for connection errors); when the runtime mints a NEW session instead, adopt the multi-hop lineage (record every ID: R1→R2→R3→R4→R5) and confirm single active writer (all priors terminal `agent_close`, no concurrent edits).
- After TWO consecutive zero-artifact deaths on the same task, the full packet is the likely killer (this session: 5KB prompt + ~15 required-reading docs incl. 25KB PLAN + 11KB REVIEW + frozen contract + caller + PM decision). Shrink the resume payload: send a micro-prompt that assumes the prior session's context (name the 2 missing files + 5 must-run tests + env block only) instead of re-sending the full required-reading list. If the third attempt also dies in reading, split the task (scaffold + tests first, evidence/REPORT second) rather than burning a fourth full-packet attempt.

## 8. Write-set guard FAILED needs byte attribution, not a label

- A guard `verify` returning FAILED (e.g. `protected_file_changed` on 3 files) is evidence of byte change, not a verdict. Never call it a "manifest false-positive" from `git status` alone — attribute with bytes: direction (growth vs shrink), allowlist membership, tracked-vs-untracked state, and protected-file scope.
- Growth on allowlisted files is expected work (observed T04: `pilot_preview_jobs.py` 776→1000 lines / 32KB→42KB plus schemas/routes growth — the packet authorizes bounded patches exactly there). Confirm all four before proceeding: (1) changed files ⊆ task allowlist, (2) bytes/lines GREW (shrink >10% or lost definitions = red, freeze writer), (3) no protected/frozen file drifted, (4) `git diff --stat` on tracked files shows only pre-existing dirt. Then record "expected allowlisted growth" in the verdict — the pre-worker manifest is stale by design, not wrong.
- Untracked (`??`) files firing `protected_file_changed` means the manifest captured them pre-worker and bytes changed after capture. Check WHEN via mtimes vs dispatch time: a change landing during the worker's run on an allowlisted path is the worker's edit to verify (re-run its tests + ruff + size check), not a manifest bug.
- CRLF/EOL can explain small hash drift on Windows (`core.autocrlf=true`): LF-normalize before declaring drift. Only after byte attribution may the gate proceed; record the attribution (file, before→after bytes/lines, direction, allowlist clause) so the reviewer doesn't misread it as a gate red.
- **The MANAGER can compose the wrong manifest: a live task's write-set is not the protected set.** Observed 2026-09-22: the pre-dispatch protected baseline listed the lane's own modules under edit (`adapter.py`, `lease.py`, `gpugate.py`, `contract.py`, `errors.py`, `__init__.py`, `tests/fake_transport.py`), so the first post-worker verify returned **FAILED 7/7 `protected_file_changed`** — on exactly the files the authorised lane was patching, with before/after hashes showing **growth** (adapter 442→700 lines, lease 208→442, gpugate 140→263; nothing shrank). That is a manifest-composition defect, not drift. Fix: keep the two sets **disjoint** — protected-only manifest = baseline **minus** the task's exclusive write-set — write the reclassification into the corrected manifest itself (`moved_to_task_write_set`, count, reason) so a reviewer sees what moved and why, re-verify against it (**VERIFIED, 0 failures**), and guard the task's own files with the separate write-set preimage + byte snapshots. Never hand-explain the 7 away: a protected manifest overlapping a live write-set re-fires on every later verify and trains you to ignore the guard.
- **Mass guard FAILED after a sanctioned ff-merge = reconcile, don't alarm.** When manifests were pinned at older per-lane baselines and the lane then ff-merges to the shared wave base, every file the merge itself rewrote fires `protected_file_changed` (and `guarded_file_missing` for paths relocated by design). Procedure: (1) byte-compare each flagged path against the wave-base worktree at the frozen SHA — identical bytes = merge effect, not a violation; (2) for a small residual byte delta with clean trees, run the decisive pair — `git rev-parse HEAD:<path>` blob hash must match on both sides AND `tr -d '\r' | sha256sum` LF-normalized hash must match AND the CR-count delta equals the byte delta (= EOL checkout artifact, not worker bytes); (3) re-baseline (capture post-merge manifests) for the next phase and keep both manifests + the proof JSON in the lane evidence. Allow-set verify with `--allow-change` per lane path stays valid across the merge. (S12-R6 2026-09-15: QA 10/18 flagged → 10/10 merge-explained incl. 2 relocated tests; RETRY `models.py` 64-byte delta → blob `dc71157f…` + LF-normalized `ecd68a37…` identical both sides → EOL only.)

## 9. Sibling-lane `$TEMP` hijack fakes a red suite (verified 2026-09-09, S12-C1 W4)

- Another lane's env snapshot can overwrite shell `$TEMP`/`$TMP` to its own scratch dir (later cleaned). Every pytest using `tmp_path`/default `--basetemp` then dies with `FileNotFoundError: [WinError 3]` in `pathlib.mkdir` — e.g. 18 errors + 1 passed, looking exactly like a code defect.
- Before running ANY gate on a shared machine: `echo $TEMP` / `echo $TMP`. If it points outside the OS temp, re-run with an explicit Windows-native `--basetemp=C:/Users/...` BEFORE diagnosing code. Only a red on the clean re-run is a real finding.

## 10. Vacuous-pass checks & frozen-ID mapping divergence (integrated candidates)

- **Re-run freeze/mapping/consistency checks on the MERGED candidate, not only per-lane.** A check body like `target = REPO / module; if target.is_file(): assert node in module_nodes(target)` skips silently while the artifact is absent (pre-merge lane worktree) and only becomes meaningful after integration — so it "passes" vacuously and fires exactly once, on the frozen combined candidate. Audit for the `if artifact.is_file()` pattern whenever a check passed pre-integration while the artifact did not yet exist. (S12-R6 2026-09-15: Manager finite acceptance on the frozen tip → 101 passed / 1 failed; the single failure was this class while every mechanism suite was green.)
- **Divergence between two parallel pre-review freezes → fix the MAPPING, keep executable bytes.** When a coordinator freeze (e.g. QA inventory with draft node IDs) and owner freezes (IDs inside already-verified commits) disagree, the owner-frozen executable IDs are canonical when the authority text says "test IDs must be frozen by owners". Route the correction to the mapping side (freeze doc + harness expectations), never a rename of verified bytes — renaming N passing tests forces N re-verifications + re-transport for zero functional gain. Making a vacuous check meaningful ≠ weakening it: keep `artifact present ⇒ mapped node must exist`.
- **Quantify before concluding "naming-only":** classify expected-vs-actual (exact / fuzzy-equivalent / manual); then confirm EVERY unmapped case has an executing test under some owner name (spot-check each) and ship the full mapping table + finding md in the review packet so the reviewer can re-route if they disagree.
- **Queue owner corrections to AFTER the owner's current turn exits** — never interrupt a mid-turn writer or create a second writer on the same worktree to land a mapping fix.
- Worked example: `references/s12-r6-vacuous-freeze-check-and-id-mapping.md`.

## 11. Pre-existing vs introduced: baseline-proof every broad-gate failure

- A final broad gate ending `N failed` is not a verdict until each failure is attributed. Classify by SHAPE first: (a) env-gated checks (assert on env vars only set inside a specific audit context — e.g. `S12_R5_CANDIDATE_ROOT` — fail by design anywhere else), (b) stale-expectation tests (hard-coded revision/name the repo moved past — e.g. `NEW_REV="c3d4e5f6a7b8"` while the sole alembic head is `d4e5f6a7b8c9` from an earlier round), (c) candidate-introduced regressions.
- Decisive proof for "pre-existing": frozen `git archive <BASE_SHA> | tar -x` copy, re-run ONLY the failing tests there with the identical command. Identical failures/exit on the base = pre-existing; ship the raw baseline log into the packet (`baseline-*.txt`). (S12-R6: same 5 failed/2 passed on base `83af516` as on the tip → **0 candidate-introduced**.)
- Corroborate with the delta first: `git diff --name-only base tip` containing none of the failing surfaces (no migrations/**, none of the failing test dirs) is strong evidence BEFORE spending the baseline run.
- Never drop, skip, or threshold-tune failures to green — ship counts + classification + baseline raw so the reviewer can re-run the same proof.
- A **by-design failing node** (a node that deliberately re-raises a recorded BLOCKED product state) is not a red micro to silence: exclude that ONE file from the broad gate (`--ignore=...`), keep the exclusion explicit in the gate command raw, and report the state through the blocker finding it re-raises.

## 12. Re-run adversarial reviewer probes on the frozen candidate (frozen-copy recipe)

- The strongest mechanism evidence short of re-review: re-run the reviewer's OWN counterexample probes, unmodified, on the merged candidate.
- Recipe: `git archive <TIP_SHA> | tar -x -C <runtime>/frozen-src` → copy each probe file INTO the test dir of the base module it imports (probes commonly do `import test_<x> as base`) → run with `PYTHONPATH=<frozen-src>` from the frozen root, output dir FRESH per run (probe writers use exclusive creation `open(...,'x')` — a non-empty dir fails) → save raw + probe-written JSONs into the packet.
- Prove the FLIP old→new by diffing the pre-fix failure JSON against the new run and quoting exact deltas (S12-R6: old duplicate-Job creation `Jobs 2→3` vs new typed 409 `S12_EXPORT_JOB_IDENTITY_CONTRADICTION` with counts `2/2→2/2`; stale owner old "created final" vs new "fence lost before rename" + current owner completes). Numbers in the packet, not adjectives.
- The frozen-copy run dirties no worktree and needs no merges — do it before asking anyone to hand-verify.
- Worked example: `references/s12-r6-final-gates-baseline-and-probe-reruns.md`.

## 13. Manager-side independent verifier on frozen bytes (verified 2026-09-16)

When you re-run the workers' decisive gates yourself, build ONE verifier script per lane that executes the whole gate order in a single isolated runtime, and keep every attempt — including your own failed harness attempts.

- **Provenance beats location.** Copy the reviewer's probe from the REVIEW ROOT, never from the worker's copy of it, and assert the copy's sha256 equals the review-root sha256 BEFORE and AFTER the run. A probe the worker could have edited is not independent evidence; a probe copied from the worker's tree only proves the worker agrees with itself.
- **Reproduce the reviewer-equivalent import surface.** Probes commonly do `import test_<x> as base`. Running the copied probe from an out-of-tree verifier dir without that base module importable exits **4** with `found no collectors` / `ModuleNotFoundError` — a harness defect, not a product finding. Either place the probe in the base module's test dir, or set `PYTHONPATH=<base module test dir>:<lane tests>:<worktree>`.
- **`py_compile` only the changed `.py` files.** Feeding a changed Markdown contract doc to it yields `SyntaxError: invalid character '—' (U+2014)` and a spurious non-zero exit; scope the call or the gate misreports a red.
- **Isolate the runtime.** Clear inherited `<PROJECT>_*`/lane env vars before import, point `TMP`/`TEMP`/`--basetemp` at a private runtime root, and use a FRESH exclusive output dir per run (probe writers use `open(...,'x')` and fail on a non-empty dir).
- **Record harness defects next to the corrected re-run** (same run dir: an explicit `*.HARNESS_NOTE.txt` plus a `*_corrected.*` pair) and never delete the failed attempt — otherwise the reviewer sees an unexplained gap in the ledger. State in the note that the probe/test file itself was never modified, with its hash before/after.
- **Re-hash every value a worker reports.** Worker-claimed manifest/inventory/probe sha256 prefixes, byte and line counts are self-reports; recompute them from disk and record `MATCH`/`DIFF` per item BEFORE freezing anything on them.
- **Prefer the pre-emptive re-baseline after a sanctioned ff-sync.** Prove conflict-freedom first — `git merge-base --is-ancestor <lane_head> <wave_base>` true ⇒ the sync is a pure fast-forward, so no merge and no conflict resolution is possible — then ff, then capture a FRESH post-sync guard manifest and verify post-writer against THAT. The pre-sync manifest is stale-by-design for every protected file the sync legitimately rewrote. This is the preventive form of §8's mass-`FAILED` reconciliation.
- **Untracked-dir integrity needs three separate counts.** Compare the snapshot file set byte-for-byte and report `identical` / `modified` / `deleted` separately from new additions: test runs legitimately create new (often empty) dirs, so a bare `diff -rq` "Only in worktree" list is noise, while a single `modified` or `deleted` original IS the violation.
- **Report the executed-node total as a measured number.** With a frozen inventory you can state "N node instances re-run, 0 failures, 0 new skips, 0 weakened assertions" as fact rather than an assurance. Also record which gate you deliberately did NOT run and whose license covers it (e.g. broad/global gate = the integration owner's, under one mutex) so the omission reads as scope discipline, not as a gap.

## 14. In-wave contract changes: superseded expectations, probe mappings, tip hygiene (verified 2026-09-16, S12-R7)

- **A red whose assertion CONTRADICTS a sibling lane's freshly-frozen contract is a superseded expectation, not a regression.** Signature: green on the owner lane at owner tip; red on the combined tip; the failure message quotes the new typed contract reason (e.g. `OCCURRENCE_GEOMETRY_BOX_MISSING … no boxed segmentation/prompt evidence` — the deny the frozen semantics now require, while the old test pinned `executable is True`). Triage from raw output first; never assign blame from the node name.
- Handling is write-set-bounded: IN the owner's set → one bounded owner turn (fixture satisfies the new prerequisites, keep the positive control meaningful, ADD a negative node asserting the new typed denial, one fresh transport round). OUT of every set → file the exact minimal proposal (file, asserts, proposed owner, precedent) and request a bounded exception; never edit silently, never leave unlabelled. Never loosen or skip to green.
- **A probe failing by-design at a NEW gate is an interface-change mapping.** When an immutable reviewer probe replays pre-change inputs and the changed code correctly refuses them (e.g. pre-timeline authority → typed `LEGACY_AUTHORITY_REAPPROVAL_REQUIRED` refusal), record: probe file + sha, verbatim typed error, and the mapping to the NEW coverage nodes that re-verify the probe's semantic intent (co-occurrence/repeated-role planner nodes + the legacy-gate node). "Retain assertions + explicit mapping" is the sanctioned path — never silently adapt the probe.
- **Wrong-length sha literals (e.g. 41 hex in prompt AND handoff): resolve against branch tip before merge** (`git rev-parse <branch>`, parent, diffstat match) and record both forms in the transport report.
- **Env-gated audit nodes: run with exact env as a separate raw, refreshed per tip.** A broad gate without the audit env shows a false red on that node (ship the broad raw AND a dedicated env'd run: root = candidate worktree, SHA = frozen tip); re-read the tip SHA whenever it moves.

## 15. Accept a worker's correction of YOUR packet — after byte-verifying its work (verified 2026-09-17)

A worker that contradicts your packet may be right, and a worker that claims a
capability is impossible may be telling the truth. Both look like "the worker
didn't do the task" if you triage from the report text instead of from bytes.

- **When a worker resolves an ambiguity in your own packet, verify the proof and ADOPT its reading.** This session's packet said "book scene frames 450–569"; the worker tested that literally in film space, found no match, then proved the numbering belonged to a *different index space* (demo) and mapped it to film frames 1650–1769 — evidenced by an offset sweep over 900 frames (MAE 0.1536 at the correct offset vs 0.445 at ±1 and 39.2 at ±300). That is a packet defect corrected by evidence. Record the adoption, tell the continuation "already accepted — do not re-open or re-derive", and correct the packet text so the next worker does not re-litigate it.
- **The same worker can also disqualify a "reference" artifact you supplied.** The same lane found a prototype still that matched NEITHER the film NOR the demo at any offset (best MAE 8.04 ≈ no match) — i.e. it was output of a diagnostic harness, not a source frame. Accept that: a file's name/location is not provenance. Always check whether a claimed source artifact actually matches the source before it becomes ground truth for an acceptance row.
- **Byte-verify a worker's claimed intermediate artifacts before accepting OR rejecting its round.** Hash the fixture file yourself and compare to the claimed value (`sha256sum` on disk vs the reported hex — they matched here), then independently read the load-bearing claims out of it: window count/duration, holdout presence, assertion pass flags, locked-source invariants (e.g. 39,634 decoded frames; 208/224 scene candidates matching the locked profile), and the freeze hash scope. Only then is "the analysis half is genuinely done" a fact you can act on.
- **Confirm a claimed capability blocker at the interface, not just in prose.** The worker reported vision was unavailable, which conveniently excused every semantic label. Rather than accept or dismiss it, probe the SAME route directly: POST a minimal image message (a tiny base64 PNG `data:` URL) to the endpoint and read the model's own reply. It answered *"image omitted due no vision support"* — the claim was TRUE. A blocker you can reproduce at the boundary is verified; one you cannot is a finding. Never let a blocker that is `NOT_RUN`/unavailable pass silently just because it is plausible, and never reject a true one just because it is convenient for the worker.
- **Consequence for acceptance criteria that require human judgement:** if the route is text-only, no worker in the wave can produce semantic visual approval. Say so explicitly, keep the evidence structural/numeric, require the harness's `human NOT_REVIEWED` marker, and surface to the user that a human is the reviewer for the visual gate — do not let structural metrics quietly stand in for "looked at it".
- **Honest intermediate work is not a delivery.** The same round scored ~195 real files in its runtime dir while its evidence root held 0 files and the worktree was clean. Credit the work (so the continuation does not redo it) while still holding the task at not-delivered until the artifact paths exist. Both statements are true at once.

> Worked example: `references/mf-v1-golden-iteration-cap-and-acceptance.md` — the full chain: iteration-cap termination read out of state.db, byte-verified intermediate artifacts, the frame-space adoption, the vision-blocker boundary probe, and the narrow continuation packet that shipped only the remainder.

## 16. Claims about shared/user-owned resources: prove NON-mutation, then prove RELEASE (verified 2026-09-17)

When a worker is authorized to touch an EXTERNAL resource read-only (the user's own
install, a shared model store, another tool's runtime), its "I only read it" claim
needs a positive non-mutation proof, not an assurance. Same for resources it starts
but must not leave running.

- **Non-mutation proof over an external tree — four measured checks**, all cheap:
  (1) `git rev-parse HEAD` in that tree unchanged; (2) `git status --porcelain` shows
  only entries you can positively attribute; (3) the decisive one —
  `find <tree> -type f -newermt "-3 hours" -not -path "*/.git/*"` returns **0**;
  (4) any subtree the worker could have written (`find <tree>/models -type f -newermt …`)
  returns **0**. Report counts, never an adjective.
- **`.git/index` mtime moves on a benign `git status`** (stat-refresh). It WILL appear
  in the `-newermt` sweep and is not mutation — exclude it and say so explicitly,
  rather than leaving the reader to guess why it moved.
- **Date pre-existing dirty entries by MTIME, not by name.** Captured `??` files
  (`my_workflows/`, `run_comfyui.bat`) look worker-created; their mtimes were months
  before the dispatch. Check the clock before crediting or blaming the lane.
- **"Pinned" is a per-hash claim — enumerate WHICH fields are populated.** A registry
  row filling `workflow_sha256` + `node_inventory_sha256` while `model_hashes = null`
  and `checkpoint_sha256 = None` sails past a naive "does it have hashes?" glance — and
  the missing one is exactly the component a downstream cache key depends on. Read the
  individual fields; where the artifact is identifiable on disk, hash it yourself so the
  follow-up packet can state the expected value. The worker then recomputes it
  independently, and the two matching is the actual verification.
- **Re-run the worker's suite with the worker's OWN environment.** When the lane built a
  task-local venv, `<runtime>/venv/Scripts/python.exe -m pytest <its tests> -q --no-header
  -p no:cacheprovider` reproduces the claim end to end; a claimed count reappearing
  verbatim is verified, one that does not is a finding. Run long suites via
  `background=true` — foreground terminal calls are capped well below a slow suite's
  runtime.
- **A worker that starts a server may leave it running after it exits.** Post-exit, probe
  for orphans: the health endpoint (`curl -s -m 4 <endpoint>`) plus
  `nvidia-smi --query-gpu=memory.used --format=csv,noheader`. The tell is held memory at
  **0 % utilisation** with no worker alive — on a single-GPU machine that silently blocks
  the next lane, so it is a real defect with a real cost, not housekeeping. Require
  shutdown with before/after readings (observed: 7,458 MiB → 628 MiB).
- **Never `killall`/`pkill python` to clean up** — the orchestrating agent itself runs on
  Python. Only the exact PID tree the lane owns.

> Worked example: `references/mf-v1-comfy-readonly-release-and-pins.md` — the full COMFY
> lane verification: read-only proof over the user's own 71 GB ComfyUI install, the two
> Manager-reproduced defects (unpinned model hash, orphaned GPU server), the
> independently re-run 68-test suite, and the bounded continuation that closed both.

## 17. A claim that something did NOT happen needs a method that cannot count error text (verified 2026-09-17)

The Manager reported `pushed=1` for a lane, then had to retract it one turn later. The
command was:

```
git log origin/<branch> --oneline -1 2>&1 | grep -c mf-reskin      →  "1"
```

On a branch with no upstream, git writes
`fatal: ambiguous argument 'origin/<branch>': unknown revision or path not in the working tree`
to the **merged** stream — and that error text contains the branch name, so `grep -c`
counted the error as a hit. Both the non-zero exit and the count looked like evidence.

- **Rule:** verifying a negative side-effect claim (no push, no merge, no delete, no
  publish/upload) must use a method whose false-positive mode is not the error path.
  For "not pushed", use these — none of them can be satisfied by an error string:
  1. `git rev-parse --abbrev-ref --symbolic-full-name @{u}` → `fatal: no upstream
     configured`. Here the *fatal text is the desired finding*: read it as text and treat
     non-zero as "no upstream", never as a failure of the check.
  2. `git for-each-ref refs/remotes/ | grep -c <pattern>` → **0**.
  3. `git ls-remote --heads origin | grep -c <pattern>` → **0** — the remote answering
     itself, the only form that is genuinely about the remote rather than local refs.
  4. `git branch -r --contains <sha>` → **empty**. Per-commit, cheap, and quiet about
     *sibling* lanes' legitimately-unpushed commits — unlike the
     `git log --branches --not --remotes` form §22 warns against.
  5. `git rev-parse --abbrev-ref --symbolic-full-name @{u}` returning
     `fatal: no upstream configured for branch '<name>'` is the desired finding (method 1),
     read as text, not as a failed check.
- **Never `2>&1` on a command whose STDOUT you intend to count.** Keep the streams
  separate, and prefer asserting on the *absence of a ref* over a grep count of a
  combined stream.
- Generalise: "nothing was deleted", "no foreign commit merged", "no upload happened" are
  the same shape. An enumeration that must come back **EMPTY** beats a count.
- **Retract your own bad number explicitly.** State the wrong value, the method defect and
  the corrected measurement in the next report. Cheaper than the reviewer finding it, and
  it keeps the lane's evidence chain trustworthy.

## 18. Appearance/style transfer: a colour grade passes every naive metric (verified 2026-09-17)

Verifying that an engine actually CHANGED appearance while holding geometry is the inverse
of the usual problem — the failure mode scores *well* on naive similarity. Build one
adversarial control before accepting any "reskin" / "restyle" / "re-identify" claim.

- **Pre-register the acceptance gate BEFORE rendering, and hold it when it fails.** The
  lane froze its denoise-selection rule (`raw/215_denoise_choice.json`) prior to the run;
  it returned **0/4 candidates pass**, and the lane kept it at 0/4 rather than widening.
  A gate written after seeing outputs is a description, not a gate.
- **The LUT/codebook-residual control.** Fit a per-channel LUT (or palette codebook) from
  source→output and re-measure. If the fitted map reconstructs the output's high-frequency
  structure, the "transfer" is a **colour grade**, which a source-locked reskin contract
  typically forbids. Measured here: edge IoU source→output **0.388** unmapped vs **0.927**
  after the LUT, with **92.7 %** of pixels inside the frozen-mask region landing within
  ≤16/255 of the LUT prediction. That is a colour map, not an appearance change — and it
  is invisible to every plain similarity metric.
- **Expect a monotonic trade-off, and report it instead of picking a winner.** Under
  img2img denoise the two requirements moved in opposite directions:

  | denoise | structure (edge IoU, 1/8 scale) | escapes the LUT? |
  |---|---|---|
  | 0.40 | 0.805 | no (0.927) |
  | 0.52 | 0.719 | no (0.909) |
  | 0.64 | 0.612 | no (0.812) |
  | 0.76 | 0.445 | yes (0.677) |

  Geometry-preserving denoise ⇒ grade-only change; LUT-escaping denoise ⇒ structure loss.
  The correct deliverable is the **typed blocker** ("geometry holds at 0.0 px shift but the
  appearance change is palette/LUT-explainable at every tested denoise") plus the
  structural diagnosis that img2img conditioning alone cannot satisfy both — never a
  mid-range value quietly chosen so both columns look acceptable.
- **Prefer mask-INDEPENDENT geometry evidence as the headline.** Template-match best shift
  (**0.0 px** at every denoise, peak corr 0.51–0.93) stayed trustworthy while the
  mask-derived numbers did not (below) — pick the metric that survives a broken mask.
- **Decompose a low similarity score before blaming the engine.** Edge IoU rose
  monotonically at coarser comparison scale (0.427 → 0.805 at 1/8), identifying the residue
  as a *medium* difference (flat-colour source vs photographic render), not a structural
  failure. Without that decomposition "edge IoU 0.43" reads as a fail and sends the lane
  chasing a non-defect.

### Metric defects that fake a pass or a fail

- **Degenerate source frames return 1.0/None from every geometry metric.** A pure-black
  anchor (mean/std ≈ 0, a single unique colour — observed at one window's f4212 and f4227)
  scored perfect on geometry because there was nothing to measure. Detect degeneracy FIRST
  (`mean`/`std`/unique-colour-count on the **source**), mark `degenerate_source_frame`,
  exclude from gates, and report separately. Never let it count as "geometry perfectly held".
- **A derived subject mask that misses the SOURCE makes the metric meaningless.** The lane's
  own foreground derivation failed to cover the contact band *on the source itself*
  (`source_ratio = 0.0` over 3,170 px), voiding `fg_iou`/envelope for that window while still
  printing a plausible number. Fix: use the **frozen mask union** as the metric subject
  (derivation-free), keeping the derived value only as a clearly labelled secondary with its
  bias stated. An unvalidated derivation is a measurement, not a ground truth.
- **Score contact coverage against the SOURCE's own ratio, not against 1.0.** A pair at
  0.672–0.691 read as a defect until compared with the source's own **0.653** ⇒ no contact
  loss, three sibling pairs at 1.000. A metric that can fail on the input is calibrated; one
  that cannot is not.
- **Have the lane check its own measurement code against a second route.** This lane found
  both defects above by cross-examining its derivations unprompted — worth requiring in the
  packet, since a metric bug can as easily fake a PASS as a fail.

### Frozen fixtures are not re-frozen after candidates exist

When a frozen input turns out to have a coverage defect (a camera-motion window whose
anchors are degenerate), do **not** edit the fixture, the window, or a tolerance once a
candidate exists — that silently changes what "correct" means mid-comparison. Carry it as an
explicit **open coverage gap** naming the frame ids and the measurements, and hand the fix to
the next wave. Freeze discipline outranks tidiness.

> Worked example: `references/mf-v1-appearance-transfer-lut-control.md` — the full
> calibration: pre-registered 0/4 gate, the LUT-residual arithmetic, the per-denoise
> trade-off table, the two self-found metric defects, and the degenerate-anchor coverage gap.

## 19. Adjudicating a lane's OWN proposed fix: verify against the freeze anchors (verified 2026-09-17)

A well-run lane will often end a round by asking for a decision ("authorise X?",
"confirm Y?") instead of doing it unilaterally. Accept the offer — an authorised
correction is an audited one, whereas a silent deviation forces you to reconstruct
intent later. But an improved number is **not** the proof of a correct correction.

- **The proof is: target metric improved AND every freeze anchor is byte-identical.**
  Observed: an authorised fix to the reference cutouts moved the audit from
  `{"CLIPPED": 88}` / 9,058 px outside crop to `{"EXACT": 88}` / **0 px**. That
  improvement means nothing on its own. What made it verifiable was re-hashing the
  frozen inputs and finding them untouched:
  `GOLDEN_FIXTURE.json` sha256 identical to the pre-correction value, and
  `freeze_hash_sha256` unchanged. Improvement **plus** anchor drift is a re-freeze —
  it invalidates every comparison already made against the old fixture, and it is the
  failure mode to look for first, because the metric column will look great.
- **Prefer a correction that RETAINS the superseded value in the same artifact.** The
  good version of that fix kept BOTH keys side by side —
  `mask_px_outside_crop: 0` (authoritative) and
  `mask_px_outside_declared_crop: 9058` (historical). The old measurement stays
  auditable instead of vanishing, so a reviewer can see what changed and why. When you
  brief a correction, ask for the before/after pair rather than a silent overwrite.
- **When the fix needs a file the packet had implicitly frozen, authorise it as a
  bounded patch only** — patch-with-preimage on that one file, with before/after
  sha256 + line counts recorded in the ledger, while the actually-frozen artifacts
  (the fixture, the keyframes) stay byte-identical. Distinguish "the tool that
  produces the artifact may change" from "the artifact may change"; only the second is
  a freeze breach.
- **A lane that declines its own shortcut is behaving correctly.** This one refused to
  rewrite a round-1 tool file unilaterally and asked first. Reward that in the next
  packet (state what is now authorised) so the incentive stays.

### When a lane hits its tuning cap, escalate the ROUTE — do not dispatch more tuning

A lane reporting measured FAILs after its allowed adjustments is delivering a
**result**, not a defect. Distinguish three cases:

- **The lane's own gate returned 0/N and it held that verdict** → accept and report
  (§18). Do not send it back to find a passing setting.
- **Its measurement is provably wrong** (degenerate inputs, a derivation that fails on
  the source — §18) → authorise fixing the **metric**, requiring before/after numbers
  and a statement of which value is authoritative. Fixing a metric is legitimate;
  changing the acceptance **definition** is not.
- **It measured correctly and the route genuinely cannot do both things at once** →
  accept the FAILs as kept negatives (e.g. `contact=FAIL` on 3 of 4 windows alongside
  `continuity=PASS` on the same windows — which is also positive evidence the two
  negatives are independent) and escalate the **route decision** to the user/authority
  with the numbers. Never widen a tolerance, rename a metric, or drop an adversarial
  control to manufacture a pass, and never let one nice average hide a
  badly-scoring window (a `psnr_med` of 16.2 next to 36–38 elsewhere is a finding, not
  noise).

> Worked example: `references/mf-v1-continuation-rounds-and-freeze-anchors.md` — the
> authorised cutout correction (CLIPPED→EXACT, 9,058 px→0, with the superseded value kept
> in the same artifact) verified by re-asserting byte-identical fixture + freeze hashes; the
> four-window accepted-FAIL table with its bounded-memory and independent-negative evidence;
> the detached-child death and the two-point liveness sample that caught it; and the two
> independent lanes converging on the same engine blocker.

## 20. Proving a worker is ALIVE when its log stays empty (verified 2026-09-22)

Immediately after dispatching a wave you must be able to answer "is it working?" without
trusting anything the worker prints. On this machine the worker stdout redirected to a file
sat at **0 bytes for ~6 minutes while three workers were demonstrably running** (editing
files, running tools) — with `PYTHONUNBUFFERED=1` set. Log size, log tail and "no output"
are therefore **not** liveness signals in either direction.

- **Read liveness from the state store, read-only, not from the log.** For Hermes CLI workers:
  `sqlite3 'file:C:/Users/<u>/AppData/Local/hermes/state.db?mode=ro'` (the `mode=ro` URI is
  what keeps the DB untouched — Rules forbid mutating it), then per session
  `SELECT message_count, tool_call_count, ended_at, cwd FROM sessions WHERE id=?` and the last
  row of `messages` (`role`, `tool_name`) — a rising `tool_call_count` with a recent tool row
  IS the liveness proof.
- **Two traps in that table, both observed the same session.** (a) `ended_at IS NULL` does NOT
  mean alive: two sessions from the previous wave still had NULL months-of-minutes after their
  machines died. (b) `exit 0` does NOT mean done: a resumed worker exited 0 with a **52-byte**
  log whose entire content was `API call failed after 3 retries: Connection error.` — the
  receipt's exit code was clean and the deliverable was zero.
- **Positively identify each session before trusting the lineage.** Query the new session ids by
  `started_at > <dispatch time>` and match each against the first `user` message of the session
  (it is the packet text) — that is how you prove which worker a minted id belongs to instead of
  assuming. It is also how you catch an accidental duplicate dispatch or a second manager chat.
- **`--resume <id>` may mint a NEW session id** rather than continuing the owner. Treat it as an
  ownership event (§4): record `parent → actual` in the registry the moment it appears, and
  confirm the parent is terminal (`agent_close`, low message count) so only one writer exists.
- **Resumed-but-empty rounds need a scope decision, not a rerun.** A resume that exits having
  produced nothing because it died during preflight reading is not evidence about the task:
  check whether its *prior* rounds already landed bytes, and keep the continuation packet narrow
  (the remaining artifacts + exact gates) instead of re-sending the whole required-reading list —
  the packet itself is a known killer of these rounds (§7).
- **Cheap sampling monitor beats waiting on a notification.** A 60-second sampler that appends
  one JSON line per tick (per-task log bytes, receipt presence, worker process count, GPU used
  MiB, listener ports) both feeds the ≤20-minute heartbeat and gives you the "8 minutes with no
  progress" audit trigger for free. Start it right after dispatch, in the background, and let it
  exit when every receipt file exists.
- **Never `killall`/`pkill python` while cleaning up** (§16) — the orchestrator and the desktop
  app are Python. Exclude your own runtime PIDs from every process count: the two Hermes
  processes (`hermes desktop`, `hermes serve`) are not workers, and a naive `tasklist` count of
  `python.exe` looks like worker activity when it is only the harness.
- **A sampler monitor outlives its usefulness; retire it by exact PID and prove the delta.** Once
  every stem it watches has a receipt it can never report anything again. Enumerate the full
  `python.exe` PID set, stop **only** the monitor PIDs (leaf→root, one `taskkill /PID <p> /F` each,
  never `/T`), then re-enumerate and show the set difference is exactly those PIDs — observed
  `14872,29648,28788,31448` → `14872,29648`, with the two Hermes PIDs alive: 0 collateral. Do the
  same before dispatching a new wave, so a stale monitor's notifications cannot be mistaken for
  current liveness (§20's whole point).

### Harness traps that cost debugging time while writing those manager tools

- **Windows-native paths for Windows binaries.** `python /c/Users/x/tool.py` from git-bash fails
  with `can't open file 'C:\c\Users\...'` — the interpreter receives the MSYS path verbatim. Pass
  `C:/Users/...` (forward slashes are fine) into `python.exe`/`node.exe` argv; keep `/c/...` for
  shell built-ins and `cd`.
- **Backslashes inside a single-quoted bash heredoc break the parser** — `python - <<'PY' … r'C:\a\' … PY`
  gives `SyntaxError: unterminated string literal`, and `sed 's|\\|/|g'` gives
  `sed: unterminated 's' command`. Use `pathlib.Path(...).as_posix()`, `chr(92)`, or write the
  script with the file tool and run it by native path. When a heredoc script dies on quoting,
  re-issue it as a file rather than iterating on escapes.

> Worked example: `references/worker-liveness-state-db-and-wave-dispatch.md` — the state.db
> liveness query and its two traps, the empty-resume lineage (parent terminal at 13 msgs / 52-byte
> log → minted continuation adopted), the guard-before-dispatch capture + pre-dispatch re-verify,
> the 60 s sampler, and the disjoint 3-CPU-worker wave with GPU serialised behind a gate.
> Reusable runners: `scripts/worker_liveness.py` (read-only `state.db` liveness probe —
> `--recent-minutes N` or `--sessions <id…>`) and `scripts/capture_writeset.py` (protected /
> write-set manifest with SHA-256 + byte size + lines + mtime, plus byte snapshots of
> untracked/dirty bytes, run once before dispatch).

## 21. Reporting a verified result back to the user (shape + language, verified 2026-09-22)

Verification ends in a report, and a correct report in the wrong language or shape is still a
failed turn. Both halves below were user-corrected during this wave.

- **Write every reply in the user's language, entirely.** A Vietnamese prompt gets a 100 %
  Vietnamese answer — headings, table cells, status words included. No stray English or
  Chinese fragments inside a Vietnamese sentence: this session's user had to repeat
  "trả lời bằng tiếng Việt" twice, the second time mid-turn, after stray Chinese characters
  appeared in an otherwise-correct report. Once asked, the language holds for every later
  reply in that session, one-liners included.
- **Fixed shape: status → measured numbers → anchored ETA → slippage risks.** Status line
  first; then a table of REAL values (counts, hashes, ports, bytes, seconds — never
  adjectives); then an ETA table whose dates are anchored (`22/09 11:25 +07`, not
  "trong ~20 phút"); then the honest list of what could push the ETA, by how much; then what
  was NOT done and why. When asked "bao giờ xong", lead with status + numbers instead of a
  plan, and when an estimate slips, report it in the same turn with the measured cause rather
  than silently re-forecasting.
- **Never let metadata stand in for a missing deliverable.** A report that says "31 files, 305
  commands, 10/10 controls" while the actual thing under test still fails must say that the
  thing FAILS, in the first sentence. Report kept FAILs as the headline result (§22).
- **Return the packet in chat; do not self-approve.** Hand the review packet back in the reply
  and let the user transport it to the independent reviewer — never send `APPROVED`/`CLOSED`
  or open the next sprint on your own authority.

## 22. Re-run the worker's own decisive command, then explain every byte that changed (verified 2026-09-22)

The strongest cheap verification of a finished lane: run the EXACT command the worker told
the reviewer to run, from the lane's own worktree, and hash the whole evidence tree before
and after your run. "Reproducible" then stops being an adjective and becomes three numbers.

- **Run the advertised reviewer command verbatim.** The lane's report named
  `run_dryrun.py --steps golden,extract,propagate,stills,negatives,sheets,report`; running it
  in the lane worktree gave **exit 0, 17.7 s, 305 commands** against the report's own 17.5 s /
  305. Redirect the raw into the guard dir, not into chat.
- **Hash the evidence tree before and after, and classify every delta.** 31 files:
  **30 byte-identical**, exactly **1 changed** = `raw/cmd_transcript.jsonl` — the command
  ledger, which the re-run itself appends to. "One file differs and here is why that one is
  *supposed* to differ" is a far stronger statement than "re-ran, looked fine"; a bare
  non-identical count would have been misread as non-reproducibility. A differing
  *load-bearing* artifact (report, metrics JSON, media) is the red, not a footnote.
- **Consume the negative controls, not the pass count.** The run printed one line per
  assertion with its control (`frame_count_exact←TAIL_TRUNCATE`, `pts_contract←DROP_RANGE`,
  `not_source_copy←SOURCE_COPY`, `cut_timeline←SHIFT_3`, …) — **10/10 `proved=True`**. An
  assertion with no proven-failing control is not evidence, so this row is the deliverable.
- **Credit kept FAILs as the result.** The same run scored **7/7 incumbent clips
  `TECHNICAL_FAIL`** and kept them: `not_source_copy` 6/7 at mae 0.86–1.43 (reconstruction, not
  a reskin), `cut_timeline` `[18,21,26,82,88,90]` vs source `[21,88]`, `frame_pairing` offset
  5. A harness that fails the artifacts it was pointed at is doing its job; do not ask for a
  re-run to make them green.
- **Transport-check a finished lane with three cheap git reads** — `git log --oneline -3`,
  `git rev-parse HEAD^` must equal the declared wave base, `git status --porcelain` empty —
  then use the §17 method for "not pushed". Do **not** substitute
  `git log --branches --not --remotes --oneline` for that: it enumerates *every* local-only
  commit in the repo (this wave it also listed two sibling lanes' commits), so it neither
  proves your lane is unpushed nor stays quiet when another lane legitimately is. Label it
  what it is — "commits not reachable from any remote-tracking ref" — or drop it.
- **Do not `du -sh` / `find` a multi-tens-of-GB model tree inside a foreground call.** The
  same wave's downloads made a `du -sh` over the model dir hang past the 180 s tool timeout.
  Measure big trees with `df -h` deltas between two known points, or `ls -la` the one subdir
  you actually care about; reserve the full walk for a background job with its raw kept.

> Worked example: `references/mf-v1-wave1-verify-guard-reclass-and-rerun.md` — the manager-side
> guard reclassification (7 false `protected_file_changed` → corrected manifest VERIFIED 0),
> the independent BENCH dry-run re-run with its 30/31 byte-identical evidence proof, the 10
> negative controls, and the download/disk accounting from the same wave.

## 23. A round that ends at the tool-call cap: verify the claim, snapshot the uncommitted bytes, order the continuation (verified 2026-09-22)

A cap-ended round is the most dangerous shape to triage, because it is simultaneously
**partly delivered** (real code, real gates) and **entirely ungated** (no report, no commit,
sometimes test code that has never executed). Exit 0 tells you nothing (§20). Do not call it
a success, do not call it a death, and never re-dispatch a fresh full packet.

- **Separate "the claim is verified" from "the task is delivered".** The lane reported
  `RUNNING` and enumerated its own missing evidence set, which is the honest shape to reward.
  Re-run its decisive suite yourself before crediting anything: `python -m pytest tests/ -q
  -p no:cacheprovider` in the lane worktree returned **114 passed, 10 skipped in 4.19 s** (the
  10th skip is the real-server case while the engine is down). Credit the verified half
  explicitly in the continuation ("accepted — do not redo", §15) and hold the task at
  not-delivered until the artifact paths exist.
- **Snapshot the dirty worktree BEFORE resuming the same owner.** A cap-ended lane usually has
  no commit at all, so its bytes exist only on disk. Walk `git status --porcelain` covering
  **both** `M` and `??` entries, copy each into a manager-owned snapshot dir, re-hash the
  copies and assert equality before dispatch (observed: 9 files — 8 modified plus one
  untracked test — **9/9 hash-match**). The untracked file is the highest-risk byte, because it
  exists nowhere else. Say in the continuation that the snapshot is recovery evidence and
  **not** a substitute for the lane's own commit.
- **Find the un-executed bytes and make running them the FIRST task.** The lane disclosed that
  its final edit — a new real-server test — "was written but NEVER RUN; the server is already
  stopped". That one sentence reorders the whole continuation: start the engine → run the
  never-executed test → only then write reports. A test that has never executed is not
  coverage, and a lane that says so unprompted has earned the benefit of the doubt on the rest
  of its claims.
- **Give the continuation a fixed four-part order so a second cap cannot strand the work:**
  (A) start the engine + run the unrun test + append the exact pytest command and raw output;
  (B) write the missing evidence set (report, state×outcome matrix with every row dispositioned,
  before/after hash table, handoff for the downstream lane); (C) commit locally on the task
  branch with the parent intact; (D) stop the server and prove it — port closed, VRAM back to
  baseline, listener list empty, and **no collateral `python.exe`** (§16). Reports before commit
  before shutdown, so an early stop still happens with the work captured.
- **The documented cap is not the real budget — measure it.** Packets assumed ~90 tool calls;
  the two lane sessions in this wave recorded `tool_call_count` **110 and 122** before
  stopping. Derive the continuation size from the observed count (§20), plan two to three
  narrow rounds per task instead of one, and expect the cap to land mid-gate — which is exactly
  why the evidence-then-commit order above is not optional.
- **After a round that drove an external server, check for orphaned server-side state.** The
  aborted gate run left a genuinely running prompt plus one unresolved marker on disk; the lane
  recovered *through its own new mechanism* (a recovery tool that waited for terminal history,
  reconciled to `completed`, recorded `release_count 1`, and preserved `orphan_recovery.json`),
  which is stronger evidence than a hand-cleanup. Require that receipt in the continuation and
  verify "server stopped, marker gone, release counted exactly once" as the row — not the lane's
  prose that it cleaned up.
- **Downloaded ≠ validated, and license gates the RUN SET, not just the file.** A lane that had
  fetched ~71 GB across 11 model files still had **no real hashes**, an incomplete pair of
  LoRAs, and for those LoRAs **no license at the pinned revision**. Rules for the continuation:
  every file needs URL + revision + license + bytes + **actual sha256 of the file on disk** (a
  file without a hash is `UNVALIDATED`, never "downloaded"); a weight whose license cannot be
  established at the pinned revision is **excluded from the run configuration** and recorded as
  `license_unclear` + `excluded_from_run` in the manifest *and* in the workflow delta — not
  deleted, not quietly used; and the run set stays the official matched
  checkpoint/quantization set, never a hand-mixed distill/LoRA/sampler combination.
- **Authorise environment changes narrowly, and demand the capability proof with them.** The
  lane needed a CUDA-enabled torch build and correctly stopped at the packet's rule about global
  CUDA/driver changes. The authorised scope was therefore: install into the **task-local venv
  only**, verify the wheel source/version first, then prove the capability with exact outputs —
  `torch.__version__`, `torch.version.cuda`, `torch.cuda.get_arch_list()` containing **sm_120**,
  `torch.cuda.is_available()` true — while still forbidding model load or inference (that is the
  next phase's gate). A permission without its proof line becomes a claim you cannot audit.

> Worked example: `references/mf-v1-cap-ended-round-continuation.md` — the COMFY cap-ended round
> (F01 verified fixed by the manager's own suite re-run while the evidence set was still
> missing), the 9-file dirty-worktree snapshot, the four-part continuation order, and the
> VIDEO14B round whose 71 GB of downloads needed hashes plus a license decision.

## 24. Verifying a round that LANDED a commit: the commit trio, the scoped linter, and the claim matrix (verified 2026-09-22)

The follow-on to §23: the continuation ran, the lane came back `TASK_SUBMITTED` with a commit and
a full evidence set. Five cheap checks decide whether that is true, and each one caught something
real in this wave.

- **Commit trio + allowlist proof, before reading any prose.** `git log --oneline -3`;
  `git rev-parse HEAD^` must equal the declared parent (here `9e57f3e…` intact — the earlier
  round's commit was not rewritten); `git status --porcelain` must be **empty**. Then
  `git show --stat --oneline HEAD` and check every path against the task's exclusive write-set:
  9 files, all under `experiments/mf_reskin_v1/comfy/**`, `+1173/−35`. A diffstat whose file list
  is *entirely* inside the allowlist IS the allowlist proof; one outsider is the finding. Then the
  §17 reads for "not pushed" (method 4 is the tidiest).
- **`git` can print `fatal:` and still have succeeded — assert the invariants, not the message.** A
  commit that had just landed also emitted `fatal: bad object refs/codex/turn-diffs/.../base` and
  `failed to perform geometric repack` from a pre-existing dangling ref. A `fatal:` line can be about
  the ref/pack git happened to touch, not about your object. Confirm with `rev-parse HEAD`,
  `rev-parse HEAD^`, `git show --stat HEAD` and an empty porcelain; if those hold, the operation
  succeeded and the noise belongs in a note, never in the verdict. (Answering "did the commit land?"
  by reading the message is the same class of error as §17's counting an error string as a hit.)
- **Scope static checks to the files in the commit, then attribute the residue by name.**
  `ruff check --select F mf_comfy/ tests/` returned **4 errors** — which read as a regression until
  it was re-run against the explicit nine paths from the diffstat: **`All checks passed!`**. Every
  residual finding lived in a file the round never touched (`file:line` each, named as outside the
  diff). Never let a package-wide count stand as the round's lint verdict, and never "fix" a
  pre-existing finding inside an unrelated round's write-set.
- **A claim matrix is verified only when every row is dispositioned AND every non-`pass` row
  carries a reason.** Observed: 40 rows = 35 `pass` / 4 `not-applicable` / **1 `fail`**, with
  `rows_undispositioned: 0` and a `counts_verified_by` field naming the recount command. Read the
  n/a rows individually — each named *why* the state is outside the component's authority
  ("authority is MotionForge; the adapter can only ever reach `validated`") or *why* it was not
  exercised this round, with the unproven path explicitly carried as an open item. An `n/a`
  without a reason is a silent skip wearing a label.
- **A self-inflicted incident belongs in the matrix as a `fail` ROW, not as a sentence in the
  report.** This lane probed a helper script with `--help`; the script has no argparse, so it ran
  and its shutdown overwrote the previous round's shutdown record. It disclosed this and recorded
  `V3 = fail` naming both damaged files and stating the old bytes are **not recoverable
  byte-exactly** — and did not fabricate replacements. Reward that shape, then verify the
  honesty claim rather than the apology: the surviving record is still identity-verified and
  complete, and no reconstructed "prior round" bytes were written.
- **Re-run the lane's own suite on the final bytes and separate its two modes.** Engine-up the
  lane reported `124 passed, 0 skips`; the manager's engine-down re-run gave `114 passed,
  10 skipped in 4.33 s`. The skips are named per node, so the engine-down figure is evidence for
  the 114 only — a skip is an unmeasured row, not a pass (§22's control rule applied to skips).
- **Read the shutdown receipt's individual fields, never its verdict string.**
  `SHUTDOWN_CONFIRMED` is a label; the evidence is `listener_pids_after: []`,
  `tree_kill_used: false`, `no_collateral_python_killed: true`, VRAM back to the idle baseline
  (~1.9 GiB of 12,227 MiB), plus your own check that the orchestrator's Hermes processes are still
  alive (§16).
- **A capability registry row is FOUR facts, not one label.** When a downstream lane must decide
  what it may run, split every previous "unavailable" row into: **missing artifact** (no weight on
  disk — name the dirs searched), **missing node** (the class is absent from the pinned build —
  name build id + class list + negative result), **measured OOM** (you loaded it and measured —
  and a row with no such run simply does not qualify; this lane's own file says "No row in this
  file qualifies"), and **vendor/stock claim** (quoted as a claim, flagged as not a local
  measurement). Distinct engines must stay distinct — a custom-editing checkpoint is not the same
  product as the T2V/I2V model whose classes you happened to find. Grant `RUNNABLE_LOCAL` only
  after actual local inference with measured resources, and `QUALITY_ACCEPTED` only after a human
  or vision-capable review; a text-only route can never award the second, and any clip/image not
  actually seen stays `NOT_VISUALLY_APPROVED`.
- **A delivered lane can still leave the wave blocked — pass its negatives forward verbatim.**
  This round closed its defect and froze a handoff, yet its report carried the load-bearing
  negatives that decide the next phase: no video engine on the machine, zero `QUALITY_ACCEPTED`,
  an unproven idempotent path, an unrepaired broken ref. Read the **handoff file**, not the chat
  summary, before authorising the downstream lane, and quote those negatives into the next packet
  rather than letting a green round imply a green wave.

- **A real-server proof can be preserved as evidence WITHOUT competing for the wave's single GPU slot.**
  When another lane owns the only heavy-GPU job (Rules: one heavy job at a time), do not let that force
  the CPU lane's real-server gate to be skipped — run it against an **isolated runtime the lane creates
  inside its own write-set**, on a private port, with the device pinned to CPU
  (`device=cpu`, `CUDA_VISIBLE_DEVICES=` empty) and a model-free workflow. Observed 2026-09-22: port
  `8301`, ComfyUI `0.28.2`, `node_class_count 807`, empty `EmptyImage → ImageScale → SaveImage` graph;
  the proof still produced every row that matters — `queue_still_running_the_prompt: true` at the timeout,
  caller-2 refused (`MF_COMFY_UNRESERVED_RESERVATION`, `unresolved_count 1`, `submit_count 0`), a real
  `/interrupt`, `release_count 1`, `unresolved_after_release []`, a second close returning the same single
  receipt, then a clean shutdown. Verify the isolation claims from bytes, not prose: the frozen baseline
  runtime's digest unchanged and **zero files under it newer than the dispatch**, the port list showing
  only the private port, and VRAM essentially unmoved (1,104 → 1,102 MiB). A CPU-side gate is real
  evidence; a skipped gate "because the GPU was busy" is a hole.
- **The five mandated test NAMES are themselves a checklist row.** When a correction packet names exact
  test ids, run `pytest … -k "<name1> or <name2> …"` and require the expected count (observed
  `5 passed, 125 deselected`) rather than trusting the lane's "all five pass" — a renamed or absent
  test also disappears from a full-suite count. Pair it with the full suite
  (`120 passed, 10 skipped`) and the scoped linter so the row has both breadth and identity.

> Worked example: `references/mf-v1-comfy-r7-delivered-commit-verification.md` — the full
> post-commit pass: commit `cc3222b` with its allowlist diffstat, the 4-error lint residue proved
> to be in untouched files, the 40-row claim matrix with its one disclosed `fail`, the
> engine-up/engine-down suite pair, the shutdown field reads, and the F06 four-way capability
> re-classification.

## 25. Verifying "the model actually ran on THIS card" from the engine's own log (verified 2026-09-22)

The phase after §24 turns a capability claim into a run. Two questions look alike and must be
answered separately: **did it run** (`RUNNABLE_LOCAL`) and **is the output good**
(`QUALITY_ACCEPTED`). Only the first is provable without vision — never let the first imply the
second, and never let a green harness stand in for a clip nobody has looked at.

- **The engine's stdout is the primary witness, even while every other channel looks quiet.** A
  ComfyUI sampling run writes tqdm frames separated by bare `\r`, so a normal `tail` shows one
  overwritten line. Read it as frames:
  `tail -c 300 <rt>/logs/server_gpu.log | tr '\r' '\n' | tail -3` →
  `70%|███████   | 14/20 [13:13<05:39, 56.53s/it]`. That single line is the difference between
  "the lane claims inference" and "a 14B model is 14/20 steps into a real sampler".
- **Prove liveness with mtime, not with the PID — and never call it stuck from a stale read.**
  `stat -c %y <log>` against `date` (observed log write 12:56:14, check 12:57 = alive), and the
  step counter advancing between two reads. A process-table entry says a process exists; only a
  moving log/counter says it is progressing. A steady rate is itself the finding: 9/20 → 14/20 at
  a constant 56.5 s/it is convergence, not a stall.
- **Corroborate with independent counters taken at the same moment.** Three together: the model
  load line naming the mechanism (`Model WAN21_Vace prepared for dynamic VRAM loading. 33068MB
  Staged`), the GPU counters (`9,176 / 12,227 MiB used, util 100 %`), and the holder's RSS (PID
  30060 at `30,357,600 K` ≈ 30 GB) — the staged weights offloading through host RAM. Any one
  alone is a guess; the three agreeing is the proof that a 33 GB model runs on a 12 GB card.
- **State "fits" as a measured ceiling with headroom, never as a yes.** Quote the peak and the
  sequencing constraint it creates: an image model that peaked at **11,590 / 12,227 MiB (94.8 %)**
  must be unloaded before any video run — a peak that high is a warning, not a pass.
- **When a candidate is REJECTED by the server, read the raw payload and check whether the error
  MOVED.** Four attempts on candidate 1: `required_input_missing` on a subgraph-internal node id
  (`672:648`, class `CreateList`, input `input0`) alongside `ComfyMathExpression` nodes — twice —
  then `prompt_outputs_failed_validation` for output 246. A changing typed error means the lane is
  converging; identical repeats mean it is guessing. Both are results: keep every attempt's
  payload and record which attempt produced which error.
- **A pre-authorised fallback only counts after IT passes the same preflight.** The replacement
  graph earned the run because its own checks were clean first (`missing_classes: []`,
  `excluded_weight_hits: []`, 15 API nodes / 14 classes). Credit it on its own evidence; never let
  the working candidate retroactively validate the failed one, or the reverse.

> Worked example: `references/mf-v1-video-model-local-inference-proof.md` — the GPU-phase
> verification: the 4-attempt candidate-1 rejection with its exact 400 payloads, the flat-template
> fallback that converted cleanly, the 14B-on-12GB offload measurements, and the progress/liveness
> reading that proves a sampler is really running.

## 26. Verifying an evaluator lane that had to BUILD its own harness (verified 2026-09-22)

An evaluator lane ("score this frozen artifact, build only small helpers") will often find that the
command it was told to re-run does not exist. That is a legitimate finding — but it is a claim until
you measure it, and the suite it then writes is itself unverified code needing the same treatment as
product code.

- **"This package has no test suite" is a claim — measure it before accepting the conclusion.** The
  lane proved it: `pytest tests -q --collect-only` collected **3,299** unrelated app tests while
  `grep -rl '<artifact names>' tests/` returned **nothing** and no `test_*.py` existed under the
  package dir. Verify that shape yourself, then accept "so I created one". Do NOT let it substitute
  the unrelated global suite for verification (§23's scope rule) — and credit the lane for saying it
  declined to run the app suite *because* that would be an out-of-write-set global gate.
- **A brand-new assertion needs its OWN capacity proof — mutate a COPY, never the real file.** After
  writing 9 hermetic tests, the lane copied the package to a scratch dir, reverted the wording the
  defect had produced, and showed exactly one test (`frame_pairing_message_is_self_consistent`)
  **FAILing on the old string** while the other 8 stayed green; the real file kept its sha256 and the
  copy was deleted. That is the non-vacuity proof for new rows — a control exercising only
  pre-existing assertions says nothing about them.
- **A lane's first test run failing may be its own test being vacuous, not the code.** Observed
  8 passed / 1 failed where the failing row was `assert not (0.0 < 0.01)` on identical inputs — an
  assertion that can never fail for the intended reason, because equal inputs give spread 0.0. The
  fix belongs in the TEST (assert on the message shape the defect produced: advantage + floor +
  spread as separate facts). A lane that reads its own failure and says "my test was wrong" earns
  credit for the rest of its claims.
- **The evaluated artifact must come out byte-identical.** Re-hash the candidate after the evaluator
  exits (`sha256sum` unchanged, same byte count — observed `ca42806b…`, 163,391 B) and require it to
  write only inside its own evidence/review dirs. An evaluator that re-encodes, re-times or "cleans"
  the artifact under test has destroyed the thing it was grading.
- **Re-run the evaluator's own suite yourself.** §22 applies to it too: the manager re-ran it and got
  the same **9 passed in ~0.6 s**, then checked the git shape — a chain of small commits on the
  frozen base (`0246968 → a2ff225`), every path inside `experiments/**`, base commit intact, none
  reachable from a remote (§17 method 4).
- **Separate measured rows from `NOT_REVIEWED` rows in the reviewer bundle.** An evaluator's
  deliverable is not a score: it is (a) the measured rows with values and dispositions, (b) the
  explicit list of rows only a human can answer, and (c) review copies — 1× and 0.5×, a side-by-side,
  contact sheets, crops — with a `REVIEWER_REQUEST.md`. Count the bundle files and sizes before
  shipping (14 artifacts, 4,892,229 B this wave) and keep every semantic row `NOT_REVIEWED` when the
  route has no vision.

### Freeze-before-evaluate sequencing (manager-side)

Do not dispatch the evaluator while the producing lane still owes the same artifact a correction: it
would score an intermediate. Order is **owner correction → byte snapshot → independent evaluation
(read-only on the frozen artifact) → packet**. This wave held the evaluator back until the producer's
audio/PTS correction landed and then scored the single frozen export; evaluating the first export and
again after the fix would have cost a full harness run and published numbers about bytes that no
longer exist.

## 27. When the lane's PROSE and its own ARTIFACT disagree, the artifact wins — and the fix is a report-only reclassification (verified 2026-09-22)

The most dangerous worker output is not a false claim; it is a **true narrative attached to a
contradicting evidence file**, because both halves look finished. Observed: a lane's final response
said `SHUTDOWN_CONFIRMED` while the artifact written in the SAME round (`SHUTDOWN.md` /
`wave2_shutdown_evidence.json`, same mtime as the report) ended with `verdict: SHUTDOWN_UNPROVEN` and
printed `COLLATERAL (removed but not in the engine chain): [21092] -> COLLATERAL DAMAGE — INCIDENT`.
Two incompatible verdicts inside one evidence set. Neither may be silently adopted.

- **Read the artifact's own verdict line, not the lane's summary of it.** Same-mtime is a hint that
  both came from one run and therefore cannot both be right — it is not proof of which is correct.
- **Separate the PHYSICAL question from the CLASSIFICATION question.** The physical end state is
  yours to measure cheaply and directly: port `connect_ex` (10061 = refused), the `netstat` listener
  set, VRAM back to idle, and the orchestrator's own processes still alive. That proved the engine was
  genuinely down, leaving only *how to classify one PID* — a much narrower question than the verdict
  string implied. Resolve them in that order; never let an unresolved classification stand in for an
  unmeasured end state, or the reverse.
- **Look inside the lane's OWN conflicting file before demanding a re-run.** The same `listeners_before`
  dump carried `127.0.0.1:64381 → 127.0.0.1:8210 ESTABLISHED 21092` — that PID was a *client of the
  engine* — and the before-dump's cmdline showed it was the lane's own stage-runner script, absent from
  the stop log's target list. The datum that resolves the contradiction is usually already in the file
  that created it.
- **Force a report-only reclassification: no new measurement, no engine start, no media byte touched.**
  The correction round may change *only* classification fields (`collateral_removed`,
  `pid_classification`, `verdict`, `previous_verdict_first_pass`, `superseded_first_pass`,
  `report_only_reclassification`) and must prove the restraint
  (`engine_started: false`, `media_bytes_changed: false`, `metrics_remeasured: false`,
  `changed_fields_only: [...]`). Re-measuring in order to fix a classification rewrites history
  instead of annotating it.
- **Keep the superseded verdict INSIDE the same file, verbatim.** The corrected `SHUTDOWN.md` ends
  `SHUTDOWN_CONFIRMED_WITH_DISCLOSED_OWN_CLIENT_EXIT` and keeps a `## SUPERSEDED first-pass verdict`
  block holding `SHUTDOWN_UNPROVEN` plus *why* it was superseded (the first pass computed collateral as
  `removed − engine_chain` with no ownership test). Never delete the old verdict, and never restate it
  in prose only — §19's retain-both-values rule applied to a verdict.
- **Upgrade a verdict only with a testable ownership proof.** Acceptable:
  `own_client_process_exited_after_engine_stop` backed by cmdline + an ESTABLISHED inbound row + the
  stop log's exact target list + the client's own `ConnectionRefused`. Not acceptable: "it must have
  been ours". When ownership cannot be proven, **keep `UNPROVEN`** and keep the incident.
- **Demand adversarial coverage of the new classifier, not a green happy path.** The lane added 15
  cases proving it cannot emit CONFIRMED when it should not (PID gone but neither own nor engine ⇒
  `UNPROVEN` + collateral listed; own-tool cmdline with no client row ⇒ `UNPROVEN`; a chain PID without
  its `taskkill rc=0` ⇒ basis false ⇒ `UNPROVEN`; port still open ⇒ `UNPROVEN`; a LISTENING row after
  stop ⇒ `UNPROVEN`). A classifier whose only test is the case it was written for is not verified.
- **Verify the correction across every place the verdict appears.** Grep the verdict token in all of
  `SHUTDOWN.md`, the evidence JSON, the classification JSON and the wave report: the new string must be
  present and the old one must appear **only** inside the superseded block. Then re-hash the media and
  re-probe the ports so the annotation demonstrably changed no measured byte.

### The reviewer correcting YOUR packet is a first-class finding

The same independent review disproved three claims the **Manager's own** packet had made: that the raw
render's PTS was "impossible" (it was already CFR 30 fps with presentation PTS `0…61440` step 512 — the
packet author had read B-frame **decode-order** packet PTS and called it a limitation), that the export
"dropped the padding" (the decoded-PNG SHA map showed output 119 ↔ raw 120, i.e. raw 119 was dropped
and the padding frame kept), and that 640×368 was the expected geometry (a stretch, not a pad).

- Adopt the review's evidence, then make the owning lane produce a **`CLAIM_CORRECTIONS.md`** naming
  each disproved claim and its replacement — a correction is an artifact, not an apology in chat.
- Route the correction to the lane whose code produced it, and put the disproof into the next packet's
  required reading so the lane cannot re-derive it.
- Mark the wrong claim as **yours** in the report (§15). A manager packet is evidence too, and an
  uncorrected one propagates the same false finding into the next wave.

### Register the acceptance rows BEFORE the fix, and keep them as rows

When dispatching a correction wave, make the lane **register each test name (or a 1:1 mapping onto an
existing test) before editing code**, and require per row: before/after code hash, raw command, exit
code, expected vs actual. Then state explicitly that **test counts are not evidence — the row is**.
That is what turns "the suite is green" into something a reviewer can re-run one row at a time, and
what stops a passing count from hiding one undispositioned row (§24's matrix rule, applied to a
correction wave).

### Freeze the WHOLE input subtree before an evaluator reads it (shared-live-root hazard)

An evaluator dispatched while the producing lane was still rewriting sibling evidence in the *same*
root flagged it itself ("9 sibling files modified during my run"), and was safe only because the
artifact under test had already been frozen and hash-verified. Do not depend on that luck:

- Order is **owner terminal → manager byte-snapshots the whole subtree (media + run record + graph +
  frame-map + pins) into `manager/frozen/<candidateID>/` with a hash manifest → evaluator reads ONLY
  that frozen copy**. Never evaluate from a live evidence root (§26's sequencing rule, made mechanical).
- **A correction means a NEW candidate ID and a NEW freeze.** Never keep a path and mutate files a
  review has already read — that silently invalidates every number published about them.

> Worked example: `references/mf-v1-correction-wave-narrative-vs-artifact.md` — the contradicting
> verdict pair, the report-only reclassification and its `changed_fields_only` restraint, the 15
> adversarial classifier cases, the three self-corrected packet claims, and the freeze-before-evaluate
> protocol that replaced last wave's shared live root.

## 28. Sealing an accepted-but-uncommitted fix, and the evidence-preservation rules that cost real bytes (verified 2026-09-22)

A lane can be **correct and still un-sealed**: fix verified, suite green, bytes sitting uncommitted
because the packet granted no git authority. That is the lane obeying you, not a defect — and it is
also un-reviewable, because a reviewer cannot name *which* bytes to read. Seal it with a separate
narrow round; never re-open the content.

### The commit-only seal round (~15 tool calls, git only)

- Preflight must show HEAD unchanged **and** `git status --porcelain` listing **exactly** the expected
  paths. Anything else modified or untracked ⇒ stop and report; never commit an unknown diff.
- Re-confirm the content hashes equal what the lane reported; if any moved, stop.
- Add the **explicit paths only** — state in the packet that `git add -A` / `git add .` is forbidden, so
  no orphan or stray file can enter the index.
- Parent must stay the declared base: no amend, no rebase, no reset, no history rewrite, no push, no merge.
- Require the proof set, not prose: `git show --stat HEAD` (exactly N files, every path inside the
  allowlist), `git rev-parse HEAD` **and** `HEAD^`, porcelain empty, and `git branch -r --contains HEAD`
  empty (§17 method 4).
- **Verify the committed bytes, not just the diffstat:** `git show HEAD:<path> | sha256sum` must equal the
  hash the lane reported for the working-tree file — observed **3/3 matching** (`340ebc24…`, `0936b9a6…`,
  `96a358e0…`). That equality is what makes the commit the authority rather than a second claim.
- Let the lane append one line (the commit SHA) to its existing report instead of restructuring it, and
  confirm the diff is a single append with the first line unchanged (`206a207`).
- Budget it small and say so: this is a seal, not a work round.

### A hash-only manifest is NOT recovery evidence

The Manager's own pre-run snapshot of an evaluator's evidence tree was a **hash manifest** (149,831 B,
sha `D2CEBE0A…`) with no byte copies. The lane then reopened its command ledger with mode `"w"` and
truncated 306 rows to 20 — and nothing could restore it: not git, not the manifest, not the reviewer's
copies. The manifest proved *that* it changed and could not produce *what* it was.

- For anything that **could be destroyed** — untracked code, ledgers/transcripts, tool scripts, generated
  media, run records, unpinned fixtures — snapshot **BYTES** and re-hash the copies (§23's
  dirty-worktree pattern, applied *before* the risk, not after it bites).
- Keep hash-only manifests for sets you merely need to prove *unchanged*.
- **Label the manifest type in the file itself** (a real `snapshot` copy path + hash vs a hash-only entry)
  so a later reader cannot assume recoverability that was never there.
- When loss has already happened, record `OPEN_WITH_ACCEPTED_LOSS` with the surviving-evidence index
  (which JSONs/reports still carry the measurements, with hashes) and state explicitly that the old bytes
  are **not reconstructed** — a rebuilt ledger with invented timestamps is a fabrication, not a recovery.
  A loss in an append-only ledger is at least bounded: the measurements survive in the per-step, per-run
  raw files, so say which ones.

### The recurring trigger: probing a destructive tool with `--help`

Two evidence losses in this project family came from the same natural-looking move — asking an unfamiliar
helper for its usage. A stop/cleanup script with **no argparse** ignored `--help` and simply ran, wiping
the previous round's shutdown record; in each case the old bytes were unrecoverable and the surviving
record had to be carried as a loss.

- If a tool's action is destructive or state-changing (stop, shutdown, delete, free, cleanup), **read its
  source first** — `grep -n 'argparse\|sys.argv' <tool>` or read the file — instead of invoking it. Never
  probe with `--help` when the default action is the thing you are trying to avoid.
- When it has already fired: keep the surviving identity-verified record, record the loss as a `fail` row
  naming the damaged files, and state plainly that the old bytes are not reconstructible. Do not rebuild
  them from memory, and put the tool's "takes no arguments / runs immediately" behaviour in the handoff
  so the next lane does not repeat it.

### The guarded-resume packet shape

When authority grants exactly **one** correction to a lane after an evidence-loss incident, the stake has
to be inside the packet, not in your head:

- Name the incident, quote the preimage facts (bytes + sha), and say the old bytes are unrecoverable.
- State the escalation literally: a repeated destructive write or scope breach ⇒ freeze the lane and
  raise `OWNER_TRANSFER_REQUIRED`.
- Make the incident note required reading and demand an addendum artifact from the round (surviving
  evidence + no-reconstruction statement).
- Narrow the ask: "re-run only the checks still relevant with the new ledger; do **not** re-run the old
  N-command dry-run to fake a recovery", and forbid growing the fix into a new framework.

### Your own checker is code — re-derive a contradicting count before filing it

A manager health-count over the lane's new ledger reported **"5 duplicates"** against a lane claiming an
idempotent, duplicate-free ledger. Classifying rows by kind first showed the truth: 6 run-**header** rows
carry no `row_id` at all, the other 200 are command rows with **100 unique `cmd_id`**, and `row_id`
duplicates = **0**. The lane was right; the checker was wrong.

- When your verification produces a number that contradicts a worker's claim, treat your own instrument as
  the suspect first: re-derive with a second method (classify rows by kind, count the right key) before
  writing a finding.
- Retract it in the report when it happens — a manager's false finding costs what a worker's does, and
  §17's retract-explicitly rule applies to your own tools too.

> Worked example: `references/mf-v1-seal-round-and-guarded-resume.md` — the commit-only seal round's
> preflight/commit/prove sequence with the 3/3 committed-blob hash match, the hash-only-manifest loss and
> its `OPEN_WITH_ACCEPTED_LOSS` record, the guarded-resume packet text, and the manager's own false
> duplicate count with its corrected derivation.

## 29. A CLI worker that died MID-JOB: reconcile against the SERVER before re-dispatching (verified 2026-09-22)

The most expensive triage error available in this wave would have been reading a cap-ended GPU round as
a failed run. The worker's CLI stopped; **the job it had already submitted finished successfully
server-side.** Ask the engine before you believe the wrapper.

- **Cap death ≠ job failure. Read `/queue` + `/history` + the engine's output dir FIRST.** The lane
  exited `RUNNING` at its cap, yet `GET /queue` was `{"queue_running": [], "queue_pending": []}` and
  `GET /history` held **4 entries, all `success`** — the last being the lane's own prompt id with **3
  outputs** — plus the engine log line `Prompt executed in 150.04 seconds`. Both artifacts already sat in
  the engine's output dir before any continuation was written. Re-running here would have burned the
  whole GPU budget reproducing bytes that existed.
- **Read the run record FIELD BY FIELD, not its status word.** The load-bearing facts were `attempt_id`,
  `allowed_types: ["output"]` (proof the output-contract boundary held on a **real** run rather than only
  in unit tests), `graph_sha256`, `node_inventory_sha256`, `model_pins`, and `service_epoch`
  (`instance_id` + `pid` + `port`). Those are what let a continuation reconcile instead of resubmit.
- **Engine still alive ⇒ RESUME, never restart.** If the PID/`instance_id` is up and the GPU still holds
  MiB, the model is resident: say so in the packet ("do not start a second engine") and reserve a NEW
  port for the wave so a stale lease from the previous round cannot be mis-read as current.
- **Before `--resume`, resume the LATEST session of the lineage — not the one you remember.** Resuming a
  parent two rounds back mints a **parallel writer** on the same task. `--resume` printed no complaint and
  the minted session's first user message WAS the right packet, so packet text alone cannot catch it: the
  parent id must be checked separately against the newest `started_at` in that lineage (§20's query).
  Kill it **before any write** — the tell is a tiny `tool_call_count` and no bytes changed — then record
  the dead id as `DEAD_KILLED_BEFORE_WRITES` in the registry so the evidence chain stays clean.
- **N attempts, ONE candidate — prove it with hashes, then count it once.** Two render attempts produced
  **byte-identical** output: same `graph_sha256`, same seed node value, same driving-video sha, same
  reference sha, same five model hashes. That is a deterministic re-render, not a second candidate; state
  it from the evidence and keep the candidate count honest, while keeping the superseded attempt's own
  record of *why* it failed (here a wrong media-kind declaration — `videos` declared, server publishes
  under `images`).
- **Stat every artifact path the report NAMES.** The lane stated it had copied the chosen raw render into
  the evidence `media/` dir; the file was **not there**. A path in a report is a claim, not a fact: close
  it with a narrow round that writes the bytes and reports the sha, and mark that path unproven until the
  sha lands.
- **Prove audio provenance by decoding BOTH sides to raw PCM.** A container-duration comparison is not
  enough — decode the delivered clip and the source window with identical settings and compare bytes:
  `ffmpeg -v error -y -i <clip> -t 4 -f s16le -acodec pcm_s16le -ar 44100 a.pcm` and
  `ffmpeg -v error -y -ss <t0> -t 4 -i <film> -f s16le -acodec pcm_s16le -ar 44100 b.pcm`, then
  `sha256sum a.pcm b.pcm` + `cmp -s`. Observed: **identical sha `2387eded…`, 705,600 B each**
  (176,400 samples × 2 ch × 2 B) ⇒ the voice IS the source audio, not a re-encode or time-stretch. Keep
  the container delta and the decoded-sample delta as **separately labelled** numbers (+1.995 ms vs +84
  samples) instead of collapsing them into one vague "audio off by ~2 ms".
- **Freeze the candidate subtree with BYTES + manifest, after the writer is terminal.** Reusable runner:
  `scripts/freeze_subtree.py <freeze_id> <dest_root> <src…>` copies files/dirs into
  `<dest_root>/<freeze_id>/files/`, re-hashes every copy against its source, **refuses** to write into an
  existing non-empty freeze id (a correction means a new id, never a mutated reviewed path), lists what it
  skipped (weights, `__pycache__`), and writes `FREEZE_MANIFEST.json` with per-file sha256 + bytes +
  mtime and a `hash_mismatch` count. Pair it with a short `SNAPSHOT.md` saying which parts are frozen and
  which are deliberately **not** (e.g. a candidate that has no freeze id yet).

> Worked example: `references/mf-v1-server-completed-job-reconciliation.md` — the queue/history
> reconciliation that saved a completed GPU job, the alive-engine reuse decision, the wrong-parent resume
> slip and its pre-write kill, the deterministic-re-render candidate collapse, the claimed-but-absent
> media copy, and the PCM bit-exact audio proof.

## 30. Verify the claim AT THE ARTIFACT the round produced, not at the run it reported (test drift at a new HEAD) (verified 2026-09-22)

A worker round can be internally honest and still wrong about its own gate, because the suite it ran
happened **before** the commit it then made. Observed the same evening as §29: the lane's summary read
`F05 PASS · F06 PASS · F07 PASS · F09 PASS`, and re-running the same suite in its worktree at the HEAD it
had just created returned **`2 failed, 24 passed, 1 skipped in 2.12 s`** — where the *previous* commit was
`26 passed, 1 skipped` — with `ruff check --select F` reporting **6 findings (F401 ×5, F841 ×1) inside the
files that very commit added**. Nothing was fabricated: the lane quoted a real earlier run. "Green suite"
is only meaningful **at a named commit**.

- **Re-run at HEAD, not at the report.** Two commands, immediately after the commit lands:
  `python -m pytest <their tests> -q -p no:cacheprovider` and
  `ruff check --select F <the tools dir the commit touched>` in the lane worktree. This is the difference
  between a row you can close and a row you cannot.
- **Classify the red before assigning blame — two shapes, opposite fixes:**
  - *Over-literal assertion that went stale when the code legitimately changed.* The lane folded the F07
    geometry crop into the F06 frame-selection call, so `assert 'select_filter(keep)' in main()` failed
    while the mechanism was intact (`select_filter(keep, crop_ffmpeg)`). Fix = re-anchor the assertion on
    the **call** (allow arguments) and keep every negative assertion it carried (`-frames:v` absent,
    stream-copy absent). Tighten; never delete, never weaken to "contains select".
  - *Stale expectation where the CODE is right.* The test pinned `kind: 'videos'`; the real server
    publishes `SaveVideo` under the history key **`images`** — which the code had already been corrected
    to. Fix = change the expectation to the **measured payload** and cite the evidence file
    (`raw/run_b3_book4s_a3_history.json`) in a comment, so a reader sees it came from a real history dump
    and not from making a test green.
- **Put the never-weaken rule in the correction packet as text**, e.g. "do not delete the check, do not
  weaken it"; "every change must be justified by a measured fact (a real server payload, or the code's
  real call shape), and the justification goes in the evidence JSON".
- **Keep two labels apart in the row table: PASS-on-behaviour vs green-at-HEAD.** F05 and F06 were
  genuinely satisfied on the delivered artifact (the real run record carried `allowed_types: ["output"]`
  with declared terminal nodes; F06's decoded-index identity was proven by the pixel map against the
  delivered clip) **and** their registered tests were RED at that commit. Say both in the same row, and
  state that the table is only trustworthy once the post-fix green run is on disk *and the Manager has
  re-run it* — then do that re-run before closing the rows.
- **Require the artifact to be re-hashed in the same correction round.** A test/expectation fix must not
  move the deliverable: name the expected sha in the packet and demand `ffprobe` + `sha256sum` unchanged
  as an explicit numbered step (here `55daef67…`, 1,645,695 B, 640×360, 120 frames).
- **A cap-ended round makes this cheaper, not optional.** A lane that stops at its cap and enumerates its
  own gaps (§23) is still quoting runs from *before* its final edit — the cap is exactly when the last
  edit most often lands unexecuted (§23's "un-executed bytes" bullet is the pre-commit form of this).

Small tooling note that costs a round if forgotten: when freezing via `scripts/freeze_subtree.py`, create
the freeze id **only** through the tool. Writing a companion `SNAPSHOT.md` into `manager/frozen/<id>/`
first makes the id non-empty, so the freeze call refuses with
`error: freeze id exists and is not empty` (exit 2) — the refusal is by design (a correction means a NEW
id, never a mutated reviewed path). Write companion docs *beside* the freeze dir
(`manager/frozen/SNAPSHOT_<id>.md`) or copy them in after the manifest exists.

> Worked example: `references/mf-v1-test-drift-at-head.md` — the b3→b4 case: the lane's claimed row
> dispositions, the 2-failed/24-passed re-run at its own HEAD, the two failure shapes with their exact
> diffs, the six lint findings, the b4 packet's never-weaken rules, and the freeze-id collision.

## 31. Manager-side record integrity: session-id provenance, killed sessions, and gating your OWN deliverables (verified 2026-09-22)

The last verification target in a wave is the Manager's own paperwork. It is not exempt: this session's
registry was wrong twice and its dispatch ledger held duplicates, and only the closing gate caught both.

- **A worker's self-reported session id is a claim, not a fact — derive it.** After `--resume` the lane
  routinely reports its **parent's** id as its own (observed: b4's row named the b3 session, and b3's row
  said "resumed, no new id"). Rebuild every `parent → actual` pair from two independent sources: the
  read-only `state.db` (`SELECT id, started_at, ended_at, end_reason, message_count, tool_call_count`
  over the dispatch window) matched to the **measured process window** (launch time + duration from the
  receipt). Then make it a gate row: every `actual_session` in the ledger must exist in `state.db`, and
  every completed round's `end_reason` must be `agent_close` — that single check is what exposed both
  wrong ids. (§20 covers the minting; this covers the *misattribution* that follows it.)
- **A session killed as a PROCESS stays OPEN forever.** `ended_at` is NULL and there is no `agent_close`
  because nothing closed it — the process was terminated. Record the round as
  `outcome: KILLED_PRE_WRITE` with `receipt: null`, and say in the registry that the row is **still OPEN**
  rather than describing it as a clean close. §29's "kill the wrong-parent resume before any write" is the
  action; this is the bookkeeping that must survive it.
- **An append-only manager ledger will accumulate duplicates the moment you backfill.** Writing the first
  dispatches at dispatch time and re-appending them during a later catch-up produced **15 rows for 10
  dispatches**, plus one row pointing at a receipt filename that never existed (the corrected round reused
  the killed attempt's log/receipt stem). Never rewrite the raw history: emit
  `dispatch-ledger.reconciled.jsonl` beside it (unique rows, verified ids, the killed row explicit) plus a
  short `…RECONCILIATION.md` table of *raw said X vs ground truth Y* with the evidence for each. Prove
  `receipt files on disk == dispatches` and `unresolved: 0`.
- **Gate your own deliverables as artifacts, with integrity assertions — not just presence.** The closing
  gate must check more than "file exists and is non-empty": that the expected **row count is present and
  each row key appears exactly once** (`MATRIX.md` must contain one `| **F01** |` … `| **F11** |`), that
  no table is structurally corrupted (`"\n||" not in text`), that every commit/hash string you cite is
  actually in the file you cite it from, and that every frozen id still re-hashes. This caught a real
  self-inflicted defect: successive fuzzy `patch` calls on a markdown table **silently dropped the BENCH
  row and doubled every surviving row's leading pipe** while each call reported success with a plausible
  diff (see `terminal-engineering-discipline` pitfall 34).
- **Write the retraction into the artifact, not just the chat.** The corrected registry carries a
  *Disclosed Manager errors* section naming both failures (the wrong-parent resume, and the file's own
  corruption with the reason it was caught and how it was fixed). A reviewer reading only the artifacts
  then sees the same history you told the user — and the next Manager does not re-derive it.
- **Because your own files are artifacts, rewrite rather than chain-patch when a table needs two or more
  adjacent row edits.** `write_file` the whole table from the reconciled truth; chained replacements in
  the same region are precisely how a row disappears while looking successful.

> Worked example: `references/mf-v1-manager-record-integrity-and-self-gate.md` — the two wrong session
> ids and their ground-truth derivation, the killed session's OPEN row, the 15-vs-10 ledger
> reconciliation with its raw-vs-truth table, and the 79-check self-gate that caught the corrupted
> registry it was written to protect.
