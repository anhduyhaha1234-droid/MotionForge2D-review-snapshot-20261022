# S09-C7-R2 Final Config and Build Integrity — Hermes Manager Prompt — 2026-08-27

Before any preflight, shell command, process inspection, repository read,
worker dispatch or write, you MUST read the ENTIRE canonical rules file:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Do not rely on memory, chat history or an earlier summary. Report
`RULES_LOADED` with full line count, SHA-256, current HEAD and loaded rule
sections before continuing. Then read this prompt in full and execute it
without weakening any binary gate.

## 1. Authority and terminal state

Codex is PM/BA/reviewer. Hermes Manager may preflight, resume the exact owner,
monitor, adversarially review, run gates and update Manager-owned coordination
records. Manager must not edit code, tests, launchers or production config.

Read after the canonical rules:

1. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C7_R1_PM_REVIEW_2026-08-27.md`
5. live S09 registry, T06B LOG/REPORT, C7 runner and R1 machine evidence.

Starting state:

`S09-C7-R2 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

This is the final bounded continuation inside C7, not C8. S09 is not approved
or closed. Do not open S10, production S11 or production S13. Do not commit,
merge, push, release, reset, clean, stash, restore or rewrite unowned changes.

## 2. Exact model/session and continuous completion policy

- Hermes model/combo is exactly `meta`.
- Manager and worker use reasoning `max`, TTFB 900 seconds and fallback outside
  the `meta` combo disabled.
- Resume exact T06B owner `20260824_131423_423e42`; do not create another
  worker/session for this correction.
- If launched by CLI, resume Manager `20260827_020702_b17b35`; do not create a
  duplicate Manager lane.
- Connection/provider auto-stop follows the canonical five-minute wait and
  same-session resume loop. It is not completion.

Continue `monitor -> review -> same-owner correction -> verify -> rerun` until
all binary gates are green. An in-scope failure is not permission to stop, ask
for C8 or return an intermediate terminal to Codex.

## 3. Workspace preflight

