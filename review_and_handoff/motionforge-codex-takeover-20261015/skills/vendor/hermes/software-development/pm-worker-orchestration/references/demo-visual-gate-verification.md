# Demo visual-gate verification — window mapping, model-alias errata, disk-truth liveness

Use when managing any source-locked video/demo lane with a fixed source window, or any worker REPORT that claims a visual event (pose, prop state, transition frame).

## 1. Source-window vs clip-index mapping (blocking-class mistake)

- When acceptance covers a slice of a longer clip (e.g. source 450..569 of a 900-frame clip), never name diagnostics `0/60/119` bare. Always record the mapping in one line: `local 0/60/119 = source 450/510/569`.
- Manager pre-stage that extracts clip frames 0/60/119 produces plausible but WRONG fixtures. On discovery: delete the wrong files immediately and record the deletion in the decision-ack file — never leave them for a worker to inherit.
- Worker prompt must state the mapping and require `window: {first_source, frames, last_source}` in the contract JSON.
- Transition strips must log crop rect + source frame per cell. A tiny strip (e.g. ~5 KB) showing only background crop with no subject is a crop-geometry bug, not "no transition" evidence.

## 2. Model-alias transposition: pong ≠ equivalence

- Transposed-token model ids (e.g. `...muse-spark-1.3-contributor-free` vs `...muse-spark-contributor-1.3-free`) can BOTH pong on ping. That proves nothing about alias equivalence.
- Ground truth is `state.db sessions.model` for the owner session plus the exact dispatch launch string. On mismatch: append `MODEL_ERRATA.md` preserving the original registry text (never rewrite history) and pin the forward route explicitly in the next prompt.
- Independently verified DB/visual forensics do NOT need rework for a label error — record that so no one reruns a full gate over a string mismatch.

## 3. Vision cross-check before visual-gate approval

- A worker claim about an event frame (e.g. "book opens at 516, first white sliver") must be checked against INDEPENDENTLY extracted full frames (`ffmpeg select=eq(n,N)`) before the manager gate — never just the worker's own zooms/strips.
- Gate shape: full-frame vision + zoom vision + (where cheap) second crop, quoting exact visible evidence per file. One vision read of a worker derivative is navigation, not verdict.
- Conflicting reads (worker zoom says OPEN, independent full frame says CLOSED; worker says STANDING, independent crops say SEATED with chair seat under hem and zero bare legs) keep the item OPEN until re-extracted at full resolution and re-read. Record the conflict verbatim in the gate note; do not average the reads.

## 4. Dispatch liveness when the log stays 0 bytes

- Background `hermes -z "$(cat prompt)" ... >> dispatch.log` buffers: the log can sit at 0 bytes for minutes while the worker already writes evidence to disk.
- Verify via three independent signals, not the log: (a) `state.db` new session row within ~seconds of dispatch (model = exact id, user msg = prompt head, `message_count` growing, `RULES_LOADED` line present); (b) evidence-dir mtimes growing; (c) wrapper process alive. A missing `Resumed session` line on a NEW session is expected, not failure.
- Arm a BOUNDED watchdog (poll `REPORT.md` for `STATUS:` every 60 s, hard timeout 90–180 min, notify on complete) and stop hand-polling so the worker keeps the in-flight budget. Log START/END rows in `commands.jsonl` for lane and watchdog alike.
