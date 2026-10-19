# Gate calibration, drift & prevalidation traps (S10-C6B proven patterns)

Detail bank for the gate-execution and acceptance sections of SKILL.md —
concrete S10-C6B cases behind each rule.

## Canonical ruleset calibration — verify BEFORE scripting

Bare `ruff check` runs the full default ruleset (E501/I001/N814 → hundreds of
pre-existing style hits on mature code; C6B saw 343) while the sprint's real
gate is `--select F` (evidence-log naming like `ruff_F.log` is the tell). Read
the prior gate evidence logs during pre-staging and copy the exact command; a
wrong-ruleset `RUFF=1` is a SCRIPT false positive, not a product defect —
re-run the canonical command manually, record both outputs in the verdict
(J6C_VERDICT.md did), and never "fix" style errors the gate never gated.

## Sweep hits: verify against the handler, not the regex

A broad-except sweep can flag a legitimate nested rollback-guard — inner
`try: session.rollback() except Exception: pass` sitting INSIDE an outer
`except Exception:` that compensates and raises HTTPException(500). That is
fail-closed by design, not a swallow. Route-scope the sweep first (map each
line to its owning `def`), then manually read every hit's handler before
declaring a defect; one LEGITIMATE hit documented in the verdict beats a
false gate failure.

## Live-UI acceptance failures: classify before acting

