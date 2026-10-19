# Manager-Side Pixel Verification for 2D Animation Lanes

Session-tested techniques (MotionForge2D demo V3, 2026-09-08) for independently
verifying worker visual claims without trusting reports. All commands run from
a manager shell with PIL + numpy; derivatives go to manager-owned evidence dirs,
never the worker's tree.

## 1. Event-frame detection by ROI step measurement

To pin a state change (e.g. book closed→open) to an exact source frame:

```python
from PIL import Image
import numpy as np
frames = {f: np.array(Image.open(f'full-{f}.png').convert('RGB')).astype(int)
          for f in [513,514,515,516,517,518,519,520,521,522,523,524]}
for name,(x0,y0,x1,y1) in {'trueROI':(235,210,295,285)}.items():
    base = frames[513][y0:y1,x0:x1]
    for f in sorted(frames):
        if f == 513: continue
        d = np.abs(frames[f][y0:y1,x0:x1]-base).sum(axis=2)
        print(f'513vs{f}', round(float(d.mean()),3),
              round(float((d>30).mean()*100),3))
```

Read it as: a run of `0.0` = byte-identical hold; a jump (here 0.0 → 151.7
at 521→522, 42% pixels changed) = the true transition. A worker-claimed event
with `mean 0.0` across it (here claimed @516) is a FALSE event — send it back
with the numbers. Always extract the check frames yourself with ffmpeg
`select='eq(n\,N)'` rather than trusting worker-supplied strips: one 5.3 KB
worker strip in this session showed curtain+wall, not the book at all.

Changed-pixel bbox localizes the ROI for vision follow-up:

```python
d = np.abs(A-B).sum(axis=2)
ys, xs = (d>30).nonzero()
print('bbox x:', xs.min(), xs.max(), 'y:', ys.min(), ys.max())
```

Crop that bbox (with margin) to ~150 px and hand it to vision — small,
on-target crops get accurate answers; full frames get prose drift.

## 2. Overlay-mask measurement MUST respect channel order

Review sheets often tint masks with an OpenCV-style BGR tuple, e.g.
`mask_overlay(src, mask, (255,0,0))` intending red, then the sheet code flips
`[:, :, ::-1]` for PIL saving. The tint then lands in the BLUE channel, not
red. Measuring only the red channel yields ~0.01% ("no mask") while the real
mask is 2.39% in blue — a false negative that can wrongly fail a good worker.

Procedure: read the overlay function first, note every `[:,:,::-1]`, then
measure per-channel deltas for both hypotheses:

```python
dR = targ[:,:,0]-orig[:,:,0]; dG = targ[:,:,1]-orig[:,:,1]; dB = targ[:,:,2]-orig[:,:,2]
bm = (dB>15)&(dR<-5)&(dG<-5)   # red-in-BGR hypothesis
gm = (gG>15)&(gR<-5)&(gB<-5)   # green overlay hypothesis
print('mask pct', round(float(bm.mean()*100),2))
print('protected overlap pct', round(float((bm&gm).mean()*100),3))
```

Gate numbers from this session (640x360): removal bbox x221–328/y96–271
(reader chest only), protected overlap 0.03%, outside-mask mean diff 5.3
(preserved) vs inside-mask 295.9 (really removed). Record all four.

## 3. Vision prose is not file truth — grep before correcting

A prior vision description contained the sentence "Behind him standing:
woman ...". A worker was nearly ordered to re-render a 146 KB strip over it.
Grep proved the word "standing" existed in ZERO files (only inside the test
that bans it). Rule: before issuing any correction derived from vision prose,
`grep -rni` the exact wording across worker files + evidence. Correct files,
not prose. The worker's rebuttal with a grep transcript was accepted and the
gate passed.

## 4. RULES_LOADED path must resolve to the canonical file

One worker's REPORT cited `RULES_LOADED .../repo/docs/pm/HERMES_AUTOPILOT_RULES.md`
(1873 B, 37 lines) — a nested stub — instead of the canonical
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
(24345 B, 277 lines). Treat a wrong-path RULES_LOADED as an evidence-doc
defect: check `ls -l` + `wc -l -c` on the cited path during the manager gate.
In this session it did not block substance approval (code/tests verified
independently), but it was recorded in the gate note.
