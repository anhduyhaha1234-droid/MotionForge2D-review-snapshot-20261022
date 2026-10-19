# S09-C4 META Completion — 27/08/2026 Manager Notes

Authority: `docs/pm/prompts/S09_C4_META_COMPLETION_MANAGER_2026-08-27.md` (supersedes all prior prompts; `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c59f…`). Worktree `C:/Users/Admin/MotionForge2D-worktrees/s08-integration` @ `ee10e55a` (`codex/s08-integration`, dirty 117), MAIN `a43b20d` read-only. Freeze J1-v4 `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5` 13/13, I03 `12de1345…`/`dab37e41…`, I05 `d289929d…` retained. Model combo `meta` (9Router round-robin `cmc/meta/muse-spark-1.2-contributor` + `ocg/muse-spark-1.2-contributor`, reasoning max, fallback disabled, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`).

## J0-META + byte-freeze CRLF diagnosis (verified 02:42)

7 files batch-stamped `2026-08-26 22:57` converted LF→CRLF. Diagnostic = two SHA per file:

- direct byte SHA vs expected manifest SHA
- normalized-LF SHA (UTF-8 LF no BOM) vs expected

Pattern §4 exact: 7 direct MISMATCH but normalized MATCH, 6 direct MATCH (including `composite.py` intentionally CRLF `3b419d8b…` direct MATCH / normalized DIFF). Worker must assert normalized == expected before rewriting, then rewrite as LF and prove direct == expected; Manager independently re-hashes 13/13 after exit. Do NOT pin v5 or rerun I03/I05.

Worker `S09-FRZ-C4` via `hermes -m meta` restored 7 files to LF → 13/13 MATCH, bonus fence `renderer_freeze_manifest_v4.json` itself also rehashed. Log: `output/s09/20260823_sprint_full/freeze-c4-meta/`.

## DAG — META

`J0-META → S09-FRZ-C4 (7-file LF normalize, new session, meta) → T04 narrow test-integrity correction (resume 052859_c6e197, meta) → J1-C4 backend join (FRZ+T04+T03 38 + T05A 25 = 66 southern tests) → T05B final (resume 093602_af7c26, meta) → J2-C4 → T06B production ×2 (resume 131423_423e42, meta) → final gate → Codex`

Writers quiescent at each join. No S10/S11/S13.

## T04 integrity — owner 052859_c6e197 (23 passed)

Fixes `tests/test_s09_t04_demo_compare.py:_seed_applied_zorder_correction` (650-707):

1. Unknown/empty/multi-loop → FAIL CLOSED, never default to `d4` (counts before/after, zero mutation).
2. No fresh-DB determinism claim with random `project/scene/role` IDs in recipe — use fixture-anchored deterministic `logical_id` (`wire_extraction_segment` == `create_extraction_segment:1334`) or persisted-lineage + restart/read proof.
3. On `SegmentConflictError` reuse only after proving exact `project/video/role/scene/source-generation` + payload ownership, else fail closed.

Added 2 adversarial tests (unknown_loop + collision ownership), total 23 (21+2) ×2 basetemps, ruff/mypy clean.

## T05B final — owner 093602_af7c26

F1 retained: `affectedLoopIds=[selectedLoopId]` only when `baseJobId && selectedLoopId`, gate `regenBlocked=!baseJobReady||len!=1`, fail-closed before HTTP for submit/confirm/openRegen, helper `text-gray-400` 11px. Types §4.5 mirror `GenerationEvidence(generation: string)` + `frozen_evidence_sha256` + `PublicationStatus`. tsc 0, eslint 0, 25 T05A rerun 24.10s, Playwright 2 passed/6 skipped (desktop F1 blocked + mobile overflow), output `t05b-c4/`.

## T06B ×2 — owner 131423_423e42 (partial, needs probe patch)

Probe `db_attempt_probe.py` reads `job_attempt.result_json` for `s09_demo_loop_regen`. Gotcha: `WHERE id IN (?)` with tuple fails on SQLite (must expand to `:jid0,:jid1…`), and `step_code` for regen jobs is `run` in isolated QA DB (not `demo_loop_regen` as in `REGEN_STEP_CODE`). Regen job `2d64742a` completed with `affected [d4_group_occlusion]`, `d4 regen True render_ms 500`, others False — targeted semantics correct, but `regen_attempt_count` counted 0 until probe patched to count `run`. Needs 1-2 retries to achieve ×2 PASS with evidence snapshots (d4 id/hash change, others verbatim).

## Model routing — meta (27/08)

`hermes config set model.default meta` (provider muse, base_url `http://127.0.0.1:20128/v1`, api_mode `codex_responses`). Verify `hermes -m meta -z "ping"` → pong 200. All new/resumed workers `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 … -m meta --yolo`. Never `provider muse` alias or direct `ocg/…` pin.

## Heartbeat + continuous execution (27/08 META)

27/08 user updated from 5' (Muse phase) to **30' + instant on completion/blocker** — recorded in SKILL.md Registry & heartbeats section. Mid-DAG the user repeated `chạy đi đừng tự dừng` / `xong chưa` while T06B was in prefill/retry — manager must keep `process wait` loops alive and **resume same owner (`20260824_131423_423e42`, `-m meta`, TTFB900) immediately on any NGHTTP2/429/exit**, with instant dispatch confirmation + ETA table in the same reply (don't defer to next 30' heartbeat). Slow-coding with reasoning max (150k prefill → 15–22 min silence) is normal, not a stall — distinguish from real worker exit.

## Final closure 27/08 11:00 — T06B ×2 PASS + final gate (verified)

- **Worker** `proc_9b02dcf653b8` via `meta` (owner `20260824_131423_423e42`, 1969s, TTFB900) → **RUN1 1 passed 27.6s (test 26.3s) + RUN2 1 passed 27.6s (test 26.2s)**, `.last-run.json {"status":"passed","failedTests":[]}` — discriminating evidence: `affected [d4_group_occlusion]` (`job_attempt` `generation targeted`), `d4_group_occlusion` sha NEW vs `d1/d2/d3` verbatim, mask `f4eca000…` distinct from phone `9c64dcb…`, contacts 1/motions 1 after manager RESET re-seed fix, checkpoint `4589149dcbb02aa5…` preserved after restart, frozen R identity `cf7f27…` vs pinned `2412b23c…` bytes-identical path-diverge via `stage_frozen_copy`.
- **Manager patches** (direct, verified on disk before resume): `db_attempt_probe.py` widen regen count to `step_code run` (`IN (?)` → `:jid0` expansion) → `regen_attempt_count 1`; `run-prod-seed.py` RESET re-seed `SceneGraphContact`+`SegmentMotion`; `mask_t06b_occluder.png` 56×96 distinct red+blue; `generate_fixtures.py` persist mask with `d4_group_1 [200,214]` occlusion.
- **Production fixes** (worker, via meta): `pose_swap` rotate BILINEAR+scale, `route_override` 2×2 marker `hash(route_to:evidence)` for deterministic byte delta.
- **Final gate §7** (manager independent, 11:00): `npx tsc --noEmit` EXIT 0, `npx eslint e2e/s09-t06bc4*` EXIT 0, freeze `ae92247b…` 13/13 + no v5 + `git diff --check` 0, `pytest tests/test_s09_t06*` 43 passed 41.13s, `tests/test_s09_t04_demo_compare.py` 23 passed (manager 56s in-turn, worker 46s) — all fresh basetemp, `MOTIONFORGE_DATABASE_URL` unset. Registry `S09-C4-SESSION-REGISTRY.md` appended `11:02 — FINAL GATE C4 — TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` (140 lines). No `BLOCKED_WITH_FINDINGS` left open in this cycle.
