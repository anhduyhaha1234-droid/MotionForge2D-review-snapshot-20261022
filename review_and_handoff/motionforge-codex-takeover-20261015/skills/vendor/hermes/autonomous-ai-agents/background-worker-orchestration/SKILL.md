---
name: background-worker-orchestration
description: Use for long-running CLI agent worker background processes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [orchestration, background-process, workers, cli-agents, verification]
    related_skills: [terminal-engineering-discipline, claude-code, codex]
---

# Background Worker Orchestration

Use when launching long-running CLI agent workers (`hermes chat --query`, or
similar one-shot CLI agents) from PowerShell/bash scripts as background
processes, then monitoring, verifying, and handing them off for review.
Proven on Windows with the Hermes desktop daemon running (2026-08).

See `references/`: dispatcher-dryrun-safety.md, output-ceiling-truncation-fix.md (truncation death loop → `HERMES_MAX_TOKENS`), detached-spawn-and-stop-order.md; stall-kill-pipe-hang.md (launch-pipe hang → Start-Process).
See `references/launcher-and-session-ops.md` for copied-toolkit path sweeps before the first dispatch, duplicate-dispatch recovery (two sessions, one write-set) with append-only incident logging, the PowerShell `$pid` read-only trap that silently stops nothing, `exit 1` = "no final response" with the work fully landed, liveness on the resolved session id (never the `--resume` parent), and cap enforcement by counting live chains.
See `references/verifying-a-new-lane-without-baseline.md` for a NEW task whose write-set was empty at
capture (no pre-dispatch manifest, guard crash on the missing file, the self-manifest schema-first +
mtime-sweep + tree-pin recipe, the "verifier compared 0 items and printed PASS" trap, and how to bring a
wave back under the concurrent-stream cap without losing work).
See `references/monitoring-and-finish-runs.md` for the receipt-aware watchdog (DONE vs STALL),
lane-name normalisation for active-writer sets, and the *finish packet* pattern for a worker that
stopped on turn budget rather than on error.
See `references/success-signals-and-phantoms.md` for fake-success signals (a pipe masking the real exit code, flap vs
budget), the read-only *confirmation run*, and the phantom guard failures with their fixes.
See `references/duplicate-session-and-dispatch-chains.md` for the `sleep N && append && launch` trap that
creates TWO live sessions for one packet, PID-scoped duplicate remediation with the zero-collateral pid diff,
the receipt/log name-collision disclosure, and sweeping hard-coded run-root paths out of copied tool sets.
See also `independent-evidence-verification` → `references/git-truth-and-liveness-signals.md` for proving an integration
transport's content with blob ids (never worktree bytes under `core.autocrlf`), accepting an **authorized HEAD advance**
(`git merge-base --is-ancestor`) instead of calling it drift, and re-using an external reviewer's probe safely.
See `references/flap-resume-cycle.md` for the 502/503 resume loop: the log-SIZE discriminator
(~125 B = pure transport flap, prose tail = turn budget), the ≥5-minute wait encoded inside the
background launch command, measuring what a resume actually wrote before assessing loss, and
per-cycle packet/round labels so the provenance resolver stays unambiguous.

## Launch pattern (Windows)

- Write a `.ps1` launcher: `$repoRoot`, `$logPath`, `$prompt` (here-string),
  `Set-Location $repoRoot`, then
  `& hermes chat --query $prompt --source cli --max-turns 300 --provider custom --model ocg/deepseek-v4-flash --pass-session-id --checkpoints 2>&1 | Tee-Object -FilePath $logPath -Append`.
- Launch with `terminal(background=true, notify_on_complete=true)` — the
  notify is how you learn the worker exited.
- ALWAYS verify the launcher BEFORE launching: PowerShell syntax via
  `[System.Management.Automation.Language.Parser]::ParseFile(path,[ref]$null,[ref]$errs)`
  (OK when `$errs.Count -eq 0`), then confirm the spawned process is alive.
  From git-bash the `$vars` must be backslash-escaped and the AST dump
  silenced, else the check's own output floods the terminal (verified
  2026-08-19):
  `powershell -NoProfile -Command "\$errs=@(); [System.Management.Automation.Language.Parser]::ParseFile('C:\…\run-<task>.ps1',[ref]\$null,[ref]\$errs) | Out-Null; if(\$errs.Count -eq 0){'PS_SYNTAX_OK'}else{'PS_SYNTAX_ERROR '+(\$errs.Count)}" 2>/dev/null`
  and `bash -n watch-<task>.sh && echo SH_SYNTAX_OK`. pytest does NOT apply
  to `.ps1`/`.sh` orchestration files (it only collects `test_*.py`) — native
  syntax + process-alive smoke is the correct gate, and running pytest in the
  worktree while the writer is active would race its in-flight runs.

## CRITICAL: worker cwd does not inherit Set-Location

When the Hermes desktop daemon is running, a `hermes chat` CLI session may
execute with the DAEMON's cwd, not the script's `Set-Location` — verified
disaster: worker wrote task files into the wrong repo while reporting
SUBMITTED. Prevention:
1. Put an explicit workdir guard INSIDE the prompt: "run `pwd` and
   `git rev-parse --show-toplevel` before ANY write; if wrong, `cd` to
   `<absolute expected root>` and re-verify; if toplevel differs, write
   nothing and report BLOCKED: WRONG_WORKTREE".
2. After launch (~60s), check `git status --short` in BOTH the expected
   worktree AND the main repo; a changed main tree means the worker is
   misplaced — kill it.
3. After exit, diff mtimes of changed files to attribute them to the right
   task window (pre-existing changes from earlier tasks are fine).

## Launcher prompt: keep it SHORT (verified 2026-08-05)

A 6–8KB `--query` string inside the `.ps1` here-string breaks
bash→PowerShell→hermes argument parsing: quotes/backticks get swallowed and
hermes exits 2 with `error: unrecognized arguments: <text after first quote>`
(NativeCommandError). Symptom: log contains only the prompt echo, no
"Initializing agent", wrapper exits 2 fast. Fix: keep the launcher prompt
SHORT (<2KB) = hard worktree guard + "read packet files
`docs/pm/sessions/<TASK>/TASK.md` and `START_PROMPT.md` completely and follow
exactly; stop at SUBMITTED". The packet carries the full contract — never
inline the whole task spec into the prompt.

## Never launch the same launcher twice; verify the REAL worker PID

- The wrapper PID you get from `terminal(background=true)` is `powershell.exe`;
  the REAL worker is `hermes.exe` + `python.exe` with `chat` in the CommandLine.
  A wrapper that exits fast with a growing log file = worker is alive under a
  different PID — check before relaunching.
- Running a SECOND instance of the same launcher while the first runs → both
  `Tee-Object -Append` to the same log → IOException file lock, and you can
  kill the healthy worker. Test a new launcher once in foreground ONLY if no
  background instance of it exists; otherwise verify syntax + process and
  launch once.
- Check for live workers with:
  `Get-CimInstance Win32_Process | Where-Object {$_.Name -match "hermes|python" -and $_.CommandLine -match "chat"}`

## Live visibility (users see NO chat window for CLI workers)

Users following on the Hermes desktop see "nothing running" — give them a
watcher:
- Copy the worker log into a folder they watch; hermes logs are UTF-16LE, so
  produce a UTF-8 tail: `iconv -f UTF-16LE -t UTF-8 "$SRC" | tail -300 > LIVE.txt`.
- Run a silent background watcher (no notify — it never exits):
  `while true; do cp -f "$SRC" dst; iconv ... ; sleep 10; done`
- `open_preview` the LIVE.txt (auto-refreshes) + `focus_pane('sessions')`.
- Kill the previous task's watcher when that task ends; keep QA servers
  (backend/frontend dev) alive for the reviewer and say so in the report.

## Exit banner parsing — exit 0 is NOT completion

Read the worker's final output:
- `Resume this session with: hermes --resume <SESSION_ID>` → capture the ID.
- `Iteration budget reached (N/N) — response may be incomplete` → the worker
  hit max-turns; verify the claimed artifacts exist on disk (REPORT=SUBMITTED,
  baseline Run ID) and re-run any missing gates yourself. A baseline run that
  completed BEFORE the cutoff can still be valid — check its Run ID exists.
- Never trust worker self-reports: run the manager pytest set independently
  (`-q -p no:cacheprovider` + distinct `--basetemp` so you don't race the
  worker's own pytest runs or `.pytest_cache`).

### The iteration cap: `hermes -z` exits 0 with ZERO deliverables (verified 2026-09-17)

`hermes -z` runs a bounded tool-calling budget — `agent.max_iterations`,
**default 90 per run** (`agent/agent_init.py`). There is **no env override**, and
`agent.max_turns` in `config.yaml` is a *different* setting that does NOT raise it.
On hitting the cap the worker is fed a synthetic turn —
`You've reached the maximum number of tool-calling iterations allowed. Please
provide a final response summarizing what you've found…` — writes a confident
summary, and **exits 0**.

Observed on one lane (MF-V1-GOLDEN round 1), all of it invisible in the exit code:

- Receipt read `exit_code: 0`, `duration 2171s` — indistinguishable from success.
  The log tail ended with a tidy self-authored status block naming its own
  remaining steps, which reads like a deliberate, honest stop.
- **Nothing was delivered:** EV evidence dir empty (0 files), task worktree
  `git status --porcelain` = 0, no guard run, no commit.
- Yet **195 files of real work** sat in the worker's own runtime dir (fixture,
  annotations, ledger, 18 tools). The lane was ~90% done and 0% delivered.
- **The log does NOT announce the cap.** The only tell is in session history:
  `select role, substr(content,1,120) from messages where session_id=? order by id desc limit 5`
  against `file:<…>/state.db?mode=ro`. The synthetic `user` row naming the cap is
  the proof. Never conclude "the worker chose to stop" without checking this.

**Rule: exit 0 is not completion — verify every deliverable path on disk** (EV
files, allowlist files, guard report, commit) before reporting or gating. A
worker's own status prose is a self-report even when it is scrupulously honest.

**Fix the packet, not the worker.** A broad packet — many required-reading docs,
many outcome sections, many acceptance rows — burns 90 iterations before reaching
finalization. Two moves:

1. **Continuation rounds stay narrowly scoped**, sized so the *remainder* fits one
   budget. Send only: Manager-verified verdict on round 1, what is already
   accepted (with an explicit "do not re-open or re-derive this"), the exact
   outstanding steps, the unchanged write set, and the gates required to emit
   `TASK_SUBMITTED`. The session's history already holds the full contract —
   never re-send it.
2. **Put packaging/evidence steps FIRST in a broad packet**, or split them into
   their own round, because they are what gets starved. This lane spent its whole
   budget on analysis and never reached the deliverables.
3. **Harvest the lane's OWN remaining-command list from its log tail and paste it into the
   finish packet** (verified 2026-09-24). A budget-exhausted worker usually ends with an honest
   numbered block — "còn lại: (1) chạy script X, (2) pytest Y, (3) commit, (4) viết REPORT" plus
   the literal commands. That block is a better packet than anything you can reconstruct: turn it
   into the packet's numbered steps verbatim, add the report shape and the budget
   ("closing run, not a redesign — ~45 turns"), and tell it explicitly the run ended on BUDGET,
   not on an error, so it does not re-litigate its own design. Two lanes closed their whole
   remainder this way in one resume round each.

`--resume <sid>` mints a NEW session id for the continuation turn (see
`independent-evidence-verification` §4). That is safe **only** after confirming
the prior process actually exited — check the receipt `exit_code`/`ended_at_utc`
before dispatching, so exactly one writer ever exists on the worktree.

### Two near-zero-information deaths, two OPPOSITE recoveries

`exit 0` cannot distinguish them, so triage from **log size + state.db** before
acting. Both hit the same lane family on 2026-09-17:

