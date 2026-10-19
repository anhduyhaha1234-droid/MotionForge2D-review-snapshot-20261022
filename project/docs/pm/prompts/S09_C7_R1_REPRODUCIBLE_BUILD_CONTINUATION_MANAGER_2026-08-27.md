# S09-C7-R1 Reproducible Build Continuation — Hermes Manager Prompt — 2026-08-27

Before any preflight, shell command, process inspection, repository read,
worker dispatch or write, you MUST read the ENTIRE canonical rules file:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Do not rely on memory, chat history or an earlier summary. Report
`RULES_LOADED` with the full line count and SHA-256 before continuing. Then read
this prompt in full and execute it without weakening any binary gate.

## 1. Authority and starting state

Codex is PM/BA/reviewer. Hermes Manager may preflight, dispatch, monitor,
adversarially review, run verification and append coordination evidence. The
Manager does not edit product code, test code or QA launchers.

Read in order after the canonical rules:

1. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C7_PM_REVIEW_2026-08-27.md`
5. `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\docs\pm\sessions\S09-SESSION_REGISTRY.md`
6. the live T06B C7 LOG, REPORT, runner, spec, helpers and machine evidence.

Starting state:

`S09-C7-R1 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

This is a continuation inside C7, not C8. S09 is not approved/closed. Do not
open S10, production S11 or production S13. Do not commit, merge, push,
release, reset, clean, stash, restore or overwrite unowned dirty changes.

## 2. Exact model, owner and persistence policy

- Hermes model/combo is exactly `meta`.
- Manager and worker use reasoning `max`, TTFB 900 seconds and fallback outside
  the `meta` combo disabled.
- Resume exact T06B owner session `20260824_131423_423e42`; do not create a new
  worker owner for this task.
- If invoked from CLI, resume Manager session `20260827_020702_b17b35`; do not
  create a duplicate Manager lane.
- A provider auto-stop is not completion. Inspect the session/process/log and
  resume the same exact session with one precise continuation.

### One-shot C7 closure contract

This prompt authorizes one continuous loop:

`preflight -> worker correction -> Manager code audit -> correct build -> Run1 -> audit -> Run2 -> audit -> retained gates -> terminal`

An in-scope failure is an internal checkpoint, not permission to stop or ask
Codex for C8. Route the exact finding to the same T06B owner, resume it, rerun
the affected gate and continue until every acceptance below is green. Stop
early only for a genuine external/config/rules blocker outside the authorized
write set, explicit user stop, or a model route that remains unavailable after
the canonical retry/resume procedure.

## 3. Workspace and preflight

