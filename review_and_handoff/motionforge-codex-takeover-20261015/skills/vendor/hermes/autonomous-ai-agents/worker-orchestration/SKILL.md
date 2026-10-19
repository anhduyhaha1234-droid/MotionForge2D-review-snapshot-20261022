---
name: worker-orchestration
description: "Use when running worker task queues with manager gates."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [orchestration, workers, sprints, verification, task-queue]
    related_skills: [motionforge-autopilot, terminal-engineering-discipline]
---

# Worker Orchestration — Manager Loop for Task Queues

Orchestrating a queue of autonomous worker sessions (e.g. `hermes chat` CLI
workers) through a sprint/batch, with a manager verification gate between
tasks. Proven on MotionForge2D Sprint S05 (T03→T06 + exit, 2026-08-05) and
S06 correction rounds.

## The loop (per task)

1. **Packet first**: TASK.md / START_PROMPT.md / LOG.md / REPORT.md /
   PM_REVIEW.md with required reading, allowed write scope, forbidden scope,
   binary acceptance criteria, targeted verification list, fresh baseline
   requirement.
2. **Fresh session per task**: one worker = one NEW compact session. Never
   resume old sessions with large context (model drift, stale state). Record
   session IDs in a tracking file (`output/SPRINT_S0X_SESSIONS_TRACKING.md`)
   so the reviewer (Codex) can open each task's session/log independently.
3. **Launcher script** (`templates/run-task-fresh.ps1`): PowerShell wrapper
   with the HARD WORKTREE GUARD pasted into the prompt + `Tee-Object` log.
   Launch via `terminal(background=true, notify_on_complete=true)`.
4. **Log visibility for the user**: sync the worker log into a folder the
   user watches on the desktop (e.g. `<project>/output/hermes-task-logs/`)
   with a UTF-8 LIVE tail file, refreshed every ~10s by a watcher
   (`templates/watch-task-log.sh`), and `open_preview` the LIVE file. Worker
   logs are UTF-16LE on Windows — convert with `iconv -f UTF-16LE -t UTF-8`.
5. **Manager verification after exit** — NEVER trust worker self-report:
   - grep REPORT.md = SUBMITTED (not APPROVED — worker must not self-approve)
   - MAIN/baseline tree unchanged (`git status --short | wc -l` before launch,
     re-check 60s after launch AND after exit; any delta = incident)
   - run the task's own tests + ALL prior-task regressions INDEPENDENTLY
   - parse the fresh baseline `summary.json` (overall PASS + all gates exit 0)
   - write `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` before opening next task
6. **Gate before next task**: worker exited + REPORT=SUBMITTED + manager
   verified + recorded. Only then create the next packet and launch.
7. **After final task**: stop all writers, run fresh baseline, write
   `SPRINT_EXIT_REPORT.md`, tell the user to call the external reviewer.

## Hard worktree guard (paste into every worker prompt)

```
Before ANY write, run and verify:
1. `pwd` -> must be <EXPECTED_ROOT>
2. `git rev-parse --show-toplevel` -> must be <EXPECTED_ROOT>
3. `git status --short`
If pwd is wrong, cd and re-verify. If toplevel differs, write NOTHING,
report BLOCKED: WRONG_WORKTREE, exit immediately.
```

## Pitfalls (all verified)

1. **Wrong-tree writes**: `hermes chat` CLI launched from a PowerShell script
   does NOT reliably inherit `Set-Location` when the Hermes desktop daemon is
   running — worker may execute with the daemon's cwd (often MAIN repo). The
   hard guard in the prompt + manager baseline checks are the defense.
2. **Iteration budget cut**: `--max-turns N` can end a worker mid-final-sweep
   ("Iteration budget reached (N/N) — response may be incomplete"). Work may
   still be COMPLETE (baseline 7/7 finished before the cut). Verify real
   artifacts (summary.json, REPORT, independent reruns) before resuming.
   S12-C1 addendum (2026-09-08): a NEWER failure mode is the
   ack-without-action exit — the worker replies a 1-line ack
   ("Committing the wiring files now.", "SHA") with exit 0 but runs ZERO
   commands (worktree tip + porcelain unchanged). Triage: after ANY ack-only
   exit, verify `git rev-parse HEAD` + `git status` yourself BEFORE the next
   dispatch; then send a COMMIT-NOW micro-prompt (single `git add` +
   `git commit` + `git status`, no gates, no prose) instead of repeating the
   full gate prompt.
