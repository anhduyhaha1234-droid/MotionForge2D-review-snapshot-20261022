# Live progress measurement, 502-flap recovery, ledger corrections

Source: MotionForge2D R27 CPU-correction fleet, 2026-09-27 (`outputs/mf-cpu-input-correction-20260927/20260927T051440Z`).
Fleet: 3 concurrent `hermes -z` lanes under a 3-upstream-stream cap + 1 queued docs lane.

## 1. An empty stdout log is NOT a stall — measure from the DB + disk

Measured: three lanes ran ~26–30 min with `PYTHONUNBUFFERED=1` and **every stdout log was 0 B the entire run**
while the read-only session DB showed 30–77 messages, climbing `api_call_count`, and the worktrees were already
patched. The log received only a terminal payload at exit — 124/125 B of
`API call failed after 3 retries: HTTP 503: [..] [502]: fetch connect timeout (reset after Ns)`.

Heartbeat probe (read-only, `mode=ro`), one JSON per poll:

- per lane session: `COUNT(*) FROM messages`, last-message `timestamp` → `age_s`, `sessions.api_call_count`,
  `end_reason`, first-user-message head (mapping re-proof);
- per lane tree/evidence: file inventory under the evidence root + newest names, `git status --porcelain` count.

Verdicts: empty log + growing `messages` + `age_s` < 8 min = healthy (the log size is NOT a signal).
`age_s` > 8 min and `end_reason IS NULL` = stall audit (process alive? waiting on input? 502 line?).
`end_reason = agent_close` + a 503/502 payload in the log = flap, NOT a task result (grade it from the payload).

## 2. Flap → resume discipline

Timeline: two lanes died within 9 s of each other (05:52:44Z / 05:52:53Z; logs 124/125 B). Manager waited the
full 5 minutes, then resumed each lane on the same model/scope/write-set.

Resume checklist:

- **Resume the ACTUAL session** (the one holding the work), not the older parent; `--resume` mints a new id, so
  re-prove with first-user-message == new packet head.
- **One NEW packet file per resume** (`<LANE>-r27cpu-resume.md`). Reusing the old packet destroys the mapping
  proof: both sessions would share a byte-identical first message.
- The resume packet carries the Manager's MEASURED disk state, not a plan: files landed with deltas
  (`adapter.py +51/−0, 3 regions`), probe counters (`prefix submit_calls=2 → postfix submit_calls=1`), the exact
  failing rows (`6 passed / 2 failed`, both `JSONDecodeError: Unterminated string`), the remaining step list, and
  "do not restart finished work; same model/scope/write-set".
- **`%TEMP%` is not durable evidence.** One lane parked its prepared patch in `%TEMP%\r27_patch\patch_r27.py` and
  died; tree and evidence root were both empty. State plainly: apply it into the tree via bounded
  patch-with-preimage and re-create every raw artifact under the evidence root.

## 3. Bounded monitor for heartbeat cadence

`notify_on_complete` fires only at exit; a 40-min lane leaves the orchestrator blind. A 6-iteration × 480 s
read-only monitor that prints one line per poll (`[05:46:58Z] iter 1/6 | COMFY: 66msg api=26 ev=6 age=125.9s
end=None | …`) and is launched with `watch_patterns=['iter ']` wakes the orchestrator every ~8 min — matching a
≤ 20-min heartbeat / > 8-min stall-audit cadence. Mutually exclusive with `notify_on_complete` (both set →
`watch_patterns` is silently dropped). Keep it bounded and read-only: writes only to `manager/` (log + last
snapshot), never dispatches or kills — an unbounded poller would be an unsupervised watcher.

## 4. Append-only ledger corrections: verify the PREFIX, not the file

1. Before the first append: record `prefix_rows` / `prefix_sha256` / `prefix_bytes` and snapshot those bytes
   next to the ledger as rollback evidence.