Implementation worktree only:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration`

Expected branch/observed review HEAD:

`codex/s08-integration` /
`ee10e55a809c84d5cb5d4a3046a1ee78828528d0`

Discover current state; do not force it to this snapshot. Protected MAIN
`C:\Users\Admin\MotionForge2D` is PM-docs-only.

Before dispatch:

1. Confirm zero active S09 writer and stable relevant mtimes.
2. Attribute listeners on 3115, 8201 and 8212. Preserve unrelated 3014 and
   8099 processes. Never kill by port; stop only an exact positively owned PID
   through its retained handle.
3. Confirm `MOTIONFORGE_DATABASE_URL` is unset.
4. Directly re-hash J1-v4: all 13 entries must match and the manifest SHA must
   remain
   `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`.
   Verify 12 LF plus `composite.py` CRLF via `git check-attr`.
5. Record hashes of the complete authorized write set before dispatch.
6. Record the current `.next/BUILD_ID`, timestamp and production server/static
   URL scan as stale baseline only. Do not treat it as accepted evidence.

## 4. One bounded correction owner and write set

Resume `20260824_131423_423e42` for `S09-T06B-C7-R1`.

Exclusive write set:

- `frontend/e2e/s09-t06bc4-targeted-regeneration.spec.ts`
- `frontend/e2e/s09-t06bc4-helpers.ts`
- `frontend/e2e/s09-t06bc4-global-setup.ts`
- `frontend/playwright.s09t06bc4.config.ts`
- task-owned launcher, canonical fixtures, manifests, logs and evidence under
  `output/s09/20260823_sprint_full/t06b-c7/**`
- T06B LOG append and `REPORT-C7.md` append/reconciliation.

Forbidden:

- every `app/**`, backend test, migration, shared fixture and frozen renderer
  implementation/manifest;
- T00-T05 code/evidence and old C6/C7 Run1/Run2 artifact mutation;
- MAIN PM docs;
- broad kill, kill-by-port, manual post-hoc cleanup, copied PASS markers,
  fabricated evidence or report padding.

## 5. Required correction A — deterministic production build

The worker must make the C7 launcher self-validating:

1. Delete the `frontendBuiltOk()`/BUILD_ID-exists shortcut. The existence of a
   build ID never proves the baked API origin or benchmark identity.
2. Invoke the installed Next CLI through the exact Node executable and CLI JS
   file with `shell: false`; do not use `npx`, `.cmd`, PowerShell or a shell
   wrapper. Capture stdout, stderr, exit code and timestamps.
3. Before Run1, build production Next with all required values explicit:
   `NEXT_PUBLIC_API_URL=http://localhost:8201`, the canonical S09 benchmark
   results path, and content SHA
   `12de134527765da2b3a2e890dc7a8d693c43b8325c2f8e122eb8886783d038c3`.
4. Immediately scan actual production `.next/server/**` and
   `.next/static/**`, excluding `.next/dev/**`, cache and source maps. Require
   the exact API URL `http://localhost:8201` and required benchmark SHA to be
   present. Fail if `http://localhost:8888`, `http://localhost:8099` or another
   active API origin is baked into production chunks.
5. Emit a machine-readable `frontend-build-manifest.json` containing start/end
   timestamps, Node and CLI paths, redacted env contract, build exit code,
   BUILD_ID, scan counts and SHA-256 of every relevant production chunk used
   for the URL/benchmark proof.
6. Run both accepted Chromium commands against this exact unchanged build.
   There must be no `next build`, dev build or mutation of `.next` after Run1
   starts. If any later build occurs, both accepted runs are invalid and must
   be repeated against the final exact build.

## 6. Required correction B — self-contained launcher and fixtures

1. Invoke Playwright through the explicit Node executable plus installed
   Playwright CLI JS path with `shell: false`. Remove all `npx` and
   `shell: true` execution from the C7 launcher.
2. Remove every active fixture/runtime/seeder fallback to `t06b-c4`,
   `t06b-c6`, a generic shared C4 root or an old copied run. No candidate-list
   selection is allowed.
3. Create one immutable C7-owned canonical fixture bundle under
   `t06b-c7/fixtures/s09_demo` from the already passing C7 input, including the
   required occluder mask. Add a complete relative-path/size/SHA-256 manifest.
   The launcher verifies all entries and rejects missing, extra or drifted
   files before creating a run root.
4. Each run copies only from that verified C7-owned bundle. Record source and
   destination manifest SHA in the run env/evidence. Missing explicit paths or
   any mismatch must fail before the backend/frontend starts.
5. Keep a single parameterized launcher. It must accept explicit run label,
   runtime root and output root so Run1 and Run2 cannot silently share DB,
   artifacts, logs or Playwright output.

## 7. Preserve the green lifecycle/product contract

Do not weaken the C7 spec or helpers. Preserve and independently verify:

- initial backend is launched and its exact listener PID is proven before
  frontend/page navigation;
- exact initial PID exits and 8201 is free before replacement launch;
- replacement PID differs and exactly owns 8201 after readiness;
- checkpoint is created before initial stop and read after replacement owns
  8201;
- outer `finally` cleans exact initial/replacement/alternate/frontend handles
  and fails closed if any PID/listener remains;
- only d4 renders; d1/d2/d3 retain exact artifact identity and no render timing;
- renderer attempt count is exactly one;
- altered C3 evidence returns exact 404 with zero mutation;
- all five correction kinds never false-success;
- same bytes/different path retain identity;
- approval, publications and checkpoint survive the real owned restart.

Do not edit backend/product code to make the UI test pass.

## 8. PREP barrier and Manager adversarial review

Worker first submits PREP only after:

- Node syntax check, TSC, scoped ESLint and Playwright `--list` pass;
- direct scans show zero active `t06b-c4`/`t06b-c6` fallback, zero `npx`, zero
  `shell: true`, zero BUILD_ID-only reuse and zero kill-by-port in active C7
  launcher/spec/helpers/config/setup;
- canonical fixture manifest validates;
- Manager traces build and data flow, validates the explicit CLI paths, and
  confirms no forbidden file changed;
- direct J1 remains 13/13 and ports are free.

Manager must not patch. Route every PREP finding to the same owner and continue
inside C7-R1 until PREP is genuinely green.

## 9. FINAL — build first, then two fresh sequential runs

With zero writer/listener and no concurrent frontend build:

1. Run the explicit production build and validate
   `frontend-build-manifest.json` as Section 5 requires.
2. Execute Run1 with new roots:
   `t06b-c7/r1/run1/runtime` and `t06b-c7/r1/run1/e2e-results`.
3. Manager independently checks Run1 `.last-run.json`, separate raw stdout and
   stderr, DB, product evidence, lifecycle ordering/PIDs, exact process exits,
   build identity and released ports.
4. Only after Run1 passes, execute Run2 with
   `t06b-c7/r1/run2/runtime` and `t06b-c7/r1/run2/e2e-results`.
5. Manager performs the same audit and proves Run1/Run2 have distinct DBs,
   artifacts, run tags, PIDs and result roots while sharing the exact unchanged
   accepted BUILD_ID/chunk hashes.
6. After Run2, do not run Next build. Run direct J1-v4 13/13 plus attributes,
   the four T06 backend files expecting at least 43 passes from a temp root
   outside protected MAIN, TSC, scoped ESLint, `git diff --check`, complete
   write-set attribution, fixture manifest verification and final port/PID
   audit.
7. Re-scan production `.next` and require its BUILD_ID/chunk hashes to match the
   pre-Run1 build manifest exactly, with 8201 present and forbidden origins
   absent.

Any failure in Sections 5-9 must be corrected by resuming the exact worker and
then rerunning every invalidated downstream gate. Do not hand an intermediate
failure back to Codex.

## 10. Evidence and terminal condition

Each fresh run must contain raw Playwright stdout/stderr, `.last-run.json`, all
owned process logs, fresh DB/artifacts, redacted env/command summary,
`lifecycle.json`, product evidence JSON and accepted build-manifest reference.
Reconcile `REPORT-C7.md` so its claims match direct scans and current files.

Success only after every binary gate above is independently verified by the
Manager:

`S09-C7-R1 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

`S09 = PENDING_CODEX_REVIEW`

Failure is allowed only for a proven external blocker after the continuous
in-scope correction loop:

`S09-C7-R1 = BLOCKED_EXTERNAL / PENDING_CODEX_REVIEW`

Never write `APPROVED` or `CLOSED`; never open C8 or another sprint; never
commit, merge or push. Stop for Codex independent re-review.

## 11. Start now

Read the entire canonical rules file first and report `RULES_LOADED`. Perform
the complete preflight, resume exact T06B owner `20260824_131423_423e42` with
model `meta`, reasoning max, TTFB 900 and fallback outside the combo disabled,
then continue automatically through every internal correction and gate until
an allowed terminal in Section 10.

