# Content binding: per-unit prompts, source cuts, cache determinism (2026-09-28, MotionForge delivery)

Datapoints behind the SKILL.md §3 paragraph "bind each graph's prompt to its own unit". Read this
AFTER the geometry fix in `template-reuse-geometry-and-cost.md` — geometry-correct is not
content-correct, and every technical gate can stay green on a content-wrong clip.

## 1. Prompt-sha carryover: three graphs, one prompt

Measured: the TURN and OCC graphs were rebuilt from the BOOK graph with only input/output deltas, and
the text-conditioning node kept the BOOK prompt — prompt sha `540d16b7…` identical in all three graphs,
while the per-unit prompts produced in an earlier round were `eca92d5e…` (TURN) / `b2a1e176…` (OCC).

Result: the TURN clip (a certificate/document shot) rendered a "person seated reading an open blue
book" scene — the BOOK content — while dims 640×368, 120 f, 30/1, 4.000000 s, pts monotonic and
"no watermark" were ALL green. A technical-only gate scores that clip as PASS.

Rules:
- Assert per-graph prompt identity: hash the CLIPTextEncode text of every built graph and compare it
  against that unit's own prompt from the unit manifest. A shared hash across graphs is a
  CONTENT-CARRYOVER defect, not a convenience.
- Bind the prompt like geometry: part of the unit manifest, diffed on every rebuild.
- Add a src-vs-gen visual row (first / mid / **last** frame) to every shot gate and review the pixels
  with real image input; metrics do not catch scene substitution.

## 2. Source windows can contain CUTS — split the unit at the cut

Measured: the OCC source window (120 f) opened on the certificate + pen hand and by frame 119 was a
different scene (person seated at a table with a book and a drink). The generated clip followed the
START anchor for the whole window, so the tail mismatched the source. The mismatch was first visible
on the LAST-frame src-vs-gen sheet — which is exactly why frame 0 alone is not a coverage check.

Rules:
- Cut-scan every source window BEFORE building units: consecutive-frame mean-abs-diff with a declared
  threshold; record frame + score + threshold in evidence. Do not guess a cut.
- Split the unit at the source's own cut (the cut is the source's cut). Each segment gets its own
  anchor taken from its own first frame (same anchor recipe), its own prompt, its own receipt, and its
  own span (no missing/overlapping frames).
- Assembly pins per segment: unit id, file, sha256, frame count, source-audio file + sha. Verify the
  boundary frames between adjacent segments and keep the boundary strip as evidence.
- Keep superseded assemblies on disk with an explicit supersede note (v1 → v1.1 → v1.2); never
  overwrite the earlier one. Mark the newest one in its own receipt with an explicit role token
  (e.g. `assembly_v13 … role=FINAL_FOR_VERIFY`) so verification lanes know WHICH file to audit —
  and point the read-only verifiers (bench/numeric + demo/vision) at that final artifact only;
  verifying a superseded assembly wastes a whole review round.

## 2b. Repair rounds: one declared variable per round, and the split creates new variables

Content repair here took a bounded chain, each round changing exactly one thing:

1. per-unit prompt (TURN/OCC were carrying the BOOK prompt) → TURN fixed;
2. split the unit at the source cut (OCC cut @102) → segments correct in span, but the NEW
   segment inherited its parent's prompt and still rendered the wrong scene;
3. prompt for the **segment** (SEG2 = person-at-table scene) → content correct.

Rules that follow:
- A split creates a new unit: it needs its **own** anchor (from its own first frame) AND its own
  prompt. Reusing the parent unit's text conditioning is the same carryover defect as §1, one level
  down.
- Declare the single changed variable per round in the receipt; stop the loop when the declared
  gate passes or after the capped number of rounds (3 here), then hand the standing defects to the
  reviewer as explicit rows instead of looping — the last round's standing notes (transient doubled
  text at one frame, book-state vs source event, watermark on the challenger branch, placeholder
  artwork) were shipped as review rows, not silently retried.

## 3. Cache ON/OFF and overlap are isolation controls, not defaults

Same seed, same 4 s window, warm server, Wan Animate 2 INT8 + LightX2V rank64:

| variant | wall for 4 s | s/output-s | VRAM peak | decoded-frame diff vs reference |
|---|---|---|---|---|
| cache ON (`WanAnimate2Cache` int8 gpu) | 154.67 s | 38.67 | 10,973 MiB | reference |
| cache OFF | 135.21 s | 33.80 | 10,763 MiB | max_abs 0, 0 frames differ |
| chunk overlap 8 → 16 | — | — | — | max_abs 0, 0 frames differ |

- Both variants were **pixel-identical** to the reference (different container bytes/sha, identical
  decoded frames) — an independent verifier re-derived the diff with its own script
  (ffmpeg rawvideo → numpy) and got max_abs = 0. Always report determinism as "decoded frames
  identical; container bytes differ" so the sha mismatch is not read as a defect.
- Cache OFF was ~12 % faster at lower VRAM in this measurement ⇒ treat "cache ON" as a hypothesis to
  measure, not a default; the overlap change was inert and reverted to 8.
- Because output is seed-deterministic here, a single-variable re-run with the SAME seed is a valid
  isolation test for geometry / prompt / cache / overlap changes.

## 4. Source EVENTS are their own gate row (not covered by coverage/relations)

Measured on the BOOK shot: the source window contains a state change — the held book opens
(`open_two_pages` at frame ~72) — and the two profiles disagreed on it:

| profile | book state at frame 119 | coverage row | relations row | event row |
|---|---|---|---|---|
| Wan Animate 2 INT8 (baseline) | still CLOSED | PASS | PASS | **FAIL** |
| VACE 14B (challenger) | OPEN (matches source) | PASS | PASS | PASS (but watermark copied) |

So a clip can pass every coverage/relations row while failing the one semantic event the shot
exists to carry. Rules:
- Extract the unit manifest's events (state changes with their first frame) into an explicit gate
  row per shot, checked at the event frame ± a few frames, from real frames — never inferred from
  the first/last coverage frames alone.
- If the primary profile cannot reproduce an event, the options are: split the shot at the event
  frame (two segments, two anchors, like a cut) or route that shot to the challenger profile — and
  record WHICH was chosen and why. Do not silently ship a clip with a failed event row.
- Event fidelity and overlay fidelity can point at different profiles: the challenger that
  reproduces the event may also copy a source overlay (watermark). Score each profile per gate row
  and keep the profile choice conditional instead of "best model".
