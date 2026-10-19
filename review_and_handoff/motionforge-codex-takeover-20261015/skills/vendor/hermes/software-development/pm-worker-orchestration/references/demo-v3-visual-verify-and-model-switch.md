# Demo-V3 visual verify + model switch — manager field notes

Applies to any PM-gated lane where a worker reports visual findings (pose, events,
artifacts) plus evidence files. Lessons from MF-DEMO-V3-R2 T00→T03.

## 1. Vision prose is a hypothesis, files are evidence
- A `vision_analyze` description (e.g. "woman standing") must NEVER enter the gate
  verdict on its own. One R3 round proved the word existed only in prior vision
  prose while `grep -rni standing` over contract/JSON/doc/brief/evidence returned
  zero hits (outside the test that bans it). Gate rule: quote file bytes first,
  vision second. When they conflict, pixels + `grep` win.
- Same for strips/contact sheets: a 5.3 KB strip that vision says shows "curtain +
  wall, no book" fails the event claim even if REPORT text says otherwise.

## 2. Pixel-diff event verification (book closed→open pattern)
- Extract the exact source window frames with ffmpeg (`select='eq(n,<frame>)'`).
- Compare consecutive candidates full-frame AND in the worker-claimed ROI:
  `mean abs diff`, `pct>30`, white-pixel share. Real event in this lane:
  513→521 byte-identical (mean 0.0), 521→522 ROI step 0.4→0.5 / mean ~151,
  white share identical before (static spine edge, not pages).
- Record changed bbox (`x221-328 y96-271` here) and re-crop tightly around it for
  vision; a loose crop lands on another person and misleads the model.

## 3. BGR→RGB overlay trap when measuring masks
- `render_decomposition_sheet` built overlays in BGR then saved `[:, :, ::-1]`
  (RGB). A `(255,0,0)` "red" overlay therefore measures in the BLUE channel.
  First measurement (red channel) read 0.01% and looked like "no mask"; correct
  channel read 2.39% tightly on the reader. Always read the overlay code before
  choosing the channel, and report bbox + overlap (here protected overlap 0.03%,
  outside-removal mean 5.3 = preserved, inside 295.9 = truly removed).

## 4. Model-id transposition is not an alias
- `ocgfree/muse-spark-1.3-contributor-free` vs
  `ocgfree/muse-spark-contributor-1.3-free` (transposed tokens): ping succeeding
  on both does NOT prove equivalence. Record the exact `state.db` model per
  session, keep the original registry text, append a `MODEL_ERRATA.md`, and
  forward-pin the correct id for new workers (PM-decision pattern). Never
  retrospectively claim "same model".
- User model switch mid-lane (`-m cmc/meta/muse-spark-1.3-contributor`): probe
  pong first, log a MODEL SWITCH ledger row, retire the old route for the lane
  only — no S12/Lunar/global change.

## 5. Resume may fork a new session — record lineage, keep one writer
- `hermes --resume <owner>` twice created a NEW session instead of continuing
  the owner (R1→R2, R2→R3). The old session was terminal (`agent_close`), so no
  concurrent writer existed, but the registry must show the full lineage
  (`...fbdeca → ...8421e0 → ...830740`) with model + live proof, not a silent
  "resumed owner" claim. Corrections still route to the live head; single active
  writer invariant holds because predecessors are terminal.

## 6. Correction shape: substance gate + micro fix
- R2 fixed real substance (event 516→522, seated woman, PACK/F05 actually read,
  contract re-hash `fd8884552a4b96ef`); R3 was a one-image-label micro fix.
  Verify substance independently (re-run tests, recompute hashes, re-measure
  pixels) and dispatch the micro fix separately instead of holding the whole
  gate for one label.
- Never claim required reading is "absent on disk": `ls` all five PACK/F05 files
  with byte counts first (25573/11860/2028 + 8664/5887 here); the worker's
  "absent" claim was false and cost a correction round.

## 7. Watchdog stale-fire clearing
- A bounded watcher (poll `REPORT.md` STATUS marker) can fire on an already
  processed report (W3 fired on the R2 REPORT). Check mtime vs prompt mtime and
  prior GATE ledger rows before acting; log `END/STALE` with the reason instead
  of re-dispatching work.
