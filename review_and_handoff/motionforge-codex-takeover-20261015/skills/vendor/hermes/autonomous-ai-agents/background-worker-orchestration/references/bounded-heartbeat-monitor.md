# Bounded heartbeat monitor — progress + stall audit for long worker lanes, no cron, no watcher

**Problem it solves.** Orchestration rules demand a heartbeat every ≤20 min and a stall audit after ~8 min of
no progress while long CLI worker lanes run — but cron delivery does not reach a desktop chat, and an
unbounded watcher/dispatcher is explicitly forbidden. Working pattern, proven 2026-09-27 (4 lanes, ~2.5 h
wall, 3 lane restarts):

## The pattern

1. Launch a **bounded, read-only poller** as a tracked background process:
   ```
   terminal(background=True,
            command='python -B <tools>/bounded_monitor.py --db <state.db> --run-root <run> \
                     --lanes "COMFY=20260927_130100_1dc76b,VIDEO=20260927_122444_50c9d6" \
                     --iterations 6 --sleep 480 --tag r27c',
            watch_patterns=["iter "])
   ```
2. The poller prints **exactly one line per tick** (`[HH:MM:SSZ] iter i/N | LANE: ...`) — the watch pattern
   therefore wakes the agent once per tick (~8 min). That single mechanism fuses the heartbeat cadence and
   the 8-minute stall audit.
3. Use `watch_patterns`, **not** `notify_on_complete` (they are mutually exclusive, and
   `notify_on_complete` only fires at exit — useless for mid-run heartbeats). Keep the marker token unique
   to the tick line (`"iter "`); `DONE`/`ERROR`-style patterns get rate-limited out after 3 windows.
4. The poller **exits on its own after N ticks** (6 × 8 min ≈ 48 min) — bounded, so it is not an
   unsupervised watcher. **Kill it once every lane is terminal**; otherwise its remaining ticks keep waking
   the agent for nothing.
5. Each tick line carries, per lane: message count **+ delta**, `api_call_count`, `end_reason`,
   evidence-file count, and the age (s) of the last message — plus a `STALL_AUDIT>8min` flag when
   `age > 480 and end_reason is None`. Add slot/stream usage (e.g. `3/3`) so the heartbeat can state
   used/free slots, and add a `lý do mọi slot chưa dùng` note when a slot is deliberately idle.

## Rules that keep it compliant

- Read-only: `sqlite3.connect(f"file:{db}?mode=ro", uri=True)`. Materialize rows (`list(cur.execute(...))`)
  before any inner query — reusing one cursor inside its own iteration silently truncates the loop.
- Writes allowed ONLY inside the run's `manager/` dir (its own `<tag>` log + `monitor_last.json`).
  It never dispatches, never kills, never touches lane trees.
- One log file per monitor **generation**; never run two monitors writing the same log.

## Traps (all measured 2026-09-27)

- **The session map goes stale on every resume.** `--resume` mints a new id AND stamps the parent row
  `end_reason=agent_close` immediately, so a monitor keyed on the parent prints the dead row (with a growing
  `age=`) as if the lane had exited, while the real writer is alive. Relaunch the monitor with the new ids
  after each resume; treat tick lines for an already-resumed session id as STALE.
- **`sessions.message_count` is a stale snapshot** (measured 603 vs 1,223 real `messages` rows). Count
  `messages` rows for progress, and read `api_call_count` from `sessions` for budget burn (a manager at
  ~451 calls is at the turn-budget ceiling — record it as evidence-only, do not resume it to operate).
- **A monitor tick is not evidence.** For the final report, re-derive every number with a fresh probe right
  before writing it.
- The monitor proves liveness/progress only; the lane's own launcher process must still be polled
  (`process(action='poll')`) to get the real `exit=0` + duration + log path for the receipt.

## Reusable script

`scripts/bounded_monitor.py` — argparse version: `--db --run-root --lanes NAME=id,... --iterations --sleep
--tag`. Prints one `iter ` line per tick and appends to `<run-root>/manager/monitor_<tag>.log`.
