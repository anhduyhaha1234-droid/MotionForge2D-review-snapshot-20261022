# Monitor succession + lane terminality (measured 2026-09-27/28, MotionForge delivery)

A bounded poller ("monitor") watches lane sessions and wakes the Manager on each tick. Two
failure modes showed up in a long delivery round; both are cheap to prevent.

## 1. A COMPLETED lane is not a stalling lane

Symptom: the monitor kept printing `STALL_AUDIT>8min` for a lane whose launcher had already
exited with `exit 0`. Cause: sessions resumed via
`hermes chat -q <packet> --resume <id>` keep `end_reason = null` in the state DB even after the
run finishes (the CLI does not close the row). So `end_reason` is NOT a terminality signal for
that launch shape.

Terminality check, in order (all read-only):
1. Launcher receipt JSON has `exit_code` + `utc_end` → the launch is over.
2. Enumerate processes matching the packet/log name: surviving matches that are only `bash.exe`
   wrappers (and your own probe shell) mean the agent process is gone → terminal.
3. Only after (1)+(2) treat silence as stall and audit process/GPU/logs.

Never let a finished lane stay in the monitor's lane map — it re-emits false stalls every tick
and pollutes the audit trail you later cite as evidence. When you publish such a flag, correct
it explicitly (lane X verified terminal at time T by launcher receipt + process enumeration).

## 2. Successor monitors: new file, new log, pruned lanes

Keep the monitor bounded (N ticks × cadence, e.g. 6 × 8 min) and replace it with a successor
whenever (a) it exhausts its ticks, (b) a lane's session id changes, or (c) a lane completes.

Rules that survived use:
- NEVER edit a monitor script that is currently running — write a successor file and launch it.
- Give the successor a NEW log name (`monitor_X.log` → `monitor_X_b.log` → `_c.log`); a reused
  name interleaves two writers into one log and destroys the timeline.
- Generate the successor in Python with explicit `.replace()` edits, then `ast.parse()` it
  before launching. A chained `sed -e ... -e ...` clone silently double-substituted (produced
  both the old and new lane entries) and would have polled the wrong ids; the syntax check is
  what catches this cheaply.
- Prune completed lanes from the successor's lane map; keep only live sessions.

## 3. Evidence-worthiness of monitor output

Monitor ticks are convenience telemetry, not proof. For any claim that later goes into a report
("lane alive", "lane stalled", "3 streams active"), re-derive it at write time from the two
authoritative sources: the read-only state DB (message/api counts per session id) and the
process table. Keep raw ticks in the log for the narrative, but never cite a tick as the
measurement.

## 4. Cross-ROUND succession — the stale STOP file kills the next round's monitor (measured 2026-10-12, R6)

Newer shape than §2: a long-lived heartbeat daemon appends a row every ~2 min and honors a
`HEARTBEAT_STOP` control file for graceful stop. Round R5 closed with the STOP file written.
Next round R6: the freshly launched heartbeat printed `heartbeat: STOP file present (...) -> exit`
on its FIRST iteration and died silently — the previous round's control file was still on disk,
so the new invocation had NO monitor until a human/turn noticed the last row was stale (it still
showed the PREVIOUS round's invocation).

Rules:
- Before starting the monitor for a new round, check for the STOP flag (and any round-scoped
  control files) from the prior round. If present, RENAME to a round-suffixed archive
  (`HEARTBEAT_STOP.<round>-closed`) — never delete; it is round evidence.
- Verify the FIRST fresh tick, not just process existence: it must bind to the NEW invocation
  (`open=true`, receipt=<this round>, lease children ALIVE). A tick whose read lands a fraction
  of a second BEFORE the new dispatch row is appended resolves the PREVIOUS invocation — a
  benign read race; confirm on the NEXT tick instead of "fixing" anything.
- Never cite `tail -1` of the tick log without checking its `at_utc` freshness — the prior
  round's last row lingers as the tail until the first fresh tick.

## See also (same delivery round, 2026-09-27/28)

- `references/provider-flap-and-payload-discipline.md` — router flap signatures
  (`422 messages.<N>.tool.content.str` / `503 fetch timeout` / `502 ERR_HTTP2_STREAM_ERROR`),
  ≤200-char tool confirmations in every long-lane packet, wait-5-min then resume the SAME
  session/model/scope, verify disk BEFORE re-running (a flap can hit at the last step after all
  real work is done), and cold-vs-warm cost accounting for benchmarks/ETAs.
- `references/cloned-graph-identity-and-segment-pinning.md` — one proven graph cloned for N units
  must swap per-unit fields: hash the prompt per unit (a carried-over BOOK prompt rendered the
  wrong scene while all technical gates stayed green); assemblies pin per-segment file+sha;
  budget one native-vision src-vs-gen check per delivered shot.
