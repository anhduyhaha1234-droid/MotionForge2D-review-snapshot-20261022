# S09-C7 Owned Restart Correction — Hermes Manager Prompt — 2026-08-27

Before any preflight, shell command, process inspection, file read beyond this
prompt, worker dispatch or write, you MUST read the ENTIRE canonical rules file:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Do not rely on memory or an earlier summary. Report `RULES_LOADED` with line
count and SHA-256 before continuing. Then read this prompt in full and follow it
without weakening any binary gate.

## 1. Authority and terminal state

Codex is PM/BA/reviewer. Hermes Manager only preflights, dispatches, monitors,
reviews and records coordination evidence; the Manager does not edit code,
tests, QA launchers or product files.

Read in order:

1. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C6_PM_REVIEW_2026-08-27.md`
5. the live S09 registry and T06B LOG/REPORT/evidence.

Starting state:

`S09-C6 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

S09 is not approved/closed. Do not open S10, production S11 or production S13.
Do not commit, merge, push, release, reset, clean, stash, restore or rewrite
unowned dirty changes.

## 2. Model and session policy

- Hermes model/combo selection is exactly `meta`.
- Manager and worker use reasoning `max`, TTFB 900 seconds and fallback outside
  the `meta` combo disabled.
- Resume exact T06B worker session `20260824_131423_423e42`; do not create a new
  owner for the same task.
- If the Manager itself is resumed by CLI, resume Manager session
  `20260827_020702_b17b35`; do not create a duplicate manager lane.
- A transient provider stop is not completion. Inspect process/log/session and
  send one precise continuation to the same session.

### One-shot completion contract

This is one continuous C7 correction loop, not a single worker attempt. Manager
must keep running `monitor -> adversarial review -> resume same owner with exact
finding -> verify -> rerun affected gate` until every binary acceptance in this
prompt is green or a genuine external blocker outside the authorized write set
is proven.

- `TASK_SUBMITTED`, a green test count or one completed Chromium run is only an
  intermediate checkpoint, never permission to stop the Manager.
- A code defect, assertion failure, launcher failure, stale C4 fallback, leaked
  owned process or incomplete evidence discovered during PREP/Run1/Run2/final
  audit must be routed immediately back to worker session
  `20260824_131423_423e42` and corrected inside C7.
- Repeat as many internal correction iterations as necessary. Keep the same
  Task ID, model, reasoning, fallback policy and exclusive write set.
- Do not request or invent C8 merely because an internal C7 attempt fails.
  Only Codex may decide another correction round after independent review.
- Manager may stop early only for `BLOCKED_RULES`, `BLOCKED_MODEL_ROUTE`, an
  authorization/configuration blocker that cannot be corrected within scope,
  or explicit user stop. Transient connection failures follow the canonical
  five-minute retry/resume loop and are not terminal.

## 3. Workspace and preflight

