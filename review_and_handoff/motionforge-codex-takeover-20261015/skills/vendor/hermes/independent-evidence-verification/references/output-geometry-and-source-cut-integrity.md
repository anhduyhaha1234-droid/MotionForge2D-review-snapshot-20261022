# Output geometry & source-cut integrity (measured 2026-09-28, MotionForge delivery)

Verification lessons for generated-media pipelines (image/video graphs). All three classes
shipped inside a run whose *technical* gates were green — none of them are visible to
frames/fps/duration/pts checks.

## 1. Check output dims against the SOURCE window first — before quality or cost talk

* The first baseline clip came back **480×848 portrait** while its source window was
  **640×360 landscape**. The lane's gate set covered frames/fps/duration/pts and was fully
  green; dims simply were not in it.
* Root cause traced **in the graph, not the model**: an inherited template node carried
  `resize_type.width/height = 482×854` with `crop=center`; the sampler rounded to
  multiples of 16 → 480×848. Consequence: the center-crop silently deleted half the scene
  (table, back-view figure, and the right-edge partial person = a required coverage
  element), which then *looked* like a model/coverage defect and nearly went to a
  challenger-profile comparison as if it were.
* Rules when inheriting a template: diff every resize/resolution node against the new
  source's own dims; derive the target from the source (pad to nearest multiple-of-16,
  centered) instead of cropping; declare the assembly crop-back policy in the receipt
  (e.g. pad 4+4 rows at 640×368 → crop 4 rows per side back to 640×360). On that node type
  `crop=disabled` means STRETCH — it is not a fix. `ResizeAndPadImage`-style
  scale-min+center-pad preserved the full frame.
* Cheap permanent gate: assert `out_dims == source_dims (mod the declared pad/crop policy)`
  in every per-shot gate JSON, and view frame 0 of source beside generated once.

## 2. A source "window" may contain an editorial cut — scan with a declared rule, then split

* Declare thresholds BEFORE looking: flag a cut when `changed_fraction ≥ 0.50 AND
  mean_abs_diff ≥ 12.0` (pixel-delta 32) — both conditions together avoid flagging motion
  or lighting changes as cuts.
* Measured outcome: window A correctly had **no cut** (max diff 1.50 at the book-open
  event, changed_fraction 0.012 — a motion event, not a cut); window B had a **cut at
  frame 102** → split into `[0,102)` + `[102,120)` with a per-segment anchor each.
* An unsplit window presents as "drift at the end of the clip": the generated clip holds
  segment-1 content (its anchor) while the source tail is a different scene. The fix is
  structural — split at the cut, per-segment anchor, per-segment gate against the
  segment's OWN source span — not a prompt tweak (a prompt tweak did fix a different,
  also-real defect: carried-over prompt sha; see cloned-graph reference).
* Keep the scan artifact as evidence in BOTH directions: it attests the cuts found and it
  attests "no cut" for windows that pass.

## 3. Proving a variable is INERT: decoded frames, never file hashes

* Claims like "overlap 8→16 changes nothing" / "cache off changes nothing": two same-seed
  runs produced files with **different container sha/bytes but identical decoded pixels**.
* Prove inertness with a decoded-frame absolute diff (`max_abs == 0` across all N frames),
  and state both facts — "container differs; pixels identical" — so a later reader does
  not 'fix' a non-problem. The independent verifier should re-derive with its own decode
  path (ffmpeg rawvideo → numpy), not the lane's script.

## 4. Assembly identity recheck after any segment swap

* After replacing a segment, rebuild the assembly and re-run: boundary-frame previews at
  each join, `frame_count == sum(segment spans)`, and audio-stream presence.
* Keep superseded assembly versions (v1, v1.1, …) on disk as supersede markers, and mark
  exactly one as the verify target (e.g. `FINAL_FOR_VERIFY`) so the later gate cannot
  verify a stale file.
