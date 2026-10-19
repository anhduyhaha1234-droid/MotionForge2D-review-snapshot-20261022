# Hermes-CLI worker dispatch & platform owner transfer (S12-R6, 2026-09-15)

First MotionForge2D wave where workers are **Hermes CLI sessions** (not Codex) on a
local gateway route. Covers: dispatch, readiness-before-writes, Codex→Hermes owner
transfer evidence, byte guards, wave-base sync, chained heartbeats, route verification,
502 incident recovery (§9), post-merge guard re-baseline (§10), checkpoint verification
(§11), terminal-tool quirks (§12), INT transport of verified lane commits (§13).

## 1. Worker dispatch (exact pattern)

Launch from the target worktree; background + notify; console redirected to evidence file:

    cd <worktree> && hermes chat -q "$(cat <prompt-file>)" \
      -m "<exact-model-id>" --provider custom \
      -Q --yolo --accept-hooks --pass-session-id --max-turns <N> \
      > <evidence>/work-turn1-console.txt 2>&1

- Run via terminal(background=true, notify_on_complete=true). Poll liveness by console
  file size/mtime — they grow continuously while the worker is alive.
- `--pass-session-id` → worker self-reports its session id from its system prompt; `-Q`
  also prints `session_id: ...` at exit. Capture BOTH; record in registry.
- Resume the SAME owner session for later turns: identical flags + `-r <session_id>`.
  Each resume = ONE turn. If the worker returns plan-only (no writes), resume again with
  "tiếp tục làm việc đi" to force execution.
- Workers inherit the profile's global skill mandate → their first turn loads
  terminal-engineering-discipline (one extra tool call; harmless). Deepseek thinking
  routes stream thinking text into `-Q` stdout → consoles get large (100KB+); NOT an error.
- Per-invocation `-m`/`--provider` overrides work without touching global config.

## 2. Readiness-before-writes (gate pattern)

Before ANY writer turn, run a zero-write **readiness turn** per new owner. Prompt must
demand: `pwd`, `git rev-parse HEAD`, branch, `git status --short`, `git log --oneline -2`,
`ls` of a lane dir, `python --version`; report session id + model + RAW outputs +
explicit "READINESS_OK — không ghi gì". Then run the byte guards with **empty
--allow-change** (expect VERIFIED = zero drift) BEFORE dispatching the work turn.

## 3. Platform owner transfer (Codex → Hermes) evidence

Quiescence triad — record all three at activation:
1. **File activity**: `find <worktree> -path ./.git -prune -o -type f -newermt "6 hours ago"`
   empty for every task worktree (add a 40-min window for untracked dirs if copied).
2. **Git locks**: none in worktree roots or `.git/worktrees/<name>/` admin dirs.
3. **Process scan**: no Win32_Process command line references any worktree. Codex Desktop
   app + its sandbox runners, and `hermes desktop`/`hermes serve` pythons, are NOT task
   owners — attribute carefully before claiming quiescence.

Also reconcile read-only Hermes state: `hermes sessions list`, `hermes cron list`
(no dispatcher to freeze), `hermes profile list`. Old platform thread statuses
(idle/notLoaded) are historical only — never proof of quiescence. Record old→new
owner mapping + reason + HEAD + effective model + write-set in OWNER_TRANSFER.md.

## 4. Byte guards & snapshots

- Per lane, `docs/pm/tools/write_set_guard.py capture --root <wt> --manifest <pre.json>
  --path ...` for BOTH the allow set and the protected set. Verify after work with
  `--allow-change <each allowlist path>`; new files (exists:false) pass automatically when
  in --allow-change; protected drift / destructive shrink fails.
- Critical untracked/dirty bytes → byte snapshots in manager evidence (small files:
  copy + hash-verify; big trees: hash-manifest-only mode).
- **copytree symlinks pitfall (Windows)**: `shutil.copytree` default `symlinks=False`
  FOLLOWS symlinks → duplicated files and false "count mismatch" vs source. Re-copy with
  `symlinks=True` and verify: file list + symlink list + every hash equal. (Seen with
  pytest harness `*current` symlinks pointing at numbered dirs — stable since creation,
  do not mistake them for an active writer.)
- Foreign-owner worktrees (e.g. created by the Codex sandbox user) make git refuse with
  "dubious ownership" → use `git -c safe.directory='*' ...` PER INVOCATION; never write
  global config or ACL/symlink workarounds.