Implementation worktree only:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration`

Expected branch/observed review HEAD:

`codex/s08-integration` /
`ee10e55a809c84d5cb5d4a3046a1ee78828528d0`

Discover current HEAD and dirty state; do not force them to this snapshot.
Protected MAIN `C:\Users\Admin\MotionForge2D` is PM-docs-only.

Before dispatch:

1. Confirm zero active S09 writer and stable relevant mtimes.
2. Attribute every listener on 8201, 8212 and 3115. Preserve unrelated 8099 and
   3014 processes. Never kill a PID merely because it owns a port.
3. Confirm `MOTIONFORGE_DATABASE_URL` is unset.
4. Directly re-hash J1-v4: manifest SHA must remain
   `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`
   and all 13 entries must directly match. Verify 12 LF + composite CRLF with
   `git check-attr`.
5. Record baseline hashes for every allowed frontend harness file.

If any unknown writer or task-owned listener remains, inspect ownership and
stop only the exact positively owned process using its retained handle/PID.
Otherwise report `BLOCKED_WITH_FINDINGS`; do not use kill-by-port.

## 4. One bounded correction task

Resume exact worker `20260824_131423_423e42` for `S09-T06B-C7-PREP`.

Exclusive write set:

- `frontend/e2e/s09-t06bc4-targeted-regeneration.spec.ts`
- `frontend/e2e/s09-t06bc4-helpers.ts`
- `frontend/e2e/s09-t06bc4-global-setup.ts`
- `frontend/playwright.s09t06bc4.config.ts`
- new task-owned QA launcher/evidence only under
  `output/s09/20260823_sprint_full/t06b-c7/**`
- T06B-owned LOG append and a new `REPORT-C7.md`.

Forbidden:

- every `app/**`, backend test, migration, shared fixture and frozen renderer
  implementation/manifest;
- T00-T05 files and evidence;
- old C6 Run1/Run2 evidence mutation;
- MAIN PM docs;
- broad process kill, kill-by-port, manual post-hoc cleanup or fabricated/padded
  evidence.

## 5. Required lifecycle design

The worker must implement all of the following:

1. The initial primary backend must be launched by code that retains its exact
   `ChildProcess` handle inside the acceptance lifecycle. A parent runner may
   not launch an inaccessible backend and then let the spec pretend to own it.
2. Wrap the complete test lifecycle in an outer `try/finally`. Retain and clean
   the initial primary, replacement primary and alternate backend handles.
3. Before restart, save the initial PID, await stop of exactly that handle,
   assert that PID exited and assert port 8201 has no listener. Only then launch
   the replacement.
4. The replacement PID must differ from the initial PID. After readiness, prove
   the replacement process is still alive and that the 8201 listener is owned
   by that exact PID. A health response from an old listener is not sufficient.
   Read-only listener attribution is allowed; never terminate the discovered
   PID through that lookup.
5. Cleanup must await graceful exit, then use only a bounded exact-owned-PID
   fallback. If the PID or listener remains, fail the run. Never resolve cleanup
   success while the child is still alive.
6. Launch Next without `shell: true` or an unowned wrapper. Prefer the explicit
   Node executable plus the installed Next CLI JS path. Its exact process handle
   must be awaited and proven exited. Launch Playwright similarly without an
   unowned shell wrapper where feasible.
7. Global setup, spec and config must require explicit worktree, runtime,
   seeder, evidence and Playwright-output paths. Remove active fallback to
   `t06b-c4`, the legacy C4 seeder or a shared C4 runtime. Missing required env
   must fail closed before writing.
8. Use one parameterized C7 launcher rather than two divergent copied scripts.
   Run1 and Run2 receive explicit distinct roots and outputs.
9. Preserve every discriminating assertion already green: only d4 renders;
   d1/d2/d3 exact reuse and no render timing; DB renderer attempt count one;
   exact 404 and zero mutation for altered C3 evidence; five correction kinds
   never false-success; same bytes/different path keep identity; checkpoint and
   publications survive the real owned restart.

Do not modify backend/product code to satisfy this task.

## 6. Machine-checkable evidence per run

Each C7 run must directly create under its own directory:

- raw Playwright stdout and stderr as separate files;
- `.last-run.json` with `status=passed` and no failed tests;
- backend initial/replacement/alternate logs and frontend log;
- fresh SQLite DB, artifacts, runtime output and Playwright output;
- command/env summary with secrets redacted;
- `lifecycle.json` containing initial PID, replacement PID, alternate PID,
  frontend PID, listener-owner observations, stop timestamps and final exited /
  port-released booleans;
- product evidence JSON containing runTag, base/regen/checkpoint IDs, affected
  loop, renderer-attempt count and frozen-evidence identity.

Binary lifecycle assertions:

- `initialPid != replacementPid`;
- initial PID exited before replacement launch time;
- listener PID after replacement readiness equals `replacementPid`;
- checkpoint was created before the initial PID exited and read after the
  replacement owns port 8201;
- all owned PIDs exited and 8201/8212/3115 released at command completion.

No copied C6 artifact may serve as the only proof.

## 7. PREP barrier

The worker first submits `S09-T06B-C7-PREP` after:

- TSC, scoped ESLint and Playwright `--list` pass;
- grep/static audit proves no active C4 runtime/seeder fallback, no kill-by-port,
  no discarded handle and no `shell: true` lifecycle wrapper;
- Manager traces the data flow showing the initial handle is assigned before
  `page.goto`, stopped before replacement launch and cleaned in outer finally;
- direct J1 remains 13/13 and no forbidden path changed.

Manager must not patch. If PREP fails, give the exact finding to the same worker,
resume it and repeat PREP until green. When PREP is verified and zero
writer/listener remains, resume that worker for FINAL. Do not hand an
intermediate PREP failure back to Codex.

## 8. FINAL — two fresh sequential Chromium runs

Run two separate commands sequentially with:

- `t06b-c7/run1/runtime` + `t06b-c7/run1/e2e-results`;
- `t06b-c7/run2/runtime` + `t06b-c7/run2/e2e-results`.

Run2 starts only after Manager independently verifies Run1 lifecycle evidence,
all owned PIDs exited and all test ports released. Never run two production
stacks concurrently.

After Run2, with zero writer/process, Manager independently audits both DBs,
raw logs, lifecycle JSON and product evidence. Then rerun:

1. direct J1-v4 13/13 plus attributes;
2. the four T06 backend files, expecting at least the independently observed
   43 passes, from a temp root outside protected MAIN;
3. TSC and scoped ESLint;
4. production Next build;
5. `git diff --check` and complete C7 write-set attribution.

Do not run unrelated global suites and do not let the Manager edit anything to
make this final audit green. Route every in-scope failure back to the exact T06B
owner, then rerun the affected join and final audit in the same C7 loop.

## 9. Reporting and allowed terminal

Evidence quality is measured by material, machine-checkable facts, not LOG line
count. Do not pad LOG/REPORT with repeated lines. Reconcile one concise table of
owner/session/model/write set/gates/evidence.

Success only after all binary gates exist and Manager independently verifies
them:

`S09-C7 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Failure:

`S09-C7 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Never write `APPROVED` or `CLOSED`, never open another sprint and never commit,
merge or push. Stop for Codex independent review.

## 10. Start immediately

Begin by reading the entire canonical rules file and reporting `RULES_LOADED`.
Then perform the complete preflight. If it passes, resume exact T06B worker
session `20260824_131423_423e42` with model `meta`, reasoning max, TTFB 900 and
fallback outside the combo disabled.

Do not return only a theoretical plan. Start preflight and orchestration now,
continue all internal correction iterations automatically, and stop only at an
allowed terminal from Section 9.

If launching from CLI rather than pasting into the existing Manager chat, use
the installed Hermes CLI to resume Manager session `20260827_020702_b17b35`.
Do not create a fresh Manager session for C7.
