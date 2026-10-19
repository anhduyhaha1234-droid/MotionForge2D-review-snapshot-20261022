# Demo visual verification + resume lineage (DV3-R2, 2026-09-08)

Session-specific lessons for PM-gated visual/contract lanes. Parent skill:
`pm-worker-orchestration` (manager dispatch / verify / gate).

## 1. `hermes --resume <terminal-session>` creates a NEW session

Observed 3x this lane (R1 `...0fbdeca` → R2 `...8421e0`, R2 `...a079b0` →
`...50eccf`, R3 `...50eccf` → `...d5d2f0`): the `--resume` target was
`agent_close`/`ended_at` set, and the runtime minted a fresh session ID with
the correction prompt as its first user message instead of continuing in place.

Manager rules derived:
- Never assume resume-in-place. After every resume dispatch, read
  `state.db` (`SELECT id,model,ended_at,end_reason,message_count`) + first
  user message of the newest session to prove where the prompt landed.
- Record lineage explicitly in REGISTRY.md
  (`R1 <id> terminal → R2 <id> live`), not a single "resumed" ID.
- Single-writer still holds because the old session is terminal
  (`ended_at` set, `agent_close`); verify that, don't claim a duplicate
  writer. Correction prompts must therefore be self-contained (full roots,
  env, file list) — the new session inherits nothing except the prompt text.
- `commands.jsonl` START rows must name the intended resume target AND the
  actual new owner once observed.

## 2. Vision prose hallucinates — gate on pixels + text enumeration, not adjectives

A `vision_analyze` pass described the sentence "Behind him standing: woman
..." as rendered in `book-insert-strip-513-524.png`. Follow-ups proved it
existed NOWHERE:
- `grep -rni "standing"` over T01 evidence + all 4 new repo files → zero
  hits (only the test that bans the word + REPORT's own withdrawal note).
- A second vision call asking to "Quote EVERY text string visible ... one by
  one" enumerated 12 frame labels + 12 watermarks and stated explicitly the
  word "standing" does not appear in the image.

Rule: a vision adjective ("standing", "open", "ghost") is a lead, never a
finding. To promote it to a finding require ALL of:
1. A text-enumeration vision prompt (list every string verbatim; ask for an
   explicit present/absent verdict on the disputed word).
2. `grep -rni` over the evidence dir AND the touched source files.
3. A pixel measurement (see §3) on manager-extracted frames.

The disputed R3 "fix" was correctly closed WITHOUT an edit on this basis;
the ledger records "standing only in prior vision prose, zero file hits".

## 3. Pixel-diff recipe that settled book@516 → @522 (ffmpeg + PIL/numpy)

```bash
SRC=".../source-0040-0110.mp4"; D="<run>/_manager/verify-t01"
for f in 513 514 515 516 517 518 519 520 521 522 523 524; do
  ffmpeg -y -v error -i "$SRC" -vf "select='eq(n\,$f)'" -vsync 0 \
    -frames:v 1 "$D/full-$f.png"
done
```

```python
from PIL import Image
import numpy as np
V = "<run>/_manager/verify-t01"
frames = {f: np.array(Image.open(f"{V}/full-{f}.png").convert("RGB")).astype(int)
          for f in [513,514,515,516,517,518,519,520,521,522,523,524]}
# true ROI from changed-pixel bbox: xs 227..326, ys 186..265
for name,(x0,y0,x1,y1) in {"trueROI":(235,210,295,285),
                           "oldbook":(60,140,200,300)}.items():
    base = frames[513][y0:y1,x0:x1]
    for f in sorted(frames):
        if f == 513: continue
        d = abs(frames[f][y0:y1,x0:x1]-base).sum(axis=2)
        print(name, f, round(float(d.mean()),3),
              round(float((d>30).mean()*100),3))
# white-share distinguishes yellow-spine edge (static 0.134%) from pages
sub = frames[522][140:300,60:200]
print(((sub[:,:,0]>225)&(sub[:,:,1]>225)&(sub[:,:,2]>225)).mean())
```

Decisive numbers this lane: 513→521 byte-identical (mean 0.0); 521→522
true-ROI mean 151.7, pct>30 ≈ 42%; old-book ROI flat (0.006). Always derive
the ROI from the changed-pixel bbox first — the manager's first guess
(x60-200/y140-300) covered curtain, not the book, and showed "no change"
for a real event.

## 4. Watchdog staleness guard

W3 fired on the R2 REPORT because its condition was
`REPORT.md newer than R2-prompt` — already processed. Pin each watchdog to
its own attempt (e.g. `REPORT mtime > R3-prompt` or a content-hash change),
and on a stale fire write an `END/STALE` row to `commands.jsonl` with the
reason instead of re-processing. Prior watchdogs (W1/W2) exited correctly
on marker; only the mtime-relative condition went stale.

## 5. Model-switch bookkeeping (user override, latest wins)

`ocgfree/muse-spark-1.3-contributor-free` → `cmc/meta/muse-spark-1.3-contributor`
(provider custom, max, fallback OFF) mid-lane: probe
`hermes -z "ping" -m <id> --yolo` → pong EXIT 0 BEFORE dispatch, log a
`DV3-R2-MODEL SWITCH` row in `commands.jsonl`, pin a header note in
REGISTRY.md, and correct prior "same model" claims via a dated errata file
(original text preserved). Never retro-apply the new route to S12/Lunar.
