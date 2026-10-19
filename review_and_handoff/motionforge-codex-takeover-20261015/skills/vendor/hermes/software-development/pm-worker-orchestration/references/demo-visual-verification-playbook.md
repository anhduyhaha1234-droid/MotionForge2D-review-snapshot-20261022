# Demo Visual-Verification Playbook (manager-side, from MF-DEMO-V3-R2)

When a worker submits visual claims (event frames, poses, masks), verify
INDEPENDENTLY — never trust the worker's screenshots or prose alone.

## 1. Self-extract source frames, pixel-diff claimed transitions

- Extract the exact claimed frames yourself with ffmpeg (`select='eq(n\,F)'`).
- Pixel-diff adjacent frames in the worker's TRUE ROI: byte-identical
  (mean 0.0) across a claimed transition = FALSE event. Real session case:
  worker claimed book closed→open at source 516; manager diff showed
  515vs516 mean 0.0 (identical), true step 0.405→0.528 at 521→522 in ROI
  x235-295/y210-285. Gate on your own numbers, then confirm with vision.
- White-pixel share inside the ROI is a cheap second signal (static
  0.134% at 515/516/522 = yellow spine edge, not pages).

## 2. Vision prose is not file truth

- A vision model describing YOUR probe image can write words ("standing")
  that exist NOWHERE in deliverables. Before opening a correction, grep
  the evidence tree + new files for the exact word. Zero hits outside the
  banning test = no defect, record it and move on (R3 proved this).
- Conversely, worker-generated strips CAN carry stale labels contradicting
  a fixed contract — vision-read every label string in review sheets.

## 3. Check overlay channel order before measuring tints

- If code does BGR→RGB (`[:, :, ::-1]`) BEFORE `mask_overlay(..., (255,0,0))`,
  the "red" tint lands in the BLUE channel. Measure dB, not dR, and confirm
  against the code first — a 0.01% redmask is a measurement bug, not a
  clean mask. Real numbers once corrected: removal bbox x221-328/y96-271,
  protected overlap 0.03%, outside-mean 5.3 vs inside 295.9.

## 4. Resume may fork — record lineage, don't hide it

- `hermes --resume <id>` can create a NEW session instead of continuing the
  owner (observed repeatedly). Detect via state.db (new id, prompt as first
  user msg, old session `agent_close`). Record R1→R2→… lineage in the
  registry; single-active-writer holds because predecessors are terminal.

## 5. Watchdog staleness

- Marker watchdogs (`grep STATUS REPORT.md`) fire on ALREADY-PROCESSED
  reports when the marker predates the prompt they compare against. Compare
  REPORT mtime vs correction-prompt mtime before acting; log STALE + clear
  instead of re-verifying.

## 6. Model-id exactness

- Pong on two similar strings (transposed tokens) does NOT establish alias
  equivalence. Record exact ids per session (state.db `model` column +
  launch string); latest user instruction wins for forward dispatches;
  correct via append-only errata, never by rewriting the registry.
