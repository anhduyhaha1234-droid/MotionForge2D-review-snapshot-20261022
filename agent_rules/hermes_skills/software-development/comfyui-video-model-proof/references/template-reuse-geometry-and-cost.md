# Template reuse: inherited geometry + measured cost (2026-09-27, MotionForge delivery)

Datapoints behind SKILL.md §3 ("diff the resize chain") and §4 (throughput). Read this before
reusing ANY previously-proven template to build a new run.

## 1. The trap: a rebuild "with 4 documented deltas" can still carry stale geometry

Measured chain: template `mf_animate2_book4s.shim.api.json` (sha `6e92d82b…`) → built graph
`animate2_book.p3.api.json` (sha `441cf65f…`). The receipt listed exactly four deltas —
`LoadImage.image`, `LoadVideo.file`, and two `SaveVideo.filename_prefix` — i.e. inputs and
outputs rewired, nothing else touched. That reads like a faithful reuse.

The inherited literal was node `672:600 ResizeImageMaskNode`:

```json
{"resize_type": "scale dimensions", "resize_type.width": 482, "resize_type.height": 854,
 "resize_type.crop": "center", "scale_method": "area", "input": ["672:595", 0]}
```

`672:595` is `GetVideoComponents` of the driving clip, so every driving frame was
**center-cropped** to a portrait box before conditioning; the model rounded 482×854 → **480×848**.
A 640×360 landscape source came back as a 480×848 portrait clip with the right half of the scene
gone — including the edge-partial role the coverage requirement names explicitly.

