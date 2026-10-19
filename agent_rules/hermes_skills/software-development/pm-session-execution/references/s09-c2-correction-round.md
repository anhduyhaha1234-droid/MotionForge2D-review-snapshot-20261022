# S09-C2 correction round — setup record (2026-08-25 morning)

Reference for the NEXT correction round after a round itself came back CHANGES_REQUESTED. The SKILL.md + manager-liveness reference carry generalized patterns; this file preserves C2-specific decisions and packet shapes.

## Round setup

- Trigger: Codex review `docs/pm/reviews/S09_C1_PM_REVIEW_2026-08-25.md` → `S09-C1 = CHANGES_REQUESTED`, and explicitly corrected the C1 terminal protocol: with two FAIL_OPEN_QUESTIONs still open, the correct terminal had been `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`, NOT `TASK_MANAGER_VERIFIED`.
- Authorized prompt: `docs/pm/prompts/S09_C2_CORRECTION_MANAGER_2026-08-25.md` — again max 5 parallel workers, joins J1-C2 (immutable renderer freeze with RECURSIVE machine-readable manifest over ALL behavior-critical files, not 3 hand-named files) and J2-C2 (Wave C binding runs), terminals `TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` or `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`.

## C1 findings being closed (map)

- F1 (P0): f1_hard_cut + f5_group_occlusion had zero measured routes; manager wrongly declared TASK_MANAGER_VERIFIED anyway.
- F2 (P0): benchmark imported compositor/private `_alpha_composite_into` + `composite_*_frames` directly instead of instantiating public RendererRouter/execute; also rendered into shared fixture tree then copied.
- F3 (P0): J1 freeze invalidated AFTER measured run — `renderer_routes/__init__.py` changed post-handshake (recompute gave `62c7d7d6…` vs frozen `46c6a41f…`); manager never invalidated downstream. C1's freeze covered only 3 hand-named files; C2 mandates a recursive machine-readable manifest of every behavior-critical file, verified before AND after each run.
- F4 (P1): frontend hook hard-coded old artifact path (`useDemoCompare.ts:47`).
- F5 (P1): fixed `_CANONICAL_FPS = 30.0` retime (no rational fps/timebase), `request_id.endswith("@identity")` business behavior, output hash computed pre-encode, alpha_mode accepted but unenforced.
- F6 (P1): Windows MAX_PATH publication failure (260-char final path, `.mp4.upload` FileNotFoundError) plus an `artifacts/artifacts/<ws>/...` double-prefix bug.
- F7 (P1): production-stack E2E missing "only affected loop regenerates" snapshot proof.

## BA pre-chots encoded in the C2 prompt (do not renegotiate)

- hard_cut and group_occlusion are REQUIRED classes — no removal, no no-op PASS.
- Measured evidence must flow through public RendererRouter.execute() + production adapter; direct compositor calls are not route evidence.
- Provenance hashes canonical decoded frames of the ENCODED output.
- All hard-codes to old `t00-i05/measured_seed20260823` purged from production/frontend/active tests (archival docs may mention).
- Required class fail/unknown/FOQ = BLOCKER; "Manager không có quyền ghi TASK_MANAGER_VERIFIED trong trường hợp đó."

## Wave A dispatch table

| Task | Owner session | Focus |
|---|---|---|
| T02-C2 | 20260824_015213_f5516b | rational fps/timebase contract, layer ordering, kill @identity, post-encode hashing, TYPE_CHECKING fix for lazy re-export |
| I03-C2-PREP | 20260823_173318_69a813 | f1/f5 fixtures with real replacement, harness v3 via public router only, stops at WAITING_JOIN |
| T03-C2 | 20260824_031524_a6bb2a | long-path ≥260 atomic publication, dedupe artifacts/artifacts, stale-SHA fail-closed |
| T04-C2 | 20260824_052859_c6e197 | purge v1 hard-code, single pinned benchmark content SHA |
| T06B-C2-PREP | 20260824_131423_423e42 | only-affected-regenerates spec (snapshot all artifact IDs+hashes before correction) |

## Phase vocabulary introduced

- PREP workers stop at `STATUS: PHASE=WAITING_JOIN / PENDING_<X>_BINDING` (T03-C2) or `CORRECTION_SUBMITTED_C2` (T04-C2) — NOT TASK_SUBMITTED.
- Final binding runs happen on a SECOND resume of the same owner after the join lands (I05-C2 verified for T03/T04/T06B binding).

## Early results

