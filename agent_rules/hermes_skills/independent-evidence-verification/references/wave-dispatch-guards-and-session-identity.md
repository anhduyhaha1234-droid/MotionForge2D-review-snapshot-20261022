# Wave dispatch guards, session identity, and long-run resilience

> See also: `harness-fixture-child-spawn-safety.md` (2026-10-07/08) — fixture child-spawn
> guards (CreateProcess does not resolve .bat; guard + fake reroute), PID-reuse identity
> (pid+creation+exe or UNKNOWN), receipt path/parse provenance (banner SID, compaction
> event counts, correction protocol), terminal classification precedence
> (latest-occurrence wins), the bounded-invocation continuation loop and the banked-wait
> pattern for out-of-invocation render work.
> Also: `deliverable-review-and-correction-handover.md` (2026-10-08) — verify a
> finished media deliverable from bytes; hand a reviewed CHANGES_REQUESTED
> correction to the same owner (pilot scope, exception preimages, quiesce legacy
> watchers, worker MINOR labels are not acceptance, deliverables not optional).
> Also: `long-run-invocation-lifecycle-and-stall-kills.md` (2026-10-08) — stall-kill forensics
> (exit1+timed_out=true; detached work keeps running), anti-stall tool-call rules (>45min
> silent blocks), continuation-packet shape, `templates/stall-terminal-monitor.py`.

Context: multi-hour delivery runs that dispatch many NEW_SESSION_ONE_TASK workers in waves
(28-task DAG). These are the mechanics that repeat every wave — encode them instead of
re-deriving them per dispatch.

## Dispatch guard recipe (before every worker launch)

1. **Worktree base = the dependency's own output commit**, not just a wave base SHA.
   `git worktree add -b <branch> <path> <dep-commit>` so the dependency is physically present
   in the tree (its tests import it). For tasks whose only dependency is an earlier wave task,
   keep the wave base and document it in the ledger row.
   * Locating which tree currently holds a given SHA in a many-worktree repo (the integration
     tree moves between rounds): `git worktree list --porcelain | grep '^worktree' | while read -r w;
     do h=$(git -C "$w" rev-parse HEAD 2>/dev/null | head -c 8); echo "$h $w"; done | grep <sha8>`.
     Never assume a path from a previous round — re-derive it before branching.
2. **Record `manager/guards/<TaskID>_before.json` before dispatch**: head SHA, porcelain count,
   and per write-set path `{exists, bytes, sha256}`. This tells the worker (and you) which paths
   are NEW (whole-file generation) vs EXISTING (bounded patch with preimage) — workers otherwise
   guess and may overwrite existing modules.
3. **Baseline tests at the base commit**: the task's own focused test file (if any) plus a light
   public suite; put the counts in the launch packet.
4. **Migration-touching tasks: resolve the head with the authoritative tool.**
   `python -m alembic heads` — NOT a hand-rolled regex scan of `down_revision`. A regex scan
   missed a declaration form and pinned a STALE head; the worker then measured the real head
   (`d4e5f6a7b8c9` vs the pinned `f7a8b9c0d1e2`), chained correctly, and disclosed the stale pin.
   That is correct worker behaviour but avoidable churn. Pin exactly ONE new migration filename
   `<revision>_<slug>.py` with `down_revision` = measured sole head.
