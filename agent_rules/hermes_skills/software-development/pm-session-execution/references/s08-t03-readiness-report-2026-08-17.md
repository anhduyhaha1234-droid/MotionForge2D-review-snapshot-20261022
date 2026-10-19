# S08-T03 RO-1 Readiness Report — worked example (2026-08-17)

Context: S08 correction cycle, worktree `s08-integration`, approved sequence
R01 → T02 → T03 → T05 → T04 → H01 → T06. R01 done
(`MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`), T02 correction (finding B) running
(`proc_a9f179bfb7db`, `output/s08-t02-c1-hermes.log`), next task = T03
correction (resume `20260816_151439_21e306`). Helper was strictly read-only
(report in chat only, then exit).

## What was read
- `docs/pm/SESSION_PROTOCOL.md`, `docs/pm/sprints/S08-SPRINT_CONTRACT.md`
  (worktree), `docs/pm/CODEX_PM_HANDOFF.md` — **absent in worktree, found in
  MAIN** `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md` (the
  "similar files" hint + a MAIN-tree file search located it).
- T03 packet: TASK/START_PROMPT/REPORT/LOG (PM_REVIEW.md deliberately NOT in
  the allowed list — honored, never read).
- T02 packet: TASK + REPORT only (LOG.md is being appended by the live
  writer — treated as unstable, leaned on REPORT.md).
- R01 packet: TASK + REPORT; `output/SPRINT_S08_SESSIONS_TRACKING.md`;
  `docs/pm/sprints/S08-SPRINT_REPORT.md`; `docs/pm/AUTOMATION_PLAN.md`.
- Greps: `Required reading` across `**/TASK.md` (only S08-P00 has it —
  NONE of S08-T01..T06 packets do), findings/CHANGES_REQUESTED across
  docs/pm + output (0 hits — finding sub-items are NOT in the repo).

## Key findings that shaped the report
1. **Prompt assumption false**: the parent prompt said "architecture contracts
   listed in Required reading of TASK.md S08-T03" — TASK.md has no Required
   reading section. Reported as contract ambiguity; resume prompt must carry
   the reading list.
2. **Finding list C absent from repo**: only T02's finding B sub-items were
   recorded (in the tracking file): SAM2.1 production provider,
   deterministic=QA-only, stable media identity, role-artifact association,
   content endpoint, source-generation filtering, GPU smoke. T03's finding C
   sub-items exist only in the manager's prompt → "missing findings list =
   BLOCK condition".
3. **Migration-chain adjacency**: T02 `f2a3b4c5d6e7` ↔ T03 `f3a4b5c6d7e8`
   are parent/child. If T02 correction adds a revision, T03's migration
   parent + head-string tests shift. Same 4 test files are multi-task touch
   points (`test_persistence_bootstrap.py`, `test_durable_job_persistence.py`,
   `test_object_intelligence_domain.py`, `test_object_extraction.py`).
4. **Post-R01 tree**: R01 modified `app/config.py`, `app/api/deps.py`,
   `app/workflow/job_service.py`, `durable_worker.py`, `job_reconciler.py`;
   T03 validation battery must add R01 suites
   (`test_s08_r01_queued_cancel_lifecycle.py`, `test_s08_r01_root_resolution.py`).
5. **T02's own deviation #1** (queued-cancel drain gap, base engine) was the
   seed of finding A → R01; T03's deviations (pairwise-only, split-requires-
   merge-lineage, extractor-naming prevents same-name grouping, Python-side
   role filters) are the probable finding C targets.
6. **Env hygiene precedent**: T03 manager re-run had 18 false fails from a
   leaked `MOTIONFORGE_DATABASE_URL` (see SKILL.md env-contamination section).

## Deliverable shape (report in chat, Vietnamese, single message)
`RO-1 READINESS REPORT` with sections: Next Task ID / Required dependencies /
Binary acceptance checklist / Likely scope conflicts / Contract ambiguities /
Stop/block conditions / Recommendation — the recommendation used the two-state
vocabulary `READY_AFTER_CURRENT_GATE` (with conditions) or `BLOCKED` (reason).

Checklist structure: group A = TASK.md invariants (always binary: suggestions
never auto-confirm, CAS+idempotency+audit, fail-closed boundaries, evidence
immutability, no duplicate active roles, read-only GET, deterministic
algorithm, full validation battery); group B = correction-context items
(post-R01 tree compatibility, T02/T03 naming interplay, semantics preserved,
no scope-creep) — group B explicitly marked as pending the manager's finding
list.

Dependency list must include (beyond writer-exit + manager gate): new
migration head recorded, findings verbatim, pinned write-scope file list,
protected baseline re-verify (channels.json SHA `dd7aae26…555`, MAIN DB
311296 B), clean env.
