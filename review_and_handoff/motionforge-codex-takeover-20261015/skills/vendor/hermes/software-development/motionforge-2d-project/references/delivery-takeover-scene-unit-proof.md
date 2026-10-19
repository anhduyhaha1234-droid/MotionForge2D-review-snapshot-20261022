# Scene-unit ComfyUI proof round — measured host facts (2026-09-27/28 delivery takeover)

Context: the delivery contract requires proving scene-unit ComfyUI workflows on the real machine
(probes P0–P7 per `COMFY_UNITS_RESEARCH.md`) BEFORE writing production code, then wiring the proven
graph into the app (28-task DAG). These are the hard facts measured in the proof round so the next
session does not re-discover them.

## Host capability matrix (measured from live `/object_info`, not memory)

Runtime: `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/ComfyUI` (HEAD `73c9bad4`,
version 0.37.0). `/object_info` = **960 nodes**, sha `80850af29e04c4ae…`.

* **NOT registered by this server:** `Flux2KleinEditModel`, `Flux2KleinEditApply`, `TrackToMask`,
  `Sam2Segmentation`. Do not build graphs on these class names — they fail at `/prompt`.
* **Registered + weights present:** `WanAnimate2ToVideo`, `WanAnimateToVideo`, `WanVaceToVideo`,
  `WanImageToVideo`, `WanFirstLastFrameToVideo`, all video nodes (`LoadVideo`, `Video Slice`,
  `VideoTrim`, `GetVideoComponents`, `CreateVideo`, `ConcatenateVideo`, `SaveVideo`), image nodes
  (`ImageCompositeMasked`, `MaskComposite`, `ResizeImageMaskNode`).
* **Registered but weights MISSING:** `WanSCAILToVideo`, `SCAIL2ColoredMask`, `SAM3_Detect`,
  `SAM3_VideoTrack` (SCAIL/SAM3 are candidates only after a weights+12 GB feasibility probe).
* Model roots live in the **sibling** `runtime/video14b/models` (not `ComfyUI/models`): groups
  clip_vision / diffusion_models / loras / text_encoders / vae; groups sam3, sam2, checkpoints are
  absent.
* Wan Animate 2 takes `reference_image[:1]` — a batch of character refs does NOT mean multi-role
  swap. Multi-role needs the SCAIL/VACE class or a primary composed scene reference.

## Working anchor (image) graph shape

The proven image path (used by the R27 anchor graphs) is the FLUX2 latent pipeline:
`UNETLoader` + `CLIPLoader` + `VAELoader` + `EmptyFlux2LatentImage` + `ReferenceLatent` chains +
`ImageScaleToTotalPixels` + `ResizeImageMaskNode(scale_method='area')` +
`SamplerCustomAdvanced`/`KSamplerSelect`/`Flux2Scheduler`/`RandomNoise`/`CFGGuider` + `VAEDecode` +
`SaveImage`. Copy the node set from a graph that already ran; verify every class against the live
`/object_info` before submitting.

## Two anchor-output policies that MUST be declared, not silent

1. **Pad-to-8 resolution**: anchors come out 640×**368** for a 640×**360** source (+8 rows of latent
   padding). The pipeline must crop back to the source box before assembly/timeline or the whole
   video drifts. State the crop bbox in the evidence and verify it.
2. **Source watermark**: source frames carry the channel watermark (YouTube + channel text); the
   anchors legitimately drop it. Record that as a POLICY claim in the report — an unexplained
   missing element reads as an omission to a reviewer.

Also record per shot: who holds the prop at frame 0 (a closed book at f000 vs "book open" — the
open state may start at a specific index; check the event map before writing prompts), partial
people at frame edges (they must appear in the anchor), and prop restyles (a table repainted is a
style-pack decision, not a defect — but it goes in the report).

## Proof isolation + receipts

Launch the proof server with `--input-directory/--output-directory/--temp-directory/--user-directory/
--cache` all pointing INTO the run's `proof/` tree, a private port (8321), and `--cpu` for the P0
capability pass. Every launch receipt must carry the epoch triple (**instance_id + launched_at +
port**) plus a shutdown proof (port closed, pid gone). Evidence layout:
`RUN/proof/{graphs,tools,inputs,output,evidence}`; the CU_RESEARCH doc ships in the takeover package,
not on this host — pass its absolute path into worker packets.

## Path hazard