| | iteration cap | connection error |
|---|---|---|
| receipt | `exit 0` | `exit 0` |
| log | normal size, ends with a coherent self-authored status block | **tiny** — observed **52 bytes**: `API call failed after 3 retries: Connection error.` |
| state.db tell | synthetic `user` row *"You've reached the maximum number of tool-calling iterations…"* | no cap row; the message count simply stops |
| artifacts | often ~90 % of the work landed in the worker's runtime dir; the deliverables starved | may have landed partial edits (tool patches already returned success) or nothing |
| correct response | **shrink the packet** into a narrow continuation — the budget was the problem | **resume the same packet unchanged**, after the 5-minute wait |

- A tiny log is the fastest discriminator: the cap path ALWAYS writes a long
  summary, because the synthetic turn explicitly asks for one. So never read
  "exit 0 + tidy final prose" as a deliberate stop, and never read a tiny log as
  "nothing was done" — that lane had already applied its patches.
- Connection-death recovery is RULES §7 verbatim: **report at the first failure,
  wait a full 5 minutes, then resume the SAME session/model/provider/api-mode/
  scope/write-set** — no model switch, no new owner, no hot-looping. A long-lived
  manager session can hold a connection error for minutes (see the frozen-manager
  diagnosis in the watchdog section) — give it that window before intervening.
- Do not reach for a **continuation packet** as the reflex fix for every
  non-delivery. The cap needs one; a connection death does not, and handing
  "here is what you already did, don't redo it" to a session that merely lost its
  connection forecloses it finishing its own plan.

### A worker's DETACHED child dies with the worker (verified 2026-09-17)

When a worker spawns its own long batch as a background/detached process and tells
you it is "running in background (PID N)" while it ends its turn, that child is
**not** independent — it dies with the worker. Observed: a lane launched a
120-frame × 7-window sweep, reported the PID and log path, ended at the iteration
cap, and the sweep froze part-way through the 5th window. The lane's plan
("when the sweep finishes, run assemble/report/acceptance") could never execute,
because nothing survived to poll it.

- **Rule for packets: require remaining work to run SYNCHRONOUSLY.** Say it
  explicitly — "run the remainder as one foreground command (or at most two), do
  NOT spawn a detached process you then have to poll; that is what killed the
  previous round." A lane will otherwise reach for `Popen`/`start /b`/`&` to dodge
  its own turn budget, and you lose both the work and the budget.
- **`exit 0` hides this.** The sweep's death is invisible in the receipt; the lane
  even reported the plan honestly. Only the artifacts show it: partial windows,
  no assembled output, no commit.

#### Telling a dead detached child from a live one — TWO-POINT SAMPLING

A single "recently modified files" count is **not** a liveness test and gave a
false ACTIVE reading this session: `find <runtime> -type f -newermt "-4 minutes" | wc -l`
returned **183** — impressive-looking, but those files had simply been written
moments *before* the child died, and the window was still catching them.

The reliable test is a two-point sample of BOTH counters:

```
A=$(find "$R" -type f | wc -l);  L1=$(wc -c < "$R/sweep.log")
sleep 45
B=$(find "$R" -type f | wc -l);  L2=$(wc -c < "$R/sweep.log")
[ "$A" = "$B" ] && [ "$L1" = "$L2" ] && echo STALLED || echo ACTIVE
```

- File count catches media writers; log size catches everything else. Require
  **both** flat across a ≥40 s gap (seconds apart lies — buffered writers fake a
  freeze, and an active writer can pause between windows).
- Corroborate with the process table filtered by the child's cmdline marker, and
  with "how many windows did the log actually finish" (grep the per-window summary
  lines) — that count is your real progress, and it is what the continuation packet
  must state so the next round does not redo completed windows.
- Recover by resuming the **same** owner session with a finishing-only packet:
  name what already landed and is accepted, list only the remaining windows, and
  require a single synchronous run plus the commit. Accept the partial round as
  real work — the measured results it produced are valid and reusable.

## Per-task session tracking (for reviewers)

Users ask for "one session per task" so a reviewer can resume each. Keep a
tracking file (e.g. `output/SPRINT_Sxx_SESSIONS_TRACKING.md`) with columns:
Task | Worktree | Session ID | Model | Started | Finished | Manager Verify | REPORT.
Append manager verification evidence (exact pytest commands + counts) under it.

**The registry is the handoff document — it must survive multi-round lanes.** Once a lane
runs R1 → R2 → R3, the row has to carry the whole lineage and the reason for each hop, or
the reviewer cannot tell a recovery from a second writer:

- Put the **lineage in the Session-ID cell** (`R1 sid → R2 sid → R3 sid`) and end the row
  with the round's terminal state, not just "RUNNING".
- Add a per-task **round-history table** below the main table: one row per round with
  session, packet filename, and the *measured* outcome (numbers, not adjectives). Each new
  round appends a row; the compact session-history slot in memory is not a substitute.
- **Keep a per-task "manager-reproduced defects" list with the exact values**, so the
  continuation packet and the final review packet quote the same numbers. When a defect is
  closed, move it to the round-history row rather than deleting it — the closure is part of
  the evidence.

**Do not build that table with repeated in-place patches.** Inserting a section into the
MIDDLE of a Markdown table silently orphans every row below the insertion point: the table
splits and the trailing rows render as stray text. This cost three corrective patches plus
one duplicated table with the wrong contents on a `SESSION_REGISTRY.md` this session.
Rules: to **add a row** anchor on the table's LAST row; to **add a section** anchor on the
line after the whole table (or its heading), never on a line inside it; for a small doc you
are restructuring more than twice, stop patching — `read_file` it whole and `write_file` it
once. After any patch touching a table, re-read the region and confirm the row and column
counts are unchanged (a mangled table still passes lint, and ATS/lint will not catch it).

## Verifying non-Python artifacts in a turn

If the changed files are `.ps1`/`.sh`, a gate demanding pytest will loop —
pytest only collects `test_*.py`. Verify natively:
- `.ps1` → `Parser.ParseFile` (syntax)
- `.sh` → `bash -n file`
- functional: launcher → spawned process alive with right cmdline; watcher →
  diff its output vs source stable tail (a 10s-poll watcher trails the live
  source; compare `tail -280` after one poll cycle, not the full file)
- watcher diff vs LIVE source ALWAYS mismatches on fast-growing logs (source
  outruns the 10s poll). Correct method: capture `tail -300` of the source at
  T0 into a temp file, sleep one full poll cycle (12s), then diff that T0
  capture against the DST tail — a healthy watcher equals the T0 snapshot
  exactly one cycle behind. Diffing against the live source at any other
  moment proves nothing.
- then pytest the Python workspace to prove nothing broke, and state plainly
  that pytest does not apply to .ps1/.sh.

## Dispatch a dedicated MANAGER session (BA pattern, verified 2026-08-21/22)

When the user makes THIS agent the review gate ("BA") while a separate
session manages the work: dispatch a dedicated Hermes MANAGER session, not
just workers.

- Write the FULL management contract to a temp `.txt`, structured in order:
  rules-file pointer first line (+ required `RULES_LOADED` ack before any
  action), authority split (Manager orchestrates only / Workers code in
  allowlists / BA reviews only), current verdict with concrete evidence
  paths, authorized scope IN/OUT, workspace guard (branch/HEAD pin, forbidden
  git ops, protected hashes, DB guards), worker-model block, task map (each
  finding → Task ID → exact owning session → outcome → exclusive write
  allowlist → acceptance criteria), wave ordering with dependencies,
  heartbeat cadence + 8-min liveness audit + 5-min connection-error retry
  rule, and the terminal condition
  `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_<REVIEWER>_REVIEW`.
- Launch it exactly like a worker (file-loaded `-q`, background +
  notify_on_complete, tee to an evidence log). It then preflights, composes
  worker resume prompts, monitors, verifies, and appends packets itself —
  never run a second owner for the same lane alongside it.
- Division of labor the user expects: BA reads logs/PIDs/packets, runs
  isolated verification, returns findings + the next manager prompt in chat;
  the USER (not BA) triggers the external final reviewer (Codex) when BA
  declares clean. BA never self-writes APPROVED/CLOSED.
- Long prompts ARE safe when loaded via bash `PROMPT=$(cat file)` + quoted
expansion (7.9KB contract dispatched flawlessly); the <2KB rule applies to
PowerShell here-string launchers only. **Never inline resume text through
`-q "$(printf '…')"`**: any quote/apostrophe inside the printf payload kills
bash with `unexpected EOF while looking for matching '` at exit 2 BEFORE hermes
starts — no log append, no EXIT marker, session untouched, trivially misread as
a completed dispatch (verified 2026-08-25, one resume round lost). Always write
the correction/resume text to a `.txt` packet and launch with `-q "$(cat …)"`.
- **Even `-q "$(cat <packet>.md)"` is NOT reliable for multi-line Markdown
  packets — prefer a Python argv launcher (verified 2026-09-16, S12-R7).**
  `hermes chat -q -Q -r <sid> … "$(cat packet.md)"` inside a compound `&&`
  chain died INSTANTLY for BOTH lanes with
  `hermes chat: error: argument -q/--query: expected one argument` (exit 2, not
  one byte from hermes) while the identical packet dispatched cleanly through a
  Python launcher. Robust form: `scripts/hermes_worker_launch.py` — it passes an
  argv LIST to `subprocess.run` (never `shell=True`), so there is no quoting, no
  `$(...)` expansion and no argument-length ceiling, and each attempt logs
  prompt-path/bytes/cwd/session/model/provider plus UTC start/exit. Two
  mechanical traps it also avoids: pass **Windows-native `C:/...` paths** (an
  MSYS `$VAR` such as `"$A/launch.py"` reaches python.exe as `C:\c\Users\...` →
  `[Errno 2] No such file or directory`), and launch it with
  `background=true, notify_on_complete=true` so the exit notification wakes the
  manager turn. Prove the path once with a throwaway probe dispatch
  (`Reply exactly with the token: X` → require the literal token) before spending
  the real packets: it validates flags + route + launcher in one ~2-minute run,
  and that probe session stays separable in state.db afterwards.
- Acting as the reviewer gate itself? Follow
  `references/ba-sprint-review-contract.md` (five-part output, verdict
  shortcuts, cross-task defect attribution, fail-open test grep list).

## Codex-packet lane takeover — Hermes owner transfer + readiness gate (S12 R6, verified 2026-09-15)

When an external packet (Codex) transfers existing task IDs onto Hermes owners on a pinned
model (`ocg/deepseek-v4.1-flash` / provider custom / fallback OFF) and asks for correction
lanes, follow `references/hermes-lane-takeover-s12r6.md` (exact commands, prompt template,
guard recipe, pitfalls). Core rules:

1. **Quiescence = 3 independent signals before trusting "idle/notLoaded" headers**: mtime scan
   (`find <worktree> -newermt "6 hours ago"`), lock scan (worktree + `.git/worktrees/<name>/`),
   and a `Get-CimInstance Win32_Process` cmdline scan for processes referencing the worktree
   paths. Empty on all three + no cron + no existing Hermes registry record → transfer is legit;
   record the evidence in OWNER_TRANSFER.md.
2. **Byte guards BEFORE readiness probes** (allow + protected manifests per lane), then verify
   with NO `--allow-change` AFTER readiness — the readiness gate is only proven zero-write if
   the guard says VERIFIED.
3. **Readiness probe first (new session, strictly non-writing: 7 fixed read-only commands +
   READINESS_OK marker), then resume the SAME session for the work turn** (`-q -r <session_id>`).
   New task = new session; corrections = resume exact owner. 5/5 probes returned real tool
   output + self-reported session ids.
4. **Model-route proof before the first write**: catalog probe (`/v1/models` exact ID) + one
   live PROBE_OK inference + adapter gate check — Hermes emits NO reasoning/effort field for
   non-OpenRouter base URLs (`_supports_reasoning_extra_body()` = False), so an unsupported
   `reasoning_effort: max` in config never hits the wire. Pin `-m/--provider` on EVERY dispatch
   and resume; never rely on profile defaults.
5. **Heartbeat turn-waker for gateway-off desktop chats**: cron heartbeats don't deliver to
   desktop chat — arm `sleep 1140; <collector.ps1>` as terminal(background=true,
   notify_on_complete=true); each completion notification wakes you for a poll+report turn,
   then re-arm. Collector writes per-lane console size/mtime/tail + live `chat -q` PID count
   to HEARTBEAT.md (template inline in the reference file).

