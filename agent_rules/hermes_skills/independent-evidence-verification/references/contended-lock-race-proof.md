# Contended-lock race proof — true rendezvous, not a held-lock control (measured 2026-10-12, MF R6 Q11)

A sequential case ("winner starts, sleep 1s, loser runs") proves a HELD lock blocks the second
controller. It does NOT prove the contested acquire/reserve is race-free — a reviewer can (and
did) reject it as non-proof. The real race needs two LIVE processes meeting at the contested
operation.

## Design

- Rendezvous immediately before the contested section: a thin WRAPPER script reads a barrier
  epoch from env, busy-waits (`while time.time() < T: time.sleep(0.002)`), then runs the
  production entry unchanged (`runpy.run_path(dispatch, run_name="__main__")`; `sys.argv`
  stays the wrapper's argv so the entry's argv-slicing is unchanged). Launch both Popen ~4s
  before `T` so startup jitter is gone; the only jitter left is a few ms of pre-acquire work.
- The contested op itself should fail fast on refusal (e.g. lock acquire with `timeout=0`) so
  the loser exits rc≠0 immediately instead of queueing.
- 3 rounds on fresh isolated roots beats 1 round; evaluate per round.

## Assertions (per round)

- rc set == {0, 4}: exactly one winner, one refusal; refusal path prints the reason
  ("controller lock held"/"gpu lease barrier") and spawns nothing.
- Exactly ONE child (spawn marker + `child_spawned` ledger row).
- Winner receipt: expected outcome + decision (e.g. CONTINUE_REQUIRED /
  PENDING_SAME_OWNER_CONTINUATION).
- Exactly one terminal record — named for the WINNER.
- End state: winner lease RELEASED; loser has NO lease file; controller lock released.

## MEASURE the ledger row composition — do not invent it

First attempt asserted `dispatch rows == 2` and failed 3/3. Measured composition of one true
race round = **4 rows**, in this shape:

1. `dispatch_refused` (reason `controller_locked`) — the LOSER's row, no invocation id;
2. `dispatch` — winner;
3. `child_spawned` — winner's child;
4. `terminal` — winner.

The loser writes NO `dispatch` row. Rule: dump the actual rows after round 1 and assert on the
measured shape (counts + named presence), never on a guessed expectation — an invented
expectation makes a green proof read FAIL (same family as a fabricated assertion failing an
intact artifact).

## Rows worth adding beyond the race

- SENTINEL: a single fresh dispatch AFTER the races still succeeds — refusal is not sticky.
- NEG cross-revision: dispatch with `--revision <new>` while the fake child writes an
  OLD-revision record ⇒ NEEDS_RECONCILIATION, never submission (an old result can never
  satisfy the new binding).
- Ordered held-lock control kept as its own, explicitly LABELLED row: "not race proof".

## Hygiene

- Fixtures/fake children live in an isolated temp root; assert no stray fake-child processes at
  exit; results JSON carries the suite's provenance hashes (dispatch/runtime/contract/wrapper/
  fake-child) so a reviewer re-runs the same bytes.
- Test files for a new round go under that round's evidence tree (e.g. `evidence/<round>/q11/`)
  so EVERY output of the round lands in the new revision — old rounds stay frozen.
