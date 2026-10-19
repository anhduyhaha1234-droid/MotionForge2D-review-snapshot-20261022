# Manager-role variation: correction chains & final gates (verified 2026-08-22)

`pm-session-execution` SKILL.md covers the WRITER side of PM-gated sessions. This reference
covers the MANAGER/BA role the same project uses for sprint correction chains: the manager
never writes production code — it audits, routes corrections to owning sessions, runs global
verification gates, and writes evidence.

## Correction-chain close-out flow

1. **Mandatory rules load**: read the project's autopilot rules file IN FULL at session start
   AND before every dispatch/resume (re-read after compaction). Reply with the canonical
   `RULES_LOADED` marker: rules path, real repo HEAD, main sections loaded.
2. **Preflight**: worktree + branch + HEAD re-discovered live (`git rev-parse`), dirty-tree count,
   `MOTIONFORGE_DATABASE_URL` unset check, no other writer running (`ps` + port listeners).
3. **Disk audit before any dispatch**: tail each task's `LOG.md` + list `output/<task>-c*/<ts>/`
   run dirs. Corrections finished earlier THE SAME DAY appear as complete LOG entries with green
   gate logs — dispatching them again duplicates completed, already-reviewed work.
4. **Route open findings by area** to the EXACT owning session (resume, never a new session):
   backend/domain → backend owner; frontend/e2e harness → frontend owner; acceptance/verifier
   tasks never edit production. Recover the proven resume invocation from prior manager logs on
   disk (`output/codex-review-*/*.log`) and verify flags via `--help`; do not reconstruct from
   memory:
   ```
   hermes chat --resume <owner-sid> --provider <p> --model <m> -q "$(cat /tmp/brief.txt)" \
     --yolo --pass-session-id --max-turns 200 --source tool
   ```
   Brief must be self-contained: preflight pins, findings w/ file:line + repro evidence,
   exclusive write-set + forbidden paths, numbered gates with expected outputs, report/evidence
   requirements, TASK_SUBMITTED-not-APPROVED reminder.
5. **Never trust the worker's dispatch log or REPORT alone**: re-verify from disk — gate log
   tails, test counts in raw logs, netstat orphan checks, `git status --porcelain <scope>` vs
   allowlist, HEAD unchanged. Then re-run the decisive gates YOURSELF (e.g. Playwright full
   matrix ×2 consecutive runs with distinct seed UUIDs + runner self-exit + empty LISTENING
   checks).
6. **Terminal state**: write consolidated gate report under `output/<sprint>-manager-verification/<ts>/`,
   record `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`, stop all lanes, emit the
   one-shot Codex handoff (sprint scope → prior verdict → corrections applied → gates green →
   request independent review). NEVER write APPROVED/CLOSED; never open the next sprint.

## Gate menu that ran green end-to-end (S07, 2026-08-22)

Full nine-file suite (85 passed) · cross-sprint regression cluster (95 passed) · ruff app+tests ·
mypy · alembic single head · `git diff --check` · `PRAGMA foreign_key_check` = [] on a REAL
migrated temp DB opened read-only (`file:...?mode=ro`) · frontend typecheck `npx tsc --noEmit`
(`--incremental=false` is NOT a valid tsc flag → TS5023; plain `--noEmit` is correct) · eslint ·
`next build` · Playwright FULL matrix ×2 consecutive (distinct seed UUIDs, self-exit,
no post-run LISTENING) · MAIN HEAD + protected data file byte-identical start-vs-end.

Round-2 addition (2026-08-22 evening): the full lint/type battery must re-run AFTER the last
writer edit of the round — a 17:54 spec edit invalidated the 17:43 green tsc gate and only the
final re-run caught the TS18047 ×2 it introduced. Also: writer-scoped lint passes do not imply
repo-wide cleanliness (`ruff check app tests`, `eslint .`, `tsc` each caught new errors that
focused writer runs missed); verify writer-cited smoke logs for Tracebacks before citing them;
alembic temp checks need `MOTIONFORGE_DATABASE_URL=sqlite:///<temp>` env + pre-created parent
dir (`mkdir -p`), not `-x db_url=`.

## Manager-side pitfalls

- **Wrong-config reproduction**: sibling playwright configs with near-identical names may differ
  in webServer wiring; reproducing with the stale one manufactures a fake root cause ("wipe never
  ran") while the accepted-evidence config is fine. Match mtime + webServer command block against
  prior evidence BEFORE concluding.
- **Teardown hang ≠ lost results**: when a PW runner finishes tests but never exits (orphaned
  webServer child), results are already in `test-results/` / reporter output — read them instead
  of waiting on `process(wait)` forever; detect staleness via log mtime vs `date`.
- **Consent-gated kills can block mid-flow**: batched `Stop-Process` / `rm -rf` may sit awaiting
  user consent in background review mode. Don't retry; record the specific PID as residual risk
  and continue with read-only gates.
- **Heartbeat discipline**: poll worker progress via log-tail greps every few minutes; audit on
  ≥8 min of silence (process alive? waiting on input? log frozen?). Report the first failure
  immediately; retry connection errors only after the mandated wait, same session/model.
