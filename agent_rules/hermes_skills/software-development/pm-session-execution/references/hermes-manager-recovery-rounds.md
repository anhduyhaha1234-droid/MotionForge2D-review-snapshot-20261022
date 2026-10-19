# Hermes Manager correction / recovery rounds (proven S10-C6H C15→R1→R2, 2026-09)

Field-proven recipe for PM-gated **bounded correction rounds**: Codex verdict arrives with
`CHANGES_REQUESTED / <EXACT_GAP> / NOT_APPROVED`; Manager must drive
RED → minimal fix → GREEN → gates → packet with exactly ONE worker. Every step below was
executed end-to-end (S10-C6H R1 union-identity-resolver; R2 relevant-manifest-scope) and each
repeat exposed a pitfall that cost a review cycle.

## Dispatch & runtime facts (Windows, Hermes CLI, git-bash)
- Command shape — log dir MUST exist before the redirect:
  ```bash
  mkdir -p output/s10/c6h/<round>/worker && export HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900
  hermes -z "$(cat <packet-file>)" --provider custom -m <EXACT_MODEL_ID> --yolo --no-restore-cwd \
    > output/s10/c6h/<round>/worker/<round>_worker.log 2>&1; echo "EXIT:$?"
  ```
  Run with `terminal(background=true, notify_on_complete=true)` — never foreground. Packet via
  `-z "$(cat file)"` is safe (command-substitution output is not re-parsed for quotes); keep prompt
  short (<8K; split into two files if larger). `--resume <old>` creates a **NEW effective session ID**
  (parent stays None): record requested-ID + effective-ID + timestamp + same Task ID in the registry
  immediately (append-only), BEFORE the worker's first write.
- Model probe before dispatch: `hermes -z "Reply with exactly: PROBE_OK" ...` → verify the resulting
  state.db row shows the EXACT model id (`ocg/deepseek-v4-flash`, not bare `deepseek-v4-flash`).
- **RUNTIME_CONFIG_GAP (persistent CLI behavior)**: oneshot/resume sessions record
  `model_config={"max_iterations": 90, "reasoning_config": null, "max_tokens": 16384}` even when the
  prompt demands reasoning max/fallback OFF. Protocol: log the real state-row values, continue on the
  same exact model route, NEVER claim "reasoning max proven", compensate with extra Manager verification.
- `process(action='wait')` clamps at 180s → loop it; every ~3–10 min run a real status check
  (state.db message/tool counts growing, new evidence files, sha256 of critical files, ps alive)
  so you can answer "estimate bao giờ xong" with a `date`-anchored ETA table instead of guesses.
- Worker writes its final report to the log ONLY at exit; an empty log is NOT a dead process.
  Liveness = process alive + message_count growing + file/hash activity.

## Preimage & ownership gates (before ANY mutation)
- Pin: worktree, branch, HEAD, critical-file SHAs, dirty porcelain count, DB env UNSET (both
  `MOTIONFORGE_DATABASE_URL` and `MOTIONFORGE_DB_PATH`), 0 writer processes, task ports free.
  Any mismatch → `BLOCKED_PREIMAGE_DRIFT` with actual hashes; do NOT self-restore.
- Manager-owned byte snapshots → `<round>/manager/guard/snapshots/<file>.pre_<round>`; verify snapshot
  hash == source hash BEFORE dispatch; post-worker audits diff against these snapshots.
- Owner transfer (rules §4/§8): any SECOND forbidden write in a lineage → freeze the ENTIRE lineage,
  create exactly ONE fresh recovery worker for the SAME Task ID, append registry record with the exact
  reason string (e.g. `REPEATED_FORBIDDEN_COPY_OVERWRITE_AFTER_RECOVERY_TRANSFER`). Evidence = raw
  state.db tool messages (see audit), NOT worker prose.
- Critical-file edit contract for recovery workers: unified/V4A patch mode ONLY, one small hunk at a
  time; forbidden: patch mode=replace / fuzzy whole-string, write_file on existing files, cp/copy/
  Copy-Item/move/rename-overwrite, delete/recreate/truncate, shell redirection or script direct-write,
  restoring snapshot/.bak over the working file. Broken patch → STOP + `BLOCKED_UNSAFE_WRITE`, preserve
  the broken bytes as evidence; never self-restore from a snapshot (that itself is a forbidden write).

## Raw session tool-call audit (MANDATORY before any positive packet)
Scan worker session messages read-only (sqlite URI `file:...state.db?mode=ro`) for:
- write_file / Set-Content / Out-File targeting critical files;
- patch mode=replace or fuzzy whole-string; cp / copy / Copy-Item / move / rename-overwrite;
- shell redirection/direct-write scripts against critical files; wrong provider/model/fallback.
Tip: text occurrences of forbidden strings inside packet prose (user/tool file-content messages) are
NOT events — only actual tool calls/results count. Confirm by message role and JSON shape.
Zero forbidden critical-file write is required for a positive terminal.

## Patch-tool realities (worker perspective)
- `mode=replace` fuzzy patches on large files drift indentation and sometimes break the file. The
  project rules FORBID script direct-write as a replacement (that triggers owner transfer!). Only V4A
  hunks; a `no files were modified` rejection is fail-safe (zero mutation) → OK to retry with a
  corrected preimage.
- Escape-drift: the V4A patch tool rejects `old_string` containing `\"` when the file literally holds
  a backslash-quote. Pass the line UN-escaped (matcher normalizes) and avoid backslashes in new
  f-strings entirely.
- After EVERY hunk: sha/line-count/size delta + `py_compile` + targeted collect.

## RED-first correction loop
1. Add/extend failing tests FIRST (unified patch), run them on the CURRENT route → save raw RED log.
2. Patch production minimally; then micro → retained matrix → full module → focused ×2 → broad ×2,
   all on fresh isolated basetemp `%TEMP%/mfc*_*`, `-p no:cacheprovider`, DB env UNSET.
3. Test-count arithmetic: new tests append above the retained baseline (62→68→70); explain any delta
   by collected node IDs, never by moving the gate.
4. Worker gates then Manager independent gates (same commands, fresh roots, on the frozen hashes);
   Manager proves counts/durations itself and never trusts the worker report alone.

## Evidence, registry, terminal vocabulary
- Registry/LOG/REPORT are append-only; corrections must explicitly mark earlier statements
  `SUPERSEDED`, never rewrite history. Role-invalid claims (e.g. a Manager packet stating
  `APPROVED / SPRINT_CLOSED`) are superseded, not deleted.
- The final `NEXT_REVIEW_PACKET.md` must have mtime LATER than every cited gate log, and must not copy
  stale counts without reconciling new tests.
- Manager positives: `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`; CLOSED/APPROVED are
  Codex-only. Negative terminals: `BLOCKED_PREIMAGE_DRIFT`, `BLOCKED_CONCURRENT_WRITER`,
  `BLOCKED_MODEL_ROUTE`, `BLOCKED_UNSAFE_WRITE / CODEX_DECISION_REQUIRED`, `BLOCKED_TEST_AUTHORITY`.
- Heartbeat = lightweight file evidence + completion notification, not a delivery system.
- User "estimate/bao giờ xong": run `date` first, lead with status, ETA table with date anchors; a
  worker iteration-ceiling (90) is NOT a sprint verdict — resume the latest effective session and
  continue in the same Manager turn.
- This host's command parser blocks some compound bash (e.g. `grep -c ""`, `$(...)` substitutions in
  complex one-liners) — split into small commands and prefer `wc -l` over `grep -c ""`.