The R28 canonical evidence root is
`…/2026-09-27/c-v-th-c-hi-n/outputs/r28-cpu-execution-20260927/**` — a **one-hyphen-different sibling**
(`c-v-th-c-h-i-n`) exists as a decoy. Grep the exact string from an authority doc; see
`independent-evidence-verification` → `references/packet-path-drift-and-relaunch.md`.

## Manager gate practice for generated media

Read the generated PNG/MP4 with native vision and compare against the staged source frame/contact
sheet; log differences as observations (pad, watermark, prop restyle, scale) while the lane owns the
formal per-shot gate JSON. GPU discipline: one job at a time, seq receipts with wall time + peak
VRAM/RAM; a retry changes exactly one variable and ≤3 attempts per failure class.

## Wan video profile — P3b→P7 measured facts (2026-09-28, same delivery)

These are the numbers and traps the next session needs before spending GPU on the demo (Phase C).

**Geometry trap (cost one full round).** The R27 video template hard-coded node `672:600
ResizeImageMaskNode` at `482×854, crop=center` → a landscape 640×360 source rendered as portrait
480×848 with the right half of the scene (table, back figure, right-edge partial person) cropped away.
Fix that worked: DELETE 672:600 and insert the registered `ResizeAndPadImage` (scale = min-fit +
centered pad, black, area) as a new node feeding `672:596 GetImageSize` → `WanAnimate2ToVideo.width/
height` and `pose_video`; `crop=disabled` is NOT the fix (it STRETCHES). Diff = 5 nodes, 0 validation
errors. Target `640×368` keeps the full 640×360 content (pad is conditioning-only, no bars in the
output); assembly crops 4 rows each side back to 640×360.

**Cost table (same unit BOOK, seed pinned).**

| Profile | s per output-second | VRAM peak | Watermark |
|---|---|---|---|
| Wan Animate 2 INT8 @640×368, COLD (first run after server start) | 596.95 | 11,224 MiB | no |
| Wan Animate 2 INT8 @640×368, WARM | **38.67** | 10,973 MiB | no |
| Wan + `WanAnimate2Cache` OFF (warm) | **33.80** (faster, −210 MiB, pixel-identical) | 10,763 MiB | no |
| VACE 14B fp16 (challenger, 20 steps cfg6 uni_pc) | 291.13 | 11,680 MiB | **copies source watermark** |

Publish cold AND warm per profile; an ETA on warm must also price one cold run per server start.
Cache on/off and chunk-overlap 8↔16 produced **pixel-identical** output (max_abs 0, different file
shas = container-level only) — state that, don't imply a quality delta.

**Profile semantics differ per shot.** At frame 119 VACE had the book OPEN matching the source event
`open_two_pages @72` while Wan kept it CLOSED — and VACE copies the source's YouTube watermark
(blocking for that path until a removal strategy is declared). Choose the profile per shot's hard
events, not per global preference.

**Per-unit prompts are not optional.** One prompt sha carried into all three shot graphs produced
book-reading content on the TURN/OCC clips while dims/timing/frames all passed — the coverage gate
must compare against the shot's OWN source frame, not just technical gates. One variable per rerun.

**Split units at the SOURCE's own cuts.** The OCC window contained a cut (certificate @f000 →
person-at-table @f102); a single-window run anchored on f000 mismatches the later scene. Measured
cut rule that worked: declare thresholds up front (`changed_pixel_delta 32 AND changed_fraction
≥ 0.50 AND mean_abs_diff ≥ 12`), scan every window, split, then re-anchor each segment from its own
first frame and rerun with its own prompt. BOOK showed no cut (max 1.50 at 71→72 = the book-open
event, not a cut).

**Assembly = graph-native, with per-segment pins.** `LoadVideo`×3 + `LoadAudio`×3 + `AudioConcat` →
`ConcatenateVideo.complete_audio` (no ffmpeg remux). The receipt must pin file+sha+span per segment
(measured final: BOOK 120f + TURN 120f + OCC_SEG1 102f + OCC_SEG2 18f = 360f / 12.000 s / 640×368 /
AAC 44.1k stereo). Keep superseded assemblies on disk as supersede markers; boundary previews at each
segment join. Continuation: chunk length 81 / context overlap 8 leaves a numeric motion flag at the
join (80→81 ≈ 2.16 vs p99 2.17) that read as a motion-rate elevation, not a seam; overlap 16 is
inert (pixel-identical), so keep 8.
