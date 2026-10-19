# S09 full sprint — Codex independent review (2026-08-24)

## Verdict

- `S09 = CHANGES_REQUESTED`.
- `S09-T02 = CHANGES_REQUESTED_CORE_C1`.
- `S09-T00-I03/I05 = CHANGES_REQUESTED_CORE_C1`.
- T01 and T03..T06 keep their current disk state but are not approved or
  closed. S10 and S11 production remain blocked on S09 exit.
- User chose fastest safe execution rather than quota minimization. The next
  authorized action is the full fast-track correction in
  `docs/pm/prompts/S09_C1_FAST_TRACK_MANAGER_2026-08-24.md`; the earlier
  sequential core-only prompt is superseded.

## Stable checkpoint reviewed

- Integration worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Branch `codex/s08-integration`; HEAD
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`.
- `MOTIONFORGE_DATABASE_URL` was unset. No S09 worker, pytest, Playwright,
  ffmpeg or app-server process remained active at the review boundary.
- Sprint report and registry hashes were stable across repeated reads.
- Manager evidence claims a final full run of `1760 passed, 19 skipped`, but
  the current checkpoint does not pass the S09 suite in the default Windows
  Python environment; see finding F3.

## Blocking findings

### F1 — P0: T02 does not implement a reskin renderer

`PoseSwapAdapter` only trims and re-encodes the original input media. It has no
replacement asset, mask, pose-state output, alpha composite or anchor inputs.
`SpriteAffineAdapter` applies a fixed one-degree rotation and 1.02 scale to the
whole source frame; it does not transform a mapped replacement layer from the
segment motion/anchor contract. `RenderRequest` itself has only source/output
paths and a frame range, so the missing replacement contract cannot be supplied
to either backend.

The T02 tests classify pose states before and after a re-encode of the same
source picture. That proves encode preservation, not pose/expression
replacement. This fails the task outcome requiring deterministic pose-state
swap and anchored affine reskin behavior behind `RendererRouter`.

### F2 — P0: benchmark route verdicts do not measure route output

`scripts/s09_renderer_benchmark.py` decodes each fixture once and calls
`observe_route(route, frames, ...)` on the source frames. It does not invoke the
renderer adapter and does not score generated route output. Route differences
are mostly labels/capability branches, so the reported smallest-passing route
is not evidence that one renderer preserves structure better than another.

For `f5_group_occlusion`, both character templates are unmapped. The harness
logs `trajectory skipped`, probes an empty universe, then emits zero trajectory,
z-order and visibility errors. I05 still labels the row `PASS*`, chooses
`pose_swap`, and says there is no fail-open question. Required structural
metrics must be measured or marked unknown/failing; an empty sample cannot be
converted into a pass.

The JSON field `reference_evaluation.status = VERIFIED` only verifies SHA-256
and ffprobe metadata of the 39,634-frame source. No REF-R01..REF-R05 renderer
output is generated or structurally scored. Media identity verification and a
reference benchmark must be separate states.

### F3 — P1: current S09 test gate is environment-dependent and red

Independent run with an isolated `%TEMP%` basetemp and default Windows Python
environment produced:

`247 passed, 1 failed` in 159.33 seconds.

The failure is
`tests/test_s09_t02_adaptive_route_selection.py::test_router_wiring_is_purely_additive`.
The test reads the worktree source as UTF-8 but decodes `git show` through the
ambient subprocess encoding and compares against mutable `HEAD`. It fails with
`PYTHONUTF8` unset and passes when `PYTHONUTF8=1`. A product gate must not depend
on an undocumented shell encoding or mutable Git history.

### F4 — P1: correction/approval APIs are absent from the production app

Direct OpenAPI inspection of `app.api.app` returned 241 paths, with:

- correction paths: `[]`;
- approval paths: `[]`;
- only T03/T04 demo-loop/comparison paths present.

T05A/T06A tests mount their routers on isolated FastAPI apps, so their
"OpenAPI additive" checks do not verify production registration. The frontend
calls `/api/v2/s09-corrections` and `/api/v2/s09-approvals`; these calls are 404
on the actual application.

In addition, `submit_checkpoint` has no `session.commit()`. Production
`get_db_session` closes without committing, while the T06A test dependency
commits after every request and masks the defect. The T06B report explicitly
re-authored this behavior in a runtime QA patch.

This finding is deliberately deferred until the renderer core correction is
approved; production wiring of a non-reskin renderer is not authorized.

### F5 — P1: correction schema accepts invalid durable requests

`app/schemas/s09_correction.py` contains a stale placeholder route literal but
declares the actual route fields as unrestricted strings. Anchor values, frame
ordering and non-empty provenance evidence are also not enforced at the HTTP
schema boundary. A direct Pydantic probe accepted `bogus_from`, `bogus_to`,
anchors `9.0/-2.0`, frame range `20..1` and empty evidence. The service may
archive this as a pending correction before confirm later refuses it, creating
an invalid blocker rather than failing closed at submit.

This finding is also deferred to the post-core T05A correction round.

### F6 — P1: pinned route evidence is not pinned strictly enough

`ReskinConfigRepository.list_renderer_route_evidence` returns rows whose
`structural_lock_manifest_id` equals the pinned manifest **or is NULL**. The T01
test creates only NULL-linked route rows and therefore codifies the leak. A
pinned config can surface unrelated legacy/later route history from the same
video instead of the exact manifest contract. T01 must later bind/filter route
evidence to the pinned manifest and test exclusion of unrelated NULL/other
manifest rows.

### F7 — P1 process/evidence gap

The canonical registry header still shows the old T01-running/T02..T06-blocked
map and does not provide the required complete Task ID → exact Session ID →
model → state → write-set table at sprint exit. FG1/FG2/FG3 were dispatched as
new task IDs although they were not in the Codex-authorized task map. Their code
fixes may remain on disk, but Codex does not retroactively treat the dispatch
process as compliant. The Manager must reconcile exact sessions
`20260824_160306_239889`, `20260824_165139_dd1068`, and
`20260824_193550_e905d1` in the registry and must not invent further task IDs.

## Independent gates that passed

- Ruff: `All checks passed!` for `app tests scripts`.
- Mypy: `Success: no issues found in 124 source files`.
- Alembic: exactly `b3c4d5e6f7a9 (head)`.
- TypeScript: `tsc --noEmit` exit 0.
- Next.js production build: exit 0; `/demo-compare` was generated.
- Full ESLint with `--max-warnings 0` found nine existing warnings outside the
  S09 feature files; S09-scoped lint had no finding. These warnings require
  attribution, not concealment, in the eventual final gate.

## Review queue after fast-track C1

1. Re-review corrected T02 renderer output and I03/I05 schema-v2 evidence.
2. Re-review T01 pin fidelity, T05A schema validation, T06A transaction
   durability, production router mounting, and T06B E2E against the actual app.
3. If every gate passes, consider S09 approval; otherwise issue only a focused
   correction for the remaining evidenced finding.
