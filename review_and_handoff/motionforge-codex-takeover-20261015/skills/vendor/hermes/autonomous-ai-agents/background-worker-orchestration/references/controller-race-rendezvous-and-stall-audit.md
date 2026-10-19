# Controller-race rendezvous, stall-audit rules, probe guards & legacy-harness isolation (measured 2026-10-12, R6 / MF-DEMO-LONG-01)

Harness-hardening facts from closing a reviewer's "true race proof missing" finding (Q11) and
from a frozen-evidence drift incident. All numbers below were measured against the live patched
consumers (dispatch_long / invocation_runtime / terminal_contract), not theorized.

## 1. True two-controller race proof — rendezvous AT the contested lock

The reviewer will NOT accept "winner started first, loser refused 1s later" as race evidence —
that only proves a held lock blocks (keep it, but label it `CONTROL_ORDERED (not race proof)`).

Working design (34/34 assertions green, 3 rounds):

- Thin wrapper process per contender: `while time.time() < float(env["BARRIER_EPOCH"]): sleep(0.002)`
  then `runpy.run_path(<real dispatcher>, run_name="__main__")` with the real argv. Launch both
  Popen ~4 s before the barrier so both are LIVE and waiting when the barrier releases; they then
  race through the real reconcile → acquire → reserve path at the same wall-clock instant.
  The barrier is the last controllable point before the contested section — you cannot hook
  inside the dispatcher without editing it, and you should not.
- Both contenders run against the SAME isolated MF_RUN_ROOT; the dispatcher's own
  `DISPATCH_TEST=1` + explicit python fake-child prefix applies (no real CLI).
- Per-round assertion set (all measured):
  1. `sorted([rc_a, rc_b]) == [0, 4]` — exactly one winner, one refusal.
  2. Loser's stdout contains the lock-held refusal text.
  3. Exactly ONE child spawned — use a per-side marker file written by the fake child.
  4. **Ledger row algebra for a race round is EXACTLY 4 rows:
     `dispatch_refused` + `dispatch` + `child_spawned` + `terminal`.**
     The loser writes ONLY `dispatch_refused` (no `dispatch` row exists for it) — a first-cut
     expectation of "2 dispatch rows" was WRONG and failed 3/3 rounds. Derive row expectations
     from the reader code, then dump one real round's ledger rows and pin the exact set.
  5. Winner receipt: outcome `CONTINUE_REQUIRED`, decision `PENDING_SAME_OWNER_CONTINUATION`;
     exactly one terminal record under the winner's invocation id; winner lease RELEASED,
     loser lease absent; controller lock released; bounded joins (`communicate(timeout=90)`).
- Add-on cases that make the proof complete:
  - **SENTINEL**: a single dispatch AFTER the races must succeed (refusal is transient, not sticky).
  - **NEG binding**: dispatch with the NEW revision and a fake child writing the OLD revision's
    record → `NEEDS_RECONCILIATION` (older-revision result cannot bind a newer dispatch).
  - Record sha256 of the ACTUAL consumer scripts in the suite's results JSON (provenance).
- Env plumbing gotchas: pass the barrier as a float via `"%r"` formatting (locale-safe), and give
  each side its own marker/log/receipt/invocation-id so every artifact names its contender.

## 2. Stall-audit decision rule — "all descendants dead" is a broken gate (venv shim re-exec)

Measured on Windows: the venv `python.exe` is a shim that re-execs the base interpreter as its
CHILD. Consequences:

- `descendants_of(worker_pid)` returns one live python (the real worker) throughout a HEALTHY
  run; an audit that requires "all descendants dead" before classifying TRUE_HANG never fires —
  a true silent-hang case looped `UNKNOWN` audits instead of killing.
- Correct precedence (order matters):
  1. artifact delta (new files in watch roots) ⇒ **PROGRESSING** — never kill;
  2. render probe not `True` (queue busy, runner present, or probe `None`) ⇒ **UNKNOWN** — never kill;
  3. probe `True` + no artifact delta ⇒ **TRUE_HANG** — kill with a distinct classification.
- Lease `children` legitimately contain the re-exec chain (`hermes.exe` shim + `python.exe` shim +
  base python) — both ALIVE while logically ONE worker; do not read that as a double-writer.

## 3. Packet probe false-positives — simulate the tokenization BEFORE dispatch

The render probe matches live cmdlines; the worker CLI's argv contains the PACKET TEXT. Before
dispatching a packet that mentions script filenames, simulate the worst case:

- Split the packet on whitespace (naive), take `basename(token.lower())`, flag tokens that
  (a) end with an exec extension (`.py`, `.exe`, `.bat`, `.cmd`, `.pyd`), (b) don't hit the
  excludes, and (c) whose stem matches a runner pattern. Also run the same check on a
  heavily-stripped variant (trim backticks/parens/`:` suffixes) to be conservative.
- Writing file refs as `` `name.py:NN` `` (backticked, or with a line-number suffix) is SAFE —
  the basename no longer ends with `.py`. A BARE `name.py` token is what would false-positive.
- Measured: a 15 KB packet with dozens of `x.py:NN` refs → 0 candidate tokens even under the
  stripped variant. Run this sim and record the result in the dispatch ledger; it is cheap
  insurance against an audit that flags the LLM child as a render runner.

## 4. Legacy-harness reruns MUST be isolation-redirected (frozen-evidence drift incident)

Incident: a Manager regression rerun of an OLD test suite (its source hardcodes output paths of a
PAST round and rewrites a results report) executed against the REAL run root and silently
rewrote **16 frozen evidence files** (1 report + 15 receipt copies) of a closed round. A reviewer
baseline diff found them: 21 changed paths = 5 scoped/legit + 16 frozen.

Rules:
- Before re-running ANY legacy harness in a new round, redirect its output paths into the new
  round's evidence tree (or a temp root). Never point an old suite at the frozen round's real
  paths. The mechanism (hardcoded paths) explains it — report the mechanism, not a motive.
- On discovery: preserve, in the NEW round's evidence, the before/after hash pairs (the reviewer's
  drift list is authoritative) + byte copies of the CURRENT state; append a reconciliation with
  cause and the explicit policy "no restore / no backdate / no refresh"; add the drifted paths to
  the next round's protected guard.
- The same incident class includes nested-manifest staleness: a manifest entry that captures an
  artifact BEFORE its final write (e.g. a terminal record refreshed as the last action) reads as
  drift later. Policy: manifests must hash AFTER the last write of the round; a stale nested
  entry is documented in the reconcile, never fixed by rewriting the frozen manifest.
