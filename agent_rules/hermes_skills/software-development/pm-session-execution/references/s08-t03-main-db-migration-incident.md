# S08-T03 Incident — Bare TestClient(app) Migrated the MAIN Production DB

**Task:** S08-T03 cross-scene grouping API (worker session `20260816_151439_21e306`).
**Date:** 2026-08-16. **Status:** remediated byte-exact; manager re-verified; recorded in LOG/REPORT + sprint tracking.

## What happened

While debugging a 500 error in the grouping API, the worker ran a quick repro
using a bare `TestClient(app)` constructed inline, NOT the conftest `client`
fixture. The FastAPI lifespan ran alembic migrations against the DEFAULT
database URL, which resolved to MAIN `C:\Users\Admin\MotionForge2D\data\
motionforge.db` — the production user database. The S08 migrations then ran
against MAIN in place.

Evidence of the corruption (worker's protected-data gate caught it):
- MAIN `data/motionforge.db`: 311296 B → 417792 B.

## Recovery (worker) + independent manager verification

1. Worker restored from the backup-policy file
   `data/motionforge.db.bak-20260816T091802-4174cef8` (auto-created by the app
   before starting — size 311296 B, matching baseline).
2. Manager independently re-verified:
   - `certutil -hashfile data/motionforge.db SHA256` =
     `67d5c7736042b9d4e4b7249e611bea3e85124df0317fafe6aaf32405ff79f2e6` —
     IDENTICAL to the backup file's SHA (byte-exact restore, not just size).
   - Content check on the live DB: `alembic_version` = `d5e6f7a8b9c0` (the
     pre-S08 MAIN head), 17 tables, `object_role` ABSENT, size 311296 B —
     matches the P00 baseline exactly.
   - `channels.json` SHA-256 `dd7aae26…555` unchanged.
3. All later worker repros went through the pytest fixtures (isolated temp
   DBs). The T03 focused suite (25 tests) and all regressions pass on
   isolated basetemps.

## Root cause

FastAPI lifespan (which runs migrations on startup) + a bare TestClient
without the conftest fixture's dependency patching = migrations execute
against the production DB. The conftest `client` fixture exists precisely to
isolate this (it patches `deps._config` to a temp root with a temp DB).

## Lessons enforced in T04+ prompts

- "Never use bare TestClient(app) outside the conftest client fixture — it
  can migrate the MAIN database via lifespan. All backend repros/tests MUST
  go through the pytest fixtures."
- Protected-data gates must check DB SIZE AND CONTENT (alembic_version +
  table list), not just size, because an in-place migration changes size
  unambiguously but a restore must be proven by SHA equality with the backup.
- This is a process-safety deviation, not a code defect: the remediation is
  complete and no source change was needed; the incident is disclosed in the
  task LOG/REPORT and the sprint report for Codex.
