# Reproducing independent-review findings at PREP (S10-C6C pattern, 2026-09-01)

When a correction packet arrives with `CHANGES_REQUESTED` and concrete findings
("Submit failure leaves pending run with zero durable job; identical replay
returns 200 reused=true"), the Manager's PREP phase should RE-RUN each finding
as a runnable reproduction before dispatching the worker. Benefits proven in
C6C: confirms the finding against the current tree (the verdict may predate
other fixes), gives the worker prompt exact file:line + observed HTTP/DB truth,
and produces the before/after evidence the EXIT gate needs.

## The setup that worked (real route + real service + isolated SQLite)

Do NOT hand-roll a minimal FastAPI app with ad-hoc seed rows — the product's
own test files already encode the full seed chain (project → video → scene →
character → pack version → role → reskin config → persisted authority → v2
checkpoint). Reuse it:

- Load the test module via `importlib.util.spec_from_file_location` with the
  resolved absolute path (tests/ is NOT a package — plain
  `from tests.test_x import helper` fails both under `python -c` and when the
  repro script lives outside `testpaths`).
- Compute the repo root from `Path(__file__).resolve().parents[N]` by PRINTING
  each candidate level first — off-by-one here silently points at the parent
  worktrees dir and fails confusingly.
- Write the repro as a pytest file and run it with `python -m pytest <path>`
  (not bare `python <path>`), so fixtures/monkeypatch/TestClient machinery all
  work; keep `MOTIONFORGE_DATABASE_URL=` UNSET and a short basetemp.
- Inside the test, call the test module's `_make_client(tmp_path, monkeypatch)`
  to get (client, seed), then grab the REAL service from
  `deps._job_service` and its `_session_factory` for DB-truth queries —
  creating a SECOND service/DB "for the repro" queries a different database
  than the seeded one and yields misleading 404s (this mistake cost a cycle).
- Force the failure by monkeypatching `deps._job_service` with a
  `JobService` subclass whose `create_job` raises (same session_factory +
  managed_root), then restore the real service for the replay step.
- DB-truth queries must match the real schema: the durable job table column is
  `job_type`, NOT `type` (`SELECT id, job_type, state, idempotency_key FROM
  job WHERE job_type LIKE '%full_apply%'`) — a guessed column name reads as
  "no such column" mid-assert.

## Truth semantics: record, don't assert green

A PREP repro of a BUG is SUPPOSED to show the bug (orphan runs, false-reuse
200s, `_Boom`-triggered 500s). Assert only the pre-conditions you need
(500 surfaced, cancel worked); capture everything else as JSON/print evidence
and mark flags like `ORPHAN_PENDING_RUN_ZERO_JOBS: True` — these are the
BEFORE half of the before/after pair the exit gate verifies. Keep re-runnable:
run the repro again at J-gate; the same script must show the flags FLIP after
the worker's fix (or the equivalent coherent behavior).

- Production-test scope stays with the worker: the PREP repro lives in manager
  evidence dirs, not tests/ — the worker writes the REAL regression tests.
- If a race branch (cancel-vs-completion CAS) needs a barrier hook that does
  not exist in production and caller-controlled hooks are forbidden, record
  branch-level code truth (the un-checked rowcount) as the repro and leave the
  deterministic runtime race to the worker's mandated tests + J-gate rerun.
- Clean up superseded drafts in the evidence dir (a half-written repro that
  import-errors misleads the next reader/reviewer); keep ONE canonical
  runnable repro and say so in PREP_SUMMARY.

## Repro file naming must mirror the verdict language

Name repro files after the FINDING labels the review actually uses (F1a/F1b/
F1c in C6C), not after your own ad-hoc step names — Codex and the next review
round read those labels verbatim. Output one result file per finding
(`repro_f1_result.json`, `repro_f1c_result.json`) with the HTTP bodies + DB
rows, so the J-gate before/after diff is a file comparison, not a scrollback
hunt.
