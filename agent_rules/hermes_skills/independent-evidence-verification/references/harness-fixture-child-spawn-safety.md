# Harness fixture safety: child spawn, identity, receipt paths (2026-10-07)

Context: MF-DEMO-LONG-01 context recovery. Manager patched a dispatch/heartbeat
harness and ran offline fixtures. Five failure classes measured live; all fixes
verified by a 24-case offline suite (no GPU, fake children only).

## 1. A fixture CAN silently invoke the real binary — guard the spawn
- `Popen`/`CreateProcess` does **not** resolve `.bat`/`.cmd` via `PATHEXT` (only
  appends `.exe`). A fixture that shims `hermes.bat` on PATH therefore ran the
  **real hermes.exe** with the fixture prompt (stray session + tool calls before
  it was killed; contained only because the cwd was a temp dir).
- Fix pattern: (a) a test-only env guard in the launcher — if `DISPATCH_TEST=1`
  and the argv-prefix override is unset, **refuse to spawn** (exit non-zero);
  (b) fixtures route the child through an explicit argv prefix to a python fake
  (writes its own argv to a file so the test proves the FAKE engaged, not just
  "a process started"); (c) after any fixture run, scan process cmdlines for the
  fixture prompt and for the fake path; (d) never rely on PATH ordering.
- "Process started" is not proof the harness hooked the intended child — capture
  the child's argv/log output and assert on it.

## 2. PID existence is not aliveness — identity or UNKNOWN
- `tasklist /FI "PID eq N"` reported a **conhost** as the live worker because the
  old worker's PID was recycled. Record identity **at spawn** (pid + creation
  timestamp + exe name; optionally cmd hash) in the ledger's `child_spawned` row,
  then verify per poll: same pid AND same creation AND same exe → ALIVE; pid dead
  → DEAD; query failure → **UNKNOWN** (never collapse UNKNOWN to zero/dead).
- The terminal row must also carry `launcher_pid`/`child_pid`, otherwise the
  monitor's "open invocation" list never closes (every old child looks live).

## 3. Receipt path bugs read as "<none>", not as errors
- A monitor joined `RUN`(already the manager dir) + `"manager"` → looked in
  `manager/manager/` and reported no receipt forever. Resolve the receipt FROM
  THE LEDGER invocation (latest dispatch row), validate it against the expected
  directory, and write the resolved path into every monitor row so a reviewer
  can see which file was actually read. Close invocations by `launcher_pid` and,
  for legacy rows, by receipt **basename** (path spellings drifted between
  rounds and an exact-string compare never matched).
- Same for terminal rows: a missing terminal row (historical gap) must be
  detectable; only the LATEST dispatch counts as "current invocation".

## 4. Encoded defaults are policy — don't leave stale ones
- Defaults in a harness encode task policy. Stale `max_tokens=131072` vs a
  1,048,576 total context left no headroom → provider HTTP400; stale "stop when
  process exits" logic misclassified exit0-with-error as completion. Update
  defaults with the policy, record requested vs effective in the receipt, and
  keep terminal classification machine-readable.

## 5. Outcome classification: exit code alone is never "completed"
- Classify from the log payload: `CONTEXT_EXHAUSTED` (compaction-limit / context
  markers), `OUTPUT_TRUNCATED`, `QUOTA_BLOCKED`, `USER_STOP`,
  `CONTINUE_REQUIRED`, `SELF_REVIEW_PASS_PENDING_CODEX`, `ITERATION_YIELD`;
  fall back to `EXIT0_NO_KNOWN_MARKER` (read payload) / `EXIT_NONZERO`, never
  "completed". Match **case-insensitively** (CLI logs capitalise markers) — a
  case-sensitive substring made a correct classifier fail its own fixture and,
  worse, would silently miss real terms.
- **Token precedence: the LATEST occurrence wins** (rfind per marker, pick the
  max position; ties by list order). List-order scanning let a forward-looking
  plan line ("SELF_REVIEW_PASS_PENDING_CODEX only when the whole master passes")
  beat the real terminal (`CONTINUE_REQUIRED`) in W5. Verified v2.2 on W2r/W4/W5
  with expected positions; keep the worker contract's exact final line anyway.
