---
name: cli-agent-worktree-execution
description: "Run CLI agents in git worktrees: cwd guards, recovery."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [worktree, cwd, cli-agent, hermes-chat, codex, recovery, git]
    related_skills: [motionforge-autopilot, terminal-engineering-discipline]
---

# CLI Agent Worktree Execution

Run background CLI-agent task sessions (`hermes chat`, `codex exec`,
`claude -p`) inside dedicated git worktrees, verify they actually executed in
the intended tree, and recover safely when they did not.

## When to use

- Launching any CLI agent from a launcher script (`.ps1`/`.sh`) with
  `Set-Location`/`cd` into a worktree, while a desktop/daemon host for the same
  agent is running.
- Multi-task parallel delivery where each task owns a worktree (one writer per
  tree).
- Any post-run handoff where the next reviewer (PM/Codex) expects files in a
  specific tree.

## Critical pitfall (verified 2026-08-05)

**A launcher script's `Set-Location`/`cd` does NOT reliably set the child
agent's cwd when a desktop/daemon host is running.** The agent session can
execute with the DAEMON's cwd — often the MAIN repo — and silently write all
task files (code, tests, LOG/REPORT) to the wrong repository.

Verified failure: `run-s06-t05-deepseek.ps1` did `Set-Location` into
`s06-t01-review`, but the agent wrote backend/frontend/tests/REPORT into the
main tree `MotionForge2D`; the worktree's REPORT.md stayed IN_PROGRESS while
the agent self-reported SUBMITTED. The misplacement was only caught by
verifying on disk, not by trusting the agent's summary.

## Prevention — WORKDIR GUARD

First lines of every prompt passed to the CLI agent:

```
WORKDIR GUARD: Before anything else, run `pwd` and
`git rev-parse --show-toplevel`. If the toplevel is NOT <expected absolute
worktree root>, run `cd <absolute worktree root>` and re-verify. Your cwd for
ALL commands MUST be the review worktree. If it still differs, stop
WRONG_WORKTREE without writing anything.
```

Launcher script shape (PowerShell):
```powershell
$repoRoot = "C:\...\worktrees\<wt>"
$logPath  = "$repoRoot\output\<task>-hermes.log"
Set-Location $repoRoot
& hermes chat --query $prompt --source cli --max-turns 260 --provider custom `
  --model <model> --pass-session-id --checkpoints 2>&1 |
  Tee-Object -FilePath $logPath -Append