3. **MSYS `--basetemp` trap**: passing `--basetemp=/c/Users/...` to pytest
   makes Python resolve `C:\\c\\Users\\...` → mass `ERROR` entries at
   `os.mkdir` in `pathlib.py` (looks like broken code; it's a path bug). Use
   Windows-native `--basetemp=C:/Users/...`.
   S12-C1 addendum (2026-09-08): the `$TEMP` variable ITSELF can be hijacked —
   a foreign session's exports had redirected `$TEMP` into another lane's
   evidence dir, so `--basetemp=$TEMP/...` failed the same way (18 ERRORs on
   healthy code, misread as broken). Always `echo $TEMP` first; on any
   foreign-looking value pass an explicit short Windows-native path
   (`C:/Users/Admin/AppData/Local/Temp/<tag>`) instead of `$TEMP`.
4. **Parallel-pytest race**: running pytest in the same worktree while a
   worker is active races `.pytest_cache` and in-flight test files. Use
   `-p no:cacheprovider` (+ isolated `--basetemp`) for manager checks during
   a run; full independent runs after worker exit.
5. **E2E hang on stale dev server**: Playwright `page.goto` hangs against a
   Next dev server started by an earlier session. Kill the stale server, start
   fresh (different port + `.env.local` API URL), rerun.
6. **Fast-job screenshot trap**: with a 4s source video the "progress"
   screenshot equals "completed" (identical hashes). Use a ~30s source to
   capture a genuine RUNNING state.
7. **Scope creep audit mid-run**: for UI tasks, `app/services|workflow|api`
   modifications may be pre-existing from earlier tasks — check mtimes against
   the task's start time before accusing the worker. `frontend/.env.local`
   changes are acceptable dev config.
8. **MSYS `kill` silently fails on Windows bash/watcher processes (verified
   2026-08-19)**: `kill <pid>` from git-bash on a stale `bash`/watcher process
   returns "already gone" even while the Windows process is still alive
   (`wmic` still lists it). Neither `kill` nor `kill -9` reaches it. Use
   `MSYS_NO_PATHCONV=1 taskkill /PID <pid> /F` (the `MSYS_NO_PATHCONV=1`
   prevents `/PID` from being mangled to a path), then RE-VERIFY with
   `wmic process where "name like '%bash%'" get ProcessId,CommandLine | grep
   <watch-tag>` — the only remaining matches must be your own wrapper's
   command line (it contains the grep tag), not the watcher.
9. **`process('wait')` is clamped to ~180s even when you request more**
   ("Requested wait of 540s was clamped to configured limit of 180s");
   foreground `sleep 300` likewise times out at ~180s. Bounded monitoring
   loops: call `process(action='wait', timeout=180)` repeatedly and check the
   writer log mtime/size between waits — not one long block.
10. **Session_search before re-creating a task packet (verified 2026-08-19)**:
    before materializing a fresh `docs/pm/sessions/<TASK>/` packet or
    launching a writer for a Task ID, run `session_search(query="<Task-ID>")`
    — a prior manager attempt may have already received the same handoff
    (e.g. `20260819_142623_c80e67` sat with only the prompt, zero actions).
    This prevents double materializing packets or double-launching a second
    writer on the same task.
11. **Attributing status deltas during a run**: after launch, MAIN/worktree
    `git status --short | wc -l` can grow by files YOU created (e.g. the
    `scripts/watch-<task>.sh` watcher you add to MAIN) — the delta is not
    writer drift. Verify with `git status --short scripts/` / identify the
    new path before treating a delta as an incident. Writer-only writes stay
    inside the worktree; a change in MAIN docs/pm/* is the suspicious one.
12. **Packet allowlist must cover the AC-driven write surface (verified
    S08-A01 2026-08-19)**: authoring TASK.md, map EACH binary acceptance
    criterion to the exact file(s) it forces to change and list them ALL.
    S08-A01's backend allowlist listed `services/object_grouping.py` +
    `services/object_correction.py`, but AC4/AC5 (grouping kind-homogeneity,
    correction role_kind) architecturally REQUIRE
    `persistence/object_grouping.py` (merge guard), `api/routes/object_grouping.py`
    (policy pass-through), `schemas/object_correction.py` (role_kind pattern).
    The writer, faced with BLOCK-or-deviate, silently deviated. When this
    happens: verify the out-of-allowlist changes are minimal + AC-required,
    record as a NON-BLOCKING deviation escalated to the external reviewer
    (Codex), and do NOT auto-expand the scope yourself. Prevention beats
    escalation: audit AC→file coverage when writing the packet.
13. **Manager migration round-trip verification has two silent-false traps**
    (verified S08-A01 2026-08-19): (a) a checksum of `e3b0c44298fc1c149afbf4c8
    996fb92427ae41e4649b934ca495991b7852b855` = SHA-256 of EMPTY input — if
    your baseline "row checksum" equals it, the fixture seed inserted ZERO
    rows and the preservation test is vacuous, yet the script may still print
    OK/True; (b) seeding against guessed columns fails silently (your INSERT
    errors are swallowed, rows stay 0). Before trusting any round-trip: print
    per-table row counts after seeding, and introspect real columns first
    with `PRAGMA table_info(<table>)` (e.g. `video_item` has no `source_kind`;
    `object_role_artifact` has no `sha256`/`size_bytes`) instead of assuming
    the ORM shape. Only a NON-empty checksum that equals across
    upgrade→downgrade→upgrade proves row preservation. Two more traps hit on
    S08-A01-C1: (c) when driving alembic via `subprocess.run`, pass the
    sub-command and revision as SEPARATE argv elements — `["python","-m",
    "alembic","upgrade","head"]` — never one joined string `"upgrade head"`
    (the joined form exits rc=2 with nothing upgraded, and the failure is
    silent if you only print `.returncode`); (d) seed rows must satisfy the
    table's CHECK constraints or `INSERT OR IGNORE` will silently drop the
    row and leave broken FKs (`object_role` → missing `video_item` when
    status `'ready'` violates `ck_video_item_status`; use a valid enum value
    like `'imported'`). A lingering `foreign_key_check` row after the seed =
    your seed is wrong, not the migration.
14. **pytest suites >180s must run `terminal(background=true,
    notify_on_complete=true)`** — a foreground call hard-clamps at 180s and
    kills a suite that legitimately needs 200–280s (S08 full set 214s,
    S05+S06+S01-S03 20-file set 272s). The `process('wait')` clamp (pitfall
    9) still applies to the background session: poll the tail between waits.
15. **Writer dies mid-run on provider HTTP 502 → RESUME the exact stored
    session, never a second writer (S08-A01-C1, 2026-08-19).** A long
    `hermes chat --query` worker can die at ~56 min with `API call failed
    after 3 retries: HTTP 502 — fetch connect timeout` from the local custom
    provider endpoint (`127.0.0.1:<port>`), usually after it has done ONLY
    analysis (no file writes yet — verify with `find ... -newermt`).
    S12-C1 addendum (2026-09-08, transient stream failure): `API call failed
    after 3 retries: Codex Responses stream did not emit a terminal response`
    is the SAME class — hold `RUNNING_RETRY_WAIT`, wait the mandated 5 min,
    then resume the same session/scope/model (record the error timestamp from
    the evidence-log mtime so the retry demonstrably lands past the 5-min
    mark). Implementation note: `sleep 300` inside a
    `terminal(background=true)` command WORKS (unlike the ~180s foreground
    clamp in pitfall 9 — background sleeps are not clamped); chain as
    `sleep 300; hermes chat ... --resume <sid> ... | tee <evidence-log>` with
    `notify_on_complete=true` so the retry pings back instead of running
    silent. The
    session is NOT lost: the exit banner prints `Resume this session with:
    hermes --resume <SESSION_ID>`. Recovery: create a RESUME launcher (.ps1)
    with the SAME `--resume <SESSION_ID>` + a short "RESUME: continue from
    where you left off ... re-verify the hard guard ..." prompt, launch in
    background with notify. Do NOT open a fresh session for the same Task ID
    (Codex protocol: same Task ID must resume the stored session id). Before
    resuming, check whether a PM scope-decision was appended to the packet
    LOG.md mid-run — the resumed writer will read it and continue (see 17).
16. **Do NOT fan out read-only delegate lanes over a flaky provider while the
    writer runs (S08-A01-C1, 2026-08-19).** Dispatching `delegate_task`
    subagents (design/audit lanes B/C/D) in parallel with the writer on the
    SAME provider → every subagent died on HTTP 502 too, and even a
    re-dispatch batch died again (`status=interrupted`, transcripts show
    tool-calls but NO final analysis). When the provider shows one 502,
    STOP compounding: consolidate — run read-only lanes after the writer
    exits and the provider is idle, or serialize instead of launching
    parallelism that all shares the failing endpoint. Re-dispatching the
    the same work repeatedly is waste; gather the no-final-analysis transcripts
    and re-run once later. IMPORTANT CAVEAT (S07, 2026-08-21): this ban is about
    a FLAKY/failing provider. When the provider is healthy, read-only review/BA
    lanes MAY run in parallel with the production writer — the S07 authority
    explicitly required S07-RO1 (domain/persistence) + S07-RO2 (API/UI/test) +
    S11-T01-BA-PREFLIGHT alongside the T01 writer, and all four ran clean in
    parallel. They only write to `output/s07-readonly-review/<run>/` and
    `output/ba-parallel-assessment/s11-t01/<run>/` (never app/tests/migrations),
    so no file conflicts arise. Distinguish the two cases: parallel read-only
    lanes = safe when the endpoint is stable; parallel lanes that ALSO depend on
    the same flaky endpoint = still ban.
17. **PM scope-decision appended to LOG.md mid-run unblocks a writer that
    would otherwise STOP BLOCKED (S08-A01-C1).** When a writer needs exactly
    ONE file outside its allowlist (e.g. `app/persistence/object_correction.py`
    for a preview conflict path), it will correctly STOP BLOCKED per
    protocol. The PM can APPROVE the single-file expansion; the manager
    appends an official `## SCOPE DECISION (PM/official)` block to the packet
    LOG.md (append-only, NOT TASK.md/PM_REVIEW.md). A RESUME of the same
    session reads LOG.md, sees the decision, and continues implementing —
    no second BLOCKED round trip. The decision must name the exact file,
    the sole purpose (e.g. F2 preview validation), require read-only +
    zero-durable-mutation, and forbid touching unrelated behavior.
18. **Never trust a writer's claimed lint/quality counts — rerun the gate
    yourself and diff against the REPORT's claim (S08-A02-C2, 2026-08-20).**
    A Muse writer SUBMITTED with REPORT claiming "ruff 0", but an independent
    `python -m ruff check app tests` returned 121 errors — 90 in the new test
    file, 16 in production `structural_evidence.py`, 5 in routes, all inside
    the allowlist. Lint is the first thing a fast-terse model botches (E501
    line-too-long, E702, F401 unused imports, E402, I001). What saved the
    round: (a) run `ruff check app tests` yourself, never the writer's count;
    (b) bucket by file with `--output-format concise` + `awk -F: '{print $1}'`
    (plain `grep` for `app/`/`tests/` misses on Windows because paths use
    backslashes); (c) compare against a PRIOR baseline's Gate 3 lint result
    (034340/053350 = PASS) to prove the errors are NEW from this writer, not
    pre-existing; (d) classify recoverability — E501/E702 need manual
    wrapping, F401/I001 are auto-fixable (`ruff check --fix`, 7 of 121).
    Also: evidence files a REPORT references (e.g.
    `output/.../20260820_145200_writer/ruff.log`) may not actually exist —
    verify referenced log paths exist before accepting the REPORT. Corrective
    loop: launch a recovery writer (NEW session, same model, per isolated
    single-writer rule) to fix lint + re-verify REPORT, then manager re-check.
19. **The quality-baseline script's Gate 2 (full pytest) takes ~790–830s —**
    never launch it with a ≤180s timeout (S08-A02-C2, 2026-08-20).**
    `scripts/quality-baseline.ps1` Gate 2 runs the whole non-gpu/non-sam2
    suite and historically takes 791–829s (034340/053350 runs). A
    180s/60s-foreground invocation dies with `exit 124` (SIGTERM mid-run)
    and leaves `summary.json overall.status=RUNNING` with only Gate 1 PASS —
    that is a timeout artifact, NOT a test failure. Launch it with
    `terminal(background=true, notify_on_complete=true)` (or timeout ≥ 1200s)
    and poll `output/quality-baseline/<run>/summary.json` for
    RUNNING→PASS/FAIL instead of assuming a timeout = failure. If a baseline
    run is killed mid-Gate-2, restart it ONCE with the long timeout and record
    every attempt (writer reasoning gate expects 7/7 from a real completed Run
    ID — a killed or purely-interim run does not satisfy it).
20. **Two N-code writers + read-only lanes can run in PARALLEL only when the
    allowlists are provably disjoint; verify ownership by MTIME WINDOW after
    both exit (S08-A02-C5/C6 + T02-C1/C2, 2026-08-20/21).** Lane A touched
    `persistence/object_intelligence.py`+`structural_evidence.py`+c3-tests at
    23:11–23:19; Lane B touched `services/object_extraction.py`+its tests at
    23:27–23:35 — zero overlap. Audit recipe: after each writer exits, print
    `ls -la --time-style=full-iso <file>` for every allowlisted file and check
    the mtime falls in THAT lane's run window; a shared/untouched-by-this-run
    file (e.g. `models.py` mtime from the morning) proves no lane drifted into
    it. Also: a writer legitimately READS the other lane's file (`git show
    HEAD:...`, `head`, `git diff --stat`) to compare against baseline — reads
    are fine, only writes matter; don't flag a read. Finally, do NOT panic if
    a writer's log shows a forbidden-looking command (e.g. `git checkout HEAD
    -- tests/...`): on an UNTRACKED file that pathspec "did not match any
    file(s) known to git", so it fails harmlessly and cannot erase work —
    verify the file's line count/hash is intact before reacting.
21. **User got angry at perceiving the manager as "stopped" because a mid-turn
    out-of-band message INTERRUPTED the assistant turn and swallowed the
    drafted heartbeat text (2026-08-21).** When the user pings mid-run, the
    response-in-progress is truncated (`[This response was interrupted by a
    user correction.]`) and the heartbeat/status you were composing never
    lands — the background writer kept running the whole time, but the user
    only sees silence and assumes a stall. Default heartbeat for this user is
    now **every 10 minutes** (config: `liveness: heartbeat 10m`; user asked
    "muốn có heartbeat mặc định mỗi 10 phút nhé"). Rule: whenever a turn is
    interrupted or you're between long waits, STRUCTURE the next reply as an
    immediate short status (what ran / what's running / ETA / next) BEFORE
    continuing tool work; never wait for the user to ask "bao giờ xong".
    Also explain "interrupt" honestly: it's the chat cutting my mid-turn
    response, not the workers dying (verify with `process('list')`/process
    exit codes before claiming anything stopped).
22. **SQLite fixed-bind-parameter scalability — the JSON1 `json_each()` idiom
    (S08-A02-C5→C6, 2026-08-20).** Two-layer fix, both reproducible:
    (a) C5: per-stale-video `UNION ALL` via `literal_column(f"'{v}'")` breaks a
    SQLite 500-term compound-SELECT at 501 videos (`OperationalError: too many
    terms in compound SELECT`) — replace with ONE authoritative batch
    current-generation query in the repository + chunked `IN(...)` at
    `_SQLITE_MAX_PARAMS=900`. (b) C6: even chunked IN-list × N chunks yields an
    `or_(IN(c1),IN(c2)...)` whose TOTAL bind count grows with the set size —
    still not bounded. Final fix: bind the whole id-set as ONE JSON text param
    and filter with `video_item_id IN (SELECT value FROM json_each(:stale_json))`;
    final COUNT/page SELECT then has a FIXED param budget (base predicates +
    1 json + LIMIT/OFFSET), independent of video count. Capability-probe JSON1
    first (`SELECT value FROM json_each(:_probe)`) and FAIL CLEARLY if absent —
    never fall back to raw interpolation. Validate with a `before_cursor_execute`
    hook that captures every `statement`+`parameters` (assert per-statement
    param count ≤ declared budget at 1001 AND 5001 stale videos; assert
    no OR-chain growth, no UNION, no raw id interpolation).
23. **Flaky statement-counter tests: `contextlib.suppress(Exception)` corrupts
    the session and inflates the counter (S08-A02-C4→C5, 2026-08-20).** A
    "no N+1" test wrapped `_advance_generation` in `with
    contextlib.suppress(Exception)`. When that advance silently failed, the
    SQLAlchemy session was left needing a ROLLBACK, so the NEXT query emitted
    extra ROLLBACK/BEGIN statements that the `before_cursor_execute` counter
    counted → the `<=10` assertion flaked (~1/12 runs) even though the batch
    query was correct. Fix bundle: REMOVE the broad suppress (a setup error
    must FAIL the test immediately), make setup deterministic, and instrument
    ONLY `SELECT`s (`stmt.lstrip().upper().startswith("SELECT")`) — never
    count BEGIN/ROLLBACK. Prove stable by looping the test 20–30×
    (`--count=` needs pytest-repeat which is often NOT installed — use a
    plain `for i in $(seq 1 30)` shell loop and count PASS/FAIL lines).
24. **A parent prompt mandating ONE owning writer session can be corrected
    MID-RUN into a multi-subtask DAG (S11-T01, 2026-08-21)** — the user split
    S11-T01 into T01A/B/C/D, each with its own NEW owning session, dispatched
    in waves (A∥B parallel → C after B verified → D after all three), with a
    mandatory session registry, per-subtask exclusive allowlists that list
    sibling TEST files as forbidden, correction = resume-the-same-owner,
    recovery-only-on-dead-session, model-pinned lanes (pinned model + max
    reasoning + fallback disabled for every NEW session; provider rejects ⇒
    BLOCKED_MODEL_ROUTE, never substitute), read-only reviewer Task IDs, and a
    global-gate mutex. Do NOT treat this as a contradiction to resolve
    yourself: the correction SUPERSEDES the earlier single-writer instruction;
    keep all other safety rules from the parent prompt. Full reusable playbook:
    `references/sprint-slice-subtask-decomposition.md`.

25. **Smoke-test the model route BEFORE dispatching writers; handle mid-lane model redirects (S11-T01, 2026-08-21).** A named model/provider can be dead or misrouted. Verify cheaply first: `hermes chat --provider <p> --model <m> -q "Reply with exactly one word: ALIVE" --yolo -Q --max-turns 2` and require the literal word in output. Dead → BLOCKED_MODEL_ROUTE, report to user, never silently substitute a model. When the user REDIRECTS worker models mid-lane (this user self-tests models and swaps providers mid-stream): treat the directive as authoritative for all FUTURE sessions (next waves, reviewers, recovery), record the new model line in sprint contract + registry, do NOT kill/relaunch already-running writers unless told. Reasoning level rides on global `agent.reasoning_effort` in config.yaml — verify it says max instead of hunting for a CLI flag.

  S11-C1 addendum (2026-09-04): a mid-lane "dung luon <model X>, tat het <model Y>" redirect does NOT mean zero Y-requests instantly — audit FOUR sources before answering "sao van thay request Y": (a) already-running writers dispatched under the old binding prompt (theirs keep the old `-m/--provider` cmdline until exit — show the user the live cmdlines as proof, do not kill unless told); (b) global defaults (`config.yaml` model.default + `providers.custom.model`) that every unpinned session falls back to — update them to X; (c) stale cron jobs pinned to Y (`cron/jobs.json` `"model"` field + `hermes cron list`) — pause/re-pin them; (d) watchdog/nudge scripts with their own model constants — pin explicitly, never rely on defaults. Latest user model directive SUPERSEDES the binding prompt's model block for all FUTURE dispatches (waves, recovery, nudges, cron) — record the supersession in the registry with timestamp. Report per-source: what still runs Y and why, what was switched to X.

26. **Bind Task ID → Hermes session ID right after launch via state.db (read-only).** Tee logs often don't print `session_id:` until exit, but the mandatory registry needs it immediately. Query `C:/Users/Admin/AppData/Local/hermes/state.db` read-only (`sqlite3.connect('file:state.db?mode=ro', uri=True)`): last N rows of `sessions` (`SELECT id, source, model FROM sessions ORDER BY rowid DESC LIMIT n`), then disambiguate same-second launches by each session's FIRST user message — `SELECT substr(content,1,150) FROM messages WHERE session_id=? AND role='user' ORDER BY rowid LIMIT 1` — the dispatch prompt text names the task. Beware unrelated probe/smoke sessions created seconds earlier (route smoke tests): match on message content, not recency alone.

27. **Worker response truncation on large single writes — watch, don't kill.** A writer emitting one ~450-line `write_file` can be cut mid-tool-call with `⚠️ Response truncated (finish_reason='length') - model hit max output tokens`. The background process normally SURVIVES and self-recovers next turn (re-plans, chunks the write, proceeds — verified S11-T01B). Do not resume/kill on the banner alone; wait one monitor cycle and confirm progress actually stopped. Prevention: put "write big NEW modules in chunks of ≤200 lines per write_file call" in the packet prompt.

28. **Triage user-reported "Connection error"/session errors against the lane before reacting.** The error the user saw "in your session" may belong to an UNRELATED probe/smoke/delegate session. Verify scope first: `process(action='list')` for the lane's PIDs/status + state.db recent sessions and their first messages. Then answer honestly with evidence (uptime + last log activity of each writer). Never claim "no impact" without having checked both.

29. **Writer self-reports a forbidden-op violation (e.g. `git stash`+`pop` during diagnosis) → verify RECOVERY, record honestly (S11-T01C, 2026-08-22).** A writer ran `git stash`+`git stash pop` chasing a full-suite failure despite the packet forbidding it, then DISCLOSED it in REPORT/LOG. Treat the disclosure as correct behavior — never punish honesty. Verify recovery yourself: `git stash list` empty (nothing left parked), tracked-modified count matches the writer's own post-pop record, ALL untracked work products present (default stash excludes untracked — they were never at risk). When attributing LATER tree deltas (e.g. 33→29 tracked-modified), compare against the writer-only baseline AND check whether a parallel sprint lane shares the worktree before blaming your writer. Autocrlf-specific addendum (S11-T01C R5, 2026-08-22): a stash/pop can silently rewrite a tracked TEXT-mode fixture LF→CRLF (observed: video.mp4 38→39 bytes); git shows NO modification (autocrlf normalizes), but a byte-exactness test fails LATER with no obvious cause. Diagnosis: compare working-tree sha256 vs `git show <commit>:<path> | sha256sum` — size delta ±N bytes on binary-ish fixture = line-ending rewrite. Repair: write the exact committed blob back via python `write_bytes` (never text-mode tools), verify sha matches, re-run the affected suite (18/18 after restore). Prevention to route to Codex: `.gitattributes` with `tests/fixtures/** -text` / `binary`.

 30. **Worker-side context-compaction failure is survivable — don't kill (S11-T01C, 2026-08-22).** A ~180K-token writer logged `⚠ Compression summary failed: Context compression LLM returned empty content … Inserted a fallback context marker.` and still finished SUBMITTED (next turns were re-orientation reads of key files). On this banner: expect a few degraded-context turns, keep monitoring; intervene only if progress stalls ≥2 monitor cycles.

31. **Acceptance test invoking pytest-in-pytest needs an explicit recursion guard (S11-T01D, 2026-08-22).** An acceptance module whose test runs the full suite AS A SUBPROCESS that includes ITSELF fans out exponentially (observed: 21-min non-terminating nested run, killed). Fix: subprocess env sets `env["<PREFIX>_NESTED"]="1"` and the module tops out with `if os.environ.get("<PREFIX>_NESTED")=="1": pytest.skip("nested …", allow_module_level=True)` — exactly one nesting level, frozen suite command unchanged. Put this guard REQUIREMENT in the packet whenever the task defines a one-command acceptance suite. Evidence pattern: tee each full-suite run to `output/<task>/run-<id>/suite_one_command[_rerun].log`.

32. **Correction resumes land first-try when the `-q` text enumerates EXACT findings + gates (S11-T01A/B/C/D cycle, 2026-08-22).** Format that worked repeatedly: every error verbatim as `ruff F841 workspace_id assigned but never used @ app/workflow/original_audio_handler.py:665` (mypy unused-ignore likewise), explicit "fix ONLY these points, no behavior change, no refactor", then exact gate commands with literal expected outputs (`ruff check <files>` = All checks passed!, `mypy <file>` = Success, `pytest <files> -q -p no:cacheprovider --basetemp=<fresh Windows-native>` = N passed). Vague "clean up lint" invites refactors; exact inventories yield ~10-minute narrow fixes. Manager re-runs the SAME gates independently before MANAGER_VERIFIED.

33. **The background-process tracker can DROP a live session id (`process wait` → not_found, `process list` → empty) — the tee'd log is ground truth (S11-T01D, 2026-08-22).** Determine completion from artifacts: log mtime stops advancing + exit banner in the tee'd log + REPORT.md=SUBMITTED + Owning-session filled in TASK.md. Never relaunch off a missing tracker entry alone (double-run risk). Also: when repeated `process(wait)` calls return IDENTICAL preview text or empty payloads, stop polling blind — read the raw log directly (`grep -avE '<box-art regex>' <log> | tail -25`, or `tail -c 3000 | grep -aE 'FAILED|passed|assert'`) to see real progress. Same family, task-list edition: after context compaction the restored todo list can be the SESSION-START snapshot, not current reality — before acting on it, reconcile against actual progress (registry/artifacts/process states) and rewrite with `todo(merge=true)` so only genuinely-finished items get marked completed.

34. **Close-out handoff report for the external reviewer (S11-T01 closeout, 2026-08-22).** After the final subtask verifies, write ONE `docs/pm/sprints/<SPRINT>-CODEX_HANDOFF.md`: per-subtask table (session ID, deliverables, corrections count, terminal state); manager-independent verification evidence (exact commands + counts); a MIN-BLAME protocol-violations section (writer self-disclosed stash/pop, killed its own runaway subprocess) so honesty never costs the lane; known pre-existing failures OUTSIDE sprint scope with root cause + suggested fix; frozen acceptance command with current pass count; resumable session IDs. Then update the registry heartbeat line and STOP all workers — terminal state stays `MANAGER_VERIFIED_PENDING_<REVIEWER>_REVIEW`, never self-APPROVED.

35. **Codex CHANGES_REQUESTED round-trip: verify findings on real code BEFORE dispatching, then verify the FIX STRUCTURALLY, not just by green tests (S11-T01B corr#2, 2026-08-22).** Codex reported P1 (`os.replace` ran BEFORE the source re-hash ⇒ `SOURCE_MUTATED` could co-exist with a published target) + P2 (`assert x == [] or True` tautology). Playbook that landed first-try in ~45min: (a) read the cited lines YOURSELF first — confirm both findings are real before resuming the owner (never relay a finding unverified); (b) resume the owning session with each finding verbatim (file:line), the required fix SHAPE (re-order: fsync → re-hash+cleanup+raise → publish; keep stable error code; add deterministic regression), forbidden scope, and exact gate commands; (c) after exit, verify the invariant STRUCTURALLY: `grep -n CODE_SOURCE_MUTATED` must show exactly ONE raise site and it must sit pre-publish; `grep "or True"` must be zero-match; read the new regression test to confirm it's deterministic (monkeypatch the engine's single `_sha256_file` hook with a call-counter returning a wrong digest only from the 2nd source-hash onward — no sleeps, asserts code + target-absent + dir-empty); (d) rerun the frozen full suite and ACCOUNT FOR THE EXPECTED DELTA: 52→53 passed, the +1 being the new regression test — an unexplained delta either way is a stop-and-investigate; (e) re-run preflight fresh for the new round (rules file re-read mandated per prompt; HEAD/status/route re-check) and UPDATE THE EXISTING handoff doc in place (new date line, corrections count bumped, engine hash replaced, verification section annotated "+N = regression") instead of spawning a second handoff file.

36. **Windows MAX_PATH kills nested acceptance suites via chained child basetemp — fix the HARNESS, and prove root cause by reproducing BEFORE dispatching the correction (S11-T01D C1, 2026-08-22).** An acceptance module that spawns the suite as a subprocess used `basetemp = tmp_path.parent / f"{tmp_path.name}-suite"` — the child basetemp inherits the OUTER pytest tmp_path prefix, and the nested run's artifact/media/SQLite trees then exceed Windows MAX_PATH (observed: outer 2 failed / inner 28 failed with a ~100-char outer basetemp; same code with short basetemp = 2 passed). Fix shape for the writer: a `_child_basetemp(tag)` helper that creates `Path(tempfile.gettempdir()) / f"<lane>-{tag}-{os.getpid()}-{next(seq)}"` — short, unique (pid+counter for concurrent runs), `mkdir(exist_ok=False)` + verify BEFORE spawn, never chained from outer tmp_path; cleanup via `shutil.rmtree(basetemp, ignore_errors=True)` in a `finally` targeting ONLY that dir. Keep the frozen suite command, recursion guard (pitfall 31), shell=False, env-strip. MANAGER verification pattern that landed first-try: (a) reproduce the defect YOURSELF pre-fix with a deliberately long `--basetemp` (expect the failure) + a short control (expect pass) — this proves harness-not-engine and hands the writer an exact repro; (b) after the fix, re-run BOTH gates independently (long-path gate must now pass — that is the regression proof), then the frozen full suite and confirm the pass count did not DROP; (c) check `Temp/` for leftover `s11c1-*` dirs to verify the cleanup actually ran.

37. **Closeout hygiene for a manager lane: sweep temp residue by LANE PREFIX, and attribute cross-lane hash drift before blaming anyone (S11-T01D C1 + S09-P00 wave, 2026-08-22).** (a) Workers leave dozens of `--basetemp` dirs in `Temp/` (one writer produced 40+ `s11t01b_st*`); at closeout `rm -rf` ONLY the lane's own prefixes (`<lane>t01*`, `<lane>smoke*`, `<lane>dbg*`, manager `<lane>-mgr-*`), never a broad Temp sweep — other lanes' live basetemps must survive. (b) When a PROTECTED file's hash drifts mid-wave (e.g. S07 `project_cast.py` 66dbb946→7919aa7b while your lane ran), attribute before reacting: grep YOUR lane's worker logs for any write to that file (expect zero), check mtime, and check whether a PARALLEL manager lane (S07 was `CHANGES_REQUESTED` with its own manager) is authorized to touch it — concurrent-manager edit is the explanation, record it in the handoff §violations as cross-lane attribution, not a violation of your lane. (c) When the parent prompt authorizes TWO lanes in one wave (correction resume + new read-only planning session), dispatch both simultaneously, keep write-sets provably disjoint (test file + packet vs `output/<lane>/` only), and give the read-only lane an explicit output-file manifest (9 named .md files) with a mandatory first-line guard string for any draft/future-prompt artifact (e.g. `DRAFT_ONLY — BLOCKED_DEPENDENCY — DO NOT DISPATCH UNTIL …`) so a planning doc can never be mistaken for a dispatchable prompt.

38. **Worker finishes the ENGINEERING but dies before appending LOG/REPORT —
    manager may complete the PACKET, never the code (S07-T03-C1,
    2026-08-22).** A writer ran the full real-vertical Playwright (2 passed,
    `frontend/test-results/.last-run.json` status=passed) but its process
    died before writing LOG.md/REPORT.md. Recovery playbook: (a) prove the
    work exists via ARTIFACTS (`.last-run.json`, PW logs, file mtimes inside
    the run window) — silence ≠ not-done; (b) re-run every gate yourself;
    (c) append LOG/REPORT entries explicitly LABELED as manager-supervised
    completion: dead writer session + time/reason of death, who appended,
    per-phase model provenance (original route vs correction route),
    evidence paths; STOP vocabulary stays protocol-correct (TASK_SUBMITTED,
    never self-APPROVED). Do NOT second-guess/redo the writer's code — a
    genuinely missing fix gets its own correction dispatch. Companion
    frontend check after a finding deletes a test-only page/route: grep the
    FRESH production build's `.next/app-path-routes-manifest.json` for the
    old route name (comment references in specs are fine; a live manifest
    entry is residue).

39. **Monitoring resumed/long workers: compression grace + watchdog
    lifecycle + tool-syntax traps (S07-T01-C3, 2026-08-22).** (a) Resuming
    a 200+-message Hermes session opens with ~2–4 min of preflight context
    compression ("Compacting context", zero log movement) — NOT a stall;
    grant a grace window before any liveness alert. (b) Extend the
    watchdog's WATCH_GLOBS to cover EACH new lane's output dir
    (`output/<task>-c<N>/*.log`) BEFORE dispatch, or it watches stale
    paths; the watchdog EXITS after an alert or when its watched manager
    exits — re-arm a fresh instance every wave. (c) Tune STALL_SECS per
    lane type: full-stack Playwright verticals are legitimately silent
    >8 min (480s gave repeated false alarms; 900s clean). (d) Alembic
    rejects git-style `HEAD^` — pass the explicit parent revision hash as
    the downgrade target.

40. **API-surface findings: verify with a real OpenAPI probe BEFORE
    dispatching, then re-probe AFTER the fix (S07-T01-C4, 2026-08-22).**
    Codex P1 "client can choose workspace via query param" verified
    deterministically in ~1 min without reading every handler:
    `TestClient(app).get("/openapi.json")`, scan every operation's
    `parameters` — 20 project-cast operations leaked `workspace_id`
    (note: `POST ""` and `POST "/"` are DISTINCT operations; check both).
    Root-cause CLASS: any handler parameter WITH A DEFAULT VALUE
    (`workspace_id: str = WORKSPACE_ID`) silently becomes a
    client-controlled query param in FastAPI; fix shape = remove it from
    every signature, read the server-owned constant in the body. The SAME
    probe post-fix returning zero matches IS the acceptance evidence —
    structural proof stronger than green tests. Companion finding pattern,
    differential-response existence leak: if a cross-workspace request
    returns 409 "already exists" when the natural-key pair is OCCUPIED in
    another workspace but fail-closed mismatch when UNOCCUPIED, that
    response pair is an occupancy oracle; fix = add the workspace filter
    to EVERY lookup (natural-key lookups too, not just idempotency), and
    regression-test BOTH states asserting identical fail-closed status/
    reason-family + zero mutation + other workspace's mapping
    byte-identical. Dispatch protocol that landed first-try: writer writes
    regression tests FIRST, runs them on UNFIXED code capturing
    prefix-FAILED logs, fixes, captures postfix-PASS logs; manager
    verifies both logs exist with matching test names and accounts for
    the expected pass-count delta (+N regressions) on the frozen suite
    (83→85). Untracked sibling-lane test files changing inside your
    worker's window (e.g. S11 files while S07 lane ran) = parallel-lane
    work, NOT scope violation: confirm via transcript grep (0 hits for
    "s11") + `git status --short` showing `??` untracked.

41. **Machine-wide process scans in tests are a concurrency landmine — scope
    them with DUAL ownership signals + add a concurrency regression control;
    subprocess diagnostics need BOTH stream tails (S11-T01B corr#3 +
    S11-T01D C2, 2026-08-22).** A remux-test orphan check scanned
    `psutil.process_iter` filtered ONLY by process name (ffmpeg/ffprobe) —
    two suites running concurrently with separate basetemps each saw the
    other's live ffmpeg as "their" orphan and both failed (real Codex
    finding, reproduced). Fix shape that landed first-try:
    `_owned_ffmpeg_pids(marker)` counts a pid as ours only when BOTH
    signals agree — (a) process-tree descendant of THIS pytest via psutil
    parent-walk from `os.getpid()`, AND (b) the run's unique resource
    marker (managed-root/basetemp path) appears in the process cmdline.
    Replace fixed `time.sleep()` race-masking with bounded-deadline polls.
    ADD a regression control like `test_concurrent_invocations_no_cross_blame`:
    spawn 2 REAL pytest workers with independent managed roots, each
    breaching a short engine timeout, each asserting ITS OWN scoped set
    comes back CLEAN while the sibling provably ran mid-flight. Companion
    P2: a harness that captures subprocess output but surfaces only the
    stdout tail in assertion messages makes stderr-side failures
    undiagnosable — return bounded tails of BOTH streams
    (`_diag_message(code, out_tail, err_tail)`). When a sibling file
    OUTSIDE the write-set keeps a machine-wide pid-diff check, do NOT
    weaken it — serialize the nested suite with a lock-file context
    manager (`msvcrt.locking` on Windows; OS releases on holder death),
    wrap ONLY the run call, zero assertion changes, and record the
    rationale in REPORT. Dispatch rule from the same round: when subtask B
    fixes tests that subtask D's acceptance depends on, their corrections
    run SERIALLY (B→gates→D→gates) even though write-sets are disjoint —
    dependency order beats wave parallelism.

    Round-4 addendum (S11-T01B R4-P2, 2026-08-22): the dual-signal check
    above still leaked — descendants are computed AT CALL TIME, so a child
    RE-PARENTED after its parent dies escapes the parent-walk entirely
    (leak-gate false-negative Codex caught). Re-parent-proof shape:
    SNAPSHOT the run's owned pids WHILE the engine is provably mid-flight
    (tree+marker both true then), and AFTER engine exit poll THAT FIXED
    PID SET via `psutil.Process(pid).is_running()` / bounded-deadline loop
    until gone — pid identity no longer depends on the tree. Marker stays
    for cross-run isolation; never revert to machine-wide name-only scan;
    no fixed sleeps.

    C3 addendum (S11-T01D, 2026-08-22): a pytest-in-pytest harness that
    polls `child.poll()` while holding stdout/stderr PIPEs WITHOUT draining
    them DEADLOCKS — the child fills the pipe buffer on its final output
    flush and blocks forever in `_console_main` AFTER all tests pass
    (py-spy shows main idle at `_pytest/config/__init__.py:254`, 0 CPU for
    hours; the OUTER poll loop has no total deadline so it hangs with it).
    Observed 80+ min hang. Fix shape (both halves REQUIRED): dedicated
    reader threads draining both streams concurrently with the poll loop,
    PLUS a hard total deadline (`time.monotonic() + 1800`) after which the
    child is killed and the tails are surfaced with a diagnostic marker.
    Manager detection pattern for "deadlocked or just slow": psutil
    CPU-times delta over 8s == 0.0 + py-spy dump showing `_console_main`
    = tests DONE but process refusing to exit → pipe deadlock; kill it.42. **Existence/size-only evidence-validity helpers are a false-pass CLASS;
    and a fail-closed fix that fires EARLIER ripples into sibling task
    tests (S11-T01C R4-P1, 2026-08-22).** `_source_evidence_valid()`
    checked relative_path + is_file() + size_bytes only — a same-size
    different-bytes source mutation returned True and the job happily
    remuxed/published wrong bytes (Codex repro'd independently). Integrity
    fix shape for any artifact-evidence gate: (a) verify SHA-256 on disk
    against the recorded Artifact.sha256 at FIRST resolve (fail closed,
    existing stable error code); (b) checkpoint-reuse path verifies size
    AND sha256, never size alone; (c) post-engine compare
    result.source_sha256 AND post_remux_source_sha256 vs recorded; (d)
    pre-publication gate refuses publish on any mismatch, cleanup scoped
    to own staging only; (e) regression = mutate source to equal-length
    garbage mid-pipeline (monkeypatch hook for determinism) → job FAILS
    with stable code, ZERO audio artifact rows and byte-for-byte unchanged
    managed tree; (f) audit checkpoints contain NO absolute paths. THE
    RIPPLE: blocking bad sources EARLIER changes which error code sibling
    suites observe downstream — an integration test from another Task ID
    asserted the OLD code (ENGINE_FAILED from a corrupt-source case) but
    now gets SOURCE_NOT_READY from the source phase; behavior is correct,
    the expectation is stale. Routing rule: the sibling file is OUTSIDE
    the correcting writer's allowlist — writer reports it, manager does
    NOT let them touch it; expect the frozen-suite red, dispatch a
    mini-correction resuming the SIBLING TEST's OWN owning session to
    update the expectation, then re-run global gates. Never widen one
    lane's write-set to absorb another task's ripple.

    R5 addendum (S11-T01C R5-P1, 2026-08-22): same false-pass CLASS, DB
    authority edition — `_validate_source_artifact()` only read
    `VideoItem.source_artifact_id` when its argument was EMPTY, and every
    runtime path passes the manifest-pinned id, so a stale job kept
    validating/remuxing/publishing from artifact A after the item's
    pointer moved to B; checkpoint reuse validated bytes only. Fix shape:
    the CURRENT column value is the single authority — resolve phase
    rejects manifest id ≠ current with `SOURCE_OWNER_MISMATCH`; checkpoint
    resume revalidates authority BEFORE any byte check (purge staging then
    raise); publish gate re-compares current id+sha. Regression: submit-A
    → swap-B → job fails closed at BOTH replay points (post-source-
    checkpoint and post-remux-checkpoint), zero audio artifacts, engine
    never re-runs. General rule: ANY validator that treats a caller-
    supplied identifier as authoritative over current persisted state is
    a stale-reference bypass.

43. **Windows `os.execv` in a Playwright webServer wrapper leaks an orphan
    server per run (S07-T03 harness, 2026-08-22).** A boot wrapper that
    wipe+seeds then `os.execv`s into uvicorn does NOT replace the PID on
    Windows: Python spawns a NEW interpreter process, the wrapper exits,
    Playwright teardown kills the already-dead wrapper PID, and the REAL
    uvicorn survives holding its port + temp DB — the runner then hangs
    forever after tests pass. Symptom signature: one fresh LISTENING
    :<port> entry after EVERY run (three consecutive different PIDs across
    three runs). Fix shape: seed/wipe in the same script, spawn the server
    via `subprocess.Popen`, keep the child PID, forward SIGTERM/SIGINT →
    terminate. Manager gate: `netstat -ano | grep :<port>` must be EMPTY
    after each run; also require the runner process to self-exit.

44. **Dual-project Playwright configs bleed DB state across projects
    (S07-T03, 2026-08-22).** desktop + mobile projects sharing one seeded
    DB make natural-key-creating scenarios execute TWICE per full run; the
    second execution hits idempotency-key-bound/already-exists 409 while
    `--project=<one>` alone passes. Detection rule: fails ONLY when both
    projects run in one invocation. Fix AT THE CAUSE (per-scenario cleanup
    of pre-existing mappings incl. cross-project rows + explicit handling
    of already-published/idempotent replay), never by splitting into
    separate per-project invocations — that hides the defect the config
    exists to catch.

45. **Focused-clean ≠ global-clean: after EVERY correction round re-run the
    GLOBAL battery yourself and route residuals back as micro-corrections
    (S07 round-2, 2026-08-22).** Two consecutive rounds where writers
    verified only their own files: global `ruff check app tests` found 19
    I001 errors in their new test code, then global `npx eslint .` found 4
    no-explicit-any errors + an unused var the writers never saw. Loop
    that works: manager runs global gates → resume the OWNING session
    (same session id) with an exact inventory (`file:line` + rule code +
    "fix ONLY these points") → re-run global gates → repeat until clean.
    Expect ~4–20 min per micro-correction on muse-spark.
    Two addenda (S07 round-2 confirmations): (a) VERIFY GATE INPUT FILENAMES
    EXIST before launching a battery — recalling sprint-convention test names
    from memory (`tests/test_s06_surface_api.py`,
    `tests/test_s08_object_gallery.py`) made pytest exit 4 with
    "file or directory not found": a FALSE-FAILED gate, not a regression.
    `ls tests/ | grep <pattern>` first and run only real paths. (b) the correct
    typecheck invocation is plain `npx tsc --noEmit`;
    `--incremental=false` is not a valid CLI flag (TS5023 Unknown compiler
    option).

46. **A worker REPORT can contradict its own evidence file — grep the
    artifacts (S07-T02-C4, 2026-08-22).** REPORT claimed "SMOKE PASS" while
    the referenced smoke.log contained a Traceback
    (`AttributeError: 'NoneType' object has no attribute '_session_factory'`)
    and `SMOKE_EXIT:0` was appended unconditionally. Never accept a smoke
    claim without reading the log tail; if a smoke is broken, don't block on
    it — check whether the same coverage already exists elsewhere (here:
    pytest fallback-matrix tests + API tests + Playwright banner assertions)
    and note the discrepancy honestly in the manager verification report.

47. **Parallel corrections where B's new test depends on A's production fix:
    ship the dependency honestly as BLOCKED_DEPENDENCY evidence, re-run after
    (S07-T03-C2 + T02-C4, 2026-08-22).** T03 replaced an API-level repin with
    a real UI-flow test that requires T02's picker PATCH fix. T03 ran it
    anyway, captured the EXPECTED failure (0/4, all failing at submit-success
    with 409 already-exists — the exact P1 symptom) as BLOCKED_DEPENDENCY_T02
    evidence, and did NOT patch production itself. After T02 landed, the
    manager re-ran T03's suite: 0/4 blocked → 4/4 PASSED is end-to-end proof
    that T02's fix works through the production UI. Rule: write-set-disjoint
    waves may run in parallel even with runtime dependencies IF each lane
    records honest dependency evidence instead of faking green.

48. **Reproduce e2e findings ONLY against the sprint's canonical config
    (S07 round-2, 2026-08-22).** A stale sibling playwright config (missing
    the webServer boot-backend wiring) made the manager conclude "wipe+seed
    never runs in PW flow" — wrong diagnosis; the canonical config wires it.
    Before diagnosing any Playwright failure: confirm WHICH config file is
    authoritative (webServer wiring, ports, projects list), read it fresh,
    and reproduce with exactly that file. Stale-config reproductions burn a
    whole correction dispatch on a phantom defect.

49. **Allowlist-vs-evidence arbitration: a file outside the literal write-set
    is IN scope when the verdict cites it by path:line (S07 round-2,
    2026-08-22).** Codex's P1 cited `app/persistence/project_cast.py:168-197`,
    which sat inside T01's persistence write-set on paper; the T02 writer
    edited it and that was the CORRECT call — the reviewer's citation is the
    authoritative scope grant. Manager arbitration recipe: (a) confirm the
    cited lines match the finding (read them yourself pre-dispatch); (b)
    verify NO collateral: schema/migrations untouched (`git status
    --porcelain models.py migrations/` + mtimes older than the run window),
    no files beyond the cited one changed in that directory; (c) record the
    extension explicitly in the manager report as "cited-by-verdict
    extension" so Codex sees it was deliberate, not drift. Contrast: an
    UNCITED file in the same directory would still be a violation.

50. **Temp SQLite FK/alembic gate recipe that actually works (S07 round-2,
    2026-08-22).** `MOTIONFORGE_ROOT` alone is NOT a DB URL — `alembic
    upgrade head` fails with "No database URL configured", and SQLite cannot
    create a DB inside a not-yet-existing directory (`unable to open database
    file`). Working sequence: `mkdir -p <tempdir>` FIRST, then export
    `MOTIONFORGE_DATABASE_URL="sqlite:///<tempdir>/fkcheck.db"` and run
    `python -m alembic upgrade head`, then `PRAGMA foreign_key_check`
    (expect `[]`) + table count via SQLAlchemy. Never point this at MAIN's
    `data/motionforge.db`.

51. **Empty assistant replies after tool batches are a recurring failure
    mode — the user must re-prompt "process the tool results" (≥4× this
    session, 2026-08-22).** When a turn ends with tool calls and no text,
    the results still landed — the NEXT turn must open by processing them
    (state what the output shows, then act). For long monitor loops, do not
    end a turn on a bare `sleep+tail` command: append one line of
    interpretation ("T02 still running, next check HH:MM") so a swallowed
    reply costs the user nothing. If the user pings mid-turn (out-of-band
    message), pending tool results are still valid evidence — answer from
    what already landed instead of re-running gates.

52. **Stale background notifications after close-out: classify before
    acting (S07 round-2, 2026-08-22).** After terminal state, delayed
    completion notices keep arriving (old diagnostic runs, already-processed
    gate batteries, mystery exit-1 wrappers). Triage each in ONE cheap
    command — read the log tail: if the result was already consumed in the
    manager report (or the run predates the fixes), reply "already
    processed, no action"; if it is a NEW failure, investigate. A `rm -rf`
    "Device or resource busy" on a temp root resolves itself once the holder
    process dies — retry the delete once at close-out instead of treating
    the old exit-1 as an open blocker.

53. **Docs-only readiness waves between sprints: three read-only lanes ∥ one
    synthesis lane, against a MOVING baseline (S11-P02, 2026-08-23).** When a
    parent prompt authorizes a post-sprint readiness packet (audit lanes +
    synthesis, zero production writes), run Wave 1 = P02A∥P02B∥P02C (new
    sessions each, disjoint `output/<run>/lane-{a,b,c}/**` write-sets,
    read-everything/write-own-dir-only) then Wave 2 = synthesis ONLY after
    manager-verifying every lane. Prompt structure that landed first-try per
    lane: explicit deliverable-file manifest, per-claim gate ("self-check
    VERIFIED/UNVERIFIED via grep/read before writing"), forbidden scopes
    (app/tests/frontend/migrations/docs-pm/data/MAIN/prior outputs), no
    network/model downloads, TASK_SUBMITTED-not-APPROVED vocabulary.
    Synthesis prompt must enumerate the exact input files + demand a trace
    matrix (each output ID cites lane section + roadmap row), DAG with
    parallel-safe pairs, migration single-head runtime rule (measure head at
    run time, never hard-code), BLOCKED_ON_<gate> labeling, and a
    MEASURED/PROPOSED/UNKNOWN split. Full playbook:
 `references/readiness-docs-lane.md` (incl. the C1→C6 correction-round
 ladder: frozen decisions → exact-artifact freezes → full DAG
 re-serialization + audit-metadata fixes → ID-split/ID-add structural
 surgery (17→19 IDs; enumerate every downstream touchpoint in the
 dispatch prompt; prompt-FILE dispatch for >8KB prompts) → micro-surgical
 stale-text rounds (locate each sentence yourself pre-dispatch, pass
 verbatim old→new pairs + a legit-occurrence allowlist for banned tokens,
 full-run-dir inventory diff, REPORT history-order gate); cumulative
 stale-string regression batteries; verification-script traps for drifting
 heading formats, false-positive same-wave dependency flags, AND
 manager-side gate greps whose anchors were typed from memory — pull
 anchors from the live text before ruling FAIL).
    Three traps from this run: (a) **moving baseline** — a parallel sprint
    lane (S09-T00-I01/I04) mutated `models.py` + added migrations DURING the
    readiness run; docs citing such files must anchor to SYMBOL NAMES
    (`grep class StructuralLockManifest`), never line numbers or hashes, and
    cross-lane attribution goes in the coordination report, not as your
    lane's violation; (b) **unverifiable numbers in prompts** — a lane
    correctly REFUSED to echo the prompt's "suite took 237s" (no evidence
    anywhere), re-measured itself (64 collected, 166.70s) and recorded the
    original as UNVERIFIED; manager re-ran the measurement independently and
    confirmed — reward this honesty, never let a worker fabricate support
    for a prompt-supplied number; (c) **terminal condition** stays
    `TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` with production IDs
    labeled `BLOCKED_DEPENDENCY_ON_<gate>` — a planning packet NEVER opens
    the gate it documents.

54. **Process-tracker anomalies at closeout: `not_found`, identical wait
    payloads, and psutil scan races — artifacts are ground truth
    (S11-P02, 2026-08-23).** (a) After an orphan-recovery marker, `process
    poll/wait` can return `not_found` for a worker that ALREADY exited
    cleanly — do not relaunch off tracker absence alone; verify via tee'd
    log exit banner + artifact mtimes + REPORT verdict (lane C had all 4
    deliverables written before the tracker lost it). (b) Repeated
    `wait(timeout=240)` returning byte-identical previews or empty payloads
    means you're polling blind — switch to reading the raw log tail and
    state.db last-message timestamps for liveness. (c) psutil
    `process_iter(['pid','cmdline'])` list-comprehensions raise
    `KeyError: 'pid'` when a scanned process dies mid-iteration, and a grep
    scan can match ITS OWN cmdline (the pattern string appears in the
    python -c argument). Robust scan: heredoc script, per-process
    try/except inside the loop, filter by process-name prefix
    (`name.lower().startswith('hermes')`) BEFORE touching cmdline, and
    treat scan results as approximate — confirm survivors with a second
    targeted pass.

55. **A CHANGES_REQUESTED can target the PLANNING PACKET itself — resume the
    synthesis owner with Codex's decisions relayed verbatim, then gate the
    result STRUCTURALLY on the plan text (S11-P02D-C1, 2026-08-23).** Codex
    returned P1s against the synthesis doc: T02A required tests but its
    allowlist forbade the test paths (AC→allowlist closure); edge_halo/
    temporal_flicker were droppable despite the overlay mandating all 8 QC
    reason codes; T03A/T04A were too big for one session; T06A ran parallel
    to the threshold contract it consumed; 4 product decisions left open.
    Round landed first-try: hash-baseline ALL prior outputs pre-dispatch →
    resume the SAME synthesis session (allowlist narrows to plan+REPORT
    only) with findings verbatim + frozen BA/CODEX decisions A–H verbatim +
    the exact 17-ID decomposition and wave DAG pre-named by Codex → after
    exit, verify by structural greps on the plan itself (ID count, per-ID
    8-field completeness, mandated enumerations present in outcome AND
    acceptance, `item…UNKNOWN` co-occurrence zero, no arbitrary-create POST,
    no accept/dismiss control, shared files each have ONE named owner,
    protected hashes unchanged). Prevention list that would have saved the
    round lives in `references/readiness-docs-lane.md` §"Correction round on
    the PLAN itself".

56. **Triage worker exits honestly — EXIT≠0 crash AND EXIT=0 false-complete
    both happen; corrections land first-try when the MANAGER pre-root-causes
    every finding (S09-T00-I01/I04 wave, 2026-08-23).**
    (a) Two failure shapes in one wave: I01 died EXIT=4 mid-edit (half-edited
    test file left behind); I04 exited EXIT=0 cleanly but MID-PATCH of an
    output-lane script, never wrote REPORT.md. DONE requires REPORT.md =
    TASK_SUBMITTED + cited evidence files exist + manager-run gates pass —
    exit status alone proves nothing either way.
    (b) Before dispatching any correction, ROOT-CAUSE the failures yourself:
    run the worker's focused suite independently, enumerate exact findings
    ("migration has ck_…_revision_positive but ORM class lacks it → parity
    fails"; "test seed inserts duplicate PK 'rr1' → UNIQUE fail"), then
    resume the OWNER session with numbered verbatim findings + explicit
    keep-list (prior work untouched, write-set unchanged) + the remaining
    TASK.md checklist. This landed first-try: crashed I01 went from 7/9 to
    full SUBMITTED (incl. the domain suite it had never started) in one
    resume.
    (c) Crash truncates the log BEFORE the `session_id:` banner prints —
    recover the owner from Hermes state.db (`sessions` recent rows,
    disambiguated by each session's FIRST user message naming the TASK ID),
    then `--resume <sid>`; never open a second session for the Task ID.
    (d) Parallel writers interfere TRANSIENTLY: the schema-publishing writer
    (new migration file appearing mid-run, briefly broken DDL) blew up the
    SIBLING writer's regression suites (27F/187E, every failure inside
    `alembic upgrade head` fixture setup). Correct worker behavior (encode
    in packets): attribute failures by WRITE-SET OWNERSHIP before
    self-blame, bounded wait ≤10 min/cycle, re-probe `upgrade head` + table
    set after the sibling settles. Manager mitigation: stagger dispatch so
    the migration-publishing writer lands first, or schedule suite-heavy
    regression runs only after the schema source stops changing (mtime
    probe). Full runbook: `pm-session-execution` skill →
    `references/manager-verify-and-correct-workers.md`.

57. **A foreign manager lane can be mid-correction INSIDE your worktree —
    detect via cmdline scan before treating tracked-file drift as your
    incident (S11-P02 C1/C2, 2026-08-23).** Dirty count drifted 266→273→275
    across a docs-only readiness run with zero writes by this lane. Attribution:
    psutil scan for `hermes` processes whose cmdline contains another lane's
    task tag (`S09-T00-I01`, `S13-P00D`) — those writers legitimately mutate
    models.py/migrations/tests in the SHARED worktree under their own prompts.
    Record as cross-lane activity in your coordination report; never blame
    your workers or revert. Corollary: your own lane's "only allowlist
    changed" proof must diff FILE HASHES of your artifacts (snapshot before,
    after), not git dirty counts — dirty counts move for reasons outside
    your control.

58. **Resume-time context compression on a 130+-message session is normal;
    distinguish it from a hung dispatch (2026-08-23).** A resumed writer
    shows ~2–4 min of zero log movement right after launch (`↻ Resumed
    session … N total messages` then silence) plus venv lazy-refresh warnings.
    That is preflight compression, not a stall — grant the grace window
    before liveness alerts. Real progress signal = state.db last-message
    timestamp advancing; log mtime alone can lag during long thinking turns.

59. **Dispatching long correction prompts via bash `-q '...'` dies on quoting
    before hermes even starts; use a prompt FILE (S11-P02D-C4, 2026-08-23).**
    A ~12KB prompt containing single quotes/backticks passed inline as
    `-q '<text>'` killed the shell with `unexpected EOF while looking for
    matching '''` — the log file was never created and NO session ran, so
    verify dispatch actually launched (log exists + grows) before entering
    monitor waits. Working pattern: `write_file` the prompt to
    `%TEMP%/<lane>_prompt.txt`, then background-launch
    `PROMPT=$(cat <file>) && hermes chat --resume <sid> --provider custom
    --model alpha -q "$PROMPT" > <log> 2>&1`. Same family: a FOREIGN lane can
    COMMIT inside your preflight window (observed dirty 508→1, HEAD
    a43b20d→ee10e55 mid-audit) — always discover+pin ACTUAL head at
    preflight instead of trusting the parent prompt's snapshot, re-pin
    protected hashes after any foreign commit, and note that `output/**`
    git-ignored artifacts stay byte-stable across commits so your hash-diff
    allowlist proof survives. Cross-check psutil open_files() on the two
    synthesis files for writer-collision before resuming.

60. **Worker self-check reporting ALL-PASS can still miss a binding clause —
    the MANAGER's independent structural greps are the real gate; close gaps
    with a one-finding R2 resume (S11-P02D-C4/R2, 2026-08-23).** The C4
    worker printed "12/12 PASS" yet its T03G block omitted the mandated
    "client KHÔNG chọn handler/provider/detector implementation và KHÔNG tạo
    QCItem trực tiếp" outcome clause; the manager's own regex sweep over the
    block caught it. Playbook: after exit, run YOUR OWN field-presence greps
    per binding bullet (not the worker's script); when exactly ONE finding
    remains, resume the SAME owner with a MICRO-FIX prompt naming the exact
    insertion anchor + verbatim clause + "no other block/wave/dep changes"
    — landed in 13 min first-try. Also classify automated-gate flags before
    believing them: dependency-parser "MISSING T03C/T03D/T03E" was just the
    abbreviation `T03B/C/D/E`; "extra dep T06B" was the explicit negation
    `(+ T06B không ràng buộc)` (same as rev-C3); stale strings "17 IDs"/
    "12 waves"/"REV4 current" living ONLY in the prompt-mandated history
    line and the self-check row DESCRIBING the grep (=0) are legitimate,
    not regressions. Verify each flag against context; report parser
    artifacts as resolved, never as findings.

61. **Docs-only correction hygiene classes from C5/C6 (S11-P02D, 2026-08-24):
    partition-freeze acceptance, current-round metadata honesty, explicit
    tri-file scope split.**
    (a) *Aggregate-count acceptance invites ownership ambiguity (C6-F1 [P1]).*
    An AC like "tổng W6 = đủ 8 codes cùng T03B/T03C/T03E audio/timecode" reads
    as if the audio/timecode checks COUNT toward the 8 overlay codes. When
    freezing binary acceptance over an enumerated set, freeze the PARTITION,
    not the aggregate: per-owner codes verbatim (T03B sở hữu 2 <named> +
    T03C sở hữu 3 <named> + T03D sở hữu 3 <named> = 8 overlay codes), an
    explicit exclusion ("T03E sở hữu RIÊNG audio_missing và av_sync_drift —
    hai check này chạy trong W6 nhưng KHÔNG được tính vào tám overlay codes"),
    and the total ("T03F vẫn chạy đúng 10 checks tổng = 8 overlay + 2 audio
    checks"). Dispatch as ONE verbatim whole-sentence replacement; leave the
    frozen Decision table alone when it is already correct.
    (b) *Stale current-state markers accumulate across rounds (C6-F2 [P2]).*
    After N rounds the header still describes an old round: Task field says
    "áp correction round 4", a superseded history entry keeps "(hiện tại)",
    an ops line says "trong correction C4 này", the old self-check section is
    unlabeled, AND a past REPORT entry carries a wrong date. Fix pattern:
    rewrite current-round prose (title/task/ops line), STRIP "(hiện tại)"
    from superseded history entries while keeping EVERY entry, relabel old
    sections "HISTORICAL — Self-check correction C<n> (verification current
    nằm trong REPORT mục CORRECTION C<m>)", and correct dates APPEND-ONLY —
    never rewrite the historical line; record "heading X dùng ngày
    2026-08-23 là metadata SAI; ngày authoritative từ filesystem/coordination
    là 2026-08-24 ~00:04+07" inside the NEW append.
    (c) *Split worker vs Manager writes EXPLICITLY once reviewers audit the
    ledger (C6-F3 [P2]).* Worker allowlist = the synthesis files ONLY;
    the Manager coordination append happens AFTER worker exit + tree stable
    and ONLY because the round prompt grants it explicitly; historical
    coordination sections are untouchable. Preflight then pins hashes for ALL
    THREE files — the reviewer pinned the manager-owned COORDINATION_REPORT
    alongside plan/report (each MATCH + byte-stable ≥3s ×2 snapshots) — and
    one final stability snapshot runs AFTER the Manager append.
    (d) *Workers can insert the round's append block at the WRONG POSITION*
    (C5's section landed BETWEEN existing sections instead of at file end;
    the worker caught it during its own ordered-section check and moved it).
    Demand ordered-section verification in the dispatch self-check AND gate
    it manager-side (section positions strictly ascending C1<C2<…<Cn).
    (e) *Manager gate FAIL ≠ document FAIL.* Structural greps failed on
    anchors typed from assumption ("CHỈ theo" vs written "CHỈ được theo";
    missing "/PUT/PATCH" in the quoted clause; case-sensitive "RIÊNG") —
    read the FULL block text before ruling any structural FAIL; only then
    decide micro-fix resume vs pass (extends #53/#60).

62. **Silent worker death is an EPIDEMIC pattern, not an anomaly — triage
    signature + mandatory post-exit DONE check (S09 full-sprint run,
    2026-08-23/24).** In one 10-task sprint, 5 of 10 workers died mid-run:
    some with hard crash (EXIT=4), most with wrapper EXIT=0 while actually
    MID-WORK (patching a script, mid-CORS-fix, before ever writing
    REPORT.md). Triage signature for silent death: log size frozen across
    two spaced samples (+0 bytes over 60–90s), `tasklist` python.exe count
    = 0, process tracker empty, AND no wrapper `EXIT=` line appended at log
    tail. Recovery loop that worked every time: (a) verify disk state
    yourself (`find <lanes> -newermt`, run the focused suite, read the last
    reasoning lines); (b) recover owner session id from state.db first-user-
    message disambiguation (pitfall 26/56c); (c) write a RESUME packet that
    states what is ALREADY DONE on disk (so the writer doesn't redo it),
    names the exact stopping point, lists remaining steps only, forbids
    scope change; (d) `--resume <sid>` background launch. NEVER treat
    wrapper EXIT=0 as completion — DONE requires REPORT.md =
    TASK_SUBMITTED + cited evidence existing + manager-run gates passing.
    Expect ~40–50% of tasks in a long sprint to need exactly one resume;
    budget timeline accordingly (each resume cost 20–90 min here).

63. **Validate gate applicability to file type BEFORE treating a gate
    failure as a finding (S09-T01 verify, 2026-08-24).** Running
    `ruff check` over a write-set that included a `.ts` frontend file
    produced "Found 561 errors" — all invalid-syntax noise because ruff is
    a PYTHON linter. A gate failure on files the gate was never meant to
    parse is a FALSE-FAILED gate, not a regression (same class as pitfall
    45a's nonexistent test paths). Rule: before recording a lint/type gate
    result, confirm the tool matches the file extension set; JS/TS gates
    are tsc/eslint, Python gates are ruff/mypy. Record the correction in
    the registry when you got it wrong (transparency), and never let the
    bogus failure reach a dispatch prompt as a finding.

64. **When a worker contradicts a TASK.md context assumption WITH evidence,
    hash-verify the contradiction yourself before flipping the verdict
    (S09-T00-I05, 2026-08-24).** TASK.md said reference media `5A175454…`
    was absent → plan called for SKIP_WITH_REASON; the worker found the
    file on disk (READ-ONLY under MAIN projects/) and reported
    VERIFIED-with-deviation instead of silently skipping OR silently
    trusting. Manager acceptance pattern: (a) praise the honest deviation
    explicitly in the registry (it is the behavior pitfall 53b rewards);
    (b) re-hash the referenced artifact YOURSELF (`sha256sum` over the
    actual path) and compare against the expected digest before accepting
    VERIFIED — a claimed hash match you didn't reproduce is hearsay;
    (c) record the TASK.md assumption error so future packets stop
    propagating stale context. Generalizes: any worker claim about
    external-world state (file exists, version X installed, endpoint up)
    gets one cheap independent probe from the manager before it enters
    the evidence chain.

65. **"Model returned empty content after retries" bursts are a distinct
    failure mode from router-down — shorter resume prompts + stepwise
    logging as countermeasure (S09-T06B, 2026-08-24).** Near sprint end,
    3 dispatches in ~2h died with `⚠️ No reply: the model returned empty
    content after retries` while `/v1/models` kept returning 200 — health
    probes do NOT catch this mode (the endpoint is up; chat completions
    intermittently return empties). What worked: resume the SAME owner
    session with a SHORTER prompt that names only the exact stopping point
    + remaining steps, and instruct "mỗi bước ghi log ngay để không mất
    tiến độ khi model trả empty" — each surviving window then banks
    progress instead of losing it. Also: one resume can die before writing
    ANYTHING to the log (R3 wrote 0 bytes; wrapper exit code even got
    mangled by an unterminated quote in the next command) — verify the new
    log tail actually advanced past the resume banner before entering
    monitor waits. Distinguish from silent-death pitfall 62: there the
    process vanishes mid-work; here the process exits cleanly but early.

66. **Final full-repo regression will catch stale allowlist tests your
    per-task waves never touched — budget a narrow FG correction lane
    (S09 final gate, 2026-08-24).** The first full-suite run of the whole
    worktree failed on `test_durable_job_persistence.py::
    test_no_worker_or_api_cutover_tables`: its hard-coded expected-tables
    set predated SIX additive tables (`reskin_config`, `apply_checkpoint`,
    `project_cast_mapping`, `s09_correction`, `segment_render_route`,
    `structural_lock_manifest`). This file was NOT in I04's normalization
    allowlist, so no wave ever fixed it — and part of the gap PRE-DATED
    the sprint (pre-existing, but per rules never used as an excuse).
    Handling that worked: dispatch a narrow FG-correction worker whose
    allowlist is exactly ONE test file + its output lane, pointing at the
    already-normalized sibling (test_persistence_bootstrap.py) as the
    copy-pattern, requiring ×2 PASS + an adversarial plant-a-fake-table
    proof that the assertion still fails closed. Also note for round-trip
    gates: downgrade-to-base can be BLOCKED by earlier sprints' irreversible
    migrations by design — prove the NEW revision's round-trip against its
    parent revision instead of `base`.

67. **Manager self-inflicted false gates: run linters only on file types
    they parse, and record your own gate mistakes transparently
    (S09-T01, 2026-08-24).** Running `ruff check` across a write-set that
    included `frontend/src/features/reskin/index.ts` produced "Found 561
    errors" — all invalid-syntax noise because ruff is a PYTHON linter.
    Before recording any gate result: match tool to extension set (ruff/
    mypy = .py; tsc/eslint = .ts/.tsx). If you already recorded the bogus
    failure, correct it in the registry explicitly ("ruff trên .ts không
    áp dụng — Manager nhầm lẫn đã loại khỏi gate") rather than silently
    dropping it — the registry is also an audit trail of MANAGER errors.

68. **Playwright 'skipped' results need a by-design check before counting
    as green or red (S09-T04/T05B/T06B, 2026-08-24).** Multiple S09 lanes
    reported Playwright FULL spec as "N passed / M skipped" where the skips
    were by-design mobile-project checks (dual-project config, skip gated
    on viewport). Acceptance language for packets: require workers to state
    WHICH tests skipped and WHY in REPORT (by-design vs environment), and
    manager spot-checks one skipped id against the spec source. Never let
    a worker report bare counts without the skip classification — both
    fake-green (skipping the real mobile assertions) and fake-red (treating
    designed skips as failures) happen without it.

69. **Stale hard-coded HEAD constants are a SECOND final-gate class beyond
    stale allowlists (S09-FG2, 2026-08-24).** When a sprint adds a new
    alembic revision (T05A → head moved d8e9f0a1b2c3→b3c4d5e6f7a9), every
    older migration test file asserting a literal head breaks: two files
    carried `HEAD = "b2c3d4e5f6a7b"` (stale since BEFORE the sprint), one
    `HEAD = "d8e9f0a1b2c3"`, one mixed (revision-identity assert correct,
    heads/db-state asserts stale). Fix shape per file: replace the constant
    with `ScriptDirectory.from_config(...).get_heads()` live discovery while
    PRESERVING each assertion's original meaning (revision-identity checks
    on the file's own migration keep their literal; heads/db-state checks go
    live). Never weaken the single-head assertion itself. Dispatch as a
    narrow FG-correction lane: exactly N named test files + output lane,
    ×2 PASS + ruff, plus a quick re-run of adjacent migration suites to
    prove nothing else broke. Together with pitfall 66 this means: budget
    TWO narrow FG lanes in every full-gate pass (expected-tables class +
    head-constant class).

70. **Full-suite teardown can fabricate a huge ERROR count — judge by
    FAILED, not errors (S09 final gate run 1, 2026-08-24).** A 5-minute
    full worktree regression reported "4 failed, 238 passed, 1526 errors"
    where ALL 1526 errors were `PermissionError: [WinError 32] The process
    cannot access the file` raised inside pytest's tmpdir `rmtree` cleanup
    (Windows keeps SQLite handles alive briefly after the session closes).
    Triage: bucket `^ERROR` lines by file — when they cluster on unrelated
    legacy files AND the captured exception is WinError-32-on-basetemp, the
    failures are teardown noise, not code. Countermeasures: evaluate the
    gate on the FAILED list only; give each run its own fresh
    `--basetemp=<short Windows path>`; if a specific fixture's db handle is
    the repeat offender, that ONE fixture gets an `engine.dispose()` before
    yield-return, never a global ignore.

71. **Verify day-of-week before publishing dated ETA tables (user-corrected,
    S09 planning, 2026-08-23).** An estimate table labeled a completion
    milestone "Chủ nhật 25/08" when 23/08 was the Sunday (25/08 = Tuesday)
    forced the user to correct the calendar. Rule: any timeline that maps
    offsets to weekday names gets one `date -d '+N days' +%A` (or equivalent)
    check BEFORE it goes into chat; and every heartbeat timestamp carries
    the full DD/MM so drift cannot accumulate silently. Cheap fix, but a
    wrong calendar in an ETA destroys trust in the whole estimate.

72. **Keepalive watchdog for a stalled manager/worker session — cron
    `hermes chat --resume` with PINNED model (S11-C1 C2, 2026-09-04).**
    When the user's manager session keeps stopping between turns, run a
    cron **no_agent** script every 10 min that nudges it:
    `hermes.exe chat -q "tiếp tục làm việc đi" -r <SID> -m <MODEL>
    --provider custom -Q`. Hard rules learned:
    (a) resume WITHOUT `-m/--provider` silently uses the profile DEFAULT
    model, NOT the session's `model_config` (observed `meta` via the old
    9Router = a FORBIDDEN route) — always pin both;
    (b) cron `.sh` scripts break on Windows (scheduler mangles backslash
    paths → `C:UsersAdmin... No such file`) — use `.py`;
    (c) in the .py use `subprocess.run(stdout=<logf>)`, NEVER
    `capture_output=True` (it swallows the manager's response so logs keep
    only start/exit markers); fd-direct writes land BEFORE the buffered
    "start" line — order skew in the log is normal;
    (d) the cronjob tool cannot set a model → agent-mode cron jobs fall to
    the default model — keep watchdogs script-only/no_agent;
    (e) cron `deliver='origin'` NEVER reaches the desktop chat when the
    gateway is off (`no origin or home channels — skipping delivery`) —
    report by reading the log when the user asks, and ALWAYS include the
    NUDGE TIME column (user complained when the table lacked it);
    (f) `HTTP 502 FreeUsageLimitError` from a free-tier provider
    (ocgfree/muse-spark-1.3-contributor-free) = provider rate limit, NOT a
    script bug — cron self-retries each tick; never silently swap route
    without asking the user;
    (g) ONLY stop the cron when the user says "dừng" explicitly —
    "m ko nhac nua a?" is a QUESTION, not a stop order ("t có bảo m dừng
    đâu"). Full recipe + the working script:
    `references/keepalive-reminder-watchdog.md`.

73. **Full-model migration mid-sprint (1.2 → 1.3): kill the CONSTANT, not just the process (S11-C2, 2026-09-04).** User demanded 100% `cmc/meta/muse-spark-1.3-contributor` (muse provider), zero `muse-spark-1.2`. Audit FOUR places before claiming clean: (a) live worker cmdlines (`ps aux | grep hermes`) — dispatches via `hermes chat --resume` with NO `-m` flag inherit the session's `model_config` (desired 1.3); a `-m ...1.2` cmdline is the only live-violation signal; (b) watchdog/nudge scripts with hardcoded model constants (`NUDGE_MODEL = "ocg/muse-spark-1.2-contributor"`) — kill the loop AND comment out the constant, or the next nudge reintroduces 1.2; (c) cron jobs pinned to old model; (d) dispatch logs (`grep -ril 1.2 lanes/`) — hits in `.db` copies are lookup artifacts, not workers. Billing-side "muse meta" requests while `ps` is empty = the MANAGER's own session model, not a worker leak — prove with empty ps + exited tracker states before arguing. Record the supersession (old→new, timestamp, scope=future-dispatches) in the registry.

74. **Explicit `-m <model> --provider custom` can 403 while the SAME model via session inheritance works (S11-C3, 2026-09-04/05).** Dispatching `hermes chat --resume <sid> -m cmc/muse-spark-1.3-contributor --provider custom` died with `HTTP 403 FORBIDDEN: Model/provider not recognized: anthropic:muse-spark-1.3-contributor` — a deterministic route-binding rejection, NOT a transient 502 (contrast pitfall 15's 502-timeout, which IS retryable). Bounded retry on the identical pin failed the same way. But the SAME lanes dispatched with NO `-m/--provider` flags — inheriting the session's stored `model_config` — ran fine on the identical model. Rules: (a) a 403 "not recognized" means the pin spelling/binding is wrong, not the model — retry the exact pin at most ONCE after ≥5 min, then switch the INVOCATION to inherit-route form (drop the flags) and record the switch; never silently substitute a different model; (b) route-death EXIT=1 does NOT mean no work happened — the worker may have completed N nudges and committed BEFORE the failing call (observed: `b0a334d`+`1135499` for one lane, `f37c55e` for another, all committed despite wrapper EXIT=1); always inspect task-branch tips + porcelain before declaring the lane failed; (c) a route can die MID-lane (one worker logged zero route errors through N2, then 403'd on the next call) — per-nudge model-usage logging is what proves which committed work is trustworthy.75. **24/24 watchdog must track EVERY active lane + monitor itself (S12-C1, 2026-09-08).** A v1 watchdog that only watches the first lane's branch tip (e.g. T03B) goes blind the moment the wave advances: W4/T03C stalled ~2h with zero bytes while the log kept printing healthy T03B lines. Shape: v2 loop records canonical HEAD + porcelain + ahead/behind + EVERY active lane tip + ledger count per cycle (5 min), fires `PROGRESS_<LANE>_DONE` on any tip change, and nudges the CURRENT active lane (tip still on old base + no new log >15 min) with the exact owner session. Self-liveness: the watchdog process itself can die silently (`process list` empty, `ps` no match) while its log looks alive — detect by log-mtime freeze across two cycles (>10 min without a new line = dead, re-arm a fresh instance immediately). Nudge cadence: stall >15 min between nudges to avoid quota spam; commit events notify instantly.
76. **Truncated single-fragment worker replies need a structured re-ask, not a retry of the same prompt (S12-C1, 2026-09-08).** An overloaded owner session can return a cut reply (`D`, `R fetch reality...`, `3–C14 ngay.`) with exit 0 — the work did NOT happen, but the session is alive. Do NOT resend the identical long dispatch (it produces another fragment). Instead send a SHORT nudge demanding a fixed reply skeleton in ONE message: RULES_LOADED + branch tip + porcelain + fetch result + prompt-file read confirmation + first file to edit + first test to write. Once the skeleton lands complete, follow with a separate CODE-NOW prompt naming the single first artifact (exact file + exact test name). Two short turns beat one long turn that keeps fragmenting.
77. **`git fetch` object-transfer failure is NOT proof of a stale base — `ls-remote` HEAD equality is ground truth (S12-C1, 2026-09-08).** `git fetch origin <branch>` can fail with `fatal: bad object refs/codex/turn-diffs/...` + `did not send all necessary objects` (remote object-store gap) while `git ls-remote` shows remote HEAD == local cache and interfaces were already aligned read-only with disjoint scopes. Rule: on fetch failure, (a) verify `ls-remote` HEAD vs local, (b) confirm scope-disjointness of the pending corrections, (c) if both hold, post an explicit START authorization recording the fetch error as a remote-store issue (never as stale-base) and let the owner code — do NOT burn turns re-aligning what is already aligned. Record the bad-object string in the evidence log so the reviewer sees it was triaged, not ignored.
78. **Continuous-execution reporting contract for this user (hardened S12-C1, 2026-09-08).** User corrections `xong chưa / đến đâu rồi`, `sao cứ dừng/treo giữa chừng`, `chạy 24/24 / liên tục đi`, `cứ làm theo prompt Codex đi` are FIRST-CLASS: (a) never end a turn on a bare dispatch with no interpretation — every turn opens with lead-with-status (what finished / what runs / ETA table with `date -u` anchor), in Vietnamese, concise tables over prose; (b) report worker EXIT in the SAME turn before verifying further (user-corrected 2026-09-02: silence until asked = perceived stall); (c) `chạy 24/24 / liên tục` = arm the multi-lane watchdog + chain the next DAG lane in the same turn, no per-step permission asks; a mid-turn user ping truncates the drafted reply, so the NEXT reply re-states status first. `m ko nhắc nữa à?` is a QUESTION, never a stop order — only explicit `dừng` stops a recurring loop.

79. **Require workers to bank gate evidence as single-purpose micro-files with sentinel content (S12-C1 W5, 2026-09-08).** A T05 correction worker wrote `s12-t05/SUMMARY.txt` (one line per gate with measured counts) plus one file per gate: `pytest_t03c_regression.txt` (`15 passed, ... in 19.46s`), `ruff_F.txt` (`All checks passed!`), `porcelain.txt`, `diff_check.txt` (`DIFF-CHECK-0`), `tsc.log` (empty = exit 0). Manager verification became six `cat` calls in seconds instead of re-running a 20s suite + tsc + ruff. Rules: (a) put the micro-file manifest in the dispatch prompt (exact filenames + expected sentinel for green); (b) sentinel content must be the tool's OWN success string, never a hand-typed "PASS" (hand-typed PASS is hearsay; `All checks passed!` only exists if ruff printed it); (c) empty-file-means-green applies ONLY to zero-output-on-success tools (tsc, diff-check) — record the exit code alongside; (d) micro-files accelerate, never replace: the manager still spot-reruns the DECISIVE gate (focused pytest) independently once per wave.

80. **Ack-only escalation ladder: ack → micro-commit → MANAGER runs gates → COMMIT-VERIFIED (S12-C2 W6/W7, 2026-09-09).** Several owners (T06A, T06B) acked repeatedly (`TARGET checklist`, `RULES_LO`, `Committing now`, `SHA`) with exit 0 while the worktree tip/porcelain never changed — one-shot `-q` resumes often end after the ANALYSIS turn; the worker never started gates. Escalation that finally landed: (a) 1st ack → verify `git rev-parse HEAD` + porcelain yourself; (b) send a narrow RUN-NOW / COMMIT-ONLY micro-prompt (exact gate commands inline, "KHONG ack suong, CHI bao so that"); (c) 2nd+ ack with a SMALL in-allowlist diff → STOP round-tripping: the Manager runs the gates THEMSELVES read-only in the worker's worktree (pytest + ruff + diff-check — all preimage-safe), then dispatches a COMMIT-VERIFIED packet that says "Manager đã tự chạy gates thật: <exact counts>; việc của bạn CHỈ LÀ: git add <files> + git commit + báo SHA" — a pure 2-command commit-only resume lands first-try. A worker's "Lỗi tool C22"/off-scope error report: send a 4-question CLARIFY (which tool+command, which file, in-scope?, traceback) before believing any self-diagnosis — the T06B "C22 failure" was its own empty `terminal` command (Invalid command: expected string, got NoneType), zero relation to tests.

81. **Model override with quota exhaustion: probe with a REAL 5-token chat completion, not GET /v1/models (S12-C2, 2026-09-09).** `GET /v1/models` returns 200 + the model listed even when the route is dead (CMC weekly 429 `weekly usage limit... resets at <ts>`; deepseek 502 connect timeout mid-dispatch). Before dispatching/retrying after ANY model change or 429/502: POST `/v1/chat/completions` with `{"model":<exact>,"messages":[{"role":"user","content":"ping"}],"max_tokens":5}` using the REAL api_key parsed from config.yaml (never a truncated key — `sk-cff` yields a misleading `invalid_api_key`). Record a MODEL_SWITCH.md (append-only) in the fresh evidence root with: user order, old-model quota evidence + reset timestamp, new model/provider, and "do not silently substitute" — a later user switch-back order still needs re-probing before use (CMC quota may still be exhausted; C2 ended on `ocg/deepseek-v4-flash` provider custom after the switch-back failed 429).

82. **Multiple task packages must collect TOGETHER: same-basename test files + missing `__init__.py` = `import file mismatch` (S12 C2 F11, 2026-09-09).** Five `tests/s12/s12-t0X/` dirs each containing `test_c1_closure.py` (no `__init__.py` in three of them) made `pytest tests/s12/` fail at COLLECTION (`imported module 'test_c1_closure' has this __file__ ... not the same as the test file we want to collect`) while every per-dir run passed — per-dir totals (221) are NOT evidence the suite collects. Fix that Codex demanded and the T03A owner applied: rename to a unique basename (`test_s12_export_c1_closure.py`, git mv keeps history) or add `__init__.py` per package. Manager gate: `pytest tests/<suite>/ --collect-only -q` must list every file with zero ERRORs BEFORE accepting any "N passed" totals; packet language for every wave: "all <suite> tests must collect together; fix import/package naming correctly, no disabling".

83. **Dedicated INT01 integrator transport loop between waves — Manager never touches Git (S12-C2, 2026-09-09).** After each wave's commits are Manager-verified (independent pytest/ruff on the task worktree), dispatch the DEDICATED Git-only INT01 session with an exact transport packet: (1) verify canonical HEAD clean local==remote (live `ls-remote`, never cached ref); (2) merge each verified commit `--no-ff` (conflict → abort + report, no hand-resolution); (3) push non-force; (4) verify `ls-remote == local`; (5) ff-prep the NEXT wave's clean task branches onto the new canonical base so owners patch the current contract (T01-C2 authority must be in W2's base or W2 runs on stale production — explicitly forbidden); (6) report HEAD/remote/branch states + append to the C2 ledger. Manager role = verify + dispatch only; a Manager that committed/pushed canonical directly in an earlier round must formally stop that (recorded role correction), never "take over Git because the API route lacks quota".

84. **Repeated provider flaps during a MULTI-LANE wave: cut concurrency, stagger
    starts, one packet per lane (2026-09-23).** With 7 long worker streams open, the
    upstream provider flapped TWICE in ~50 min and killed every lane both times.
    Signature is easy to misread: the launcher returned **`exit 0`** while its log was
    a ~125-byte payload containing only `API call failed after 3 retries: HTTP 503:
    [<provider>/<model>] [502]: fetch connect timeout (reset after Ns)`. So: gate on
    log CONTENT, never exit code (extends #62/#65). Recovery ladder that worked:
    (a) measure each lane's real footprint before touching anything — per-tree
    porcelain + evidence-file count + whether WIP files exist (three lanes had
    nothing, two had real dirty files); (b) capture byte snapshots of the WIP so the
    resume prompt can state exactly what is already on disk; (c) wait the mandated
    5 min, then probe the route with BOTH `GET /v1/models` and a real 5-token chat
    completion (#81) before re-dispatching; (d) resume the SAME owner session per lane
    — no new owners; (e) **reduce concurrent long streams** (7 → 3 landed clean) and
    **stagger starts ~45 s** so the lanes are not mid-request together. Treat "two
    flaps while N lanes are open" as a load signal, not bad luck: re-dispatching all N
    at once is the blind retry the rules forbid.
    **One packet FILE per lane per round — never a merged packet.** A shared
    `RESUME2-WAVE-A.md` ("read the section matching your Task ID") makes the
    lane↔session mapping UNPROVABLE: all sessions' first user message is byte-identical,
    and this Hermes `state.db` has a `parent_session_id` column but leaves it **NULL**
    for worker rows, so lineage cannot resolve it either (the `[terminal] ran \`…\``
    command echo is a UI rendering and is NOT stored; tool RESULTS echo the packet text
    and poison keyword counts). With per-lane packets, `first-user-message == packet
    head` is a valid proof (see #26). If a merged packet is unavoidable, record the
    launch-order → session mapping from session start timestamps and label it
    `INFERRED` in the ledger — never present it as proven.
    **Verify an isolation fix with a sentinel run, not the worker's word:** to accept
    the BENCH ledger-leak fix, the manager ran the previously-leaking FULL suite
    twice and diffed the protected artifact byte-for-byte before/after (184,680 B /
    422 rows / sha unchanged ⇒ 0 bytes appended). Full runbook:
    `references/provider-flap-multilane-recovery.md`.

## Support files

- `templates/run-task-fresh.ps1` — worker launcher (guard + model + log)
- `templates/subtask-registry-and-packet.md` — copy-paste registry + per-subtask
  TASK.md skeleton + dispatch command for sliced sprints (S11-T01A/B/C/D pattern)
- `templates/watch-task-log.sh` — 10s log sync watcher (UTF-8 LIVE tail)
- `references/s08-a01-manager-verification.md` — post-writer-exit manager
  verification runbook for migration/taxonomy tasks: mtime-window file audit,
  independent migration round-trip (seed-real-rows + PRAGMA column introspect +
  row checksums), >180s pytest in background, screenshot verification,
  protected-hash re-check, MANAGER_VERIFIED_PENDING_* close-out.
- `references/integrated-base-procedure.md` — merging two APPROVED sprint
  trees into one integration worktree (S08-P00 pattern): manifests, copy
  rules, shared-file semantic merge, verification, baseline autocrlf trap,
  MANAGER_VERIFIED_PENDING_CODEX_INTEGRATION_REVIEW close-out.
- `references/sqlite-fixed-bind-json-each.md` — SQLite fixed-bind-parameter
  scalability: JSON1 `json_each()` idiom, capability probe, real-SQL
  `before_cursor_execute` verification harness, and the
  `contextlib.suppress(Exception)` flaky-counter pitfall (S08-A02-C5→C6).
- `references/sprint-slice-subtask-decomposition.md` — splitting an oversized
  task into formal subtask IDs with per-subtask owning sessions, DAG wave
  dispatch, session registry, model-pinned lanes, read-only reviewer lanes,
  global-gate mutex, and close-out vocabulary (S11-T01 pattern).
- `references/readiness-docs-lane.md` — docs-only readiness waves between
  sprints (S11-P02 pattern): A∥B∥C audit lanes + D synthesis against a moving
  baseline, per-lane prompt skeleton, manager spot-check checklist, symbol-name
  anchoring, MEASURED/PROPOSED/UNKNOWN discipline, terminal-state vocabulary.
- `references/hermes-cli-dispatch-and-owner-transfer.md` (in
  `pm-worker-orchestration` skill) — Hermes-CLI worker dispatch: `-q`
  FLAG-ORDER trap (`-q -Q` ⇒ exit 2, no session) + argv-list launcher
  (`templates/hermes-lane-launch.py` in that skill), per-lane differentiated
  resume after a shared upstream death, cross-lane typed-error SUBCLASS ruling,
  and pre-code node-inventory freeze with independently re-hashed worker claims.
- `references/manager-verify-and-correct-workers.md` (in `pm-session-execution`
  skill) — post-exit triage of incomplete/crashed workers: DONE criteria,
  independent verification recipe, owner-session discovery via state.db,
  correction-resume dispatch, parallel-writer interference protocol.
- `references/full-sprint-runbook.md` — running a WHOLE sprint end-to-end in
  one manager session under full-sprint authority: wave DAG execution
  (I01∥I04 → I02∥I03 → I05 → resume-owner T01 → serial T02..T06), per-task
  TASK.md packet template with frozen thresholds + allowlist + FORBIDDEN
  block, registry update rhythm between waves, silent-death/resume loop,
  and the ETA-reporting pattern for the user (S09 run, 2026-08-23→24).
- `references/s09-full-sprint-session-log.md` — S09 concrete record backing
  pitfalls 56/62/65–71: task ledger with owner sessions + corrections +
  gate evidence, silent-death counts, final-gate FG1/FG2 root causes, and
  user-interaction notes.
- `scripts/openapi_param_leak_probe.py` — runnable OpenAPI parameter-leak probe
  (pitfall 40): scans /openapi.json for forbidden client-controlled query
  params (e.g. workspace_id); exit 0/1 doubles as correction evidence.
- `references/playwright-harness-corrections.md` — S07 round-2 detail:
  os.execv orphan fix shape, dual-project state-bleed detection/fix,
  canonical-config-first rule, correction dispatch prompt structure,
  manager verification battery ordering, dependency-blocked parallel
  pattern (pitfalls 43/44/46/47/48), cited-by-verdict allowlist extension
  + temp-SQLite FK gate recipe (pitfalls 49/50).
- `references/keepalive-reminder-watchdog.md` — cron keepalive watchdog for
  a stalled manager/worker session (pitfall 72): working .py script,
  resume-model pinning, log-buffering quirks, no_agent + deliver rules,
  FreeUsageLimitError triage, report format with nudge-time column.
- `references/mid-sprint-model-switch.md` — mechanical mid-sprint worker
  model switch (S12-C1, 2026-09-08): audit live consumers, kill loops not
  writers, backup-chained dispatch patching, append-only MODEL_SWITCH.md
  errata, watchdog restart verification, switch-back handling.
- `references/provider-flap-multilane-recovery.md` — MULTI-LANE wave recovery
  from repeated upstream 502 flaps (2026-09-23): the `exit 0` + 125-byte log
  signature, WIP blast-radius measurement, snapshotting, the wait/probe/resume
  ladder, the 7→3 concurrency + 45 s stagger fix, why a merged resume packet
  makes lane↔session mapping unprovable (`state.db.parent_session_id` NULL for
  worker rows), the sentinel-run acceptance technique, and the worker-claims-vs-
  disk-truth gate traps.

## Related

Project-specific rules (protected data hashes, MotionForge paths, notification
contracts) live in `motionforge-autopilot`. Generic Windows/terminal discipline
in `terminal-engineering-discipline`.
