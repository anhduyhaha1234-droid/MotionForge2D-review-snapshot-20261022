# Provider flap + payload discipline (long worker lanes)

Signatures observed from a local router in front of the upstream model during multi-hour lanes:

* `422 invalid_request_error: messages.<N>.tool.content.str` — a tool message's content was an
  unacceptable shape/size; fired late in a run (~420 msgs) carrying oversized tool payloads.
* `503 fetch connect timeout` — transient; a lane can die with a 124–125 B log and `exit 0`
  (misleading: exit code alone is not a verdict; read the log + disk).
* `502 ERR_HTTP2_STREAM_ERROR` / `NGHTTP2_ENHANCE_YOUR_CALM` — transient; can hit at the very LAST
  step after all real work (GPU outputs, gates) already completed.

## Packet rules that prevent the 422 class

1. "Write files via scripts; print ≤200-char confirmation lines; never cat/dump large files to the
   model." Put this in every long-lane packet — a run that dies at minute 19 of a report write has
   burned the whole budget.
2. Keep tool-call output small at the source: aggregate in scripts, print one summary line.

## Flap recovery (RULES-compliant)

1. Wait ≥5 minutes before retrying (transient connection class).
2. Resume the EXACT same session id, same model pin, same scope — never switch models to dodge
   quota; never mint a new owner for a recoverable session.
3. **Verify disk BEFORE assuming the work is lost.** In one incident the run completed every GPU
   run + assembly + gates and died only while writing the final report. The correct action is a
   short finishing packet (append docs, no GPU), not a re-run.
4. A killed/aborted launcher produces no receipt: classify it `KILLED_PRE_WRITE` (or similar) and
   retain any files it already wrote rather than deleting them.

## Turn-budget exhaustion — the other last-step failure (exit 0, no commit)

Signature (differs from every flap above): launcher receipt `exit 0`, NO HTTP error in the log,
tail reads `⚠ Iteration budget reached (160/160) — response may be incomplete`, and `git log`
still shows the transport/guard base — the task commit is MISSING. This is not loss: the largest
integration tasks (6+ write-set paths, multi-module services) can legitimately spend all 160
turns before the commit step (measured on the 28-task delivery wave's biggest integration task).

Recovery (proven end-to-end in 5m46s):
1. Measure disk FIRST: `git status --porcelain` (expect exactly the write-set `M`/`??` entries),
   file sizes, then run the task's own test file yourself with `-p no:cacheprovider`. Green test
   ⇒ the work is done; do not re-run anything expensive.
2. Resume the SAME session with a ≤40-tool-call FINISHING packet — exactly 4 steps: (a) re-run
   2 decisive test commands, (b) close missing evidence (REPORT / final_gate / commands appendix),
   (c) commit EXACTLY the measured paths (name them in the packet), (d) print the terminal line.
   Forbid GPU, scope expansion, and new artifacts.
3. Append an incident ledger row: symptom, disk state measured, finishing-packet name, session id.

Prevention: every large-task packet carries an explicit commit-ordering rule, not just a budget
number — "target ~80 tool calls; if you reach ~120 and are not done, COMMIT the allowlist +
write REPORT before ending". Without it, a run can end green-but-uncommitted.

## Cold vs warm cost accounting

Benchmark numbers are only comparable within the same regime:

* **COLD** (first run after the Comfy/served process starts): e.g. 596.95 s per output-second.
* **WARM** (subsequent runs on the same loaded process): e.g. 38.67 s per output-second.

An apparent 15× speedup between two runs was cold→warm, NOT the geometry/config change made in
between. Every cost claim must name the regime. For ETAs: use warm numbers for batch work and add
one cold run (~40 min in that case) per server start. Cache-off runs can be marginally faster and
pixel-identical — measure, don't assume the named "cache" node helps.

## User-facing behaviour during flaps (learned from "sao thế / làm nốt đi")

When a flap leaves a lane silent, the user sees a stalled job and asks why it isn't moving. Answer
must LEAD with (1) same-turn cause ("provider router flapped: 502 at the last step"), (2) what is
already safe on disk (e.g. all GPU outputs + assembly exist), and (3) the relaunch ALREADY
executed in that same turn. Never answer with only an apology or a plan — relaunch first, then
report. A flap reply containing no newly dispatched action reads as an excuse.
