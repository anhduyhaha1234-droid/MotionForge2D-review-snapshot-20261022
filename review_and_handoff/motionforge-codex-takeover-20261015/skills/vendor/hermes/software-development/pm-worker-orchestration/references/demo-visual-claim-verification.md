# Verifying worker visual claims — pixel diff + vision protocol

When a worker REPORT makes visual claims a manager gate depends on
(frame-event timing, pose/placement, before-vs-after sheets), do NOT trust
the report. Re-derive from source bytes in the manager turn.

## 1. Pixel-diff first (ground truth for "did anything change")

- Extract the exact source frames yourself with ffmpeg
  (`select='eq(n\,<frame>)'`) into manager-owned evidence. Never reuse the
  worker's crops blind.
- Compute mean-abs-diff + pct-changed on the full frame AND on the claimed ROI:
  `515vs516 full mean 0.0, pct>30 0.0` = byte-identical, so a claimed event
  at 516 is FALSE. True event found by scan: `513→521 all 0.0`, jump to
  `mean 151.7, 42%` at 521→522, so the event is @522.
- White-pixel share inside the ROI across frames distinguishes real page
  content from static edges (0.134% identical at 515/516/522 = static
  spine edge, not pages).
- Changed-pixel bbox (`(d>30).nonzero()` → x227–326, y186–265) locates the
  TRUE ROI when the worker's stated ROI is wrong — re-crop from the
  measured bbox, not from the claimed one.

## 2. Vision second (semantics pixel math cannot give)

- Full frames first, then crops. Tight crops mislead: a 120px crop of the
  reader was misidentified by vision as a different person (long blue hair,
  student). Always anchor every crop to a full frame viewed in the same turn.
- Ask for quoted exact evidence ("gray seat band directly under hem + brown
  chair legs to floor, zero bare legs" vs "standing"). When two vision
  answers conflict, pixel-diff + full-frame re-view decides — e.g. woman
  SEATED at 450/510/522/569 despite one crop reading "standing".
- Vision-check worker derivative artifacts too, not just source: a worker
  strip rendered the scene text "standing" while its own contract said
  seated — one stale image label held the gate until re-rendered.

## 3. Window-index discipline

- Probes named 0/60/119 are LOCAL indices into the occurrence window
  (source 450/510/569 for window 450..569). Extracting clip 0/60/119
  instead is a wrong-window error: delete the bad probes, record the
  local→source mapping explicitly, re-extract. Never let local indices
  pass as source indices in evidence or reports.

## 4. Correction routing that preserves the gate

- Route visual corrections to the EXACT owner session with measured numbers
  (diff table, bbox, white-pct), not adjectives. The worker moved its event
  @516→@522 and matched the manager's numbers exactly.
- `hermes --resume <id>` MAY create a NEW session instead of continuing the
  owner (observed: correction spawned a new session while the owner stayed
  terminal `agent_close`). Do not hide this: record both IDs plus which
  session is live in the registry; single-active-writer still holds because
  the old session is terminal.

## 5. Model-label errata (ping does not prove alias equivalence)

- Transposed model tokens (`...muse-spark-contributor-1.3-free` vs
  `...muse-spark-1.3-contributor-free`) can BOTH pong — that does not make
  them aliases. Pin the exact id per task from state.db / launch string,
  append a MODEL_ERRATA note preserving the original registry text, never
  rewrite history. Forensics already independently verified do not need
  redoing over a label error.