## Two-Manager split with a single ownership-transfer gate (S12-R7, verified 2026-09-16)

When one review splits work across TWO manager chats (`…-MANAGER-A-…` /
`…-MANAGER-B-…`), each owning different Task IDs in the same wave. Full record:
`references/two-manager-export-wave.md`.

1. **Establish which Manager YOU are before writing anything.** Nothing hands you
   your own session id. Read the session DB (read-only) and find the session whose
   rows hold YOUR tool results:
   `SELECT rowid, session_id, role, substr(content,1,80) FROM messages ORDER BY rowid DESC LIMIT 8`.
   Rule out same-day probe/smoke sessions (one candidate was only a
   `Reply exactly: <TOKEN>` route probe). Then record the id in YOUR OWN registry.
2. **Ownership transfer must be proven acknowledged, not assumed**, before your
   first write turn: read the OTHER manager's own registry file (read-only) for the
   relinquishment statement naming your lanes, AND cross-check its live newest
   messages in state.db show work on its own lanes only. Never edit the sibling
   manager's registry — put your id where the user can bridge it across.
3. **Coordination output is per-manager, never shared**: separate evidence root
   (`outputs/<wave>/<UTC>/A/…` vs `…/B/…`), separate runtime root, separate
   registry. Each Manager writes only its own.
4. **Two owners, two lanes, one wave is fine when**: write-sets disjoint, public
   interfaces unchanged, runtime (DB/temp/port/output) isolated, and the wave-base
   sync proven conflict-free by construction —
   `git merge-base --is-ancestor <lane_head> <candidate>` TRUE for every lane ⇒ the
   sync is a pure fast-forward. The WORKER performs the ff inside its own worktree;
   the Manager still forbids `reset/clean/stash/rebase/force` and conflict
   resolution.
5. **Inventory-freeze gate before any code turn**: each owner submits exact
   executable node IDs, parameter IDs per variant, expected typed status plus
   all-row/file deltas, new-vs-existing nodes and raw destinations; the Manager
   freezes that into coordination docs. This is where you learn a file must be NEW
   while you can still demand proof it is absent.
6. **A simultaneous upstream 502 hits EVERY lane at the same second** — audit each
   lane's state individually before resuming, because one lane may already have
   completed the step the other never started (observed: VAL's ff-sync had landed,
   RETRY's had not ⇒ VAL's resume is a no-op `Already up to date`, RETRY's must
   redo). Temporary connection class ⇒ `RUNNING_RETRY_WAIT`: report at the first
   failure, wait the full 5 minutes, curl the gateway, then resume the SAME
   owner/model/provider/api-mode/scope. Fallback OFF, no new session.
   **A local-gateway HTTP 200 (curl `/models`) does NOT prove completions
   recovered** — the upstream can flap while the local gateway answers instantly.
   Gate every resume on a live inference probe
   (`hermes chat -q "Reply exactly: PROBE_OK" … ` under `timeout`): healthy ≈
   20–25 s; a hang/timeout means still down → wait and re-probe instead of
   burning a resume. Flap cadence observed (2026-09-16): deaths ~17 min apart,
   each wave costing 5–10 min; budget ETA buffers accordingly. Full recovery
   mechanics (console RESUME markers, death-time triage, continuation nudge
   template, incident-doc waves): sibling skill `pm-worker-orchestration` →
   `references/gateway-502-mass-resume-cycle.md`.
7. **Stale completion notices mislead**: an OLD superseded dispatch's
   `notify_on_complete` fired ~30 min late and looked like a fresh lane death.
   Triage by the notifying process's OWN log (`turn1_run.log` vs `resume1_run.log`)
   plus a fresh state measurement — never by the notice alone.
8. **Every recovery write keeps the audit trail**: append-only command ledger
   (executable, argv, cwd, UTC, duration, exit, evidence path), an incident file
   for the 502 with per-lane before/after state, and explicit "no production/test
   file was written" evidence (porcelain counts + unchanged HEADs).
9. **Report the ETA slip, don't hide it**: when the user asks "bao giờ xong" after
   a stall, lead with measured status, give the ETA table (plan vs buffer, anchored
   to the live `+07` clock), then a section naming the previously-promised ETA, the
   concrete cause, and why it is a TIME slip not a quality slip (0 files written, 0
   partial patches, guards green). Never wait to be asked.

## Heartbeat watchdog so stalls page you (verified 2026-08-21/22)

For multi-hour unattended stretches run
`scripts/heartbeat_watchdog.py [manager_pid]` via
terminal(background=true, notify_on_complete=true) instead of relying on
manual polls or user pings:

- Configure WORKTREE/WATCH_GLOBS at top: manager log, every worker-lane log
  dir, packet LOG.md/REPORT.md files. Polls every 60s printing
  `HEARTBEAT_OK newest=<file> age=<n>s`.
- Exit conditions: `STALL_ALERT` when nothing advanced >480s (matches the
  8-min liveness-audit rule), `DONE manager_exited` when the manager process
  disappears, healthy self-expiry ~3h (`TIMEOUT`).
- Treat expiry notifications as HEALTHY — re-arm a fresh instance. Only
  STALL_ALERT / manager_exited is your wake-up call to audit.
- **A DB-row/log-sampling watchdog FALSE-ALARMS on any lane that has already EXITED**
  (verified 2026-09-24). A finished lane's `messages` count is frozen and its log stops
  growing, so once the stall window elapses every normal exit reads as `<-- STALL`. Observed:
  the flag fired on a lane whose launcher receipt, tidy log tail, commit and guard report all
  already existed — the "stall" was the Manager's own verification time. Two fixes, both needed:
  1. **Receipt = DONE.** Before flagging, treat `manager/receipts/<lane>.json` existing as
     terminal for that lane and tag the line `DONE(exit, not stalled)` instead. Keep the
     per-lane receipt filenames in the watchdog config.
  2. **A stall flag is a prompt to investigate, never a finding.** Triage in this order:
     receipt (`exit_code`, `ended_at_utc`) → log tail → evidence-file mtime. Only a lane with a
     LIVE process, frozen rows AND no receipt is a real stall; report the retraction explicitly
     when it was one of your own monitoring artifacts.
- **Watch the MINTED continuation session ids, never the requested parents.** `--resume <parent>`
  mints a NEW session id, so a watchdog pointed at the parent watches a session that will never
  receive another row — it reads as permanently frozen while the resumed worker is busy. Resolve
  parent→actual first (first-user-message == own packet head), put the ACTUAL ids in the watchdog,
  and RE-RESOLVE after every resume round; a stale id list is the most common source of a false
  STALL_ALERT.
- **Re-derive the lane→PID map by cmdline at every liveness check** (`--resume`, the lane's tree
  name), never from a list captured hours earlier: completed lanes leave dead pids in your notes,
  and every later check then reads "worker gone". Also note a freshly-launched lane spawns a bash
  wrapper + `hermes.exe` + two `python.exe` per lane — pick the pair whose CreationDate matches the
  dispatch second.
- **Kill the previous watchdog instance BEFORE re-arming with a new
  threshold** — an already-running instance loaded the old code at start and
  keeps firing DUPLICATE STALL_ALERTs at the old threshold (two false alarms
  hours apart on S07, 2026-08-22, from a forgotten 480s instance after a
  900s one was armed).
- A lane inside a LONG legitimate test run freezes its own worker LOG far
  beyond 8 min while progressing in the RUNNER's output (real-vertical
  Playwright: 1.3h incl. webServer boot + orphan-race cleanup). For such
  lanes add the runner artifacts to WATCH_GLOBS (Playwright stdout log,
  `frontend/test-results/.last-run.json`) or raise the stall threshold ≥900s
  — else every long E2E run pages you as a stall.
- Frozen-but-alive manager diagnosis: sample `Get-Process -Id <pid>` CPU twice
  ~20s apart (flat = blocked on a model call — reasoning-max routes can hold
  minutes); check `C:/Users/Admin/AppData/Local/hermes/sessions/request_dump_*.json`
  mtimes for a fresh dump proving a provider connection error. A manager whose
  prompt embeds the 5-min retry rule WILL self-heal (observed: frozen
  18:59 → resumed 19:14 with zero intervention) — give it that window before
  touching anything.
- No-agent cron watchdog that NUDGES stalled lanes itself (S11-C1, 2026-09-04).
  When the user demands a watchdog that "tu chay lai, bat lai khi bi dung"
  without another chat session burning context: `hermes cron create --no-agent
  --script <name>.py` — the script IS the job, stdout silent unless action is
  needed (empty stdout = no delivery). The script checks per lane: dispatch-log
  mtime + branch tip + owning-session last-active. STALL requires BOTH log
  frozen (>30 min) AND session quiet/absent — either signal alone lies
  (buffered `-Q` logs, resume-time compression grace). On stall it sends a
  DETACHED nudge into the EXACT owning session — `hermes chat --resume <sid>
  -m <model> --provider <provider> -q "<short status-now-then-continue>" -Q`
  spawned with DETACHED_PROCESS|CREATE_NO_WINDOW, stdout to a per-nudge log —
  never a new worker session. Cap nudges per tip (2); past the cap, escalate
  as BLOCKED instead of nudging forever. Pin `-m/--provider` explicitly on the
  nudge; never rely on global defaults.

## Periodic keep-alive nudge for a stalled MANAGER session (cron no_agent, verified 2026-09-04)

When a MANAGER session keeps silently stopping and the user asks for an
autonomous reminder ("mỗi 30 phút nhắc nó: tiếp tục làm việc đi" — every 30 min
until told to stop): a no-agent cron job whose script sends the nudge INTO the
existing session (never a new one) is the cheapest mechanism. Known-good
script: `templates/cron_keepalive_nudge.py`.

- **`hermes chat --resume <sid>` WITHOUT `-m/--provider` does NOT reuse the
  session's stored `model_config`** — it runs the turn with the profile's
  DEFAULT model. Verified 2026-09-04: a session whose `model_config` said
  `ocgfree/muse-spark-1.3-contributor-free` / `custom:muse` resumed its first
  reminder turn with `model=meta` over the OLD 9Router combo base_url
  (`127.0.0.1:20128`) — the banned route. The `sessions.model_config` column
  stays untouched, so the wrong-model turn is invisible in the session record.
  ALWAYS pin `-m <model> --provider <provider>` on every resume/nudge string.
- **Verify the model ACTUALLY used — never trust the session row**:
  `grep -a "<sid>" "$LOCALAPPDATA/hermes/logs/agent.log" | grep -a "Turn ended"`
  → the `model=` field names the real model per turn (also `API call #N:
  model=… provider=…` lines); `session_model_usage` in state.db shows
  provider/base_url per run. Compare BEFORE (default model) vs AFTER (pinned
  model) to prove the fix landed.
- Confirm the nudge landed: message count for the session in state.db
  increases, and agent.log shows a new `Turn ended` for that session with
  growing `tool_turns`. A desktop-source session (`source='desktop'`) responds
  fine to CLI `--resume` nudges — the tag is cosmetic; the manager's reply in
  the log IS the proof it continued working.
- Cron `deliver=origin` is LOCAL-ONLY for desktop/CLI chats (no live-delivery
  channel; gateway off) — the observers are the log file + `cronjob list`
  `last_status`/`last_run_at`. ALWAYS test end-to-end with
  `cronjob action=run`, then read `execution_success`/`execution_error` before
  trusting the job. Script design: silent stdout on success (empty stdout = no
  delivery), `print()` only on failure (`REMIND_FAIL exit=N`) + exit non-zero
  so `last_status` flips to error; retry once after ~20s on exit 1/2 (Hermes
  CLI retryable codes).
