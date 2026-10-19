# Manager-role sessions (orchestrator variant of PM-gated execution)

> SKILL.md is at its size cap, so there is no inline pointer — future manager-role
> prompts should load this file directly: `references/manager-role.md`.

Add-ons that apply when the prompt casts the agent as **Manager** (preflight / resume
owner sessions / dispatch workers / run gates / report) rather than a hands-on writer.
Base sequence (rules load → git baseline → LOG → scoped work → gates → report) still
comes from SKILL.md; this file only covers what's different in manager mode.

## Rules-file protocol

- Projects running this pattern pin a canonical rules doc, e.g.
  `docs/pm/HERMES_AUTOPILOT_RULES.md`. Read it IN FULL every turn that performs
  preflight/dispatch/resume/report-edit — not from memory, not from an older summary.
- Emit the ack token the prompt demands (`RULES_LOADED` + absolute path + real HEAD +
  sections loaded). Unreadable/contradicted → stop with the prompt's BLOCKED token
  (usually `BLOCKED_RULES`); never dispatch workers based on remembered rules.

## Sprint-open preflight (opening a NEW sprint, before its Wave-1 dispatch)

Per-turn baseline (rules load → git status) is not enough when unlocking a whole sprint:

1. Re-discover, never copy: the prompt states "observed HEAD / dirty count", but run
   `git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git status --porcelain | wc -l`
   fresh and pin THOSE values. Wrong branch → stop BLOCKED_PREFLIGHT; never checkout.
   Run these INSIDE the integration worktree (cd first): `git -C <MAIN-tree>` can fail
   with "fatal: not a git repository" even though MAIN visibly has a .git entry — don't
   debug MAIN's git plumbing mid-preflight; all baseline commands work from the worktree cwd.
2. Model-route probe: `curl -s <provider-base>/v1/models` must literally list the required
   model id (e.g. `"alpha"`) before any dispatch; missing → BLOCKED_MODEL_ROUTE.
3. Prior-lane liveness sweep: `tasklist //FI "IMAGENAME eq hermes.exe"` + python process
   count + `netstat -ano | grep LISTENING` on dev ports — a still-running old-sprint lane
   invalidates the dirty-tree baseline and risks two owners on one task. Stick to NON-interactive
   probes (tasklist, log mtime/size, grep markers inside dispatch logs); PowerShell CIM/WMI
   process queries can trip interactive-consent blocks in unattended sessions — if a command comes
   back consent-BLOCKED, do NOT rephrase or retry it, switch straight to read-only equivalents.
4. Protected hashes at REAL paths: planning docs can cite stale paths (a WRITESET_MATRIX
   said `data/channels.json`; reality was worktree-root `channels.json`, while MAIN kept
   `data/channels.json` + `data/motionforge.db`). Locate with find, sha256sum each, and
   ALSO baseline every cross-task intersection file (models.py, app.py, api.ts,
   job_service.py…) — correction-attribution disputes are settled by dispatch-time hashes.
5. Env/migration anchors: `MOTIONFORGE_DATABASE_URL` must be UNSET; `alembic heads` exactly
   one head, recorded as down_revision anchor for the sole-migration-owner decision.
6. Coordination files BEFORE dispatch: sprint CONTRACT (DAG + frozen decisions),
   SESSION_REGISTRY seeded with ALL task rows upfront (future ones BLOCKED_DEPENDENCY, only
   Wave 1 RUNNING), REPORT skeleton; the baseline-hash table lives inside the registry.
   Afterwards these are append-only and edited only between writer sessions.
7. Dispatch binary: resolve hermes.exe once (`where.exe hermes`; here
   `C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe`), quote the
   full path in dispatch lines, and sanity-check with `--help` — startup may print
   venv-health warnings that do not by themselves block CLI usage.
8. Conflict precedence: planning package vs canonical rules vs current user prompt —
   current prompt + canonical rules win WITHOUT stopping (e.g. a stale "stop after 3
   retries" rule is superseded by wait-5-minutes → resume-same-session/same-model loop,
   unlimited cycles for transient connection errors). Emit BLOCKED_* only for genuinely
   unresolvable contradictions.

