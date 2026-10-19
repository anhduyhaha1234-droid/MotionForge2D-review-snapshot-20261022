# MotionForge2D — Codex PM Final Review — S09-C7-R2 / Sprint S09

- Review time: 2026-08-27 21:40 +07
- Reviewer: Codex Project PM / BA / independent reviewer
- Integration worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch / reviewed HEAD: `codex/s08-integration` / `ee10e55a809c84d5cb5d4a3046a1ee78828528d0` plus the attributed dirty S09 sprint tree
- Manager: `20260827_020702_b17b35`
- Exact T06B owner: `20260824_131423_423e42`
- Submitted state: `S09-C7-R2 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`
- Decision: **S09-C7-R2 APPROVED; S09 CODEX_APPROVED / CLOSED**

## Authority loaded

- `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`: read in full, 180 lines, SHA-256 `987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`.
- Workspace `AGENTS.md`, Codex Settings instructions, `CODEX_PROJECT_PM_HANDOFF_2026-08-23.md`, `CODEX_PM_HANDOFF.md`, `ROADMAP.md`, `SESSION_PROTOCOL.md`, `README.md` and `TARGET_PROFILE_2D_SOURCE_LOCKED.md` were reconciled against the live repository and evidence.
- Filesystem, current code, databases, process lifecycle, raw Playwright output and independently rerun gates were treated as authoritative; Manager prose was not accepted by itself.

## Scope and correction verification

R2 stayed inside the authorized same-C7 correction boundary:

1. `frontend/next.config.ts` now keeps the normal product fallback `http://localhost:8888` while allowing the C7 build to inject `NEXT_PUBLIC_API_URL=http://localhost:8201`.
2. `run-c7.js` accepts explicit run/runtime/output roots, rejects protected/non-fresh roots, invokes Next and Playwright through explicit Node CLIs with `shell:false`, and no longer relies on a BUILD_ID-only reuse decision.
3. The build is bound to a companion SHA, complete file inventory, 185 chunk/file hashes, nine source-input hashes, the benchmark content hash and the exact environment contract. A seven-check validator runs before each accepted browser run.
4. The canonical C7 fixture bundle remains self-contained and verifies 21/21 files at SHA `6639dd8771bf7b52a5ff8b0fc469a94b81a254b044b328489ac0cdc2d3ef2b08`.
5. No backend product-flow rewrite was introduced by R2.

## Independent evidence

### Build and freeze integrity

- `run-c7.js --verify-build-only`: **7/7 checks passed**.
- Accepted BUILD_ID: `dm7D7QTAc52eVVVHqU09Y`.
- Build inventory: 185 files; required 8201 matches 7; benchmark matches 2; forbidden 8888/8099 matches 0/0.
- Manifest and companion SHA match: `c606d99b63511e7ed92c14b47d3ed52ef008370d445bfde6cdd7eb3c3497a58b`.
- J1-v4 manifest SHA remains `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`; direct byte comparison is **13/13**, with `.gitattributes` reporting 12 LF files and the intentional CRLF `composite.py`.

### Product/database truth

- R2 Run1 and Run2 raw Playwright state: `passed`, no failed tests, sequential and isolated.
- Direct read-only SQLite probes on both accepted databases independently show:
  - completed regeneration job;
  - exactly one attempt;
  - `affected_loop_ids == [d4_group_occlusion]`;
  - only d4 has `regenerated=true` and `render_ms`;
  - d1/d2/d3 preserve exact publication IDs/hashes/frame counts;
  - frozen evidence SHA is `653d6d6c2ae58f0887f6d4fe4b7ee66e7cfd3c0ed82fcf23f47715fd2418ee36`.
- Owned restart evidence is coherent in both submitted runs: initial PID exits before replacement launch, replacement PID differs and owns 8201, checkpoint is created before the initial exit and read after replacement, all exact process handles exit, and ports 3115/8201/8212 are released.

### Fresh Codex acceptance run

Codex ran a third browser acceptance with previously nonexistent explicit roots outside MAIN:

- runtime: `C:\Users\Admin\AppData\Local\Temp\codex-s09-c7-r2-final-runtime-20260827-2200`
- output: `C:\Users\Admin\AppData\Local\Temp\codex-s09-c7-r2-final-output-20260827-2200`
- result: **1 passed in 41.4 s** against the same validated BUILD_ID.
- lifecycle: `28784 -> 18924`, exact listener ownership before/after restart, `initialStopTimestamp < replacementLaunchTimestamp`, all four owned processes exited, all three task ports released.
- product evidence: one attempt, only d4 rendered, checkpoint persisted/read after restart, d1-d3 reused.
- Unrelated listeners 3014/PID 22436 and 8099/PID 29304 were preserved.

### Retained gates rerun by Codex

- Exact four-file T06 backend suite: **43 passed**, 83 known warnings, isolated Windows basetemp and `MOTIONFORGE_DATABASE_URL` unset.
- Frontend TypeScript: exit 0.
- Scoped C7 ESLint: exit 0.
- Tracked working-tree `git diff --check`: exit 0; only Git's LF-to-CRLF warning for `next.config.ts` remains. The later full Git staging pass surfaced whitespace-only P2s in previously untracked reports/tests; these do not alter the reviewed product/runtime verdict.

## Non-blocking findings carried forward

### P2-1 — R2 report was not appended to the task report

`docs/pm/sessions/S09-T06B-approval-ui-sprint-acceptance/REPORT-C7.md:1-121` still describes R1 and ends at `S09-C7-R1`. R2 is recorded only in `S09-SESSION_REGISTRY.md:120-125`. This is stale documentation, not a contradiction in the code, raw evidence or independent rerun, so it does not justify an eighth correction cycle.

### P2-2 — per-run env summary omits the accepted build reference

`output/s09/20260823_sprint_full/t06b-c7/run-c7.js:532` writes label/root/fixture/exit only. The validator actually binds every run to the accepted build before Playwright, but `env.json` should also record manifest SHA and BUILD_ID for easier audit.

### P2-3 — positional garbage is not rejected explicitly

`run-c7.js:78-80` rejects unknown `--options`, but a non-option positional token can be ignored if all required flags are valid. This does not weaken root, build or product acceptance; future launchers should parse every token strictly.

These three findings are PM/evidence hardening items for the S10 manager discipline. They are not P0/P1 product or safety defects and must not reopen S09.

## Verdict and dependency decision

- `S09-C7-R2 = CODEX_APPROVED / CLOSED`.
- `S09 = CODEX_APPROVED / CLOSED`.
- The S09 exit dependency for `S10-T01` is satisfied; S10 Full Apply is the next authorized production sprint.
- S11-T02..T06 remain production-blocked on E06 until S10 Full Apply closes; S11-P02 docs-only correction remains a separate readiness matter.
- S13-P00 remains approved planning only. Production S13 is not opened in parallel with S10 because both early lanes require shared `models.py`, migrations, `app/api/app.py` and integration state.
- Next authorized packet: `docs/pm/prompts/S10_FULL_APPLY_MANAGER_2026-08-27.md`.
