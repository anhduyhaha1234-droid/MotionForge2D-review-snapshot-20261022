# S08-A02-T01-C3 correction cycle — blockers, test-quality smells, independent-verification playbook

Context: HERMES MANAGER round for A02-T01 (structural evidence supersede/lineage/API) on worktree
`s08-integration` (branch `codex/s08-integration`, HEAD a43b20d). Writer = Muse
`ocg/muse-spark-1.2-contributor` (provider muse, 9Router) reasoning max. Manager then verified
independently. These are the durable patterns, not the one-off narrative.

## BLOCKER patterns (recurring in Codex-style adversarial review)

### 1. Ownership validation that checks the WRONG subset of identity columns
`supersede_segment` workflow B validated workspace + video + generation + kind but **silently
dropped `project_id`** — even though `ObjectRole.project_id` exists (models.py). A role can match
ws/video/generation/kind yet belong to a different project and be wrongly accepted as successor.
Rule: when binding any FK-owned entity (role, job, artifact, scene) to evidence, enumerate ALL
project-relative identity columns (workspace_id, project_id, video_item_id, source_generation, kind)
and assert each against the predecessor/current evidence BEFORE the mutation. Add the wrong-project
test: same ws + video + gen + kind, different project_id → stable `OwnershipMismatchError`,
predecessor still active (`superseded_by_id IS NULL`), zero successor rows, `PRAGMA foreign_key_check` empty.

### 2. "Fetch N then filter/count/paginate in Python" history API bug
Historical endpoint `source_generation` branch called `repo.list_segments(..., limit=10000, offset=0)`
then filtered (superseded OR stale-generation) and computed `total=len(...)` + sliced in Python.
With >10,000 rows this corrupts both total and pagination (repro: 10,001 valid rows → total=10000,
offset=9900&limit=200 returns 100 not 101).
Rule: push the business filter into SQL BEFORE COUNT and BEFORE OFFSET/LIMIT (a repository method),
ORDER BY a deterministic key (`start_frame,end_frame,z_order,id`), and never load the full history
into RAM just to paginate. Keep excluding the current active successor. Regression test MUST cross
the actual boundary (bulk insert 10,001 rows; assert total=10001 and page 101) and FAIL on pre-fix code.

### 3. "Exactly one selector" contract (both None AND both present → 422)
Historical list endpoint must accept EXACTLY ONE of `logical_id` / `source_generation`. Codes often
only add the `both None → 422` branch and forget `both present → 422`. Add both; three tests
(none / both / exactly-one).

## Test-quality smells the manager should grep for in writer submissions

These are the three the independent reviewer keeps flagging; a writer-report "all pass" hides them:

1. **Fake concurrency** — test named `test_..._concurrent_...` actually runs supersede twice
   SEQUENTIALLY (first succeeds, second expects failure). Not concurrency at all. Fix: real
   threads + `threading.Barrier` + independent sessions per worker (proven pattern in
   `test_s08_a02_r1_c1_semantic_safety.py::test_c1f2_concurrent_supersede_single_winner`).
   Assert exactly one `ok:` outcome and a 2-row valid lineage. Do NOT accept a rename-dodge.
2. **NaN/Infinity test hitting the wrong field** — e.g. putting NaN inside `transform_json` with a
   `transform_type` so the 422 fires for a DIFFERENT reason (transform validation), not for
   non-finite-number validation. Fix: use a real DTO float field (`allow_inf_nan=False`, e.g.
   `confidence`) in an otherwise-valid payload and prove NaN/+Inf/-Inf each → 422; if checking
   detail, pin location not exact message text.
3. **Broad `try/except Exception` turning anything into PASS** — grep for `except Exception` +
   `pytest.raises` misuse. Tests must FAIL when the named behavior is absent.

## Independent manager verification (do not trust the writer REPORT)

1. Record preflight hashes of every file expected to change BEFORE dispatch (sha256), then diff
   after — proves the diff is real and scoped.
2. Re-run each suite yourself with the same isolated-DB discipline (`MOTIONFORGE_DATABASE_URL`
   unset, `-p no:cacheprovider`, unique shallow `--basetemp`), and the combined focused suite.
3. Write a **standalone manager repro script** (in Temp, NOT importing any writer test module):
   seed its own data through app.persistence + alembic, assert each required repro. This is the
   strongest "not tuned by the writer" check. Log to a manager-owned evidence dir.
4. Spot-check code directly (grep the guard/selector/filter), not just README-style claims.
5. Check `# ruff: noqa:` whole-file headers — a writer can clear "ruff 0" by suppressing E501 etc.
   instead of fixing; hand that to the reviewer as a warning even when ruff exits 0.
6. Match every writer REPORT number to the raw log; a discrepancy (report says ruff 0, real ruff
   shows 121) is an immediate STOP/CHANGES_REQUIRED signal.

## Standalone-repro script pitfalls (learned the hard way)

- Each repro needs its OWN fresh DB (create a new db path per repro); reusing one seeded DB across
  repros → `UNIQUE constraint failed: workspace.id` from re-seeding.
- Bulk 10,001-row insert collides with the partial UNIQUE active-identity index
  `(role_id, scene_id, start_frame, end_frame, source_generation)` when rows share role/scene/gen
  AND have `superseded_by_id IS NULL`. Fix: make `start_frame` unique per row (or mark rows
  superseded) so the partial index doesn't trip.
- Check the real DTO fields first — `SegmentCreateRequest` DOES carry `project_id`, `video_item_id`,
  `role_id` in the body (not only as path params). A payload missing them → `ValidationError`,
  which misreads as a pass for the NaN test. Read the schema before assembling scripts.

## Dispatch pattern that worked

`hermes chat --provider muse --model ocg/muse-spark-1.2-contributor -q "$q" --yolo --pass-session-id
--max-turns 400 --source tool` run via `terminal(background=true, notify_on_complete=true)` with
`q=$(cat START_PROMPT.md)` (single-quoted-var avoids backtick/quoting issues). Probe the route FIRST
with a 1-turn minimal call (expect PROBE_OK) before spending a full writer run on a dead model route;
confirm reasoning_overrides in the ACTIVE profile config (`AppData/Local/hermes/config.yaml`, not
`~/.hermes/config.yaml` which may still name a different provider).