2. Verifier refuses to append when the immutable prefix no longer hashes to the recorded value.
3. After each append: re-read, assert `prefix_sha256_after == before` and `rows_after == prefix_rows + appended`.
4. Whole-file sha256 is valid only BEFORE the first append. Once appends accumulate, assert on
   `lines[:N]` — a whole-file compare starts failing the moment a second batch lands. The mis-scoped guard's
   refusal reads `REFUSED: ledger has 41 rows, expected 36` — a COUNT assertion rejecting a file that is correct
   by the real invariant (`sha(lines[:36])` still equals the recorded prefix). Scope it to
   `sha(lines[:N]) == prefix_sha` AND `len(lines) >= N`; never `== N`.
5. Corrections are new events that reference the old row/line number; never edit or delete old rows. Real cases
   this round: recorded session ids absent from the DB (corrected to packet-match-proven ids), a `-STOPPED`
   suffix that was a status annotation rather than part of the session id, and a latest-actual registry refresh
   that names its DB proof method inside the row.

## 5. Two more fleet facts

- **Slot math.** `running + resumed ≤ cap`: a lane's flap frees a slot but its own resume consumes it, so a queued
  lane waits for the FIRST lane that finishes cleanly. Record why every slot is unused ("CONTRACT queued — 3/3").
- **Manager session at the turn-budget ceiling.** `api_call_count` ≈ 450 with `end_reason=null` means the
  canonical orchestrator session is at the ceiling; resuming risks immediate recovery. When the user bridges the
  prompt into a fresh chat, that chat performs the role for the round — record the audit + bridge as a ledger
  event (canonical session evidence-only, no duplicate lineage, no owner transfer claimed).

## 6. Re-point EVERY probe after each resume (stale-session trap)

A flap-resume changes the lane's actual id (COMFY `…122256` → resumed `…130100`; QC `…122348` → `…130203`). The
monitor and heartbeat tool written BEFORE the resume kept polling the dead parents and printed, tick after tick:

    COMFY: 70msg (+0msg) api=28 ev=6 age=1863.4s end=agent_close

That is indistinguishable, at a glance, from a lane that died and produced nothing — while the resumed session was
already at 47+ messages with files on disk. Rules:

- On every resume, update the session ids in the heartbeat probe AND launch a freshly-scoped monitor; diff its
  session list against the ledger's latest `actual_session` rows before trusting a single tick.
- Give the new monitor its own log (`monitor_r27.log` vs `monitor_r27b.log`) — appending fresh ticks into the stale
  monitor's log mixes a dead session's `end=agent_close` rows with live ones and poisons the evidence.
- The stale tick's `age_s` grows past every stall threshold, so the false alarm is guaranteed, not sporadic.
- A monitor launched with `watch_patterns` does NOT also fire on exit — when it is the only live wake source, launch
  its successor BEFORE the bounded run ends, or accept a silent gap until the lanes finish.

## 7. Turn-budget exit (exit 0, work landed, closing steps missing) → FINISHING packet

Measured this round: VIDEO14B ran 4,909 s (~82 min), exited 0 with a 6,528 B log whose tail self-declared
`CHƯA XONG (3 việc)` — REPORT.md + MATRIX.md, run the deliverables script, local commit. Gates were green
(micro 13/13, related matrix ALL_MATCH, focused clean, broad 48 passed / 1 failed / 1 skipped); the single red test
was a sha pin in `tests/test_video14b_roundD.py:156` — OUTSIDE the write-set.

Shape of the finishing packet (short, ~25 tool calls budget):

- Enumerate the log's own remaining-steps list verbatim as numbered steps; state "do NOT redo finished work, do NOT
  change scope, do NOT touch the GPU".
- Order the steps so the durable record lands first: REPORT.md + MATRIX.md (with per-file old→new bytes/sha and the
  raw gate counts), then the deliverables generator (record its exit code), then the local commit with the
  shrink-guard byte/line delta per file.
