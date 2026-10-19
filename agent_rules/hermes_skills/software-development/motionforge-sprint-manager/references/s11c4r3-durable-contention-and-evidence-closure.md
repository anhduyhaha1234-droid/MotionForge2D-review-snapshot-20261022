# S11-C4-R3 durable contention + evidence closure (2026-09-05, owner 20260905_192221_6da09b)

Correction round of the same Task ID `S11-T03G-C4-R2-RECOVERY` with
production FROZEN. Write-set is test-only: `tests/test_s11_t03g_qc_check_c4r1.py`
+ append-only `docs/pm/sessions/S11-T03G/LOG.md` + `REPORT.md`. No handler,
registry, job service, persistence, detector, migration, schema, frontend,
T05/T06, S10, MAIN, S12/S13 bytes.

## 1. True-contention rendezvous must be INSIDE the production critical section

The R2 two-thread test was rejected because rendezvous happened before one
caller waited for the other to finish — it never proved the production lock
contends. Required shape:

1. Caller A enters the explicit-registration operation WHILE holding
   `_BOOTSTRAP_LOCK`, signals `entered`, then pauses on a bounded release event.
2. Start caller B while A is paused. Prove B started but has NOT returned and
   is blocked by the production transaction lock before releasing A.
3. Release A; A must fail through an injected ordinary `RuntimeError` and return
   stable `RunQcChecksError / QC_RUN_BOOTSTRAP_CONFLICT` with preserved cause.
   B must then succeed with ten exact revisions.
4. Capture and assert both raw outcomes, event-wait booleans, bounded joins,
   and the exact immediate final four-field registry snapshot/order.
5. Absolutely NO post-thread call to `ensure_full_band_registered()` or other
   repair/cleanup may occur before the final-state snapshot/assertions.
6. Run the corrected node alone first and independently inspect that rendezvous
   is inside the production operation and final state is read before repair.

## 2. Durable BaseException test (KI + SystemExit in clean subprocess)

One new test function exercising BOTH `KeyboardInterrupt` and `SystemExit`:
each performs a side effect inside explicit registration, restores the exact
pre-call four-field snapshot, propagates the original unwrapped type/message,
and cleanly reconverges ONLY after the failure assertions are complete.
Then run the four micros together (import-RuntimeError, explicit-RuntimeError,
true contention, BaseException) all green before the module run.

Expected arithmetic after adding one BaseException function: C4R1 module has
6 pytest nodes; all three T03G modules have 152 nodes. If collection differs,
STOP and explain before claiming green.

## 3. Dirty-attribution guard (5 untracked incident files)

R2 worktree `s11-c4-r2` / branch `codex/s11/c4-r2` at tip `938d759` is expected
to contain five untracked files from the frozen competing session
(`20260905_192249_150b51`) under `docs/pm/sessions/S11-T03G/evidence/c4r2/`.
They are incident evidence: enumerate each absolute path, hash, bytes, logical
lines, mtime; copy a byte snapshot ONLY into the new external `R3-final`
evidence root (never inside a worktree). Do NOT delete, modify, move, stage,
commit, clean, stash, reset, restore, or reuse them as new gate output.
Baseline-manifest allowed + protected paths (handler, job_service,
qc_check_runs, registry, job/api tests, plus the five dirty files) with
tracked/untracked/dirty attribution; snapshot the writable test authority and
every dirty file; run `write_set_guard.py` before resume, after each patch,
and at terminal, retaining raw JSON externally.

## 4. Truthful packet must index the failures, not just the greens

`NEXT_REVIEW_PACKET.md` must list every pass AND fail, including: R2's first
matrix run `129 failed, 9 passed, 13 errors`; the R2 double-dispatch timeline;
DB message 176346 at 20:04:12 +07 creating the five untracked files after the
claimed 19:55 freeze; both R2 evidence roots and their missing fields;
intended-owner patch provenance; R3 exact node arithmetic and Git ancestry.
Do not rewrite history or claim the competing session made no writes. State
precisely: no tracked production/test byte collision found, while its five
untracked worktree writes remain preserved incident evidence. INT01 integrates
only the verified correction commit; one conflict-free `--no-ff` merge is
authorized, any conflict aborts without manual resolution.