5. **Put the guard facts INTO the launch packet** ("Manager guard đo trước"): which files exist,
   their hashes, baseline counts, plus any measured facts from earlier rounds (so the worker
   doesn't re-probe what you already measured).

## Wave sequencing

- Co-dispatch only tasks with **disjoint write-sets** — read each task packet's
  "Exclusive write-set" and require zero shared files.
- Cap = Manager + 2 workers (the Manager counts as a stream).
- Dispatch only when ALL DAG dependencies have landed (commit exists). When only one task is
  ready, leave the second slot idle and RECORD the reason in the ledger (never invent work).
- The worker's self-reported "next step" often converges with your plan — check it, but keep
  your own gate (e.g. workers propose a challenger whose weights are missing; the packet must
  pin the actually-available alternative).

## Multi-dependency transport (composing divergent dependency branches)

Later waves contain tasks that depend on SEVERAL earlier tasks whose commits sit on DIFFERENT
branches (e.g. a task needing 05 + 14 + 18, each landed separately). One worktree base SHA
cannot express that; compose it:

1. `git worktree add -b <branch> <path> <primary-dep-commit>` (dependency with the deepest own
   chain — usually the core lane).
2. For each additional dependency: `git merge --no-ff <dep-commit> -m "transport <TaskID> into <TaskID> base"`.
3. Verify `git status --porcelain` == 0 after the merges, then measure the guard against the
   COMPOSED tree.
4. Record in the guard JSON `head` = composed SHA and `transport: "<sha> (TaskID) + merge <sha> (TaskID) + ..."`;
   carry the same line into the launch packet and the ledger row so later verifiers re-derive
   ancestry from a declared recipe, not from memory.

Disjoint write-sets make these merges conflict-free in measured practice. If a merge DOES
conflict, stop: that is evidence two supposedly-disjoint tasks shared a file and the wave plan
(or the write-set audit) is wrong — fix the plan, don't hand-resolve.

## Protected files: worker pre-registration + verifier re-measurement

A task may legitimately need to touch a protected file (typically an earlier task's test whose
expectations the change invalidates). Permitted mechanism, seen working:

- Worker writes `raw/writeset_guard_protected_test_change.json` (file, impacted assertions, why)
  BEFORE patching; then patches; the writeset guard output shows porcelain == allowlist + the
  disclosed file, 0 drift.
- Verifier duties: (a) confirm the pre-registration artifact predates the patch; (b) re-run BOTH
  the task's own test file and the protected file it touched (e.g. 20 + 13 = 33 passed); (c) if a
  broader protected suite shows failures, re-run the SAME suite at the BASE commit to classify
  pre-existing vs regression, and write that classification into the ledger row verbatim.

## Session identity facts (registry-critical)

- **`hermes chat -q --resume <id>` preserves the SAME session id** — the round's actual session
  IS the parent id (no successor to reconcile). This differs from `hermes -z --resume`, which
  mints a successor id. Verify by message-count growth + `end_reason` instead of looking for a
  new id.
- After a NEW_SESSION launch, resolve the actual id by querying the newest sessions and matching
  the first user message against the packet title; never guess from launch order when multiple
  launches overlap in time.

## Killing a mis-dispatched worker (exact-PID discipline)

Process chain is nested: bash wrapper → python launcher (`mfv1_launch_delivery.py`) → `hermes
chat` → python agent. Enumerate the tree (`Win32_Process` ParentProcessId), then kill
**leaf→root by exact PID**, re-checking after each kill. NEVER `killall`/`pkill python` — the
orchestrator itself is Python. After killing: snapshot whatever the worker already wrote
(hash it, leave bytes in place), fix the packet (+ an incident note the worker will read),
relaunch the SAME session, and append the incident to the ledger.

## Long-run resilience (provider flaps at the last step)

- Symptom: a run dies after hours; log tail shows HTTP 502/503, or 422
  `messages.NNN.tool.content.str`. The 422 = oversized tool payload; 502/503 = transient flap.
- **FIRST measure disk.** Often 100% of the expensive work (GPU runs, assembly, evidence JSONs)
  is already on disk and only the final docs/append step is missing. Never re-run expensive work
  on the strength of an error line.
- Wait ≥5 minutes (RULES), then resume the SAME session/model/scope with a short finishing packet
  ("append-only docs; no GPU; no new runs").
- A DIFFERENT last-step failure is **turn-budget exhaustion** (`exit 0`, log tail
  `Iteration budget reached (160/160)`, task commit missing, disk complete): measure disk →
  resume the same session with a ≤40-call finishing packet. Full recipe:
  `references/provider-flap-and-payload-discipline.md` → "Turn-budget exhaustion".
- Add to EVERY worker packet: "print ≤200 chars per command; write files via scripts; never cat
  large files" — this is the preventive fix for the 422 payload flap.
- **Verification must not run while a writer is live in the same tree.** Before a read-only
  verification pass, check for live writer processes in the target root; if present, either wait,
  or have the verifier scope around the locked files and record it as a finding (a live writer
  during verify is itself a process-collision finding).

## Ledger discipline for long runs

- One append per event: dispatch (with resolved session id + grade), worker report (with commit
  SHA + your independent re-run counts), verify pass, gate close, provider flap note.
- Snapshot the ENTIRE current prefix as the immutable base before each append; verify
  `prefix_immutable` + row counts after every write.

## Manager independent re-run recipe (measured over ~14 task verifications)

1. **Command shape** (per task, run in the task worktree):
   `python -m pytest tests/product_delivery/test_<task>.py -q -p no:cacheprovider 2>&1 | tail -2`.
   The flag is the SPACE form — `-p:no:cacheprovider` fails with
   `ImportError: No module named ':no:cacheprovider'` (a plugin lookup, not a test failure).
   When the commit also touched a protected file, include it in the same invocation
   (e.g. `test_mf_end_05.py test_mf_end_02.py` → counts add up: 20 + 13 = 33 passed).
2. **A gate-row count is not a test count.** A lane's own gate can report `16/16 PASS`
   (rows/assertions of its final-gate script) while your pytest re-run prints `49 passed`.
   Different denominators are expected — compare exit code and `failed == 0`, never the number.
3. **Read the guard/JSON artifacts back from disk; don't trust a truncated inline print.**
   A `print(json.dumps(g)[:420])` slice cut off the `alembic_heads` field and forced a re-read.
   Slice per-key (`for k in (...): print(k, g[k])`) or re-open the file.
4. **Extraction hygiene on this host:** nested command substitution in a shell call
   (`$(grep -n ... | cut ...)`) tripped the terminal parser's blocklist. For slicing file
   sections use a python `-B -c` one-liner (`t=open(p).read(); print(t[i:i+1800])`) — quoting
   safe, no backticks, no nested `$()`.
