# A negative/near-zero comparison score is a bug signal — scan the offset first

Measured 2026-09-29 (MF2D export `av_policy` gate). A product validator rejected a
correct artifact, and the fastest path to the truth was a **lag scan**, not a re-run.

## The shape of the signal

A content comparator (waveform correlation, frame PSNR, perceptual similarity) that
compares two decoded streams **chunk-by-chunk at ZERO lag, with no alignment step**,
collapses to a *negative or near-zero* value when the two sides are offset by even a
millisecond. The companion metrics betray it:

| Metric | Measured | Threshold | Reading |
|---|---|---|---|
| `min_correlation` | **−0.6003** (product) / **−0.3823** (independent, lag 0) | ≥ 0.80 | FAIL — looks like wrong content |
| `min_spectral_cosine` | 0.8088 | ≥ 0.85 | close but *just* under |
| `max_relative_rms_error` | 0.2007 | ≤ 0.40 | **PASS** — level is right |
| `sample_delta` | 48 samples | ≤ 1600 | **PASS** — length is right |

**Passing level + passing length + near-threshold spectrum + negative correlation ⇒
offset/phase misalignment, not a content mismatch.** Wrong content drags the level and
spectrum down too; a pure time shift does not.

## The probe (run this before believing the comparator)

```
lag  0 ms -> corr = -0.3823     <- the comparator's own comparison point
lag  1 ms -> corr = +0.9972     <- the true alignment
lag  2 ms -> corr = -0.3830
lag  5 ms -> corr = -0.0256
lag 10 ms -> corr = -0.0972
self-control (reference vs itself, lag 0) = +1.0000
```

Run `scripts/content_compare_lag_scan.py <candidate> <reference>` — it prints the lag
sweep plus a self-control, so the number is auditable rather than asserted. **The
self-control is mandatory**: if `ref vs itself` does not reach ~1.0, the measurement
itself is broken and no verdict from it is valid (same family as the blanket
100%-failure bug signal).

Cross-checks that confirmed the offset independently:
- `ffprobe` audio `start_time`: reference `0.001000` vs candidate `0.000000` → 1 ms.
- 48 samples @ 48 kHz = exactly 1 ms — the worker's own `sample_delta` was describing
  the same defect.

## Locate the mechanism in code before routing the finding

`app/services/s12_export/validation.py:733` → `probe_audio_content()` decodes both
sides with ffmpeg and compares per 8192-sample chunk **at zero lag** (no alignment
step anywhere in the function). That is what turns a 48-sample shift into a FAIL.
Read the comparator's own comparison loop before declaring which side is wrong —
the defect can be in the *mux* (offset introduced) or in the *comparator* (no
alignment), and both are legitimate, routable findings.

## Rules

1. **Never conclude "wrong content" from one negative score.** Sweep lag and run a
   self-control first.
2. **Do not widen the threshold to make it pass.** Bounded-lag alignment is a real
   fix; lowering `min_correlation` >= 0.80 to admit a shifted waveform is not.
3. **Report both numbers when they disagree, and do not edit either to make them
   match.** Product recorded −0.6003, the independent probe measured −0.3823 at lag 0
   (different windowing): same sign, same conclusion, different value. Keep both and
   disclose which is which — a reviewer needs to know which measurement was
   double-checked.
4. **A micro repro like this one retires the re-run.** With the candidate and the
   report in hand, the owner can fix and re-prove against the *same* artifact
   (`probe_audio_content` re-run), so no GPU render is needed. Capture it before
   authorising any regeneration.