Implementation worktree:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration`

Observed review baseline:

`codex/s08-integration` /
`ee10e55a809c84d5cb5d4a3046a1ee78828528d0`

Discover current HEAD/dirty state; do not force this snapshot. Protected MAIN
`C:\Users\Admin\MotionForge2D` is PM-docs-only.

Before resume:

1. Prove zero active S09 writer and stable relevant mtimes.
2. Attribute 3115/8201/8212 listeners; all must be free. Preserve unrelated
   3014 and 8099. Never kill by port.
3. Confirm `MOTIONFORGE_DATABASE_URL` is unset.
4. Direct J1-v4 must remain 13/13 with the existing EOL attributes.
5. Record hashes/timestamps for the narrow allowed write set and all R1
   evidence. R1 evidence is immutable.
6. Record the direct findings: current next.config fallback 8201;
   `run-c7.js:389-398` BUILD_ID-only reuse; fixed-root parser; current
   `git diff --check` blank-EOF warning.

## 4. Single correction task and exclusive write set

Resume `20260824_131423_423e42` for `S09-T06B-C7-R2`.

Outcome: remove the test-port product regression and make the existing C7
acceptance launcher genuinely self-validating and fresh-root reproducible.

Worker-exclusive write set:

- `frontend/next.config.ts` — only the exact environment-driven rewrite with
  normal 8888 fallback;
- `output/s09/20260823_sprint_full/t06b-c7/run-c7.js`;
- new R2 launcher/build/run evidence only under
  `output/s09/20260823_sprint_full/t06b-c7/r2/**`;
- T06B LOG append and REPORT-C7 reconciliation.

Existing C7 spec/helpers/config/global setup are read-only unless the Manager
first proves a new failing acceptance that cannot be fixed in the two files
above. Every `app/**`, backend test, renderer, schema, migration, shared
fixture, T00-T05 file, R1 evidence and MAIN PM document is forbidden.

Manager may append/reconcile only Manager-owned S09 registry entries after
worker exit. No broad formatting rewrite.

## 5. F1 correction — production-safe rewrite default

`frontend/next.config.ts` must use exactly the equivalent of:

```ts
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8888";
```

and the rewrite destination must derive from `apiUrl`. The ordinary no-env
application default remains 8888. Do not hard-code C7 port 8201 as a fallback.

The C7 build still sets `NEXT_PUBLIC_API_URL=http://localhost:8201` explicitly,
so its generated rewrite and non-map production chunks must use 8201. Include
the relevant top-level `.next/routes-manifest.json` and
`required-server-files.*` in the accepted build scan in addition to server and
static JS/JSON files. Exclude only source maps, dev and cache artifacts.

## 6. F2 correction — full build-manifest validation before every run

Replace the BUILD_ID-only branch with one fail-closed validator invoked before
any backend/frontend/Playwright process starts. It must verify:

1. canonical build manifest exists and its companion SHA-256 matches;
2. build exit code is zero and env contract is exactly API 8201 plus the frozen
   benchmark relative path/SHA;
3. current BUILD_ID equals the manifest;
4. current relevant production file set exactly equals the manifest set — no
   missing, changed or unrecorded file;
5. every recorded file SHA-256 matches;
6. a fresh content scan matches the recorded counts and contains 8201 plus the
   benchmark SHA while excluding 8888/8099;
7. build-input hashes include at least `frontend/next.config.ts` and the active
   S09 frontend API/demo source files, and current inputs equal those hashes.

`--build-only` must rebuild explicitly with Node + installed Next CLI,
`shell:false`, then atomically write the manifest and companion hash. A normal
`--run` must never silently rebuild. It either validates the exact accepted
build or fails before process launch with a precise mismatch.

Add `--verify-build-only`. Manager must prove:

- canonical manifest passes;
- a temporary copied manifest with one wrong chunk hash fails nonzero while
  BUILD_ID remains unchanged;
- the canonical manifest still passes afterward without modifying `.next`.

## 7. F3 correction — explicit safe fresh roots

Every run command must require all three arguments:

- `--run-label <sanitized label>`
- `--runtime-root <absolute fresh path>`
- `--output-root <absolute fresh path>`

Requirements:

1. reject missing/relative/duplicate/unknown arguments before writing;
2. reject protected MAIN, repository root, worktree root, home/root drives and
   any path outside a task-owned C7 output subtree or an explicitly allowed
   reviewer temp subtree;
3. require runtime/output roots to be distinct and nonexistent or empty fresh
   task-owned directories;
4. never recursively delete an arbitrary supplied path or prior R1/R2 evidence;
5. stage only from the verified C7-owned fixture bundle and record fixture plus
   accepted build manifest SHA/BUILD_ID in each run env and summary;
6. keep exact process ownership, lifecycle and product assertions unchanged.

Negative PREP probes must prove missing roots fail before writing and protected
MAIN paths are rejected. A valid dry/preflight argument parse must not start
the production stack.

## 8. Dependency/parallel decision and liveness

There is one correction owner and shared `.next` plus ports, so no coding or
production-run parallelism is safe. Unused slots remain intentionally idle.
Only read-only hashing/static inspection may overlap. Build, Chromium Run1,
Run2 and global gates are serialized under one Manager mutex.

Heartbeat at least every 20 minutes; audit after eight minutes without new
progress. Include task/session, current phase, latest output, blocker, next
action and active/idle slot reason. Resume the same owner for every correction.

## 9. PREP barrier

Worker submits PREP only after:

- next.config normal fallback is exactly 8888 and env override remains active;
- Node syntax check, TSC, scoped ESLint and Playwright `--list` pass;
- static scan shows zero BUILD_ID-only reuse path, zero `npx`, zero
  `shell:true`, zero C4/C6 fallback and zero kill-by-port;
- canonical fixture 21/21 passes;
- full canonical build-manifest validation plus the bad-hash negative control
  pass as specified;
- explicit-root negative controls pass before any process starts;
- J1 remains 13/13 and no forbidden path changed.

Manager reviews code directly and routes every failure back to the same owner.
Manager does not patch.

## 10. FINAL serialized evidence

After PREP with free ports and zero writer:

1. Run one explicit `--build-only` with API 8201 and frozen benchmark env.
2. Run `--verify-build-only`; record accepted BUILD_ID, manifest SHA, complete
   file-set/hash count and URL/benchmark counts.
3. Execute fresh Run1 with explicit absolute roots under
   `t06b-c7/r2/run1/{runtime,e2e-results}` and output root
   `t06b-c7/r2/run1`.
4. Manager audits `.last-run`, raw logs, DB, lifecycle, product evidence,
   fixture/build references, exact PID exits and free ports.
5. Execute Run2 only after Run1 audit, using distinct explicit roots under
   `t06b-c7/r2/run2/**`; perform the same audit.
6. Do not build after Run1 starts. Verify both runs reference one unchanged
   manifest SHA, BUILD_ID and exact production hashes.
7. After Run2 run direct J1-v4 13/13 plus EOL attributes; the four T06 backend
   files expecting at least 43 passes from a temp basetemp outside protected
   MAIN; TSC; scoped ESLint; Playwright list; fixture verification;
   `git diff --check`; complete write-set attribution; final process/port audit.
8. Re-run `--verify-build-only` after all gates and require the same accepted
   manifest/build identity.

Directly query both R2 databases and require one completed regeneration
attempt, affected/rendered loop d4 only, d1-d3 `regenerated=false` without
render timing, and distinct databases/run tags/PIDs.

## 11. Report and allowed terminal

REPORT/LOG must state exact owner/model, files changed, explicit commands,
actual counts, negative controls, manifest/build/fixture hashes, both run
summaries, DB query results, process cleanup and any deviation. Correct the
false “no BUILD_ID-only reuse” claim only after the live code truly validates
all hashes. Remove the registry's extra blank EOF so direct `git diff --check`
is actually exit 0.

Success only when every binary gate is independently verified:

`S09-C7-R2 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

`S09 = PENDING_CODEX_REVIEW`

Failure is terminal only for a proven external/config/rules blocker after the
continuous same-owner loop:

`S09-C7-R2 = BLOCKED_EXTERNAL / PENDING_CODEX_REVIEW`

Never write APPROVED/CLOSED, never open C8 or another sprint, and never commit,
merge or push. Stop for Codex independent review.

## 12. Start now

Read the entire canonical rules file first and report `RULES_LOADED`. Perform
preflight, then resume exact owner `20260824_131423_423e42` with model `meta`,
reasoning max, TTFB 900 and fallback outside the combo disabled. Continue
automatically through every correction and gate until an allowed terminal in
Section 11; do not return only a plan.