exit $LASTEXITCODE
```

## Post-run placement verification (always do this yourself)

Never trust the agent's self-report about WHERE files landed. Verify on disk:

1. `git status --short` in BOTH the worktree and the main tree.
2. Compare mtimes of the task's `REPORT.md`/`LOG.md` in both trees.
3. Classic misplacement signature: agent claims SUBMITTED while the worktree's
   REPORT.md is still IN_PROGRESS / has an old mtime.
4. Check the session log for absolute paths the agent used (grep for the
   repo-root string) — a run that should be in a worktree but greps main-tree
   paths is misplaced.

## Manager dispatched into the wrong worktree (verified 2026-09-05)

The inverse of the launcher-cwd pitfall above: the MANAGER's own dispatch
command `cd`'d into the wrong worktree, while the worker behaved correctly.
The worker analysed the task properly but committed onto the wrong tree, and
a subsequent run fast-forward merged a foreign commit into the real task
branch. Verified failure: a dispatch meant for task worktree W ran with cwd
in the integration tree instead — the worker's root-cause analysis was right,
but its output landed on the integration branch; the next dispatch then
fast-forwarded the integration merge commit into the task branch (`reflog`
showed `merge <foreign-sha>: Fast-forward` on the task branch).

Prevention — MANAGER-SIDE DISPATCH GUARD (do this in the dispatch itself):

1. Prove the target tree in the SAME command before `&& hermes chat`:
   `git -C <wt> log --oneline -1` + `git -C <wt> branch --show-current` must
   print the expected tip/branch. The wrapper exits 0 even when the worker
   fails (`bash: no job control`), so the pre-dispatch proof line is the only
   thing tying the run to the right tree.
2. Put a BRANCH GUARD in the worker prompt alongside the WORKDIR GUARD:
   expected worktree root + expected branch + expected tip, plus explicit
   bans — no `merge`/`fetch` of any other branch/commit, no touching any
   other worktree. A worker that needs another tree's commit must STOP and
   report BLOCKED instead of merging it in.
3. Post-run, verify tip + porcelain of the INTENDED worktree — not just the
   log tail. A `*_EXIT=0` line proves the wrapper ran, not that the right
   tree gained the right commit.

Recovery — branch fast-forwarded by mistake (objects still present):

1. `git reflog show <branch> --date=iso` — find the last good tip before the
   foreign `Fast-forward` entry. `git rev-parse <good-sha>` must still resolve
   (objects are intact; only the ref moved).
2. `git reset --hard <good-sha>` on that worktree, then verify
   `git log --oneline -2` shows the good tip and `git status --porcelain`
   is empty.
3. Confirm the tree that wrongly received the commit (e.g. integration) still
   shows only its own legitimate history — clean up any stray commit there
   before re-dispatching.

## Recovery — RESTORE, do not copy-over

Reusable correction-prompt template for the full recovery flow:
`references/wrong-worktree-correction-prompt.md`. False-missing quirk on
linked worktrees (MSYS `git -C <abs>` fails while the tree exists — `cat .git`
pointer check + `cd` + plain git recovery):
`references/msys-linked-worktree-false-missing.md`.

When files landed in the wrong tree:

1. **Do NOT copy the misplaced files from the wrong tree over the target
   tree.** The wrong tree may hold older/divergent code — mtime is NOT
   authority; the approved state in the target tree is.
2. RESTORE the target tree's pre-incident approved files from a backup taken
   BEFORE any copy. Always keep such backups by default
   (`output/backup-pre-copy/`).
3. Verify parity: `diff -q` every restored file against the backup — all must
   match.
4. Quarantine corrupt artifacts instead of keeping them (e.g. a test file
   written against forbidden/nested endpoints): move to
   `output/quarantine-<task>/`.
5. Re-run the focused/mandatory test suite in the TARGET tree
   (`--cache-clear`) to prove the restored approved state passes BEFORE
   redoing task work on top of it.
6. Only then reimplement the task, frontend-only or within the allowed write
   scope, on the restored base.

## Verify the launched writer's actual model/reasoning (state.db is ground truth)

The runtime banner and the launch command are NOT proof the session runs the
intended model or reasoning level. After launching `hermes chat
--provider <p> --model <m> -q "$(cat prompt.md)"`, query state.db — the
launch flag alone can be shadowed by config (e.g. a per-model
`reasoning_overrides` that silently failed to apply, see hermes-config
pitfall 8):

```python
import sqlite3, os
con = sqlite3.connect(os.path.expandvars(r'C:\Users\Admin\AppData\Local\hermes\state.db'))
con.row_factory = sqlite3.Row
for r in con.execute("SELECT id, model, model_config, started_at FROM sessions ORDER BY rowid DESC LIMIT 2"):
    print(r['id'], '|', r['model'], '|', r['model_config'])
```

- `model_config` JSON carries `reasoning_config.effort` — confirm it is the
  intended level (e.g. `high`) BEFORE letting a long writer burn quota at
  `max`. `hermes config get agent.reasoning_overrides` printing a dict does
  NOT prove it loaded as a dict (`isinstance(dict)` gate).
- Cross-check the model id spelling against the live `/v1/models` list and
  the provider `api_mode` — a 401/404 on one namespace spelling (e.g.
  `meta/muse-spark-1.2-contributor`) does not mean the sibling
  (`ocg/muse-spark-1.2-contributor`) is dead (see llm-provider-verification).

### Proving the route when you RESUME a session onto a DIFFERENT model (verified 2026-09-29)

`state.db.sessions.model` records the model the session was CREATED with — after a
resume on a new route it is stale, so it cannot prove the current round's model.
The per-request receipt in `~/AppData/Local/hermes/logs/agent.log` can:

```
INFO [<session>] agent.conversation_loop: API call #2: model=<m> provider=<p>
  base_url=... in=... out=... latency=...s cache=X/Y (Z%)
