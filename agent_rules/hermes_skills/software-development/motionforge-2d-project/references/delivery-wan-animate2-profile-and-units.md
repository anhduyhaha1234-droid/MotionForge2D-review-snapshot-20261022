# Wan Animate 2 / VACE profile + scene-unit pipeline — measured 2026-09-28 (delivery Phase A tail)

Companion to `delivery-takeover-scene-unit-proof.md` (P0–P2 facts). This file records P3b–P7: the geometry defect+fix,
the real cost table, determinism, the cut-split/per-unit-prompt semantics, and the graph-native assembly.

## Profile cost table (same unit BOOK, same seed 582699151003550, 4 s / 120 f / 30 fps)

| Profile | s per output-second | wall (4 s clip) | VRAM peak | Watermark | Notes |
|---|---|---|---|---|---|
| Wan Animate 2 INT8 `@640×368` COLD | **596.95** | 2,394 s | 11,897 MiB | no | first run after server start |
| Wan Animate 2 INT8 `@640×368` WARM | **38.67** | 154.67 s | 10,973 MiB | no | the usable number |
| Wan + cache OFF (warm) | **33.80** | 135.21 s | 10,763 MiB | no | 19.5 s faster; PIXEL-IDENTICAL to cache-on |
| VACE 14B fp16 (20 steps cfg 6 uni_pc) | **291.13** | 1,174 s (121 raw frames) | 11,680 MiB | **copied (blocking)** | whole latent, no seam |
| Earlier P3 portrait run `@480×848` | 598.58 | 2,394 s | 11,897 MiB | no | see geometry defect below |

Rules: publish cold AND warm separately (a first-run number is not a profile cost); cache on/off and context-overlap
8→16 both produced `max_abs_diff = 0` on decoded frames (different container shas only) — so cache-off is a free 12%
and the overlap change is INERT (keep 8).

## Geometry defect and the real fix (Wan Animate 2 graphs)

* Symptom: output 480×848 portrait for a 640×360 landscape source; the right half of the scene (table, back-view
  figures, the partial edge person) was cropped away → coverage gate FAIL, not a model fault.
* Root cause: the graph inherited a hardcoded `ResizeImageMaskNode` (`672:600`) with `resize_type.width/height =
  482/854` and `crop: "center"` from the older template; the model rounds to /16 → 480×848.
* `crop=disabled` is NOT the fix — that setting STRETCHES (nodes_post_processing.py:440). The fix is to insert the
  registered **`ResizeAndPadImage`** (scale = min-fit + CENTERED pad; nodes_images.py:594-641) targeting 640×368 with
  black/area, feeding `GetImageSize` → `WanAnimate2ToVideo.width/height` and the pose-video input; remove the old
  resize node. Pad is conditioning-only → no black bars in the render; assembly crops 4 rows top+bottom back to 640×360.
* Gate for any such fix: dims vs source aspect + coverage on frames 0/60/119 with native vision (the partial edge
  person must be back) + frames/fps/duration/PTS + "no visible seam".
* Footgun: a cloned graph keeps the original `SaveVideo` PREFIX — outputs landed in `output/p3/` while the round
  expected `p3b/`. Reconcile by hash-verifying the existing files FIRST, then relocate with a mapping+hashes file;
  do NOT re-run (the prefix does not enter the computation).

## Chunking / seam (Wan Animate 2, 120 f)

Chunk 81 / context overlap 8 is the working primitive; a numeric seam flag at the join (pair 80→81, mean_abs_diff
2.16 vs ~0.1–0.8 baseline) read as motion-rate elevation (the woman's arm rising), with 0 zero-diff pairs and no
visible defect — keep the flag, label it, and don't "fix" it blind.

## Unit semantics learned the hard way (two content defects, both fixed by ONE variable each)

1. **Per-unit PROMPT is mandatory.** The BOOK prompt was carried into all three graphs (identical prompt sha across
   TURN/OCC) → the TURN clip rendered a "person reading a book" scene instead of the certificate. Gate content against
   the SEGMENT'S OWN source, not just technical fields; fix = the unit's own prompt, one variable.
2. **A source window can contain a CUT — split the unit at the cut.** Measured with a declared rule
   (`changed_fraction ≥ 0.50 AND mean_abs_diff ≥ 12` on consecutive decoded frames): BOOK no cut (max 1.50 at 71→72 =
   the book-open EVENT, changed_fraction 0.012 — an event is not a cut), OCC cut at frame 102 → split into
   SEG1 [0,102) + SEG2 [102,120) with its own anchor AND its own prompt (the un-split window kept the certificate
   anchor through a scene that switches to "person at a table" → mismatch at the clip tail).
3. **Book-state is a real product decision**: Wan kept the book CLOSED through the window while the source event
   `open_two_pages @72` opens it (VACE opens it but copies the watermark). Record as policy for the reviewer — do not
   silently pick.

## Assembly (P7, graph-native)

`LoadVideo×3 + LoadAudio×3 + AudioConcat → ConcatenateVideo.complete_audio` — no ffmpeg remux. Verified:
360 frames / 12.000 s / 640×368 / AAC 44.1k stereo; **pin every segment by file+sha+span in the assembly JSON**
(`P7_ASSEMBLY_V13.json`) and re-check boundary frames (119/120, 239/240, 341/342). Keep superseded assemblies (v1,
v1.1, v1.2) on disk as supersede markers; the "final for verify" one is named explicitly in the candidate doc.

## Verification contract that closed the gate

Writer terminal (evidence index frozen, newest write timestamped) → BENCH independent audit (246/247 hash checks, then
a full-index re-audit 323/323; its own ffprobe/numpy scripts; accepted-second cost = UNDEFINED while
`accepted_seconds = 0`) → DEMO visual pass (≥9 frames, boundary strips, U-mapping, `DEMO_OWNER_VISUAL_PASS` with
findings) → orchestrator's own eyes at 5 checkpoints. `QUALITY_ACCEPTED=0` throughout; only the independent reviewer
writes APPROVED/CLOSED.
