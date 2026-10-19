# Independent visual-claim verification (demo lanes — DV3-R2-T01, 2026-09-08)

When a worker REPORT makes pixel-level claims (event at frame N, pose,
open/closed, standing/seated), do NOT gate on re-reading the report or on a
single vision confirmation. Verify with pixel math + dual vision passes.

## 1. Pixel-diff event localization (the arbiter)

- Extract the exact source frames yourself — never trust worker-supplied
  crops for the verdict:
  `ffmpeg -y -v error -i <src> -vf "select='eq(n\,<f>)'" -vsync 0
  -frames:v 1 <owned-verify-dir>/full-<f>.png`
  (derivatives ONLY under an owned verify dir, never MAIN/repo).
- numpy ROI abs-diff: `d = abs(A-B).sum(axis=2)`; report mean + pct>30.
- Byte-identical neighbors (mean 0.0, pct 0.0) DISPROVE a claimed
  transition. Observed: claimed book-open @516 → 515vs516 diff 0.0 (false);
  513→521 all identical + step 151.7 at 521→522 → true event @522.
- Derive the TRUE ROI from the changed-pixel bbox
  (`(d>30).nonzero()` → xmin/xmax/ymin/ymax), not from the worker's stated
  ROI — the manager's first ROI covered curtain, not book.
- Page/white claims: count white pixels in the ROI across the boundary
  (identical 0.134% = static spine edge, not pages).

## 2. Vision text-in-image needs TWO passes

- A vision model quoted "Behind him standing: woman ..." as image text;
  worker grep + a second vision pass ("quote EVERY text string, list one by
  one") proved the word appears NOWHERE in image or files.
- Rule: never dispatch correction work on a single vision text reading.
  Require (a) second vision pass enumerating ALL text, (b) grep over
  evidence + repo files. If the worker proves zero hits, accept + close
  with a ledger note (R3 pattern) — the error was in prior vision prose,
  not in any file.
- Vision remains useful for pose/state description (open-book shape
  language, seated cues: seat band under hem + chair legs + zero bare
  legs), but pixel diff arbitrates frame indices.

## 3. Resume-lineage check (observed 2x in one lane)

- `hermes --resume <sid>` can spawn a NEW session instead of continuing
  the owner. After every resume dispatch: query state.db newest session +
  first-user-message match, record ACTUAL lineage in the registry
  (R1 sid → correction sid → micro sid). Single-writer holds iff the prior
  session is terminal (`agent_close`) — never assume resume worked.

## 4. Stale watchdog clearing

- A watchdog firing on a REPORT mtime newer than the correction prompt may
  be STALE (that REPORT was already processed in a prior turn). Before
  acting: compare marker content against what was already verified; if
  processed, log `END/STALE` with reason and clear — do not re-verify.

## 5. Model-ID exactness + window discipline

- Transposed-token IDs (`...muse-spark-1.3...` vs
  `...muse-spark-contributor-1.3...`) BOTH pong — ping ≠ alias equivalence.
  Pin exact IDs from state.db/launch strings; keep a MODEL_ERRATA note,
  never rewrite history.
- Source-window vs clip-index: window 450..569 ≠ clip 0/60/119. Record the
  local↔source mapping explicitly; delete wrong-window artifacts + note it.
