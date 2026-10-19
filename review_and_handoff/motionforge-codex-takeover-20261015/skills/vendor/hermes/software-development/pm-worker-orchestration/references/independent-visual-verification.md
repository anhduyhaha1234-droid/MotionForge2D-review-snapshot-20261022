# Independent visual verification — pixel math first, vision second, contract third

Manager-side discipline for lanes where a worker reports visual findings
(frame events, poses, masks). Used on MF-DEMO-V3-R2 (source window 450..569);
the pattern is window-agnostic.

## Rule 1: never gate on a single vision read of a crop

Vision models confidently misread small crops and strips, in BOTH directions:
- A 5.3 KB transition strip was read as "no book at all" (brown curtain +
  cyan wall) — the strip was indeed built from the wrong ROI, but the read
  gave no usable localization signal, only a blanket negative.
- Full-frame reads contradicted each other across turns on whether a woman
  was standing or seated; crops of the same woman flipped the verdict again.
- One strip read even hallucinated scene-description text ("standing")
  that grep proved existed in ZERO files — it came from an earlier
  vision-prose summary, not from any artifact.

Durable rule: a vision claim that contradicts pixel math LOSES. Corroborate
every visual finding three ways before it enters a contract or a gate.

## Rule 2: pixel-diff protocol (cheap, decisive)

1. Extract the exact frames yourself with ffmpeg (`select='eq(n\,F)'`),
   never reuse the worker's derivatives as ground truth.
2. Full-frame identity check first: `515vs516 mean abs diff 0.0, pct>30 0.0`
   proves byte-identical frames — no event can exist between them.
3. ROI step measurement: pick the worker-claimed ROI, diff frame-by-frame
   against a base. A real event looks like `513..521 all 0.0` then
   `521vs522 mean 151.7, pct>30 42.2` — flatline then step. A claimed event
   with `0.006` mean and identical white-pixel share (0.134% at 515/516/522)
   is static texture, not a transition.
4. Localize the change bbox (`np.nonzero(d>30)` → x221-328/y96-271) and
   re-crop exactly there; eyeball/vision only the re-crop.

## Rule 3: the BGR-channel trap (OpenCV pipelines)

When the producer draws overlays in BGR (OpenCV) but the review sheet is
saved/compared as RGB, a RED tint reads as BLUE gain. Measuring the wrong
channel yields `redmask pct 0.01` on a mask that actually covers 2.39%.
Fix: check per-channel deltas first (`dB max 110` vs `dR max 11` tells you
which channel carries the tint), then threshold that channel. State the
colorspace conversion explicitly in the verification note.

## Rule 4: triangulation checklist for a visual gate

- Pixel: flatline-then-step numbers with exact bbox (Rule 2).
- Vision: full frames at base/event/end + tight re-crop of the bbox —
  never a crop alone, never a strip alone.
- Contract: event/pose/z-order entries + fail-closed negatives + a test
  that bans the withdrawn claim (e.g. `assert "standing" not in
  json.dumps(contract)`), all green on a fresh manager re-run.
- Guards: ruff F clean, frozen write-set VERIFIED, protected-DB hash
  unchanged, sibling lane untouched.

## Rule 5: correction routing for false visual claims

Route each finding to the exact owner with the decisive numbers inline
(zero-diff pairs, ROI means, bbox), not "look again". Require the worker
to regenerate the derivative (true-ROI strip with per-frame labels),
recompute the contract hash, and correct the REPORT — then re-run Rule 4
yourself. A stale-hash REPORT line (`32bb2ed4…` vs actual `748c02c6…`)
is itself a finding.
