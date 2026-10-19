# Removing self-imposed budget caps from a live Manager harness — and the dry-run shim trap

Measured on MF-DEMO-LONG-01 run `20261005T1643Z-wan-long` (2026-10-06). When the user
"bỏ budget tự đặt" (removes PM-set caps), the Manager must apply the policy to its OWN
harness/registry — not just re-word the prompt — with preimage snapshot, per-file change
records, and consumer verification. Two non-obvious traps earned here.

## PART 1 — Apply a budget-policy change to a live harness

### Step 1: snapshot preimages BEFORE patching
The dispatcher/heartbeat may be mid-run. Copy the exact preimage of every file you will
touch (dispatcher, heartbeat, registry JSONs) into `manager/evidence/policy-preimage-<date>/`
and record sha256 / bytes / lines in a `MANIFEST.json`. Then emit
`manager/evidence/POLICY_CHANGE_<date>.json` with per-file pre/post sha256/bytes/lines so a
reviewer can diff the change.

### Step 2: remove the STOP GATE, keep the HANG GUARD
- **Dispatcher**: delete the `--deadline-epoch` "refused when remaining <= 0" return path;
  do NOT delete the wait itself. Keep the launcher waiting on a per-invocation hang guard
  (e.g. `MAX_INVOCATION_S = 6*3600`) so a truly wedged child is still killed and the Manager
  can resume the SAME owner. Never set `proc.wait(timeout=None)` — you lose hang detection
  and a wedged child blocks forever.
- **Heartbeat**: a monitor that self-exits at its own cap (`STOP_AFTER_S = 7*3600`) IS a
  self-imposed stop gate. Set it to `None` and guard the comparison
  (`if STOP_AFTER_S is not None and now - started > STOP_AFTER_S:`), otherwise `None > int`
  raises / `now-started > None` misbehaves.
- **Registry `BUDGET.json`**: relabel numeric caps as `counters_observability_only` plus a
  `stop_gates_removed` list, and park the old deadline under `old_caps_are_history`. Never
  transcribe several `UNKNOWN` counters as `0`.
- **Verify the consumer, not the file**: `py_compile` every patched tool, then grep the
  changed regions back. A `str.replace` patch can silently DUPLICATE a block (see Pitfall A).

### Pitfall A — idempotency guard re-fires when `new` CONTAINS `old`
If the replacement embeds the original text (old is `API_MODE = "chat_completions"\n`; new is
that line **plus** added policy lines), re-running the script passes a naive
`assert count(old) == 1` a second time and produces a DOUBLED block. A guard of the form
`if count(old)==0 and new in text: skip` is WRONG here — `count(old)` is still 1 because
`new` literally contains `old`. Fixes (pick one): (a) make the added text NOT contain the
anchor; (b) check `if new in text: skip` FIRST; (c) after patching, assert
`text.count(new) == 1` and collapse a known duplicate pair. ALWAYS read the region back after
patching — the diff "looks local" is not proof. (Same family as the CRLF/table patch pitfalls
in terminal-engineering-discipline: only live read-back proves the edit landed once.)

## PART 2 — Pitfall B: dry-running the dispatcher against the REAL PATH resumes a real worker
Testing `dispatch_long.py` by dropping a fake `hermes.cmd` shim on `PATH` does NOT work on
Windows: process resolution prefers `.exe` over `.cmd`, so the **real `hermes.exe` ran and
resumed the real worker session** `20261005_235131_0caeab` with a trivial test packet
(108 → ~130 msgs, ~52 s). The test *looked* contained because the temp launcher's ledger and
receipt were written to the temp root — but a live worker had actually been driven with the
test packet.

Rules:
- Never point a dry-run at a PATH that can resolve to the real CLI. Instead either
  (a) add a `--dry-run` branch to the dispatcher that prints the argv and returns BEFORE
  `Popen`, or (b) if you must shim, name it so it cannot shadow the real binary AND assert
  inside the launcher that the resolved launcher path is your shim before trusting the run.
- After ANY harness change/test, enumerate processes for the exact resume id / temp path
  (`tasklist`; `Get-CimInstance Win32_Process | Where CommandLine -match '<resume-id>|<temp>''`)
  and diff the real D's file mtimes to see what a stray run wrote.
- Prove containment from the SESSION, not the temp ledger: the temp receipt is NOT evidence
  the real session was untouched. Check the real session's message count / last state.
- Record an `incident_note` ledger row: `{summary, effect, control, lesson}`, and DISCLOSE
  rather than hide. Real harm here was limited to extra P1 contact-sheet frames in D
  (`work/grid2/*`, 29 files) — no clip/output/commit, no real RUN ledger row.

## PART 3 — truncation recurrence under "no budget" policy
The W0 worker died on repeated `finish_reason='length'` (long inline reasoning + giant inline
`python -c` tool args → model cut mid-call → "refusing to execute incomplete tool arguments"
→ session exited, exit 0). The W1 continuation packet must make this explicit: no inline
python/JS in `-c`; `write_file` a small script (<~120 lines, split by function) and run it;
terminal lines ≤200 chars, one action each; short reasoning; file edits via bounded patch with
preimage. Telling the worker once is not enough — it re-truncated in W1, so treat truncation
control as a first-class section of every continuation packet, not a one-line reminder.
