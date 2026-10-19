# Append-only ledgers, live-progress polling, bounded monitor cadence

Measured in the MotionForge2D R27 CPU-correction round (2026-09-27, run
`20260927T051440Z`). Source of truth: `manager/dispatch-ledger.jsonl` in the
submission root — 36 historical rows, prefix SPACE that must never change.

## 1. Append-only correction of a manager ledger

Invariant: **the first N rows are immutable; the file only ever grows.**
A correction is a NEW row that names the old one — never an edit.

Event shape that survived review:

```json
{"event": "corrected_actual_session", "task": "MF-V1-BENCH",
 "corrects_ledger_line": 33,
 "recorded_actual_session_invalid": "20260926_174619_9b22c1",
 "actual_session": "20260926_173425_c114dd", "grade": "PROVEN",
 "actual_session_proven_by": "first-user-message == head of packets/<lane>.md (sha …); re-verified read-only state.db; legacy id ABSENT from state.db"}
```

Rules learned the hard way:

1. **Guard only the PREFIX, not the whole file.** The first version asserted
   `sha256(entire file) == recorded_prefix_sha` (36 rows / 29,021 B). That is
   correct for append #1 and REFUSES append #2 once the file is 41 rows /
   32,740 B. Verify `sha256("".join(rows[:N]))`, allow growth, and re-verify
   after: `prefix_sha_before == prefix_sha_after` and
   `rows_after == N + appended`.
2. Snapshot the pre-append prefix bytes next to the ledger
   (`dispatch-ledger.prefix36.before-r27.jsonl`) and write both hashes +
   byte counts + row counts into the append report JSON.
3. Open ledgers with mode `"a"` — never `"w"` (a `"w"` open destroyed 306
   rows once; see discipline pitfall #29).
4. A status suffix someone wrote into an id field (`20260924_230740_70b95b-STOPPED`)
   is an annotation; append an event that records the real id + the status
   separately. Do not "fix" the id in place.
5. Batch the whole correction set into ONE append file, run the tool, then
   batch dispatches separately — each append re-proves the prefix.

## 2. Live progress when the worker log stays 0 B

`hermes -z` launchers write the log via `subprocess.run(stdout=log)` with
`PYTHONUNBUFFERED=1`, yet the file can stay **0 B for the whole run** (the CLI
buffers its own output). An empty log is NOT evidence of a stall and NOT
evidence of a flap — the previous 125 B log-의 flap signature only appears at
exit.

Poll the ground truth instead (read-only, `mode=ro`):

* `SELECT COUNT(*), MAX(timestamp) FROM messages WHERE session_id=?` → message
  count + staleness (age_s) per lane
* `SELECT api_call_count, end_reason FROM sessions WHERE id=?` → turn budget +
  termination
* file-count inventory of each lane's evidence root + `git status --porcelain`
  of its tree → real bytes landing

The session's own row (`sessions.message_count`) is stale by design (603 vs the
1223 actual message rows in one case) — always COUNT the message rows.

## 3. Bounded monitor with per-iteration wake-ups

The binding rules forbid uncontrolled watchers AND demand a heartbeat every
≤20 min plus an 8-min stall audit. Compliant pattern:

* a Manager-owned, READ-ONLY script of bounded length (N iterations × ~480 s,
  e.g. 6 × 8 min), appending one line per poll to `manager/monitor_r27.log`
  and a `monitor_last.json` snapshot;
* launched with `terminal(background=true, watch_patterns=["iter "])` so EVERY
  iteration wakes the agent (with `notify_on_complete` you would only hear once,
  at the end, ~48 min later — too late for the ≤20 min heartbeat);
* it must never dispatch, kill, or write outside `manager/`.

Per-lane dispatch notifications are separate: launch each lane with its own
`notify_on_complete=true` and stagger with a `sleep 45;` prefix inside the
background command (45 s between upstream streams, cap 3).

## 4. Manager context health without reflexive recovery

`api_call_count` (e.g. 451) is measured against the CLI's turn-budget ceiling
(~450). A canonical manager session at/over the ceiling cannot be productively
resumed: record it as **evidence-only** with the audit numbers
(msgs / api_calls / end_reason / rewind_count) and perform the role in the
chat the user actually bridged the prompt into. Length alone (1223 messages) is
NOT a recovery trigger — the ceiling + a live bridge is.

## 5. Packet / dispatch facts worth re-checking every round

* One packet file per lane per round; the resume row records
  `parent_session` = the id the packet says, and the LIVE writer is proven by
  `first-user-message == packet head` via read-only state.db (never by dispatch
  order — `--resume` mints a new id).
* Packet sha256/bytes go into both the ledger row and the launcher receipt
  (`packet_sha256`, `packet_bytes`); packet-head match can then be quoted as a
  hash comparison.
* Worktree counting: `git status --porcelain` = "normal" entries;
  `-uall` expands directories (9 vs 14 for the same tree) — quote which one you
  measured.
