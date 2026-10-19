# Measurement attribution discipline (cold vs warm, changed-state enumeration)

Field cases from a GPU render-proof lane (2026-09-28) where the first read of a benchmark was
wrong, and the fix was method — not a re-run.

## Case 1 — a "15× speedup" that was actually cold → warm

Two baseline runs of the same graph were compared:

| run | change | measured | first interpretation |
|---|---|---|---|
| P3  | template geometry (portrait 480×848) | **596.95 s** per output-second | baseline |
| P3b | geometry fix (640×368) + rerun | **38.67 s** per output-second | "geometry fix made it 15× faster" |

Reality: **P3 was COLD** (first run after server start; includes model load / kernel compile —
296.83 s/it cold, init ≈907 s) and **P3b was WARM** (≈8.7 s/it). A later warm run with the cache
node disabled measured **33.80 s** — i.e. all three warm numbers cluster, and the geometry change
contributed nothing to speed; its purpose was correctness (aspect + coverage). The lane's own
receipt had the evidence (`cold` vs `warm` labels); the Manager's first summary did not carry it.

Rules that follow:

1. **Label every benchmark cold or warm** (and cache on/off, server lifetime, context/batch
   settings) in the row itself. A number without its thermal/cache state is not comparable.
2. When a run differs from the last, **enumerate ALL changed state before attributing**:
   resolution/canvas, cache flags, server restarts, provider flaps, model reload, seed. Two
   changed variables ⇒ zero attribution.
3. Prefer **within-state A/B**: hold the server warm and change exactly one variable (the
   observed lane did this later — cache on/off and overlap 8↔16 both returned `max_abs = 0`
   pixel-identical, which is a *determinism* claim you can only make under warm A/B).

## Case 2 — keep UNDEFINED metrics undefined

`accepted_seconds = 0` (no output quality-accepted yet) ⇒ **cost per accepted second is
UNDEFINED**. Do not compute a denominator from unaccepted output, do not substitute "seconds of
video produced", and do not let downstream tables quietly divide by output-seconds. The
verifier's job is to keep the undefined metric spelled `UNDEFINED` until a quality owner accepts.

## Case 3 — keep NOT MEASURED metrics unmeasured

A RAM-peak sampler returned ~5 MiB on three attempts (non-credible). The correct result is
**`RAM peak: NOT MEASURED`**, carried into the final report as a named failure — not `0`, not a
best-guess, and not silently omitted. An independent verifier should treat a plausible-looking
value with no credible instrument as a finding, and the writer should be *praised* for the
disclosure, not pressured to fill the cell.

## Case 4 — verify the fix, not just the number

The geometry defect was real (a template node hard-coded `482×854, crop=center`, producing a
portrait latent from a landscape source, cropping away a required partial figure). It was found
by an independent verifier looking at SHAPES and coverage, not by any timing number. Keep the two
axes separate: **correctness findings come from pixel/structural checks; performance findings
come from labeled A/B under identical state.** A timing anomaly is a hypothesis, not a finding,
until the state is enumerated.
