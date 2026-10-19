# S10-C4 Authority-Fence Correction — preflight recipe (verified 2026-08-29)

Manager-correction round for `S10-C4 AUTHORITY_SEMANTICS_EXIT_CORRECTION_MANAGER_2026-08-29.md`.
Serial DAG: `PREP -> T01C-C6-authority/fence -> J1 -> T03-C4-correction -> J2 -> T04A-C4-measurement -> J3 -> T01C-C7-static -> J4 -> T04C-C3 -> EXIT`.
Exact owners: T01C `20260828_003035_859fe5`, T03 `20260828_011920_b79bd6`, T04A `20260828_014304_25d94a`, T04C `20260828_023122_76b87e`.

## 1. Rules + full context load (before ANY preflight/dispatch)

Order used and sufficient for C4 (all must be read IN FULL, then confirm no `BLOCKED_RULES`):
1. `docs/pm/HERMES_AUTOPILOT_RULES.md` (180 lines, SHA `987386c5…`) → report `RULES_LOADED` with path + line count + SHA-256 + section list + live git state
2. `AGENTS.md`, `frontend/AGENTS.md`
3. `docs/pm/CODEX_PM_HANDOFF.md` (590L), `ROADMAP.md` (457L), `SESSION_PROTOCOL.md` (147L), `README.md`, `TARGET_PROFILE_2D_SOURCE_LOCKED.md` (526L)
4. S10 Manager prompts C0..C3 (`S10_FULL_APPLY_MANAGER_2026-08-27.md` 322L, `S10_C1…2026-08-28.md` 145L, `S10_C2…2026-08-28.md` 128L, `S10_C3…2026-08-29.md` 120L) + `CODEX_PROJECT_PM_CONTINUATION_S10_C2_REVIEW…` (159L)
5. Codex reviews C0..C3 (`reviews/S10_C0/C1/C2/C3_PM_REVIEW*.md`) — C3 is the binding verdict
6. `docs/pm/sprints/S10-SPRINT_REPORT.md` + `docs/pm/sessions/S10-SESSION_REGISTRY.md` (append-only; detect stale/false claims — C3 registry claimed "ALL 9 GATES GREEN" while itself noting mypy 15 errors; must be superseded, not rewritten)
7. FULL TASK/LOG/REPORT of the four C4 owners (T01C, T03, T04A, T04C) — 12 files under `docs/pm/sessions/S10-<task>-*/`

The C3 review's six finding groups are the frozen C4 scope — the manager must be able to recite them from the review file, not from memory.

## 2. Stable preflight command set (all verified live this round)

- Git state BOTH trees: `git -C <worktree> branch --show-current && git rev-parse HEAD && git status --porcelain | wc -l` and same for MAIN (`C:/Users/Admin/MotionForge2D`, branch `master`). C4 live state: worktree `codex/s08-integration` @ `d3f6f79…` (45 dirty — S10 write-set), MAIN @ `f0ee4bd…` (78 dirty — user/foreign, PRESERVE).
- DB guard: `env | grep -i MOTIONFORGE` must be empty → `MOTIONFORGE_DATABASE_URL UNSET`.
- Ports/listeners: `netstat -ano | grep -E ':(8201|3015|8888|8099|3014|8212|20128)[[:space:]]' | grep -i LISTENING` — 20128 (9Router daemon) is EXPECTED; 8201/3015/8888/8099/3014/8212 must be free.
- Process audit: inline `powershell -NoProfile -Command` with `$_` gets eaten by MSYS bash — write a `.ps1` via `write_file` and run `powershell -NoProfile -ExecutionPolicy Bypass -File <ps1>`. Zero S10 writer = no process carries the four owner session IDs; foreign daemons (9Router, hermes desktop/serve, MCP, Codex CUA) must NOT be killed.
- J1-v4 re-hash: `python scripts/j1v4_rehash.py` (packaged with this skill) → 13/13 + EOL 12 LF + composite.py CRLF, exit 0.
- BUILD_ID: `output/s10/_build/frontend-build-manifest.json` → C4 live `KIWvay6FvLdiWmVFduSMG` (registry C3 claim vs manifest must be re-checked, never inherited).
- Baseline SHA of the C4 write-set: `sha256sum` the 10 production files (jobs/structural/recompute/multi_role/full_apply/chunk_plan/schemas/persistence/routes/job_reconciler) and record before dispatch.
- TASK/LOG/REPORT mtimes of the four owners captured as evidence baseline (detect worker writes later).

## 3. Source-sweep baseline BEFORE dispatch (proves the tree is in the reviewed defective state)

