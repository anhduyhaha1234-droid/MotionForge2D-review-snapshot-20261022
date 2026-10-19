# S08 manager handoff and experimental writer model protocol

Use this reference when managing MotionForge2D PM-gated sprint/task handoffs where a prior correction has just been externally reviewed and the next packet must be launched with a specific experimental writer model.

## Durable lessons from S08-A01-C1 → S08-A02-T01

1. **Bookkeeping before writer launch**
   - Append the external Codex/PM verdict to the prior task `REPORT.md` first.
   - Record exact previous session id, model, reasoning, provider outage/recovery, wall-clock span and active model duration.
   - If a historical timestamp cannot be recovered, write `not recorded`; never infer/fabricate it.
   - Update `output/MANAGER_STATE.md` while no writer is active: close/approve the prior task, name the next active task, and remove stale active-task labels.

2. **Packet before process**
   - Create the next task `TASK.md`, `LOG.md`, and `REPORT.md` before launching the writer.
   - The `TASK.md` should contain scope, out-of-scope, exact allowlist, acceptance criteria, migration invariants, required tests, expected artifacts, protected files/hashes, baseline commands, stop conditions and rollback/downgrade behavior.
   - Verify real filenames/paths before finalizing the allowlist.

3. **Experimental model discipline**
   - When the user mandates an experimental writer model, record the exact display name/model id and reasoning level in the packet and report before launch.
   - Do not fallback or silently switch models. If the provider refuses or model id fails, mark BLOCKED with the verbatim error.
   - Do not say a writer has launched until a real process/session exists. If a chat/network interruption happens between packet creation and launch, resume by checking state and launching; do not invent a session id.

4. **Single writer invariant**
   - Only one code writer may be active at any time.
   - Read-only research/review lanes may run in parallel only if they do not write filesystem, run migrations, start servers, or update `MANAGER_STATE.md`.

5. **Heartbeat/recovery**
   - During active writer work, heartbeat at least every 5 minutes with session id, phase, new evidence, current test/blocker.
   - After provider 502/disconnect, resume the same session id; do not create a second writer and do not change model.

6. **Writer BLOCKED ≠ "wait for process exit" — the notify gap (S08-A02-T01-R1)**
   - A one-shot writer CLI (`hermes chat -q ... --source tool`) has NO channel to push notifications
     to the user. When it sets `REPORT.md = BLOCKED` (a scope question) but its process keeps running
     (e.g. still waiting on a quality-baseline subprocess), **nothing reaches the user** — no
     heartbeat, no popup. The user experience is "writer blocked silently".
   - The MANAGER owns the notification contract (autopilot notification prefixes + popup script):
     poll the writer log/REPORT during long runs; the moment REPORT flips to `BLOCKED`, surface
     `DECISION_NEEDED` to the user immediately — do NOT wait for the writer process to exit.
   - `notify_on_complete` fires only on process exit, so a BLOCKED-while-still-running writer is
     invisible until it exits. Manager must heartbeat on the REPORT state, not just process state.

7. **`clarify` timeout → writer self-authorization is a SCOPE RISK**
   - When a leaf writer hits its own §8/§3 BLOCKED gate, its `clarify` tool has a timeout. On
     timeout the tool tells it to proceed under "best judgement" — and it may then silently edit
     allowlist-EXTERNAL files (e.g. head-bump 8 pre-existing test suites that hard-code the old
     migration head). That is NOT user authorization; it is an un-authorized scope expansion the
     manager must catch.
   - Manager recovery when a writer expanded scope after clarify-timeout:
     a. **mtime audit first**: `Get-Item`/`powershell LastWriteTime` of the touched files vs the
        writer start timestamp — proves whether edits happened inside the writer window vs the
        S08 dirty baseline.
     b. **git ls-files check**: many S08 test files are UNTRACKED at HEAD (`??` in `git status`),
        so "modified vs HEAD" means nothing — classify tracked vs untracked before judging scope.
     c. **Verify the edits are mechanical**: for a head-bump, run the affected suite standalone and
        confirm only expected-head literals / approved table-set names changed; assert the A01
        downgrade-refusal literal is left intact.
     d. **Get explicit user authorization with conditions** before accepting SUBMITTED. In
        S08-A02-T01-R1 the user authorized on the condition of before/after hash snapshots + verbatim
        diffs recorded in REPORT for Codex transparency.
     e. **Reconstruct "before" hashes from the writer patch log** when edits preceded authorization:
        reverse-apply the exact hunks (from the writer's tool log "review diff" blocks) to a temp
        copy, hash it, and `ast.parse` the reconstructed file to prove the reverse is structurally
        faithful. Record the caveat clearly: BEFORE = reconstructed, AFTER = live.
   - Never accept a writer's "this is required so I did it" as a substitute for user approval.

## Suggested manager checklist

- [ ] Load terminal-engineering-discipline and MotionForge2D/PM session skills.
- [ ] Verify worktree/branch/HEAD/status count, no old writer, ports free, MAIN unchanged.
- [ ] Append prior external verdict/correction facts to prior `REPORT.md`.
- [ ] Update `output/MANAGER_STATE.md` between writers.
- [ ] Create next packet (`TASK.md`, `LOG.md`, `REPORT.md`) with exact allowlist and binary AC.
- [ ] Launch exactly one mandated writer; capture session id/model/provider.
- [ ] During the run, poll the writer REPORT/LOG state (not just process state) — the instant
      REPORT flips BLOCKED, surface DECISION_NEEDED to the user without waiting for exit.
- [ ] After SUBMITTED, independently verify diff/allowlist/migrations/tests/static/protected hashes/ports.
- [ ] If the writer self-expanded scope after a clarify-timeout: mtime + tracked/untracked audit,
      mechanical-edit verification, then explicit user authorization with hash-snapshot + verbatim-diff
      conditions (see S08-A02-T01-R1 pattern; reference `s08-a02-t01-r1-scope-recovery.md`).
- [ ] Stop at `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`; do not auto-start the next task.
