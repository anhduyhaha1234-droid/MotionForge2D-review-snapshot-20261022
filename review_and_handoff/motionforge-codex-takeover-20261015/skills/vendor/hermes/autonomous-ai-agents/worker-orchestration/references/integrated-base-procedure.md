# Integrated-Base Procedure (S08-P00 pattern, verified 2026-08-05)

Class of work: merging two APPROVED sprint trees (S05 + S06) into one NEW
integration worktree as a preparation task before the next sprint's contract
is released. Non-destructive: source trees + MAIN stay byte-identical.

## Setup

- New worktree at expected base commit: `git worktree add
  <wt> -b codex/<name>-integration <base-sha>`. Verify `pwd`, branch, HEAD
  BEFORE any write; wrong any → BLOCKED: WRONG_WORKTREE.
- Record pre-write snapshot: `git status --porcelain=v1` counts for MAIN +
  EVERY source tree + integration tree (expect e.g. MAIN=45, S05=55, S06=45,
  INTEG=1); protected `channels.json` SHA-256; MAIN DB stat (bytes + mtime)
  without opening it; active process inventory.
- Read SESSION_PROTOCOL.md + CODEX_PM_HANDOFF.md + the final PM_REVIEW of
  each sprint (they define what "approved" means for each side).

## Copy rules

- Build exact manifests: `git -C <tree> status --porcelain=v1` — but `git -C`
  is broken with MSYS paths in git-bash (see background-worker-orchestration);
  `cd` into each tree instead.
- Classify every path: S05-only / S06-only / shared-conflict / generated
  artifact / session evidence / fixture.
- Copy FILE-BY-FILE from authoritative trees only (MAIN and old non-review
  worktrees are NOT product sources). Never recursive repo/output copies.
- For directory untracked entries: enumerate contained files, exclude
  caches/old reports, then copy only needed files.
- Exclusions: `frontend/test-results/.last-run.json`, `playwright-report-*`,
  old `output/`, `backup-pre-copy`, quarantine, launcher/watcher scripts,
  corrupt quarantined tests (e.g. `tests/test_pack_publish_ux.py`), obsolete
  nested API artifacts.

## Shared-file semantic merge

For each file both sprints modified (e.g. `app/api/app.py`, `app/api/deps.py`,
`frontend/src/lib/api.ts`, `docs/pm/ROADMAP.md`):
- Keep BOTH approved behaviors; verify neither side lost an export/route/dep.
- Backend: one authoritative session factory/root; fail-closed before
  init; no private-attribute patching; no competing engines; lifespan owns
  start/stop/resume ordering.
- Frontend: no duplicate `apiFetch`/types/exports; no nested legacy API
  resurrection; flat CAS publish contract wins.
- ROADMAP: append-only history; S00–S06 marked complete; next sprint stays
  unopened until this integration is approved.

## Verification (independent, cache disabled)

1. S05 final suite + S06 corrected suite FROM THE INTEGRATED TREE
   (e.g. 41 + 90 = 131 passed) — counts must match the recorded references.
2. Focused shared-file tests: route registration/OpenAPI, one lifespan/one
   factory, both feature APIs reachable, no obsolete routes, no duplicate
   exports, no "job service not initialized".
3. ruff on changed Python; `mypy app`; `npx tsc --noEmit`; eslint;
   `npm run build`; `git diff --check`.
4. UI smoke on a NEW isolated root `output/<task>-integration/<new-run-id>/`
   (never reuse prior QA roots): both features at desktop AND 390px, publish/
   cancel flows, no old screenshots overwritten.
5. Fresh `quality-baseline.ps1` → NEW Run ID, 7/7 PASS.

## Baseline autocrlf trap (verified 2026-08-05)

First baseline run may fail on legacy fixtures after copy due to CRLF/autocrlf
smudge. Diagnosis: `git diff` empty AND `git hash-object <file>` matches the
base blob → bytes are semantically correct; normalize fixture to source bytes
and re-run with a NEW Run ID. Keep the failed run as evidence (never delete).

## Source integrity + close-out

- Byte-identity: S05-only files in integration == S05; S06-only == S06;
  shared files have semantic evidence both sides preserved.
- Source trees + MAIN status counts and protected hash/stat UNCHANGED before
  and after. If a source tree changes mid-copy → BLOCKED: SOURCE_MOVED.
- REPORT/LOG append-only, end at SUBMITTED; TASK/PM_REVIEW untouched; never
  APPROVED. Manager writes `MANAGER_VERIFIED_PENDING_CODEX_INTEGRATION_REVIEW`
  state file; stops all writers; does not open the next sprint.