**Rules that follow:**
- A deltas list is NOT a geometry audit. When reusing a template, always diff the geometry chain
  (`ResizeImageMaskNode` / `GetImageSize` / the sampling node's `width`/`height` inputs) against
  the CURRENT source window, class-by-class.
- Retarget from the source's own dimensions: **pad** to the /16 multiple (640×360 → 640×368) and
  crop the pad back on export; never center-crop away content to reach a target shape.
- Assert the resolved W×H in the built graph *before* submitting, and keep the comparison seed
  unchanged so geometry is the single isolated variable between the two runs.
- Gate output W×H vs source W×H as its **own** row: time fields (frames/fps/duration) matching is
  not a geometry pass — see SKILL.md §5.

## 2. Read the output tree by node, not by file count

One prompt (`bbd21edd-…`, status `success`) wrote **4** files from **2** SaveVideo nodes:

| node | file | geometry | frames | bytes |
|---|---|---|---|---|
| 246 | `…_00001_.mp4` | 480×848 | 120 | 259,061 |
| 246 | `…_00002_.mp4` | 480×848 | **1** | 28,073 |
| 292 | `…_00003_.mp4` | **1986×848** | 120 | 346,108 |
| 292 | `…_00004_.mp4` | 1986×848 | **1** | 50,793 |

Two output branches and 1-frame "videos" (stills / composed strips) are normal for this template
family — a file-count heuristic ("4 outputs = 4 runs") is wrong. Count submissions from
`/history` `prompt_id`s only (see `references/motion-window-and-submit-counting.md`); here it was
one prompt for all four files.

## 3. Cost datapoints for ETAs (RTX 5070 12 GB, ComfyUI 0.37)

Config: Wan Animate 2 INT8 (`wan_animate_2_int8_convrot`) + LightX2V rank64 distill,
6 steps lcm, cfg 1, shift 5, chunk 81 / context 21 / overlap 8, `WanAnimate2Cache` int8 gpu.

| span | wall | per output second | VRAM peak | GPU util peak |
|---|---|---|---|---|
| 120 f @ 30/1 = 4.000 s @ 480×848 | 2,394.31 s (39.9 min) | **598.58 s/s** | 11,897 / 12,227 MiB (97 %) | 100 % |

- Server RAM peak: **NOT MEASURED** (tasklist parse returned 0 → record `NOT MEASURED`, never 0).
- 640×368 is 0.58× the pixel area of 480×848 — expect cheaper, but re-measure; never quote a
  predicted s/s as measured.
- State the arithmetic in the report so nobody assumes otherwise: 30 min of source at 598 s/s
  ≈ 300 h of GPU; a 12 s stress demo ≈ 2 h per pass. Report throughput only as **seconds of
  render per second of video a reviewer ACCEPTED**.
- A run at 97 % VRAM peak leaves no room for a parallel GPU job — one GPU job at a time, cold vs
  warm measured separately, and shutdown proven (port closed, pid gone, VRAM back to idle).

### 3b. The geometry fix, AND the cold/warm confound in its cost claim

| run | geometry | wall for 4 s | s/output-s | VRAM peak | server state | notes |
|---|---|---|---|---|---|---|
| P3 | 480×848 portrait | 2,394.31 s | **598.58** | 11,897 MiB | **COLD** (first run after launch) | center-crop; right half of scene gone |
| P3b | **640×368** (pad 4+4) | **~155 s** | **38.67** | 10,973 MiB | **WARM** | same seed `582699151003550` |
| P6 cache OFF | 640×368 | 135.21 s | **33.80** | 10,763 MiB | WARM | pixel-identical to P3b |
| later warm runs (TURN/OCC/SEG) | 640×368 | ~140–160 s each | ~35–40 | ~11,000 | WARM | same profile |

- **Correction to the earlier claim in this file: do NOT attribute the 15.5× to the geometry fix.**
  The two runs differ in **two** variables at once — geometry *and* server thermal state (P3 was the
  **cold** first run; the worker's own cost table reads `Animate2 cold 596.95 s/s · warm 38.67 s/s`).
  Every measured **warm** run clusters at **~34–39 s/output-s regardless of geometry**, so the
  dominant term here is cold→warm, not pixels. Rule: **never compare a cold run to a warm run and
  call the delta a code effect** — re-measure the SAME config twice on one server, or state the
  confound explicitly in the report. (The pixel-area heuristic being wrong is still true — area is
  simply not the variable this pair measured.)
- The area heuristic (640×368 is 0.58× the area of 480×848) is NOT a valid predictor for these
  graphs; the only defensible way to price a geometry change is warm-vs-warm.
- **Each server restart costs one cold run (~40 min for a 4 s clip at 480×848 observed; ~10 min at
  640×368).** Budget it explicitly in ETAs: warm throughput prices the batch, cold throughput prices
  each relaunch — do not quote one as the other.
- Record the corrected crop policy explicitly: **centered pad 4 rows top + 4 bottom** keeps the full
  640×360 content; the export stage crops those 4 rows back — never the sides.
  extrapolate a predicted s/s into a report.
- Record the corrected crop policy explicitly: **centered pad 4 rows top + 4 bottom** keeps the full
  640×360 content; the export stage crops those 4 rows back — never the sides.
- Same-window profile comparison (one run each, identical inputs and seed):

| profile | steps / cfg | s/output-s | VRAM peak | defect |
|---|---|---|---|---|
| Wan Animate 2 INT8 + LightX2V rank64 | 6 / 1 lcm | **38.67** | 10,973 MiB | — |
| VACE 14B fp16 | 20 / 6 uni_pc | 291.13 | 11,680 MiB | **copies the source watermark** (blocking) |

A challenger profile is not interchangeable just because it renders: VACE reproduced the source's
watermark overlay into the output (name this as its own blocking-defect row, don't average it away
in the coverage PASS), and its raw 121-frame pass needed a declared trim to 120 before frame/time
gates passed.

### 3c. Chunk-boundary seam: the number and the verdict are TWO rows

BOOK run (chunk 81 / context 21 / overlap 8) showed a numeric spike in consecutive-frame
mean-abs-diff at the boundary pair **80→81 = 2.16** against a 0.1–0.8 neighbourhood baseline, with
no visible seam in the strip. Record both, separately:
`seam_numeric_flag: {pair: "80->81", value: 2.16, baseline: "0.1-0.8"}` and
`seam_verdict: NO_VISIBLE_SEAM_DEFECT` — never collapse them into one "no seam" claim, and keep the
pair for the next bounded continuation hypothesis (overlap 8→16 is the single-variable test).

## 4. Anchor geometry note (pairs with `scene-unit-proof-and-anchor-review.md`)

Anchors generated at 640×368 carry an **+8-row pad** vs the 640×360 source: the assembly stage
must crop the pad back, or the timeline/scale check fails downstream. The anchor review itself
(watermark policy, text-on-prop = content, placeholders declared as placeholders, partial edge
roles) lives in that reference — this file only fixes the geometry/scale side of it.
