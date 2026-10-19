# True two-controller RACE proof — rendezvous at the contested acquire (2026-10-12, MF-DEMO-LONG-01 R6)

An **ordered held-lock control** (start winner → sleep 1s → start loser) proves the lock
BLOCKS a late second controller. It is **not** a race proof, and a reviewer will score it
PARTIAL/UNKNOWN if presented as one (measured: R5-F09, Q11 UNKNOWN). The real proof:

## Requirement

Two LIVE controller processes rendezvous at a wall-clock barrier **immediately before** the
contested `acquire_controller_lock` / `lease_reserve`, then race through the real production
code path. Exactly ONE winner (rc0, spawns the only child) and one refusal (rc4). Bounded
joins; audit every row. The ordered control is kept as a SEPARATE labeled row
(`"NOT used as race proof"`).

## Design that worked (34/34 rows green, 3 rounds + sentinel + negative)

- **Barrier wrapper** (no production change): a thin script that spins
  `while time.time() < float(os.environ["BARRIER_EPOCH"]): time.sleep(0.002)` and then
  `runpy.run_path(<real_entry>, run_name="__main__")`. `sys.argv` passes through unchanged,
  so the real entry reads `argv[1:6]` identically.
- Launch BOTH Popen ~4s before the barrier with the same root and per-side env
  (`DISPATCH_TEST=1` + explicit python fake-child prefix; two invocation ids; two receipt/log
  paths). Both are live at the barrier; after release they hit acquire within milliseconds.
- The contested acquire uses `timeout=0.0` in the patched consumer, so contention resolves
  instantly — loser gets "controller lock held" and rc=4, no waiting loop needed.
- Repeat ≥3 rounds (fresh root per round). Add:
  - **SENTINEL** — one plain dispatch after the races still succeeds (refusal is not sticky);
  - **NEGATIVE** — a dispatch bound to revision `rN` whose fake child writes an `rN-1` record
    must land `NEEDS_RECONCILIATION` (old-revision result can never satisfy a new binding).

## What to assert per round (derive from the REAL row composition!)

Measured row composition of one contested round — **4 rows total**:

| row | writer |
|---|---|
| `dispatch_refused` (reason=controller_locked) | loser |
| `dispatch` | winner |
| `child_spawned` | winner |
| `terminal` (CONTINUE_REQUIRED) | winner |

So the counts are: `n_refused == 1 and n_disp == 1 and n_child == 1 and len(rows) == 4`.
**The loser never writes a `dispatch` row** — an initial expectation of `n_disp == 2` failed
3/3 rounds; the fix was the EXPECTATION, not the product. Lesson: when a count assertion
fails, dump the actual rows first and reconcile the expectation against the producer's real
behavior before touching anything.

Also assert: `sorted([rcW, rcL]) == [0, 4]`; loser stdout contains `controller lock held`;
exactly one spawned-marker; winner receipt `outcome_class`/`decision`; exactly ONE terminal
record (winner's); winner lease `RELEASED`, loser has NO lease file; controller lock meta has
`released_utc`; wall time bounded (< 90s both joins). Record the full ledger rows in the
results JSON as the audit evidence.

## Windows process-identity trap that breaks hang/progress audit rules

`venv/Scripts/python.exe` is a **launcher shim**: it spawns the BASE python as a CHILD.
Consequences measured in the same harness:

- `descendants_of(child_pid)` returns ONE live descendant that is actually the running
  script itself (the shim's re-exec). An audit rule "any live descendant >= progress" then
  NEVER classifies a true hang (it waited the full 90s sleep instead of killing at the
  first audit window).
- Correct rule: the process-chain re-exec is NOT render progress. Render-progress detection
  must be **machine-wide pattern-based** — arm A native-exe argv0 patterns
  (`ebsynth`, `video_blend`, `sam2`, ...), arm B `python` in prog + token basename ends with
  an exec extension and stem matches a runner pattern — with excludes for the harness's own
  files (`dispatch_long`, `test_`, ...). A TRUE hang = log silent a full window + zero
  artifact delta + render probe quiet; anything else is PROGRESSING/UNKNOWN (never kill).

## Packet-vs-probe false-positive simulation (run before dispatch)

The consumer's process matcher scans a live LLM child's argv — which contains the packet
text when the packet references script filenames. Before dispatch, simulate worst-case
tokenization: naive whitespace split of the packet + stripped wrappers (backticks, parens,
`:NN` suffixes), then run the SAME predicate (basename endswith exec-ext, stem contains a
runner pattern, not excluded). Measured: 1795 tokens, 0 candidates when every reference is
written as `` `script.py:NN` ``-style (the `:NN`/closing-backtick keeps the basename from
ending in `.py`). A packet whose tokens produce a hit will make stall-audits misread the
LLM as a renderer. Re-run the sim whenever the packet or the matcher changes.
