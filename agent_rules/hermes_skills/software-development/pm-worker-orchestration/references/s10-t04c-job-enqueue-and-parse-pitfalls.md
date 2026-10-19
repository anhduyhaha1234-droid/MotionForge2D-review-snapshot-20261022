# S10 T04C job enqueue swallow + harness parse pitfalls (verified 28/08 03:48)

**Context:** T04C `20260828_023122_76b87e` Run1 (`output/s10/r1/run1`) failed at `expect(foundCheckpoint).toBe(true)` after 1.2m — worker never polled. DB query `SELECT job WHERE job_type='s10_full_apply'` empty, `s10_full_apply_run.status=pending`. Two root causes in `app/api/routes/s10_full_apply.py:180-195`, neither a harness bug, so T04C (forbidden to touch production) reported `BLOCKED_WITH_FINDINGS` with file:line.

**P0 — commit-before-enqueue + swallowed duplicate:**

- **Bug 1 — `except Exception: pass` hides real errors.** Inner block:
  ```python
  try:
      job_service.create_job(..., idempotency_key=f"s10_full_apply_job:{rec.id}")
  except Exception:
      pass   # <- swallows SQLite busy/lock, FK, handler-missing
  session.commit()
  ```
  Run commits, job silently lost. Worker stays pending forever.

- **Bug 2 — create inside uncommitted tx → SQLite busy.** `session` (request tx) holds the whole-DB write lock; `create_job` opens a second connection via `job_service.session_factory()` while the lock is held → `database is locked` (busy 5s) → swallowed by Bug 1 → indistinguishable from idempotent duplicate.

- **Fix (T01C correction 2 — exact owner `20260828_003035_859fe5` — bounded `app/api/routes/s10_full_apply.py`):**
  1. Commit the run **before** enqueue (release lock before second connection). Split tx: `session.commit()` after `svc.submit()` returns, then `create_job` in its own tx.
  2. Narrow the swallow to duplicate-key only:
     ```python
     from sqlalchemy.exc import IntegrityError
     try:
         job_service.create_job(..., idempotency_key=job_key)
     except IntegrityError as e:
         if "UNIQUE" in str(e) or "idempotency" in str(e).lower():
             pass  # idempotent replay — expected
         else:
             raise
     except Exception:
         raise  # never swallow lock/FK/handler errors
     ```
  3. Re-verify with `grep -n "except.*pass" app/api/routes/s10_full_apply.py` (expect 0 bare) and `pytest tests/test_s10_full_apply_api.py tests/test_s10_full_apply_workflow.py -v -p no:cacheprovider --override-ini="addopts=" --basetemp=$(mktemp -d)` — must be 11 passed ×2 (54s each, isolated).

**P2 — harness shape mismatch (already half-fixed before the P0 surfaced):**

- Seeder created projects; spec parsed `{items:[]}` but API returns `{projects:[]}` (and `{videos:[]}` for videos). `active_only=false` was correct, parsing was not. Fix in `frontend/e2e/s10-full-apply.spec.ts`:
  ```ts
  const projects = (raw.projects ?? raw.items ?? raw ?? []) as Project[];
  const videos   = (raw.videos   ?? raw.items ?? raw ?? []) as Video[];
  ```
  Handle all three shapes (new key, legacy key, raw array). Runner corruption from `r1/`→`_build/` rename already recovered (`node --check` PASS) before this — keep `_build/` stable and never mutate after Run1 starts.

**Manager checks before retrying T04C same session:**

- Confirm handler registered: `grep -n s10_full_apply app/workflow/job_service.py` shows 2 hits (import + register). Already fixed by T01C correction 1 — re-check anyway.
- Confirm no bare swallow: `grep -n "except Exception" app/api/routes/s10_full_apply.py` shows only narrow IntegrityError branch.
- Then resume `20260828_023122_76b87e` with `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume ... -m meta --yolo` to redo fresh Build validator + 2× Chromium distinct roots same `IarEG...` manifest, capturing per-run `playwright-stdout.log` / `.last-run.json` / `env.json` / DB probe / lifecycle ports.
