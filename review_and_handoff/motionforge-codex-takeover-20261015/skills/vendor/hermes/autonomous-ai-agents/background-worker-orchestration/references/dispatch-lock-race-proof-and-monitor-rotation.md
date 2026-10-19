# Dispatch-lock race proof, monitor rotation, and self-probe simulation

Context: an external reviewer kept a mutual-exclusion fix at UNKNOWN/PARTIAL because the test
only proved "lock held -> second controller refused" (start winner, sleep 1s, start loser).
The demanded proof: TWO LIVE processes rendezvousing at the contested acquire/reserve, with
exactly one winner. Recipe below was built and passed 34/34 (3 race rounds + controls).

## True-race proof recipe (no changes to production code)

1. Thin WRAPPER script (`r6_race_wrapper.py`): reads `R6_BARRIER_EPOCH` from env, busy-waits
   (`while time.time() < barrier: sleep(0.002)`), then `runpy.run_path(<real entrypoint>,
   run_name="__main__")` with its own argv passed through unchanged. This makes both
   processes LIVE and synchronized immediately before the contested section.
2. Launch both wrappers ~simultaneously (Popen), same isolated root, DIFFERENT invocation ids
   + receipts + logs, `DISPATCH_TEST=1` + explicit python fake-child prefix (never the real
   CLI). Barrier = now + ~4s so both are alive and waiting.
3. Assertions per round (all measured):
   - sorted(rcs) == [0, 4] (winner / lock-refused); loser stdout contains the refusal text.
   - exactly ONE child-spawn marker exists; terminal records == exactly the winner's file.
   - ledger row COMPOSITION: the winner writes `dispatch` + `child_spawned` + `terminal`;
     the loser writes ONLY `dispatch_refused` (reason controller_locked). TOTAL = 4 rows.
     Do NOT assert dispatch-row count == 2 — the loser never writes a dispatch row
     (this wrong expectation was the only test bug in the first run).
   - winner receipt outcome/decision valid; lease end-state: winner RELEASED, loser none;
     lock released; bounded join (each process exits well under timeout).
4. Keep an ORDERED held-lock control (winner -> +1s -> loser) as a SEPARATE row explicitly
   LABELED "not race proof" — the reviewer asked to preserve it, not to call it race proof.
5. SENTINEL after the races: a plain single dispatch still succeeds (proves refusals are
   transient, not sticky).
6. Cross-revision negative: dispatch revision B with a child writing a revision-A record ->
   must be NEEDS_RECONCILIATION (old-revision results can never bind a new dispatch).
7. All new test outputs go under the NEW round's evidence dir; re-run the existing suite too
   (redirect its output path via bounded patch) so old counts stay preserved (51/51 + 34/34).

## Monitor (heartbeat) rotation pitfalls

- A STOP control file from a PREVIOUS round kills the freshly-started monitor INSTANTLY.
  Before starting: check for the stale flag; RENAME it to keep bytes as evidence
  (`HEARTBEAT_STOP.r5-closed`) rather than deleting; then start; then VERIFY the process
  survives its first tick.
- Tick staleness: the monitor reads the ledger at tick start; a dispatch row landing within
  the same second shows up on the NEXT tick (open=False on one row is not a failure —
  check the following tick before diagnosing).
- After a round closes, rotate/stop the monitor deliberately; the next round needs a fresh
  start (covered above).

## Self-probe simulation before injecting big payloads

If your own audit probe scans worker process cmdlines for render-side runners (basename
endswith `.py/.exe/...` + stem-contains pattern), then a big packet text becomes part of a
worker argv item. Before dispatch, simulate the WORST-CASE tokenization of the packet text
against the probe predicate: naive whitespace split AND an ultra-conservative
stripped-token variant (strip backticks/parens/trailing `:NN`). Prove zero candidate tokens
(here: 1795 tokens, 0 hits, even stripped) — then the probe cannot false-positive on its own
worker. Keep the probe narrow (extension suffix + stem match; skip tokens >400 chars or with
newlines) so quoted full-packet argv items are always skipped.