```

Two checks that make this a proof and not a grep:

1. **Grep by `model=`, not by session id.** A resumed session's log holds BOTH
   rounds (observed: 100 calls on the old model + 60 on the new one under the SAME
   session id), so `grep "<session_id>"` mixes models and proves nothing about the
   new route. The signature of a genuine route switch is the new `model=` string
   *plus* the `API call #` counter restarting at `#1`.
2. **`hermes fallback list` is separate evidence.** `No fallback providers
   configured` is the only cheap proof that fallback is OFF; the absence of a
   fallback line in the log is not.

Report both rounds' counts (old-route N, new-route M) rather than silently
crediting the whole session to the new model.

## STOP → kill → audit → relaunch (never reuse a dead writer's session)

When the user orders "stop everything" / "đổi model rồi tiếp tục" mid-run:

1. Immediately kill the writer process (`process action=kill` by session id).
2. Confirm no writer remains: `ps aux | grep -iE 'hermes.*chat' | grep -v grep`.
3. AUDIT what the killed writer touched — do NOT trust memory of its planned
   work. Compare on-disk state: `find <paths> -newermt "<kill-start>"` for
   mtimes, SHA-256 hashes of the key production files vs the pre-launch
   baseline, `git status --short | wc -l`. The killed writer's partial edits
   may already be on disk (e.g. 5 prod files DIFF + a new test file + stray
   scratch `_fix_*.py` at repo root).
4. Ask the user (or follow their STOP): revert to baseline, or KEEP the
   mid-edit files and relaunch from the on-disk state. Recording the current
   hashes in the LOG/prompt makes the relaunch deterministic.
5. Relaunch is a COMPLETELY NEW session — explicitly forbid resuming the dead
   writer's session id in the new prompt. One dead writer's session is never
   a live writer.
6. Update the writer prompt to reflect the on-disk continuation state (list
   the exact mid-edit hashes + existing in-progress test file + scratch files
   to clean up), so the new session audits rather than re-derives.

## Live log monitoring for the user

Task logs written by `hermes chat` on Windows are UTF-16LE — a raw preview
shows null bytes. To let the user watch live from the desktop/file browser:

