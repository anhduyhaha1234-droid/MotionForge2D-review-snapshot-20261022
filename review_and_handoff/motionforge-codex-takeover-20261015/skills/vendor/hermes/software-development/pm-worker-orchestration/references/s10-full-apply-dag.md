# S10 Full Apply — 8-Owner DAG & ETA Contract (verified 2026-08-27)

Source: `docs/pm/prompts/S10_FULL_APPLY_MANAGER_2026-08-27.md` + `ROADMAP.md` S10 + `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c5`.

## Frozen DAG (do NOT resequence)

```
PREP -> (T01A || T01B) -> J1 -> T01C -> J2 -> T02 -> J3 -> T03 -> J4 -> T04A -> J5 -> T04B -> J6 -> T04C -> SPRINT_EXIT
```

- Only T01A + T01B parallel (max 2 writers). Disjoint write-sets: T01A owns `app/persistence/models.py`, `app/persistence/s10_full_apply.py`, `app/schemas/s10_full_apply.py`, one new `migrations/versions/*`, `tests/test_s10_full_apply_{domain,migration}.py`; T01B owns `app/services/s10_chunk_plan.py` + `tests/test_s10_chunk_plan.py` (pure planner, no persistence/API/renderer).
- T01C onward serialized: shared `app/services/s10_full_apply.py`, `app/workflow/s10_full_apply_jobs.py`, `app/api/routes/s10_full_apply.py`, wiring in `app/api/app.py`/`deps.py`.

## Task map (for prompt copy — verbatim)

| Task | Outcome | Allowed write scope (production) | Binary acceptance (must grep before terminal) |
|------|---------|----------------------------------|----------------------------------------------|
| T01A | Durable FullApply domain + checkpoint contract | models/s10_full_apply, schemas/s10_full_apply, 1 migration, 2 test files + session/output | one live head, round-trip isolated DB, immutable ApplyCheckpoint linkage, no `.partial` publication, deterministic chunk boundaries |
| T01B | Deterministic shot/layer chunk planner | s10_chunk_plan.py + test | byte-identical plan 2x, exact core coverage + explicit overlap, no gap/drift/off-by-one, pinned routes, ambient-path invariant |
| T01C | Durable orchestration + API | s10_full_apply service/workflow/route API + deps wiring + 2 tests | additive idempotent API, async (no sync render), durable checkpoint before stop, resume without rerender, cancel/retry isolation, dedupe lineage, atomic publish |
| T02 | Multi-role 1-4 independent | s10_multi_role_apply + bounded edits in s10_full_apply jobs | group fixture with occluder, per-role evidence, no cross-role mutation, contact/z-order survives stitch |
| T03 | Affected-only partial recompute | s10_recompute + bounded edits | closure exact, unaffected IDs/SHA reuse, new generation for affected, no-op dedupe |
| T04A | Structural compare gate | s10_structural_compare + bounded edits | frame/timebase/cut + trajectory/scale/rotation/contact thresholds, zero z-inversion, fail-closed on missing metric |
| T04B | Apply UX (tiếng Việt) | `frontend/src/features/apply/**`, route, `lib/api.ts`, `AppNav.tsx`, e2e `s10-apply-ui` | disabled reason, progress truth survives reload, evidence gating, dark helper text gray-400 11px+ |
| T04C | Prod Demo->Apply restart x2 | 2 e2e files + playwright config + deterministic fixture under `tests/fixtures/s10_full_apply/**` + `output/s10/**` | no mock, real renderer, cut/z-order checks, owned restart with PID ownership, affected-only proof, 2 isolated DB/roots reuse same build manifest |

## Model/heartbeat contract for S10

- Workers: `model: meta` via `http://127.0.0.1:20128/v1`, `reasoning: max`, `fallback OFF`, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`, `api_mode: codex_responses`.
- One Task ID = one new session; correction = resume exact owner with same model.
- Heartbeat: 30' cadence + instant on lane exit/blocker (supersedes 5' Muse phase). Continuous 24/24 bounded `process poll`, never `sleep 570`.

## ETA reporting contract (mid-turn `estimate` signal)

User signal `xong thì estimate cho tôi bao giờ xong S10` arrived as `[OUT-OF-BAND USER MESSAGE]` mid-terminal turn. Required handling: in the SAME first Manager reply, emit lead-with-status + `date`-anchored wall table — never defer to next heartbeat. Columns: Phase | Task | Công việc chính | Est. wall (ideal) | ETA ideal | ETA thực tế (+1 correction round as S09 C3-C7 pattern).

Anchored 27/08 22:13 +07:
- Ideal `SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` ~28/08 12:00 (~14h wall: T01A/B 60-90' parallel + six Js 15' + T01C/T02/T03/T04A/T04B 60-90' each + T04C 90-150' + exit gates 40-60').
- Realistic +1 correction round (every S09 C3-C7 needed 1-2 extra loops after green gates): 28/08 18:00-23:00 + separate Codex review gate.
- If `chạy đi` + ETA arrive together, dispatch confirmation and ETA table MUST co-occur.

## Preflight checklist (before T01A/T01B)

1. `RULES_LOADED` 180/SHA + `WORKSPACE_INSTRUCTIONS_LOADED` + SESSION_PROTOCOL/ROADMAP/TARGET_PROFILE/S09_C7_R2 review.
2. Discover live `codex/s08-integration HEAD d3f6f79`, dirty attribution, `MOTIONFORGE_DATABASE_URL=UNSET`, one Alembic head, J1-v4 13/13 baseline.
3. Inventory baseline SHAs for `models.py`, migration head, `app/api/app.py`, `channels.json`, `data/**`.
4. Freeze `S10-SESSION_REGISTRY.md` + per-task `TASK.md/LOG.md/REPORT.md` under `s08-integration`, then dispatch T01A + T01B as `hermes -z "$(cat prompt.txt)" -m meta --yolo` background.

## Sprint-exit gates (serialized, mutex, zero writers)

1. J1-v4 13/13 direct + EOL; 2. `tests/test_s10*.py` + retained S09 T06 suite ×2 isolated basetemp; 3. Ruff + mypy + one head; 4. OpenAPI additive; 5. TSC + ESLint + Next build (8888 fallback); 6. T04C Chromium Run1→Run2 sequential isolated roots reusing same build manifest; 7. SQLite attempt/reuse truth; 8. `git diff --check` + attribution + port/process audit.
