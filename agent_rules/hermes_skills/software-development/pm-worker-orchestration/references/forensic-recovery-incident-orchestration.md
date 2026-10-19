# Forensic test-authority recovery — Manager orchestration (C14-T3 pattern, 2026-09-02)

When a worker destroyed a source/test file and Codex authorizes a guarded
resume with an EXACT-HASH candidate gate, the Manager's job is evidence +
routing, never reconstruction. Proven shape on MotionForge2D S10-C6G C14-T3.

## 1. PREP-INCIDENT evidence bundle (Manager-owned, `output/s10/<round>/manager/recovery-*/`)
Write `PREP_INCIDENT.md` capturing, with real command output:
- rules/instruction hashes (path, logical line count, SHA-256 vs canonical) +
  binding PM decision + binding prompt paths;
- timestamp/timezone (`date "+%Y-%m-%d %H:%M:%S %z"`);
- worktree/branch/HEAD + `git status --porcelain` count (carry dirty
  attribution; nothing reset/cleaned/committed);
- `MOTIONFORGE_DATABASE_URL` UNSET proof + state.db size/mtime (mode=ro);
- owner process scan (command lines; exclude generic Hermes desktop/serve) —
  zero C14/T01C worker = the resume precondition; task ports free (`netstat`);
- all current hashes/line counts: destroyed `.bak`, reconstructed main,
  recovery variants, route (FROZEN), target pre-destruction SHA, frozen files;
- immutable incident facts (Codex numbers supersede Manager claims: "58 failed/
  5 passed" beats "9 fail"; original pyc NOT preserved → not authority);
- model-route probe result (`hermes -z "reply exactly: pong" -m <selector>
  --provider <p> --yolo` → pong).
Then `sha256sum PREP_INCIDENT.md > PREP_INCIDENT.md.sha256` (SHA-manifest).

## 2. Owner-ledger correction (append-only, never rewrite history)
- Registry/ledger IDs have proven STALE. Identify the actual writer from
  read-only state.db (`sessions.message_count`/`tool_call_count` + `model`;
  see hermes-session-forensics). C14: ledger `20260901_230235_b80d4b`
  (4 msgs/1 tool) vs actual `20260902_013803_4d5ce5` (88 msgs/41 tools).
- Append: (a) one registry line naming actual owner + destructive message IDs
  (146796/146797) + "do not resume <stale id>"; (b) an append-only CORRECTION
  section to the existing RECOVERY_REPORT listing what supersedes what; (c)
  the dispatch ledger line when the worker goes out (prompt file, PID,
  proc id, model, expected terminal).

## 3. Resume prompt recipe for the exact-hash gate (§5.3-style)
Header = "session của bạn: <actual owner>". Sections, in order:
1. Mandated reads (rules + binding prompt + manager PREP + RECOVERY_REPORT).
2. "Context của chính bạn" — one honest paragraph about the destruction
   (the worker destroyed the file; Codex authorized ONE guarded resume; no
   replacement session; no resume of stale ID).
3. Verified current state (hashes, line counts, what is/ isn't authority,
   pyc invalidation, route frozen).
4. **Phase A allowed writes** (the damaged file ONLY via apply_patch after
   candidate gate; append-only LOG/REPORT; new evidence dir).
5. **FORBIDDEN list verbatim** (write_file / Set-Content / Out-File / shell
   redirection / heredoc write / Python direct write / Copy-Item|Move-Item
   replace / editor save on the damaged file; memory rebuild; Git destructive;
   pyc as source; skip/xfail/assertion weakening; %TEMP% as only location).
   Consequence spelled out: `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`,
   no third resume.
6. **Exact candidate gate**: read-only SQLite export recipe starting from
   known message IDs; prefer READ-PAYLOAD stitching (tool read_file results
   with `N|...` content, coverage print "COVERED 1..N" / gap list); fallback
   replay (base write_file + ordered patches resolved by
   `effect_disposition` + col-0 def blocks from drift-skipped patch
   new_strings); candidate stored OUTSIDE the repo tests dir; binary gate =
   SHA-256 exactly equals target (similar line count/names/compiling/passing
   a subset is NOT a substitute); on failure STOP with
   `BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION` and name the missing
   interval; only after exact hash: deterministic unified diff → apply_patch →
   immediately re-hash main file.
7. **Bounded delta** (e.g. 57 retained nodes + 5 new = 62 unique; zero
   missing retained node; zero duplicate `def test_`; zero unresolved helper).
8. Run list (`py_compile`, ruff --select F, `pytest --collect-only -q`, full
   module on fresh short root, DB UNSET, `-p no:cacheprovider`).
9. Terminal: `TEST_AUTHORITY_RECOVERED` (structural/provenance pass) → STOP
   for Manager R-GATE — NOT TASK_SUBMITTED, no production edit in Phase A.

## 4. Dispatch + phase discipline
- Dispatch ONLY after zero-writer proof + route probe. `background=true,
  notify_on_complete=true`, `mkdir` log dir before redirect, log tail gets a
  `WORKER_EXIT=$?` line.
- Post-resume 0-byte dispatch.log for 5-10 min is compression silence
  (normal). Confirm the `↻ Resumed session <id>` line appears before treating
  the lane as running; confirm the resumed id == the ACTUAL owner (a resume
  against the stale id is the same owner-lineage mistake the decision warns
  about).
- Phase A ends at worker stop; Manager R-GATE is read-only verification of
  candidate/restored hashes, export+replay script, node arithmetic, no
  duplicate/helper/memory-written body, and the raw full-API result
  classification. Phase B (production closure) opens only after R-GATE green.

## 5. User cadence during long recovery
"chạy ổn ko / sắp xong chưa / lần này xong hết đi nhé" → instant reply with
lead-with-status + phase ETA table anchored to a fresh `date` (per-phase
planned wall time incl. worker chain-turn buffers), and state the terminal
state that WILL be reached this run (e.g. SPRINT_SUBMITTED / MANAGER_VERIFIED_
PENDING_CODEX_REVIEW) so the user knows the finish line is a review boundary,
not APPROVED.
