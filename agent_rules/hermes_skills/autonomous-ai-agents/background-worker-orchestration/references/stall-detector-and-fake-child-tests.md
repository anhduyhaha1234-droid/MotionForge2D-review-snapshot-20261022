# No wall-clock kill — stall-only kill, proven by fake-child tests; state gates for watchdogs

Measured 2026-10-07 (MF-DEMO-LONG-01, Windows). The progression of liveness policy in one
lineage, and the harness that proves it without waiting 6h or burning GPU:

1. total-deadline `proc.wait(timeout=remaining)` → killed healthy long tasks (budget defect);
2. `MAX_INVOCATION_S = 6h` wall-clock cap → **also a defect**: it killed a legitimate
   multi-hour child mid-render (reviewer finding F12: *"Launcher hiện kill child sau 6h
   bằng wall-clock dù policy bỏ budget"*);
3. final: kill **only on stall evidence** — the worker log stopped growing for N minutes
   (no tool output at all). Any log growth resets the patience window, so a healthy task
   that runs for days is never killed by elapsed time.

## The stall detector (drop-in shape)

```python
DEFAULT_STALL_KILL_S = 3600   # override per dispatch: --stall-kill-seconds

def _log_sig(path):
    try:
        st = os.stat(path); return (st.st_size, st.st_mtime)
    except OSError:
        return None

def wait_with_stall_detector(proc, log_path, stall_kill_s, poll_s=20):
    """Wait WITHOUT any wall-clock total cap. Kill only on real-hang evidence:
    log existed (or child never wrote one — same tolerance) and has not grown
    for stall_kill_s."""
    prev, last_growth = _log_sig(log_path), time.time()
    while True:
        try:
            return proc.wait(timeout=poll_s), False        # child exited normally
        except subprocess.TimeoutExpired:
            pass
        cur, now = _log_sig(log_path), time.time()
        if cur != prev:
            prev, last_growth = cur, now                    # growth = healthy, reset
        if now - last_growth > stall_kill_s:
            append_ledger({"action": "stall_kill", "child_pid": proc.pid,
                           "log": log_path, "silent_s": round(now - last_growth, 1),
                           "stall_kill_seconds": stall_kill_s})
            proc.kill()
            return proc.wait(), True
```

Wire-up details that matter:
- poll interval derived from the threshold: `poll = max(5, min(20, stall // 3))` — testable
  with small values, sane in production.
- The receipt records `stall_kill_seconds`; the `stall_kill` ledger row is the evidence a
  reviewer uses to distinguish "hang killed" from "task failed".
- Keep per-request timeouts on individual HTTP calls — those detect hung requests, not
  hung tasks. Removing them is not part of this fix.

## Proving it without waiting hours: fake-child tests

Do NOT try a PATH shim again — the first draft used `hermes.bat` and would have re-run the
real CLI (`.exe` beats `.bat` in Windows resolution; see `dispatcher-dryrun-safety.md`).
The correct hook is an explicit argv-prefix env var honoured by the launcher, empty in
production:

```python
_prefix = os.environ.get("DISPATCH_HERMES_ARGV_PREFIX", "").strip()
if _prefix:
    prefix = json.loads(_prefix)          # e.g. ["<venv>\\python.exe", "-B", "fake_child.py"]
    if isinstance(prefix, list) and prefix:
        argv = prefix + argv[1:]          # replace the 'hermes' token, keep the rest
```

Fake child (`fake_child.py`): reads `--mode grow|silent|exit --secs N`, writes its log to
`$FAKE_LOG` — `grow` appends a line every 2 s for N ticks; `silent` writes once then
sleeps; `exit` exits immediately with a sentinel code.

Triple test, all three must pass in one run, verdict stored as
`manager/evidence/HARNESS_TEST_<date>.json`:

| Case | Setup | Expected |
|---|---|---|
| A healthy-growth | grow, ~16 s of log growth, stall 6 s | NOT killed: exit code preserved, `timed_out False`, dt ≥ 14 s — *proves no wall-clock kill* |
| B silent-hang | silent 40 s, stall 6 s | killed at ~6–15 s: `timed_out True`, killed exit code |
| C normal-exit | exit 1 s | passthrough: sentinel exit code, `timed_out False` |

Measured result 2026-10-07: A/B/C all pass, A dt 16.1 s (no kill), B dt 15.1 s (killed on
stall), C dt 0.1 s (passthrough). Cost: ~35 s of CPU, no GPU, no 6 h wait.

## Pitfall: the fake-child test writes rows into the REAL ledger

The test launcher runs the production script, whose `LEDGER` path resolves inside the real
RUN — so three fake `dispatch/child_spawned/stall_kill/terminal` triples landed in the
production `DISPATCH_LEDGER.jsonl`. Fix is **append-only annotation, never deletion**:

```python
{"action": "test_note", "at_utc": ..., "note":
 "Rows 17:39:28Z..17:40:00Z are FAKE-CHILD harness policy tests (DISPATCH_HERMES_ARGV_PREFIX),
  NOT real worker dispatches. Evidence: manager/evidence/HARNESS_TEST_<date>.json"}
```

A reader can then distinguish test rows from production rows without the history being rewritten.

## State gates: watchdogs must not resurrect what was stopped on purpose

Self-healing watchdogs (comfy ensure + runner respawn + progress poll) need a state gate
before any resurrection — otherwise a user stop is undone within one poll cycle, and a
rejected input batch is re-armed blindly. Gate file inside the task dir
(`D/state_gate.json`): `{"gate": "USER_STOP | INPUT_QC_FAILED | RENDER_ALLOWED | COMPLETE", ...}`.
Ensure-loop logic: read gate first; spawn only when `RENDER_ALLOWED`; treat unreadable
state as UNKNOWN → do not spawn (fail closed), never as "no runner".

When the user lifts a stop by delivering a new execution packet, record an **authorization
transition** — registry status change (`USER_STOP → RESUMED_AUTHORIZED`), a new gate value
(e.g. `INPUT_QC_PENDING` until the input gate passes), a ledger row — and keep the original
stop rows as history. A stop is lifted by a recorded transition, not by deleting evidence.
