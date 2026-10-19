---
name: ai-code-review-resilience
description: "Use when agent-built code faces adversarial AI review."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [code-review, testing, production-wiring, durable-jobs, adversarial-review]
    related_skills: [terminal-engineering-discipline, motionforge-autopilot, test-driven-development, requesting-code-review]
---

# AI Code Review Resilience

## Overview

An external AI reviewer (Codex, Claude, another Hermes) reviews agent-built
work adversarially. Rounds of `CHANGES_REQUESTED` are normal — but each round
costs hours. This skill encodes the patterns that PREVENT rounds, learned from
a real sprint that burned 4 correction rounds (C01→C04) on one systematic
root cause.

## User preference (first-class, from the user who runs this loop)

> "Đừng test giả nữa — hãy test thật kỹ rồi hãng đưa cho codex review."
> (No fake tests. Test thoroughly and for real, THEN give it to Codex review.)

- NEVER submit work whose only proof comes from dependency-injected or
  monkeypatched tests.
- Before SUBMITTED, prove the REAL production path with a pristine test.
- An honest "5/6 passed, 1 flaky race documented" beats a claimed "6/6" that
  was never actually run on the final bundle.

## Variant: focused independent read-only review (user-requested)

Use when the user asks you to **independently REVIEW** a specific subsystem,
core, or worktree deliverable **read-only** — distinct from reviewing your own
pre-commit diff. No `git diff` to scan, no reviewer subagent to dispatch, and
**no writes of any kind**.

**Hard rules (read-only phase)**
- NO file writes — not product code, not tests, not docs. Do not create files.
- Do NOT run migrations, start servers, or execute the code under review.
  Verification is by reading + cross-referencing only.
- Never modify a file to "prove" a finding. A finding stands on the text as it
  exists; if a vector can't be cited from the file, it isn't a finding yet.

**User-specified findings-list output contract**
For every finding, give exactly these four fields, dense and actionable:
1. **Exact vector** — file + line number + the code snippet.
2. **Why it matters** — what breaks, what silently goes wrong, who trips.
3. **Missing negative test** — the precise test that would have caught it
   (name the assertion, not just "add tests").
4. **Severity** — P0 / P1 / P2.

Severity rubric:
- **P0** — live test failure, data loss, or a policy not enforced where it
  matters (e.g. migration/ORM mismatch that a parity test already compares).
- **P1** — contract hole or silent wrong behavior a consumer would trip on;
  validation missing where the contract requires it.
- **P2** — consistency/robustness, edge-case policy ambiguity, no corruption.

**Always close with what IS sound.** A review that only lists failures is
unusable — name the parts of the design that are correctly implemented and
tested, so the reader knows what not to touch.

### High-leverage techniques for migration / ORM / repository cores

**Schema-migration-ORM trio parity (highest yield).** When reviewing a
migration plus its ORM model, diff them against each other rather than reading
them separately:
- For **every FK** in the migration DDL, grep the ORM for the same column and
  compare `ondelete` (CASCADE vs RESTRICT). A mismatch here is usually a
  **live test failure**, not a latent gap: parity tests compare FK options, so
  the mismatch is findable by a cheap direct comparison instead of by running
  the suite. Found on MotionForge2D S08-A02: the migration still CASCADEd
  `occurrence_segment.role_id` while the ORM declared RESTRICT.
- Compare **CHECK literals** byte-for-byte (frozen migration literals vs
  ORM-derived constants). Drift means the enum validated in app code is not
  the enum the DB enforces.
- Compare **partial-index predicates** and unique-column sets — a partial
  unique index omitting the lineage column silently allows duplicate
  historical rows.

**Idempotency equivalence-helper completeness.** For every
`_assert_equivalent_*_request`, verify it compares the **same identity fields
the natural key uses** — segment id, endpoint ids, contact kind, start frame.
The segment helper usually includes them; the edge/motion helpers usually omit
them by copy-paste. A replayed idempotency key that skips identity fields
returns the existing row bound to a *different* segment under the caller's
payload.

