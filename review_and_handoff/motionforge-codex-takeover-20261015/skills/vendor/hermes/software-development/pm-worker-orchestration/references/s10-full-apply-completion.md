# S10 Full Apply — 8-Owner Completion (verified 2026-08-28 04:12 +07)

Source sprint: `docs/pm/prompts/S10_FULL_APPLY_MANAGER_2026-08-27.md` — 8 owner sessions, DAG `PREP -> (T01A || T01B) -> J1 -> T01C -> J2 -> T02 -> J3 -> T03 -> J4 -> T04A -> J5 -> T04B -> J6 -> T04C -> SPRINT_EXIT` — Manager `20260827_220742_de1883` meta/max/TTFB900 fallback OFF — worktree `s08-integration` HEAD `d3f6f79` (S09 CODEX_APPROVED CLOSED, J1-v4 13/13).

## Owner sessions & evidence (all TASK_SUBMITTED -> MANAGER_VERIFIED)

| Task | Session | Wall | Evidence | Notes |
|---|---|---|---|---|
| T01A Durable domain + checkpoint | `20260827_234001_9d7f39` + resume `proc_fde510fe01a5` pid 28140 (gateway 524 retry) | 23:39-00:22 | 15 domain + 6 migration = 21 passed x2 (isolated DB/basetemp, MOTIONFORGE_DATABASE_URL UNSET), migration `a10b11c12d3e` head down `b3c4d5e6f7a9` one head verified `cd s08-integration && alembic heads` | Gateway 524 at 23:46 -> RUNNING_RETRY_WAIT per Rules §7 -> same-session resume at 23:58 after 5' wait, no new session |
| T01B Chunk planner (pure) | `20260827_234004_25fb5c` | 23:39-23:56 | 26 passed x2, deterministic byte-identical 2x, exact core coverage + explicit overlap, no gap/drift, pinned routes, ambient invariant, fail-closed 9 cases | Disjoint with T01A (persistence vs pure planner) — only parallel pair allowed |
| T01C Orchestration + API | `20260828_003035_859fe5` + corr1 `proc_37e79ea73621` + corr2 `proc_d511bf07c7a7` | 00:31-04:12 (3 dispatches) | 7 api + 4 workflow = 11 passed x2 final (54s each) | P0x2: (1) handler missing in `job_service.py` (2) commit-before-enqueue + swallowed busy |
| T02 Multi-role 1-4 | `20260828_010435_b24638` | 01:04-01:12 | 30 passed x2, group fixture with occluder, per-role evidence, isolation, contact/z-order survives stitch | Bounded shims in `s10_full_apply.py` / `s10_full_apply_jobs.py` (untracked new files, diff empty expected) |
| T03 Partial recompute | `20260828_011920_b79bd6` | 01:19-01:36 | 9 passed x2, affected closure deterministic, unaffected preserved exact IDs/SHA, stale/cross-project fail-closed, restart resume | Service creates 3 tables via CREATE IF NOT EXISTS (no Alembic migration) |
| T04A Structural compare gate | `20260828_014304_25d94a` | 01:42-01:54 | 27 passed x2, frame/timebase/shot/cut, trajectory 0.5/1.0 + scale 3% + rotation 3° + contact 1.0, zero z-inversion, REVIEW_REQUIRED vs BLOCKED with actionable pointer | Pure deterministic, no DB |
| T04B Apply UX (tiếng Việt) | `20260828_020206_b1f8af` | 02:02-02:24 | TSC 0, ESLint apply/** 0, Next build Compiled successfully (9 routes inc /apply), 6 playwright --list, 8888 fallback preserved, dark helper text gray-400 11px+ | P2 docs: no TASK/LOG/REPORT standalone files, only `output/s10/t04b/*.log` — carried as P2 at J6 |
| T04C Prod restart x2 | `20260828_023122_76b87e` + resume `proc_c2459cfe7f60` + fix `proc_c4b759326c2c` + retry `proc_f495e63bdfbb` | 02:31-04:08 (4 dispatches) | 2x Chromium sequential distinct DB/runtime/output (`output/s10/r1/run1` vs `run2`) same manifest `g3s0EKHByfzsFsRNZpWRI` 201 chunks validator 7/7 before each, 1/1 each, checkpoint/restart/partial/structural DB truth | Forbidden to touch production code — reports via `BLOCKED_WITH_FINDINGS` file:line |

## Join gates (all MANAGER_VERIFIED before next dispatch)

- J1 (00:30): 47 passed x2 (21+26), alembic `a10b11c12d3e` single head, mypy clean, diff-check 0, E501 P2 carry-forward on `s10_chunk_plan.py`
- J2 (01:00): 11 passed x2, total 58, 6 bullets (202 queue outside request, checkpoint durable, resume skips verified)
- J3 (01:17): 30 passed x2, total 88, 5 bullets
- J4 (01:40): 9 passed x2, total 97, 5 bullets
- J5 (02:00): 27 passed x2, total 124, 5 bullets
- J6 (02:30): T04B frontend verified (TSC+ESLint+build+list+8888+dark) — P2 docs only

## Sprint-exit gates (04:12 +07, zero writers, mutex)

1. J1-v4 13/13 direct bytes, EOL 12 LF + 1 CRLF (`composite.py`), manifest v4 `ee10e55a` frozen `2026-08-25T23:15:00+07`
2. Full S10 suite 124 passed (isolated DB/basetemp, 79 SAWarning) — `pytest tests/test_s10*.py -v -p no:cacheprovider --override-ini="addopts=" --basetemp=$(mktemp -d)`
3. Ruff S10 write-set P2 E501 (SQL/doc literals) — `job_service.py` All checks passed; mypy 7 pre-existing misc/no-any-return on try/except None guards (same before sprint)
4. Migration one head `a10b11c12d3e`, OpenAPI additive 6 new `/full-apply` routes (259 total, no S09 lost), frontend TSC 0 / ESLint 0 / Next build 0, `git diff --check` 0, `channels.json` / `data/**` untouched
5. T04C 2x Chromium distinct fresh DB/runtime/output reuse same manifest, owned PIDs exit, 3014 preserved 22436, 8201/3015 FREE after run2

## Corrections (exact-owner resumes, no new sessions)

- **Gateway 524 (T01A):** `isRetryable:true` at 23:46 — per Rules §7 `RUNNING_RETRY_WAIT` 5' then `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume 20260827_234001_9d7f39 -z "$(cat prompt.txt)" -m meta --yolo` — same prompt/TTFB/model, session context preserved, mid-flight progress not lost.
- **T01C handler missing (T04C -> T01C):** `app/workflow/job_service.py` registered scene/proxy/discover/recompute/attach_audio but not `s10_full_apply` — allowlist had `app/api/app.py (+deps)` but not `job_service.py`. Fix: `from app.workflow.s10_full_apply_jobs import register_s10_full_apply_handler` + `register_s10_full_apply_handler(self._worker)` after `register_attach_original_audio_handler`.
- **T01C commit-before-enqueue + swallow (T04C Run1 1.2m fail):** `app/api/routes/s10_full_apply.py:180-195` inner `except Exception: pass` swallowed SQLite busy; job created inside uncommitted `session` tx held whole-DB lock. Fix: commit run before `create_job` + narrow to `IntegrityError` duplicate-key only (UNIQUE/idempotency in str), else raise. Re-verify 11x2 now durable checkpoint observed.
- **T04C harness parse:** API returns `{projects:[]}` / `{videos:[]}` not `{items:[]}` — seeder vs spec shape mismatch. Fix: `raw.projects ?? raw.items ?? raw ?? []` both sites. Also rename `_build` stable (never mutate after Run1).

## Reusable checklist for next S10-like sprint

- **Dispatch:** `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes -z "$(cat output/s10/<lane>/prompt.txt)" -m meta --yolo` via `terminal(background=true, notify_on_complete=true)` — never inline printf/heredoc with Vietnamese diacritics (EOF break: use `write_file`), never shell `&`.
- **Alembic CWD trap:** `alembic.ini` `script_location = migrations` is relative — run `cd s08-integration && alembic heads` not from MAIN (4 vs 17 files hidden).
- **Pytest invocation trap:** `pyproject.toml` addopts breaks bare `--cache-clear` — use `pytest <tests> -v -p no:cacheprovider --override-ini="addopts=" --basetemp=$(mktemp -d)` for every x2 gate.
- **Heartbeat:** 30' + instant on lane exit/blocker — every `go+ETA` gets `date`-anchored wall table same reply; `sao thấy dừng rồi?` means state which wait reason (`đang chờ T0x exit để mở Jx` / `terminal xong đang chờ Codex`), not idleness.
- **Terminal:** `SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` only — no APPROVED/CLOSED, no commit/push/merge, no S11/S13.

Terminal: SPRINT_SUBMITTED 2026-08-28 04:12 +07 — 124 passed, J1 13/13, BUILD_ID `g3s0EKHByfzsFsRNZpWRI`, awaits Codex independent review @session:default/20260827_220742_de1883.
