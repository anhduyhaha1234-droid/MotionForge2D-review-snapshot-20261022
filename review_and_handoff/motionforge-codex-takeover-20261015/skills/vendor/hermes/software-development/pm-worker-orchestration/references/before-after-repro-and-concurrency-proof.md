# Correction-round reproductions, true-concurrency proof, DB-backed convergence

Proven across S10-C6C/C6D/C6E (Codex PM review loop). Applies to any PM-gated
correction round where a reviewer reproduces a defect and the Manager must (a)
prove it on current bytes, (b) prove the fix, (c) trust nothing from the
worker's own report.

## 1. RED-phase before/after reproduction scripts (pytest-style evidence)

Shape: one script per finding under `manager/prep/before/<finding>/`, run via
pytest with the test module's helpers loaded through importlib (tests/ is not a
package):

```python
_ROOT = next(p for p in Path(__file__).resolve().parents
              if (p / "tests" / "test_s10_full_apply_api.py").exists())
```

- Root discovery: NEVER hard-code `parents[N]` — evidence dir depth changes
  between rounds (C6C `parents[5]`, C6E `parents[7]`).
- Use the REAL route + REAL service: `_make_client(tmp_path, monkeypatch)`,
  `deps._job_service` + `_session_factory`, then rebuild `TestClient(app,
  raise_server_exceptions=False)` for forced-failure paths.
- The script's asserts express the POST-FIX contract, so pre-fix runs FAIL =
  defect recorded. Save `result_before_*.json` + HTTP bodies sidecar BEFORE the
  asserts (so evidence survives the intentional failure).
- **Implication-style checks**: when the fix changes the expected behavior from
  "200 success" to "fail closed" (e.g. tampered manifest → 422), a check like
  `C1 = replay_ok and not mismatch` is WRONG post-fix. Write
  `C1 = (not replay_ok) or (not mismatch)` — "success ⇒ exact match", never
  "replay must succeed". (Bitten twice: F2/C6E.)
- Immutability: `before/**` never rewritten after worker starts; post-fix copies
  go to `after/**` with NEW filenames (`repro_after_f1.py`,
  `result_after_f1.json`) — reviewer checks no shared paths (P2 finding in
  C6C if violated).
- Force a service failure without touching production: subclass the service
  and raise inside `create_job`, swap via
  `monkeypatch.setattr(deps, "_job_service", boom)`.

## 2. True-concurrency proof (threading.Barrier inside the real call)

Requirement: "sequential A-then-B is forbidden; evidence must show barrier
rendezvous + final raw DB rows."

- Patch the service with a wrapper whose `create_job` does
  `barrier.wait(); reached.append(...); return super().create_job(...)` —
  both request threads rendezvous INSIDE the production call (test-only
  barrier; transaction/lifecycle untouched).
- **Pitfall A — thread names**: `TestClient` dispatches on portal threads;
  two portals can share the same thread name. `len(set(reached)) == 2` fails
  even though both passed. Use `len(reached) == 2` (count entries).
- **Pitfall B — Barrier auto-resets**: after 2 parties pass, a later
  `barrier.wait(timeout=0.1)` for verification sleeps and raises
  `BrokenBarrierError`. Don't post-check the barrier; record rendezvous inside
  the wrapper.
- Expected C6E defect reproduced this way: 2× HTTP 200 `reused=true` with ONE
  pending run and TWO queued jobs with the SAME idempotency key.
- Each race test must also assert the final DB rows (count jobs/runs/states),
  not just HTTP codes.

## 3. DB-backed serialization (the nullable-unique-index hole)

Finding F1/C6E: a unique index on `(workspace_id, idempotency_key,
input_generation)` with NULLABLE `input_generation` does NOT serialize two
inserts — SQLite treats NULLs as distinct. Both concurrent replays win.

Fix pattern (bounded, no migration):
- derive a deterministic NON-NULL `input_generation` server-side from the
  run/work identity (`s10:<run-id>`), pass it on EVERY S10 job-create path
  (submit, repair/replay, retry, resume) so the same identity collides on the
  same key+generation.
- catch the stable job-domain idempotency conflict (NOT raw `IntegrityError`),
  re-read the winner, validate it, return the truthful convergent outcome; the
  loser must NEVER compensate the shared run back to `failed`.

## 4. CAS run-row arbiter — closing cross-path races WITHOUT migration

When two paths can create work for the same lineage (replay-repair vs retry),
serialize them on a common row with MUTUALLY EXCLUSIVE predicates, rowcount-
gated, before any job/successor creation:

- replay-repair: `UPDATE run SET status='pending' WHERE id=:r AND status='failed'`
- retry-claim: `UPDATE run SET status='cancelled' WHERE id=:pred AND
  status IN ('failed','cancelled','completed')`
- SQLite is single-writer → exactly one wins; loser sees rowcount=0 → 409
  fail-closed, ZERO mutation, no compensation path runs.
- Result: exactly one 200 + one 409, exactly one active job + one active run.
- Test must be deterministic and FAST (loser fails before creating anything →
  no long-held locks → no 93s/180s hangs that a naive barrier test produces).

## 5. Manager must VERIFY a worker's "needs migration" claim

A worker may declare `BLOCKED_SCOPE_EXPANSION` after a couple of turns. Before
routing to Codex/user:
1. Re-run the worker's own standalone repro + the failing test — confirm the
   defect is real and on current bytes.
2. Inspect the code: does the retry path really lack a CAS? Is a shared-row
   arbiter feasible in the bounded write-set? (Usually yes: CAS on the run row.)
3. If a bounded path is plausible, route BACK to the same owner with the design
   direction ("try CAS arbiter X; if still impossible, stop with exact
   file:line + proof"). Manager guides, never writes code.
4. Only ship BLOCKED when the bounded attempt FAILED with evidence. In C6E the
   "needs migration" claim was disproven by a 4th resume turn.
Also: a worker turn killed by router `401` (auth-server deadline) mid-work is a
connection-type error — resume same session/model; landed bytes must be
audited (mtimes + run the new tests yourself), and the final LOG/REPORT/STATUS
append may be the ONLY thing left.

## 6. Evidence-claim hygiene (F4 finding)

- Never label a serial A-then-B test "concurrent"; if the docstring says
  barrier, the code must have barrier (reviewer greps).
- Worker "8 + 1 = 9 tests" vs 8 landed: count the file, not the prose.
- mtime alarms: read FULL `stat` (a file may be from an old date — `awk
  '{print $6,$7}'` dropped the date and looked "future"). Ground truth is the
  content hash vs the PREP baseline; mtime is only a hint.