- `git -C /c/abs/...` can false-fail ("cannot change to") on this host → `cd` first.

## 5. Wave-base sync (conflict-free)

Verify ancestry BEFORE promising a clean sync: `git merge-base --is-ancestor <lane-tip>
<wave-base>`; if true, the lane's first git action is ONE `git merge --ff-only <wave-base>`.
No reset/clean/stash/rebase. Lanes sync their own worktrees; INT later merges each lane's
NEW commit range into the candidate branch.

## 6. Heartbeat on desktop chat (gateway off)

Cron delivery does NOT reach desktop chat → heartbeat = **chained background cycles**:

    sleep 1140; powershell -NoProfile -ExecutionPolicy Bypass -File heartbeat_collect.ps1; echo done

with notify_on_complete=true → wake-up + visible heartbeat every ~19 min. Collector
appends to HEARTBEAT.md: per-lane console size/mtime/last line + count/PIDs of live
`hermes chat` procs (Get-CimInstance filter on CommandLine). Write the collector as a
.ps1 FILE (inline PowerShell quoting breaks in bash). Re-arm the next cycle on every firing.

## 7. Custom-gateway route verification

- Exact model on wire: `curl http://127.0.0.1:20128/v1/models` → exact ID present, then a
  REAL inference probe (PROBE_OK) — catalog presence alone is not access.
- Thinking mapping: `run_agent.py::_supports_reasoning_extra_body()` returns False for
  non-OpenRouter/Nous base URLs → Hermes sends NO `reasoning`/`reasoning_effort` field;
  native thinking is gateway-side. Do not "fix" config effort=max — it never hits the wire.
- Provider `custom` without `api_mode` defaults to chat_completions; `codex_responses`
  entries pin it explicitly.

## 8. Stale exit-notices

Background exit notifications for already-processed procs arrive late (e.g. a batch of
readiness probes). Always reconcile against `process(action='list')` + console tails
before reacting; never double-process or re-dispatch on a stale notice.

## 9. Connection-error recovery for CLI worker turns (gateway 502/503)

