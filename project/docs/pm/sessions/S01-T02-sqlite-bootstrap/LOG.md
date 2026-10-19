# S01-T02 - Execution Log

Append-only.

| Timestamp | Action/Decision | Command or files | Result/Evidence |
|---|---|---|---|
| 2026-08-03 16:12 +07:00 | Session packet created | TASK/START_PROMPT/LOG/REPORT/PM_REVIEW | READY; depends on approved S01-T01 |
| 2026-08-03 16:20 +07:00 | Required reading complete | SESSION_PROTOCOL, PERSISTENCE_DOMAIN_CONTRACT, QUALITY_BASELINE, pyproject.toml, app/config.py, tests/conftest.py | Contract V1 read; scope boundaries confirmed |
| 2026-08-03 16:20 +07:00 | Baseline git status inspected | `git status` | Pre-existing changes preserved: `channels.json` (modified, 224 insertions), `docs/pm/ROADMAP.md` (modified, 4 lines); untracked: `docs/architecture/`, `docs/pm/sessions/S01-T01-domain-contract/`, `docs/pm/sessions/S01-T02-sqlite-bootstrap/`. No write outside allowed scope |
| 2026-08-03 16:21 +07:00 | Baseline tool state | `python -m alembic --version` | alembic NOT installed (module missing) -> installed alembic 1.18.5 via pip (runtime dep requirement) |
| 2026-08-03 16:21 +07:00 | Baseline targeted test | `python -m pytest -q tests/test_persistence_bootstrap.py` | "no tests ran" (file does not exist yet) |
| 2026-08-03 16:21 +07:00 | Baseline ruff | `python -m ruff check app tests` | All checks passed (ruff 0.16.0) |
| 2026-08-03 16:21 +07:00 | Baseline mypy | `python -m mypy app` | Success: no issues in 41 source files (mypy 2.3.0; Gate 4 currently passes — better than S00 documented baseline) |
| 2026-08-03 16:25 +07:00 | Implemented persistence package | `app/persistence/{__init__,engine,models,revision}.py` | Engine factory with FK pragma + busy timeout (AC1/AC2); 8 S01 ORM models (AC3); schema-revision guard (AC5) |
| 2026-08-03 16:25 +07:00 | Alembic bootstrap | `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako` | Explicit migration path; refuses to run without explicit DB target |
| 2026-08-03 16:25 +07:00 | Alembic autogenerate quirk | `python -m alembic revision --autogenerate` | alembic 1.18.5 CLI autogenerate produced empty `pass` migrations despite detecting 14 ops programmatically; hand-wrote initial revision `a1b2c3d4e5f6` instead |
| 2026-08-03 16:25 +07:00 | Initial migration | `migrations/versions/a1b2c3d4e5f6_initial_s01_persistence_schema.py` | 8 tables, FKs, CHECK constraints, indexes; `length()` not `char_length()` (SQLite); NOCASE on channel.name; no Job tables |
| 2026-08-03 16:26 +07:00 | Model fix | `app/persistence/models.py` | Entities now inherit TimestampMixin/ArchivableMixin (were missing — schema drift); Artifact uses `trashed_at` per contract |
| 2026-08-03 16:27 +07:00 | Tests written | `tests/test_persistence_bootstrap.py` | 15 tests: AC1 engine no-file-on-import, AC2 FK+busy timeout, AC3 schema shape/no jobs, AC4 upgrade x2, AC5 reopen/FK-fail/newer-revision |
| 2026-08-03 16:28 +07:00 | Targeted tests | `python -m pytest -q tests/test_persistence_bootstrap.py` | 15 passed |
| 2026-08-03 16:29 +07:00 | Direct alembic CLI on temp DB | `MOTIONFORGE_DATABASE_URL=... python -m alembic upgrade head` | Upgraded temp DB to head; downgrade base + re-upgrade OK; `alembic check` = "No new upgrade operations detected" |
| 2026-08-03 16:29 +07:00 | ruff | `python -m ruff check app tests` | All checks passed |
| 2026-08-03 16:29 +07:00 | mypy | `python -m mypy app` | Success: no issues in 45 source files |
| 2026-08-03 16:29 +07:00 | Full pytest | `python -m pytest -q -m "not gpu and not sam2 and not integration"` | 175 passed, 8 skipped, 7 deselected (baseline was 141 passed) |
| 2026-08-03 16:43 +07:00 | Quality baseline (7 gates) | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | OVERALL: PASS (exit 0) — all 7 gates PASS including Gate 4 typing and Gate 6 frontend lint |
| 2026-08-03 16:43 +07:00 | Scope/preservation check | `git status` + `git diff --stat` | Pre-existing `channels.json` (224 insertions) and `docs/pm/ROADMAP.md` (4 lines) unchanged; all new files within allowed write scope; temp DBs under OS temp dir removed |
| 2026-08-03 16:44 +07:00 | REPORT updated, status SUBMITTED | `docs/pm/sessions/S01-T02-sqlite-bootstrap/REPORT.md` | Submitted for PM review |
| 2026-08-03 16:50 +07:00 | PM review: CHANGES_REQUESTED | `docs/pm/sessions/S01-T02-sqlite-bootstrap/PM_REVIEW.md` | 4 bounded corrections: artifact FK constraints, env.py FK pragma, focused tests, re-validation |
| 2026-08-03 16:51 +07:00 | Fix 1: artifact FKs in ORM | `app/persistence/models.py` | `channel.avatar_artifact_id` and `video_item.source_artifact_id` now `ForeignKey("artifact.id", ondelete="RESTRICT")` |
| 2026-08-03 16:51 +07:00 | Fix 1: artifact FKs in migration | `migrations/versions/a1b2c3d4e5f6_initial_s01_persistence_schema.py` | Added `fk_channel_avatar_artifact` + `fk_video_item_source_artifact` (RESTRICT) in-place (initial revision not shipped) |
| 2026-08-03 16:52 +07:00 | Fix 2: env.py uses shared engine factory | `migrations/env.py` | `create_engine_for_path` replaces raw `create_engine`; Alembic online connection now enables `PRAGMA foreign_keys=ON`; verified pragma = 1 on migration-style connection |
| 2026-08-03 16:53 +07:00 | Fix 3: focused tests added | `tests/test_persistence_bootstrap.py` | 3 new tests: channel avatar FK rejects missing artifact, video_item source FK rejects missing artifact, Alembic online connection FK enabled |
| 2026-08-03 16:54 +07:00 | Fix 4: re-validation | targeted + full pytest + alembic + baseline | 18/18 targeted; full 178 passed, 8 skipped, 7 deselected; alembic upgrade/check on temp DB zero drift; FKs present with RESTRICT in PRAGMA foreign_key_list; ruff/mypy/git diff --check pass; 7-gate baseline OVERALL PASS (exit 0) |
| 2026-08-03 16:55 +07:00 | REPORT updated, status SUBMITTED | `docs/pm/sessions/S01-T02-sqlite-bootstrap/REPORT.md` | Resubmitted after PM corrections; temp DBs removed; pre-existing changes preserved |

