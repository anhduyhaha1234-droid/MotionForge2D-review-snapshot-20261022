# True-race proof + harness probes on ACTUAL consumers (no real CLI)

Built/ran 2026-10/14 for a Q11-class requirement: "two live controllers rendezvous at the contested
acquire; exactly one winner/child; audit all records". Runs the REAL dispatch chain (never the real
CLI) under `TEST_MODE=1` + an explicit fake-child argv prefix.

## True two-controller race (the shape reviewers accept)

- Isolated run-root; each "controller" = a thin wrapper that (a) blocks until a shared wall-clock
  barrier epoch, then (b) `runpy.run_path(<dispatch.py>, run_name="__main__")` — so both processes
  are LIVE at the barrier immediately before the contested lock acquire (flock timeout=0).
- Launch both ~4 s before the barrier; join with bounded timeouts.
- Assertions that hold when the harness is correct:
  - exactly one rc0 (winner, spawns the only child) + one rc4 with `REFUSED: controller lock held`;
  - ledger row audit: exactly 4 rows `{dispatch_refused:controller_locked, dispatch, child_spawned,
    terminal}` — losers write ONLY the refusal row (no `dispatch` row);
  - winner receipt decision `PENDING_SAME_OWNER_CONTINUATION`; loser has no lease + no record;
  - lock released; lease end-state correct; bounded joins.
- Keep an ORDERED held-lock control (winner → sleep 1 → loser) but LABEL it "not race proof" —
  reviewers explicitly reject calling sequencing evidence a race proof.
- Add a SENTINEL (a further dispatch after the races succeeds → refusal is not sticky) and a
  NEGATIVE (old-revision record cannot bind new-revision dispatch → NEEDS_RECONCILIATION).
- Repeat the race ≥3 rounds; assertion drift across rounds is the signal, not one lucky run.

## Packet false-positive probesim (render-process detector safety)

If the stall-audit detector scans process cmdlines for runner scripts (python + token basename ends
with .py/.exe/.bat/.cmd/.pyd + stem contains a runner pattern e.g. `cotracker|sam2|vace|ebsynth|...`),
remember the LLM child's argv carries the WHOLE PACKET text (worst case: psutil token-splits it).
Before dispatch, scan the packet with a worst-case whitespace split and assert ZERO hits.
Backticked tokens are safe (they end with a backtick, not `.py`); bare `r6_cotracker.py`-style
tokens are NOT — backtick them or drop the extension. Run the sim against BOTH naive and
stripped forms of each token before shipping the packet.

## venv-shim descendant trap (stall audit misclassification)

On Windows the venv `python.exe` shim spawns the BASE interpreter as its child, so
`descendants_of(child_pid)` reports 1 ALIVE descendant for the entire run. Any rule of the form
"all descendants DEAD ⇒ TRUE_HANG" therefore never fires (observed: 7 audits, all misclassified
UNKNOWN, no kill). Correct rule: artifact delta OR machine-wide render probe OR busy queue ⇒
PROGRESSING/UNKNOWN (never kill); only log silence + zero artifacts + quiet render probe ⇒ TRUE_HANG.

## Stale stop-file kills a fresh monitor silently

A `HEARTBEAT_STOP` (or equivalent) left over from a prior round makes the next monitor exit on its
first tick. Before starting a monitor: rename the stale stop file with a suffix (preserve as
evidence), then start; confirm a first tick landed and shows the CURRENT invocation open. A live
monitor process is not evidence the WORKER is alive — check the lease children + log growth too.