- T03-C2: 15 passed ×2, ruff clean, long-path refs present, artifacts/artifacts duplication fixed (stale string only in explanatory docstring). Verified within ~5 min of exit.
- T04-C2: 13 passed ×2, tsc EXIT=0; v1 hard-code purged from useDemoCompare.ts (only a "NO default here" comment remains); benchmark content SHA pinned in BOTH frontend hook and backend route. STATUS CORRECTION_SUBMITTED_C2.
- T02-C2: focused suites 51 passed ×2 + NEW `test_s09_t02_c2_timebase_identity_contract.py` 14 passed ×2 (probe timebase, fraction validation, exact inclusive frame count, NTSC 30000/1001 conditional on ffmpeg); mypy app --no-incremental Success 125 files; `@identity` live code fully removed → typed `identity_transform: bool` that only validates when the keyframe track is empty; decoded-frame hash is now a first-class evidence field.

## Late Wave A outcomes (added end of round)

- I03-C2-PREP exited claiming TASK_SUBMITTED but Manager's own suite run found **8 failed / 21 passed**: worker bumped `SCHEMA_VERSION = 3` in `scripts/s09_renderer_benchmark.py` but left `tests/fixtures/s09_renderer/thresholds.json` at `"schema_version": 2`; every subprocess test fail-closed on load (`BENCHMARK_ERROR: thresholds schema_version must be 3, got 2`). Good parts confirmed first: public `RendererRouter.execute()` path present, zero private composite calls in the script, f1/f5 manifests have typed replacement. Resume packet FIX1 went back to the same owner: bump ONLY the version field (+ new v3 fields the design needs), threshold VALUES untouchable, re-run ×2, then WAITING_JOIN.
- **Generalize**: any worker bumping a `SCHEMA_VERSION`/policy constant must bump every fixture/data file carrying that version IN THE SAME change — put that sentence in PREP prompts up front. And always run the focused suite YOURSELF before accepting a TASK_SUBMITTED whose log you haven't diffed against test names; a red suite behind a green STATUS line is the most common worker-report lie of this project.

## Mid-round incidents (patterns, not noise)

- T06B-C2-PREP exited early WITH a correct root-cause in its log (seeder filtered `Job.job_type == "S09_DEMO_LOOP"` but durable rows store lowercase `"s09_demo_loop"` → reset deleted nothing → pinned resubmit returned 200/reused instead of 201). Correct handling: resume the SAME owner with a packet that names the exact root cause and remaining steps — do not treat early-exit as done and do not spawn a replacement session.
- First resume attempt FAILED SILENTLY: inline `-q "$(printf ...)"` with apostrophes in the text → bash `unexpected EOF while looking for matching quote'`, exit code 2, worker received NOTHING. Rule: resume/correction prompts ALWAYS go through a prompt file (`$(cat resume-x.txt)`), never inline printf with free text. After any dispatch, grep the log for your EXIT tag to confirm the launch actually happened. (This bit twice in one round — the relaunch via file worked immediately.)
- Worker also surfaced cross-lane findings outside its write-set (CorrectionPanel missing affected_loop_ids; ApprovalPanel reasonsOf can never match route_override corrections) — record them in the registry for the owning lane (T05B), don't let the reporter "fix" them.

## Manager verification shortcuts that held up
## Manager verification shortcuts that held up
- Grep REPORT.md for `STATUS:` tail rather than trusting log size alone; check live-code vs docstring hits separately (`grep endswith("@identity")` over adapters/routes — docstring mentions are acceptable, executable branches are not).
- For "no more hard-coded artifact v1" gates: expect ONE explanatory comment hit max, zero functional references.
- New test files created by workers need to be RUN explicitly ×2 — they don't appear in the old focused-suite invocations (the timebase suite was missed by the first verify pass).
- Registry append after EVERY verified task with timestamp +07, exact numbers, and which finding it closes — this is the raw material the final packet assembles from.

## Wave C / final binding (end-of-round record)
- After I05-C2 verified with `FAIL_OPEN_QUESTION = 0` and 6/6 required classes MEASURED_RENDERED_OUTPUT through public router evidence: pin benchmark + decision SHAs in registry, then resume T03/T04/T06B owners a SECOND time for binding runs. PREP-phase statuses upgrade only then. If any required class still lacks measured evidence → terminal is BLOCKED_WITH_FINDINGS, no exceptions (C1's F1 lesson enforced).
- J1-C2 freeze manifest: recursive SHA-256 over contract/router/adapters/**/routes/** written to `output/s09/20260823_sprint_full/j1-c2/renderer_freeze_manifest.json`; I03 verifies manifest before AND after every measured run; drift → stop I03, invalidate downstream, resume the drifting owner, new J1, rerun I03/I05. Never "just update the constant".