- **Out-of-scope failures are DISCLOSED, never fixed.** The failing test stays red, the packet requires the exact
  test id + failure reason in REPORT.md plus the resolution options left open for the reviewer ("orchestrator re-runs
  the retained generator to rewrite the stale JSON, or the reviewer drops the pin"). Editing a test outside the
  write-set to make a broad gate green is a scope violation, not a fix.
- Record the finishing pass as its own ledger row: `parent_session` = the ACTUAL id that exited on budget (resume
  chains), plus the measured list of what it left undone — so the next reader can see the budget boundary was
  measured, not assumed.

## 8. Generating per-round monitor/heartbeat variants: block replacement + syntax check, never chained sed

Every resume needs a freshly-scoped monitor (new session ids, its own log). First attempt used a chained `sed`:

```bash
sed -e 's/monitor_r27b.log/monitor_r27c.log/' \
    -e 's/"COMFY": "...1dc76b"/"P1QC": "...e1527d"/' \
    -e 's/"P1QC": "...e1527d"/"VIDF": "...910880"/' monitor_r27b.py > monitor_r27c.py
```

Each `-e` runs against the PREVIOUS one's output, so the third substitution re-matched the key the second had just
renamed: the shipped file carried a **duplicate `"VIDF"` dict key plus a stale `"VIDEO14B"` entry** — silently,
because Python keeps the last duplicate key. A monitor that measures "whatever the last duplicate says" is worse
than no monitor: it prints a retired session as if it were live and omits the lane that matters.

Correct shape: read the source, replace the WHOLE config block with an explicit literal, write, then verify before
launching:

```python
out = re.sub(r'LANES = \{.*?\}', new_lanes_literal, src, count=1, flags=re.S)
out = out.replace('monitor_r27b.log', 'monitor_r27c.log')
open('monitor_r27c.py', 'w', encoding='utf-8').write(out)
ast.parse(open('monitor_r27c.py', encoding='utf-8').read())  # + print the LANES block back
```

Same rule for the heartbeat/guard tools that carry a LANES dict, and for any per-round fork of a launcher.

**Editing a monitor's file does NOT re-point the instance already running.** Python loaded `LANES` at process start,
so after you rewrite `monitor_phaseb_b.py` with the new lane set the LIVE process keeps printing the retired lanes
(measured 2026-09-28: the running instance still showed a finished task's stale row and flagged `STALL_AUDIT` for it,
while the file on disk listed the two live lanes). Fork a NEW file (`monitor_phaseb_c.py`) with its own log, launch
that, and let the old bounded instance run out its remaining iterations and die — never kill it mid-flight and never
trust its rows after the lane set changed.

## 9. Slot bookkeeping when the round has nothing left to dispatch

`slot_note` ledger row shape for a deliberately idle slot: `"slots": "2/3 in use after <LANE> exit — <running lanes>;
the freed slot is intentionally LEFT UNUSED: every authorized scope of this round has been dispatched, the remaining
lanes (<list>) are idle by the authorizing prompt's instruction and would have no authorized artifact to work on"`.
An unused slot with a recorded reason is auditable; an unused slot with silence reads as an oversight.

## 10. Payload-class provider failure (422 `messages.<N>.tool.content.str`) — prevent, then resume small

Measured 2026-09-28: a long lane (~424 msgs, ~275k context tokens) was killed by
`HTTP 503: [..] [422]: {"error":{"param":"messages.421.tool.content.str", …}}` after 3 retries — the provider rejected
an oversized/ill-formed tool message, NOT the task; every GPU artifact of that round had already landed. The immediate
retry then died with `502 ERR_HTTP2_STREAM_ERROR` (≈19 min in), and a THIRD attempt with a deliberately short packet
(docs-only, ~10 tool calls) finished in 4 minutes with everything the round still owed.

- **Preventive, in EVERY packet for long lanes:** write files via short scripts and print ≤200-char confirmations;
  never `cat`/paste large blobs into tool output; keep each tool result small. Lanes that accumulate hundreds of
  messages are the ones that trip this class, so the rule matters most for finishing/report passes.
- **Reactive:** classify by the error `param` (payload) vs connect classes (502/503 timeout); wait the mandatory
  5 minutes; resume the SAME session with the smallest possible packet; re-check disk before assuming anything was
  lost — measure what landed, then ask only for the remainder.
- **User-facing:** when the user asks why it stopped, three lines — measured cause class · what already landed on
  disk with numbers · the relaunch being issued now — and issue that relaunch in the same turn, not next turn.
