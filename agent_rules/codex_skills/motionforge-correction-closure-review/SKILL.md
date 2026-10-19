---
name: motionforge-correction-closure-review
description: Independently review MotionForge2D Hermes correction-sprint submissions and recovery incidents, especially concurrency, durable identity, evidence overclaim, destructive writes, and closure-matrix rounds. Use when Codex must issue a binary verdict or incident decision, an exact session-opening proposal, and the next bounded Hermes prompt with minimal correction loops.
---

# MotionForge correction closure review

Use this workflow for MotionForge2D correction submissions. Keep the review read-only for production code and tests.

## Load authority before action

1. Read the full current `HERMES_AUTOPILOT_RULES.md` in the same turn.
2. Read applicable `AGENTS.md`, the current PM handoff/roadmap/session protocol, prior verdict, binding Manager prompt, current task records, registry, Manager EXIT, raw evidence, and actual source/tests.
3. Reconcile branch, HEAD, dirty attribution, database guard, relevant processes, ports, owner terminal state, and evidence mtimes. Reports route the investigation; repository and runtime bytes are truth.
4. Reconcile the actual writer session against read-only Hermes state data when
   registry/session claims conflict. Record both the reported and actual owner;
   never resume a stale ID that would create another lineage.

## Protect source and test authority

- Before dispatch, require SHA-256, byte size, line count and tracked/dirty
  attribution for every writable and protected file. Critical untracked/dirty
  files need a byte snapshot whose hash matches the source.
- Prefer the project guard at
  `C:\Users\Admin\MotionForge2D\docs\pm\tools\write_set_guard.py`. Treat a
  missing file or destructive shrink as an incident, not an ordinary test fail.
- Existing source/test files are patch-only. Full overwrite tools, redirection,
  script direct-write and copy-over are unacceptable unless the target is a new
  allowlisted file.
- If authority is destroyed, freeze the writer and evidence first. Manager and
  Codex Reviewer remain non-writers. Require an external candidate from Git,
  byte snapshot, full tool payload or deterministic patch replay; when a
  reviewed hash exists, exact hash match is the restoration gate.
- Do not accept test names, docstrings, pyc function lists, compile success or a
  selected green subset as source recovery. Collect and run the full relevant
  module and audit duplicate definitions and unresolved symbols.
- One guarded exact-owner resume may be proposed after a first destructive
  incident. A second unsafe overwrite/scope violation is repeated context-health
  evidence and must trigger owner-transfer review.

## Audit closure at four layers

For every binary closure row, independently verify all four layers:

1. Contract: exact requirement, expected response, row counts, mutation count, and owner.
2. Mechanism: trace the production call path and identify the actual ownership/serialization primitive.
3. Test structure: verify setup, participants, synchronization, operation under contention, join/timeout, assertions, and all-row query.
4. Reproduction: run a fresh isolated probe against current bytes. Do not inherit Manager output as the verdict.

Reject a row as open when any layer is missing, even if a focused or full suite is green.

## Concurrency and CAS checks

- A CAS ownership token must perform a real state/version transition. A same-state update such as `cancelled -> cancelled` is not an exclusive winner merely because SQLite reports `rowcount == 1`.
- Instrument winner count as well as final rows. A downstream unique constraint may preserve one final successor while both callers falsely believe they won the earlier claim.
- Place a barrier at the contested production operation, not at an unrelated precheck that has the same outcome on both sides.
- Require two live participants, rendezvous evidence, bounded joins, raw outcomes, all run/job rows, and coherent final lifecycle.
- Keep sequential controls clearly named; never count them as race evidence.

## Durable identity resolution checks

- Resolve candidates by the union of independent durable identities: canonical key, deterministic generation, stored manifest run identity, and relevant owner/workspace identity.
- Classify zero exact candidates as a possible orphan, one exact candidate as validate/reuse, any wrong candidate as fail-closed, and multiple/ambiguous candidates as fail-closed.
- Query/read errors are not proof of absence and must not enter repair.
- Test single-field tamper, combined tamper, multiple claimant rows, cross-workspace claimant, true zero-job repair, and valid unchanged replay.
- Count all relevant Job rows; never filter only canonical-key prefixes or trusted job types when testing identity corruption.

## Minimize correction loops

Before dispatch, lock one finite anti-omission matrix containing:

- every prior finding;
- combined/adversarial variants exposed by the mechanism;
- ambiguity and error-path cases;
- retained controls and explicit non-regression rows;
- exact test names, source locations, expected counts, and after-evidence paths.

Use one compact correction packet for one exact owner. Resume the same owner for the same Task ID unless canonical recovery evidence is met. After the writer exits, run:

`micro repros -> matrix 100% -> focused/static readers -> final broad gate`

Parallelize isolated read-only gates only after writer terminal. Keep shared/global gates under the project mutex. Do not run broad suites before micro and matrix closure.

For S10-C6G, read and apply the current review-routing checklist at
`C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6G_NEXT_REVIEW_READINESS_CHECKLIST_2026-09-02.md`.
Require a `NEXT_REVIEW_PACKET.md` that indexes raw commands, exit codes,
durations, hashes, node counts, owner/model/turns and every matrix row. The
packet is navigation only; independently re-run risk-critical rows.

## Verdict and next prompt

Record P0/P1/P2 findings with file:line, reproduction, actual/expected, impact, required tests, and exact owner. Check documentation arithmetic against the canonical matrix; inconsistent row counts are evidence defects.

After every verdict, write a Session Opening Proposal matching the prompt exactly: new/resume/recovery decision, context health, dependencies, maximum safe wave, exclusive write-set, model/reasoning/fallback, and dispatch authority. Always save and return the complete next Hermes prompt; never stop at a plan.