**Generation semantics.** Check `!=` vs strict-advance comparisons, and
whether a same-generation manual-correction path exists at all. An error
message claiming "must advance" while the code only refuses equality permits
backward generations into a lineage ordered by `created_at`.

**Containment re-validation.** Range-within checks are usually create-time
only. Verify no `update_*` path re-validates containment against already-
attached dependents, and whether time containment is checked at all (many
helpers check frames only).

**Ownership re-validation on replay.** Idempotency replay returning the
existing row without re-running the ownership chain hands back a row bound to
a trashed artifact or superseded segment.

### Pitfalls
- **"No test exists" ≠ "the code is wrong"** — cite the missing negative test
  as the gap; that is the actionable fix.
- **Line numbers drift.** Verify each cited vector by reading the file at the
  cited location before reporting; never cite from memory of a prior read.
- **Never trust a comment's claim over the code.** A docstring saying "RESTRICT
  (was CASCADE in draft)" is a claim — grep the actual `ForeignKey(...)` call.
  The trio-parity check lives or dies on this.
- **Read-only reviews are not debugging.** If you find a runtime defect you
  cannot fix (writes forbidden), report the exact reproduction path so the
  owner can fix it — do not attempt a workaround that requires writing.

## The core pattern: DI tests hide production wiring defects

If every test monkeypatches module globals (`deps._job_service`,
`deps._lifecycle_db`), the real default path (`app.main:app`) can be
completely broken while 100% of tests pass. Each review round that forces
tests one layer closer to production exposes a NEW real defect:

| Round | Layer forced closer to production | Defect exposed |
|---|---|---|
| 1 | UI → approved API surface | UI called legacy endpoint; retry was a rendered 500, not a real successor |
| 2 | Route → read-only semantics | GET endpoint secretly advanced the chain; chain logic lived in routes |
| 3 | Lifecycle → app lifespan | Orchestrator started only via POST, not wired into lifespan |
| 4 | Wiring → pristine no-DI path | Default JobService bound a placeholder worker ("job service not initialized") |
| 4b | Cache → fail-closed binding | Orchestrator cached a competing factory when service uninitialized; stage-boundary assertions missing from restart test |
| 4c | UI → cancel reliability | Cancel target from polled chain snapshot went stale during step transitions (0 /cancel requests reached backend); visual evidence internally inconsistent (100% label, partial bar) |

## Mandatory checklist BEFORE first submission (not after rejection)

1. **Pristine production-path test from the FIRST task of the sprint**:
   - temporary isolated root/database only (never MAIN/worktree data);
   - import the REAL app entrypoint (`app.main:app`) with default dependency
     path — no injection, no monkeypatch of module globals;
   - enter the real app lifespan (TestClient startup/shutdown);
   - exercise the real flow once (e.g. POST analyze), then restart the app
     lifecycle over the SAME temp DB in genuinely fresh module state
     (fresh subprocess — two TestClient contexts over one bound singleton is
     NOT a restart);
   - assert "job service not initialized" (or equivalent) NEVER appears in
     captured worker logs.
2. **Read-only endpoints are read-only**: GET must cause ZERO database
   mutations on repeat/concurrent calls. Test it adversarially — grep the
   handler, then prove zero row changes.
3. **Retry = successor Job** (real idempotent successor with owner validation),
   not honest rendering of an IdempotencyKeyInUse 500.
4. **Lifecycle owned by the app lifespan**: startup scans and resumes
   incomplete work without POST/GET/polling/manual advance; shutdown stops
   cleanly.
5. **Chain/job identity binds to immutable input evidence** (source SHA-256 +
   generation). Replacing the source creates a NEW chain; old jobs/artifacts/
   scenes stay immutable; state exposes only the current source.