- **Stop a recurring nudge ONLY on an explicit stop order — an ambiguous
  question is not one** (user-corrected 2026-09-04). When the user asked
  "m ko nhac nua a?" (≈ "aren't you reminding anymore?") the agent misread it
  as a stop command and disabled the job; the user corrected with "tiep tuc
  nhac lien tuc di, t co bao m duung dau?" (keep nudging — I never told you
  to stop). Vietnamese colloquial "…à?" / "…hả?" sentences are QUESTIONS, not
  commands. Rule: for a user-requested recurring reminder, keep it running on
  any ambiguous message, reply clarifying current status ("reminder still ON,
  next run HH:MM"), and act only on an explicit stop ("dừng"/"tắt nhắc").
- **Stream the nudge's output into the log file, never `capture_output`**
  (verified 2026-09-04): the script must call
  `subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)` with the open
  log handle. A `capture_output=True` variant swallowed `hermes chat`'s
  stdout, so the log logged only `start/exit/end` per reminder while the
  manager kept answering — the "did it continue and what did it say?"
  evidence was gone. Also `f.flush()` after writing the `=== start ===`
  marker BEFORE the subprocess runs, else Python's buffered write lands
  after the subprocess's direct-fd output (observed interleaved order).
  Regression signature to watch for: reminder runs with exit=0 but an empty
  body between start/end lines.
- **Do NOT convert a keep-alive job to agent-mode (`no_agent=false`)**: the
  `cronjob` tool exposes NO model/provider parameters, so an agent-based
  cron job runs the profile DEFAULT model (banned-route risk — a test run
  executed `model=meta` over the old 9Router combo base_url) and its
  delivery is skipped anyway (`deliver=origin but no origin or home
  channels — skipping delivery` in agent.log). Keep it `no_agent=true` +
  the `.py` script = zero model involvement. If the managed session still
  stalls between nudges, tighten the schedule (30m → 15m → 10m; user:
  "30p nó vẫn bị dừng", 2026-09-04) before considering other mechanisms.
  Verifying a cadence change: after `cronjob update` with a new schedule the
  returned `next_run_at` may still reflect the OLD cadence (observed:
  */15→*/10 update returned next_run 11:30 while real time was 11:29) — the
  scheduler recomputes from the next tick and a tick that already passed
  between update and run simply does NOT fire. Don't panic/re-update: verify
  the `schedule` field via `cronjob list` against the real `date`, then
  confirm the first post-update run appears in the reminder log at the
  expected boundary. Rename the job to match the new cadence (…-15m → …-10m)
  so future `cronjob list` reads stay unambiguous.
- **Cron jobs vanish from the scheduler — never assume a previously created
  job still exists** (verified 2026-09-04): between turns both the reminder
  job AND an older watchdog disappeared from `cronjob list` (desktop app
  restart / UI removal) while the script files under `scripts/` survived.
  Consequences: (a) before "re-enabling", run `cronjob list` and confirm the
  job id actually exists; (b) keep the nudge logic in a standalone
  `scripts/*.py` file so recreating the job is a one-liner pointing at it;
  (c) treat `last_run_at` not advancing across expected tick boundaries as a
  silent-death signal — recreate + `cronjob action=run` immediately rather
  than waiting for the next scheduled tick; (d) after recreate, note that the
  gap since the last successful nudge means the managed session went
  unnudged — fire one immediate `action=run` as both test and catch-up nudge.

- **Provider free-limit 502 — the managed session is dead from the API, not
  stalled** (verified 2026-09-04): free-tier routes (`ocgfree/*-free`) return
  `HTTP 502 {"error":{"type":"FreeUsageLimitError","message":"Rate limit
  exceeded. Please try again later."}}` and EVERY turn dies with it — the
  nudge, the desktop user's direct messages to that session, all of it
  (agent.log shows `error_type=InternalServerError summary=HTTP 502 …
  FreeUsageLimitError`). This is NOT a script defect: stop hammering (each
  script run fires 3–9 requests and stretches the cooldown; the CLI error
  prints `(reset after Nm)`), keep the cron ticking so it auto-resumes when
  the provider recovers, or pause the job on the user's explicit word. The
  `↻ Resumed session` banner is NOT proof the API works — verify with
  `grep -a "<sid>" agent.log | grep -a "API call"` (the `model=… provider=…`
  line) or the `Turn ended … model=` line. When the USER changes the managed
  session's model mid-run (desktop), SYNC the reminder script: read
  `sessions.model` / `model_config` from state.db and patch the script's
  MODEL/PROVIDER constants (observed change: `ocgfree/muse-spark-1.3-
  contributor-free`+`custom` → `cmc/meta/muse-spark-1.3-contributor`+
  provider `muse` — the provider name can move away from `custom`), then
  then verify one nudge's `API call` line shows the new model before reporting OK.
    When the user REPORTS a model change verbally, verify the DB row FIRST — the
    typed name may be abbreviated or typo'd (user wrote `cmc/muse-spark=1.3-contributor`;
    the `sessions.model` row read `cmc/meta/muse-spark-1.3-contributor` provider `muse`).
    Patch constants from the DB row, never from the user's string verbatim.
- **Watchdog .sh model switch = patch file + kill old PIDs + restart + errata (verified 2026-09-08)**: a running `watch_*.sh` loaded its `-m/--provider` at start — patching the file does NOT change the live process (it keeps nudging on the old model/quota). Protocol: (a) verify the new model EXISTS in the live router catalog (`/v1/models`, exact id match — a first grep can miss it, re-check full list); (b) `cp watch.sh watch.sh.bak-<model>-<UTC>` before editing; (c) patch the header comment (v2→v3→v4 lineage) AND the `hermes chat ... -m <new> --provider <new>` nudge line; (d) `grep -n "\-m "` to prove the switch; (e) kill the old watchdog PIDs by exact PID (never broad `pkill python` — the agent itself runs on Python) and verify `ps` empty; (f) relaunch the script `background=true` and confirm a fresh `WATCH... START` beat + new PID in the log; (g) write append-only `MODEL_SWITCH.md` (who ordered, old→new, PIDs killed, canonical HEAD, worker dirty-state at switch) — NEVER rewrite old prompt/registry files, history stays as-dispatched.
- **Stuck `already running` = the scheduler silently skips every later tick**
  (verified 2026-09-05): after one long nudge run, agent.log shows
  `cron.scheduler: Job '<name>' already running — skipping` at every boundary
  (17:00, 17:15 in a row) while `cronjob list` still shows `last_status: ok`
  and a STALE `last_run_at`. The job's running-flag never cleared — no new
  reminder runs fire. Fix: `cronjob pause` then `cronjob resume` (resets the
  flag), immediately `cronjob action=run` as test + catch-up, then read the
  reminder log for a fresh start block. Watch BOTH signals: `last_run_at` not
  advancing across expected boundaries AND `already running — skipping`
  lines in agent.log. Note the scheduler tick also drifts minutes late under
  load (observed 15-min boundary firing at :20/:33) — drift alone is normal;
  flat `last_run_at` + skip lines is the defect.
- **Pointing the reminder at a NEW manager session** (user hands a new
  session id, verified 2026-09-05): read the new row from state.db FIRST
  (`SELECT model, model_config, ended_at …`) — model/provider may differ
  from the old session; patch the script's SID (and MODEL/PROVIDER if
  changed), point LOG at a fresh log file so history stays clean, rename the
  job, then `cronjob action=run` once and confirm a start block in the NEW
  log. If the managed session's prompt rules demand an exact model id ABSENT
  from the router catalog (manager answers BLOCKED_MODEL_ROUTE, zero
  dispatch, 401 probe — fail-closed), the nudge works but the manager will
  not start work until the USER fixes the route: report the blocker, never
  patch the managed session's rules yourself; after the user says it's
  handled, fire one nudge immediately and read the manager's reply.
- **Attribute `hermes` processes by cmdline before blaming the cron**
  (verified 2026-09-05): `ps` may show `hermes.exe chat --resume …`
  processes whose session id is NOT the one your reminder targets — those
  are the manager's own worker/nudge spawns (`/proc/<pid>/cmdline` names the
  resumed session). A reminder nudge that times out in foreground (manager
  turns can run >5 min, e.g. while verifying a wave) orphans its child which
  keeps writing the log — verify via the log, and never kill an unrelated
  worker session while cleaning up.
- **Progress report tables MUST carry the nudge-hour column** (user-corrected
  2026-09-04: "sao trong bảng ko có giờ nhắc?"): when the user asks for a
  reminder/progress report, render a table with a `Giờ nhắc` column anchored
  to the script's start-block timestamp in the reminder log (the manager's
  own `date` inside its response drifts ±1–2 min from buffering/clock, so the
  start block is the anchor), then per-lane status from that run's response.
- **"I don't see the nudge" in the desktop app is a REFRESH artifact, not a
  missing nudge** (user-asked 2026-09-04: "sao ko thấy nhắc nó thế"): the CLI
  `--resume` writes the nudge message straight into state.db; the desktop app
  does NOT live-refresh a session that was already open, so the user watches an
  idle-looking manager and concludes the reminder stopped. Proof it kept
  running: reminder-log start/exit blocks advancing + session message-count
  growth in state.db + `cronjob list` last_run_at/last_status. Tell the user to
  close/reopen the session (or app) to see the nudge lines.