When a full acceptance run fails some scenarios (16/20), sort each failure
into harness gap vs product defect BEFORE any fix: which store does the
failing UI call read (v1 disk store vs durable SQLite), did the scenario
ever run live before, what does the failure screenshot show. Harness gap
(seeder doesn't populate the legacy store) → fix global-setup with
assertions untouched, re-run full; genuine product defect outside the node's
scope → BLOCKED_WITH_FINDINGS. A clean-exit partial run plus the worker's
own root-cause notes converts verbatim into `prompt_t2.txt`.

## Prevalidate BEFORE burning expensive e2e verticals

A multi-minute full-product run (backend+frontend launch, seed,
submit→chunks→publication) must be preceded by a cheap dry-run script
against a COPY of the DB that exercises the seed + manifest + route paths
the spec will hit. T04C-C5 T2's prevalidation caught the fixture creating
segments with NULL `segmentation_json` (no geometry → no `affected_region`)
and a `mesh_warp` route outside `FULL_APPLY_EXECUTABLE_ROUTES` — either
would have failed the verticals mid-run after 5-9 wasted minutes each.

- Gate the real runs on an explicit `PREVALIDATION_RESULT: PASS` line.
- Fix fixtures (node-owned) and re-prevalidate until PASS, only then burn runs.
- Keep the prevalidation script + diag outputs as evidence (Temp or output/**).
- After manager-side lifecycle changes (e.g. layer_id now derived from
  role_id), trace the downstream binding path in the SAME prevalidation pass
  — closure corrections must still match logical ids.
- The gate script must honor the SAME env constraints the worker hit: short
  pytest basetemp roots under `%TEMP%` (WinError 206 — see the motionforge-2d
  s10 reference), DB env UNSET, `-p no:cacheprovider`, and per-run distinct
  roots.

### Prevalidation catching a defect is a WORKFLOW PROOF, not a delay (C6B T04C, 2026-09-01)

T04C-C5's prevalidation caught fixture defects in TWO consecutive turns (NULL
`segmentation_json` + out-of-set `mesh_warp` route; later a manifest bundle
desync), each of which would have burned a 5-9' vertical mid-run. When it
fires, resist the urge to weaken the prevalidation or skip it "just this once"
to save time — the pattern that saved the sprint:

1. Read the failure OFFLINE (read-only DB-copy probes, per-branch tracing) —
   classify it as node-owned fixture gap vs product defect BEFORE touching
   anything.
2. Patch the node-owned fixture/spec; if the fix touches a hash-pinned bundle,
   resync ALL bundle artifacts (file + manifest.json files[] sha/size +
   regenerated manifest.sha256 + generator source).
3. Re-prevalidate on a FRESH DB copy — a PASS against a stale copy proves
   nothing (same principle as pytest roots: fresh per run).
4. Only a fresh-PASS burns the verticals. Track "prevalidation caught N" in
   the verdict — it is the evidence the gate earns its cost.

Related: a blocked first vertical (BLOCKED_SHOT_ORDER_MISMATCH) that was
reproduced offline branch-by-branch (policy/hash/lineage/decode/timebase all
OK, only seg-id mismatched) pins the root cause to one line
(`shot_id = occurrence_segment.id`) without a single extra live run —
offline replication of a blocked run is cheaper and more precise than
re-running to "see what happens".

## Rules-file drift triage (worktree vs MAIN divergence)

A worker reporting "RULES SHA mismatch" may be a pre-existing BRANCH DIVERGENCE,
not tampering: worktree copy 37 lines ≠ canonical 180 lines while `git status`
is clean on BOTH sides means the worktree branch is simply behind. Triage:
compare `git show HEAD:<file>` line counts, verify the MAIN copy's SHA against
canonical, and record the divergence honestly in LOG — do NOT merge/reset
(guard). Manager reads canonical rules from MAIN at preflight, so sprint
authority was never at risk.

## Hash-verification method: parse the snapshot, never hand-copy

Verify hashes by PARSING the snapshot file (split its actual format — e.g.
`STATUS path hash@snapshot hash@recompute` lines), never by hand-copying
hashes into a verification dict: hand-typed wrong values produced false DIFFs
and nearly a wrong invalidate/skip conclusion. If the format is unclear, read
the file first (read_file), then write the parser.

## Build-skip hash-equality is a PRE-STAGE HYPOTHESIS — re-verify at gate time

Hash-equality proven SAME at pre-stage is NOT a gate-time fact: the live-UI
node then modified production frontend bytes and the skip shortcut became
false. Re-check when the gate fires:

- Fast tell: `git status --porcelain | grep -iE "frontend"` — any modified
  production frontend file ⇒ hash-equality is dead, rebuild for real.
- Rebuild flow: `node output/s10/run-s10.js --build-only` (prints the new
  BUILD_ID) then `--verify-build-only` (7/7 validator), appended to ONE log
  under a manager evidence dir.
- `mkdir -p <log dir>` BEFORE the `>` redirect — bash never creates the
  redirect target's directory; missing dir = instant BUILD_EXIT=1, zero work.
- Patch the DOWNSTREAM node's pre-staged resume prompt with the new BUILD_ID
  before dispatching it (stale id sends the worker at the invalidated build).

## Focused live-UI checks: canonical config + BAKED build origin (C6C, 2026-09-01)

A manager-side focused live check (grep'd subset of a full-acceptance spec)
failed twice on harness misconfig before going 8/8 green — both failures
LOOKED like product defects. The traps, in the order they bite:

1. **A hand-rolled minimal playwright config silently omits `globalSetup`.**
   The spec's first scenario then dies with `project S10-C6A-EXEC not found
   via public API` — the seeding chain (T04C canonical setup + the
   EXEC/NOAUTH/PROD-E2E projects) is part of the harness contract. Always run
   through the canonical per-spec config (e.g. `playwright.s10-ui.config.ts`),
   even for a `--grep` subset; do not author a fresh minimal config.
2. **`NEXT_PUBLIC_API_URL` is baked into the production build at build time**
   (verify: `grep -r "localhost:8201" .next/static/chunks/`). Launching the
   live check on other ports (`S10_FRONTEND_PORT=3015`,
   `S10_BACKEND_PORT=8212`) makes the UI fetch the wrong origin → a
   "Failed to fetch" error box plus an empty `(không có project)` dropdown
   that mimics a data/product defect perfectly. Diagnosis path: failure
   screenshot → error-box text → `API_BASE` in `src/lib/api.ts` → grep chunks
   for the baked URL. Live checks MUST run on the baked origin (8201/3000 for
   this build).
3. **Gate scripts must use absolute evidence paths whenever the script `cd`s**
   (a relative `G=output/...` died after `cd frontend` → phantom `LIVE_EXIT=1`
   with no log file written).
4. **Newline-less `cat` in gate logs creates phantom parse values**: `cat
   frontend/.next/BUILD_ID` without a trailing newline concatenates with the
   next `echo` in the log, so the log parser read `BUILD_ID ...DIFF` and the
   gate printed a phantom hash mismatch. Verify by content + sha256
   comparison (parse-don't-hand-copy rule) and record the parse artifact in
   the verdict.

**Harness-vs-defect triage, restated:** attempts 1–2 failed = harness
misconfig; the spec was never touched. Say so explicitly in the verdict with
the diagnosis chain, and make the FINAL green come from a re-run of the FIXED
script (not just the ad-hoc inline command that happened to pass). When a
post-terminal verification hook flags stale evidence, close it by re-running
the decisive suites FRESH on the final tree (repro script + focused pytest +
fixed live-check script), then append a re-verification line to
EXIT_VERDICT/registry — ad-hoc passes from earlier tree states don't count.

## Reproduction evidence: immutable before/after roots + RED-phase discipline (C6D, 2026-09-01)

The correction-packet pattern (Codex `CHANGES_REQUESTED` → Manager preps
BEFORE reproductions → worker fixes → Manager proves the fix) hard-requires
evidence immutability. This is the discipline that prevents Codex's P2
evidence-integrity finding (C6C prep repro files were overwritten at 17:08,
after EXIT_VERDICT 16:56, mixing post-fix output into a `prep/` location):

1. **Two separate immutable roots**, never one mutable dir: Manager writes
   `output/s10/<round>/manager/prep/before/<case>/**` BEFORE dispatch and the
   worker's fix, then NEW files under `.../after/<case>/**` after the fix.
   Same filenames/paths are forbidden across before/after — no "rerun in
   place". Never rewrite any C6C-era or earlier evidence; a packet's PREP
   section may forbid touching the previous round's `output/s10/c6c/**` at all.
2. **RED-phase asserts are evidence, not a bug.** Each before-repro asserts the
   CORRECT contract (e.g. `C1_replay_coherent: replay ok AND not failed+queued`)
   and FAILS pre-fix by design. Save `checks: {C1: bool, ...}` plus full HTTP
   bodies and every run/job row to `result_before_<case>.json` in the same dir —
   the failing pytest run + the JSON are the defect proof Codex will compare
   against. Do NOT "repair" these scripts when they fail pre-fix; do NOT re-run
   before/** while the worker owns the tree (importlib loads the tests module
   half-edited mid-flight → corrupted evidence). Refinement (C6E): before
   re-running any before-repro to satisfy a verification hook, FIRST check the
   write-set mtimes against pre-dispatch baseline — if the worker has not
   landed yet (mtimes unchanged, dispatch log 0 bytes), a re-run is
   deterministic-safe and gives fresh RED evidence; only defer when the worker
   has already started editing (single-writer rule). Post-fix proof goes to
   after/** with the same contract; the flip False→True is the gate.
3. **Depth-independent repo-root finder for importlib repros.** A repro that
   `sys.path.insert` + `importlib`-loads `tests/test_*.py` (tests/ is not a
   package) must NOT use a fixed `parents[N]` — it breaks when the Manager moves
   the repro deeper (C6C `prep/repro_c6c.py` = parents[5]; C6D
   `prep/before/<case>/repro_c6d_f1.py` needed parents[7] and failed with
   `FileNotFoundError: ...worktree\output\s10\tests\...`). Use:
   `_ROOT = next(p for p in Path(__file__).resolve().parents if (p/"tests"/"test_s10_full_apply_api.py").exists())`
   then insert into sys.path.
4. **Evidence dirs are part of the contract.** The packet may name exact
   `before/failed-run-queued-job-retry/**` and `before/tampered-manifest-replay/**`
   paths with required contents (HTTP bodies, durable counts, expected/actual
   manifest, lineage rows) — write the script to emit those sibling files, and
   keep the script itself next to them so the dir is self-contained.