6. **Stage-boundary assertions in restart tests**: assert intermediate counts
   per generation (gen1: proxy=0/scene=0 → gen2: proxy=1/scene=0 → gen3:
   scene=1 → gen4: no duplicates). The test must FAIL if a successor completes
   before its intended restart point — a happy-path-only restart test is
   insufficient evidence.
7. **No competing/cached fallback factories**: a cached singleton (e.g.
   orchestrator cached by object identity) must NOT fall back to a competing
   factory when the authoritative service is uninitialized — fail closed
   (raise) or provide an explicit public rebind. Add a regression test:
   access before init → init → obtain → prove the authoritative factory is
   used and no stale cache survives.
8. **Deferred verification gets rejected**: if the reviewer explicitly
   requires Playwright desktop/mobile + fresh 7/7 baseline, RUN them — with
   NEW isolated evidence dirs/run IDs, never overwriting existing artifacts.
   If safe isolation cannot be established, stop BLOCKED rather than claiming
   the gate passed.
9. **Status lines stay consistent**: flipping to SUBMITTED means TASK.md,
   REPORT.md AND LOG.md all flip; append correction-round sections without
   erasing prior evidence; never claim APPROVED.
10. **Baseline on FINAL code**: any edit after the baseline run (even docs)
    → re-run fresh 7/7 and record the new Run ID.
11. **User-action flows must be reliable under state transitions** (cancel/
    retry buttons): if the UI derives the action target (e.g. active job id)
    from a polled chain snapshot, that snapshot can go stale between render
    and click — the click then sends NO request or targets a terminal job
    (reviewer reproduced: cancel failed 2/2 with zero /cancel requests
    reaching the backend). Do NOT waive as "machine too fast", add sleeps,
    enlarge fixtures or mark flaky. Fix with the smallest robust design:
    re-resolve current chain state at action time (retry safely when the
    previously observed job became terminal) or add an atomic backend
    chain-level endpoint that resolves the active job server-side. Fail
    honestly when the chain genuinely completed. Evidence: cancel request
    reaches the real isolated backend, job enters cancelling/cancelled,
    retry remains available, no successor/orphan effects, pass 3×
    consecutively, full suite 6/6, mobile variant too.
12. **Tests that use the production default path must not leak into the
    worktree**: a test initializing the default service with a CWD-relative
    managed root (e.g. `Path("artifacts")`) resolves INTO the worktree under
    pytest CWD, creating real directories in the repo. Fix isolation without
    weakening the default-path assertion: `monkeypatch.chdir(tmp_path)` (or
    a fresh-process boundary), assert the resolved root is inside tmp_path,
    assert NO worktree artifacts dir was created/modified. All test files and
    DBs stay under pytest temporary storage.
13. **Visual completion evidence must be internally consistent**: a
    screenshot showing step labeled 100% but with a partially rendered
    progress bar is either an unfinished CSS transition or a product bug.
    Determine which; if transition-only, wait for the rendered bar to reach
    full width before capturing; if product bug, fix the smallest rendering
    issue. Add an assertion that every completed step displays 100% AND has
    a visually full indicator. Regenerate only the C04-specific screenshots
    in new evidence dirs — never overwrite earlier evidence.

## Behavior-truthfulness review class (Codex rounds C3→C6 + T02-C1/C2, 2026-08)

Codex's CHANGES_REQUESTED rounds on the S08-A02 structural-evidence /
object-extraction core kept firing on a distinct CLASS of defect:
**silent fabrication + non-determinism + exception-swallow in production
paths**. Prevent these UPFRONT — each one costs a correction round:

1. **Never use Python `hash()` on strings for stable identities/transforms.**
   `hash(str)` is randomized by PYTHONHASHSEED across processes, so QA
   evidence diverges between runs. Use `hashlib.sha256(...).digest()` or
   `uuid5` derived values. *Proof test:* two fresh SUBPROCESSES with
   `PYTHONHASHSEED=1` vs `=999` run the ACTUAL publication path (real repo,
   real handler, fresh SQLite) and must produce byte-identical prompt/seg
   JSON, mask SHA, transforms, refs, kinds/ranges, provenance, ordering. The
   test must fail if the implementation reverts to `hash()` — and it must NOT
   recompute the formula inside the test (that only re-checks the tester).
