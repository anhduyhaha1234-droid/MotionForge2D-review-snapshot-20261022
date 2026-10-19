# Continuation cadence, guard classification, worker-byte snapshots

Detail bank for the dispatch/verify sections of SKILL.md. Proven on MF-RESKIN-V1
(2026-09-22, CUDA/video wave: 3 disjoint CPU workers + 1 serial GPU worker).

## 1. `hermes -z` retires a worker at the iteration cap, not at "done"

Measured on this host: workers exited `exit_code 0` after **98, 110, 122 and 126 tool
calls** (~90 budget, the header count is approximate). Consequences:

- **exit 0 ≠ task complete.** Never accept a receipt as the terminal proof; verify the
  artifacts on disk (paths, hashes, line counts) before writing any status.
- Plan **2–4 narrow continuation rounds** per non-trivial task in the ETA, and say so up
  front. A round should close named items ("A–E"), not "finish the task".
- A worker that hits the cap and writes `RUNNING` with a precise remaining list is behaving
  correctly — that is a good report, not a failure. Never reclassify it as `TASK_SUBMITTED`
  on the manager side; the worker owns its terminal state.
- Always give the packet a **priority order** ("do A first, then B, then commit, then
  shutdown") so a capped round still leaves the most valuable artifact on disk, plus a
  checkpoint rule so nothing is lost between rounds.

## 2. `--resume` mints a NEW continuation id — record parent → actual immediately

`hermes -z --resume <old-id>` creates a new session row and closes the parent
(`end_reason=agent_close`). So one Task ID legitimately spans
`R1 → R2 → R3 …` ids. In the registry keep `parent → actual`, resolve **corrections to the
ACTUAL most recent owner**, and confirm the previous process has exited before dispatching
(the old launcher's receipt is that proof). Never dispatch a second owner while an earlier
owner is still live; that is how two writers end up in one write-set.

## 3. Byte snapshots for a worker's dirty/untracked tree, taken BEFORE each dispatch

Before resuming any worker, snapshot every modified + untracked file of its own worktree
into the new evidence root (`manager/snapshots/<task>-rN/`), with SHA-256 verified at copy
time and a manifest recording path/bytes/lines/hash/match. Read the porcelain list, walk
directories for untracked ones, skip `__pycache__`, and prove `n/m hash-match`. Rationale: a
worker may end a round with **9 changed files and nothing committed**; git cannot recover
`??` files, and the snapshot is the only recovery evidence. It is recovery evidence only —
never write it back over the implementation yourself.

## 4. Guard manifests: protected-only vs task write-set (the 7-false-FAIL trap)

A byte-safe "protected" baseline that also lists the files the running worker is *supposed*
to edit will report `FAILED` on every legitimate edit. Observed: 7
`protected_file_changed` rows that were exactly the live task's own adapter files, while the
protected set was clean.

Pattern that works:

- **protected-only manifest** — everything the task must not touch (other worktrees, source
  media, canonical docs, quarantined owner bytes, frozen fixtures). Verify this for drift.
- **task-write-set preimage manifest** — the files the task owns, captured with
  SHA-256 + bytes + lines, used for shrink detection and before/after tables.
- When a guard fails, **open the report and name the paths** before reacting. Reclassify by
  rebuilding a corrected manifest from the reports — never widen a baseline to silence it,
  and never "fix" a legitimate edit.
- Re-verify after each worker terminal; a clean `VERIFIED, failures 0` on protected-only
  plus "all changed files grew, 0 shrunk" on the write-set is the pair of facts to report.

## 5. Re-run the worker's own claimed reviewer command

The cheapest independent proof is re-running the command the worker says a reviewer should
run. Hash the evidence dir before and after: reproduction looks like identical counts,
identical duration, and **only the command-ledger file changing**. Report both numbers.
Also spot-check model/asset hashes by recomputing the smallest files yourself — cheap and it
catches a fabricated manifest row immediately.

## 6. Heartbeat without a cron job: a sampling monitor process

Cron does not deliver into the desktop chat. For heartbeats, run a small background script
that appends one JSON sample per minute into `manager/logs/monitor.log` — worker process
count, GPU used MiB, listeners on the task ports, per-task log bytes, receipt present, log
tail — and exits when every receipt exists or after `--max-minutes`. It gives the manager
real liveness data (and a "log not growing" signal for the 8-minute audit) without touching
the workers or polluting the chat.

## 7. Dispatch loop shape

`hermes -z` (not `-p`), model pinned EXACTLY as the prompt requires, `PYTHONUNBUFFERED=1` so
the worker log is tail-able, one launcher invocation per task with
`packet, cwd, log, receipt[, --resume <id>]`. Record a dispatch ledger line per task (packet
sha256, model, argv, cwd, session actual id). Because stdout is block-buffered by default,
set the unbuffered env var or you will see 0-byte worker logs for 20 minutes and mistake a
working worker for a hung one.

## 8. Manager-side acceptance of an honest negative

A worker that reports `RUNNING`, `FAIL` rows, or a disclosed self-inflicted evidence loss is
producing valid results. Accept them explicitly in the next packet (name what was accepted)
so the worker never re-derives it, and keep the FAIL rows in the matrix. The two things that
must be fixed immediately are: **a server/GPU process left running without shutdown proof**,
and **evidence that was overwritten** (write each round's evidence to a NEW filename).
