# S07 Final Gate & Correction-Chain Close-Out — C3 harness round (verified 2026-08-22)

Session evidence for the manager-side lessons now in SKILL.md (disk-audit-before-dispatch,
defect routing, resume invocation, final-gate checklist). Companion to
`s07-project-cast-reuse-linear-sprint.md`.

## 1. Disk audit before dispatch found half the chain already DONE

Prompt arrived describing P1a/P1b/P2 as open work. Before dispatching anything, tail
`docs/pm/sessions/*/LOG.md`: T01-C4 (both P1s) had finished 11:26 and T02-C2 (P2) 11:41 the
same day, with full gate logs under `output/s07-t01-c4/20260822_110655/` (38 passed ×2, full
nine 85 passed) and `output/s07-t02-c2/20260822_113953/` (compat 21 + picker 7 passed).
Re-dispatching them would have duplicated completed corrections inside one review boundary.
Only genuinely-open work was dispatched (T02-C3 below).

## 2. T02-C3: two real harness defects surfaced ONLY by the manager final gate

- **F1 dual-project state bleed**: `playwright.s07t03.config.ts` had grown a second project
  (`mobile-390`) AFTER the accepted T03-C1 evidence (whose log ran 2× [desktop] only). Test
  "Scenario I desktop" runs under BOTH projects → project A/B each execute `fullScenarioI`
  twice against ONE shared seeded DB. Second pass hits natural-key/idempotency 409 after the
  V1→V2 repin → mobile lane fails at `submit-success` while each lane passes standalone.
  Lesson: when a playwright config gains projects/tests after acceptance evidence was recorded,
  the FULL matrix has never been proven — run it before trusting old "2 passed" logs.
  Fix (writer): per-test cleanup (list+delete existing mapping for target + cross-project C)
  at top of `fullScenarioI`, plus already-published handling on publish.
- **F2 orphan uvicorn on teardown**: boot wrapper used `os.execv`. On Windows execv does NOT
  replace the process — Python spawns a NEW pid then the wrapper exits, so Playwright kills the
  dead wrapper pid and uvicorn survives holding port 8004 + the SQLite file (3 consecutive orphans:
  pids 19432/19744/16212, each found via `netstat -ano | grep LISTENING | grep :8004`, killed via
  `powershell Stop-Process -Id <pid> -Force`). Symptom: runner hangs forever after "N passed".
  Fix (writer): `subprocess.Popen` + wait + signal forwarding so the wrapper keeps the child pid.
- **Manager self-caught misdiagnosis**: first reproduction used a STALE config
  (`playwright.s07t03-real-vertical.config.ts`, no webServer boot wiring) — concluded "harness
  never wipes" before noticing two configs existed. Check mtimes + which config prior evidence
  actually invoked BEFORE writing root causes into reports.

## 3. Proven worker-resume invocation (T02 owner)

```
hermes chat --resume 20260821_044658_7fde0f --provider muse \
  --model ocg/muse-spark-1.2-contributor -q "$(cat /tmp/prompt.txt)" \
  --yolo --pass-session-id --max-turns 200 --source tool
```

Brief must be self-contained: preflight pins, findings with file:line + reproduction evidence,
exclusive write-set AND forbidden paths, numbered gates with expected outputs, report/evidence
requirements, TASK_SUBMITTED-not-APPROVED reminder, BLOCKED_DEPENDENCY stop rule. Flags verified
against `hermes chat --help`; pattern recovered from `output/codex-review-s07/*/manager_s07_session.log`,
not memory. Writer finished 12m42s / 143 tool calls; every claim re-verified from disk
(`output/s07-t02/20260822_155527/`: run1+run2 4 passed, netstat no LISTENING, pytest 28 passed,
head.log unchanged).

## 4. Manager final sprint gate — full checklist that ran green (2026-08-22 16:12+07)

Full nine-file S07 suite **85 passed** (66.8s); regression cluster (S06-surface + S08 files,
7 files) **95 passed**; ruff app+tests clean; mypy 96 files clean; alembic single head
`b2c3d4e5f6a7b`; `git diff --check` clean; `PRAGMA foreign_key_check` = [] over 28 tables on a
REAL migrated temp DB opened read-only (`file:...?mode=ro`); frontend typecheck
(`--incremental=false`) exit 0; eslint exit 0 (9 pre-existing warnings); `next build` exit 0;
Playwright FULL matrix ×2 consecutive runs with DISTINCT seed UUIDs (20091820… / 36ec7379…),
both **4 passed**, runner self-exits, post-run netstat shows NO LISTENING on 8004/3014;
MAIN HEAD `a43b20da` + `data/motionforge.db` 311296 B byte-identical start-vs-end. Consolidated
report written to `output/s07-manager-verification/20260822_1612/manager_final_gate.md`;
terminal state `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW` with a one-shot Codex
handoff paragraph (sprint scope, prior verdict, corrections applied, gates green, request for
independent review). No APPROVED/CLOSED written anywhere.

## 5. Tooling notes from this round

- `process(wait)` on a Playwright run that finished tests but hung in teardown returns duplicate
  "still running" outputs forever — detect via log mtime staleness (`stat -c %y log` vs `date`)
  instead of waiting blindly; test RESULTS are already on disk in `test-results/`.
- `timeout 540 npx playwright …` in MSYS wraps the runner in job-control-less bash: EXIT=124 kills
  mid-run. Rely on playwright's own per-test timeout instead of shell `timeout`.
- Consent-gated destructive commands (`Stop-Process` batches, `rm -rf` temp roots) may BLOCK
  silently in background review mode — don't retry; record the orphan pid as residual risk and
  continue read-only gates.
- `grep -c LISTENING netstat_runN.log` returning 0 matches (exit 1) IS the desired green
  evidence for orphan checks — don't treat exit 1 as tool failure there.
