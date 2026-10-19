---
name: motionforge-sprint-manager
description: Use for MotionForge2D full-sprint Manager orchestration.
---

# MotionForge2D Full-Sprint Manager (isolated-worktree mode)

> 2026-09-28 full-delivery takeover: read `references/delivery-takeover-20260928.md` first;
> when resuming Phase B, also read `references/phase-b-wave-execution-status.md` (per-task loop, task→commit table, FE UI-convention block, 160-cap recovery pointer).
> Phase-C demo rounds (R1–R4), delta-pair routing and the real-run seam-class catalog
> (A–G: persistence projection, media-kind bucket, long-path/argc ceilings, key-space,
> declared-pad geometry, evidence-window starvation, audio provenance): see
> `independent-evidence-verification/references/iteration-budget-exhaustion-and-finish-packets.md` §7b/§7k.

Role: **Manager only** — preflight, materialize packets, dispatch/resume worker
sessions, monitor, audit, run gates, record evidence. NEVER write
implementation (source/test/migration/frontend/fixture). Defects route back to
the exact owner session of that Task ID. Terminal verbatim for the current
sprint (e.g. `S11 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`);
never write APPROVED/CLOSED; never open a sprint the binding prompt did not
authorize.

Authority chain to read BEFORE anything: `HERMES_AUTOPILOT_RULES.md` (report
`RULES_LOADED` + line count + SHA), `AGENTS.md`, `SESSION_PROTOCOL.md`,
`CODEX_PM_HANDOFF.md`, `ROADMAP.md`, latest PM review, sprint contract, task
handoff, binding plan + its REPORT/COORDINATION_REPORT. Verify SHA-256 of
rules/plan/contract vs the prompt's expected values; hash mismatch or
unresolved contradiction ⇒ `BLOCKED_RULES`, no dispatch from memory.

## Proven dispatch mechanics (Windows, git-bash, Hermes CLI v0.19)

```bash
# 1) wave base = clean canonical HEAD (verify porcelain=0 + ls-remote equal)
# 2) task branch + clean worktree at EXACT wave base:
git -C s11-integration branch codex/s11/<task-lower>-<token> <WAVE_BASE>
git -C s11-integration worktree add "C:/Users/Admin/MotionForge2D-worktrees/s11-<task-lower>-<token>" "codex/s11/<task-lower>-<token>"
# prove: rev-parse HEAD == WAVE_BASE, porcelain == 0, no other task uses path/branch
# 3) materialize packet at external evidence root with the BINDING PLAN BLOCK
#    copied VERBATIM (all 8 fields) — never summarize acceptance/write-set
# 4) dispatch one NEW worker (background, notify_on_complete; -Q quiet gives session_id):
cd <task-worktree> && hermes chat -q "$(cat '<evidence>/<task>/<token>/prompt.md')" \
  -m <model-from-prompt> --provider custom -Q --yolo --accept-hooks --pass-session-id \
  --max-turns 400 > "<evidence>/<task>/<token>/dispatch.log" 2>&1
# 5) corrections resume the EXACT session: add --resume <session_id> to the same command
#    (--yolo/--accept-hooks keep an unattended worker off approval prompts; --pass-session-id
#    makes the worker's FIRST reply self-report its session id + model — this IS the readiness probe)
```

- Model policy from the prompt usually overrides config: exact
  `ocg/deepseek-v4-flash` @ custom (9Router `127.0.0.1:20128/v1`), reasoning
  max, fallback OFF, TTFB 900. If raw session row shows `reasoning_config=null`
  record `RUNTIME_CONFIG_GAP` (CLI path) — do not claim max is proven. Wrong
  model/provider/fallback ⇒ `BLOCKED_MODEL_ROUTE`.
- One persistent Git-only owner `S11-INT01`: create ONCE (charter prompt), keep
  `session_id`, then resume it for every wave's merge/push. Serial wave:
  `git merge --ff-only <verified-branch>`; parallel wave: ff first then
  `--no-ff --no-edit` siblings. Conflict ⇒ abort + preserve + route to owner.
  Push only after combined wave gate green: `git push origin HEAD:refs/heads/codex/s11-integration`
  (no force) and verify `git ls-remote origin codex/s11-integration` == local.
- Wave gate runs on integrated HEAD from a DISPOSABLE detached verifier
  worktree (`git worktree add --detach`), never in canonical; remove it after
  gate (evidence stays external). Full gates on frozen bytes need zero writers.

## Byte-safe manifest (every task, before dispatch)

1. Pin allowed/protected files: path, tracked/dirty, SHA-256, bytes, lines, mtime.
2. Snapshot critical dirty/untracked files to the task evidence dir; verify hash.
3. Existing files: bounded patch w/ preimage ONLY (apply_patch/unified).
   Whole-file generation ONLY for genuinely new allowlisted paths.
   Ban: write_file on existing files, redirection, Set-Content/Out-File,
   heredoc into files, copy/move/restore/delete/recreate.
4. Post-patch: hash/bytes/lines → compile → narrow test. Shrink/lost-def/
   wrong-path/compile-fail ⇒ `BLOCKED_UNSAFE_WRITE`; freeze evidence, never
   restore-over.
5. Worker may commit only allowlist + its own `docs/pm/sessions/<task>/**`,
   record commit SHA/range, `TASK_SUBMITTED`, exit. No push from task branches.
6. Manifest files consumed by `sha256sum -c` must be MACHINE-GENERATED
   (`sha256sum <files> > manifest.sha256` inside the worktree), never
   hand-written. Hand-built lines (e.g. `**path` prefix from an awk format)
   fail verification with `No such file or directory` on every entry
   (S12-T03B 2026-09-07: 5/5 FAILED before rewrite, 5/5 OK after
   regenerating). Always run `sha256sum -c <manifest>` (exit 0) immediately
   after writing it, before dispatch.
7. Persistence/migration lanes: bootstrap-table-set failures need
   stash-baseline attribution, not instant regression verdict. When a lane's
   new migration breaks `test_persistence_bootstrap`-style table-set tests:
   `git stash` own changes (migration + models edit), re-run the failing
   tests on the pure baseline, then `git stash pop`. Identical failures on
   baseline = pre-existing, lane proceeds to its own tests (S12-T03A
   2026-09-07: 3/3 bootstrap fails reproduced on pure `0d04673`, correctly
   classified pre-existing, code restored, lane continued).

## CRLF hash attribution (verified 2026-09-03)

`core.autocrlf=true` ⇒ disk files are CRLF; `sha256sum disk` ≠ git blob hash.
An apparent "drift" on a protected file was fully explained by EOL: LF-normalize
(`bytes.replace(b'\r\n', b'\n')`) and compare to the pinned/committed blob —
they matched byte-for-byte. Also compare the SAME file across refs (old HEAD,
checkpoint, activation HEAD, archive worktree) to attribute stale handoff pins
(e.g. T01 acceptance pin `28244b02` → committed `8a8b912b9b` identical on all
refs). Do NOT declare `BLOCKED_PREIMAGE_DRIFT` before this attribution.

## Session/approval pitfalls

- Keep `git worktree add`/branch mutations in a PLAIN command. A python heredoc
  appended to the same terminal call trips smart-approval and can time out
  mid-flight (routine protocol-authorized action stalls until user approves).
  Generate manifests in a separate call with no git mutation.
- Baseline manifests: read with Python (`hashlib` on raw bytes) BEFORE any
  worker write; store in evidence root, not %TEMP%.
- `sha256sum` output differences disk-vs-blob are EOL, not corruption — verify
  before alarming (see CRLF section).
- Worker REPORT may record a wrong after-hash (measured mid-edit) while the
  committed blob == LF-normalized disk == tested bytes. Record the delta as an
  evidence note for Codex; it is not a defect.
- **MSYS `git -C /c/...` intermittently fails** ("cannot change to ... No such
  file or directory") even though the path exists — a shell-state quirk, NOT a
  vanished worktree. `ls` the parent to confirm, then `cd` into the parent and
  use RELATIVE paths (`git -C s11-t03f-0903w7 ...`). Do not raise an alarm or
  recreate worktrees from this signal.
- **Python heredocs mangle backslash content.** `python - <<'EOF'` bodies with
  escape sequences (`'\\'`, regex `\d`, Windows paths) get backslashes eaten
  by the shell layer — S12-R6 2026-09-15: `str.replace('\\','/')` arrived as
  `replace('','/')` → `SyntaxError: unterminated string literal`. Any script
  containing backslashes/regex/escapes: write it with the `write_file` tool
  and run `python <file>` (same class as the JS-heredoc pitfall in
  terminal-engineering-discipline, extended to Python).
- **Nested `$(...)` inside quoted args can be hard-BLOCKED by the command
  parser** — S12-R6 2026-09-15: `"$(grep -c 'pat' \"$file\")"` nested in a
  larger shell line returned `BLOCKED (hardline): command parser limit or
  malformed executable payload` (parser refusal, not permissions). Flatten to
  one plain command per line or move logic into a script file; never retry
  variations of the nested form. RECURRED S12-R7 2026-09-16 — two more hard-blocked
  shapes (a `grep -c "pat" "$f"` count nested inside an already double-quoted echo
  line, and a `tail | tr | tail` status pipeline whose args embedded `$(...)`).
  Proven fixes: precompute the value into a plain var in a PRIOR simple call and
  reference `$var`, or drop the wrapper entirely (`grep -c` already prints its own
  number). The block is the PARSER refusing the payload SHAPE — the same command
  re-worded flat passed first try every time; never debug the block as a shell error.
- **B01-style worktrees: `.git` owned by another sandbox user.**
  `git` in the B01 worktree fails `dubious ownership ... CodexSandboxOffline`
  — use per-invocation `git -c safe.directory='*' <cmd>` for every git call
  there (no persisted config change, no ACL work). Write-set guards
  (pathlib-only) are unaffected.
- **Session IDs of killed/paused workers never print.** Recover via
  `hermes sessions list` (filter by title matching the prompt header; cron
  sessions are interleaved). NEVER guess or reuse a session ID from another
  task — one wrong `--resume` (T02B ID on a T03B resume) must be killed
  immediately and the real IDs looked up. Verify ID → task mapping before
  every resume.
- **Stale exit notifications**: after a long sprint, background-process exit
  notifications keep arriving for bash wrappers of processes that finished
  hours ago. Recognize as cleanup noise; do not re-verify or take action —
  confirm terminal state stays unchanged.
- **Wrapper exit 0 ≠ worker done.** A `hermes chat -Q` background wrapper
  exits 0 as soon as the CLI returns, but `dispatch.log` may hold only a
  review-diff with no terminal marker. Before declaring a lane done, check
  terminal markers (`TASK_SUBMITTED` / `NEEDS_T04B_*` / `BLOCKED_*` /
  `EXIT=`), tip movement, and porcelain. Wrapper exited with no terminal ⇒
  nudge the EXACT owner session (resume + short status-demand prompt) — never
  open a replacement worker. Count "no state advance" nudges, not total
  nudges: if each nudge advances worktree state (new bytes, new test nodes, a
  new real failure→fix cycle), the counter resets — S11-C2 A2 needed ~10
  nudges across a progressing lane and still converged. Freeze only after 2
  consecutive nudges with zero tip/porcelain/log advance. A first raw run that
  FAILED with a real error (wrong repository API, unmapped entity) and gets
  fixed next nudge is healthy TDD iteration, not stall — never nudge a
  direction change on it; only nudge for completion (gate + commit +
  terminal).
- **Model-route attribution via `session_model_usage`.** When the user asks
  "why still <model> requests", query
  `select model, billing_provider, api_call_count,
  datetime(last_seen,'unixepoch','localtime') from session_model_usage where
  session_id=<sid> order by last_seen desc` on
  `%LocalAppData%/hermes/state.db`. Rows with old `last_seen` are stale
  history (prior rounds), not current work; rows with `billing_provider=auto`
  + `task=approval` are system approval calls, not worker code. Also check
  `cron/jobs.json` model pins — a paused/old heartbeat cron may be the real
  source. Attribute by timestamp before claiming a route violation.
- **Owner session lookup needs `--limit 200`.** Default `hermes sessions list`
  shows only ~22 recent rows (heartbeat cron sessions interleaved) and hides
  older exact owners (S11-C1: T03A/T03G/INT01 were invisible until
  `--limit 200`). Always search with `hermes sessions list --limit 200` +
  grep for the exact session IDs before declaring an owner missing.
- **`hermes sessions export` needs a Windows-native output path, not MSYS.**
  The CLI is Windows-native Python: an output of `/c/Users/.../x.jsonl`
  dies `FileNotFoundError` even though the dir exists under bash. Pass
  `C:/Users/.../x.jsonl` instead (S12-C1 2026-09-08 — same class as the
  terminal-engineering-discipline MSYS quirk, but for the hermes CLI's own
  file args, not node/python).
- **Windows `$TEMP`/`$TMP` can be hijacked by another session's env snapshot.**
  `echo $TEMP` may point into an unrelated run folder (S12-C1 2026-09-08:
  `.../demo-v3-r2/.../_mgr-verify3-tmp` instead of
  `C:/Users/<user>/AppData/Local/Temp`), so `pytest --basetemp="$TEMP/..."`
  dies `FileNotFoundError` at fixture setup — an env defect, not a code
  failure (18 errors → 19 passed on retry with the real Temp path). Always
  `echo "TEMP=$TEMP"` before trusting it; on mismatch pass an explicit
  basetemp under the real Windows Temp and record that path in evidence.
- **Post-compaction dispatch amnesia: audit yourself before crying intruder.**
  After context compaction the Manager forgets its own prior dispatches and may
  misread legitimate wave owners as foreign sessions (S12 2026-09-07: three
  09:48 W2 owners were first judged "not Manager-dispatched", but the
  Manager's own session messages table held the 09:47–09:48 dispatch tool
  calls plus a REGISTRY W2 section). Before declaring any session
  unauthorized: (1) query your OWN session's messages for dispatch tool calls
  near the session's start time, (2) read REGISTRY.md for a matching
  dispatch/wave section, (3) check the evidence dir (`prompt.md` /
  `dispatch.log` mtimes + session_id lines). Only a session failing all three
  is truly foreign — freeze that one, adopt the rest into the wave table with
  verified state.
- **Self-authored merges forgotten post-compaction are own work, not an
  intruder.** (S12 2026-09-07): two merge commits on `s12-integration`
  looked foreign — but the state-DB query showed zero INT01/writer sessions
  existed, while merge messages + timestamps matched the Manager's own
  prior-turn activity. Rule: unknown merge ⇒ compare
  `git log --format='%h %ci %s'` against your OWN session messages before
  alleging a foreign writer.
- **Push `up-to-date` is not remote proof when `ls-remote` times out.**
  (S12 2026-09-07): `git push` said `Everything up-to-date` while
  `git ls-remote` failed (github.com:443 timeout, exit 128). Record
  local-HEAD-verified / remote-SHA-unverified, retry at the next wave gate,
  disclose the gap in the packet — never claim local==remote without the
  ls-remote line.
- **Merge-tree pre-check for parallel siblings.** Before merging two verified
  task tips onto integration:
  `git merge-tree $(git merge-base A B) A B` — conflict-free output proves no
  textual overlap; then merge serially (`--no-ff`) and run the combined gate
  on the integrated HEAD.
- **Pre-stage (not pre-dispatch) a DAG-blocked dependent node.** When the
  user authorizes "dispatch early if parallelizable" but the contract DAG
  still blocks (e.g. T03B waits for T03A): create the worktree @ integration
  HEAD + CAPTURE guards + write `prompt.md` headed `PRE-STAGED, CHƯA
  DISPATCH` with the exact firing condition. Dispatch fires automatically at
  the gate — no user re-order needed, no DAG violation. Refresh the
  pre-staged guard manifest at fire time: re-CAPTURE on the W-complete
  checkpoint because the blocker's own files (new persistence module +
  migration) join the consume set — a stale pre-stage manifest undercounts
  (S12-T03B 2026-09-07: 5 files pre-staged → 7/7 re-captured after T03A
  landed, then dispatched).