## Correction routing = resume the owner session

- Findings map 1:1 to owner worker sessions. Dispatch pattern:
  `PROMPT=$(cat <temp>/xxx_prompt.txt) && hermes chat --resume <sid> --provider <p> --model <m> -q "$PROMPT" --yolo --pass-session-id --max-turns N --source tool > <temp>/xxx_dispatch.log 2>&1`
  run with background=true + notify_on_complete=true; write the prompt file first so
  quoting is safe. Log EXIT=$? into the log for exit-code forensics.
- Never create replacement sessions for an existing task; never change a live session's
  provider/model/reasoning/fallback (route mismatch = stop with BLOCKED_MODEL_ROUTE).
  New task = new session; correction/retry/bonus tests = resume the old one.
- Manager NEVER edits production code/tests/migrations/UI/config. Route defects back to
  the owning session with a minimal self-contained prompt: finding + file:line + exact
  repro + fix constraints (allowlist) + required re-verification commands +
  "append LOG entry". Keep correction prompts small and single-purpose — they complete
  in minutes instead of tens of minutes.

### Resuming LARGE owner sessions (correction rounds, context >~150k tokens)

Observed on S13-P00D-C1 (2026-08-23): resuming a synthesis owner carrying ~190k tokens
hits a `📦 Preflight compression … may take a moment` phase that runs for minutes and can
kill the run outright (one segfault EXIT=139 mid-`write_file`, one silent death DURING
compression with the log frozen at the compression banner). Protocol that worked:

1. Transient crash classes (segfault 139 / silent death in compression) are treated like
   connection errors: report immediately, mark RUNNING_RETRY_WAIT, wait ≥5 min, resume the
   SAME session/provider/model — unlimited cycles. Hermes persists session history to disk,
   so the owner stays recoverable after any crash; never declare context-loss without evidence.
2. Expect PARTIAL writes from the crashed round (2 of 9 deliverables were already rewritten).
   The continuation prompt must open with "re-read current file states FIRST, finish the
   missing findings, do NOT redo what is already correctly done".
3. NEVER wrap `sleep N && hermes chat --resume …` in ONE foreground terminal call — the
   shell timeout kills the parent while the hermes child SURVIVES as an orphan still
   appending to its log. You lose the `EXIT=$?` marker append AND risk double-dispatching
   (two owners on one task). Dispatches are always background=true + notify_on_complete=true;
   after any timeout, audit orphan liveness (process table + log growth) BEFORE deciding to
   re-resume. An orphan that keeps writing is still the live owner — let it finish, don't race it.
4. Keep continuation prompts SHORT on resume: the full correction text already lives in the
   session history from the original round; reference findings by ID (F1..Fn) instead of
   re-pasting them. Long re-paste + huge history is exactly what pushes into compression.
5. Independently verify the worker's own "sweep clean" claims, then CLASSIFY leftover grep
   hits: prohibition notes ("NOT alembic/versions/**", "NEVER hard-code `<rev-id>`",
   "no qa_stub under app/**") are COMPLIANT; the same strings inside active/stale
   instructions are not. Worker self-reports drift — grep counts came back non-zero twice
   and both times were prohibition phrasing, but that had to be confirmed by reading the lines.
6. Correction-round hash gate: `sha256sum -c <baseline.txt>` → the FAILED set must equal
   EXACTLY the intentionally-edited file set (all 9 synthesis files FAILED, zero lane-a/b/c
   failures = pass). Any FAILED line outside the expected set = scope violation or a
   foreign-lane edit to attribute — settle it with mtime+topic plus "does the worker's
   dispatch log mention that filename AT ALL?" (zero mentions ⇒ not your worker).
7. Dirty-count delta during a correction (266→270 here) is attributed, not assumed:
   filter `git status --porcelain` minus your run dir, match each path to a live foreign
   lane (S09/S11 writers were up at the time), and cross-check mtimes vs your dispatch window.

### Correction-round series on ONE owner (C1→C2→C3…, S13-P00D 2026-08-23)

