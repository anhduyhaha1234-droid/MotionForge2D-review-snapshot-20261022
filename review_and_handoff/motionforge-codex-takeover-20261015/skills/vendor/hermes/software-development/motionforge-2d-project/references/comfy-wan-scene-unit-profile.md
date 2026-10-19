# ComfyUI / Wan scene-unit profile — MEASURED facts (2026-09-27/28 delivery run)

All numbers below were produced by real runs on this host (RTX 5070 12 GB). Use them instead of
re-measuring; the evidence root for the full proof is
`…/mf-delivery-runs/20260927/20260927T163824Z/proof/` (PROOF_GATE_CANDIDATE.md = checklist).

## Primary profile (video)

- Wan Animate 2 INT8 (`wan_animate_2_int8_convrot`) + LightX2V `rank64_bf16` LoRA +
  `umt5_xxl_fp8_e4m3fn_scaled` + `clip_vision_h` + `Wan2_1_VAE_bf16`; 6 steps · lcm · cfg 1 ·
  shift 5 · context 21/8 · **cache OFF**.
- **Speed: cold ≈ 597 s per output-second** (model init ~907 s, ~297 s/it) vs **warm ≈ 38.7
  s/output-s**. A "15× speedup" between two runs is almost always cold→warm, not a config win —
  always compare warm-vs-warm and label which is which.
- Cache ON vs OFF (same seed, warm): OFF 135.21 s vs ON 154.67 s; VRAM 10,763 vs 10,973 MiB;
  **outputs pixel-identical (max_abs 0) but different file sha** (container metadata only).
  Audit determinism by decoding pixels, not by comparing shas.
- VRAM peak ≈ 10.9–11.9 GiB. `nvidia-smi` VRAM works; process-RAM samplers on this host return
  non-credible values (~5 MiB) — record **NOT MEASURED**, never a fake 0.

## Geometry — the biggest trap

- Template node **`672:600 ResizeImageMaskNode` hardcodes `width/height = 482/854` + `crop:
  center`** → portrait latent 480×848 from a 640×360 source; the center-crop silently deletes the
  right half of the scene (props, back figures, partial characters) while every decode check still
  passes. Symptom: correct frames/fps/duration, wrong coverage.
- **Fix**: insert the registered `ResizeAndPadImage` with target = source aspect rounded to /16
  (640×360 → **640×368**), `scale = min(fit)` + centered pad (black), and feed its `GetImageSize`
  into `WanAnimate2ToVideo.width/height` and the pose video; delete the hardcoded node.
- `crop=disabled` is NOT the fix — it **stretches**.
- The pad is conditioning-only: the output has no black bars. Recovering the source shape at
  assembly = crop the pad rows (4 top + 4 bottom), never the sides.
- Wan Animate 2 emits `4n+1` frames on some paths — declare any trim (121→120) explicitly in the
  receipt and keep both raw + trimmed hashes.

## Content-correctness rules (learned the hard way)

- **Prompt per unit.** A prompt carried across units generates the wrong scene: a BOOK prompt left
  in the TURN/OCC graphs produced "person reading a book" for every shot. Swap the positive prompt
  per unit and record the prompt sha before/after (identical prompt sha across graphs = red flag).
- **Source windows can contain cuts.** Scan each window before treating it as one unit (declared
  rule: `changed_fraction ≥ 0.50 AND mean_abs_diff ≥ 12`). A window that starts on a certificate
  and ends on a person at a table is TWO units — split at the cut, give each segment its own anchor
  (from the segment's first frame) and its own prompt. Assembly then pins file+sha+span per segment.
- Prop-state events are hard events: if the source opens a book at frame 72, a clip that keeps it
  closed for the whole window fails the event even when coverage passes.

## Model behaviours / availability (this runtime)

- **VACE 14B fp16 (challenger)**: honours hard relations and source events, but **copies the
  source watermark** (play button + channel text) = blocking for delivery, and costs ≈ 291
  s/output-s (7.5× the warm primary). Use only for shots where the primary fails relations, and
  only with a declared watermark-removal strategy.
- **Not registered** (do not build graphs on them): `Flux2KleinEditModel`, `Flux2KleinEditApply`,
  `TrackToMask`, `Sam2Segmentation`. Weight groups sam3/sam2/checkpoints are absent.
- The **working image path** is `UNETLoader + EmptyFlux2LatentImage + ReferenceLatent`
  (+ `ImageScaleToTotalPixels` / `ResizeImageMaskNode`) — see the R27-I1 anchor graphs
  (`…/20260927T051440Z/VIDEO14B/graph_proposals/anchor_book.i1.api.json`). FLUX.2 klein 4B
  distilled image-edit + in-graph alpha compositing produced a real 1024×1024 asset (MF-END-08).
- Server hygiene: run ComfyUI isolated (`--base-directory` pointing at the pinned runtime), **1 GPU
  job at a time**, and record a shutdown proof (POST_STOP_VERIFIED: port refused, pid gone).
  `object_info` is only meaningful when the server was started with the base-directory (otherwise
  loader enums come back empty).
- Graph builder footgun: reuse of a template's `SaveVideo` prefix writes outputs into the OLD run
  dir; always set a per-run prefix and reconcile + hash-check before moving anything.

## Cost model for planning

`s_per_output_second = server_side_wall_s / output_duration_s`.
Warm primary ≈ 38.7 → a 4 s shot ≈ 2.6 min warm (+ one cold pass per fresh server start);
a 12 s stress demo (3 shots) ≈ 8 min GPU once graphs are correct; a 30-min full source at this
profile ≈ 19 h (feasible overnight, not interactive). `accepted_seconds = 0` until a quality
review accepts — never quote a cost per *accepted* second before then.