- **Ancestor check by TIP SHA, not branch name.** Task branches are not
  fetched into the canonical worktree, so
  `merge-base --is-ancestor <branch-name>` fails with "Not a valid object
  name". Check each task TIP SHA instead:
  `git -C <canonical> merge-base --is-ancestor <TIP_SHA> HEAD` — yes means
  the owner branch is FF-able onto canonical.
- **Guard-CLI arg shape.** `write_set_guard.py capture` REQUIRES
  `--root <worktree> --manifest <path>` (bare `--path` alone exits 2).
  One manifest per lane; DB owner proof needs no sqlite3 binary — use
  python stdlib `sqlite3` with `mode=ro&immutable=1` URI.
- **Prompt-file overwrite trap.** A `write_file` used to \"append\" a second
  half of a lane prompt REPLACES the whole file — if the second content
  omits the first half (findings), the dispatched prompt loses its closure
  rows. Compose the FULL prompt in one write (or re-read after each write
  and verify both sections present) before dispatching.
- **Evidence-root first-write creates parents — via `write_file` ONLY, never via shell `>`.** The first artifact write with the `write_file` tool under a fresh `s11-c3/` tree auto-creates `manager/`, `lanes/` etc. — don't burn a turn on manual `mkdir -p`; write `LATEST_RUNID.txt` first. BUT shell redirection (`>`, `>>`, `tee`) does NOT create parents: a background verify run redirecting into a not-yet-existing `manager/` subdir dies instantly with `No such file or directory` (observed S11-C4-R1 2026-09-05: verify wrapper exit 1, zero test output). Guard: every terminal command that redirects into the evidence root starts with `mkdir -p <evidence-subdir> &&` (cheap, idempotent) before `cd <worktree>`; only skip it when a prior call in the same wave already created that exact subdir.
- **Verify owner identity via state-DB first message before dispatch.** Session IDs differing
  `...4a4548` = real T05A owner vs `...5b3841` = T04D owner). A prompt.md label
  or prior Manager note is NOT proof — query the Hermes state DB read-only for
  the session's first message / durable task assignment and confirm it names
  the Task ID being dispatched. Dispatching the wrong session yields a commit
  on the right branch by the wrong owner: a P1 ownership violation no gate
  count waives. Never rewrite history to hide it — freeze the wrong session
  from that task, and the real owner re-derives the bytes, recording explicitly
  which bytes are retained vs replaced plus the incident in LOG/REPORT.
- **Any piped git verdict loses its exit code — never trust `$?` after a pipe.**
  `git diff --check … | tee file; echo $?` reports tee's exit (0) even when
  diff-check finds whitespace defects; likewise
  `git fetch … --dry-run 2>&1 | head; echo FETCH_EXIT=$?` reported 0 while
  fetch itself died `fatal: bad object … / did not send all necessary objects`
  (S12-C1 W3 2026-09-08 — `$?` was head's exit, masking a real fetch failure;
  only the separate `ls-remote` line carried the true remote verdict). Use
  `${PIPESTATUS[0]}` (bash) or run the git verdict unpiped whenever its exit
  code is the decision input.
- **Dispatch CWD guard: `cd` into the task worktree, never canonical, before
  `hermes chat --resume`.** The resume prompt names the right session but the
  shell's `cd` picks the worktree — dispatching a task prompt from the
  integration/canonical worktree lets the worker merge foreign commits into
  the task branch (observed: integration merge commits fast-forwarded onto a
  task branch, moving its tip away from the pinned SHA while the task tip
  itself was untouched). Guard: every dispatch command starts with
  `cd <exact-task-worktree> && git log --oneline -1` (tip must equal the
  pinned tip), and the prompt itself restates worktree + branch + tip plus an
  explicit merge/fetch ban. Recovery on a local-only task branch (never
  pushed): `git reflog show <task-branch>` to find the pre-merge tip,
  `git reset --hard <pinned-tip>`, then verify `log --oneline -1` +
  porcelain 0 before re-dispatching with the guard restated.
- **Log growth without tip movement is still stall.** A worker can burn
  several nudges writing analysis (diff reads, root-cause notes) while branch
  tip and porcelain never move. Count "no state advance" on tip + porcelain,
  not on log bytes: after one analysis-only turn, the next nudge must ban
  further analysis and order patch-now + gate + commit in that same turn.
  The FIRST stall-suspect nudge must demand concrete bytes + continued writes
  in the same turn — never a status-only report. A "bao trang thai" nudge lets
  the worker answer with delivery-only text (analysis summary, zero tip /
  porcelain movement) and burns a full cycle: S12-T06B 2026-09-07 sat at
  pristine WT 0 bytes from 22:48 to 23:13 while reading production context;
  the 23:11 status-only nudge returned text with still-zero bytes. Order
  "report bytes-written-so-far AND keep writing the next file in this same
  turn" from the start.
- **Worker subagent-delegation silence is stall, not progress.** When a worker
  says it is "dispatching the build via claude/codex" (orchestration policy)
  then goes session-quiet + tip-frozen + porcelain-empty past the 8-min audit
  threshold, that is NO state advance — the subagent may be stuck and the
  worker has no bytes to show for it. Nudge the EXACT owner demanding ground
  truth in the same turn: what the subagent actually returned (files written,
  tests run with counts) — and if one more turn still yields delivery-only
  text with zero tip/porcelain movement, order hand-writing the files +
  running the gates directly, no further subagent wait (S12-T03B 2026-09-07:
  17' silence after "dispatching via claude", nudged 13:12 demanding
  file/test-level truth, lane then converged to 19/19).
