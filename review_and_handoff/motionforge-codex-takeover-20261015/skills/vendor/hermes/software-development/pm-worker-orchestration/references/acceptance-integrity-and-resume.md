# E2E acceptance integrity, ownership routing and iteration-cap resume (PM-gated sprints)

Session-proven patterns from S10 C4→C6A correction sprints (Hermes Manager driving
exact-owner workers on Windows worktrees). These are the traps that made Codex
return `CHANGES_REQUESTED` and the methods that closed them.

## 1. Iteration-cap resume — the worker's "RUNNING" report is a continuation contract

Workers hit tool-call iteration caps mid-task, exit 0, and write an honest
`STATUS: RUNNING — hết vòng lặp tool-call` summary: exactly what is DONE, what is
NOT done, next actions, and which session/prompt/model to resume. This is NOT a
failure; it is a continuation handoff.

- Resume the SAME exact session with the SAME prompt file; the worker continues
  from its own summary (verified repeatedly: T01C-C8 R1→R2, T04B-C3 R1→R2→R3,
  T04C-C3 R2→…→R8).
- Do not treat a mid-report log (e.g. a 4-line dispatch-r2.log) as the worker's
  verdict. Audit the evidence directory on disk (`.last-run.json`, `env.json`,
  fresh mtimes) before concluding where the worker actually stopped.
- If the summary names a concrete next step (e.g. "fix config, re-run"), just
  resume; if it names a BLOCKER (e.g. `BLOCKED_SCOPE_EXPANSION` needing Codex),
  verify the finding independently before routing it upstream.

## 2. Foreign-owner failure routing — attribution first, then exact owner

When a worker's full regression fails, MANY failures can sit in test files owned
by OTHER tasks. The worker must not touch them (exclusive write-set), even when
its own change is the cause.

- Attribute with a command before routing:
  `grep -E '^FAILED' full.log | grep -v <owner_file>` — zero results proves the
  failures are 100% foreign-owned.
- Read the failing test's payload construction (e.g. hard-coded
  `manifest_hash`, `source_generation "gen-1"`, fixed `affected_region`) — the
  failures are usually stale fixtures from a pre-correction contract, not a bug
  in the new code.
- Route to the EXACT owner session with a bounded correction prompt: re-align
  fixtures/seeds to the new contract, keep every assertion semantic, forbid
  touching `app/**` unless live evidence proves it necessary.

## 3. Acceptance-theater detection — E2E tests that pass on an empty page

Codex flags these as P1 acceptance-integrity defects. Grep the spec for:

- `.or(empty/loading/error)` disjunctions in a test that claims progress,
  evidence, or actions — the empty branch satisfies the test.
- `if (await x.isVisible())` / `count() === 0` early returns around core
  assertions — the assertions never run.
- `test.skip(...)` gating a required platform (e.g. mobile) behind a project
  name convention; a "5 passed, 1 skipped" result then contains zero mobile
  acceptance.
- Non-asserting loops that screenshot "enabled" state: `while(attempts<3){ if
  (disabled===false) break; ... }` without `toBeEnabled()`.
- A green Playwright summary alone is never proof — inspect traces/requests to
  prove the real clicks (Apply/Cancel/Retry/Resume/compare/Review) and their
  public product responses were asserted.

The correction pattern that satisfies Codex: deterministic per-scenario
precondition, binary assertions (`toBeDisabled()` → `toBeEnabled()` after real
approval POST), real API identity propagation (URL/localStorage/display + public
status API), executed (not skipped) 390x844 Chromium viewport, trace/evidence per
action, and NO `page.route` / DB status patch / mocked response.

## 4. Client-fabricated-authority anti-pattern (green runs that prove nothing)

The classic P0: an E2E harness constructs the authority payload itself —
reading DB hash directly, converting `mesh_warp`→`sprite_affine`, fixing
`affected_region: [0.10,0.10,0.40,0.40]` — so vertical runs go green while
proving only media/job plumbing, not immutable render authority. The durable fix
sequence:

1. Make approval an immutable hash-covered snapshot (`s09.approval/v2`) that pins
   source/SLM/selected routes/role mappings/pack/geometry/eligibility — client
   cannot supply authority.
2. Shrink the public submit contract to identity/CAS only
   (video/checkpoint id+hash+revision + bounded chunk controls); legacy
   authority fields become OPTIONAL and are canonical-compared — mismatch =
   fail-closed, zero run/job, client value never merged.
3. Server derives planner inputs from the immutable checkpoint; job manifest
   carries an authority fingerprint the worker re-derives on start/restart
   (tamper/mutation fenced before render).
4. Unsupported routes fail closed — no downgrade.
5. Re-align ALL owner test fixtures (including foreign-owner files via §2) to
   submit through the public contract; region geometry derives from persisted
   boxes, never hard-coded.