1. Tee the run to `<worktree>/output/<task>-hermes.log` (as in the launcher).
2. Sync to a user-visible folder (e.g. the main repo's `output/hermes-task-logs/`).
3. Produce a readable tail: `iconv -f UTF-16LE -t UTF-8 <log> | tail -200 > <dst>-LIVE.txt`.
4. Run a tiny background watcher while the task runs:
   ```bash
   while true; do
     cp -f "$SRC" "$DST" 2>/dev/null
     iconv -f UTF-16LE -t UTF-8 "$SRC" 2>/dev/null | tail -200 > "$DST_LIVE" 2>/dev/null || true
     sleep 10
   done
   ```
   Kill the watcher when the task exits (it is a daemon — no notify_on_complete).
5. Open the folder/files pane and preview the `-LIVE.txt` so the user sees it
   without hunting.

## Long launcher prompts fail (verified 2026-08-05)

Embedding a large contract (~7.7KB with quotes/backticks/arrows) directly in
the PowerShell `--query` string made `hermes chat` exit with code 2 BEFORE any
work — the log contained only the echoed prompt, no session output. Symptom:
launcher exits 2 in seconds, `tail` of the log shows nothing but the prompt.

Fix — keep the launcher prompt SHORT and make the packet files the contract:
```
TASK: <task-id> - <short title> (fresh task, no resume).
Read COMPLETELY and follow EXACTLY:
1. docs/pm/sessions/<packet>/START_PROMPT.md
2. docs/pm/sessions/<packet>/TASK.md (your contract)
The packet is complete and authoritative. Implement, verify, update the packet
LOG/REPORT, set TASK status READY -> SUBMITTED after all evidence, STOP at
SUBMITTED (never APPROVED).
```
The WORKDIR GUARD stays inline (it is short); everything else lives in the
packet. Verify a short probe first: `hermes chat --query "Say OK" --max-turns 2`
must exit 0 before launching the real worker.

### Bash/MSYS variant — shell interpolation mangles multi-line prompts (verified 2026-09-16)

In git-bash, `hermes chat -q "$(cat packet.md)" ...` dies in seconds with exit 2
and `hermes chat: error: argument -q/--query: expected one argument` — the
multi-line prompt is re-split by the shell before argparse sees it. Consequences:

1. `-q "$(cat ...)"` is NOT a safe dispatch form for a real packet, regardless of
   size. Do not "fix" it by trimming the prompt — a long contract is a supported
   payload; the transport is what is broken.
2. Heredoc launchers (`python - <<'PY'`) can also be rejected by the command
   parser, so you cannot build the launcher inline. Write it to a file instead.

Fix — pass argv directly from a small Python launcher written with `write_file`:

```python
prompt = prompt_file.read_text(encoding="utf-8")
cmd = [HERMES, "chat", "-q", prompt, "-Q"]
if session_id != "-":
    cmd += ["-r", session_id]
cmd += ["-m", MODEL, "--provider", PROVIDER, "--max-turns", str(max_turns), "--yolo"]
subprocess.run(cmd, cwd=str(workdir), stdout=fh, stderr=subprocess.STDOUT, text=True)
```

No shell is involved, so multi-line/quoted/backticked prompts pass verbatim and
`cwd=` sets the worktree without `cd` interpolation. Reuse one launcher for every
lane, and write the exact argv, prompt byte count and the worker's EXIT line into
the run log so the dispatch is auditable. Validate the launcher ONCE with a
new-session probe (`-q "Reply exactly with the token: <TOKEN>"`, `--max-turns 2`)
and require the token back before dispatching real work — that single probe also
proves model route, provider and API mode end-to-end.

**Pass Windows-native paths to that launcher.** Invoking `python.exe launch.py`
with an MSYS `$A/...` variable makes Python resolve `C:\c\Users\...` →
`FileNotFoundError: can't open file`. Build the argument from a `C:/Users/...`
style string, not from an MSYS variable.

Working, field-tested launcher (argv transport + unbuffered logging + JSON
receipt capturing packet sha256/bytes, argv shape, cwd, start/end, duration and
exit code): `scripts/hermes-oneshot-launcher.py`. Dispatch one lane as
`python <launcher> <packet.md> <cwd> <log> <receipt.json> [-m <model> --pass-session-id …]`
run with `background=true, notify_on_complete=true` — never `nohup`/`&`.

## Session-per-task tracking (Codex/PM review handoff)

When a reviewer will audit each task independently, keep ONE session per task
(fresh, no resume) and record it in a tracking file the reviewer reads:

1. Every launcher run gets `--pass-session-id`; the session ID is printed at
   the end of the run (and in the log).
2. Maintain `output/SPRINT_S<NN>_SESSIONS_TRACKING.md`: table of
   task / session ID / model / started / finished / manager-verify / REPORT
   status, plus a manager-evidence section (exact pytest commands + counts).
3. Give the reviewer one instruction that names the tracking file and the
   session IDs so they open each session/log independently.

## Manager verification gate (never trust the worker's self-report)

Before opening the NEXT task in a queue, the manager must independently:

1. Confirm worker exited (process gone) and `REPORT.md` says SUBMITTED.
2. Re-run the task's focused pytest suites ITSELF (different command from the
   worker's) — never cite the worker's "passed" counts as evidence.
3. Check the MAIN tree file count is unchanged from its pre-run baseline
   (e.g. `git status --short | wc -l` — a drift means the worker wrote out of
   tree).
4. Enumerate the module's test-file inventory FIRST (`ls <wt>/tests/ | grep
   <task>`) and run ALL of them — one file is not the module. Verified
   failure: a manager verify that ran only `test_s11_t05a_readiness_api.py`
   reported 9 passed while the gate required 14/14; the other 5 lived in
   `test_s11_t05a_next_action_flip.py`. Never claim a single-file count as
   the module total.
5. Check protected-file hashes unchanged (`channels.json` SHA-256).
6. Record the result as `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` before the
   queue advances.

## Nudge pattern — run-first, theorize after (verified 2026-09-05)

A resumed worker stuck in analysis loop will read code, derive conclusions,
and even flip-flop between opposite conclusions (e.g. "fix the expect" one
turn, "nothing to change" the next) — all without ever running the failing
test on its own tree. Code-reading conclusions are hypotheses; only the test
run is ground truth. Do not accept any worker conclusion until it quotes an
actual run on the current tip.

Nudge shape that breaks the loop (one turn, no further analysis allowed):

1. Name the EXACT node to run plus the fresh-root/unset-env invocation.
2. Demand the worker report actual-vs-expected numbers FIRST
   (pass/fail + the actual value observed), and only then its conclusion.
3. Branch the next step on the number, not the theory: PASS → SUBMITTED
   immediately (a RED gate elsewhere may be stale evidence from before this
   fix landed); FAIL with actual X → patch exactly that, re-run, commit.

Verified failure: three nudges accepted analysis-only replies while the tip
never moved; the fourth nudge demanding "run the node first, report the
actual `run_state`, then decide" settled in one turn whether the expect or
the production code was wrong.

Block the "nothing to change" escape with ordering evidence. A worker that
finally runs the node may PASS on its own older-semantics tree and claim an
integrated RED gate is stale evidence ("the fix hadn't landed when the gate
ran"). Do not debate theory — quote the integration log's own
merge-then-test ordering back at it: a log line stating merge → new merge
SHA → gate still RED proves the failure ran ON the merged tree, so the
stale-evidence claim is refuted by the log itself. The next nudge then
orders the production-semantics replication on the worker's own tree, citing
both evidence halves (which tree returns what value, and why the newer
authority's contract wins).

## Isolated-worktree full-sprint manager loop (verified 2026-09-03, S11 19-task/14-wave sprint)

Full-sprint mode: one Manager chat, many waves, a few logical parallel groups.
Pattern that held end-to-end (~13.5h, zero merge conflicts, zero lost commits):

1. Activation preflight: branch/HEAD/porcelain, `ls-remote` parity, zero
   workers, DB env unset, alembic single head, plan parse (IDs/waves/parallel
   groups), fresh baseline gates.
2. Each wave: pin WAVE_BASE = clean canonical HEAD; per task create
   `codex/s11/<task>-<token>` branch + clean worktree at exactly that base;
   materialize task packet (binding block VERBATIM, never summarized) under an
   external evidence root; record baseline manifest (SHA/bytes/lines of
   allowed+protected files) BEFORE dispatch.
3. Dispatch: `hermes chat -q "$(cat prompt.md)" -m <model> --provider custom -Q`
   backgrounded with notify_on_complete, cwd = task worktree.
4. Verify AFTER exit: numstat vs WAVE_BASE (zero deletions outside allowed
   changes), fresh tests on a DIFFERENT basetemp, ruff F, protected hashes,
   scope grep — then MANAGER_VERIFIED_PENDING_SPRINT_REVIEW.
5. Integration owner = ONE persistent session (INT01) resumed for every wave:
   pre-merge proof porcelain=0 + `ls-remote == local base`; serial = ff-only,
   parallel = ff first + `--no-ff --no-edit` siblings; conflict → abort +
   BLOCKED_INTEGRATION_CONFLICT; wave gate on frozen integrated HEAD in a
   disposable detached verifier worktree; only then push non-force + ls-remote
   verify. Local-ahead: if remote == INT01's OWN last push, Manager may
   authorize the merge; foreign drift → BLOCKED_REMOTE_DRIFT.
6. Defect found post-verify (e.g. enum values vs binding contract): pause ALL
   parallel dependents BEFORE they commit; ff the defective task branch to
   canonical; resume exact owner with a finite finding matrix; after fix
   merge+push, ff dependent branches to the new canonical and resume the SAME
   sessions (context preserved) — cheaper than post-hoc corrections per task.
7. Exit gate on frozen bytes: cumulative fresh suite + protected regression +
   alembic round-trip + OpenAPI zero-dup/zero-removed + ruff/mypy + frontend
   typecheck/build/Playwright + leak scan + per-worker raw write audit, then
   coordination docs committed by INT01 and one final push.

Exact command recipe: `references/isolated-worktree-full-sprint.md`.

## Per-task dispatch into a wave (one task = one session = one worktree, verified 2026-09-28)

Full-sprint mode above is one Manager + waves; the *per-task* variant dispatches each task as a
fresh session into its own worktree under a stream cap (Manager + 2 workers). Three rules that
were load-bearing across a 28-task delivery:

1. **Branch from the DEPENDENCY'S OUTPUT COMMIT, not a stale wave base.** Once task A lands its
   commit, every task depending on A branches from A's commit — otherwise the dependency is
   physically absent from the tree and the worker stubs or re-invents its interface. Tasks whose
   dependency is the wave root share the wave base. Pin the chosen base SHA in the launch packet
   and the ledger row.
2. **Freeze a before-guard OUTSIDE the worktree** (`manager/guards/<TaskID>_before.json`):
   head/branch/porcelain + per-write-set-path `{exists, bytes, sha256}` + baseline test counts.
   `exists: false` ⇒ whole-file generation in the allowlist; `exists: true` ⇒ bounded patch with
   preimage (state this per file in the launch packet). The guard result changes the packet's
   wording, so run it BEFORE writing the packet.
3. **Resolve-and-pin contract placeholders before dispatch.** A packet field like
   `<live_head_child>` must be resolved from the actual tree and pinned literally in the launch
   packet; a guessed name leaves two heads. Resolve the alembic head with
   `python -m alembic heads` — a hand-rolled `down_revision` regex scan pinned a STALE head in the
   observed run (the worker measured the real one and disclosed it; correct behaviour, but fix the
   method, not just the instance).
4. **Multiple dependencies → transport, don't re-branch and don't cherry-pick.** Base the worktree
   on ONE dependency commit and `git merge --no-ff <other-dep-commit>` for each remaining
   dependency, recording `transport: ...` in the guard JSON; re-check porcelain 0 and that each
   dependency's test file exists in the tree before dispatch. Disjoint write-sets made every
   observed transport conflict-free.

Launch packet = operational envelope only (RULES_LOADED + task-packet path, model pin, worktree +
base, evidence root, guard/pinned facts, gate order, retry + payload-hygiene rules); the task
packet stays the scope authority and is never re-summarised. After exit verify scope
(`git show --stat` = exactly allowlisted paths), `git branch -r --contains HEAD` = 0, porcelain
clean, and re-run the task's focused + broad suites yourself. A follow-up correction commit on the
same branch is legitimate when it touches only allowlisted paths — verify both commits' stats.
Details, guard JSON shape, migration-head resolver (use `alembic heads` — the regex fallback
pinned a stale head), multi-dependency transport via `merge --no-ff`, protected-test
pre-registration, lane-monitor retargeting and RUN layout:
`references/task-dispatch-guards-and-wave-bases.md`.

## Proving a writer is idle before you touch its tree (verified 2026-09-16)

`ended_at = null` in `state.db` does NOT mean a session is running — rows are
never closed on normal turn end. Never use it as liveness proof, and never let a
stale "still running" reading block a sanctioned resume. Equally, do not treat
"the process I launched is gone" as proof an owner finished: it may have died
mid-turn, in which case the tree can hold a partial edit.

Idleness evidence that actually holds — sample at one instant, re-sample after a
settle window, and require NO change across the window:

1. per-session `SELECT max(rowid) FROM messages WHERE session_id=?` stays flat,
   compared against the live global `max(rowid)` — which DOES advance when other
   agents are working, so a flat owner rowid alongside an advancing global max is
   positive evidence the owner is idle;
2. lane `git rev-parse HEAD` and `git status --porcelain` unchanged;
3. the launcher process for that run is absent.

Write both samples plus `stable_across_samples: true` into the handoff artifact
(and the owner's last-message rowid / message count), so a reviewer can
re-derive idleness without trusting your summary. Use the same rowid comparison
BEFORE dispatch, while other agents are known to be busy.

## Pitfalls

- Do not run the same pytest suite concurrently in the same worktree as the
  running agent — cache/DB/port races produce false results. One writer owns a
  tree at a time. If you MUST verify while a worker runs, use
  `-p no:cacheprovider` and a Windows-native `--basetemp="C:/Users/.../Temp/..."`
  (MSYS `/c/Users/...` paths make Python resolve `C:\c\Users\...` →
  FileNotFoundError).
- `--cache-clear` avoids stale pytest caches masking env failures.
- On Windows use Windows-native paths (`C:/Users/...`) when invoking python/
  node against files written via MSYS paths; `/tmp/` does not map.
- Verify the launcher `.ps1` with
  `[System.Management.Automation.Language.Parser]::ParseFile(...)` before
  trusting it (pytest does not apply to PowerShell launchers).
- Long-running Playwright E2E against a long-lived Next dev server hangs on
  `page.goto`; kill the dev server and start it fresh, then re-run the suite —
  the first run after the restart uses the compiled bundle.
- MSYS git-bash: `git -C /c/Users/.../abs/path` can spuriously fail with
  "cannot change to ...: No such file or directory" while the directory EXISTS
  (recurring path-resolution quirk). Before panicking over "worktree
  vanished", verify with `ls`/`cd`; then `cd` to the parent and use relative
  `git -C <wt-name>` or plain git inside the dir.
- `core.autocrlf=true` ⇒ worktree files are CRLF while git blobs are LF:
  `sha256sum` of the disk file will NOT match the committed blob or pinned
  hashes. Compare LF-normalized bytes
  (`open(p,'rb').read().replace(b'\r\n',b'\n')`). When a pinned hash disagrees,
  check the blob in EVERY ref (branch tip, checkpoint, activation HEAD) before
  declaring drift.
- Resuming a killed CLI worker: find its REAL session id via
  `hermes sessions list` (plain recent list; the `--workspace` filter can
  return nothing for CLI runs). NEVER guess/resume another task's session id —
  if mis-targeted, kill the process immediately before it injects the wrong
  prompt into that session.
- Sharing node_modules across worktrees: a junction
  (`powershell New-Item -ItemType Junction`) serves dev servers fine, but
  Next.js Turbopack build fails ("Symlink [project]/node_modules is invalid,
  it points out of the filesystem root") — use `next build --webpack`. Verify
  `package-lock.json` hash matches the source tree before sharing.
- Background bash wrappers of finished `hermes chat` runs fire "completed
  normally" notifications LONG after the real work (hours later). Treat each
  notification as stale until you confirm state (process gone, commit/log
  present); never re-run or duplicate actions on old notifications.
- **Identify WHICH run a notification refers to before reacting.** The notice
  quotes the command that produced it, so a notice citing `turn1_run.log` says
  nothing about a later `resume1_run.log` / `code_run.log` on the same lane. In a
  resumed-wave session the superseded attempt's failure notice can arrive AFTER
  the replacement already succeeded — read the cited log, not the notice's
  arrival time.
- **An `EXIT=<n>` line is the WRAPPER's code, not the worker's verdict.** Exit 1
  with a truncated turn means the worker died mid-run: the cause is the line
  just above it (`API call failed after 3 retries: HTTP 503 … fetch connect
  timeout`). Classify that as a temporary-connection death (wait, then resume the
  SAME owner/model/scope) rather than as a task failure, and check whether the
  turn's side effects already landed before assuming nothing happened — a
  fast-forward sync may have completed before the cut.
- When a verified task's CONTRACT VALUES are wrong (e.g. enum literal names),
  structural checks + green tests won't catch it — verify enumerated
  constants byte-for-byte against the binding plan before marking verified
  (missed once → correction cascade across three downstream tasks).
- **`git worktree add` with an MSYS `/c/...` argument creates the tree SOMEWHERE
  ELSE.** `git worktree add /c/Users/<u>/.../wt-x -b br <sha>` made git resolve the
  argument as `C:/c/Users/<u>/...` — it created the worktree under a stray `C:\c`
  root, and `git worktree list` then displayed that bogus absolute path. Always pass a
  **Windows-native `C:/Users/...`** path to `git worktree add`, then confirm placement
  with BOTH `git worktree list | grep <wt-name>` (shows the resolved path) AND a real
  `ls` of the intended directory — an echoed `HEAD=<sha>` from `git rev-parse` still
  succeeds when the tree lives elsewhere, so it is not placement proof. Recovery:
  `git worktree remove --force <bogus-native-path>` → `git branch -D <branch>` →
  `git worktree prune` → re-add with the native path → re-verify HEAD/branch/porcelain.
- **MSYS-path-into-Windows-binary re-fired 2026-09-29 in THREE separate places in one
  turn.** (a) `git worktree add "$B/..."` built from an MSYS `$B` variable created the
  tree under a stray `C:\c\Users\...` — note the SAME command's `mkdir -p "$R"/{a,b,c}`
  worked fine, because MSYS tools accept MSYS paths and only the Windows binary
  re-resolves them; `mkdir` succeeding is therefore NOT evidence the next command in the
  chain will. Never build a `git worktree add` argument from a shell variable — write the
  `C:/Users/...` literal inline. (b) The dispatch launcher was handed
  `$R/manager/packets/<p>.md` and died with
  `FileNotFoundError: '\\c\\Users\\...'` before launching anything, even though the packet
  existed; pass the same argv to the launcher as a `C:/Users/...` literal. (c)
  `python -B /c/Users/.../script.py` → `can't open file 'C:\c\Users\...'`; `cd` into the
  script's directory and run `python -B ./script.py` instead. Diagnostic tell for all
  three: the error path contains a doubled `C:\c\` or `\c\` segment. Because the launcher
  exits non-zero BEFORE creating the child, a failed dispatch looks like "worker never
  started" — check the launcher log's first bytes for the path error rather than assuming
  the route or model is broken.
- **Before deleting anything at a bogus root, check what that root IS.** In the
  observed case `C:\c` was a stale **junction pointing at `C:\`**, so the misplaced
  worktrees sat inside a mirror of the entire system drive — a careless recursive
  delete there would have been catastrophic. Confirm the stray path is a link/junction
  and holds nothing but your misplaced tree before removing it, then after recovery
  re-prove the protected surface intact: `C:\Windows`, `C:\Program Files`,
  `C:\Users\<user>\*`, each repo's `git rev-parse HEAD` + tracked-file count, and the
  agent's own home (`config.yaml` bytes, skill count, session-file count, `projects.db`
  bytes). Report the counts, not an assurance.
- **A redirected child's stdout is block-buffered — the "live" log stays EMPTY.**
  Launching `hermes -z` with `stdout=<file>` yields a zero-byte log for the entire run,
  which reads exactly like a hung worker. Set `PYTHONUNBUFFERED=1` (plus
  `PYTHONIOENCODING=utf-8`) in the child's env inside the launcher, and monitor
  liveness from `state.db` (per-session message count / max rowid) rather than by
  tailing the log. Ready-made launcher with receipt + unbuffered logging:
  `scripts/hermes-oneshot-launcher.py`.
- **Do not use `hermes sessions export` to READ a session.** It streams the whole store
  to a file — observed **444,105,519 bytes** landing in the launch cwd — and a
  positionally-passed session id silently became the OUTPUT filename (bare id, no
  extension), so the large file is easy to create by accident. To inspect a session
  (map id → task, count messages, find last activity or a termination marker), open
  `state.db` **read-only**: `sqlite3.connect('file:...state.db?mode=ro', uri=True)` and
  query `messages` / `sessions`. Delete any stray export immediately.
- **Exit code 0 is not completion.** A worker can stop by exhausting the runtime's
  tool-calling budget (`agent.max_iterations`, default 90 per `hermes -z` run, no env
  override) and still exit 0 with a confident summary while the deliverable paths are
  empty. Always verify the artifact paths on disk, and read the cap marker out of the
  session's messages before assigning a cause — then size the continuation to the
  remainder rather than re-sending the whole contract.
- **Budget death on a big task ≠ lost work.** When the log tail says
  `Iteration budget reached (N/N) — response may be incomplete` and HEAD is still the
  base commit, measure disk FIRST (`git status --porcelain` + run the task's test file
  yourself): observed case had every write-set file on disk and 31 passed with only the
  commit/evidence-closure step missing. Recover by resuming the SAME session with a
  ≤40-call 4-step finishing packet that quotes the measured disk truth, closes evidence,
  commits exactly the measured paths and prints the terminal line — 5m46s vs re-doing
  hours of derivation. Full packet shape, prevention line for later packets and the
  incident-row schema: `references/budget-exhaustion-finishing-packet.md`.