- **Manager verify must reproduce the worker's claimed count exactly.**
  A verify pass with FEWER tests than claimed (S11-C3 2026-09-05: worker
  claimed T05A 14/14, Manager verify ran only the readiness file → 9 passed)
  is a RED flag, not a pass — it means the verify ran a SUBSET of the gate.
  Procedure: enumerate the task's test files (`ls <worktree>/tests | grep
  <task>`) and run ALL of them; compare collect-only count to the claimed
  count first. Never merge on a subset pass.
- **Expect-vs-production attribution on the last failing row.** When one row
  still fails after a sync fix, read the production contract branch BEFORE
  patching: if production matches the binding contract (e.g. completed +
  coverage-FAIL → `failed`; `stale` only when coverage OK but evidence/policy
  rotated), the stale EXPECT is wrong — preimage-patch the expect, never
  "fix" correct production to satisfy an old expect. Record which side was
  wrong + why in the lane evidence.
- **Cross-tree production import is out of scope — revert, don't merge it.**
  S11-C3 2026-09-05: a task worker "synced semantics" by copying a sibling
  lane's strengthened production file into its own tree (+228/-23 on
  `app/persistence/qc_check_runs.py`, outside its test-only allowlist).
  Procedure: `git diff --stat` on every worker tip BEFORE verify; any
  production file outside the lane allowlist ⇒ `git checkout -- <prod-file>`
  immediately, keep only the allowlisted test/seed change, re-verify. The
  strengthened semantics arrive via the INT01 merge on the integration tree —
  task trees must never import them by copy.
- **Forged-fingerprint stale seeds die under a fail-closed envelope.**
  S11-C3 2026-09-05: seed V_S used manifest `evidence_fingerprint="z"*64`
  (forged). Under C2-A1 it reached the stale branch (`stale`); under C3A1
  items 7–8 (manifest fp must equal recomputed-current-with-manifest-gen)
  coverage FAILS first → `failed`, never `stale`. Fix the SEED (real fp at an
  old generation + new generation before read → coverage OK + caller
  mismatch → STALE), never weaken correct production. Expect then stays
  `stale` on both semantics; record the mechanism
  (coverage-vs-recomputed-manifest-gen vs stale-split-vs-caller-evidence) in
  the lane log so the next nudge doesn't re-litigate it.
- **Green suites can hide an empty production registry — probe clean-process
  bootstrap before trusting counts.** S11-C4 2026-09-05: 143 tests green
  because every fixture imported/registered detectors first; two
  clean-subprocess probes (bare `from app.main import app` → `[]`; real
  `JobService` on fresh Alembic-head DB → `[]`, full band →
  `QC_ORCHESTRATOR_MISSING_ARGS`) proved production unusable. Recovery is a
  server-owned composition path (`ensure_full_band_registered`: exact ten
  names, real entry points/revisions, idempotent, conflicting registration
  fails closed), never a test-only bootstrap. Full pattern in
  `references/s11c4-production-registry-fail-closed.md`.
- **Mocks hide constructor/signature defects — demand an unmocked-path repro
  before closing.** (S12-C1 W4 2026-09-08): the publication suite mocked
  `_load_chunks`, so the missing required `ChunkSpec.content_hash` raised
  `TypeError` only on the real path; the readiness chain
  (`evidence_fingerprint` → `policy_bundle` → `compute_project_readiness` →
  `_check_run_readiness.status`) had matching signatures on paper but had
  never run unmocked against a real DB. Rule: every publication/wiring lane
  needs at least one test driving the REAL loader + REAL readiness chain on
  an isolated DB — a green suite with those seams mocked is not closure
  evidence. The first correction nudge orders the unmocked repro (exact
  failing test name + last 20 traceback lines + root cause) before any fix.
- **Guessed authority fallbacks are P1 fail-open — delete, don't default.**
  S11-C4 2026-09-05: try/except around the revision resolver → `{}` +
  `"1.0.0"` default accepted a forged ten-detector completion as `completed`
  with 2/10 registered. Every authority-unavailable path (exception,
  unregistered member, incomplete/extra map, empty revision, conflict) must
  return `failed` + `not_run` + truthful detail. Prove with the minimum
  revision matrix (2-of-10, one-missing, resolver-raise, rotated-server,
  wrong/empty/extra/missing, all-ten-green, tamper rows, both controls).
- **Consumer lanes must probe the merged API contract live; Manager verifies
  route promises by grep, never by worker REPORT.** (S12-C2 W5 T05 2026-09-09):
  after INT01 merged backend wave W4, the frontend lane discovered T03C's
  `8753f2a` had NOT delivered the result/download endpoints its own prompt §4
  required — probes of `/s12-exports/{run}/result|download|media|output` all
  404 and REPORT_C2 rows C01–C18 omitted C22. Procedure: (1) after any backend
  wave merge, diff the prompt's promised endpoint list against
  `grep -n "@router" app/api/routes/<file>.py` in canonical — a missing route
  is a real gap even when tests are green; (2) route the gap back to the exact
  owner as a BOUNDED ADDENDUM resuming the SAME session on the merged tip
  (exact delta list: two GET endpoints, completed+ownership guard, fail-closed
  on stale/partial/missing, tests, REPORT row update) — never let the consumer
  lane fake the endpoint or SQL-seed around it; (3) let the consumer continue
  its non-dependent work in parallel (disjoint frontend vs backend write-sets)
  so the wave does not stall; (4) only after the addendum lands + merges does
  the consumer prove the positive case through the REAL endpoint. A worker
  TASK_SUBMITTED whose REPORT row list drops a row the prompt assigned it is an
  incomplete promise: compare REPORT rows against the prompt's §5 rows before
  merging (S12-C2 addendum `t03c-addendum-*`: `GET /s12-exports/{run_id}/result`
  metadata + server-owned media URL, `GET /s12-exports/{run_id}/media`
  stream/download, both completed-only, ownership-checked).
- **Source-locked exact-digest validation can never pass a re-encode
  pipeline — add a fail-closed measured mode, never weaken assertions.**
  A validator demanding byte-identical frame digests rejects EVERY legitimate
  job on an upscale/re-encode product path (4K from 320×180 is never
  byte-identical to the approved artifact), so the positive publish row stays
  blocked after the producer already supplies reference evidence. Route the
  delta to the VALIDATOR owner: `frame_match_mode = "exact"` (default) |
  `"psnr"` + `frame_psnr_min_db` (consumer-set per profile, missing threshold
  → FAIL closed), per-frame PSNR probe at the approved raster, and PROVE all
  tamper cases (reorder/audio/drift/wrong-ref/combined) still FAIL under the
  tolerance — only legitimate lossy re-encode of the same content passes.
  Then the producer wires the mode per profile (psnr for re-encode, exact for
  identity-copy) and optional `expected_sha256`. Tolerance is documented and
  opt-in; default stays fail-closed. (S12-C2 W7 2026-09-09: verifier F11-T06B-01
  → T03C findfix `47dae37` builds SourceReference/AudioReference/CutPoint from
  the approved artifact → T04A delta `c5654ad` adds psnr mode → T03C wire-psnr
  `04a5036` → T06B re-verify-2 closes native same-raster but finds the NEXT
  link: `probe_frame_psnr` decoded the reference at its ORIGINAL raster, so
  cross-raster candidates (1080p→4K upscale, 4:3 letterbox) fail — validator
  owner fixes by FIT+PAD of the reference to the candidate raster per the
  product letterbox policy (never stretch), `SourceReference.reference_width/
  height` server-owned, tamper re-proven still-FAIL (T04A `bd5837e`, 78
  passed); full pattern in
  `references/s12c2-finding-loop-reencode-validation.md`.)
- **Windows ffmpeg rawvideo stdout pipe drops frames under heavy filter
  graphs — decode BOTH sides to temp raw files, not just the reference.**
  (S12-C2 2026-09-09/10): cross-raster PSNR still read 7/30 frames at
  ~7.6 dB after the reference was moved to a temp raw file — the CANDIDATE
  still streamed through `_open_raw_pipe`, and a large scale filter graph on
  Windows drops rawvideo pipe frames (native same-raster 30/30 via pipe is
  fine, cross-raster scale is not). Fix shape (`probe_frame_psnr`, T04A
  `83e7714`, 81 passed): on the CROSS-RASTER path decode BOTH candidate and
  reference to mkstemp raw files in %TEMP% (validate `size % frame_size == 0`
  → fail-closed None, delete in finally) and read frame-by-frame from disk;
  the same-raster path keeps the proven 30/30 pipe. Ground truth is ALWAYS
  the verifier's re-run on the merged canonical — validator-branch green
  proved nothing about the product path until T06B re-verified (`70cb392`
  still 7/30, root cause named exactly, routed back). Pattern: pipe-loss
  under scale ≠ content mismatch; assert the FULL frame count in the test
  (`"30 frames PSNR"`) so a truncated pipe fails as frame_count mismatch,
  never passes as low-PSNR noise.
- **Verifier-discovered positive blockers route as a chain, not a one-shot
  fix.** First fix (producer supplies reference) exposes the NEXT link
  (validator mode), then the next (producer wiring). Each round: verify the
  claim on the merged canonical, route to the exact owner, bounded commit,
  INT01 merge, re-verify — and keep the verifier's row `failed` honestly until
  the FULL positive chain closes; a render-green + publish-failed split is a
  REAL open row.
- **Full-tree pytest dies on duplicate test basenames after a multi-lane
  merge — run the gate PER PACKAGE DIR.** Every C1 lane adds
  `tests/s12/s12-t0X/test_c1_closure.py`; dirs missing `__init__.py`
  (t01/t02/t04a) collide on prepend import-mode → `import file mismatch:
  imported module 'test_c1_closure' has this __file__ attribute
  …/t01/…` at COLLECTION, before any test runs. Not a code defect, not a
  merge conflict, not a correction. `--import-mode=importlib` does NOT fix
  it (breaks lanes using `from conftest import X`). Fix: loop per dir with a
  SHORT per-dir basetemp (`--basetemp=C:/Users/.../Temp/s12_$d`) and sum
  counts (S12-C1 INT01 2026-09-09: T01 31, T02 36, T03A 44, T03B 32,
  T03C 19, T04A 48, T06B 11+1skip all green individually).
- **A test that documented a pre-fix bug fails on the merged canonical —
  route the TEST update to its owner, never re-open production.** When a
  verifier lane pinned a known-bug behavior as a documented expectation
  (T06B `test_f3` asserted dims-only `native_4k` = F-OBS-01) and ANOTHER
  lane's correction closed that bug in production (T01-C1 `0d5bc77` → bare
  dims now `upscale_4k`), the merged INT01 gate fails with `AssertionError`
  while the lane's OWN branch passes (pre-fix prod). Correct action: resume
  the exact TEST owner, order the assertion updated to the new behavior +
  note `closed by <owner-Cx commit>`, merge that test-only commit, re-run
  the per-dir gate on canonical → green. The verifier's local run FAILING
  by design (its tree still has pre-fix prod) is expected — do not hold the
  merge for the lane branch to go green. (S12-C1 INT01 2026-09-09:
  test-only fix `97a54b0` merged `60d5864`.)
- **Determinate model quota 429 with reset timestamp is a BLOCKER, not a
  retry-loop.** `HTTP 503: […][429]: weekly usage limit … resets at <ts>` is
  auth/quota, not transient — Rules §7 5-min retry does NOT apply; never
  retry the dead route in a loop. Log the raw error + reset time in
  `BLOCKER_LOG.md` at the evidence root, switch the SAME exact owner resume
  to the LAST route the user explicitly authorized this session
  (`ocgfree/muse-spark-1.3-contributor-free` @ custom was user-chosen
  2026-09-08 ~19:4x), record the switch, and report the blocker to the user
  lead-with-status in the same turn (S12-C1 INT01 2026-09-09).
- **Fetch blocked by stray refs ≠ diverged branch — ancestor-check local
  objects first.** S11-C4 2026-09-05: `git fetch` died on
  `refs/codex/turn-diffs/*` ("did not send all necessary objects") while the
  task tip was already an ancestor of canonical; `git merge --ff-only
  <canonical-SHA>` on local objects succeeded with no rebase/reset/force.
  Procedure: `merge-base --is-ancestor <tip> <canonical>` before any alarm;
  true only when ancestor → FF locally. A fetch error alone never justifies
  reset/rebase/recreate.
- **Machine-wide gates run serial; parallel=false-positive is proven by the
  serial rerun.** S11-C4 2026-09-05: T01 leak-scan (`test_12_no_process_leak`,
  machine-wide ffmpeg PIDs) went 63/64 parallel with the inner suite, 64/64
  serial (269s). Never re-litigate the parallel fail after the serial green
  — record both runs in the verdict and move on. Same for any port/lock/
  global-runtime gate sharing the box.
- **Guard `FAILED` needs attribution: growth on allowlisted files is
  expected, shrink is red.** S11-C4 2026-09-05: 5/5 drift with bytes/lines
  GROWING on the exact C4 write-set = intentional change, not destructive
  shrink. Check direction (growth vs shrink), lost definitions, and
  protected-file drift before judging the ladder; record the attribution in
  the verdict so the reviewer doesn't misread it as a gate red.

## Codex→Hermes transfer + post-merge guard reconciliation (S12-R6, 2026-09-15)

- **Two-phase dispatch: readiness turn BEFORE any write turn.** Every newly
  transferred owner gets one NON-WRITING readiness turn first (with
  `--pass-session-id`; run `pwd`, `git rev-parse HEAD`, `branch`, `status`,
  `log -3`, one allowlist dir listing, runtime python `--version`), then the
  work order as turn 2 on the SAME session. Readiness must return RAW output
  per command + its session id; it doubles as route proof (5/5 owners OK).
  Record each session id in the registry the moment it lands.
- **Batch upstream-502 incident (multi-worker same-upstream death).** One
  upstream `HTTP 503: [...][502]: fetch connect timeout` killed 3/4 workers
  mid-turn simultaneously while the 4th survived. Procedure: (1) confirm each
  dead turn's worktree is CLEAN (design-phase deaths leave no partial writes —
  check `git status` per lane before anything else); (2) tiny route liveness
  probe (`hermes chat -q "Reply with exactly: PROBE_OK"`) and RECORD latency
  (57s vs 9.5s baseline = degraded-but-up); (3) wait ≥5 min per failure, then
  resume SAME session/route with a continuation prompt (verify own state →
  continue from stop point → do not redo completed work → don't ask); (4)
  cycle `wait 5' → probe → resume` unlimited on the transient class only.
  Write an INCIDENT md + registry `RUNNING_RETRY_WAIT` in the same turn.
- **Guard baselines go stale after a sanctioned ff-merge — reconcile, never
  alarm.** Manifests captured BEFORE the wave-base sync will flag every file
  the merge itself updated as `protected_file_changed` (and
  `guarded_file_missing` for tests relocated by design, e.g. T03C→retry).
  Procedure: (1) prove merge-induced by byte-comparing each flagged path
  against the wave-base worktree at the frozen SHA (INT tree) — identical
  bytes = merge effect; (2) re-baseline (capture post-merge manifests) for
  the correction phase; (3) keep both manifests + proof JSON in lane
  evidence. Manager allow-set verify with `--allow-change` per lane path
  stays valid across the merge.
- **A byte diff ≠ violation: reconcile at git-blob + LF-normalized level.**
  64-byte on-disk delta on `models.py` with both trees porcelain-clean was
  pure EOL: `git rev-parse HEAD:<path>` blob identical on both sides AND
  `tr -d '\r' | sha256sum` identical. Check blob equality + CR-count delta
  (3528 vs 3592 = 64) before escalating any byte mismatch; report as EOL
  artifact with both hashes, never as scope violation.
- **Snapshot copies of symlinked test trees need `symlinks=True`.**
  VAL `work/` holds `*current` → numbered-dir symlinks; default
  `shutil.copytree` materializes them (58 src vs 116 dst false mismatch).
  Re-copy with `symlinks=True`, verify file-list + symlink-list + per-file
  hashes, then write the verify JSON.
- **Manager verify of a submission = git scope + independent re-run + guards.**
  `git show --stat` (every path inside allowlist), parent == wave base,
  porcelain empty, `diff --check` exit 0, ruff `--select F` on changed py,
  FULL affected pytest re-run reproducing the worker's claimed count EXACTLY,
  guard verify both manifests. Worker-printed numbers are claims until the
  Manager re-run prints the same ones.
- **INT completion verify: union-delta exactness + whitelisted protected
  guard.** After the 4 lane merges: per-merge second parent == source SHA;
  `git diff --name-only base tip` == EXACTLY the union of lane path lists
  (25 = 6+5+8+6 disjoint — any extra path = stop); protected post-transport
  guard verified with `--allow-change` for exactly the transport-intended
  paths and zero-change elsewhere (keep the unfiltered raw JSON for audit);
  `geometric-repack bad object refs/codex/turn-diffs/...` stderr on merges is
  pre-existing tooling noise (exit 0, never repair). INT's turn may END with
  exit 0 after the merges while static+docs are still pending — wrapper exit
  0 ≠ lane complete; resume the SAME INT session with the explicit
  finish-list (static gates → docs commit → report).
- **Frozen-ID divergence (inventory draft vs owner-frozen node IDs) =
  correct the freeze DOC, never rename verified tests.** A pre-implementation
  inventory may predict node names the owners then implement differently;
  harness checks of the form `if target.is_file(): assert node in nodes` are
  VACUOUS on owner-less worktrees and fire only on the merged candidate
  (101/102 finite acceptance this round). Quantify first (parse inventory +
  AST-collect module nodes + fuzzy match: 42 cases → 0 exact/25 fuzzy/17
  unmapped; every case existed under an owner name, some 1:2), then rule:
  owner-frozen IDs are canonical (MATRIX: "frozen by owners") — route the
  mapping correction to the OWNER OF THE FREEZE DOC (update doc node column +
  harness expectation to actual IDs + provenance note; keep check strength,
  no skip-ification). Never rename dozens of Manager-verified test functions
  across owners for a naming mismatch. Queue the correction AFTER the owner's
  running turn completes (same session, no second writer).
- **Immutable reviewer probes re-run from a frozen COPY, not a worktree.**
  `git archive <frozen-sha> | tar -x -C <runtime>/frozen-src`; copy the probe
  files into the SAME test dirs as their imports; fresh EXCLUSIVE-create
  `S12_REVIEW_OUT` (probes use `open('x')`); run with `PYTHONPATH=<frozen-src>`.
  This round: 7/7 pass (was 1/4 + 6 failures in R5) — Jobs 2→3 duplicate →
  typed 409 zero-mutation; foreign adoption → "completed output exists —
  refusing overwrite"; stale-A-published → `fence lost before rename` + B
  completes. Hash the new probe JSONs next to the untouched R5 originals and
  quote the old→new deltas in the packet.
- **Endgame order + the by-design red nuance:** product chain (B01-I on the
  owner's own worktree ff-merged to the frozen tip) → queued correction →
  INT round 2 → Manager finite acceptance → ONE broad gate under mutex →
  packet. When the chain returns an HONEST BLOCKED, "all-green" is impossible
  by design: the chain node deliberately re-raises the recorded BLOCKED, and
  that documented red IS the packet's headline finding — it does not gate the
  broad gate the way an unexplained micro does, but it is never hidden or
  fixed by weakening.
- **A public-chain blocker at a module boundary = contract collision; route
  it, never pick the contract yourself.** S12-R6 B01-I: the real chain PASSed
  producer→S09 (`full_apply_executable=true`) then S10 rejected the manifest
  422 `shots overlap or non-monotonic` — S10 derives shots 1:1 from authority
  segments (`s10_full_apply.py:191-262`) while the B01 manifest contract says
  segments are co-occurring OCCURRENCE rows with z-order (and carries its own
  `shot_order`); the chunk planner demands disjoint contiguous shots
  (`s10_chunk_plan.py:166`). Procedure: (1) confirm the owner kept it honest
  (re-raise node, exact request/response/IDs, DB-delta counts at failure,
  zero mutation, no harness-weakening, no out-of-scope fix); (2) Manager
  names the exact root cause file:line on the frozen candidate; (3) route to
  the reviewer with ≥2 proposals (structural fix vs typed denial) + evidence
  paths — a contract choice between two accepted modules is Codex's call,
  not a unilateral Manager dispatch.
- **Verify a bundled submission with a by-design red node by running only
  the FAST files.** S12-R6 QA `c5954d2` bundled the node-mapping correction +
  B01-I artifacts: Manager verify = inventory+prep files (11 passed) + ruff +
  guard, NOT a re-run of the chain node (6 owner chain executions already;
  a re-run only reproduces the recorded BLOCKED, ~30 min burned). Document
  the skip + reason in the verdict.

Full transcript detail:
`references/s12r6-codex-to-hermes-transfer-and-guard-reconciliation.md`, and
`references/s12r6-final-gates-and-frozen-id-reconciliation.md` for the
completion round (INT union-delta verify, finite acceptance 101/102,
frozen-ID divergence reconciliation, frozen-copy probe re-run 7/7, endgame
ordering, B01-I S10 contract-collision blocker + honest-BLOCKED routing,
by-design-red verification).

## Two-manager split + Manager-B activation (S12-R7, 2026-09-16)

- **Coordination transfer, NOT writer replacement.** The existing Manager chat is resumed as Manager B
  (new coordination Task ID); a NEW Manager chat becomes Manager A for the other finding family. B's
  registry records verbatim: RETRY/VAL (exact sids) dispatch under A from this wave — B never
  resumes/dispatches them nor touches their worktrees; B keeps B01 + new BRIDGE + QA + sole INT. Record
  A's actual session id when the user opens that chat (PENDING until then). Both prompts are activated
  independently by the user; a user message delivering a prompt IS the activation — execute, don't re-ask.
- **RULES_LOADED extended format (user-demanded):** path + line count + bytes + sha256 + ACTUAL HEADs
  (main + every relevant worktree/branch with dirty counts) + section list; then verify the user-pasted
  prompt matches the prompt FILE (line count + spot check). Never report from memory.
- **Per-activation setup order (proven):** fresh evidence `outputs/<family>/<uniqueUTC>/B/<lane>/` +
  runtime `work/<family>/<shortUTC>/B/<lane>/` (persist in `00_run_context.txt` AND a scratchpad note
  vs compaction) → registry with split + per-lane table → one-pass guard capture per lane (allow +
  protected + byte snapshots; B lanes protect A's files as protected) → `--ff-only` sync ONLY B's lanes
  to the wave base (BEFORE guard capture) → NEW task worktree only after `git branch --list` absence
  check + `git worktree add -b <branch> <path> <wave-base>` (existing assignment ⇒ resume owner, never
  recreate) → per-lane prompts (finding file:line, acceptance rows verbatim, patch-only, gates, ledger)
  → ONE batch dispatch + heartbeat arm.
- **Cross-manager link = one immutable handoff file** (A: `EXPORT_HANDOFF.json` with base/commits/
  ranges/guards/results) consumed by user bridge or one-shot local read; no watcher/auto messages; only
  INT changes the canonical branch; A never merges.
- **New cross-sprint task = contract-first phase:** the BRIDGE owner writes CONTRACT.md only (scene
  shots = disjoint timeline partition, occurrences = layers, explicit frame conventions/bounds/layer
  identity/geometry/fail-closed codes) and freezes it with Manager+QA BEFORE any production write;
  production may overlap other lanes only after shared interfaces are stable.
- **Contract freeze = Manager rulings across EVERY open question + ONE bounded QA co-signoff turn,
  BEFORE production dispatch.** Cross-check every draft recommendation against the binding acceptance
  rows — they can contradict: S12-R7 draft Q1 said "select boxes[0] + provenance, deny only cross-key
  conflicts" but ACCEPTANCE B04 demands "points-only/missing/**ambiguous** boxes honestly ineligible
  with typed reasons" → ruling: within-key >1 differing box ⇒ typed `OCCURRENCE_GEOMETRY_AMBIGUOUS`
  deny; cross-key keeps the documented precedence. Write rulings to
  `B/manager/<TASK>_CONTRACT_FREEZE_REVIEW.md` (ACCEPT/REVISE per Q + rationale + cited acceptance row).
  The QA co-signoff = one bounded dispatch with named deliverables: per-Q CONFIRMED/REVISE with evidence,
  the exact evidence-format definition the production owner must implement (Q9: per-layer decoded-region
  proof fields next to the existing sidecar pattern), and the B03–B06 node mapping (nodes not yet
  existing stay "to be frozen by owner", never invented). Production waits for the sign-off; the
  Production waits for the sign-off; the contract commit itself (docs-only, guards verified) is not a production green light. The sign-off can OVERTURN a ruling premise — audit every enforcement premise against REAL persisted values: S12-R7 Q4's "real chains use normalized boxes" premise died on actual run rows (pixel-scale `{x:400,y:100,w:250,h:250}` on a 640×360 source; the draft `[0,1]` bounds-deny would have rejected the ENTIRE sanctioned chain incl. P01). Amendment shape: deterministic dual-mode derivation at the consumer (Mode A: all four values inside `[0,1]` + `x+w<=1`/`y+h<=1` → as-is / Mode B: pixel-scale → divide by positive source dims; dims unavailable ⇒ NEW typed code `OCCURRENCE_REGION_SCALE_UNRESOLVED`; neither mode ⇒ existing out-of-bounds; **v0.2.1 post-production hardening (accepted)**: strict Mode-B containment rejected the sanctioned chain's OWN padded boxes ({400,100,250,250} on 640×360 → x+w=650>640) — final accepted rule = box INTERSECTS frame (`x<src_w`,`y<src_h`) + region CLIPPED to the physical frame (`x2=min(x+w,sw)`, `y2=min(y+h,sh)`), fully-outside ⇒ out-of-bounds, dims unavailable ⇒ the typed scale code. Validate a freeze ruling's containment bounds against ALL real persisted values INCLUDING padded/overrun boxes BEFORE freezing), frozen block records `raw_box` + `scale_mode` + `geometry_source`, one fixture per mode + a dims-unavailable negative. Write amendments to `B/manager/<TASK>_RULING_<topic>_v0.2.md` and flag them to Codex in the packet (interface decision beyond the original Q-list). Freeze outputs feed the production prompt VERBATIM: contract + freeze-review rulings + amendment + QA sign-off cited by path, the QA-frozen evidence-format reference, the exact node-ID list copied name-for-name, and the dependency branch that stays blocked until the parallel lane lands. Parallel-consumer interface discipline: fix ENFORCEMENT, keep the consumed wire format frozen — B01's F03 proof module deliberately kept manifest `time_base` as `{fps_den}/{fps_num}` so BRIDGE could code against the existing parse path on day one (record "enforcement-only fix" explicitly).
  - **Production Manager-verify = gate-set parity + flagged-module confirmation + hardening code-review.** For a
  cross-module production submission (4 service files + new module + suite + docs, e.g. BRIDGE `c49a578`): `git
  show --stat` on EVERY commit (all paths in allowlist), guard allow/protected verify, independent re-run of EXACTLY
  the gate sets the worker ran (micro 27 / api 71 / regression 66 — counts must match the worker's claims) PLUS the
  out-of-gate module the worker flagged (G4: 3 failed/18 passed confirmed the flagged set), and read the sensitive
  hardening code yourself (`derive_region` clip) before accepting the change. Treat the worker REPORT's "flags"
  section as a checklist — every flag gets a verdict, none gets skipped.
  - **Contract-mandated test supersessions: file a FINDING + bounded proposal, never silent-edit.** Tests that were
  green while a reviewed bug existed (e.g. points-only `executable is True`/`reasons == []`) go RED BY DESIGN when
  the frozen fix lands — not regressions, not pre-existing. File `B/manager/FINDING_<id>_<topic>.md`: exact
  file/asserts, why superseded (cite the acceptance row), pre-existing-vs-mandated split (alembic-head constant was
  the pre-existing sibling), minimal proposal + proposed owner (test-only exception precedent), and label the reds
  in the final broad gate. Codex decides the write-set grant — the Manager never silently extends scope.
  - **Node-ID list discipline: copy name-for-name AND verify the count by arithmetic before writing it into a
  prompt.** A propagated miscount ("23" vs the real 8+6+6+7=27) reached a dispatch prompt; the owner delivered all
  27 verbatim and flagged the discrepancy in its REPORT. Count named lists yourself when transcribing; a worker
  flagging a prompt arithmetic error is healthy — accept it, correct the records, don't argue the number.
  - **Flapping-upstream 502:
  console.** Local `/models` HTTP 200 (0.1s) while a completion probe TIMES OUT (240s) = local gateway
  fine, upstream flapping (~15–20 min cycles observed; resumes can die again ~11 min in). Do NOT resume
  on a failed/timed-out probe — run another wait(≥5')→probe cycle; dispatch only on a real probe success.
  Track waves by appending to the same `<lane>-console.txt` with `RESUME_N_EXIT=$?` markers (death times =
  console mtimes; one INCIDENT md section per wave; embed a literal `sleep 30` at the head of each resume
  command so the rules' ≥5-min mark is guaranteed even when dispatching right at the boundary). In the process table (and heartbeat), attribute each
  `chat -q` proc to its lane by the `-r <session-id>` cmdline fingerprint — the OTHER manager's lanes
  appear there too: observe and record their liveness, never touch their PIDs/worktrees.
- **SHA-copy discipline: a malformed quoted SHA is resolved from the branch, never a deviation.** A 41-hex
  literal (typo duplicated char) propagated from a handoff file into the dispatch prompt; INT resolved it to
  the real commit via branch tip + parent == wave base + diffstat match (+ cross-check against the
  NO_ACTIVE_WRITER evidence) and recorded both forms in its report. Manager rule: before writing any SHA into
  a prompt, resolve it from the live branch (`git rev-parse <branch>` / `git log -1`) and assert length 40 —
  never transcribe from a memory note; a transporter receiving a malformed SHA must resolve from the tip and
  document the two forms rather than aborting.
- **Freeze-coverage gap found in QA review = bounded test-only follow-up to the PRODUCTION owner, documented
  as "additions beyond" the frozen list.** QA's independent review of a frozen-contract implementation can
  under-cover a ruling (3 missing negative/positive nodes for an accepted hardening + an unused fixture):
  dispatch the production owner ONE bounded follow-up turn adding exactly those nodes in its own suite (+
  wiring the unused fixture), production untouched, full suite re-run (27→31), and the new nodes documented as
  "additions beyond <frozen-list>" in LOG/REPORT while the original frozen node list stays DELIVERED VERBATIM.
  Manager verify = standard scope + full-suite re-run + protected guard; closing a named coverage gap is not a
  contract change.
- **Post-transport lane sync before a lane continues: ff-only to the new integration tip.** After INT round N
  lands, any lane still holding work does `git merge --ff-only <new-tip>` in its OWN worktree before its next
  dispatch (sanctioned conflict-free local sync exception); the exit-0 ff may print the pre-existing
  `geometric-repack` bad-object warning — known tooling noise, never repair. The continuing lane's prompt
  states the NEW wave-base (verify `rev-parse HEAD` first) + refreshed env values (e.g. R5 candidate root +
  expected SHA = new tip).
- **Product chain and Manager gates run in PARALLEL after transport** (chain uses the lane's own runtime/DB,
  gates use Manager basetemps): dispatch the QA public-chain turn (long, `--max-turns 600`) and the Manager
  finite suite in the same batch; the broad gate stays serial-after-finite. The chain prompt names the exact
  previously-blocked seam to now verify (e.g. S10 must pass the former 422 shots-overlap step) so the lane
  knows what a real pass proves.
- **Combined-candidate finite can catch a cross-lane interaction red invisible on either lane alone — read the
  typed reason before calling it a bug.** S12-R7 2026-09-16: `test_B01_F` passed on B01's own lane, failed ONLY on
  the merged candidate (`assert eligibility["full_apply_executable"] is True` → False, reason
  `OCCURRENCE_GEOMETRY_BOX_MISSING: ... no boxed segmentation/prompt evidence`) — the fixture seeded occurrences
  without boxed geometry and BRIDGE's frozen B04 semantics now type-deny that. Classification: superseded POSITIVE
  control (deficient fixture), NOT a production bug; sibling of the contract-mandated-supersession FINDING class,
  but the file is IN the owner's write-set → bounded correction directly, no exception needed (contrast: the
  out-of-write-set reds route as FINDING + Codex decision). Procedure: ff-only the owner's worktree to the
  combined tip FIRST (its suite must run merged code) → bounded fix (persist boxed geometry via the sanctioned
  interface + assert the new timeline block + add the negative no-boxes node) → Manager re-run shows the count
  bump (27→28) with ≥2 consecutive green runs and `git diff --name-only PARENT..COMMIT` == EXACTLY the announced
  set (test + docs; production untouched). When a lane-vs-combined verdict disagrees, ALWAYS classify from the
  typed reason: superseded expectation / cross-lane defect / environment — never weaken an assertion, never
  declare regression without the lane-vs-combined comparison.
- **Post-sync guard "FAILED" on a continuing lane = stale pre-wave baseline, not drift — prove delta, then
  re-baseline.** After a lane's worktree is ff-synced to a newer combined candidate, re-running its PRE-WAVE guard
  manifests flags every other lane's transported change as `protected_file_changed` (CR2: protected 9/18, allow
  3/8). Reconciliation: (1) the authoritative proof-of-scope for the new commit is its parent —
  `git diff --name-only PARENT..COMMIT` == exactly the announced files (CR2: test + 3 docs); (2) SHA-match each
  flagged protected `after` hash to the owning lane's REPORTED post-hash (`s09_approval.py` `61916B71…` ==
  BRIDGE's own report value) → attributable, zero own-lane drift; (3) re-baseline: capture FRESH allow+protected
  manifests at the new base (allow grew to include the lane's earlier NEW module; protected grew to include OTHER
  lanes' NEW files, e.g. `publication_lease_guard.py`); keep old + new manifests both in lane evidence.
- **Transport round N+1 = one small prompt, same discipline as round 1.** A correction commit on an ff-synced
  lane re-enters via a short second INT turn: verify tip+porcelain → `git diff --name-only <sha>^ <sha>` ==
  announced set → `--no-ff` merge → static trio → LOG §N + ledger append → report merge SHA + new final tip;
  then finite re-run on the new tip → broad gate → probes → packet.
- **Final-gate trio on the frozen tip + env-test attribution.** Finite-v2 (lane suites exact list) and broad
  (scope kept R6-comparable: `tests/s12/` + `tests/test_s09_structural_lock_producer.py` +
  `tests/test_s09_reskin_config_api.py` + `tests/test_s10_full_apply_api.py`, `--ignore` the chain node) ran
  chained in ONE bg command (`finite; if exit 0 → broad`) so broad never starts on a red finite. R7 numbers:
  finite 197/197; broad 656 passed / 1 skipped / 1 red — and the red was the R5 env test executed WITHOUT its
  `S12_R5_*` env (a config miss, not a code red): re-run that dir separately with env, and only if it STILL
  fails attribute before alarming. R7-B2 case: the static probe inventory referenced node names renamed by the
  AUTHORIZED Q02 correction (`test_single_head_is_new_revision` → `test_single_head_is_current_head`, +1 more) —
  a supersession-class FINDING → bounded test-only sync to the QA owner (rename rows; provenance/env assertions
  stay byte-intact), never counted as a code defect.
- **Probe re-run hard requirements (frozen copy, hash-identical — v2).** PYTHONPATH must carry FOUR roots or
  probes die ModuleNotFoundError mid-collection: frozen root + `frozen/tests` + `frozen/tests/s12/s12-lc3-retry`
  + `frozen/tests/s12/s12-t03c` (probes do `import test_s09_structural_lock_producer as base`,
  `test_r4_retry_execution`, `test_publication`). `S12_REVIEW_OUT` = FRESH dir PER PROBE (probes `open('x')`;
  reused dir = immediate error) — inner_fence + planner abort with `KeyError: 'S12_REVIEW_OUT'` AFTER their full
  test logic ran, so classify a late KeyError as harness config, not a test failure. R7 outcomes: identity 3✓
  (probe sha == A-handoff sha `0b8ff350…`), inner_fence 1✓ (== VAL handoff sha `524d4a86…`), producer 6✓ (timing
  denials + DB controls). **A probe can fail BY DESIGN after an authorized interface change:** planner 2× fed the
  captured PRE-timeline authority → frozen Q7 types it `LEGACY_AUTHORITY_REAPPROVAL_REQUIRED` (zero-mutation) —
  record an explicit old→new mapping (semantic intent re-verified by the new D2 nodes) in
  `B/manager/REVIEW_PROBES_RERUN_R7.md`; never call it a regression, never weaken the probe to make it pass.
- **Provenance pins re-freeze as part of every AUTHORIZED amendment — the NEXT finite run is the gate that
  catches them.** `test_r6_finite_inventory.py::test_r6_reviewer_assertion_provenance_hash_proven` pins an
  `IN_REPO_IMMUTABLE` sha map over in-repo docs; when a granted bounded exception edits a pinned file, the pin
  fires on the following gate (R7 finite v3: `R5_MATRIX.md` expected `D601E8FA…` vs actual `9E136CC4…` after the
  authorized R5-sync `3444a49`). The pin is doing its job — the drift is AUTHORIZED, so re-freeze, never alarm:
  (1) reconcile ALL pins programmatically against the authorized commits (`393e1bf`+`3444a49`); only files inside
  those commits may be updated — ANY other drift ⇒ STOP + report (that one is a real drift signal);
  (2) bounded owner turn updates the pin(s) + re-runs the pin file (expect full-file green, e.g. 7 passed) +
  commits (`5947088`), then an INT round transports it;
  (3) **re-run the full finite after EVERY transport round** — each round can expose the next pin/expectation
  (v3 red → INT r4 → v4); the closing loop is `finite ⇄ transport` until one pass comes back clean, and each
  iteration is cheap (minutes), so never batch rounds before re-gating.
- **A public chain that now passes the FORMER seam and blocks at a NEW typed gate is progress, not failure.**
  R7 chain: S10 submit 202 (old 422 gone) → 6 chunks → publication → audio completed, then
  `BLOCKED_EXACT_S12_READINESS` (`S12_EXPORT_NOT_READY` ← readiness `not_run` ← no SCOPE_FULL QC run; public QC
  submit `422 QC_RUN_EVIDENCE_UNAVAILABLE` because server-side composition exists only for the audio band —
  Manager code-verified — and the repo's own E2E seeds the full-run row). Classification: pre-existing product
  gap → packet residual with exact 3-part evidence + options for Codex (implement non-audio composition vs rule
  the gate); zero fabrication, honest BLOCKED labels, chain node re-raises the recorded blocker by design.
  Same round: candidate frontend cannot `next build` as-is (Next 16 `useSearchParams` prerender — pre-existing);
  the UI acceptance still ran via a prod build in a disposable copy with **2 disclosed copy-only route-config
  lines** (`export const dynamic = "force-dynamic"`), lockfile bytes verified unchanged, screenshots + raw
  flow JSON as evidence, submit fail-closed + reload/reopen showing the same server-derived state.
- Playbook + pitfalls: `references/s12r7-two-manager-split-and-b-activation.md`; execution + transport round +
  combined-candidate CR2 fix:
  `references/s12r7-execution-and-transport-round.md` (§7: B01_F cross-lane interaction, guard re-baseline,
  INT round 2); final gates + probe re-run v2 + R7-B2:
  `references/s12r7-final-gates-and-probe-reruns.md`; closing rounds (QA chain outcome + R7-F1/F3 dispositions,
  R5-sync verify, INT r3/r4, provenance-pin re-freeze):
  `references/s12r7-closing-int-r3-r4-and-provenance-pins.md`.

## Cross-task defect cascade (schema/contract bugs found post-verification)

A verified task can still carry a binding-contract defect (S11: T02A enum used
`z_order/clipping/identity/flicker/audio_timecode` instead of the frozen 8
overlay codes + `edge_halo` missing). Manager verification must check enum
**VALUES against the binding text**, not just structure/count. When it cascades:

1. Diagnose precisely — run the cumulative gate, list EXACT failing tests and
   which owner each belongs to (a single enum fix broke T06A1 manifests then
   T02B fixtures; T03A/T06A2 were already correct).
2. **Pause sibling parallel workers FIRST** (process kill by session_id, never
   pkill) before they commit code against the wrong contract; their analysis
   is preserved because sessions resume with full context.
3. Route ONE finite correction packet per affected owner; ff the exact task
   branch to current canonical before resuming the exact session.
4. After all corrections land: cumulative gate again (expect the pre-fix
   failure count to drop to zero), then push once (INT01 may stop on
   remote≠local — see local-ahead below).
5. Recovered W6 session IDs via `hermes sessions list`; leave their stray
   untracked drafts in place, tell the resumed worker to re-scan them against
   the fixed contract (they own their worktree).

## INT01 remote-drift interaction (authorized local-ahead)

INT01's pre-merge guard requires `ls-remote == local HEAD`. If the Manager
merged an earlier task locally but told INT01 "no push yet", the next INT01
merge halts `BLOCKED_REMOTE_DRIFT` even though the remote is INT01's OWN last
push (no foreign writer). Manager then explicitly authorizes local-ahead for
that wave: "remote X = push của chính bạn; local = X + verified tasks; merge
now, push after gate". Always verify the remote SHA is self-originated before
waiving — a foreign push is a true BLOCKED_REMOTE_DRIFT. INT01 documents the
waiver in its wave evidence.

## Exit-gate specifics (10-item frozen gate)

- **Mypy cross-file false-positive routing**: `mypy file.py` follows imports —
  remaining errors after an owner's fix are often OTHER owners' unmerged
  branches. Verify per-owner on their own file(s) (their errors gone), merge
  ALL corrections, then re-run mypy on the integrated HEAD → Success.
  Exit-gate mypy corrections are small (1–3 lines) — dispatch several owners
  in PARALLEL (disjoint files), same pattern as W6.
- **Alembic round-trip**: pass `alembic -x db_url=sqlite:///<temp>` (env var
  is NOT honored by this project). A "downgrade" to the CURRENT head is a
  no-op — downgrade must target the PREVIOUS revision to actually prove the
  round-trip; then `PRAGMA foreign_key_check` + `integrity_check`.
- **Negative-scan matches are usually assertions**: grep hits like
  "UNKNOWN"/"accept"/"whole-project" in tests/code are negative binary tests
  (no-UNKNOWN assert, zero accepted-exception DOM scan, whole-project-rerun
  forbidden scan). Read context before flagging a finding.
- **Frontend build with shared node_modules**: node_modules shared read-only
  via junction (verify package-lock hash match FIRST — MAIN's lock often
  differs from worktree lock; s08 archive matched). Turbopack `next build`
  FAILS on junction ("Symlink ... points out of the filesystem root") —
  use `npx next build --webpack`. Junction creation: PowerShell
  `New-Item -ItemType Junction` (cmd `mklink /J` did not execute under this
  bash). Playwright output/tests to task-owned %TEMP% roots; a canonical
  `frontend/test-results/.last-run.json` with old mtime is pre-existing
  (staging-time), attribute by mtime before calling leak.
- One fresh measured run per gate suffices; do not re-run unchanged heavy
  suites twice. Track protected hashes at exit: S10 route/test byte-identical;
  T01 files byte-identical EXCEPT files the sprint was authorized to extend
  (T04C handler extension) — record as authorized change, not drift.

## Monitoring / liveness / ETA

- Heartbeat ≤20 min while writers active; 8-min no-progress ⇒ audit process,
  session input state, log growth, ports. Transient 502/504 ⇒
  `RUNNING_RETRY_WAIT`, wait 5 min, resume same owner/model, unlimited cycles.
- **Visible heartbeat: local-only cron is invisible, gateway-off cron never
  fires.** (S12 2026-09-07 — user asked "heartbeat đâu sao ko thấy".) A
  no-agent cron with `deliver=local`/`local`-only output is saved but never
  shown to the user; heartbeat jobs MUST use `deliver=origin`. `hermes cron
  list` prints "Gateway is not running — jobs won't fire automatically" when
  the gateway is off — then cron is decorative only, so ALSO run the bg-loop
  fallback AND prove liveness visibly each status turn: show the cron list
  (active + next_run_at), the remind-log tail (real timestamps), and the
  worker's fresh message/WT state. When a new sprint starts, PAUSE the prior
  sprint's reminder cron the same turn the new one is created (S11 15m paused
  when S12 10m created) — double-nudge on one Manager session confuses
  ownership. Prefer a 10-min cadence while writers are active (user: 10', not
  30', "thấy hay dừng lắm").
- **All-green-but-uncommitted worker gets a commit order, not another gate.**
  (S12-T05 2026-09-07: 303 msgs, pytest/TSC/Playwright all green, worker
  wrote "Chưa commit — chờ lệnh".) When the worker reports every gate green
  and is waiting, order the allowlisted `git add` + commit + TASK_SUBMITTED
  in the SAME turn via a `--resume` nudge — never ask permission, never run
  another gate round first. Verify the commit yourself right after (show
  --stat, allowlist check, diff-check).
- **Stall watchdog (no-agent cron + bg-loop fallback).** For parallel
  correction lanes: no-agent cron `*/10` running `scripts/lane-watchdog.py`
  (copy per sprint, configure LANES) — SILENT when healthy, nudges the EXACT
  owner session on >30' stall (log frozen + session quiet), max 2/tip, pinned
  model, never a new worker. Gateway OFF ⇒ cron never fires, so ALSO start a
  `while true; sleep 570` bg loop and kill it once the gateway is up.
  Terminal-marker FIRST (S11-C1 lesson, 2026-09-04: 2h false-BLOCKED): read
  the worker's own terminal line (`TASK_SUBMITTED` / `NEEDS_T04B_*` plus an
  `EXIT=`/`NUDGE*_EXIT=` trailer) from the FULL dispatch log BEFORE any stall
  judgment — a submitted lane goes log-quiet + session-quiet by design, and
  silence is not stall. Tolerate markdown prefixes (`**`, `-`, `+`) and prior
  WATCHDOG-SIGNAL lines; REPORT citations without a terminal line do not
  count. The watchdog must ALSO watch the Manager's own follow-ups (verify /
  merge / gate tasks): all lanes DONE but Manager tasks pending >60' ⇒ ping
  the Manager session — never go SILENT on a half-finished sprint (S11-C1:
  workers done 03:21, Manager idle until user asked at 07:19).
- **Committed state outranks the wrapper exit code.** A dispatch wrapper can
  report `EXIT=1` (route 403, quota, transient) AFTER the worker already
  committed the substantive work — the failure belongs to a post-commit
  nudge/trailer, not the lane. Procedure: on any non-zero exit, check tip
  movement + porcelain + `show --stat` BEFORE judging the lane failed. If the
  expected commit landed on the exact branch, the lane is DONE-with-evidence:
  verify the commit locally (tests/mypy/diff/guard need zero model calls)
  instead of re-dispatching the work. Re-dispatch only what is genuinely
  missing.
- **Ack-only resume is zero state advance — answer with exact commands, not
  another status nudge.** A `--resume` that returns one plan sentence
  (`Gate: pytest ... rồi commit nếu xanh. session_id: ...`) with zero tool
  calls and an unchanged tip/porcelain is NOT progress even though the
  wrapper exits 0. Never follow it with a "báo trạng thái" nudge —
  immediately re-resume ordering the literal commands in the same turn
  (exact pytest argv + isolated basetemp, exact ruff argv,
  `git diff --check`, then allowlisted `git add` + commit + TASK_SUBMITTED
  + SHA on green; explicit NO push/merge), each with its real output quoted
  back. (S12-C1 W4 T03C 2026-09-08: `t03c-finish-144841.log` held only the
 ack line; the follow-up `t03c-gates-*` resume carried the three exact
 gates.)
 - **Ambiguous one-line worker error reports get a 4-line clarify first.**
 A worker reporting `Lỗi tool C22` (S12-C1 W7 T06B 2026-09-09) turned out to
 be its own empty `terminal(command=None)` call made while reading evidence
 outside its scope — not a test failure, and C22 was not even its row. Before
 escalating an ambiguous one-liner: resume ordering EXACTLY 4 lines back —
 (1) tool name + the real command run, (2) file/test where it happened,
 (3) whether inside its own allowlisted scope, (4) 20-line traceback — and
 nothing else. Act on the clarify answer, never on the one-liner.
- **Escalation after two consecutive ack-only turns: run the gates YOURSELF.**
 Stop nudging and execute the read-only verify inside the task worktree
 (pytest + ruff + `git diff --check`, zero model calls, explicit basetemp
 under the real Windows Temp per the env quirk above), then order a
 commit-only resume. (S12-C1 W4 T03C 2026-09-08: three ack-only turns with
 tip frozen at `75352b5`; Manager-run pytest first showed 18 errors caused
 by the hijacked `$TEMP`, reran with the real Temp path → 19 passed, ruff
 clean, diff-check clean → commit-only order landed `9a91e18`. Ground truth
 beats the third nudge.)
- **Same escalation covers lifecycle/packaging lanes: run the FULL harness
 yourself.** After ack-only turns with a frozen tip on a lifecycle lane,
 execute the whole harness in the task worktree with zero model calls:
 preflight → build-manifest → setup → serve on isolated ports → diagnose
 (pids alive + free-disk) → stop with ports-down proof (curl `000`/refused)
 → uninstall with data-preserved proof, plus ruff + `git diff --check`. A
 harness rebuild regenerating `manifest.json` (new timestamp +
 source_commit) is expected allowlisted dirty — verify via `git diff` that
 only timestamp/source_commit changed, then commit it; never flag it as
 drift. Then order commit-only. (S12-C1 W6 T06A 2026-09-09: three ack-only
 turns at `ddc5d05`; Manager-run lifecycle: backend pid 38272:8423 HTTP
 200, frontend pid 10224:3123 HTTP 200, diagnose pids alive, stop ports
 000, uninstall data kept, ruff clean, diff-check clean → commit order.)
- **Verifier lane with zero diff re-measures green = DONE on the same SHA —
  never force an empty commit.** A read-only acceptance lane (zero prod
  touch by contract) that re-runs its full suite + live matrix green with
  porcelain 0 and an unchanged tip has nothing new to commit; its
  TASK_SUBMITTED stands on the existing SHA with fresh measured evidence.
  Verify tip + porcelain + gates-log yourself, record the re-measured
  numbers (counts, CPU/GPU/fps/wall, ruff, diff-check) in the lane evidence,
  and move the wave forward — do not order a no-op commit or hold the lane
  open for bytes that must not exist. (S12-C1 W7 T06B 2026-09-09: tip stayed
  `48bf514`, porcelain 0, suite + hardware matrix re-measured green,
  TASK_SUBMITTED on the same SHA.)
- **Transport-cutoff resume: verify ground truth before re-issuing anything.**
  When a turn dies mid-stream (network error) and the next turn is ordered
  to continue where it left off, the cut-off tool call may or may not have
  executed. Never re-issue a mutating command (kill, dispatch, patch,
  commit, merge, push) blindly — first run one cheap read-only probe (`ps`
  for the PID, `git status` / `log --oneline -1` for the tip, `ls -la` for
  the file) and continue from the verified state. Re-killing an already-dead
  PID is harmless (`No such process`); re-dispatching an already-running
  worker is not — the probe tells which one you face. Truncated worker
  fragments (`Th`, `Com`, `SHA`, `RULES_LO`, `( 3 xanh` — S12-C1 W4/W6
  2026-09-08/09) are transport artifacts, never results: never quote them
  as progress, verify tip/porcelain/log instead. After YOUR OWN reply is
  cut mid-stream, resume with the tool call first and zero narrative — the
  harness rejects plan-only continuations.
- **User skepticism about a merged state ("chắc chưa / sao nhanh thế được")
  ⇒ re-prove with live gates + ancestry, never defend with commit messages.**
  (S12-C1 INT01 2026-09-09: canonical jumped `0d2e063` → `ea78497` with 4
  merges + packet while this Manager session was network-cut; user doubted
  the speed.) Procedure: (1) `git log --format='%h %an <%ae> %ad %s'` +
  `git merge-base --is-ancestor <worker-tip> HEAD` for EVERY claimed commit —
  proves each worker commit is really in canonical; (2) re-run the per-dir
  gates on canonical HEAD yourself (zero model calls, short basetemp) and
  compare the SUM to the packet's numbers (re-ran 7 dirs → 221 passed + 1
  skipped, matched packet exactly); (3) ruff + diff-check + porcelain as the
  closing trio; (4) disclose provenance plainly: merges that landed while
  your session was down were performed by another INT01/Manager instance and
  you verified them independently — same dichotomy as the self-authored-merge
  rule, opposite side (claiming credit you did not earn is as wrong as crying
  intruder over your own work); (5) read the packet's own disclosure before
  judging (the C1 packet openly declared the duplicate-basename per-dir
  choice) — a disclosed evidence decision is not a hidden defect.
- ETA questions ("bao giờ xong", "estimate", "báo cáo đi"): respond in
  VIETNAMESE, lead with current status first. `date` (+07) first, lane/wave
  table with REAL state (running Xs / TASK_SUBMITTED / BLOCKED + reason),
  per-wave ETA table anchored to the date, buffer policy stated explicitly
  (worker-chết + reasoning-max), slippage reported immediately with reason —
  never silently slip. Worst-case band lands next morning.
- **Status pings end with action, never a permission question.** When the user
  asks "xong chưa" / "vấn đề là gì" / "bao giờ xong", answer with real state
  (date-anchored table + root cause + next step) AND dispatch the next
  nudge/verify/commit in the SAME turn. Ending a status reply with "Muốn tôi
  ... không?" forces the user to re-order work you are already authorized to
  do (S11-C3 2026-09-05: status reply asked permission for B16; user had to
  say "làm nốt ... đi"). Authorization already granted ⇒ act, then report.
- PROACTIVE reporting (user 2026-09-04 correction): when a worker EXITS —
  especially terminal BLOCKED/RECOVERED — report the user IN THAT SAME TURN
  before continuing verify work. Never work silently then wait for the user
  to ask "báo cáo đi". "Tăng tốc / chạy liên tục" ⇒ dispatch independent
  lanes in PARALLEL background processes (one per lane, own workdir +
  notify_on_complete, generous timeout), keep running without re-asking;
  pre-stage the next dependent node mid-flight.
- Model route is PROMPT-OVERRIDDEN, not skill-pinned: the dispatch prompt's
  exact provider/model/reasoning/fallback/TTFB wins over the example command
  above. S11-C1 (user 2026-09-04): provider `custom` (9Router hiện có),
  model `ocgfree/muse-spark-1.3-contributor-free`, requested reasoning `max`,
  fallback `OFF`, TTFB `900`s via `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`;
  resume with `--resume <exact-owner-session-id>`. If route/model fails,
  log raw error, wait ≥5 min, retry same session once — never swap model,
  never fallback, never create a replacement owner (`BLOCKED_MODEL_ROUTE`).

## Finite correction-sprint pattern (S11-C1, 2026-09-04)

- Trigger: Codex verdict `CHANGES_REQUESTED / NOT_APPROVED / S11_NOT_CLOSED`.
  Open ONE new compact Manager (no resume of full-sprint Manager); Manager
  only coordinates/verifies/records — never edits production code/tests.
- Registry: run-id root `MotionForge2D-evidence/<sprint>/` with
  `manager/{REGISTRY.md,raw/,exit/}` + `lanes/<lane>/prompt.md`; REGISTRY
  pins SHA-256 + bytes + lines of EVERY authority doc (rules, AGENTS,
  SESSION_PROTOCOL, CODEX_PM_HANDOFF, ROADMAP, latest PM review, sprint
  prompt, binding plan, prior NEXT_REVIEW_PACKET, plus the binding
  correction prompt itself). Preflight 1–7 raw evidence before any dispatch
  (porcelain 0, HEAD == ls-remote == reviewed HEAD, zero S11 writers per
  exact-owner rule, no DB overrides, critical-file hashes, task worktrees
  clean + FF-able, run-id created).
- Lanes resume EXACT owners (high token count alone never justifies
  transfer); each lane gets a compact handoff: exact finding, current
  canonical SHA, allowlist, forbidden files, executable acceptance matrix,
  test commands, terminal condition. Two bounded resumes with no usable
  progress / repeated scope / lost contract / unsafe write ⇒
  `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`, wait for Codex.
- Conditional lane (C1-D pattern): NOT dispatched by default — only when
  another lane produces an executable failing reproducer for a production
  defect; serial dependent wave (C2 pattern) only after the authority lane
  merged + pushed + combined gate green. INT01 stays pure Git transport.
- **Reviewer probes outrun lane matrices: harden for absence/tamper/history
  pressure.** S11-C2 lesson (2026-09-04): C1 lanes were green yet Codex's
  fresh adversarial probes failed — (a) completion validators that
  `or 0`-default missing `summary.errors`/`checks_skipped` accept tampered
  completions as valid (fail-open); missing/null/bool/string/unreadable must
  fail closed, never default to zero; (b) querying newest-with-limit BEFORE
  scope filtering lets 50+ newer audio/partial jobs evict a valid full
  authority — query newest matching FULL directly, no mixed-page scan; (c) an
  executable "restart" test that re-enqueues the NEIGHBORING workflow
  (full QC) instead of the required one (correction/recompute) proves the
  wrong path — the test must call the real bridge/API under test, recreate
  the worker over the SAME durable DB/root, and compare affected vs
  unaffected bytes. Finite matrix rows to require: missing/null/string/bool
  per required field, identity/fingerprint/policy-mismatch, count-off
  (0/9/11/unequal), cancelled/deadline-true, duplicate/missing/extra item,
  empty revision values, 51-and-101 newer-audio history pressure, newest-full
  nonterminal/stale/corrupt no-fallback, zero-item-ready + blocker-blocked.
- Terminal when green is ONLY
  `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW` — never
  write APPROVED/CLOSED; never open next sprint.

## Mid-sprint route switch + pause/resume orders (S11-C2, 2026-09-04)

- **User-ordered model switch mid-sprint.** Trigger observed: free-tier route
  (`ocgfree/...-free` @ custom 9Router) returned HTTP 502
  `FreeUsageLimitError` (rate limit), killing a dispatch with EXIT=1; user
  ordered "đổi hết worker sang model tôi đang dùng" → new route
  `cmc/meta/muse-spark-1.3-contributor` @ `muse`. Procedure: (1) confirm zero
  workers still running on the old route (`process list` + cmdline scan for
  `hermes chat --resume`) before switching; (2) record old → new route +
  reason in the registry; (3) every subsequent dispatch/resume pins the new
  `-m/--provider` explicitly — never rely on profile defaults (an unpinned
  `--resume` silently runs the profile DEFAULT model, verified 2026-09-04 on
  keep-alive nudges). Never mix routes inside one wave; never silent-fallback
  on auth/quota errors — 502/quota AFTER the switch is retried on the SAME new
  route per the 5-min rule, not swapped again.
- **Purge stale pins of the old model after a switch.** Grep every live
  script/config/prompt for the old model ID and comment/disable or re-pin
  each hit — a dead script with a live old-model pin becomes a violation the
  moment anything re-runs it (S11-C2 2026-09-04: `NUDGE_MODEL =
  ocg/muse-spark-1.2-contributor` left live in `s11c1_watchdog.py` after the
  user ordered 100% 1.3; commented it out and verified zero live
  `muse-spark-1.2` references outside a read-only `.db` copy). Verify with a
  repo-wide grep, not by memory.
- **Quota-driven selective teardown: kill exact old-route consumer PIDs,
  prove the preserved route intact.** (S12-C1 2026-09-08: user ordered all
  cmc stopped to save quota while switching every worker to
  `ocgfree/muse-spark-1.3-contributor-free` and continuing work.) Procedure:
  (1) enumerate old-route burners by FULL cmdline —
  `ps -ef | grep -E "watch_24|heartbeat_s12|remind_s12"` names the watchdog
  PIDs plus the bash `while true ... sleep 600` heartbeat loop invoking the
  remind script whose `MODEL=` constant pins the old model; attribute every
  PID before touching it; (2) write a TARGET checklist naming the exact PIDs
  to kill AND what must stay alive (other-route workers, owner sessions,
  worktrees, canonical); (3) `kill <pids>`, re-`ps` to verify, `kill -9`
  survivors, re-`ps` to prove zero old-route loops; (4) run a separate
  intact-check `ps` for the preserved-route PIDs; (5) pin audit
  `grep -rln <old-model>` vs `grep -rln <new-model>` over the evidence root
  (S12-C1: 11 files old, 0 new = fail-proof the switch had not landed), then
  re-pin only live dispatch paths + errata for history, never rewrite
  history. Never broad-kill (`pkill`/`killall python` kills the agent
  itself) and never kill by model-name grep alone without PID+cmdline
  attribution. (6) When the same user turn ALSO orders continuity ("chay
  lien tuc"), re-arm the watch loop on the new route IN THE SAME TURN:
  restart the bg script with the new `-m/--provider` pin, verify the new
  PID alive + a first log line lands — otherwise the quota save itself
  becomes the stall the user then reports ("sao cu tu dung the", S12-C1
  2026-09-08: cmc loops killed, v3 loop PID 30640 started on ocgfree).
  Before patching the loop script, `cp` it to `.bak-<route>-<UTC-ts>`; a
  patched file never updates the already-running loop — old PIDs keep
  executing the pin loaded at start (S12-C1 v4 2026-09-08: file patched to
  cmc while PIDs 65010/65022 still ran ocgfree code loaded at 19:46), so
  kill them first (`No such process` on an already-dead PID is fine —
  prove by empty `ps`) then start fresh and confirm the new START line +
  PID in the log.
  A remind-log tail reading `Session not found: <old-manager-sid>` after
  teardown is transfer/prune evidence, not a loop defect — record it, never
  re-create the old-model loop to "fix" it.
- **Explicit pause vs ambiguous question.** "từ từ" / "dừng" / "đợi tí" is an
  explicit HALT: stop all dispatch immediately, leave trees untouched, report
  frozen state. Resume ONLY on an explicit go ("chạy tiếp đi"). Colloquial
  questions ("m ko nhắc nữa à?", "đang chạy chưa?", "alo") are NOT stop orders
  — answer status and keep running. (Pairs with the keep-alive rule in
  background-worker-orchestration: ambiguous ≠ stop; explicit pause = stop.)
- **`-m` pin rule is conditional, not absolute.** An unpinned `hermes chat
  --resume <sid>` runs the resumed session's stored model, falling back to the
  profile DEFAULT. So: when the target route EQUALS the profile default (e.g.
  the user's own current model after a mid-sprint switch), unpinned resume is
  the simplest safe form — verified S11-C2 2026-09-04: three consecutive
  unpinned resumes (C2-B T05A, INT01 M3, INT01 ladder) all ran
  `cmc/meta/muse-spark-1.3-contributor`, zero `1.2`/`ocgfree` strings in
  dispatch logs, zero quota errors. Pin `-m/--provider` explicitly ONLY when
  the target route differs from profile default or for brand-new sessions
  (`hermes chat -q` without `--resume`). Never mix routes inside one wave.
- **Resume dispatch arg shape: prompt MUST go via `-q`.**
  `hermes chat --resume <sid> -Q "<prompt-text>"` FAILS with
  `unrecognized arguments` — the CLI only accepts the prompt through
  `-q/--query`. Correct form:
  `hermes chat --resume <sid> -m <model> --provider <prov> -Q -q "$(cat prompt.md)"`
  (verified S11-C4-R1 2026-09-05: resume without `-q` rejected, retry with
  `-q` resumed OK). For very long prompts prefer writing prompt.md to the
  evidence root first and using `$(cat ...)` rather than inline text.
- **Live user route order beats a prompt's exact-ID pin.**
  When a binding prompt demands an exact model ID that is ABSENT from live
  `/v1/models` (verify + count the IDs, save models_raw.json) and the user
  in-turn explicitly orders a PRESENT alias with a `PROBE_OK` probe, user
  authority wins: proceed on the user-ordered route, and record the
  divergence (exact-ID ABSENT evidence + user order + probe session/exit) in
  the run-root for Codex to adjudicate — do not hard-stop at
  `BLOCKED_MODEL_ROUTE` against an explicit user order (S11-C4-R1
  2026-09-05: exact `cmc/muse-spark-1.3-contributor` ABSENT among 142 IDs,
  user ordered `cmc/meta/muse-spark-1.3-contributor`, probe `PROBE_OK`
  session `20260905_163747_de1a1f`).
- **ABSENT verdicts require a programmatic full-list match — never a
  pretty-printed/head-truncated grep.** (S12-C1 2026-09-08: first check
  piped the model list through a display filter + `head -20` and reported
  `ocgfree/muse-spark-1.3-contributor-free` ABSENT; the user pushed back
  and a JSON-parse match over the full 149 IDs found it present.) Rule:
  `curl /v1/models | python -c "parse JSON, match the exact id string over
  ALL entries"` — print count + full match list. Only a zero-match on the
  full programmatic list justifies `BLOCKED_MODEL_ROUTE`; a truncated
  human-readable view never does.
- **Route probes need the REAL key from config — a display-redacted key
  returns a false `invalid_api_key`.** Copying the redacted form shown in
  config listings (`sk-cff…`) into a probe makes the probe itself invalid,
  which looks exactly like an auth blocker. Read `api_key` from
  `~/.hermes/config.yaml` in python (regex the provider block,
  `utf-8-sig`) and POST `/v1/chat/completions` via urllib with
  `max_tokens:5`; `PROBE_OK 200` = route live. Same class of false negative
  as the truncated-list grep above: always verify with the same bytes the
  real client would send (S12-C2 re-kickoff 2026-09-09: curl probe with
  truncated key → `invalid_api_key`; python probe with config key → 200).
- **Explicit pin rejected with 403 ⇒ drop the pin, keep the route.**
  Verified S11-C3 2026-09-04: `-m cmc/muse-spark-1.3-contributor --provider
  custom` returned HTTP 403 `Model/provider not recognized` on BOTH lanes
  (A1 after a successful N2 on the same pin — route flapped mid-wave; A2
  died at N4 with uncommitted bytes). The 403 rejects the PIN FORM, not
  necessarily the model. Procedure: (1) do NOT retry the identical rejected
  rejected pin in a loop; (2) retry once as UNPINNED resume on the same exact session
  (stored/default model is the authorized route when it equals the target);
  (2b) ROUTE OUTAGE NEVER IDLES THE MANAGER — pytest/mypy/diff-check/guard/
  allowlist gates run locally with zero model calls, so verify every landed
  commit immediately while the route is down (S11-C3 2026-09-05: T03G 143
  passed + mypy + diff-check all verified during the 403 outage) instead of
  waiting for the route to recover;
  (3) record the 403 verbatim + which pin form failed in the registry as
  `BLOCKED_MODEL_ROUTE (pin form)` evidence; (4) only if unpinned also fails
  with auth/quota, declare wave-level `BLOCKED_MODEL_ROUTE` and ask the user
  for a new route — never silent-swap. Opening extra workers on the same
  rejected pin just multiplies failures; one retry worker max.

## Evidence layout

- `C:\Users\Admin\MotionForge2D-evidence\<sprint>\manager\{ledger,gates,int01}`
  (registry + wave ledger, INT01 prompts/logs) and
  `<sprint>\<TASK-ID>\<token>\{prompt.md, baseline_manifest.*, dispatch.log}`.
- Registry rows: task | worktree | branch | WAVE_BASE | session | writer state
  | commit range | Manager verdict | integrated remote SHA.
- Final packet `manager/exit/NEXT_REVIEW_PACKET.md`: all 19 IDs + INT01 mapped
  to session/model/worktree/branch/range/remote SHA, wave ledger, raw write
  audit, protected hashes, migration/OpenAPI/frontend/leak evidence,
  quiescence proof, explicit zero S13 dispatch.

See `references/s11-w1-w3-playbook.md` for the annotated real transcript
(preflight commands, INT01 charter + wave merge/push prompts, wave-gate
commands, registry table) from the 2026-09-03 S11 run,
`references/full-sprint-corrections-and-exit-gate.md` for the W4→W14
correction-cascade / paused-worker-resume / local-ahead / exit-gate playbook
from the same run, and
`references/s11c3-exact-identity-restart-proof.md` for the finite
exact-identity + restart-proof + fail-fast-exit correction pattern
(five-row authority matrix, affected/unaffected preimage proof, per-command
exit preservation, hermetic evidence roots, post-compaction evidence
discipline) from the 2026-09-04 S11-C3 authorization, and
`references/s11c4-production-registry-fail-closed.md` for the
production-bootstrap recovery class (clean-process empty-registry probe,
`ensure_full_band_registered` composition, guessed-`1.0.0` removal,
revision matrix, local-object FF when fetch is blocked, serial
machine-wide gates, guard-Failed attribution) from the 2026-09-05 S11-C4
authorization, and
`references/s11c4r2-owner-transfer-and-resume-recovery.md` for the
two-writers-on-one-worktree freeze rule, read-only state-DB
`messages.tool_calls` forensics (payload SHA-256, no `tool_calls` table),
and wrapper-dead/session-alive resume discipline from the 2026-09-05
S11-C4-R2 owner transfer, and
`references/s11c4r3-durable-contention-and-evidence-closure.md` for the
R3 true-contention rendezvous-inside-the-lock shape, durable KI/SystemExit
subprocess test, 6/152 node arithmetic, five-untracked-file
dirty-attribution guard, and truthful failure-indexing packet from the
2026-09-05 S11-C4-R3 correction, and
`references/s11c4r4-deterministic-lock-attempt-and-evidence-closure.md` for the
R4 deterministic B-lock-attempt probe (delegating RLock wrapper +
`b_lock_attempted`), Manager-identity binding, 14-row R4 preimage baseline +
real `commands.jsonl`, and R2→R3→R4 supersession provenance from the
2026-09-06 S11-C4-R4 correction, and
`references/s11c4r4-inflight-retry-and-poll.md` for the transient
`CommandCode server_error` retry-as-502 rule, zero-model-call liveness polling
via global `messages.id` (not the stale per-session counter), single-root
discipline, and the guard tool's MAIN-tree path + `--root/--manifest` arg shape
from the same R4 round, and
`references/s11c4r5-live-ledger-evidence-only.md` for the truthful live-ledger
remedy (self-recording runner with START/END events, recorder self-test,
mechanical jsonl validation, actual-test negative controls, version-attributed
mypy, same-suffix scaffold disclosure) from the 2026-09-06 S11-C4-R5 closure,
and
`references/s12-kickoff-state-reconciliation.md` for the
snapshot-vs-live-order STATE_RECONCILIATION rule, new-sprint bootstrap from a
frozen HEAD, and the 3-signal worker-liveness audit from the 2026-09-07 S12
kickoff, and
`references/s12t01-double-dispatch-freeze.md` for the single-wrapper
double-dispatch detector, FROZEN_ACK duplicate-freeze, and nudge-timeout
liveness check from the 2026-09-07 S12-T01 dispatch, and
`references/s12-parallel-wave-integration.md` for the merge-tree pre-check,
self-authored-merge attribution, push-up-to-date vs ls-remote gap, and T03B
pre-staging under a blocked DAG from the 2026-09-07 S12-W2 integration, and
`references/s12-t03b-delegation-silence.md` for the subagent-delegation
silence-as-stall rule, wrapper-timeout nudge-landing proof, and second
self-attributed merge check from the 2026-09-07 S12-W3 lane, and
`references/s12-visible-heartbeat-and-commit-order.md` for the
visible-heartbeat fix (deliver=origin, gateway-off proof, pause-prior-cron)
and the all-green commit-order shape from the 2026-09-07 S12-W5 lane, and
`references/s12-t06b-direct-write-escalation.md` for the direct-write
escalation ladder (status-nudge trap, exact-file order with read ban),
failed-wrapper message-landing rule, and zero-model-call pre-gates from
the 2026-09-07 S12-W7 lane, and
`references/s12c1-preflight-session-identity-gate.md` for the
session-identity gate (BLOCKED_OWNER_SESSION on Manager mismatch + live
Manager), contract-path locate-by-search, snapshot-vs-live re-verify, and
reminder-loop identify-never-blind-kill from the 2026-09-08 S12-C1 preflight, and
`references/s12c1-24-7-watchdog-and-w3-start.md` for the explicit-24/24
watch-loop (read-only 5-min checks + 15-min stall nudge, kill at submit),
fetch-blocked-but-ls-remote-OK START decision, and truncated-reply recovery
from the 2026-09-08 S12-C1 W3 lane, and
`references/s12c1-w4-t03c-unmocked-repro-and-session-switch.md` for the T03C
unmocked-repro fix (ChunkSpec content_hash + keyword-only readiness call,
real-chunk-file R1b) and the lightweight session-switch re-anchor checklist
from the 2026-09-08 S12-C1 W4 round, and
`references/s12c1-int01-merged-gate-and-route-quota.md` for the merged-canonical
gate on duplicate test basenames (per-dir loop + short basetemp), the
pre-fix-behavior test routed to its owner (F-OBS-01 closed by T01-C1), the
cmc weekly-quota 429 blocker switch to the last user-authorized route, and
the T06A lifecycle-harness escalation (`diagnose/stop/uninstall` take only
`--install-root`) from the 2026-09-09 S12-C1 W6/W7/INT01 rounds, and
`references/demo-visual-claim-verification.md` for independent pixel-claim
verification (pixel-diff event arbiter, dual-pass vision text rule, resume
lineage, stale-watchdog clearing, model-ID errata) from the 2026-09-08
DV3-R2-T01 demo lane, and
`references/s12c2-kickoff-manager-continuation.md` for the same-manager
correction-sprint continuation (identity pin by SID, review-dir required
reading, stale-review-PID vs live watcher PID attribution, prompt-pinned CMC
429 probe then live-user route override to ocg/deepseek-v4-flash, fresh
<run-id>-C2 root + guards, W1 dispatch same turn, C1 anti-substitution rows)
from the 2026-09-09 S12-C2 kickoff, and
`references/s12c2-rerun-after-partial-kickoff.md` for the re-sent-prompt
continuation (reuse the existing <run-id>-C2 root instead of a second one,
read the prior dispatch log tail to learn the previous W1 ended in a
transient 502 after an analysis-only turn, real-key route probe via python
urllib, complete missing W0 MATRIX/REGISTRY during the retry turn) from the
2026-09-09 S12-C2 re-kickoff, and
`references/s12c2-w1-w4-wave-execution.md` for the repeatable INT01
wave-transport resume template (merge verified SHAs → push → ff next-branch
base, used 3× clean), the manager verify-then-chain wave loop (independent
re-run before INT01), the analysis-only-first-turn pattern (follow with a
tight IMPLEMENT turn that embeds ABSOLUTE review paths — one worker read the
Luna demo review instead of the S12 one), cross-wave contract consumption
naming (authority §8 / source_locked / CAS / byte-identity), and the
collection-conflict rename as a source-lane fix from the 2026-09-09 S12-C2
W1→W4 execution, and
`references/s12c2-w5-cross-lane-result-endpoint-gap.md` for the cross-lane
contract gap discovered by a consumer lane (backend merged without its
promised result/download endpoints → route a BOUNDED ADDENDUM to the exact
owner, never fake the endpoint, consumer continues disjoint work in
parallel) and the REPORT-rows-vs-prompt-§5 completeness check from the
2026-09-09 S12-C2 W4→W5 handoff, and
`references/s12c2-w5-diverged-base-merge.md` for the diverged-owner-branch
transport fix (ff-only exit-128 topology report → INT01 authorized
`merge --no-ff <canonical-SHA>` INTO the clean owner branch per prompt §3,
conflict-free on disjoint file-sets, no push of the owner branch, then
owner finalize on the real endpoints) from the 2026-09-09 S12-C2 W5 lane, and
`references/s12c2-w6-w7-closing-waves.md` for the closing-wave playbook (cheap
verify-only tips, regression-count shifts after an addendum merge — T03C 30→35,
verifier second-round asserts old pinned-fail now PASSES on canonical, and the
final INT01 merge → frozen per-dir gate → packet → zero-watcher checklist)
from the 2026-09-09 S12-C2 W6/W7 lanes, and
`references/s12c2-finding-loop-reencode-validation.md` for the
source-locked-exact-digest-vs-re-encode loop (verifier F11-T06B-01 positive
blocker → producer findfix builds SourceReference/AudioReference/CutPoint from
the approved artifact via T04A probe helpers, validator interface-delta
`frame_match_mode exact|psnr` + per-frame PSNR probe with ALL tamper cases
still-FAIL proof, producer wires per-profile mode + expected_sha256) from the
2026-09-09 S12-C2 W7 closing rounds, and
`references/s12r6-codex-to-hermes-transfer-and-guard-reconciliation.md` for the
Codex→Hermes owner-transfer round (readiness-then-work two-phase dispatch,
batch upstream-502 incident + same-session 5-min resume cycle, post-merge
guard reconciliation with blob/EOL proof, symlink-safe snapshots, QA/RETRY
submission verification) from the 2026-09-15 S12-R6 handoff."