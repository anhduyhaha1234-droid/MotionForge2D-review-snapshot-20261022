# Stall-kill vs detached batch, lease watch, and the submission verify chain

Measured on MF-DEMO-LONG-01 R4 (2026-10-11). All five invocation outcomes below are from real
receipts/receipt-ledger rows, not summaries.

## 1. Stall-kill kills the LLM only — design for it
The dispatcher's stall detector (LLM log silent > `stall_kill_seconds`, here 3602s > 3600s) kills
**only the LLM child pid**. A detached render batch (separate python process, own log file) kept
running untouched; the round was resumed on the same SID with zero re-render. Discipline that made
this safe:
- The batch wrote `BUILD_STATE.json` (per-shot status) + append-only run log, so resume = read state,
  skip done shots. Never relaunch a live batch: check pid + log mtime first.
- The LLM was replanned to poll in short steps that PRINT (`sleep 600; echo POLL-n; <tally>`) and to
  yield `CONTINUE_REQUIRED` when it had nothing to do — silent waits >~20 min are the root cause of
  stall-kills (a single hour-long quiet wait triggered this one).
- Treat a stall-kill outcome as `NEEDS_RECONCILIATION`, reconcile (scope scan + batch state + lease),
  then resume same owner — it is NOT a task failure.

## 2. GPU lease must survive controller exit while a detached child runs
Contract: "controller exit does not release the lease when a detached child still runs."
Implementation: lease release probe = comfy queue idle AND no `-B` runner whose cmdline contains a
watch token. Watch tokens MUST include the batch runner's own name family (`r4_build`, `r4_render`);
with the token list too narrow the release probe reported "quiet" while the batch was mid-render and
the lease would have been wrongly released. Verify with a live probe: spawn `python -B r4_build_x.py`
(sleeper) → release attempt must return `released:false, reason:"render active"` and mark the lease
`detached:true`; kill runner → next attempt releases. 4/4 assertions held.
Also: a lease left ACTIVE by a killed controller belongs to the batch — release it (children dead +
probe quiet) after the batch finishes; don't leave it ACTIVE forever.

## 3. Heartbeat tick read-lag (one tick can under-report closure)
A tick whose iteration computes across the terminal-append instant can print
`open:true/how:"no closing terminal row"` one tick AFTER the terminal row landed (its ledger read
happened ~1–10s before the append; the write lands after the slow parts of the iteration — tree walk
with 90k files). Next tick + a manual `--once` both showed closed/`CONTINUE_REQUIRED`/
`source:structured_terminal`. Rule: judge closure on N+1 tick or a fresh `--once`; the lease/lock/
llm probes in the lagged tick were still correct — do not "fix" the consumer for this.
Probe pitfall in the same family: `psutil.process_iter(['pid','cmdline'])` then filtering on
`p.info['name']` silently matches NOTHING (name not requested) — a false "batch is gone".
And a scan command whose own cmdline contains the pattern string matches ITSELF (bash
`-c` wrappers) — filter by interpreter name too.

## 4. The submission verify chain (Manager, before PENDING_CODEX_REVIEW)
1. Re-run the validator against the record: decision must be `VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA`
   (recompute = independent read of the same bytes; rc0).
2. Recompute sha256 of EVERY artifact in the record on disk — all must equal the record. Also
   re-ffprobe the media bytes (frames/duration/audio) — never trust `R4_MASTER_QA.json` alone.
3. Guard FINAL scan → diff vs PRE: expect `changed==0, removed==0` outside allowlist, all additions
   under the round's allowed prefixes (`added_violations==0`). PRE→MID→FINAL cadence: MID per
   invocation (targeted mtime scan, cheap), FINAL full hash scan (69,712 files / 9.0 GB here, ~4–6 min).
4. Cleanup proof: lease RELEASED, child DEAD, controller lock released, queue idle — from files on
   disk, not from memory.
5. Prose inertness: the worker's prose still said CONTINUE_REQUIRED while the structured record said
   TASK_SUBMITTED — accept only the structured record and keep `legacy_prose_outcome` in the receipt:
   it is the live proof the old substring classifier would have mis-fired (F09 fix).