Source sweeps that must stay zero: `list(rendered_cut_frames)` mirroring,
hard-coded `manifest_hash`/`gen-1`/`affected_region` in submit paths, DB-read
hash in harness, route coercion, `stage_c4`/`_force_requeue`/grace=0 helpers.

## 5. Owned-process cleanup with launch-record proof

Workers claim "probe killed / port clean" but leave a live `uvicorn
app.api.app:app --port <x>` behind. Before killing: exact PID + command line +
port listener + a launch-record reference in the worker's dispatch log. Kill the
exact PID(s) and the bash wrapper parents, then verify `netstat` shows the port
free and the task ports (backend/frontend) free. Never kill infrastructure
(9Router/proxy/MCP/hermes daemons) — kill only the owned tree.

## 6. Baked-origin coupling — harness must match the build

A production frontend build bakes `NEXT_PUBLIC_API_URL` (e.g.
`http://localhost:8201`). Running the backend on a different port makes every UI
fetch fail ("Failed to fetch") — that is a launch-config error, NOT a product
defect; fix the harness ports (or run through the canonical launcher) before
re-running. Browser engine coupling bites too: `devices["iPhone 13"]` pulls
WebKit; require Chromium for mobile viewport 390x844 unless the WebKit build is
installed.

## 7. Gate re-verification discipline (Manager)

- Re-run decisive gates yourself on a FRESH basetemp/DB (targeted ×2 then full
  suite); never cite the worker's log as your gate evidence.
- After contract changes, re-check OpenAPI `required` arrays literally
  (`python -c "from app.api.app import app; ..."`) — that is how the
  minimal-contract win is proven (4 identity fields required, authority objects
  gone).
- Drop `--cache-clear`/`-p no:cacheprovider` and a short unique basetemp to
  avoid pytest cache masking env failures on Windows.
- Sweep hits need context review, not raw counts: `gen-1`/`affected_region`
  inside `mask_semantics` correction effects are legitimate user input, while
  the same literals in a submit path are the anti-pattern.

## 8. Broad-except swallowing of durable side effects — live-found P0 (S10-C6A cancel defect)

During live UI acceptance (T04B-C3), Cancel failed truthfully: `POST /full-apply/{run_id}/cancel`
set the run row to `cancelled`, but the durable-job cancel block was wrapped in
`except Exception: pass` — SQLite `database is locked` (second-writer) was swallowed, the job
never transitioned to `cancelling`, the worker claimed it, ran to completion and OVERWROTE
`cancelled` → `completed` (16/16 chunks + publication). A run the user cancelled ended completed.

- **Attribution method:** service-layer tests calling `svc.cancel_run()` directly PASS, while
  the same action through the HTTP route FAILS → defect is route-level (transaction/second-writer
  handling), not service-level. Keep the service tests + a deterministic repro
  (`repro.sqlite.py` that reproduces the lock every run) as the proof of attribution.
- **Review sweep:** any `except Exception: pass` (or bare `except:`) around a *secondary durable
  side effect* (job cancel, lease expiry, requeue, manifest pin) is a cancellation-integrity trap
  on SQLite. Cancel ordering must make the job state `cancelling` durable before the worker can
  claim it; never swallow lock errors in a cancel/state-transition path.
- **Routing:** the route was T01C-owned and frozen after the join gate → worker must NOT patch
  it; stop `BLOCKED_SCOPE_EXPANSION` with evidence + owner attribution, append the registry,
  and wait for the Codex decision rather than self-expanding.

## 9. Fast-run E2E races — action scenarios vs short-lived runs

When a seeded executable run completes quickly (~15s for 16 chunks), Cancel/Retry/Resume
scenarios race the run: by the time the test navigates and clicks Cancel the run is already
`completed`, so `waitForRunStatus(cancelled)` times out; Retry's predecessor finishes before the
click so the new-run URL swap races the render adjustment. These are scenario-timing bugs in the
test code, NOT product defects (DB probe shows the retry run attempt=2 completed truthfully).

- Cancel: click the control while the run is still `pending`/`running` — assert state before
  clicking; do not navigate away and return after completion.
- Retry: establish the prerequisite first — predecessor must be genuinely `cancelled`/`failed`
  BEFORE clicking Retry; then wait on URL/new identity robustly.
- Classify from the driver log + DB before blaming anyone: completed-after-cancel with overwrite
  (§8) is a product defect; completed-before-click is a test race.

## 10. Seed asset materialization must match worker resolve semantics

`missing replacement asset for '<role_uuid>': …/assets/<role_uuid>.png` — the worker resolves
`assets_dir/<layer_id>.png` where `layer_id == object_role_id` (a UUID), but the seed copied a
fixture-named file (`layer_fg.png`). Backend fail-closed was CORRECT; the fixture must
materialize `{role_id}.png` from the published pack's first pose asset. Verify the fix with a
real E2E smoke (reapprove → eligibility true → minimal submit 202 → poll COMPLETED) before
re-running the whole suite. Rule: when live E2E hits "missing X" where X is a UUID, check the
seed's naming convention before blaming the backend.