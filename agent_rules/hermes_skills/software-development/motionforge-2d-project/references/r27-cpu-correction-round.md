# R27 CPU-correction round — reskin input-pipeline facts (measured 2026-09-27)

Source evidence root: `outputs/mf-cpu-input-correction-20260927/20260927T051440Z` (CPU only, 0 GPU; 4 lanes:
COMFY R27-03 adapter race · P1-QC R27-04 geometry authority · VIDEO14B R27-01/02/06 input+event+epoch ·
TOOL-CONTRACT R27-05 public artwork ingest delta). Read this before any GPU round that consumes the reskin
anchor inputs — the CPU round fixed *input* defects that made every prior visual FAIL uninterpretable.

## 1. ComfyUI graph: `LoadImage` IMAGE output 0 drops the alpha (measured)

- `LoadImage` returns `(IMAGE, MASK)`; the FLUX anchor builder wired output **0** alone → resize → `VAEEncode`, so a
  cutout reached the encoder as raw RGB. Reference `cast_dan_choi_standing.png`: RGBA 1024×1024, 15.499 % opaque,
  bbox 598×816, **98.859 % of its RGB pixels have all three channels < 32** → the encoder received a near-black
  image. The native decoder splits RGB from alpha (see `comfy_api/latest/_input_impl/video_types.py`), so this is
  input misuse, **not** a broken decoder — do not patch Comfy source for it.
- Reusable fix pattern (CPU-side, provenance-safe): keep the original RGBA byte-identical (record its sha256 and
  mtime); composite **once** through alpha onto flat neutral grey `(128,128,128)` into a **derived** file; pin the
  derived sha256 into the graph proposal so `LoadImage` points at the derived file; export TWO previews — the pixels
  `LoadImage` returns and the pixels the encoder receives after resize (scale-longer-side, no crop/stretch).
  Record `engine_started:false, model_loaded:false, media_generated:false` in the round's results JSON.
- Reference hygiene: a file named `..._standing.png` actually drew a **seated cross-legged** figure with face/hat/
  phone. Enforce metadata-vs-pixels with a typed refusal (e.g. `REFERENCE_POSE_METADATA_MISMATCH`) instead of
  renaming the file; the wrong filename stays as recorded data. When a cast reference is a single-colour
  silhouette block (unique RGB colours == 2), that is **authored artwork MISSING** — declare it explicitly and do
  NOT generate filler images inside a CPU round.

## 2. Source-event mapping method (BOOK shot) — per frame, never per shot summary

- The native **first** frame showed the blue **cover upright/closed** (frames 0–71); the open two-page state exists
  only from **index 72 (t = 2.4 s)** in a 120-frame / 4.000 s / 30 fps clip. A prompt that asks for "the open book"
  across the shot is provably wrong; end-of-clip state never defines frame 0.
- Whole-frame colour segmentation was useless (the room's cyan wall dominated the blue mask). Measure the object
  **inside its own screen region** with a tuned predicate (e.g. `(b>r+25)&(b>g+15)&(b>80)`), plus a zoom contact
  strip over sampled indices for visual confirmation.
- Record per event: state windows (frame ranges + seconds), the exact **owner** holding the prop, full/partial
  roles — including a **partial person cut by the frame border** that existed on every frame and was never declared —
  occlusions, camera/cut facts (no luminance jump > 12 across the window), and the source watermark to be excluded.
- Source frames constrain **layout/camera/scale/contacts/occlusion/motion-state only**; they are never the target
  identity (do not use the source person as the target to make a pass easier).

## 3. Shutdown-proof / epoch binding

The shutdown classifier must bind its verdict to the immutable `instance_id`/epoch **plus** process lifetime, not
the port: measured live epoch `b9d3df1c…` on port 8310 vs the frozen wave-B epoch `96ab17eb…` on the SAME port —
exactly the scenario a port-only check false-confirms. Missing `instance_id` = missing authority (not a pass);
foreign instance on the same port = contradiction.

## 4. Evidence layout that survived review

`derived_inference_input/` (original vs derived, hashes kept separate) · `previews/` (loadimage-pixels vs
encoder-input pairs) · `graph_proposals/` · `SOURCE_EVENT_AND_REFERENCE_MAP.md` · `fixtures/` (one dir per
adversarial control) · `raw/` (per-gate logs + JSON, pre-fix and post-fix copies kept as history) ·
`REPORT.md` / `MATRIX.md` / `results.json` / `RAW_EVIDENCE_INDEX.md`. A broad-gate test that lives OUTSIDE the
write-set (a sha pin in an older round-D test) stays RED and is **disclosed with resolution options left to the
reviewer** — never edited to go green.