When a verdict cycle repeats (CHANGES_REQUESTED → resume → verify → next verdict), each
round adds structure on top of the base resume protocol:

1. **Per-round hash baseline**, named `Cx_hash_baseline.txt` in manager/, captured BEFORE
   that round's resume. Round gate = `sha256sum -c`: FAILED set must equal exactly the
   intentionally-edited set (e.g. all 9 synthesis files), zero failures anywhere else.
   One shared baseline across rounds makes later verification ambiguous — snapshot fresh.
2. **DO-NOT-REGRESS list**: every new prompt opens with the prior round's verified
   findings restated as invariants ("T04B owns only V09..V16; T04C V13/V15; F-9 stands;
   zero-network binding") plus explicit regression grep checks in the acceptance section.
   By C3 the manager verifies BOTH new findings AND old ones — regression cost exceeds
   fix cost once a package reaches ~9 interlinked documents.
3. **Frozen-decision IDs propagate**: rulings become numbered facts (F-9, F-10…) that
   must appear consistently across all deliverables. Verify with `grep -c 'F-10'` per
   file (expect ≥1 everywhere relevant), zero `OPEN` residue for the retired decision,
   and distinguish legitimate history rows ("was D4-x") from stale operative references
   (a resolution still citing the dead ID).
4. **Manager keeps its own append-only `manager/MANAGER_LOG.md`**: one timestamped line
   per event — rules-load confirmation, preflight numbers, per-finding verification
   evidence with actual grep counts/hash outputs, terminal state. Prompts increasingly
   demand this artifact; it is also what lets the NEXT round's prompt cite prior proof
   without re-deriving it.
5. **Temp prompt files are cleaned up after verified submit** (`rm -f <temp>/cx_prompt.txt`)
   — hygiene, and prevents a stale prompt being accidentally reused for the wrong round.
6. **Post-compaction resumes shrink**: after C1's crash+compaction the same session
   resumed at 48 messages (from 77); a later round hit a FRESH 229k-token compaction and
   survived it fine under background dispatch. So: the compression banner is scary only
   in foreground; expect it on every large resume, audit only if log growth stops ≥8 min,
   and never treat "compacting…" as death while the wrapper lives.
7. **HEAD can move mid-correction-series from EXTERNAL snapshots** (C5, 2026-08-23):
   between two resume attempts, a user/Codex-side `chore(snapshot)` commit landed
   (a43b20d → ee10e55, 508 files) absorbing the whole 283-path dirty tree (porcelain → 4).
   Attribution protocol: check commit timestamp vs YOUR attempt death/start times, grep the
   commit stat for your run-dir paths (zero = not yours), grep your dispatch logs for git
   commands (zero = your worker never ran git), then record it as foreign-owned and do NOT
   revert. All protective hash gates still evaluate under the new HEAD — re-run them there
   rather than blocking on "HEAD changed".
8. **Backend restart mid-round kills worker + manager registry together**: see
   `references/manager-liveness-and-worker-process-audit.md` §third-death-mode for the full
   S13-P00-C5 pattern (poll()=not_found on a fresh proc id, multi-attempt EXIT_R<N> markers
   in one log, cross-attempt partial-write coverage verified at final gate only).

## Serial-DAG speed levers (when the audit forces ONE production writer)

When PARALLEL_WAVES-style audits reject every production pair (overlapping write-sets or
dependency chains), do NOT fabricate parallel writers — instead maximize legal throughput:

1. Read-only reviewer lanes (RO1 domain/persistence/math, RO2 UI/e2e) run CONCURRENTLY
   with the active writer; their write-set is only output/<sprint>-readonly-review/<run>/.
   Dispatch RO1 as soon as the first writer submits code — early findings shrink later
   correction rounds. Route every finding through the manager back to the owning writer
   session (RO lanes never implement).
2. Read-only recon for FUTURE tasks is safe while a writer runs: verify infra the next
   tasks depend on (ffmpeg discovery, timebase API shape, playwright config pattern,
   frontend app-router layout) without touching production files.
3. Task-focused test runs may parallelize ONLY with isolated DB/temp/basetemp/ports/output;
   global gates stay behind the writer-stopped mutex.

## Mid-sprint baseline drift from parallel lanes (R6 S11 2026-08-23)

Lanes running concurrently WILL move your sprint's baseline mid-wave. Two observed shapes,
both resolved WITHOUT blocking:

1. **Alembic head moved under you** (`b2c3d4e5f6a7b` → `c9d0e1f2a3b4` between rounds):
   `alembic history | head -3` — the chain entry's message names the owning sprint
   ("S09-T01: … SOLE S09 migration"). If it's another lane's sanctioned sole migration
   (your sprint has zero migrations of its own), do NOT block or revert: record
   foreign-lane attribution in the handoff (a dedicated "attribution ngoài lane"
   section), re-run `PRAGMA foreign_key_check` against the NEW head, and state in the
   handoff which head your evidence used. Note `ls alembic/versions/` can fail (layout
   differs per repo) — `alembic history` is the reliable discovery path.
2. **Protected-file mtime moves mid-wave** (models.py touched at 00:10 by a foreign
   lane): worker disclosures + your own before/after hash table settle attribution.
   Verify YOUR lanes' zero-write with grep over their dispatch logs, then document the
   foreign edit in the handoff — never revert/clean it.

Companion discipline: **pre-declare known in-flight foreign changes inside RO/writer
prompts** ("models.py diff là pre-existing của lane khác — bỏ qua"; "lane X đang chạy
song song trên file Y — KHÔNG report việc đó thành finding mới"). Reviewers dispatched
this way spent zero turns misattributing the concurrent wave (both R6 RO lanes came
back P0/P1-none) — without it, expect a stale-hash informational finding like
"engine hash moved DURING my review window".

## Expect residual errors after every writer wave

Writers run their gates focused-only, so each global pass by the manager routinely
catches leftovers the writers never saw:
- eslint `no-explicit-any` on newly added test code,
- TS18047 "possibly null" after a fix removes/renames a variable,
- ruff I001 un-sorted import blocks inside new test functions,
- type declarations not updated when mock bodies gain fields.

Budget 1–2 extra resume-fix rounds per correction wave before global green. Verify
worker evidence on disk too: at least once a worker reported "SMOKE PASS" while its own
smoke.log contained a traceback — coverage actually lived in pytest, and the manager's
own independent re-run was what made it provable.

## Global gates: mutex + isolation

- Run repo-wide gates ONLY when ALL writers have stopped (mutex), at a consistent
  checkpoint. Parallel-safe while writers run: read-only audits with isolated temp DB,
  temp root, basetemp, ports, output dirs (`env -u MOTIONFORGE_DATABASE_URL`,
  `-p no:cacheprovider`, `--basetemp=<unique>`).
- Standard battery: full S07-style sprint suite; focused per-owner suites; regression
  cluster (adjacent sprints); ruff app+tests; mypy; tsc --noEmit (plain flag;
  `--incremental=false` is NOT a valid tsc option); eslint; production build; alembic
  single head + migration round-trip (upgrade→downgrade→upgrade) + PRAGMA
  foreign_key_check on a THROWAWAY sqlite db (mkdir -p the parent first or sqlite fails
  with "unable to open database file"); git diff --check; protected-data hashes/sizes;
  netstat for orphan listeners after playwright runs.
- Save raw logs under output/<sprint>-final/<timestamp>/ or
  output/<sprint>-correction/<timestamp>/ — never just cite counts.

## Dependency DAG across owners

- If task B's e2e depends on task A's production fix: B's first run legitimately fails —
  record it as evidence (BLOCKED_DEPENDENCY_<A>), then resume B's owner AFTER A lands
  for the re-run. Don't collapse into one combined dispatch; don't let B weaken its
  assertions to pass early; keep B's primary flow through the real production UI
  (no route.fulfill / direct API calls standing in for the user path).
- Writers on disjoint write sets CAN run in parallel (separate ports/backends/temp dirs),
  but their e2e suites that share ports must run sequentially afterwards.

## Independent verification

- stat mtimes of forbidden files (models.py, migrations/) before/after waves — proves
  nobody touched them even if git status is noisy from other lanes.
- Grep actual assertions (exact values, not tautologies); check regression evidence is
  fail-before/pass-after, not pass-only.
- Re-run suites yourself; never trust worker-reported counts alone.
- **Verify the FIX SITE, not just green counts** (R6 S11): for each Codex finding, read
  the cited file:line region yourself and confirm the fix mechanism matches the finding's
  expected shape — e.g. F1 demanded bounded `-select_streams v:0/a:0` probing, so grep
  confirmed `_probe_one_stream` + per-query guard semantics rather than a raised cap; F2
  demanded purge-before-raise, so `sed -n` around handler:657 showed `_purge_run_staging`
  preceding the CANCELLED raise. Green focused suites alone would not distinguish a real
  fix from a test-only appeasement. Also confirm new regressions exist by name+line
  (`grep -n "def test_r6_f1…"`), since workers sometimes cite tests that landed in an
  earlier round.
- **Re-pin hashes after every wave that touched the anchor files**: engine/handler/test
  sha256s cited in handoffs go stale within hours when lanes overlap (RO2 flagged the
  stale engine hash as its main informational finding). Re-hash at closeout and update
  registry+handoff together.

## Verifying READ-ONLY audit lanes (docs-only workers)

Docs audits have no test suite to re-run, so manager verification = evidence forensics:

1. Completeness: every acceptance-listed deliverable exists (`wc -c` each; ~5–16KB per
   substantive doc is normal; near-zero = stub) + LOG.md + REPORT.md ending exactly
   `STATUS: TASK_SUBMITTED`.
2. Citation spot-check (pick 3–5 load-bearing claims): grep the cited symbol/constant at
   the cited file yourself. If a constant isn't where the worker said, grep repo-wide
   BEFORE crying fabrication — observed case: worker cited `DEFAULT_FENCE_GRACE_SECONDS=90`
   under durable_worker.py but truth lived in job_reconciler.py:99 (value correct) → record
   as P2 citation-precision nit, not a fabricated finding. Fabrication = value wrong or
   symbol absent everywhere.
3. Classification vocabulary present: EXISTING/PROPOSED/UNKNOWN rows exist and UNKNOWN is
   non-empty (a docs audit claiming zero unknowns is suspicious).
4. Write-scope audit: `grep -aoE '(write_file|>>|tee |mkdir -p|patch\()' manager/dispatch-X.log`
   then confirm every created path lands inside the lane dir (`find <run-dir> -type f`);
   cross-check the worker's own Self-Audit path list against reality.
5. Attribution when protected files moved DURING your wave: match mtime+topic, not just
   mtime — reskin_config.* + S09 registry = S09 lane; original_audio_remux.py + T01B
   REPORT = S11-T01B lane. Your lanes are clean when ALL new files under the run dir
   belong to your lane dirs and no production file matches any lane's subject matter.

### Liveness semantics for reasoning-max workers

A frozen dispatch log is NOT a dead worker. Audit order: (a) `process(action='poll')` /
`process(action='list')` — wrapper alive? (b) netstat the PID for sockets; (c) only if the
process is gone do you enter the retry/resume cycle. Observed: alpha@custom stalled 22 min
(02:12→02:34) mid-read with the process healthy, then resumed normally — long LLM-latency
gaps self-heal; waiting beats intervening. Keep the 8-min audit as an AUDIT trigger, not a
retry trigger.

Manager-side terminal discipline: compound verification one-liners with nested `$()`
inside for-loops can hit the unconditional parser blocklist even though they're read-only
("command parser limit or malformed executable payload") — that block is not consent-related
and rephrasing the SAME shape is futile; split into two plain commands (`wc -c` batch, then
a separate grep pass). Also seen: a WORKER hitting its own hardline guard once and
self-correcting with a simpler command within seconds — one blocked command in a dispatch
log is noise, not failure, as long as size keeps growing afterwards.

## Reporting

- Append-only, timestamped entries (+07 local AND Z) into sprint report + per-session
  LOG/REPORT. History is never rewritten. Terminal-state vocabulary comes from the rules
  doc; manager never writes APPROVED/CLOSED — stop at the review boundary and hand off
  to the external reviewer.

## Background dispatch hygiene

- Every background process: notify_on_complete=true; poll/wait rather than sleep-blind.
- **`process(action='wait')` results are clamped to ~180s regardless of the timeout you
  pass** (a 240s request comes back with "clamped to configured limit"). Long writer
  runs therefore need MANY sequential wait calls — that is normal, not a tool fault.
  Two failure modes seen in one session: (a) identical consecutive wait outputs get
  deduped as "[Duplicate tool output]" — interleave a cheap independent probe (registry
  msg-count via state.db, log tail) both for liveness and to make each turn distinct;
  (b) an empty assistant turn after waits — just continue the loop next turn.
- **Writer self-re-verification loops**: near submit time, workers may re-run their
  gates 2–4 extra times because the harness flags "verification stale" after they edit
  LOG/REPORT/evidence files. Expect EXIT to slip 5–15 min past the first TASK_SUBMITTED
  line in the log; treat repeated identical md5 + repeated green counts as confirmation,
  not as a hang.
- `mkdir -p` the dispatch-log directory BEFORE launching: a `> output/<run>/manager/dispatch-x.log`
  redirect into a missing directory kills the wrapper instantly (`bash: ...: No such file or
  directory`, exit 1) and hermes NEVER starts — zero repo side effects, but the slot burns minutes.
  After EVERY dispatch, stat the log within ~90s to prove it exists and is growing; if missing,
  check `process(action='list')` for instant-exit wrappers, then re-dispatch (safe: nothing ran).
- Late completion notifications for already-processed runs get a ONE-LINE ack ("already
  processed") — do not redo work. Unknown exit codes are diagnosed from their logs
  before being declared stale (an old `rm -rf` failing with "Device or resource busy"
  may simply mean a since-dead process held the file; retry the rm once to confirm).
- Registry bookkeeping at dispatch time: record the Hermes process id (proc_*) in the
  session registry IMMEDIATELY when the background dispatch starts — the hermes chat
  session id only becomes visible inside the dispatch log at exit, so proc-id is the
  only live handle during the run (patch the registry later once the real sid lands).

## Gating a wave on another lane's exit (wave-0)

Prompts often gate Wave-0 on ANOTHER sprint's worker stopping (e.g. S13-P00 opens only after the
legacy-contract S09-T01 owner exits). Never kill or message that lane; prove exit with converging
READ-ONLY signals:
1. Log-growth watchdog: loop `sleep 60; cur=$(stat -c %s LOG)`; two consecutive equal sizes ≈ stable —
   drop a marker file with timestamp/size/log-tail on stability.
2. No live owner: `tasklist //FI "IMAGENAME eq hermes.exe"` lists nothing.
3. Terminal markers inside the log: TASK_SUBMITTED / SUBMITTED / BLOCKED* / EXIT=.
Declare wave-open only after ALL three. Attribution caution: a writer can still land production edits
moments before exiting (observed 2026-08-23: stopped S09-T01 had added ApplyCheckpoint/ReskinConfig
rows to models.py). Baseline-hash the touched files and record the diff as FOREIGN-LANE ATTRIBUTION
for Codex — never revert or clean it yourself.

## Supersede / scope-flip mid-sprint (S09 2026-08-22→23)

When a Codex verdict supersedes an in-flight sprint contract (e.g. contract omitted a mandated
S09-T00 phase or a MAIN-roadmap overlay):

1. **Safe-stop the live writer FIRST; dispatch nothing until it exits.** Try
   `process(action='submit')` into the owning wrapper session — but non-interactive `-q`
   dispatches have NO stdin channel ("Process stdin not available"), so expect this to fail.
   Fall back to poll-until-natural-exit; NEVER kill. Log freeze + missing REPORT.md = died
   mid-task, which still counts as exited for gating purposes once hashes stabilize.
2. **Preserve partial writes for attribution.** Re-hash intersection files (models.py,
   app.py, api.ts, job_service.py, channels.json) before/after; keep the dead worker's
   edits untouched in the tree for Codex to attribute. Never reset/restore/delete.
3. **Audit scope drift with git + mtime evidence**: `git status --porcelain | wc -l` delta
   vs baseline; split new mtimes per lane so you don't blame the wrong lane. On large dirty
   trees, repo-wide `find . -type f -newermt …` can blow the 180s foreground timeout —
   filter the ALREADY-LISTED porcelain paths instead (`git status --porcelain | grep -v
   '^.. output/<run-dir>'`, then targeted `stat -c '%y %n'` per suspect path) and confirm
   foreign ownership by grepping YOUR worker logs for the filename (zero mentions ⇒ not yours).
   Note porcelain lists cumulative-dirty state, not just new edits — an old foreign edit
   (reskin_config.py, mtime 02:44) still appears at hour 13; mtime + topic + log-mention
   are what date it.
4. Open only when ALL hold: owner exited + snapshot stable across several minutes +
   post-drift hashes pinned. Then append registry heartbeat rows (supersede event, safe-stop
   failure mode, drift audit result, resource headroom) and dispatch the replacement wave.
6. Registry must record the REAL hermes session id (`grep -aoE "2026[0-9]{4}_[0-9]{6}_[0-9a-f]+"
   dispatch.log` or from the worker's own LOG.md) — wrapper proc id ≠ session id.
7. Reusable dispatch-prompt skeletons for read-only audit/synthesis lanes (guard block,
   allowlist/forbidden, required-reading, outcome/deliverable shape, STATUS tail):
   `templates/readonly-audit-lane-prompt.txt` — copy+fill instead of hand-writing each wave.
6. Replacement lanes are new Task IDs (T00A/B/C/D) → NEW sessions each; write their prompts
   into the run dir BEFORE the gate opens so dispatch is immediate at wave-open. Read-only
   audit lanes (own output/<run>/lane-x/** only) can run 3-wide alongside other sprints'
   active writers given RAM/CPU headroom (verify free RAM first).

## User-facing progress reports

- The user expects progress reports as a table: completed steps + real evidence per step,
  then a per-task ETA table derived from THIS sprint's actual measured velocity (prior
  sprint task durations are the calibration source), not generic guesses.
- Ask once whether they want heartbeat pings on every milestone or only on
  significant events (task verified / blocker); default to significant-events-only.
- If the user asks mid-run "bao giờ xong / when will this be done", answer IMMEDIATELY in that
  turn — elapsed time, current phase per lane, concrete ETA from observed velocity — then keep
  working. Never defer an ETA question to the next heartbeat. When they then say "ok áp dụng"
  to a proposed speed-up (early RO lanes, read-only recon), EXECUTE it that turn: pre-write the
  lane prompts during the wait so dispatch happens within seconds of the gate opening.
- Multi-correction sprints accumulate a **verdict→fix ledger** the user can read at a glance:
  report each round as a table `finding → fix → manager's own verification evidence` (actual
  grep counts, hash-check results, file:line), plus a regression section proving prior-round
  fixes survived. Vietnamese-language reports, evidence-first, no apology padding — state what
  was checked and what it returned.

## Closeout handoff updates after each correction round

The handoff doc (e.g. `docs/pm/sprints/<S>-T01-CODEX_HANDOFF.md`) is a LIVING closeout —
each round, patch ALL of these in one pass, not just the header date:

1. Header date/status line → round number + finding IDs.
2. §1 task table rows → append the new fix + regression names + correction count
   (corrections accumulate: "#5 R6-F1+F3", not a replacement of #4).
3. §2 verification bullets → NEW dated bullet for the round with file:line evidence of
   each fix mechanism, focused counts, and RO-lane verdicts; update the standing bullets
   (focused counts, full-suite count, hash pins) to current values.
4. §5 Codex section → findings→fix mapping line so the reviewer can navigate straight
   from their own verdict text to the fix; add reviewer session ids.
5. New §7-style attribution block whenever foreign lanes moved shared files or the
   alembic head mid-sprint.

Test-count baselines shift every round (52→56→58→64 across rounds here) — always keep
the frozen-sub-suite number vs full-suite number distinction explicit in §2/§5 so Codex
never reads them as a contradiction.