- Stall detector: log-growth silence is the signal, but a multi-GB session load
  is legitimately silent for minutes — a reasonable stall-kill during load is
  correct; distinguish "no growth + no queue job + no output deltas" (kill) from
  "no log growth but render queue/GPU active" (wait).

## 6. Log-parse provenance: session id + compaction counts (2026-10-07)
- **The FIRST sid literal in a worker log is usually WRONG.** The log opens with
  `Query: <packet>`; a packet that mentions an old session id contaminates
  `findall(...)[0]` — the W4 receipt recorded the OLD sid while the run belonged to
  the new one. Prefer the exit banner: `Session:\s+(sid)` / `hermes --resume (sid)`,
  take the LAST match; fall back to the last generic sid literal. Re-verify the
  parser on BOTH logs: the unaffected one AND the affected one.
- **Authoring corollary (packet side):** keep OTHER session ids out of a
  new-session packet, and keep terminal status tokens (CONTINUE_REQUIRED /
  SELF_REVIEW...) out of plan and instruction lines — state the expected terminal
  token ONCE, on the final line. A "helpful" recap of the token inside a plan
  bullet is what poisoned the W5 receipt (classifier saw the plan token first).
- **Count compaction EVENTS, not substrings.** Each event logs both
  `⟳ compacting context…` and `🗜️ Compacting context — summarizing earlier
  conversation…` (a case-insensitive substring count doubles: 3 events -> 6), and
  the agent's own prose mentions "compaction" (W4: naive count 3, real 0). Count
  the banner line only; cross-check a log with known events (W2r = 3 events, per
  the review quoting lines 699/15832/22934).
- **Parser-artifact correction discipline:** never edit the receipt bytes to make a
  field agree; fix the parser, assert it on both logs, and append a
  `receipt_field_correction` row to the ledger (recorded vs correct + why + fix).
  Keep the old value visible so a reviewer sees exactly what was double-checked.
- **If the real binary DID run (stray-incident follow-up):** kill exact PIDs
  leaf->root, prove no collateral (pid-set diff on the never-kill interpreter),
  verify integrity of anything it could have touched (read-only DB query: message
  count / max timestamp unchanged), dump its tool calls to confirm read-only, and
  disclose in evidence. Containment proof is part of the record, not an apology.

## 7. Manager continuation loop for bounded worker invocations (proven W4->W5)
- Run each invocation with a bounded turn budget (80) and require the worker to
  checkpoint and end with `CONTINUE_REQUIRED` before ~turn 60-65. Measured: a 2h
  invocation closed at 201 msgs with checkpoint v3 on disk and the terminal
  classified CONTINUE_REQUIRED from the log payload (exit0 != done; 0 real
  compactions). The bounded invocation is an orchestration boundary, never a task
  stop gate.
- Manager on invocation end: (1) read receipt + ledger terminal row; (2) verify
  the worker's claims against disk — and check the gate JSON's REAL structure
  before concluding a field is missing (hashes are often nested
  `{anchor: {sha256: ...}}`; a top-level key check mis-reports "missing"); (3)
  re-check protected sets; (4) write a compact continuation packet: point at the
  worker's own checkpoint file, list its next actions, restate invariants — no
  history dump; (5) dispatch a resume of the SAME sid with notify-on-complete;
  (6) record a manager-verify JSON in the evidence root.
- The monitor reads the LATEST dispatch row + its receipt for open/closed +
  outcome; exit0 is unclassified until the log payload is read. Background
  notify-on-complete wakes the Manager turn when the invocation ends.

## 8. Banked-wait: out-of-invocation work outlives the round (proven W5->W6)
- When a round yields while heavy work continues OUTSIDE the invocation (Comfy
  render under a detached watchdog), do NOT dispatch the next invocation just to
  poll — it burns the turn budget. Instead:
  (a) write the next packet + `run_<round>.cmd` up front so dispatch is instant
  when the work settles;
  (b) run a small read-only waiter in the background with notify-on-complete:
  settle = queue empty AND no runner process, sustained 2 checks (~120 s poll);
  compute a pending count (files present vs plan) so "idle but pending" is
  flagged IDLE_PENDING (stall signal) rather than SETTLED; cap the wait (~3 h)
  with a distinct timeout exit;
  cross-check the pending count against BOTH ledgers — routes that never touch
  the GPU runner (2d-source/doc2d shots) leave no rows in the WAN ledger, so
  "missing ok-rows" can be a cross-ledger artifact; verify files on disk +
  per-file frame counts (measured: 15/15 block files summing to exactly the
  planned 2386f = settled, not stalled).
  Match runner processes by SPAWN SHAPE (`-B\s+\S*p4_wan_run_v2\.py`): a scan
  whose match expression contains the target string also matches its own shell
  children (self-match seen twice) — sample twice before declaring "no process";
  (c) the heartbeat stays the state monitor (separate llm/render/controller
  flags); the waiter is only a wake-up signal;
  (d) on notify, dispatch the next round `--resume <same sid>` and record in the
  round's manager-verify JSON that render was in flight (queue prompt id, runner
  pids, watchdog row, pending counts).