Grep the EXACT defect strings/lines the binding review cites, to confirm the baseline is legitimate and give post-correction a measurable zero target. C4 sweeps (all hit before correction):
- `grep -rn '_c4_stage_source_and_assets' app/` → routes 38/261/557
- `grep -rn 'ckpt-fallback' app/services/s10_recompute.py` → 681 (zero-hash fallback)
- correction-id perturb: `grep -n 'perturb\|affected_region' app/services/s10_recompute.py` → 735–754
- fixed metric arrays / mirroring: `grep -n '0.05\|mirror\|source_cut_frames' app/api/routes/s10_full_apply.py app/services/s10_structural_compare.py` → routes 1250 (mirror) + 1315–1327 (fixed arrays)
- `grep -rn 'stage_c4' app/ frontend/e2e/ output/s10/run-s10.js` → reconciler 576/595 + spec 596–601
- `grep -n '_input_changed\|INPUT_CHANGED' app/workflow/job_reconciler.py` → 607 S10 bypass
- direct requeue: `grep -rn '_force_requeue\|lease_expire' frontend/e2e/ output/s10/run-s10.js`

If a cited defect is ABSENT at preflight, that is a review/baseline mismatch to report — do not silently adapt.

## 4. Model route — probe matrix (C4 verified)

C4 prompt text demanded `-m deepseek-v4-flash` ("không dùng --provider custom") — WRONG on this machine. Probe BEFORE dispatch:
- `hermes -z "ping" -m deepseek-v4-flash --yolo` → FAIL `No usable credentials found for provider 'deepseek'` (no provider named `deepseek` in `~/AppData/Local/hermes/config.yaml`)
- `hermes -z "ping" -m deepseek-v4-flash --provider custom --yolo` → HTTP 404 openrouter (misresolve)
- `hermes -z "ping" -m ocg/deepseek-v4-flash --yolo` → `pong ✅` (config `providers.custom.model = ocg/deepseek-v4-flash`)
- Confirm effective route in `~/AppData/Local/hermes/logs/agent.log`: `model=ocg/deepseek-v4-flash provider=custom`
- `hermes model list` does NOT exist (`hermes model` is an interactive picker) — probing with `-z "ping"` is the only route check.
- Dispatch verbatim: `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner_id> -z "$(cat prompt.txt)" -m ocg/deepseek-v4-flash --yolo` (no provider flag).

## 5. Worker packet + dispatch

- Write prompt to `output/s10/c4/<lane>/prompt.txt` via `write_file` (never heredoc for JSON-heavy prompts). Prompt must carry: RULES_LOADED requirement, exact allowed/forbidden scope, frozen binary requirements verbatim from the Codex review, model route, verification commands, evidence bundle, terminal = `TASK_SUBMITTED` only.
- `mkdir -p` the log dir BEFORE redirecting; dispatch `terminal(background=true, notify_on_complete=true)`; verify `↻ Resumed session` lands in dispatch.log before treating as started.
- After dispatch: confirm the `↻ Resumed session <id>` line, then END THE TURN (no polling loop — in-flight budget contention lesson).

## 6. T01C-C6 execution + J1 gate (verified 29/08 evening)

Worker R1 (iteration-cap mid-verify, honest RUNNING) → R2 (same prompt, same owner) → `STATUS: TASK_SUBMITTED`. Code changes verified on disk:
- routes: `_c4_stage_source_and_assets` deleted (sweep = 0); added `_resolve_persisted_render_authority` / `_validate_managed_artifact` / `_layer_ids_from_mapping` / `_win_long_path` — server resolves source artifact + pack/version/asset from persisted rows and pins id/rel/SHA/size/timebase BEFORE enqueue; missing/tampered/cross-workspace → 422 fail-closed before commit (no orphan run/job).
- reconciler: S10 bypass gone — `_input_changed` compares `manifest_fingerprint(job.input_manifest)` against the fingerprint stored on the `created` event; ANY post-creation mutation (incl. source/asset pins) → `INPUT_CHANGED`, zero resume render/publication. Read the code to confirm the fence is real (grep alone showed only a docstring comment).
- long-path: `_lp()` applied to managed_root at handler top so root + children share the `\\?\` prefix (containment check `renderer_contract.py:542` fails if output is prefixed but root is not, with `LongPathsEnabled=0`).
- New C6 tests: 6 API (purity sweep, pins binding, missing/tampered/cross-workspace fail-closed, retry reuse) + 3 workflow (INPUT_CHANGED fencing, restart unchanged manifest, long-path >260 zero orphan `.staging`).

Manager J1 gate (independent, NOT worker report): targeted API+workflow `32 passed` ×2 fresh basetemps; full `tests/test_s10*.py` = `179 passed` EXIT 0 (~209s, fresh nested basetemp) — worker's 179 claim matched; Ruff F* touched = All checks passed; mypy 9-file = T01C **0** with 12 carry-forward in exactly T03/T04A-owned files (structural_compare 802/807/812 + recompute 754/890/918/919); J1-v4 13/13 + EOL PASS; alembic single head `a10b11c12d3e`; `git diff --check` EXIT 0 (only CRLF warning for playwright-report); porcelain 45 = allowlist + pre-existing.