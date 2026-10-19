# S12-R6 completion round — final gates, frozen-ID reconciliation, probe re-runs (2026-09-15)

Companion to the S12-R6 transfer section in SKILL.md. Covers the phase AFTER
per-lane verification: INT completion, Manager finite acceptance, the frozen
node-ID divergence, and the frozen-copy reviewer-probe re-run.

## INT completion verify (transport of 4 lane commits)

- Merge chain to verify: `git log --oneline` + per-merge
  `git log -1 --format="%h parents: %p | %s"` — the merge commit's SECOND
  parent must be the exact source SHA (VAL `535d7c1`→`0b9ec15`,
  RETRY `1d9ed94`→`46abfba`, B01 tip `c8830b3`→`11e2de8`,
  QA `69a1280`→`b5c62d1`; INT docs commit lands on top → frozen tip).
- Union delta check: `git diff --name-only <base> <tip>` must equal EXACTLY
  the union of per-lane path lists (here 25 = 6+5+8+6, disjoint) — any extra
  path is an anomaly, stop and report. `git status --porcelain` empty after
  each merge; `git diff --check base tip` exit 0.
- Protected guard after transport: the pre-transport capture will flag the
  transport-intended shared files as changed — the correct verify is
  `--allow-change` for EXACTLY those 7 paths and zero-change everywhere else.
  Keep the unfiltered verify JSON (`guard-protected-post-transport-raw.json`)
  for audit; it is evidence, not a failure list.
- `fatal: bad object refs/codex/turn-diffs/... geometric-repack failed` on
  merge/commit stderr is PRE-EXISTING Codex-tooling ref noise — exit stays 0,
  no tree impact, never "repair" it. Note it in the packet once.
- An INT turn can end after BƯỚC 1 with exit 0 while static gates + docs
  commit are still pending (the agent narrated "BƯỚC 2 …" and stopped).
  Wrapper exit 0 ≠ lane complete: resume the SAME INT session with an
  explicit finish-list (static gates → docs commit → final report). Do not
  finish INT's static work as Manager.

## Manager finite acceptance (runs BEFORE any broad gate)

```bash
cd <candidate-worktree> && python -B -m pytest \
  tests/s12/s12-lc3-retry/test_r6_identity_resolution.py \
  tests/s12/s12-lc3-val/test_r6_publication_ownership.py \
  tests/test_s09_structural_lock_producer.py \
  tests/s12/s12-lc3-qa-r6/ -q -p no:cacheprovider --basetemp <short>
```
Result this round: 101 passed / 1 failed. The failure was the frozen-ID
divergence below — and it re-proves the standing rule: **no broad gate while
a micro is red.**

## Frozen node-ID divergence (inventory draft vs owner-frozen IDs)

- Mechanism: QA froze the finite inventory PRE-implementation with draft
  expected node IDs (`test_r6_m01_unchanged_initial_replay`); owners committed
  their own frozen IDs (`test_m01_initial_replay_unchanged_no_duplicate`,
  `test_v01_…`, `test_B01_A_…`). The harness check
  `if target.is_file(): assert node in _module_nodes(target)` was VACUOUS on
  pre-merge worktrees (owner module absent → skip) and fired only on the
  merged candidate.
- Quantify BEFORE routing: parse inventory table rows (M/V/B01 IDs) + AST-collect
  `def test_*` per owner module + normalized-token fuzzy match. This round:
  42 cases → 0 exact / 25 fuzzy / 17 unmapped; spot-check of every "unmapped"
  case proved ALL 42 exist as executing tests under owner names (some 1:2 —
  V14, B01-H). Keep the analysis script + `frozen-id-mapping.json` in manager
  evidence.
- Decision rule: MATRIX wording "test IDs must be frozen **by owners**"
  ⇒ owner-frozen IDs are canonical executable IDs. DO NOT rename dozens of
  Manager-verified test functions (blast radius: 3 owner commits, 3
  re-verifications, re-transport of passing bytes). Route the mapping
  correction to the OWNER OF THE FREEZE DOC (QA): update doc node column +
  harness expectation to the actual IDs WITH provenance note ("IDs as frozen
  in owner commits; pre-implementation draft IDs retained in history").
  Preserve check STRENGTH — module present ⇒ mapped node must exist; never
  downgrade to skip.
- Queue the correction AFTER the owner's currently running turn (same session,
  no second writer). The finding + mapping table go in the review packet; a
  reviewer preferring owner renames can order it with full evidence attached.

## Immutable reviewer probes re-run on a frozen copy (no worktree touched)