- **Nudge text stays the bare short phrase the user asked for** (user-corrected
  2026-09-04: "đã thấy prompt nhưng chỉ cần nhắc nó tiếp tục làm việc thôi, ko
  cần đưa list lại"): the cron script sends ONLY `tiếp tục làm việc đi` — never
  the task list, status tables, or context-compression dumps. Manager's own
  task list lives inside ITS session; don't mirror it into the nudge.
  (verified 2026-09-04): the scheduler resolves the script path with
  backslashes and hands it to bash, which strips them →
  `C:UsersAdminAppDataLocalhermesscriptsX.sh: No such file or directory`
  (exit 127; `execution_error` in `cronjob run` shows the mangled path). `.py`
  scripts run via Python and handle Windows paths natively — always author
  cron scripts as `.py` (matches the existing heartbeat_watchdog.py pattern).
- `--basetemp=/c/...` (MSYS path) breaks Python (`C:\c\...` FileNotFoundError)
  — use Windows-native `C:/Users/...` paths for Python tooling.
- **`git -C` fails on MSYS paths in git-bash** (verified 2026-08-05):
  `git -C /c/Users/...` errors "fatal: not a git repository", and
  `git -C C:/Users/...` SILENTLY returns 0 entries — indistinguishable from a
  clean tree unless you check! For multi-tree status comparisons (MAIN +
  every worktree), `cd` into each directory and run
  `git status --porcelain=v1 | wc -l` there. Treat a bare "0" from a `git -C`
  call with MSYS/C:-style paths as the failure signature, never as evidence
  of a clean tree.
- Playwright E2E against a long-lived Next dev server aborts `page.goto` —
  kill and restart the dev server before the run; the first run after an edit
  may use a stale bundle, so re-run after recompile before debugging the app.
- Killing a worker: kill the exact PID/session; never broad `pkill python`
  (the agent itself runs on Python).
- **Terminal hardline blocklist rejects COMPOUND verification payloads**
  (verified 2026-08-23): multi-command strings with `$(...)` substitution
  inside sed ranges, nested for-loops with printf, or long `&&` chains get
  blocked as "command parser limit or malformed executable payload". Split
  into several simple single-purpose commands (`grep … ; grep … ; tail …`)
  and read files via read_file instead of inline `$(cat)`/`$(sed)` extraction.
  **Heredocs are blocked too** (verified 2026-09-16): `python - <<'PY' … PY`
  stalled mid-turn then got hardline-refused ("command parser limit or malformed
  executable payload"). For any inline Python, `write_file` a `.py` into the
  evidence dir and run `python.exe <C:/win/path>` instead — and keep those probe
  scripts as evidence, they double as the audit trail for DB/config queries.

## Watcher & todo hygiene (user-corrected 2026-08-05)

- Kill each task's watcher IMMEDIATELY after that task's manager verification
  passes — do NOT let watchers accumulate. User complained ("sao chạy lắm
  background thế nhỉ") after 7 stale watchers (T05…C04-R2) kept copying
  finished logs every 10s for hours. Rule: exactly ONE watcher alive at a
  time — the current task's. Optionally also `close_terminal` its tab.
- Todo-list hygiene: after each completed task, REPLACE the todo list with
  only remaining/active items (merge=false); never keep a growing list of
  finished tasks. The user complained the task board became unreadably long.

## Heartbeat cadence in manager mode (user-corrected 2026-08-21)

When the user is watching the chat while background writers run ("HERMES
MANAGER" correction cycles), they demand a visible **heartbeat every ~10
minutes** by default ("ko thấy heartbeat chạy nữa", "cứ phải đợi hỏi thế",
"muốn có heartbeat mặc định mỗi 10 phút nhé"). Auto mode may be silent; manager
mode is NOT.

- Emit a short status every ~10 min: which lane/writer is running, current
  test results, how much longer. Answer "bao giờ xong" with a concrete ETA
  table (per-lane elapsed vs remaining).
- **Mid-turn interruption pitfall**: a user message that lands mid-turn CANCELS
  the in-flight assistant turn, swallowing any heartbeat text drafted at the
  end of that turn — the user then believes the work stopped ("sao t vừa thấy
  mày dừng", "ko thấy heartbeat"). The background workers never stopped (they
  exit 0 independently); only the drafted prose was lost.
  Prevention: put the heartbeat AT THE START of each turn, not only at the
  end; after any long run confirm the writer exited cleanly (`process wait`)
  and say so explicitly; when the user asks "có dừng không / sao interup",
  explain the mechanism plainly — interruptions cut drafted text, not the
  background processes.
- Never wait to be asked for progress. Do not bury multi-lane work in a single
  end-of-run report.

## Resuming a worker session non-interactively (verified 2026-08-21)

Recovery must use the **`chat` subcommand + `-q` one-shot form**, NOT bare `hermes --resume`:

- ✅ `hermes chat --resume <SESSION_ID> --provider muse --model <MODEL> -q "CONTINUE.TASK: …" --yolo --pass-session-id --max-turns <N> --source tool`
- ❌ `hermes --resume <SESSION_ID> --yolo --max-turns 200` → `argument command: invalid choice: '200'` —
  top-level `--resume` has no subcommand and `--max-turns` is parsed as a bogus subcommand.
- ❌ `hermes chat --resume <SESSION_ID> --provider … --model …` WITHOUT `-q` (and without a tty) →
  `prompt_toolkit NoConsoleScreenBufferError: Found xterm-256color, while expecting a Windows console`.
- ✅ Resume a dead/disconnected writer by resuming the SAME owning session id (one writer per Task ID;
never open a second session for the same task). The `-q` text becomes the next user turn, so put the
exact continuation instruction there (what to re-verify, allowlist, SUBMITTED-only).
- A manager MAY redo its own resume (resume2, resume3…) when its verification rejects the attempt's
quality — each retry carries a tightened prompt (sharper guard clauses, explicit evidence
classification, listener cleanup). Keep per-attempt logs named `<ts>_writer-<model>-resume<N>.log` so
attempts stay auditable; expect the task to overrun first-pass ETAs (three consecutive resumes observed
on S07-T03-C1, 2026-08-21→22, each legitimately rejecting half-done real-vertical runs).

## Worker liveness audit + connection-error retry policy (user rule, verified 2026-08-21)

Deciding ALIVE vs DEAD before resuming or reviewing a lane:
- Map PIDs to sessions, don't guess from chat history:
  `powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json"`
  — each `hermes.exe chat --resume <SESSION_ID> …` command line names its owning session. A missing PID =
  that lane's worker is GONE even while sibling lanes (other tasks) keep running.
- Two-point log sampling beats one glance: `stat -c '%y %s' <log>` → sleep 60–90s → stat again. Growing
  size/mtime = active writer; frozen log + absent PID = dead. A single old snapshot proves nothing.
- USER RULE (also added to MotionForge2D HERMES_AUTOPILOT_RULES.md §7): on connection error / 502 /
  disconnect, wait EXACTLY 5 minutes, then resume the SAME owning session; repeat the 5-min cycle until
  recovery or proven death. Report at the FIRST failure; never quit permanently after one error, never
  hot-loop retries without the 5-minute gap.
- Worker died BEFORE SUBMITTED (frozen LOG/REPORT mtimes, half-edited allowlisted files, no evidence dir)
  → record BLOCKED_LIVENESS, resume the same session with a continuation prompt listing the exact
  remaining findings; do NOT create a replacement session and do NOT review the moving corpse as final.

## False-death diagnosis — MSYS ps is NOT liveness evidence (verified 2026-08-23, cost ~3h)

An S09 manager declared its T01 writer dead (log "frozen" at one sample, proc absent from
`ps -p`) and ran read-only lanes for 3h on that basis — the writer was ALIVE the whole time
(MSYS ps lost/mismapped its Windows PID after the bash wrapper child exited; two live
23:27 hermes PIDs were waved away as "probably the sibling lane") and completed
TASK_SUBMITTED under a contract superseded hours earlier.

- A DEAD verdict requires ALL of: (a) a `wmic`/`Get-CimInstance` CommandLine scan finding NO
  python.exe whose cmdline contains the task's prompt marker (e.g. `TASK ID:`), (b) log size
  flat across samples spaced MINUTES apart (seconds-apart samples lie — buffer flushes fake
  freezes), (c) no late SUBMITTED/session_id marker. ANY size growth after a death call
  re-opens the verdict immediately; never stay anchored on the first snapshot.
- Survivors of `ps aux | grep hermes` must be ATTRIBUTED via cmdline match, never dismissed by
  lane stereotypes ("probably the other sprint's").
- Non-interactive `-q` workers have NO readable stdin: `process submit` fails with
  "Process stdin not available" → mid-flight safe-stop is impossible; plan for natural exit.
  After a SUPERSEDE order, expect the worker may legitimately finish under the OLD contract:
  preserve every change for attribution, mark PENDING_<REVIEWER>_REVIEW, never verify it as
  current scope.
- Waiting time is not idle time: run READ-ONLY audit lanes in disjoint output dirs (each lane
  ends REPORT.md `STATUS: TASK_SUBMITTED`, asserts MOTIONFORGE_DATABASE_URL UNSET, cites
  file:symbol for every claim), then one synthesis lane consumes all lane outputs into a
  readiness package; manager adversarially spot-checks several citations per lane against the
  real tree before MANAGER_VERIFIED. But NEVER dispatch dependent implementation waves until
  every live PID has CONFIRMED (not guessed) ownership.

## New migration changes the Alembic head — hardcoded-head tests break (verified 2026-08-21)

Adding a new migration moves Alembic head (e.g. `a0b1c2d3e4f5 → b2c3d4e5f6a7b`). Any baseline test that
asserts the literal old head now FAILS until updated. **Crucial: when a task adds a migration, grep ALL
test files for the old head before finishing, and update EVERY hit** (migration tests,
`test_persistence_bootstrap.py` `assert head == …` / `database_schema_revision(…)` /
`S08_HEAD_TABLES` set, object_* suites `assert version == …`, `test_s08_a0X_*_migration.py` `HEAD = …`
and `test_revision_chain_and_single_head`, `test_downgrade_refused_atomically_with_any_row`). Missing one
file (this session missed `test_s08_a02_structural_evidence_migration.py`) only surfaces later when the
NEXT task or the final combined gate runs and fails — costing an extra resume cycle. Update each head
constant/assert to the new head (comment can keep historical note), expand `S08_HEAD_TABLES`-style sets
with the new table, and re-run the whole head-test set plus T01/T02/T03 to prove a TRUE green baseline.

## Flaky test caused by shared global session/workspace → per-test isolation fixture (verified 2026-08-21)

A flaky test that passes 10/10 standalone but fails ~1/13 under a large combined run, with no traceback,
is typically ORDER/TIMING dependent = a test file that reaches a process-GLOBAL session
(`deps._job_service._session_factory()`) and/or seeds a FIXED workspace id shared with other tests.
Fix at the test level (do NOT weaken assertions, do NOT mask with try/except): add an `autouse`
fixture that, before+after each test, deletes the tables that file owns (FK-safe order) so every test
starts from a clean isolated state. Then re-run the file 6–10× AND the same combined suite ≥2× to prove
stability. Verify the fixture actually applies (grep `autouse`), syntax-check (`python -m py_compile`),
and confirm the same combined count (e.g. 437) passes back-to-back.

## Codex CHANGES_REQUESTED correction cycle — freeze policy, order resumes, pass exact commands (verified 2026-08-21)

When Codex reviews a whole linear sprint and returns CHANGES_REQUESTED with blocking findings (e.g. S07
F1–F6: write-boundary compatibility not enforced; `role.source_generation == str(pack.version)` domain
error; weak `isinstance(bool)` assertions; DELETE revision optional):
- Manager FIRST reads the actual code and confirms each finding in grep, then freezes the corrected policy
  IN WRITING (single authoritative source in the persistence layer that evaluate/create/repin ALL call —
  no duplicate policy across UI/route/repo; backend-authority generation check; fail-closed fallback
  where `fallback_allowed` is advisory-only and never turns a blocked write into an allowed one).
- Resume the SAME owning sessions IN ORDER (T01 → T02 → T03), each only after the previous is
  MANAGER_VERIFIED. The `-q` continuation text carries the frozen policy + exact allowlist + required
  tests + "SUBMITTED only". Backend defects found by a later acceptance task route back to that task's
  owning session (never self-edit production).
- Give the writer the EXACT manager-known commands — e.g. the precise 21-file pytest list that totals N
  passed. Without the literal list, a writer has been observed brute-force-searching which random file
  combination sums to 437 instead of running the suite — dozens of wasted turns (verified 2026-08-21).
- A writer "debugging corruption" (null bytes in a test file) needs ground truth: run
  `python -m py_compile <file>`. Null bytes inside a `bytes` STRING LITERAL (`b"\x00"*10`) are text, not
  file corruption — tell the writer to stop trying to "fix" them and use py_compile as the syntax gate.

## Parallel multi-lane dispatch (verified 2026-08-20/21)

Correction cycles dispatch N code writers (N≤3) in parallel, sometimes plus one
read-only planning lane. Rules proven across S08-A02 C5/C6 + T02-C1/C2:

1. Disjoint allowlists are the contract for parallelism — verify before launch
   no two lanes share a write file. A planning lane owns its own
   `output/<...>planning/<run>/` + LOG/REPORT only. Never a 4th lane.
2. Each lane gets a full packet (TASK.md + START_PROMPT.md + LOG.md +
   REPORT.md template) with the mandatory model block, worktree guard, exact
   allowlist + FORBIDDEN, blockers, stop conditions (SUBMITTED only).
3. Dispatch each lane as its own background `hermes chat` with
   `--pass-session-id --yolo --max-turns <N>`; tee output to the lane's
   evidence log. Track via `process wait` with bounded waits.
4. After all lanes exit, verify ownership by mtime — each lane's files must
   have changed only inside that lane's run window. Cross-lane mtime = scope
   breach. Then grep the FAIL-condition list in code (e.g. `literal_column`,
   `already bound`, `hash(seg_id)`) to prove 0 remains.
5. Manager re-runs EVERYTHING itself (never trust the REPORT): each lane's
   suite, combined focused suite at least twice, flaky test N× (20 or 30 as
   specified), cross-process determinism under two PYTHONHASHSEED, and the
   named repro (e.g. 5001-video SQL instrumentation).
6. End: `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`, never self-approve. Planning
   lane ends `POST_A02_PLAN_DRAFT_READY` or `BLOCKED_NEXT_SPRINT_AUTHORITY`
   (the latter = list the exact user decisions needed, don't invent a sprint).

## Read-only reviewer lanes see a SNAPSHOT — "BLOCKING / NOT LANDED" is expected pre-write (verified 2026-08-21)

RO lanes (S07-RO1/RO2) or a BA preflight dispatched IN PARALLEL with a code writer inspect the tree
BEFORE the writer writes. Their verdict reads "N x BLOCKING, 0% satisfied, all references NOT LANDED"
purely because the artifacts (table, file, router, migration head) do not exist yet. This is the correct
snapshot result, NOT a defect to route back as a correction. Workflow:
- After the writer SUBMITS, re-review each RO finding against the LANDED code (grep the actual allowlisted
  files: strict schemas, server-owned workspace, helper-text classes, OpenAPI `$ref`, idempotency/CAS,
  FK RESTRICT). Close each with "land verified".
- Record RO1/RO2 as "snapshot findings — land verified" in MANAGER_STATE so stale "BLOCKING" lists are
  not mistaken for open blockers during Codex review.
- A BA verdict (SAFE_TO_PARALLELIZE_WITH_EVIDENCE / MUST_WAIT_WITH_EVIDENCE) is read-only: even SAFE does
  NOT grant implementation authority — still wait for a separate Codex/BA code grant.

## Linear sprint owning-session rules (S07 T01→T02→T03, verified 2026-08-21)

- One Task ID = one owning writer session; a task correction resumes THAT session (never a new correction
  session). Dispatch T(next) only after T(prev) = MANAGER_VERIFIED.
- T03 (integration/acceptance) finds a production defect → T03 never edits production; Manager sends exact
  reproduction to the owning T01/T02 session via resume `-q "MANAGER_CORRECTION…"`, then T03 re-verifies.
- When a migration-owning task changes the Alembic head, the head-constant test fix may be OUTSIDE the
  task's test allowlist → Manager expands the allowlist for the EXACT head-constant files (BLOCKED_SCOPE
  decision, logged), still resumed in the owning session.
- Stale "process completed" notifications arriving after a session already exited are harmless — verify the
  session state, don't relaunch.

## Verify a writer's forbidden `git checkout` on untracked files (verified 2026-08-21)

A writer may run `git checkout HEAD -- <file>` inside a dirty worktree (forbidden). On an UNTRACKED file
(never committed) this FAILS harmlessly — git cannot restore a pathspec that is not in HEAD, so no data is
lost. Verify instead of panicking: `git ls-files --error-unmatch <file>` → exit 1 + "did not match any
file(s) known to git" = untracked = checkout could not have deleted anything; then confirm the file's line
count / test count is intact. Note: our untracked files ARE the work product (nothing is committed), so a
real `git checkout` on a TRACKED file WOULD destroy changes — different risk for committed repos.

## Flaky-test iteration without pytest-repeat (verified 2026-08-21)

`pytest --count=N` is NOT available unless `pytest-repeat` is installed —
`error: unrecognized arguments: --count=20`. Use a plain shell loop instead:
`for i in $(seq 1 N); do python -m pytest <test> -p no:cacheprovider -q
--basetemp=C:/Users/.../$(date +%s); done` and count PASS/FAIL runs. Note the
flaky test may be order/timing dependent: it passes standalone but can fail
~1/N under a large combined run (statement-counter thresholds + autobegin/
ROLLBACK noise). Instrument ONLY SELECTs (`statement.lstrip().upper()
.startswith("SELECT")`) so transaction BEGIN/ROLLBACK never trip the counter.

## Manager max-turns exhaustion → review gate takes over packet append (verified 2026-08-22)

A manager that spends most turns POLLING (sleep/stat/tail/wait loops) can
exhaust `--max-turns` BEFORE the worker finishes — observed 200/200 after
7h22m while its worker was still mid-Playwright. Recovery pattern:

- The worker keeps running independently and may finish AFTER the manager is
  gone — check the worker lane directly (log mtime + PID) before assuming
  everything died together.
- If the worker completed CODE + tests but nobody appended LOG/REPORT (worker
  or manager died first), the review gate (BA) MAY append the missing
  correction entry itself — ATTRIBUTION MUST STAY TRUTHFUL: record which
  session died when, what the WORKER completed (file mtimes, evidence dirs,
  real test counts), and that BA appended the entry post-mortem. Never
  present BA-written packet text as worker-authored; never fabricate worker
  claims.
- Budget planning: a poll-heavy session burns ~1 turn/minute; size
  `--max-turns` to the WALL CLOCK of the slowest lane (a 3-resume correction
  cycle containing a 1h+ E2E run needs headroom well above 200), and prefer
  completion-notification wakeups over fixed sleep loops.

## Alembic `downgrade <rev>^` caret syntax unsupported (verified 2026-08-22)

`alembic downgrade b2c3d4e5f6a7b^` → `FAILED: Can't locate revision identified
by 'b2c3d4e5f6a7b^'`. Alembic has no git-style caret; pass the PARENT revision
id literally (`alembic downgrade a0b1c2d3e4f5`) for roundtrip gates.

## Doc-only audit/synthesis lanes + multi-round corrections (verified 2026-08-23, S13-P00 run)

Pattern: N read-only audit lanes (A/B/C, disjoint output dirs) → one synthesis lane consumes them → reviewer returns CHANGES_REQUESTED → per-round corrections C1/C2… ALL resumed in the SAME owning session.

- **`mkdir -p` the log directory BEFORE any `> path/to/log` redirect** — three parallel dispatches died instantly (`No such file or directory`, hermes never started) because the evidence-log subdir didn't exist yet. Zero-side-effect proof afterwards: `find <repo> -newermt <dispatch-time> ! -path './output/*' ! -path './.git/*'` shows nothing.
- **Always launch resumes with background=true**, never a foreground `sleep N && … && hermes chat --resume …`. A foreground wrapper hitting its timeout (exit 124) KILLS the shell but ORPHANS the still-running hermes child, which keeps writing the log but never appends the `EXIT=` line. Detect completion by CONTENT markers instead: `STATUS: TASK_SUBMITTED` in the log or deliverable mtimes advancing.
- **Large-session resume (~190k tokens) enters a "Preflight compression" phase that can exceed 15 minutes and may DIE silently there** (log frozen at the compression banner, process gone from ps/netstat). Session state persists on disk — resume the SAME session again with a SHORT continuation prompt; the full correction text is already in session history, re-sending it all wastes context. Observed chain on one round: attempt 1 segfaulted EXIT=139 mid-write_file, attempt 2 died in compression, attempt 3 compacted successfully and finished clean. Every retry kept provider/model identical.
- **Hash-manifest gate for doc-only rounds**: before the round, `sha256sum <all deliverable dirs + frozen input lanes>/*.md > manager/Cx_hash_baseline.txt`; after exit, `sha256sum -c`. FAILED lines must equal EXACTLY the files the worker was allowed to edit — any other FAILED line is a scope breach; zero FAILED outside the allowlist plus byte-identical frozen inputs IS the write-scope proof. Re-check protected anchors (channels.json, models.py, api.ts…) against known hashes too.
- **Grep-gate false positives — read hit CONTEXT before failing**: forbidden-pattern sweeps legitimately match prohibition notes ("migrations live in `migrations/versions/**` (NOT `alembic/versions/**`)", "NEVER hard-code a revision such as `<id>`", "`app/**` contains no qa_stub") and LOG history lines. A raw count > 0 is not a finding; classify each hit operative vs prohibition/history first.
- **Foreign-write attribution in a shared dirty worktree**: concurrent lanes write production while your doc-only round runs. Attribute by mtime window + topic AND by proving YOUR worker's log has zero mentions of the changed file. Never touch other lanes' processes; record the overlap in OPEN decisions for the reviewer instead.
- Correction prompts per round stay SHORT: hard guard + this round's findings only; standing rules (allowlist, SUBMITTED-only, append-not-erase LOG/REPORT history) live in the session from round 1. Keep per-attempt logs `dispatch-d-c1.log`, `-c1r2.log`, `-c1r3.log`, `-c2.log` for lineage.

## Finding a worker's owning session ID when the dispatch log doesn't say (verified 2026-08-23)

Grepping the dispatch log for `session_id` can return NOTHING usable (quiet `-Q` dispatches may never echo it; timestamp-like IDs found in a log may be TASK.md citations, not the live session — one S09 lane matched only its own TASK.md reference). Authoritative source is the Hermes state DB:

```
python -c "
import sqlite3, time
c=sqlite3.connect(r'C:/Users/Admin/AppData/Local/hermes/state.db')
rows=c.execute('SELECT id, started_at, message_count FROM sessions WHERE started_at > <epoch-of-dispatch> ORDER BY started_at').fetchall()
for r in rows: print(time.strftime('%H:%M',time.localtime(r[1])), r[0], r[2])
"
# disambiguate same-window sessions by FIRST USER MESSAGE (TASK ID line identifies the owner):
# c.execute(\"SELECT content FROM messages WHERE session_id=? AND role='user' ORDER BY rowid LIMIT 1\",(sid,))
```

Never guess from log timestamps alone — resuming the WRONG sibling session injects a foreign task into another lane's history. Column names: `sessions(id, started_at, message_count, cwd, …)`; there is NO `created_at`.

## Quiet-death modes that are NOT clean SUBMITTED (verified 2026-08-23)

- **EXIT=4 mid-turn = crashed while editing.** Half-applied patches and dangling reasoning stay on disk. Don't restart from scratch: run the worker's own focused suite YOURSELF (isolated basetemp, `-p no:cacheprovider`) to measure exactly what landed, then resume the SAME owning session with the precise remaining findings.
- **EXIT=0 WITHOUT REPORT.md/`STATUS: TASK_SUBMITTED` = wrapper succeeded, worker died before finalizing** (observed: died while patching its own proof script's print order). Exit-banner parsing MUST include the artifact check: REPORT.md exists AND carries the STATUS marker; otherwise classify dead-before-submit and resume for report-only completion — the code work may be 100% done and independently verifiable.
- A worker that dies mid-run while OTHER lanes run in parallel leaves its siblings seeing broken shared fixtures (migration DDL errors, schema flips). Correct sibling behavior (validated): bounded wait-loop ≤10 min per cycle + independent probe of the dependency (`alembic upgrade head` from empty DB), attribute the breakage to the other writer in LOG, never fix out-of-scope.
- **No wrapper EXIT line AT ALL + log frozen + zero matching processes = hard-killed lane (verified 2026-08-24, twice in one evening on S09 Wave 2).** Pattern: BOTH the bash wrapper and the hermes child vanish without ever appending `EXIT=` (suspected provider drop killing the CLI outright), while sibling lanes keep running normally. Diagnosis needs all three signals: `tasklist`/wmic count of matching processes = 0 for the lane marker, two-point log freeze spaced ≥40s apart, and no `STATUS:`/session_id tail marker. Recovery that produced clean SUBMITTED in ONE resumed turn every time: (1) inventory what landed on disk YOURSELF (files written, which suites pass standalone), (2) resume the SAME owning session with a SHORT continuation text listing: what is verified-done (explicitly "KHÔNG chạy lại phần đã xong"), the exact remaining checklist, fresh basetemp names for the ×2 runs, and FORBIDDEN-to-touch files. Never relaunch from scratch and never re-send the whole original contract — the session history already holds it.

## Manager root-causes failures BEFORE writing the correction prompt (verified 2026-08-23)

Don't ship "tests fail, fix them." Run the failing suite yourself, read the actual assertion, and isolate both sides of the mismatch — e.g. regex-extract the CHECK-constraint names from migration vs ORM class and diff the sets (found: migration had `ck_structural_lock_manifest_revision_positive`, ORM class lacked it while its sibling table had one); read the SQL parameters in IntegrityError tracebacks to spot a duplicated PK seed ('rr1' twice). Then the resume text carries DIAGNOSIS + PRESCRIBED FIX + FORBIDDEN ALTERNATIVE per finding ("add the missing CheckConstraint to the ORM class following sibling pattern at models.py:<line>; do NOT touch the migration"). One finding per block, exact symbols and file:line. A correction resumed with manager-grade diagnosis applies mechanical fixes and finishes its whole remaining checklist in ONE resume instead of burning turns re-diagnosing.

**Verify worker REPORT claims by re-running gates yourself — including ones you'd never think to question (2026-08-24):** a T00-I05 report claimed the "missing" reference media was actually FOUND on disk with SHA matching `5a175454…`. The manager hashed the file itself (`sha256` over 1MB chunks) and confirmed VERIFIED — catching this converted a planned SKIP_WITH_REASON into a stronger gate result. Conversely, don't import the worker's own tooling into your gate blindly: running `ruff check <file.ts>` (a PYTHON linter) produced 561 fake errors that briefly looked like a write-set failure; Python linters do not apply to frontend files (frontend gates are tsc/eslint run by the worker — spot-check those instead or state plainly they're out of your gate scope). Determinism checks on benchmark JSONs: strip ONLY the fields the results file itself declares as `non_deterministic_fields_excluded_from_compare` before comparing two same-seed runs; anything else differing is a real finding.

Additive-only contract proof (cheap, exact): snapshot `sha256sum`/a byte copy of the protected file BEFORE dispatch (e.g. `models_baseline_<hash8>.py` in the lane output dir); after exit, `difflib.unified_diff(base_lines, current_lines)` and count `-` lines excluding the `---` header — `removed_lines: 0` IS the zero-removed proof, stronger than eyeballing a git diff of a 2500-line dirty file.

## Contract-compat & wiring-diff gates after implementation waves (verified 2026-08-24)

- **OpenAPI additive gate**: record total path count (+ domain subset) from a live `app.openapi()` call BEFORE the wave, re-check AFTER — `removed=0` plus only-net-new paths IS the compatibility proof (observed 215→219 foundation, →221 after the Source-Locked completion). Cheaper than diffing whole spec blobs and catches accidental route deletion instantly.
- **Wiring diffs can show REMOVED lines that are RE-ADDED nearby** (import reorder inside the same hunk region): a raw `git diff | grep -c "^-[^-]"` > 0 is NOT automatically an allowlist violation. Pair each removed line against the added hunks — the invariant is NET content loss (removed without equivalent add), not literally zero `-` lines. Observed: renderer_router.py wiring showed 3 removed import lines that were re-added 4 lines below; verdict recorded as "reorder, zero net loss" in the registry instead of failing the lane.
- **Evidence JSONs nest their verdicts**: a benchmark smoke's pass/fail lived under `results[i].threshold_evaluation.overall_pass`, not any top-level `pass`/`fixture` key — print the actual keys (`list(d.keys())`, then one result's keys) before declaring "no pass evidence". Same drill confirms `schema_version`/`frozen_content_sha256` are UNCHANGED when the harness was required to stay frozen (schema bump would need explicit justification in the REPORT).
- **Threshold-schema bumps must touch the fixture side too**: a harness that bumps `SCHEMA_VERSION = 3` while `tests/fixtures/**/thresholds.json` still says `2` fails EVERY subprocess test at load time (`thresholds schema_version must be 3, got 2`, observed 8/29 failing on S09-C2 PREP). When a correction changes a version constant, grep the fixtures for the old value in the same round.

## ETA tables: weekday+date pairs must be computed, not remembered (user-corrected 2026-08-23)

An ETA table that mislabels dates ("Chủ nhật 25/08" when 25/08 was Tuesday; milestones shifted a day off) makes the user question EVERY number in it — they immediately replied "ngày giờ đang có vấn đề sai à". Always take the current weekday/date from `date '+%A %d/%m/%Y %H:%M %z'` output in the same turn, derive milestone dates arithmetically from it, and print full `weekday DD/MM` pairs. After any calendar slip, re-issue the corrected table proactively (don't wait to be asked).

## Sprint-level task packets for resumed foundations (S09 pattern, verified 2026-08-24)

When a sprint contract supersedes an earlier one but Codex rules "keep the foundation code", the completion task is NOT a fresh TASK.md — write a `TASK-SL.md` (Source-Locked variant) in the SAME session dir and dispatch it as a RESUME of the original owner session (`--resume <old-session-id>`). The packet states explicitly: what the owner already built that is now APPROVED to keep (so it doesn't revert or re-litigate), which sibling-task artifacts are verified and importable (with exact paths), the current Alembic head (and "discover live, don't hard-code"), the delta outcomes still missing, and a NARROWER allowlist than the original task had (e.g. "migrations/** FORBIDDEN — head d8e9f0a1b2c3 already exists; models.py FORBIDDEN — I01 owns it now"). Result observed: full Source-Locked completion in ONE 1h38 resume with zero scope incidents — versus multi-day churn when the same worker re-reads a stale contract.

Ownership-transfer wiring: when a later task may touch an earlier task's file at exactly one point (e.g. registering a new renderer implementation), encode it as "ADDITIVE wiring only, zero removed lines" inside an otherwise-FORBIDDEN file, and verify post-exit with the difflib removed-lines proof above rather than trusting the report.

## Sequential sprint execution with per-task packets + immediate dispatch (S09 full-sprint pattern, verified 2026-08-23→24)

When Codex grants a WHOLE sprint at once ("run T00 through T06 without stopping between tasks"), the manager runs this loop per task — proven across I01–I05 → T01 → T02 with zero scope breaches:

1. **Write TASK.md packet per task** in `docs/pm/sessions/<TASK>/` BEFORE its wave: role+model block, mandatory Bước 0 (full rules read → `RULES_LOADED`, overlay read, worktree guard, DB-UNSET guard), **Context đã verified** section citing sibling tasks' verified artifacts WITH exact paths (so the worker imports instead of re-inventing), outcome list, binary acceptance gates (test counts ×2, ruff/mypy/tsc evidence, frozen SHA checks), NARROW write allowlist + explicit FORBIDDEN list (including sibling-owned files), SUBMITTED-only stop.
2. **One-line prompt files** (`output/<run>/tXX/prompt.txt`): "Đọc TASK.md đầy đủ tại … và thực hiện ĐÚNG từng mục" + Bước 0 reminder. Dispatch via `PROMPT=$(cat file)` bash expansion (long prompts safe this way), background + notify_on_complete.
3. **Dispatch the next task IMMEDIATELY after verifying the previous one** (same turn when possible) — don't wait for user pings; the grant covers the whole chain.
4. **Correction/resume discipline**: on crash/quiet-death, resume the SAME owning session with a SHORT continuation text that lists (a) what Manager independently verified as DONE on disk ("KHÔNG chạy lại phần đã xong"), (b) exact remaining findings with root cause + prescribed fix + forbidden alternative, (c) fresh basetemp names for ×2 runs. Observed: every such resume finished its whole remaining checklist in ONE turn (I01 parity/PK findings, I02 nvenc probe fix, I03 metric-schema patch, T00-I05 report-only completion).
5. **Parallel waves only where write-sets are disjoint** (I02∥I03 adapters-vs-harness); serial otherwise (T01→T02→T03). Record every wave transition + verify verdict in the session registry as you go — the registry IS the handoff document for the external reviewer.

**Registry rows double as the final review package**: each row = timestamp(+07 & UTC) | wave/event | verify evidence (exact test counts ×2, hashes, OpenAPI deltas, root causes found). When the last gate goes green, the reviewer reads ONLY this table plus the REPORTs — no reconstruction needed.

## Correction rounds that must NOT end TASK_MANAGER_VERIFIED (S09-C1→C2 lesson, verified 2026-08-25)

- **Required-class FAIL/unknown/FOQ forces `BLOCKED_WITH_FINDINGS`, regardless of how honest the evidence is.** C1 ended with 5/6 classes measured and 2 honest FAIL_OPEN_QUESTIONs; the manager wrote `TASK_MANAGER_VERIFIED` anyway and Codex overruled it to `CHANGES_REQUESTED`, explicitly re-stating the terminal as `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. Honesty of the evidence does not upgrade the terminal state — the prompt's binary rule ("required class fail/unknown/FOQ = blocker") wins. Before writing the terminal, re-read the prompt's own blocker list and check each one.
- **A freeze/join handshake is a CHAIN, not a point-in-time hash.** C1 pinned 3 files at J1, but a later correction round edited one of them (`__init__.py`) without invalidating the freeze — 4 downstream tests then failed on contract-SHA drift at review. C2's fix, now standard: machine-readable recursive manifest over EVERY behavior-critical file (path → SHA-256 JSON), pinned by SHA in the registry; every measured/consumer run verifies the manifest BEFORE and AFTER; any drift invalidates all downstream runs and forces owner-resume + new manifest + full rerun. If a post-freeze change is genuinely required (e.g. per-region occluder scope opening), pin an explicit v2 manifest (`version/supersedes/reason` fields), rerun everything downstream, and record the supersession in the registry.
- **rg-gate for "no references to old artifact" must run over ACTIVE test code too**, not just production/frontend — stale tests still loading the old artifact as frozen input pass their suites silently while violating the sprint contract (caught in C2 final gate: two T02 test files still pointed at the v1 benchmark). Classify each hit operative vs prohibition/comment before failing, but operative loads of a deprecated artifact ARE findings.
- **Manager decisions between worker options get recorded as BA-scope calls in the registry** with the prompt clause that grants authority (e.g. "mục 3.2: group_occlusion required — option (b) chosen"), so the reviewer sees the decision was in-scope rather than invented.
- **Benchmark determinism compares strip ONLY declared non-deterministic fields** plus run-scoped artifact paths; runtime telemetry diffs among stripped fields are expected. Adversarial controls (source-reencode substitution) must read FAILED_AS_EXPECTED — a control that passes is itself a finding.

## Wave bootstrap: `hermes -z` dispatch, unbuffered logs, state.db monitoring (verified 2026-09-17)

Starting a BRAND-NEW wave (new task IDs, new worktrees, new evidence root) — as
opposed to resuming an existing lane — use this chain end to end. Worked
first-try on MF-RESKIN-V1: two lanes dispatched in parallel, both confirmed
alive and on-scope within ~3 minutes, guard VERIFIED at capture and re-verify.

1. **Create worktrees with Windows-NATIVE paths.** `git worktree add /c/Users/…`
   makes git resolve the MSYS path literally as `C:/c/Users/…`. If a stale
   `C:\c` junction pointing at `C:\` exists (it did on this machine),
   `git worktree list` then shows a worktree that is actually rooted at the DRIVE
   ROOT, and `test -d <the msys path you intended>` fails while `git rev-parse
   HEAD` on the recorded path still returns a real SHA — a silently-misplaced
   worktree. Always `git worktree add "C:/Users/…" -b <branch> <base-sha>`, then
   verify BOTH `test -d <msys path>` AND `git -C "C:/Users/…" rev-parse HEAD`.
   Cleanup: `git worktree remove "C:/c/…" --force`, `git branch -D <branch>`,
   `git worktree prune`.
   **Never `rm -rf` a path that may be a junction** — removal can follow the
   junction and delete the TARGET's contents. Remove the junction itself only
   after listing it and confirming it holds nothing unique. After any such
   accident, re-verify the real trees by MEASURED COUNTS, never by eye: Hermes
   home (`find <home>/skills -name SKILL.md | wc -l`, session-file count,
   `projects.db` size), per-repo `git rev-parse HEAD`, and
   `git ls-files | wc -l`.
2. **Dispatch with `hermes -z`** (top-level one-shot `-z/--oneshot`): no TUI, no
   tool previews, no session_id echo, approvals auto-bypassed, `AGENTS.md` and
   rules in the CWD still loaded — it is built for scripts. An 11 KB multi-line
   Markdown packet passed as a REAL argv element dispatches cleanly:
   `subprocess.run(["hermes","-z",packet_text,"-m",MODEL,"--pass-session-id"], cwd=worktree, …)`.
   Never route the packet through a shell, `$(cat …)`, or a PowerShell
   here-string. Keep the launcher as a `.py` under the wave's `manager-tools/`
   and write a receipt JSON per dispatch (packet sha256 + byte length, cwd,
   model, argv shape, UTC start/end, exit code, duration, log path).
3. **Force `PYTHONUNBUFFERED=1` on the child.** `hermes` is a Python CLI: with
   stdout redirected to a file it BLOCK-buffers, so a live worker's log stays at
   0 bytes for many minutes and reads as dead. Pass
   `env={**os.environ, "PYTHONUNBUFFERED":"1", "PYTHONIOENCODING":"utf-8"}` to
   `subprocess.run`; otherwise tailing the log is useless.
4. **Monitor by state.db message count when the log is still empty**:
   `select count(*), max(timestamp) from messages where session_id=?` against
   `file:<…>/state.db?mode=ro` (read-only URI). Growth = alive. Two lanes
   dispatched seconds apart both showed 19 → 42 messages while their logs were
   still 0 bytes.
5. **Map fresh sessions to tasks by their FIRST user message.** A wave dispatches
   N workers within seconds, so `hermes sessions list` shows several `—` rows
   with near-identical timestamps. That first message IS the packet header
   (`# MF-V1-GOLDEN — Worker dispatch packet`):
   `select substr(content,1,180) from messages where session_id=? and role='user' order by id limit 1`.
   Record the mapping in the wave's SESSION_REGISTRY before doing anything else —
   reporting or resuming against the wrong sibling session is an ownership defect.
6. **NEVER use `hermes sessions export <id>` to read one session** — it ignores
   your intent and dumps the ENTIRE store (960 sessions, **444 MB**) into the
   current working directory as a single JSONL named after the argument. Delete
   it immediately if it happens; use read-only SQL against `state.db` instead.
7. **Prove the route on real metadata before trusting the wave.** `GET /v1/models`
   containing the exact id is necessary but NOT sufficient. POST a tiny
   chat/completions with the key read from the Hermes config
   (`providers.<name>.api_key`) and require all three: the response `model` field
   echoes the expected model, the content is your literal probe token, and
   `usage.completion_tokens_details.reasoning_tokens > 0` (proves native thinking
   is actually ON, not merely configured). A route whose adapter exposes no
   effort field must be recorded as `effort N/A` — not as a failure. Then smoke
   the DISPATCH path once (`hermes -z "Reply exactly: <TOKEN>" -m <model>
   --pass-session-id`) so flags + launcher + route are proven in one ~2-minute
   run before spending real packets; that probe session stays separable in
   state.db afterwards.
8. **Guard the whole wave before the first worker writes.** `write_set_guard.py`
   guards files under ONE root; a wave needs an equivalent that also covers
   (a) each protected repo's HEAD + porcelain (drift / head movement),
   (b) the full tracked-blob manifest of the wave base (`git ls-tree -r HEAD` —
   1,837 blobs here), and (c) binary/media protected inputs (source films,
   before/after MP4s) by SHA-256 + size. Use `scripts/wave_guard.py`. Capture,
   re-verify IMMEDIATELY (must read VERIFIED / 0 failures — this is how you prove
   the check is real rather than post-hoc), re-verify at the final gate, and
   re-verify after every worker terminal.
9. **A wave base that is a LOCAL immutable checkpoint still needs the full
   preflight** — confirm `git rev-parse HEAD` equals the pinned SHA AND
   `git status --porcelain | wc -l` is 0 before creating any child worktree, and
   record "not pushed, never to be merged" in the wave's own docs so a later
   session does not helpfully integrate it.
10. **Put resource RELEASE in the packet, and verify it after every exit.**
    A lane authorized to run a local engine (ComfyUI, a dev server, a model
    server) will often leave it running when it submits. Observed: after the
    lane exited `0`, its server still answered on its port and held **7,452 MiB
    of 12,227 MiB VRAM at 0 % utilisation** — silently blocking the next lane on
    a single-GPU wave whose own rule is "one heavy GPU stage at a time". So:
    make "shut down the server you started, record the command + before/after
    `nvidia-smi`, confirm the port no longer answers, and add the step to your
    runtime runbook" an explicit packet requirement, then verify it yourself
    post-exit (`curl -s -m 4 <endpoint>` + `nvidia-smi --query-gpu=memory.used
    --format=csv,noheader`). Tightening a later continuation packet to fix a
    resource leak is cheap; discovering it when the next lane OOMs is not.
    Clean up only the exact PID tree the lane owns — **never**
    `killall`/`pkill python`, because the orchestrating agent is itself a Python
    process.
11. **Say what a lane is authorized to READ as well as write.** When a lane may
    touch an outside resource read-only (the user's own install, a shared model
    store), name it in the packet as read-only AND make the lane prove
    non-mutation afterwards; the Manager re-proves it independently
    (`git rev-parse HEAD` unchanged, `git status --porcelain` attributable, and
    `find <tree> -type f -newermt "-3 hours" -not -path "*/.git/*"` = 0 files).
    Recipe and false positives (`.git/index` stat-refresh, `??` entries with
    pre-dispatch mtimes): `independent-evidence-verification` §16.

## A WIDE parallel wave vs SUSTAINED upstream flaps — cut concurrency, stagger, measure damage first (verified 2026-09-23)

A 7-stream `hermes -z` wave took **two upstream flaps ~50 min apart**; every lane died on
`API call failed after 3 retries: HTTP 503: [<provider>/<model>] [502]: fetch connect timeout (reset after Ns)`
while **every launcher still returned `exit 0`** with a ~125-byte log. The route answered
`/v1/models` HTTP 200 plus a live `PROBE_OK` after each flap ⇒ transient (RULES §7), NOT a typed blocker.

Blind re-dispatch of all seven is exactly the forbidden "retry mù". The measured response:

1. **Cut concurrency 7 → 3.** Batch 1 = the lanes every downstream step gates on; batch 2 (the
   independent CPU lanes) only after batch 1 reports. Present it as a *measured* load response with
   the failure correlation, never as an arbitrary worker cap.
2. **Stagger starts ~45 s** so the streams are not mid-request at the same instant — verify it landed
   from the session start timestamps.
3. **Re-probe the route and RECORD the probe** before re-dispatching (`/v1/models` + live inference
   token). Local-gateway HTTP 200 alone does not prove completions recovered.
4. **Measure per-lane damage from disk BEFORE writing any resume packet** — per lane: evidence-file
   count, worktree `porcelain`, HEAD, and which files are dirty. That is what lets a resume differ
   correctly between *"you left a 3-file WIP, verify and finish it"* and *"you wrote nothing, start
   from the top"*; it prevents both redoing finished work and assuming an empty tree when it is dirty.
5. **Byte-snapshot each lane's WIP before re-dispatch**, so a later review diffs against a known
   baseline instead of an unknown one.

### One packet per lane per round — a MERGED packet destroys lane↔session provenance

Re-dispatching three lanes with one merged packet ("read the section for your Task ID") made the
parent→actual session mapping **unprovable**: all three first user messages are byte-identical, and
this Hermes `state.db` records **no resume parent** for worker rows (`parent_session_id`, `cwd`,
`title` are NULL). Tool RESULTS echo the packet text (contaminating keyword counts) and the
`[terminal] ran \`…\`` command echo is a UI rendering **not stored in the DB at all**.

- **Give every lane its own packet file, even when the content is 95 % identical** — that is what
  keeps `first-user-message == packet head` a valid ownership proof.
- If a merged packet was unavoidable: capture the launch-order → session-start mapping at dispatch
  time, grade the row **INFERRED** (never proven) via an explicit `actual_session_proven_by` field,
  and upgrade it only when the worker self-reports its own `HERMES_SESSION_ID`.
- **A worker's self-report can name its PARENT, not itself** — derive the actual id from the read-only
  DB plus the measured process window; never accept the self-report as the id.
- Also worth knowing when measuring a budget: a mandated "one submit" cap is verified from the raw
  engine log (submits AND sampling passes), not from the artifact count in the output dir.
- Full transcript, damage table, provenance-method matrix, ledger row shape and scripting traps:
  `references/wide-wave-flap-and-lane-provenance.md`.

## New support files

- `scripts/receipt_aware_lane_watchdog.py` — stall watchdog that does NOT cry wolf: treats an
  existing launcher receipt as `DONE(exit, not stalled)`, samples the MINTED continuation session
  ids read-only from `state.db`, and re-derives liveness from live pids. Edit the CONFIG block
  (lanes → actual session ids, receipt filenames, pid pairs) and re-run after every resume round.
- `references/turn-budget-finish-and-stall-triage.md` — the 2026-09-24 round in full: three lanes
  all `exit 0` with three different true states (complete vs budget-exhausted mid-flight), the
  finish-packet skeleton, the stall-triage order, the two post-worker guard false positives
  (porcelain `.strip()`, verified HEAD advance), and the reviewer-probe private-copy recipe
  including the Windows MAX_PATH trap that killed a third probe case.
- `scripts/wave_guard.py` — wave-level byte-safe guard (MF-RESKIN-V1,
  2026-09-17). `capture|verify` over a targets file; protects each repo's
  HEAD + porcelain, the wave base's full tracked-blob manifest, and
  binary/media inputs by SHA-256 + size. Capture then IMMEDIATELY verify
  (VERIFIED/0 failures), again at the final gate, and after every worker
  terminal. Exit 0 = VERIFIED, 1 = FAILED with per-path failures in the report.
- `references/wave-bootstrap-from-review-verdict.md` — MF-RESKIN-V1 wave
  bootstrap: turn order from review verdict → two workers running on-scope,
  evidence-root layout, packet anatomy, wave gating table, stale-governing-doc
  handling, the MSYS-worktree + `sessions export` incidents with the
  count-based post-incident verification, and the accepted ETA-table shape.
- `scripts/hermes_worker_launch.py` — shell-quoting-free dispatcher (S12-R7,
  2026-09-16): argv-list `hermes chat -q <packet file> -Q -r <sid> -m <model>
  --provider <p>` with explicit cwd and a log carrying UTC start/exit + prompt
  bytes + model/provider. Use it instead of any inline `-q "<text>"` form for
  multi-line packets. For a BRAND-NEW wave prefer the `hermes -z` form in the
  wave-bootstrap section (see `references/wave-bootstrap-from-review-verdict.md`),
  and set `PYTHONUNBUFFERED=1` in the child env either way.
- `references/two-manager-export-wave.md` — S12-R7 two-Manager split: ownership
  transfer gate, own-session-id discovery, per-lane byte guards with untracked
  snapshots, fast-forward wave-base proof, simultaneous-502 per-lane recovery
  asymmetry, inventory-freeze turn structure, route evidence, and the
  lead-with-status + ETA-slip disclosure format the user accepted.
- `references/wide-wave-flap-and-lane-provenance.md` — the sustained-502 wide-wave
  section above, in full: the 7-lane failure signature (12 receipts all `exit 0` with a
  125-byte log), the per-lane damage table measured from disk before any re-dispatch
  (which lanes left 3–4 dirty files vs wrote nothing), the 7→3 concurrency cut with the
  45 s stagger proof, the four **failed** lane↔session provenance methods (merged-packet
  content match, `parent_session_id`, tool-result keyword counts, `[terminal] ran …` echo)
  and the two that work, the auditable ledger row shape, the sqlite cursor-reuse trap and
  the never-pair-by-dispatch-order rule, verifying a mandated submit cap from the engine
  log, bounded walks (an unbounded `find` over a runtime tree hit the 300 s timeout and
  returned nothing at all), and the incident-file shape that was accepted.
- Sibling-skill cross-links (`pm-worker-orchestration/references/`):
  `gateway-502-mass-resume-cycle.md` (mass-death wave recovery: probe-gated
  resume, continuation nudge template, incident waves) and
  `contract-freeze-three-layer-pattern.md` (owner draft → Manager rulings → QA
  evidence-co-sign; evidence-grounded sign-off catches false premises — e.g. a
  pixel-vs-normalized geometry assumption that would have rejected the entire
  real chain — before any code is written).
- Sibling-skill cross-link (`independent-evidence-verification/references/`):
  `mf-v1-golden-iteration-cap-and-acceptance.md` — the exit-0-with-zero-
  deliverables case behind the iteration-cap section above: cap marker read out
  of state.db, Manager-recomputed hashes, the worker's evidenced correction of
  the Manager's own frame-space packet, a capability blocker reproduced at the
  API boundary, and the narrow continuation packet that shipped only the
  remainder.
- Sibling-skill cross-link (`independent-evidence-verification/references/`):
  `mf-v1-comfy-readonly-release-and-pins.md` — the resource-ownership half of the
  same wave (points 10–11 above): read-only proof over the user's own 71 GB
  ComfyUI install (four measured checks + the `.git/index` / July-mtime false
  positives), a registry that "pinned" workflow + node hashes while
  `model_hashes = null`, the orphaned GPU server holding 7,452 MiB at 0 %
  utilisation, the lane's 68 tests independently re-run in its own venv, and the
  bounded continuation that closed both defects.