Symptom: a worker turn's console ends with `API call failed after 3 retries: HTTP 503:
[...] [502]: fetch connect timeout` and `EXIT=1`. This is the **temporary** class — per
rules §7 it is NOT a terminal state, no matter how many lanes it hits at once (one
upstream hiccup killed 3 of 4 workers in a single window while the 4th survived).

Mandatory cycle (repeat until success / explicit user stop / proved session death):
1. **Byte-safety FIRST** — `git status --short` in each dead lane's worktree + glance at
   its evidence/runtime dirs. Deaths during read/design phases leave nothing dirty → safe
   to resume. An interrupted mid-patch death = freeze + byte-incident handling instead.
2. **Wait ≥5 min** from the failure time (policy minimum; never retry in a flurry).
3. **Liveness probe on the exact route before resume** — tiny real inference:
   `hermes chat -q "Reply with exactly: PROBE_OK..." -m <model> --provider custom -Q
   --max-turns 2`. Latency is a health signal: ~10 s normal; ~60 s = degraded upstream
   (expect further deaths, keep cycling); probe failure = wait one more cycle.
4. **Resume the SAME session, SAME route** (identical flags + `-r <session_id>`) with a
   short continuity message: the glitch was not the worker's fault; route/scope/allowlist
   unchanged; re-check current state (git status + its evidence/runtime files); continue
   from the stop point; do not redo finished work; do not ask again. Redirect output to a
   NEW console filename (`work-turn2-console.txt`) — keep the dead turn's console as
   incident evidence, never overwrite it.
5. **Record** an INCIDENT md (failure times, lanes affected, byte-safety result, probe
   result + latency, resume dispatch) and set registry status `RUNNING_RETRY_WAIT`.

Never switch provider/model to dodge the error; each resume preserves all completed work
in the session context, so cycling only costs the in-flight generation.

## 10. Guard re-baseline after a sanctioned ff-merge (false "protected drift")

Guard manifests captured BEFORE a lane's authorized `git merge --ff-only <wave-base>` will
flag many `protected_file_changed` / `guarded_file_missing` entries afterwards — the merge
legitimately rewrote tracked files (and relocated/removed some). Do not call these
violations, and do not skip checking; instead:
1. Prove merge causality: hash each flagged path in the lane worktree vs the candidate
   worktree at the wave base — identical, or missing in BOTH, counts as explained.
2. Record `all_merge_explained: true` in a manager-verify JSON next to the guard reports.
3. **Re-baseline**: capture `guard-{allow,protected}-postmerge.json` from the lane's
   post-merge state and use those for the correction-phase verification.

## 11. Manager checkpoint-verification recipe (worker turn ends EXIT=0)

Wait for PROCESS EXIT, not for the commit: workers land the transport commit mid-turn and
keep going (post-commit gates, REPORT, evidence). A clean tree + a new commit while the
console still grows = turn NOT finished — keep waiting for EXIT=0 + the final report
before starting verification.

(a) `git show --stat <sha>` — changed-file set must equal the reported set and stay inside
the allowlist; (b) `git status --porcelain` empty (sanctioned leftovers like `?? work/`
only); (c) every claimed artifact exists with bytes > 0; (d) RE-RUN the worker's own tests
yourself (short basetemp, `-p no:cacheprovider`) — count parity only holds within the SAME
scope, so record your re-run scope and reconcile per-scope, not number-vs-number
(S12-R6: RETRY 85↔85 same scope; VAL worker focused 51 / full gate 168 vs manager's
broader lane run 79 — all-pass in every scope, counts not comparable across scopes);
(e) guard verify — allow set with `--allow-change`, protected set plain (apply §10 for
merge-induced deltas). Only then flip the registry row to
`TASK_CHECKPOINT_SUBMITTED / MANAGER_VERIFIED`.

## 12. Terminal-tool quirks seen while managing

- Nested `$(...)` substitutions inside a larger compound command (e.g. a `for` loop
  calling `$(grep -c "..." "$f")`) can be rejected by the terminal tool's command parser:
  `BLOCKED (hardline): command parser limit or malformed executable payload`. Split into
  simple sequential commands with one substitution each instead of fighting the parser.
- Python heredocs (`python - <<EOF`) containing backslash or quoted sequences are mangled
  by bash before Python parses them (`SyntaxError: unterminated string literal`) — write
  the script with `write_file`, then run `python <path>` by absolute path.

## 13. INT transport of verified lane commits (candidate integration)

- Transport = `git merge --no-ff --no-edit <exact lane commit>` in the pinned order
  (S12-R6: VAL→RETRY→B01→QA), one lane at a time; conflict ⇒ `git merge --abort` +
  BLOCKED_DEPENDENCY, never hand-resolve. Sibling lane commits touching disjoint files
  merge cleanly under the `ort` strategy.
- **Transport each lane's TIP, not its first reported SHA**: owners may land a follow-up
  commit after their first report (B01: main commit `9caa223` → tip `c8830b3` docs/SHA
  commit). Re-run `git log --oneline -3` on every lane right before building the
  transport manifest; transporting the first SHA silently drops the follow-up.
- Per-merge verification: merge stdout diffstat must EQUAL the lane commit's own
  `git show --stat`; then `git diff --check <pre-HEAD> <post-HEAD>` exit 0 + porcelain
  empty. Final check: union delta = exactly the union of lane path lists
  (S12-R6: 25 = 6+5+8+6 paths, zero extra).
- Merge stderr noise: `fatal: bad object refs/codex/turn-diffs/...` +
  `error: failed to perform geometric repack` is a recurring NON-FATAL git
  auto-maintenance warning (leftover Codex-app refs, seen in earlier INT rounds too).
  Merge exit stays 0 and the commit is valid — record it verbatim in the ledger as
  known noise, do not treat it as failure.
- Turn boundary: an INT turn may end mid-order (final message describes "BƯỚC 2 — ..."
  without executing it). One dispatch = one turn → resume the same session with a nudge
  that ENUMERATES the remaining steps from the order (static gates → docs commit →
  final report), not the whole brief.
- Provenance pattern that pays off: a per-op manifest TSV (step name, argv, cwd,
  start/end UTC, exit, stdout/stderr file paths) + numbered raw logs per step
  (`VAL_02_merge.stdout.txt`, `final_03_status.stdout.txt`, …) lets any reviewer
  re-derive everything without trusting the summary.

## 14. R7 additions (S12-R7-MANAGER-A, 2026-09-16)

### 14.1 `-q` FLAG ORDER is a silent dispatch killer — use an argv-list launcher

This exits **2**, prints a usage dump, and creates **NO session**:

    hermes chat -q -Q -r <sid> -m <model> --provider custom --max-turns 60 \
      --yolo "$(cat <prompt-file>)"

→ `hermes chat: error: argument -q/--query: expected one argument`

Cause: argparse will not consume a token starting with `-` as the `-q` value, so
the flag placed right after `-q` (here `-Q`) breaks it; the prompt arriving LAST
via `$(cat)` cannot rescue it. A usage dump in the console reads like a
route/worker fault, so the mis-dispatch can burn a full monitor cycle before you
realise nothing ran. §1's shape is correct — `-q` must be IMMEDIATELY followed by
its prompt.

Robust form for 7KB+ multi-line prompts: a **Python launcher passing an argv
list** — no shell, no `$(...)`, no word-splitting, no MSYS path-mangling. Starter
in this skill: `templates/hermes-lane-launch.py`.

    subprocess.run([HERMES,"chat","-q",prompt,"-Q","-r",sid,"-m",MODEL,
                    "--provider",PROVIDER,"--max-turns",str(n),"--yolo"],
                   cwd=str(worktree), stdout=log_fh, stderr=subprocess.STDOUT)

ALWAYS prove the launch took (log exists AND grows past the banner) BEFORE
entering monitor waits. Keep the failed attempt's log as ledger evidence.

### 14.2 Shared upstream death ⇒ per-lane DIFFERENT resume packets

When several lanes die on the same hiccup at the same instant (§9), do NOT
re-send one identical packet. Measured example: lane A had NOT run its
`git merge --ff-only <wave-base>`; lane B HAD completed it and was clean.
Re-dispatching the same text would have made B redo a finished step and left A
still needing it. Per lane: measure (`git rev-parse HEAD`, `git status
--porcelain`, `git diff --name-only <review-HEAD>..HEAD`, evidence-dir contents),
then write a resume packet stating **what is measured-DONE** and what remains
(B: "verify the sync is a no-op — expect `Already up to date` + `work/` intact";
A: "perform the sync now"). Same owner session / model / provider / scope /
fallback-OFF for both.

### 14.3 Cross-lane typed error: freeze a SUBCLASS, never widen an allowlist

Lane B introduced a new typed error consumed by a dispatcher inside lane A's file.
Unmapped, it degrades to a generic 500 instead of the intended typed 409, and the
only in-scope fix would be a forbidden cross-lane edit. Manager resolution is
read-only: read the mapping chain (`except <BaseError>` → typed status; bare
`except Exception` → 500) plus the target module's existing import style, then
FREEZE a constraint on B — "the new error MUST subclass `<BaseError>` using the
file's EXISTING lazy-import pattern", which yields the typed status with ZERO
writes to A's file — and require B to prove the mapping in its report. General
rule: when a lane's new public symbol must satisfy a consumer outside its
write-set, freeze the SHAPE the existing consumer already handles (subclass /
signature / return contract) rather than granting the write.

### 14.4 Freeze the node inventory pre-code, with independently verified hashes

Protocol that caught real gaps: each owner submits (a) exact executable node IDs,
(b) param IDs per variant, (c) expected typed status + all-row/file delta per
node, (d) raw output destination, (e) proof each proposed NEW file does not yet
exist. Manager then re-hashes **every artifact the workers CLAIM** (submission
md/json, each preimage file, the reviewer probe) and confirms each claimed prefix
against disk BEFORE freezing — 8/8 matched here, which is what makes the freeze
trustworthy; `test -e` each proposed new path in BOTH lanes (6/6 proven absent) so
a later "new file" write is provably not an overwrite; record the frozen total
with "the node set may NOT shrink; missing rows must be listed explicitly". While
freezing, check write-set overlap: if two lanes' allowlists touch one file, one is
read-only for the wave — state it in the freeze instead of discovering it at
verify time.

### 14.5 Manager self-identity from the session DB

When a platform creates probe/sibling sessions seconds apart, identify YOUR own
manager session by searching `messages` for a distinctive string you just wrote
(e.g. your own tool-call payload): `SELECT session_id, role, substr(content,1,80)
FROM messages WHERE content LIKE '%<your-unique-token>%'`. Here the probe session
contained only its one-line probe reply, while the manager's payloads landed in a
different session id — matching on recency alone would have picked the wrong one.

## 15. `-z --resume` continuation rounds (2026-09-24) — see the sister reference

A later round used `hermes -z "<packet>" -m <model> --pass-session-id --resume <parent>`
with **one packet file per lane**. Full write-up + reusable monitor:

- `references/continuation-monitoring-and-vacuous-guards.md`
- `scripts/lane_heartbeat_ro.py`

Headlines (each cost real time or nearly produced a false green):

1. `--resume <parent>` mints a NEW session id. A heartbeat pointed at the PARENT reports a
   day-old timestamp + flat row count = **exactly the signature of a stalled lane**, while
   the worker was producing dozens of turns a minute. Resolve requested→actual first
   (first-user-message == own packet head), then drive the monitor with the ACTUAL ids.
2. `Path.glob("dir/**")` does not recurse in CPython — a write-set capture built on it
   returned **0 files** for a 42-file lane. An empty manifest makes the post-worker guard
   guard *nothing* and answer `VERIFIED` forever: treat `files == 0` as a FAILED capture
   and cross-check the manifest against hashes the reviewer published independently.
3. Launcher logs can stay **0 bytes** while a run is healthy — progress lives in
   `state.db` (rows / newest `tool_name` / age). To separate "waiting on upstream" from
   "hung", sample the worker process pair's CPU over 45 s: ≈0.1 s + an ESTABLISHED router
   socket = waiting, not stuck.
4. The protected-drift check after a worker must skip lanes that currently have a live
   writer (`known_active`), otherwise a correct round reports `FAILED`.
5. Cheapest scope guard, no manifest needed: `git status --porcelain` per lane, assert
   every changed path starts with that lane's allowlist prefix.

## 16. Resume-shape truth table + the decoy-directory incident (2026-09-27)

### 16.1 Two resume shapes exist — verify which one fired, every time

Measured on the MotionForge delivery takeover:

| Launch shape | Session effect | Evidence |
|---|---|---|
| `hermes -z "<packet>" --resume <parent>` | **mints a NEW successor id** | every round in §15; resolve requested→actual via first-user-message |
| `hermes chat -q "<packet>" -Q --resume <id>` | **continues the SAME session row in place** | `20260927_165838_1cbd42`: rows 196→247, api 90→114, `end_reason` stayed null |

Both shapes print the same receipt fields, so the receipt cannot tell you which happened.
After EVERY resume: re-read the DB (message count + `api_call_count` + `end_reason`) and
write `same-session-resume` vs `successor-minted` into the registry/ledger row. Get this
wrong in the successor direction and the monitor watches a stale parent (= looks like a
stalled lane); wrong in the in-place direction and the registry carries a phantom owner.

Related capacity fact: these lanes hit a hard turn budget at ~90 api calls (COMFY 89 /
QC 90 / VIDEO 90, all `agent_close` mid-backlog) — size each dispatch as ONE bounded
slice (e.g. "finish the R28 rows + commit", then a separate proof packet), never a whole
phase in one turn.

### 16.2 Worktree creation & cross-lane red gates (2026-09-29)

#### 16.2.1 `git worktree add` with an MSYS-rooted path makes a `C:\c\...` phantom that VERIFIES clean

Building a fresh per-task worktree from a shell variable holding `/c/Users/...`:

    git worktree add -b <branch> "$STAGE/C11" <base-commit>

succeeded and created the tree at **`C:\c\Users\Admin\...\C11`**. The immediate check
looked perfect — right branch, right HEAD, porcelain 0:

    $ git worktree list | grep 0929
    C:/c/Users/.../mf-delivery-20260929/C11   a52fca8 [codex/mf-end-11-c11-0929]

`grep <branch>` and `rev-parse` both confirm a tree nobody will ever `cd` into. The only
tell is the literal `C:/c/` prefix. Rules:

- Pass **native `C:/...`** to `git worktree add` explicitly; never let a `/c/...` shell
  value reach it. (Same family as §4's `git -C /c/...` false-fail and §14.1's argv list —
  prefer an argv-list Python launcher over shell interpolation.)
- Verify a worktree by asserting the **expected path literally exists**
  (`ls -d "C:/Users/.../C11"` must succeed). Branch-name greps and `rev-parse` answer a
  different question and will certify the phantom.
- Cleanup order: `git worktree remove --force "C:/c/..."` **then** `git branch -D <branch>`
  (the branch outlives the tree), `rm -rf /c/c`, re-add natively, confirm `ls -d /c/c`
  fails.

#### 16.2.2 Foreign worktrees in the shared repo are outside your guard

A worktree you did not create appeared mid-run with 740 dirty paths
(`git worktree list` on the MAIN repo, branch `codex/external-review-<date>`). Date it
before concluding anything: walk the tree bucketing by `getmtime` age (`now - m < 1800`);
2703 files in 30 min = an **active external writer**, not a stale leftover. Your write-set
guard only covers registered paths, so enumerate foreign worktrees at preflight and at each
wave boundary, record them with observed write activity, never remove them (§8.1), and raise
it before freezing if one touches your integration base.

#### 16.2.3 Cross-lane red broad gate ≠ a regression by the lane under test

A lane's broad gate returned `891 passed, 1 failed` on a NEIGHBOURING task's test:

    test_mf_end_28.py::test_28_2_builder_is_deterministic
      committed inventory.json is stale vs a fresh build
      app_tree_sha256 26ef7c09… (committed) != 1f7999ec… (fresh)

The assertion hashes the **whole `app/` tree**; the lane had legitimately changed one file
under `app/`, and that inventory belongs to a DIFFERENT task's write-set. Triage before
routing a defect:

1. Read what the assertion **hashes/compares** — an aggregate tree/raster hash spans every
   lane, so any lane touching that tree reddens it.
2. Map the artifact to a Task ID via the write-set matrix. Outside the writing lane's
   allowlist ⇒ cross-lane, not a defect.
3. Never let the lane "fix it while it's in there"; never waive/skip. Write a
   `CROSS_LANE_BLOCKERS.md` row: measured command, verbatim assertion output, mechanism,
   OWNING task id, correct ORDERING.
4. Ordering for a frozen-candidate inventory: refresh belongs to the later packaging task
   AFTER the journey is frozen and BEFORE the single final broad integration gate.
   Regenerating early re-stales it on the next `app/` change; running the final gate first
   guarantees one red for a non-product reason.
5. Count recurrences. The same seam at 4 occurrences is a **verification-ops** defect
   deserving a standing rule, not a fourth ad-hoc fix.

Signature to recognise: exactly ONE red, in a neighbouring task's file, driven by a
tree-wide aggregate — while the lane's own focused tests are green.


### 16.2 A packet path typo creates a decoy tree that swallows worker writes

Canonical evidence root `…/2026-09-27/c-v-th-c-hi-n/…`; the manager's fresh packet had
`c-v-th-c-h-i-n` (one extra hyphen). Two dispatched workers *created* the typo'd sibling
directory and wrote their first 6 artifacts there — no command errored, and the real
93-file root sat untouched. Detected ~5 min later only because a verification step
noticed the typo root held 6 files while the canonical held 93.

Protocol that contained it (reuse verbatim):

1. **Detect**: right after every dispatch, walk the evidence root and compare file count
   to the pre-dispatch count; if it is lower than expected, `ls` the PARENT — a decoy
   sibling is the usual cause. Print exact names with `repr()` when two names differ by
   one character.
2. **Stop**: kill the exact worker pids leaf→root (launcher → hermes → agent python);
   verify the pid set is gone and no interpreter count changed. Never `killall`/`/T`.
3. **Preserve**: byte-snapshot the mis-rooted files into
   `RUN/manager/snapshots/incident_wrong_root/**` with per-file sha256 + verification,
   and LEAVE the originals in place — hashed bytes are never moved.
4. **Fix + relaunch**: patch the packet (correct canonical path + a written INCIDENT
   NOTE that names the wrong spelling), relaunch the same owner sessions.
5. **Owner copies its own bytes**: the INCIDENT NOTE instructs the worker to COPY its
   orphaned artifacts into the canonical root under `raw/incident_wrong_root/` with a
   README; the manager never relocates a worker's artifacts itself. Verified in-round:
   the QC worker executed exactly that copy on its first turn back.
6. **Prevention**: copy canonical paths VERBATIM from the source document into packets —
   never retype a long path; and treat "worker idle after reading packet" + "evidence
   root not growing" as the same alarm.


