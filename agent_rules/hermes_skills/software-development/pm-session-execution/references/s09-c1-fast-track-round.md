# S09-C1 fast-track round — full execution record (2026-08-24 evening → 2026-08-25)

Reference for future multi-worker correction rounds. The SKILL.md + manager-liveness reference carry the generalized patterns; this file preserves the concrete timeline, numbers, and packet texts worth copying.

## Round setup

- Trigger: Codex review `docs/pm/reviews/S09_FULL_SPRINT_PM_REVIEW_2026-08-24.md` → `S09 = CHANGES_REQUESTED` with findings F1–F7 (F1/F2 P0 renderer/benchmark fake; F3 encoding-dependent gate; F4 missing production mount + no commit; F5 schema accepts invalid payloads; F6 pinned-evidence NULL leak; F7 registry/authority reconciliation).
- Authorized prompt: `docs/pm/prompts/S09_C1_FAST_TRACK_MANAGER_2026-08-24.md` — max 5 parallel workers, join gates J1 (renderer-contract freeze) and J2 (production API integration), terminal `S09-C1 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` or `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`.
- Preflight: HEAD `ee10e55a` matched the review checkpoint exactly; dirty 82; alembic head `b3c4d5e6f7a9`; DB URL UNSET. **All 11 owner sessions named in the prompt verified in state.db** (`SELECT id FROM sessions WHERE id=?`) plus first-user-message TASK-ID disambiguation.

## Lock table (final state)

| Task | Owner session | Finding | Result |
|---|---|---|---|
| T02-C1 | 20260824_015213_f5516b | F1+F3 | 37 passed ×2; composite.py real; contract frozen |
| I03-C1-PREP→measured | 20260823_173318_69a813 | F2 | PREP 26×2; measured post-J1; gates finished on J1B resume |
| T01-C1 | 20260822_232748_b4b2ad | F6 | 13 passed ×2; NULL/other-manifest/after-pin excluded |
| T05A-C1 | 20260824_072626_645cde | F5 | 28×2 + NEW 39-test validation file |
| T06A-C1 (+T56) | 20260824_120141_312e9e | F4 | 26×2; commit in route layer; then T56 mounted app.py |
| T56-INTEGRATION | same as T06A | F4 production mount | OpenAPI 251 paths, dup ops 0, restart-durability proven |

## Key verify numbers

- Production OpenAPI after T56: 251 paths = 241 pre-existing + 5 s09-corrections + 5 s09-approvals; duplicate (path,method) pairs: 0.
- T02-C1 pixel/geometry acceptance: pose A/B within ≤1 frame schedule error; pixels outside affected mask unchanged in tolerance; two runs share canonical decoded-frame hash.
- J1 frozen hash recipe: sha256 over chain of `utf8(relative_path) + b'\0' + file_bytes` for renderer_contract.py, renderer_routes/__init__.py, composite.py → `46c6a41f2e0959736fe570b37fda564c0e330e64248e6171f6a7d4fb404bbc1e`. Manager reproduced it only via systematic combo enumeration (raw concat, hex-joins, LF-normalize all failed) — the recipe MUST be stated inline in future freeze markers.
- T05A-C1 invented its own validation file: `tests/test_s09_t05_backend_c1_validation.py` (39 tests, 29 adversarial patterns incl. anchor 9.0/-2.0, frames 20..1 reversed, bogus routes) with `_correction_row_count()` before/after assertions proving rejected requests leave zero rows.

## Packet texts that worked (patterns to copy)

- Correction packets quote the finding ID inline ("F1", "F5") so the worker maps its work to the review bullet.
- Phase-2 unlock packet (T56): "PHASE 2 — S09-T56-INTEGRATION-C1 (J2 đã mở: T05A-C1 và T06A-C1 đều TASK_MANAGER_VERIFIED, process đã exit). Bây giờ được phép sửa app/api/app.py — duy nhất phase này…" — states the gate condition as evidence, grants the lock explicitly.
- Lint-debt freeze packet (I03 J1B): "Measured results GIỮ NGUYÊN — không đo lại; chỉ sửa E501 / re-check type:ignore, re-run gates ×2, REPORT STATUS: TASK_SUBMITTED, STOP."
- Mid-question answer embedded (from earlier wave, still valid): if the dying worker left an open question ("enum ở đâu?"), the resume's first line answers it.

## Timeline actuals (for ETA calibration)

- 21:40 preflight → 21:47 Wave A ×5 dispatched
- Exits: T06A-C1 22:51 · T05A-C1 23:41 · I03-PREP 23:50 · T01-C1 00:36 · T02-C1 01:05
- Each verified within minutes of its exit (never batched)
- 00:05 J2 opened → T56 dispatched → done 00:39 (26×2 verified)
- 01:20 J1 handshake verified by manager re-hash → I03 measured resumed
- 03:10 I03 measured exit (mid-gates) → J1B polish resume 03:15
- 03:15 T06B-C1 dispatched in parallel (J2 already satisfied — no reason to serialize)
- 04:04 T06B-C1 exit → verified: Playwright Chromium RUN1/RUN2 both **1 passed** (13.4/13.5s) through ACTUAL app.api.app with a `s09-t06bc1-global-setup.ts` that resets the production-backend DB between runs, plus a standalone API probe script returning `PROD_PROBE_ALL_OK`. Production-stack E2E acceptance = Chromium ×2 identical + probe chain green + tsc/eslint/build logs archived in the lane.
- 04:15 I03-C1 final verify: benchmark suite grew 26→**29 passed ×2** (44.4/44.0s); smoke_full8 results are **schema v2** with per-result `input_hashes`, `decoded_output_hash`, `measured_state`, `artifact_path`, `backend` — this is the concrete shape of "renderer-real measured evidence" that answers F2 (each fixture/route row proves it invoked the renderer and scores generated output, not source frames).
- 04:20 I05-C1 dispatched (owner 20260823_233406_8d5b7b) — measured decision v2: smallest passing route only when every required metric is MEASURED/sample>0/pass; UNKNOWN/SKIPPED never PASS; FAIL_OPEN_QUESTION if evidence insufficient. Final C1 gate next morning.

## Attribution note kept in registry

One mypy error surfaced during T56 verify (`s09_demo_jobs.py:203 "object" not callable`) while T02-C1 was still editing `select_route()` in its own lane. Recorded as sibling-in-flight attribution, not a T56 defect; re-check scheduled at final gate. Registry row language: "sẽ resolve khi sibling exit và được check lại ở final gate."
