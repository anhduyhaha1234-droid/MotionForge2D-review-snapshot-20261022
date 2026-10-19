# S10 C4–C6A authority & acceptance lessons (2026-08-30/31)

## Full Apply authority must be server-derived, never client-authoritative (C6A)

- `SubmitFullApplyRequest` must be identity/CAS only: `video_item_id`,
  `apply_checkpoint_id`, `expected_checkpoint_hash`, `expected_checkpoint_revision`
  + bounded chunk/idempotency controls.
- The four legacy authority payloads (`approved_checkpoint`,
  `structural_lock_manifest`, `scene_manifest`, `mapping`) are optional-for-compat
  ONLY. If present, EVERY supplied field is canonical-compared to server
  authority; any mismatch (manifest/scene/shot/range/route/mapping/affected-region/
  pack/source/policy) => fail closed BEFORE creation, zero run/job/publication.
  Never prefer or merge client authority.
- Server resolves plan inputs exclusively from the frozen approval snapshot
  `s09.approval/v2` with nested `full_apply_authority`: identity, source artifact
  (SHA-256/size/frame_count/fps), structural lock (id/policy/stored manifest_hash),
  shot_order, exact manifest-selected segments/routes, role mappings, affected
  region (from persisted segmentation — never hard-coded), pack versions.
- v1 checkpoints => `REAPPROVAL_REQUIRED` (422, fail closed). NEVER auto-upgrade v1
  in place; deterministic reapproval creates a DISTINCT v2 row with new content
  hash; equivalent v2 replay idempotent; conflict zero mutation.
- Unsupported route (`mesh_warp`, `part_rig`) => explicit fail-closed reason;
  NEVER downgrade to `sprite_affine`. Worker production must not coerce either.
- Job manifest `render_authority` is built from canonical server data (fingerprint
  recomputed on worker start/restart), NOT `dict(body.*)` — the old route copy of
  client payload was the Codex P0 finding F1.
- Selected route = manifest-selected segment routes, NOT `list_routes_for_video`
  alternatives (real data: 2 segments x 3 alternatives each; snapshot v1 stored
  only alternatives, which is why v1 cannot drive Full Apply).

## Live UI acceptance must be non-vacuous (C6 F1 — "acceptance theater")

E2E suites that CAN pass on an empty page are acceptance theater. Red flags:
- `toBeVisible()` without `toBeDisabled()` on the disabled-Apply assertion
- `.or(empty/loading/error)` disjunctions for progress/evidence/actions
- `if (visible)` conditionals around core assertions
- `count()===0` early returns (project entry test)
- `test.skip` for the mobile case
- green summary without trace/request evidence of actual clicks

Required: each scenario establishes its own deterministic precondition and
executes real clicks + real public product responses; desktop + 390x844 mobile
both execute, zero skip/vacuous branch; action buttons (cancel/retry/resume) have
their own run or controlled state machine; structural compare proves
REVIEW_REQUIRED with actionable evidence AND tamper => BLOCKED with Review
disabled; worker/manager each run the suite on fresh isolated environments.

## Concrete environment gotchas

- **Baked-build origin**: `next build` with `NEXT_PUBLIC_API_URL=http://localhost:8201`
  bakes 8201 into the bundle. E2E must launch backend on THAT port (not a spare
  like 8212/8213) or every fetch fails ("Failed to fetch"). Either launch on the
  baked origin or rebuild with the desired env.
- **Mobile webkit**: `devices["iPhone 13"]` pulls WebKit which is often not
  installed (`ms-playwright/webkit-*` missing). Use Chromium with explicit
  viewport 390x844 instead.
