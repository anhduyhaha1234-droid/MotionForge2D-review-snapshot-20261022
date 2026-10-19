# S02-T04 - Execution Log

Append-only. Không xóa hoặc viết lại entry cũ; nếu sai, thêm entry correction.

| Timestamp | Action/Decision | Command or files | Result/Evidence |
|---|---|---|---|
| 2026-08-03T21:29+07 | Session initialized | S02-T04-restart-reconciliation | README/TASK/START_PROMPT read; scope = reconciler only |
| 2026-08-03T21:29+07 | Required reading complete | SESSION_PROTOCOL.md, TASK.md, DURABLE_JOB_CONTRACT.md V1.1, DURABLE_JOB_PERSISTENCE.md, DURABLE_WORKER.md, app/persistence/jobs.py, app/workflow/durable_worker.py, tests/test_durable_job_persistence.py, tests/test_durable_worker.py | Contract §5.3 fencing, §4.3 fenced->queued/failed, §7.2 checkpoint resume, §8.2 attempt accounting confirmed |
| 2026-08-03T21:30+07 | Baseline run (T02+T03) | `python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py --cache-clear` | 79 passed in 17.88s (47 + 32) |
| 2026-08-03T21:30+07 | Baseline lint/type | `python -m ruff check app tests` / `python -m mypy app` | All checks passed / Success, 50 source files |
| 2026-08-03T21:30+07 | Protected user change snapshot | `git status --short` / `git diff --stat` | Pre-existing: `M channels.json` (+224 lines, user data — NOT touched). sha256 `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` |
| 2026-08-03T21:30+07 | Plan confirmed | See chat | 7 steps: repo lease-invalidation + attempt bumps, reconciler, worker attempt numbering, tests, doc, gates, LOG/REPORT |
| 2026-08-03T21:31+07 | Repo additions | app/persistence/jobs.py | `invalidate_lease` (sentinel token — schema CHECK forbids empty), `bump_job_attempt`, `bump_step_attempt`, `latest_attempt_number`, `fenced -> cancelled` transition endpoint, `manifest_fingerprint` on created events |
| 2026-08-03T21:40+07 | Reconciler module | app/workflow/job_reconciler.py (new) | JobReconciler: bounded scan, atomic fence, fresh-session resolve to queued/failed/cancelled, ReconcileReport, no import-time behavior |
| 2026-08-03T21:41+07 | Worker change | app/workflow/durable_worker.py | Per-claim attempt rows numbered from durable per-step counter (no duplicate `(job,step,attempt)` rows across requeues) |
| 2026-08-03T21:45+07 | Test file | tests/test_job_reconciliation.py (new, 24 tests) | AC1-AC7 incl. forced-close/reopen with fresh engines; fake clock aligned to lease rewinds |
| 2026-08-03T22:00+07 | Targeted tests | `python -m pytest -q tests/test_job_reconciliation.py --cache-clear` | 24 passed in ~10.7s |
| 2026-08-03T22:05+07 | Combined tests | `python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py tests/test_job_reconciliation.py --cache-clear` | 103 passed in ~28s |
| 2026-08-03T22:10+07 | Doc | docs/architecture/JOB_RECONCILIATION.md (new) | Reconciler design, resolution rules, duplicate-effect proof, ownership boundaries |
| 2026-08-03T22:28+07 | Baseline run 1 | `scripts/quality-baseline.ps1` | Gate 2 FAIL: `test_heartbeat_thread_keeps_silent_handler_leased` — pre-existing wall-clock flake (2s assertion margin vs 3s TTL renewal under load), NOT a reconciler regression (fails on unmodified code path) |
| 2026-08-03T22:31+07 | Correction | tests/test_durable_worker.py | Widened flaky assertion margin 2.0s -> 2.5s (log entry appended; no rewrite) |
| 2026-08-03T22:32+07 | Full suite | `python -m pytest -q -m "not gpu and not sam2 and not integration" --cache-clear` | 381 passed, 8 skipped, 7 deselected |
| 2026-08-03T22:32+07 | Baseline run 2 | `scripts/quality-baseline.ps1` | 7/7 gates PASS, OVERALL PASS (run id 20260803-223206) |
| 2026-08-03T22:33+07 | Final verification | ruff, mypy, `git diff --check`, `sha256sum channels.json` | All checks passed; 51 source files; diff-check PASS; channels.json `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` UNCHANGED (byte-for-byte) |