2. **Production must be TRUTHFUL; synthetic/simulated evidence is QA-only.**
   Gate every synthetic motion/occlusion/contact/provenance/algorithm behind
   `qa_mode AND provider in (qa-providers)`. Never infer contact/occlusion
   merely because two segments exist; never fabricate a sparse-flow reference;
   never emit an observation when there is no estimator/evidence. Production
   segments must carry the ACTUAL provider algorithm — a `deterministic-layout`
   fallback in production is a review blocker.
3. **Never fabricate missing input.** Missing/malformed bbox → FAIL CLOSED or
   omit the prompt evidence (never a canned `{x:10,y:10,w:50,h:50}`). Invalid
   confidence (missing/NaN/+Inf/−Inf/out-of-range) → raise, never clamp or
   silently default (e.g. the classic `cand.get("confidence", 0.7)`). QA
   records that ARE synthetic must carry explicit provenance markers
   (`provider`, `qa_mode`, `synthetic`, `test_adapter`).
4. **Operator-precedence exception-swallow bug (high-yield grep).** The pattern
   `if isinstance(exc, X) and "msg" in str(exc) or "msg" in str(exc): pass`
   swallows ANY exception whose text merely CONTAINS the substring — because
   `and` binds tighter than `or`. Codex repro'd a wrong-type exception carrying
   the text "already bound" being silently eaten. Fixes: typed-only catch
   `isinstance(exc, X) and ("msg" in str(exc))` with explicit parens, or better:
5. **Don't classify domain outcomes by exception-message substring at all.**
   If the repository returns `(record, created)`, handle idempotent replay by
   `created=False` and DELETE the try/except swallow around the create call —
   let the typed conflict exception propagate and roll back the transaction.
   Exception TEXT changes must never affect logic.
6. **Scale-proof every SQL statement's bind budget.** Hard caps like "chunk to
   900 then `or_(IN(c1), IN(c2), ...)`" still put the TOTAL video count into
   the final COUNT/page SELECT. SQLite also has a 500-term compound-SELECT and
   ~999-param limit. Prefer `json_each(:json)` (SQLite JSON1) so ONE JSON text
   param covers an unbounded id set — capability-checked, fail clear if
   unavailable, never raw interpolation. Instrument the ACTUAL emitted
   statement + parameters (`before_cursor_execute`) and assert the final
   COUNT/page SELECT bind count stays bounded independent of dataset size.

## Independent sprint-gate review: evidence freeze before verdict

For a PM/Codex review of an entire sprint, treat every report, status file,
claimed baseline, and manager verdict as an assertion until reconciled with the
live worktree and raw output. The review is not frozen while an owning writer
process can still mutate the reviewed files.

1. **Freeze the evidence first.** Query the actual process table for the
   owning session and its wrapper/tee children; record PID, command line, cwd,
   start/elapsed time, and latest log mtime. Compare that with the manager
   state. A status line saying `writers: none running` is not proof. If a
   writer is live, do not kill it during a read-only review, but mark the
   workspace unfrozen and do not accept its evidence.
2. **Reconcile lineage and filesystem.** For each task, match the owning
   session ID, provider, model, reasoning, fallback, timestamps, allowlist,
   report state, evidence directory, and actual file hashes/mtimes. A report
   mentioning an evidence directory that does not exist is a placement/evidence
   defect, not a green result.
3. **Classify tests by what they really exercise.** A Playwright test using
   `page.route("**/*")` or `route.fulfill()` for business endpoints is mocked
   harness coverage. It is not real vertical evidence. Real vertical proof
   must traverse the product page, real API, repository, isolated database,
   and reload from persisted truth; keep mocked loading/error tests labeled as
   mocked.