```bash
# 1) frozen copy of the exact candidate
git -C <candidate-worktree> archive <frozen-sha> | tar -x -C <runtime>/frozen-src
# 2) copy probe files into the SAME test dirs as their imports
#    (probe does `import test_r4_retry_execution` / `import test_publication as base`)
cp <r5-dir>/test_review_r5_identity.py    <runtime>/frozen-src/tests/s12/s12-lc3-retry/
cp <r5-dir>/test_review_r5_publication.py <runtime>/frozen-src/tests/s12/s12-t03c/
# 3) fresh EXCLUSIVE-create evidence dir (probes use open('x') — reused dir == fail)
mkdir -p <runtime>/review-probes-out-N
# 4) run
cd <runtime>/frozen-src && S12_REVIEW_OUT=<runtime>/review-probes-out-N \
  PYTHONPATH=<runtime>/frozen-src python -B -m pytest \
  tests/s12/s12-lc3-retry/test_review_r5_identity.py \
  tests/s12/s12-t03c/test_review_r5_publication.py \
  -q -p no:cacheprovider --basetemp <short>
```

- This round: **7/7 pass** on the frozen candidate (same probes: 1/4 with
  6 failures in R5).
- Old→new evidence deltas worth quoting in the packet:
  - `identity-retry-hidden.json`: Jobs 2→3 + successor created (F01 repro)
    → typed `409 S12_EXPORT_JOB_IDENTITY_CONTRADICTION`, counts 2/2→2/2,
    zero mutation.
  - `publication-foreign-*.json`: foreign inode adopted + receipt + completed
    → call 2 `PublicationError: completed output exists — refusing overwrite`.
  - `publication-handoff-A.json`: stale A created final (transition lost after
    creation) → A `publication fence lost before rename` (no public mutation)
    + B completed + `B_recovery reused=true`.
- Copy the probe output JSONs to the durable evidence dir + hash them; keep
  the R5 originals untouched for the old→new diff.

## B01-I execution outcome — S10 contract collision (the headline residual)

- QA ran 5 bounded public chains (real 4s h264/AAC source, no seeds). Result:
  PASS upload→analyze→producer (201; manifest `5111dbcd-…`, hash `990152a3…`)
  → CAS pin → S09 reapproval v2 (checkpoint `83bccabe-…`,
  `full_apply_executable=true`) → authority executable…
  then BLOCKED at `POST /api/v2/projects/<id>/full-apply` → 422
  `shots overlap or non-monotonic: shot 29963538… [0,119] and 627b554b… [0,119]`.
  Counts at failure: `s10_full_apply_runs=0, s12_export_runs=0, jobs=4,
  reskin_configs=2, manifests=1` — zero mutation after the rejection.
- Root cause (Manager, independent): `app/services/s10_full_apply.py:191-262`
  derives one shot per authority segment 1:1; `s10_chunk_plan.py:166` requires
  shots disjoint + contiguous from 0; B01 `CONTRACT.md` defines `segments` as
  CURRENT-ACTIVE OCCURRENCE rows with z-order/visibility (co-occurring ranges
  LEGAL) while `shot_order` carries scene ordering ⇒ genuine contract
  collision + flag inconsistency (S09 says executable, S10 rejects that very
  manifest).
- Owner behavior to PRESERVE in any rerun of this pattern: QA did NOT weaken
  its harness to green — the chain node re-raises the recorded BLOCKED state
  BY DESIGN ("no false green"); it did NOT touch S10 (outside write-set); it
  recorded exact request/response/IDs + DB deltas and submitted two proposals
  (A: S10 derive shots from manifest `shot_order`; B: producer typed denial —
  weaker, would violate "chain completes").
- Manager routing: the contract choice belongs to Codex → the blocker is the
  packet's headline residual with file:line pointers + both proposals +
  evidence paths. Manager does NOT dispatch the S10 fix unilaterally (not in
  any write-set; picking the contract without the reviewer risks
  re-litigating accepted S10 semantics).

## Verifying a submission that contains a by-design red node

- QA commit `c5954d2` bundled BOTH the node-ID mapping correction AND the
  B01-I artifacts (7 files, +1201/-68; docs + harness + new chain test).
  Manager verify: run the FAST files only
  (`test_r6_finite_inventory.py` + `test_r6_b01i_prep.py` → 11 passed) and do
  NOT re-run the chain node — the owner already ran 6 chain executions and
  the node re-raises the recorded blocker by design (a Manager re-run burns
  ~30 min and can only reproduce the BLOCKED). ruff-F on the lane dir +
  guard verify with `--allow-change` for exactly the committed paths
  (50/50 VERIFIED). Document the skip + reason in the verdict; the by-design
  red IS the reported finding, not a hidden micro.

## Endgame order (corrected by the actual B01-I outcome)

B01-I (owner worktree ff-merged to frozen tip, new output dir per run)
→ node-mapping correction (SAME owner turn is fine — it bundled cleanly)
→ INT round 2 (merge the QA follow-up commit; expected delta = its 7 paths)
→ Manager re-verify finite acceptance: EXPECT `11/12` with the chain node
re-raising the documented BLOCKED — "all-green" is impossible BY DESIGN until
Codex resolves the collision; this documented by-design red does not gate the
broad gate the way an unexplained red does (it is the packet's finding)
→ ONE broad gate under the mutex (report the by-design node alongside)
→ packet with the contract collision as headline residual + proposals.
Only after round 2 does the new tip get written into the packet docs.
