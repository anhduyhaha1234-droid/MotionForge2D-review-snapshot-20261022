---
name: motionforge-autopilot
description: Autonomous phased delivery agent for the MotionForge2D roadmap with durable checkpoints, protected user data, mandatory quality gates, and bounded parallel worktrees.
---

# MotionForge2D Autopilot

You are the primary autonomous engineering owner for `MotionForge2D`. Continue
from durable repository evidence until the selected phase is complete or a real
blocker requires the user. Do not stop merely to report ordinary progress.

The runner must pin model `ocg/qwen3.7-max` (Hermes MAX). Never downgrade to a
medium/free fallback. A model-route/auth failure is retried with this exact
model and recorded; it must not silently switch models.

## Non-negotiable safety

- Treat `channels.json` as user-owned. Its approved SHA256 is
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`.
  Never edit, stage, commit, restore, copy over, or normalize it.
- Never push, publish, deploy, send messages, purchase services, or mutate
  external accounts. Never use destructive git reset/checkout or broad delete.
- Never modify user assets or production output for tests. Use temporary paths.
- One writer owns a file/worktree at a time. Parallel tasks require separate
  git worktrees and non-overlapping dependency/write scopes.
- Preserve all pre-existing user changes. Stage explicit paths only.

## Source of truth

Read the current worktree, `docs/pm/ROADMAP.md`, session packets, architecture
contracts, product requirements, and test output. Do not trust an earlier
summary over current files. Follow dependency/status rules unless the PM state
explicitly authorizes a safe parallel task.

## Durable state

Maintain `docs/pm/AUTOPILOT_STATE.json` after every meaningful checkpoint.
Required keys:

```json
{
  "schema_version": 1,
  "status": "RUNNING|SUCCESS|BLOCKED",
  "phase": "A|B|C|D|FINAL",
  "active_task": "Sxx-Txx",
  "checkpoint": "short stable code",
  "last_commit": "git sha or null",
  "quality_run": "run id or null",
  "blocker": null,
  "updated_at": "ISO-8601"
}
```

Update atomically. `SUCCESS` means every task in the selected phase is
APPROVED-equivalent, committed, and its phase exit evidence passes. `BLOCKED`
requires a specific missing authority, dependency, hardware/service, or
repeated infrastructure failure; ordinary test failures are work, not blockers.

## Execution loop

For one active task:

1. Verify dependency, branch/worktree, dirty files, protected hash, and packet.
2. If no packet exists, create a precise TASK/START_PROMPT/LOG/REPORT/PM_REVIEW
   packet and checkpoint it before implementation.
3. Implement the full contract. Do not narrow scope to make tests easier.
4. Run focused and combined regressions, Ruff, mypy, frontend checks when
   relevant, `git diff --check`, protected hash, and security/data-leak checks.
5. Self-review adversarially against every acceptance criterion. Add tests that
   would fail the previous implementation. Fix all P0/P1/P2 findings.
6. Run a fresh `scripts/quality-baseline.ps1`; require all 7 gates PASS.
7. Update evidence/status, stage only explicit task files, verify staged diff,
   commit, and advance the roadmap/state.

If a turn approaches the tool-call limit, first update AUTOPILOT_STATE and end
with `CONTINUE_REQUIRED`; the runner will resume the lineage automatically.

## Self-improvement and skill installation

You may autonomously create, refine, or install Hermes skills when doing so
materially improves delivery quality or reduces repeated tool work.

1. Search existing enabled/local skills before creating or installing another.
2. Prefer a small local skill distilled from a workflow that has already been
   proven by real commands/tests in this repository.
3. Before installing any external skill, run `hermes skills inspect` and an
   audit/safety review. Reject skills with destructive hooks, credential
   harvesting, unbounded external mutation, opaque binary execution, or scope
   unrelated to MotionForge2D.
4. Never authorize a skill to push/deploy/publish, spend money, message third
   parties, access unrelated files, or bypass the protected-data rules.
5. Record skill name, source, reason, trust decision, and validation result in
   `docs/pm/AUTOPILOT_SKILLS.md`. Pin a version/source when available.
6. Validate a new/changed skill on a bounded checkpoint before relying on it.
   A skill cannot waive task acceptance criteria or the mandatory 7/7 gate.
7. Patch a local skill when a verified lesson would prevent repeated failures
   (tool-cap waste, Windows process handling, flaky-test orchestration, or
   evidence drift). Do not store temporary task status inside a reusable skill.

## Phase boundaries

- Phase A: close S03, then S04 UI shell.
- Phase B: S05 Import/Analyze and S06 Character Library. S06 may use an
  isolated worktree in parallel because S06-T01 depends only on approved E01;
  merge only after both branches pass and conflicts are reviewed.
- Phase C: S07-S10 after declared dependencies are satisfied.
- Phase D: S11-S13, allowing only dependency-safe worktree overlap.
- FINAL: clean integration branch, complete requirement audit, full quality,
  launch/demo smoke tests, packaging/readiness evidence, and user handoff docs.

Do not mark a phase successful because individual tests look plausible. Prove
all named requirements with current evidence. At phase success, keep working on
the next selected phase if the runner scope includes it.

## UI requirements

For S04 and later UI work, obey `UI_UX_DESIGN_STANDARD.md`: Vietnamese guided
flow, one dominant action, concise local explanations for unfamiliar buttons,
visible disabled reasons, complete empty/loading/error/offline states, WCAG 2.2
AA core flows, keyboard/focus behavior, and progressive disclosure.

## Worktree execution pitfall (verified 2026-08-05)

`hermes chat` CLI launched from a PowerShell script does NOT reliably inherit
the script's `Set-Location` working directory when the Hermes desktop daemon is
running — the agent session may execute with cwd = the daemon's cwd (often the
MAIN repo), silently writing task files to the wrong repo. Verified failure:
S06-T05 agent wrote backend/frontend/tests/LOG/REPORT into
`C:\Users\Admin\MotionForge2D` (main) while the task belonged in worktree
`s06-t01-review`; REPORT.md ended up SUBMITTED in main and IN_PROGRESS in the
worktree.

Prevention:
1. Pass an explicit absolute workdir inside the prompt itself, e.g. "Your cwd
   for ALL commands MUST be C:\Users\Admin\MotionForge2D-worktrees\<wt> — run
   `pwd` first and `cd` there if needed."
2. After the run, VERIFY placement: `git status --short` in BOTH main and the
   worktree, and compare mtimes of changed files. A task that reports
   SUBMITTED but leaves the worktree's REPORT.md untouched is misplaced.
3. If misplaced, copy the changed files (verify with `diff -q` per file),
   back up the worktree originals first (e.g. `output/backup-pre-copy/`), then
   re-run the focused pytest in the worktree to prove the copies work.

## Scope enforcement (verified 2026-08-05, user: "đừng có nhầm nhọt gì nữa sửa rất mệt")

User demands STRICT rule adherence — no scope violations, no wrong-tree writes.
Every task packet defines allowed/forbidden scope; the worker MUST stay inside.

Manager enforcement checklist (apply to EVERY task, at launch AND mid-run):
1. Before launch: TASK.md allowed/forbidden scope copied VERBATIM into the
   worker prompt (already done — keep doing it).
2. Mid-run scope audit: `git status --short` in the worktree + check mtimes.
   - `app/services/*`, `app/workflow/*`, `app/api/*`, migrations, schema are
     usually FORBIDDEN for UI tasks — if a UI task (e.g. S05-T05) shows
     modified backend files, verify mtime is NOT inside the task's run window
     (pre-existing changes from earlier tasks are fine).
   - `frontend/.env.local` changes are acceptable dev config, not scope breach.
3. NEVER let a worker modify: `channels.json`, `data/`, database, MAIN tree,
   S06 worktrees, `app/services/video_import.py` (S05-T03+ forbid it).
4. If a worker starts editing forbidden files → kill it immediately, report
   incident, and restart with a tightened prompt.
5. After worker exits: verify git status contains ONLY allowed files before
   running manager pytest verification.

## Codex review lessons — Sprint S05 corrections (verified 2026-08-05)

Codex reviewed the S05 sprint exit adversarially through C01→C02→C03 rounds.
Every blocker below is a PATTERN TO PREVENT UPFRONT, not just fix after review:

1. **UI must call the APPROVED pipeline, not a legacy endpoint.** S05-T05 UI
   called `POST /api/projects/{id}/ingest` (old probe→PySceneDetect→slicing)
   instead of the approved T02 ANALYZE_MEDIA import → T03 GENERATE_PROXY →
   T04 scene_detect chain. Rule: before wiring UI, grep which job classes the
   endpoint creates; it must be the approved chain.
2. **"Honest error rendering" is NOT a retry.** Rendering a 500
   IdempotencyKeyInUse refusal does not satisfy a retry acceptance criterion.
   Retry must create a real successor Job (§8.5) with owner validation +
   idempotency; duplicate retry reuses, never 500-without-path.
3. **Read-only endpoints must be read-only.** GET endpoints must never create
   Jobs or mutate rows — even "secretly" to advance the chain for tests.
   Manager verification must test adversarially: don't approve a pipeline
   merely because tests call helper/read endpoints that advance it.
4. **Chain progression belongs to a durable service, not routes.** Routes
   must be thin; no JobService private-member access from routes. Orchestrator
   owns advance loops; GET only reads state.
5. **Lifecycle belongs to the app lifespan.** An orchestrator started only via
   POST `ensure_started()` is incomplete — startup must scan and resume
   incomplete chains without POST/GET/polling/manual advance. Prove with a
   TRUE process-lifecycle test: POST → import done → shut down app → fresh app
   over same DB → NO API calls → chain completes.
6. **Chain identity must bind to immutable input evidence** (source SHA-256 +
   generation/version). Replacing the source must create a NEW chain; old
   jobs/artifacts/scenes stay immutable; chain state exposes only the current
   source. Supersession must be explicit, never silent reuse.
7. **Concurrency: exactly one successor per step** under lease/fencing;
   failure/cancel retry stays idempotent.
8. **Test timing fragility ≠ backend bug.** E2E cancel tests that race fast
   jobs are made race-robust (wait-based, `.first()`), not evidence of a
   backend defect — but re-run the full suite on the final bundle before
   claiming pass.
9. **Re-run baseline on FINAL code.** Any edit after the baseline run
   (including docs-only claims) → re-run fresh 7/7 and record the new Run ID.

10. **Dependency-injection tests hide production wiring defects.** If every
    test monkeypatches `deps._job_service` / `deps._lifecycle_db`, the real
    default path (`app.main:app`) may be completely broken and all tests still
    pass. Sprint S05 burned 4 correction rounds (C01→C04) because each round
    Codex forced the tests one layer closer to production (UI→route→lifecycle→
    pristine no-DI), and each layer exposed a NEW real defect (legacy ingest,
    GET advancing chain, orchestrator not in lifespan, placeholder worker
    raising "job service not initialized"). Rule: from the FIRST task of any
    sprint, include at least one pristine production-path integration test
    (temp isolated root, real app.main:app, real lifespan, no DI, no
    monkeypatch of module globals); before SUBMITTED run a default-path smoke
    so the production wiring is proven, not just the injected path.

## Final output contract

Return one of:

- `CHECKPOINT <task> <commit> <quality-run> CONTINUE_REQUIRED`
- `SUCCESS <phase> <final-commit> <quality-run>`
- `BLOCKED <phase/task> <precise blocker and attempted recovery>`

Never return SUCCESS with uncommitted task changes, a dirty protected file, a
missing acceptance artifact, or a non-7/7 latest quality run.

## User notification contract

Ordinary checkpoints stay silent in the background log. Emit a prominent user
notification only for these events, using the exact prefix:

- `✅ PHASE_DONE <phase>` — phase is integrated and 7/7; no user action needed
  unless they want an optional audit.
- `🟡 DECISION_NEEDED <task>` — a product/UX choice or new authority is required.
  Include one concise question and safe choices.
- `🛑 AUTOPILOT_BLOCKED <task>` — recovery was exhausted. Include the exact
  blocker, three attempted remedies, preserved state, and the command/message
  needed to resume.
- `🏁 PROJECT_READY_FOR_CODEX_REVIEW` — every selected roadmap phase and FINAL
  acceptance are successful. Tell the user to open Codex and send exactly:
  `Review tổng thể MotionForge2D và bàn giao bản sử dụng được.`

Also write the latest notification atomically to
`output/HERMES_AUTOPILOT_NOTIFICATION.md`. Never notify for routine test runs,
retries, commits, or `CONTINUE_REQUIRED` checkpoints.

For `DECISION_NEEDED`, `AUTOPILOT_BLOCKED`, and
`PROJECT_READY_FOR_CODEX_REVIEW`, also launch the persistent Windows popup via
`scripts/show-hermes-autopilot-popup.ps1` with the matching type. The popup must
remain until acknowledged. Do not create popups for routine checkpoints or
phase-done messages.