4. **Run the final code, not the reported code.** Use a fresh temporary DB,
   `MOTIONFORGE_DATABASE_URL` unset, `-p no:cacheprovider`, and a new evidence
   run. If correction tightens a production invariant, old fixtures that omit
   required assets may fail; repair fixtures/assertions to be production-
   realistic, never weaken the invariant or accept `pass or skip` branches.
5. **Check contract surfaces, not only internals.** A runtime guard is not
   enough if OpenAPI still marks a required CAS field optional, or if a
   supposedly server-owned workspace remains a client query parameter. Verify
   evaluate/create/repin share one policy, authority failures fail closed, and
   UI advisory flags never bypass backend acceptance.
6. **Gate strictly.** Any P0/P1, unfrozen writer, failed focused suite,
   missing real vertical scenario, or unverified protected-data/process check
   means `CHANGES_REQUESTED`; do not grant next-sprint authority. Findings
   should cite exact file/function/line, reproduction, expected/actual,
   product impact, missing assertion, and owning task/session.

### Review-specific reference

See `references/independent-sprint-review-evidence-gate.md` for the compact
preflight, mocked-vs-real classification, production-realistic fixture rules,
and correction-gate reproduction patterns.

## Manager verification (never trust the worker's self-report)

- Re-run the focused tests yourself, with `-p no:cacheprovider` (pytest cache
  masks failures) and a Windows-native `--basetemp` path.
- Grep the CODE for the removed anti-pattern (e.g. `session_factory is None`
  fallback) — don't just read the REPORT's claim.
- Check protected hashes (`channels.json` SHA), MAIN-tree git status count,
  and DB stat before/after.
- Verify placement: a task reporting SUBMITTED but leaving the worktree's
  REPORT untouched is misplaced (cwd bug — see dispatch pitfalls below).

## Windows worker-dispatch pitfalls (verified)

These bite when dispatching `hermes chat` workers from PowerShell on Windows
git-bash:

1. **Long `--query` prompts with double quotes fail (exit 2).** A 6–8KB
   prompt containing `"` gets mangled through bash→PowerShell→CLI argv: quotes
   stripped, trailing text becomes stray args
   (`hermes: error: unrecognized arguments: ...`). FIX: keep prompts ≤ ~2KB,
   NO embedded double quotes; point the worker at packet files ("read
   TASK.md and START_PROMPT.md completely, follow exactly") instead of
   inlining the contract.
2. **Never run two instances of the same runner script concurrently.** A
   second run while the first is live fails with Tee-Object file-lock
   IOException/exit 127 (same append target). Launch once in background;
   verify via process query + log growth, never by re-running the script.
3. **PowerShell wrapper PID ≠ worker PID.** The wrapper may look "DEAD" while
   the real worker (hermes.exe + python.exe, `CommandLine` containing "chat")
   is alive. Query Win32_Process for CommandLine match, check log mtime,
   before concluding failure.
4. **`hermes chat` CLI does not inherit the script's `Set-Location`** when the
   desktop daemon runs — the worker may execute with the daemon's cwd and
   write to the WRONG repo. Enforce cwd inside the prompt ("run `pwd` first,
   `cd` if needed") and verify placement after the run.

## References

- `references/s05-sprint-correction-rounds.md` — the full C01→C04 round
  chronology with each reviewer finding and the fix that satisfied it
  (session evidence, 2026-08-05).
- `references/s08-a02-readonly-review-example.md` — worked example of a
  focused read-only review: the trio-parity technique that surfaced a P0 as
  a live test failure, the recurring bug classes found in the
  structural-evidence core, and the findings-list output contract.
- `references/s08-a02-truthfulness-scalability-rounds.md` — the C3→C6 and
  T02-C1/C2 blocker families with EXACT repro commands (5001-video SQL bind
  instrumentation, cross-process PYTHONHASHSEED determinism, conflicting-
  idempotency matrix, flaky-counter ×30 loop) and the `json_each` /
  stable-digest / typed-catch fixes that satisfied Codex.