- **Long-path gate reads must use extended-length form**: producers write via
  `_lp()` / `\\?\` extended paths; a gate that reads artifacts with a plain path
  (>260 chars, LongPathsEnabled=0) sees `is_file()=False` => `RENDERED_FILE_MISSING`
  => REVIEW_REQUIRED unreachable. Apply the same extended-length helper in the
  gate read branch (and in fixture copy/stat).
- **OPPOSITE constraint — pytest basetemp must be SHORT (C9, 2026-08-31)**:
  pytest `--basetemp` inside the worktree (~95 chars) makes tmp_path fixtures
  blow past MAX_PATH on spawn/child calls before the app's `_lp()` extended-path
  helper can run — WinError 206 (filename too long). Runs are green with short
  roots like `%TEMP%/mfc9_<label>` (cygpath -m form; distinct per run: r1/r2/
  full/race). Rule of thumb: DEEP roots are for the runtime media-tree actuator
  (the >260 final/staging artifact gate, C5), SHORT roots are for pytest basetemp
  — do not copy the deep-root pattern into test invocations.

## Publication content_hash is a LINEAGE hash (C4 finding-01)

- FullApply: `pub.content_hash = sha256("pub:{run_id}:{stitch_sha}")`
  (jobs:903). Recompute: `sha256("pub-recompute:{run_id}:{correction_id}:{sha}")`
  (recompute:1245). Model UniqueConstraint(run_id, content_hash) + lineage dedupe.
- A gate comparing `pub.content_hash == art.sha256` (raw artifact hash) ALWAYS
  blocks on real output (pre AND post correction); service-only synthetic probes
  (content_hash==sha) can't catch it. Compare against the recomputed lineage
  string; keep raw-sha/tamper/foreign checks separate.

## Manager recovery patterns (worker iteration caps)

- Dispatch logs truncate MID-REPORT when the worker hits its tool-call cap
  (e.g. r2 log = 4 lines after a full r1). Audit DISK truth, not the tail:
  evidence dir mtimes, `.last-run.json`, `env.json` BUILD_ID, driver logs, DB
  read-only probes.
- Workers leave orphaned `uvicorn` backends on probe ports; find them via
  `netstat -ano | grep <port>` + exact command line; ownership proof = command
  line + port + reference in the worker's dispatch log. Kill the exact PID
  (`powershell Stop-Process -Id`), never pkill/killall python. Ports 8201/3015/
  8212/8213/3000 are the usual suspects; infrastructure (9Router 5088/18524,
  hermes serve, MCP, Codex CUA) must be left untouched.
- Worktree git-status growth of ±1 per append (registry/sprint-report) is normal
  and stays inside the allowed docs/pm write-set.

## C6B addendum — server-authority refactor exposes latent ID mismatches (2026-09-01)

When the client-authoritative payload keys are dropped (spec sends identity+CAS
only, per C6A), defects that client scene_manifest copies used to MASK surface
as real failures:

- **Planner `shot_id = occurrence_segment.id` (s10_full_apply.py:262)**: once the
  server no longer echoes client shot names, server-side seg ids must already
  match the named shots the spec asserts (`shot_a`/`shot_b`). A seed fixture
  with UUID seg ids failed live with `BLOCKED_SHOT_ORDER_MISMATCH`. Fix in
  fixture (node-owned): pin `OccurrenceSegment.id = SLM shot name`; every other
  consumer treats seg.id as an opaque FK, so this is transparent. Spec-side:
  relax a UUID-regex assert to `toBeTruthy` where format genuinely doesn't
  matter — never to widen a real invariant.
- **Spec payload shape follows the contract**: drop `scene_manifest`/`mapping`
  from the submit body; approval path = `POST /s09-approvals/reapprove`
  (201/200 replayed, v1 rows never mutated).
- **Hash-pinned fixture bundles: sync ALL THREE artifacts together** — the file
  itself, its `files[]` entry in `manifest.json` (sha256+size), the regenerated
  `manifest.sha256`, AND the generator source (`generate_fixtures.py`) so a
  future regeneration doesn't silently drift back. The driver's
  verifyFixtureBundle gate checks sha/size per file and will block on any lag.
- **Driver timeout must cover the longest test, not the old suite**: raised
  run-s10 spawnSync timeout 600s→900s to match the playwright per-test timeout
  once lifecycle scenarios lengthened the run.
- **Missing `--output-root` → stale root → long-path blowup**: an omitted flag
  reuses a stale output tree; 16-segment runs then hit WinError 206 at spawn.
  `assertFreshRoot` catches it — and prevalidation (below) catches it before
  any 5-9' vertical is burned.