# Sprint S08 — Manager progress notes (through T03 verified, T04 running)

Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
Branch `codex/s08-integration`, HEAD base `a43b20da742996bafcb2f9d1ac57b10d3f1a5204`
(uncommitted integrated P00 state). Tracking:
`output/SPRINT_S08_SESSIONS_TRACKING.md` (worktree).

## Session lineage (one session per Task ID)

| Task | Session | Rounds | Manager verify |
|---|---|---|---|
| T01 object-role-domain | `20260805_235138_61ad7a` | run → resume (bg-child incident) → C1 (Codex 5 findings) | 36/36 focused, 41/41 S05, 160/160 reg |
| T02 candidate-extraction | `20260816_140218_d4c20a` | fresh, exit 0, 1h7m | 35/35 focused, 36/36 T01, 41/41 S05, 160/160 reg, migration head f2a3b4c5d6e7 |
| T03 grouping-api | `20260816_151439_21e306` | fresh, exit 0, 1h40m | 25/25 focused, 71/71 T01+T02, 41/41 S05, 160/160 reg, migration head f3a4b5c6d7e8 |
| T04 object-gallery | fresh (launched ~17:03, proc_c72fe563f3a4) | in progress | pending |

## Codex T01 findings (verbatim essence) → C1 fix mapping

1. Occurrence route ownership: PATCH `/roles/{role_id}/occurrences/{occurrence_id}`
   discarded role_id → must fail closed (role-A URL cannot touch role-B row).
   Fix: route binds role_id; repo asserts exact role+workspace ownership.
2. Supersession ownership/validity: cross-workspace supersession succeeded →
   target must exist + same workspace/project/video/source_generation; reject
   self-ref and terminal targets. Fix: `_validate_supersession_target` (6 tests).
3. Real atomic CAS: read-compare-write → UPDATE WHERE id+workspace+expected
   revision, `scalar_one()`, NoResultFound → read current revision → conflict;
   genuine 2-thread sync test (exactly one winner). Fix: `update_role` stmt +
   `test_concurrent_cas_atomic_exactly_one_writer_wins`.
4. Idempotency collision: replay only equivalent canonical request; different
   project/video/generation/payload → stable 409, never another resource.
   Fix: `_assert_equivalent_role_request` + 5 tests.
5. Preserve all behavior; no skips/weakens.

## T03 incident (resolved — see references/s08-t03-main-db-migration-incident.md)

Bare `TestClient(app)` repro during 500-debug ran lifespan migrations against
MAIN `data/motionforge.db` (311296→417792 B). Worker self-detected via
protected-data gate and restored byte-exact from backup
`data/motionforge.db.bak-20260816T091802-4174cef8` (SHA verified == current
DB SHA `67d5c7736042b9d4e4b7249e611bea3e85124df0317fafe6aaf32405ff79f2e6`,
content = d5e6f7a8b9c0/17 tables/no object_role). Enforced in T04+ prompts:
every backend repro through conftest fixture; bare TestClient forbidden.

## Manager verification recipe used (repeat for T04+)

```bash
# focused suite (per task, cache-disabled, Windows-native basetemp)
python -m pytest tests/test_<task>.py -q -p no:cacheprovider --basetemp=C:/Users/Admin/AppData/Local/Temp/s08tx-mgr-focused
# dependency suites
python -m pytest tests/test_object_intelligence_domain.py -q -p no:cacheprovider --basetemp=.../s08tx-mgr-t01
# S05 41-suite — SHALLOW basetemp (MAX_PATH lesson)
python -m pytest tests/test_s05_*.py -q -p no:cacheprovider --basetemp=C:/Users/Admin/AppData/Local/Temp/s08tx-mgr-s05
# persistence regressions
python -m pytest tests/test_persistence_bootstrap.py tests/test_durable_job_persistence.py tests/test_project_crud.py tests/test_video_item_crud.py -q -p no:cacheprovider --basetemp=.../s08tx-mgr-reg
# migration round-trip (alembic.ini has NO url by design; -x unsupported)
# use a SUBSHELL or unset after, so the env var never leaks into later pytest runs
(export MOTIONFORGE_DATABASE_URL=sqlite:///C:/Users/Admin/AppData/Local/Temp/s08tx-mgr-migration.db
 python -m alembic upgrade head && python -m alembic downgrade <prev> && python -m alembic upgrade head)
```

Protected checks after every round: MAIN `channels.json` SHA-256
`dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` (certutil),
MAIN `data/motionforge.db` 311296 bytes, MAIN non-watcher git count 45
(`git status --short | grep -vc 'scripts/watch-s08'`), S06 tree 45. Worker
prompts must end "FOREGROUND ONLY ... stop after SUBMITTED and exit".

## Launcher/watcher per task

- `output/run-s08-t0N-fresh.ps1` / `run-s08-t0N-cN.ps1` (resume: add
  `--resume <exact-session-id>`); prompt SHORT, no double quotes.
- **Model directive (user, 2026-08-16):** T01–T04 workers ran
  `ocg/deepseek-v4-flash` (sprint-pinned). FROM T05 ONWARD new worker
  sessions use `ocg/deepseek-v4-pro` with reasoning max
  (`hermes config set agent.reasoning_overrides.ocg/deepseek-v4-pro max`;
  smoke-test exact id before first launch). Corrections resume the task's own
  session/model; a running session is NOT switched mid-flight.
- MAIN `scripts/watch-s08-t0N.sh` → syncs to MAIN
  `output/hermes-task-logs/`; kill old watcher when its round ends; reopen
  preview on the new LIVE.txt.
- 30s after launch: MAIN non-watcher count unchanged + log mtime growing.

## Known transient failures (do not misdiagnose)

- Gateway HTTP 502 on ~234K-token context at exit: worker may have FINISHED
  (REPORT=SUBMITTED, all gates logged) — smoke-test model, only resume if a
  criterion is unmet.
- `RuntimeError: No database URL configured` from alembic = protection, not bug.
- Deep basetemp >260 chars → MAX_PATH failures in S05 wiring test → shallow.
- Mass "no such table: workspace" failures right after a manual migration
  check = manager-side env contamination (MOTIONFORGE_DATABASE_URL leaked) —
  `unset` it first, then re-run.