## Verification checklist for harness fixtures
- [ ] Real-CLI invocation impossible by construction (guard + fake reroute)
- [ ] Fake engagement proven from its own output (argv/sentinel), not process exit
- [ ] Identity captured at spawn; PID-reuse and query-failure paths both tested
- [ ] Receipt resolution tested against a decoy `manager/manager/` tree
- [ ] Defaults assert current policy values; outcome classes tested case-mixed
- [ ] Post-run: rescan for stray processes; census python/hermes diffs empty
- [ ] Sid/compaction parse asserted on BOTH the affected log and a known-good log
- [ ] Continuation packet points at the worker's checkpoint; receipt read before
      trusting exit0
- [ ] Packet carries no foreign session ids; terminal tokens appear only on the
      final line (plan lines free of them)
- [ ] Waiter (if any) distinguishes SETTLED vs IDLE_PENDING; heartbeat stays
      independent of the waiter

> See also: `deliverable-review-and-correction-handover.md` (2026-10-08) —
> verifying a FINAL media deliverable from bytes (sha/decode/frames/streams/
> contact-sheet) and dispatching a reviewed CHANGES_REQUESTED correction round
> (pilot scope, write-set exceptions with preimages, quiesce legacy watchers,
> deliverables-are-not-optional).

## 9. Stall-kill: LLM silence vs detached progress (2026-10-08, measured C1#1)
- The dispatch harness kills the child after `stall_kill_seconds` (3600) of NO LOG
  growth; the receipt then shows `exit_code=1, timed_out=true` even though the log
  payload still classifies CONTINUE-ish. Treat it as an invocation boundary, NOT a
  context failure: resume the SAME sid (no transfer) — session/context stay healthy.
- The trap: a watcher that resets its "progress" timer on ANY disk growth hides an
  LLM stall. C1#1 measured: the worker blocked silently ~60 min mid-tool-call while a
  detached render kept writing clips — an aggregate-progress monitor saw nothing
  wrong; a LOG-ONLY timer would have alerted at 20 min. Keep TWO independent signals:
  LLM log growth (model-turn liveness) and render/queue progress (work liveness);
  alert on LLM silence >= 20 min while alive, BEFORE the 60-min kill lands.
- Worker contract (put it in the continuation packet): never block > 45 min in one
  tool call with zero output; poll <= 10 min printing progress (clip count, queue,
  receipt rows) so the log keeps growing; detached runners are fine, silent waiting
  is not.
- ROOT CAUSE of the blocking call (measured twice: C1#1 and C2 — it IS the LAUNCH
  call itself): a bash `&`/nohup-style detach leaves the child holding the tool
  call's stdout/stderr pipe, so the call waits forever for pipe EOF even though the
  batch is already running on disk. Mandatory launch primitive: `powershell
  Start-Process -RedirectStandardOutput <f> -RedirectStandardError <f>` (breaks
  handle inheritance; the call returns at once). Never ship a packet with a
  `&`-style detach without a one-time proof that the launch call returns < 60 s.
- Do NOT early-kill a silent worker whose batch is mid-flight: C2 woke when its
  batch completed (44 min quiet) and finished the run cleanly. Let the harness
  stall-timer decide; kill early only after confirming no in-flight work.
  Cross-ref: `background-worker-orchestration/references/stall-kill-pipe-hang.md`.
- After a stall-kill: inventory DISK + PROCESS state FIRST (the detached work may
  have progressed a lot — adopt, never relaunch; check queue, receipts, output
  files), then dispatch a continuation packet that states what already landed and
  forbids duplicate launches.
