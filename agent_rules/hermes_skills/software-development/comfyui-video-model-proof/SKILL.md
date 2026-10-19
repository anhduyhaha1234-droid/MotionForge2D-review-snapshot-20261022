---
name: comfyui-video-model-proof
description: "Prove a published ComfyUI video model runs locally."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [comfyui, video, vace, gpu, windows, verification, gates]
    related_skills: [local-comfyui-adapter-proof, terminal-engineering-discipline, comfyui]
---

# Proving a published ComfyUI video model on a small GPU

Use when a task says "reskin/replace the look of an existing MP4 with a real released model",
"V2V / source-conditioned editing", "does model X fit 12 GB", or asks for the first real clip
from a video model. Companion to `local-comfyui-adapter-proof` (that one covers the adapter
contract + image proof; this one covers the **video** half: workflow conversion, memory fit,
and clip gating).

Hard rule that governs the whole class: **the picture/animation technology must be an
existing published model with released weights and a maintained official workflow.** The app
manages input, shot splitting, references, queue/resume, QC, assembly and export. No
hand-written renderer, propagation, optical-flow warp, rig/mesh, latent blending or training —
a job whose outcome is "our own engine got better" is the wrong job.

## 1. Before downloading anything

1. Verify upstream **once**, at a pinned revision: release date, license, whether the node
   class exists **in the commit you are pinning** (read the node source / `/object_info`, not
   a blog post), and the exact official template matching that checkpoint.
2. Record per file before download: URL, repo revision, license, declared size, free disk.
   After download: real SHA-256 of the file on disk → `VALIDATED` / `UNVALIDATED`.
3. License unclear (e.g. a LoRA repo with no license file at the pinned revision) ⇒
   `EXCLUDED_FROM_RUN`, plus a verifier proving no executable node references it and the file
   is not reachable from the engine's model search path. Never hand-mix an unlicensed
   distill/LoRA with a checkpoint that was not released as a matched set.
4. Cap the candidate budget in writing (2 video candidates is a sane cap) and say which one
   is the fallback **before** the first run, so a failure does not trigger improvisation.
   A newer/faster model is a replacement **slot**, not an addition.

## 1b. Prove the runtime's capabilities BEFORE spending GPU (P0)

Cheap, CPU-only, and it decides the whole graph plan. Launch the pinned source with
`--cpu --listen 127.0.0.1 --port <dedicated> --disable-auto-launch` and every dir
(`--input-directory/--output-directory/--temp-directory/--user-directory/--cache-none`)
pointed at a task-local root; dump `/object_info` (record node count + total bytes + sha256)
and `/system_stats`; shut it down with the same verified-pid discipline as §8. Receipt:
cmdline, pid, port, `instance_epoch` (id + launched_at), shutdown proof (POST_STOP_VERIFIED).

**The 5-column matrix — never inferred across columns.** For every node the plan needs,
record `source-present | imported | weights-present | inference-tested | quality-accepted` as
separate columns. Measured on one runtime (ComfyUI 0.37, 960 nodes): SAM3/SCAIL node classes
imported fine but the weights groups (`sam3`, `sam2`, `checkpoints`) were ABSENT — "node
exists" ≠ "runnable". And four classes the plan wanted (`Flux2KleinEditModel`,
`Flux2KleinEditApply`, `TrackToMask`, `Sam2Segmentation`) were **not registered by the running
server at all** even though related source files shipped — the live server, not the repo
listing or a research doc, is the authority. Fill `inference-tested` with NOT YET RUN on a CPU
pass; never with True by expectation.

**Reuse the shape that already ran on THIS runtime.** When the plan's preferred
node/template is not registered, do NOT improvise a replacement graph: reuse a graph that
already produced accepted artifacts on the exact same commit (diff it class-by-class and
input-by-input against the live `/object_info`), and mark the missing path
BLOCKED_DEPENDENCY/typed refusal instead of substituting silently.

**Extract node interfaces from the live dump, not from memory.** Record required inputs per
node straight from `/object_info` — they are exactly what the API prompt validator enforces.

Measured P0/P1 recipe, and the target-anchor review checklist (pad/crop, watermark policy,
content-vs-appearance, partial edge roles): `references/scene-unit-proof-and-anchor-review.md`.

## 2. Runtime scaffolding (task-local, never the user's install)

Own venv + models + input/output/temp + logs + its own port. Copy the ComfyUI commit that
contains the needed node; never upgrade the user's install in place. For CUDA wheels, verify
the index **and** that the wheel's arch list contains the card's capability — Blackwell
(sm_120) needs a CUDA ≥ 12.8 toolchain, and the arch list is the proof:
`torch.cuda.get_arch_list()` must contain `sm_120`, plus `is_available()` and
`get_device_capability(0) == (12,0)`. Record `torch.__version__`, `torch.version.cuda` and
the full arch list verbatim; keep the rollback command in the same evidence file.

## 3. UI template → API prompt: the step that silently blocks everything

`POST /prompt` accepts only the **API/execution** format; released templates are **UI** format
(`nodes`, `links`, `definitions.subgraphs`) and the pinned backend has **no converter**.
Working method: drive the running server's own frontend headlessly (Playwright → load
`http://127.0.0.1:<port>` → import the template → call the frontend's `graphToPrompt()`) and
save the result. Assert before submitting, against the live `/object_info` of that commit:

* every `class_type` and input name exists (`missing_classes == []`);
* no node references an excluded/unlicensed weight;
* the nodes that must receive source video / reference image actually receive them.

**The autogrow trap:** the frontend serialises autogrow inputs in *dotted* form
(`values.a`, `inputs.input0`) and the backend demands exactly that. "Fixing" them into
dicts/lists yields `required_input_missing` / `prompt_outputs_failed_validation` on every
attempt. Pass the frontend output through verbatim; on rejection read
`node_errors.<id>.class_type` — those ids show which subgraph node broke. A subgraph instance
(ids like `672:648`) failing while top-level classes all resolve is the signature of this bug.

**Conditioning windows are SAMPLING windows, not video-frame windows — and a released
template's own defaults are the control.** `WanAnimate2ToVideo` takes
`pose_strength / pose_start_percent / pose_end_percent / reference_image_strength`. Those
percentages select where in the **denoising schedule** the pose branch is applied, so a value
of `0..0` silently conditions only the first step and the rest of the sampler runs
unconditioned — the picture still renders and still looks like a clip, which is why it passes
a careless gate. Measured: submitted config `0..0` → pose applied to **1/6** steps (sigma 1.0
only); the shipped template's `0..1` → **6/6** steps (1.0, 0.961716, 0.909215, 0.833333,
0.714897, 0.500600). Cache does not rescue it (`apply_pose = pose_latents is not None` ⇒ the
pose branch is simply absent outside the window). Before blaming a model for weak motion,
diff your exported graph against the **official template in the pinned commit** and confirm
which conditioning-window values it actually uses — and note that a UI template stores widget
values as a **positional array**, so you must map them through that node's widget order read
from the live `/object_info`, never by eye.

**Reusing a proven template re-imports its hardcoded geometry — diff the resize chain.**
A graph rebuilt from an earlier round's template silently inherited `ResizeImageMaskNode`
literals (`resize_type.width: 482`, `resize_type.height: 854`, `resize_type.crop: "center"`)
from a portrait-era config: a 640×360 **landscape** source came back as a **480×848 portrait**
clip. Frame count, fps and duration all still matched the source, so a decode-check that
asserted only those three scored the run `match_source: true` while the center-crop had cut
away the right half of the scene (a table, back-view figures and the edge-partial role that
the coverage requirement names explicitly). Deltas that only rewire inputs/outputs do NOT
sanitise geometry. When reusing any template, diff the geometry chain
(`ResizeImageMaskNode` / `GetImageSize` / the sampling node's `width`/`height` inputs) against
the CURRENT source window: retarget from the source's own dimensions, **pad** to the /16
multiple (640×360 → 640×368, then crop the pad back on export) instead of center-cropping,
assert the resolved W×H in the built graph before submitting, and pick the repro seed
unchanged so the geometry is the single isolated variable. **Mind the cold/warm confound when you price a fix.** The geometry pair measured 598.58 → 38.67 s
per output second — but the portrait run was the server's **cold first run** and the fixed run was
**warm** (`Animate2 cold 596.95 · warm 38.67 s/s`), and every warm run since clusters ~34–39 s/s at
either geometry. So the dominant term is cold→warm, not the resize chain: **never compare a cold
run to a warm run and call the delta a code effect**, and budget one cold run per server restart in
any ETA. Re-measure same-config-twice on one server before claiming a speedup; never extrapolate a
predicted s/s into a report.

**Bind each graph's prompt to its OWN unit, and cut-scan every source window.** A rebuild that only
rewires inputs/outputs can silently carry the previous unit's text conditioning: measured, the same
prompt sha (`540d16b7…`) sat in all three shot graphs and the TURN clip — a certificate/document
shot — rendered the BOOK scene ("person reading an open book") with every technical gate green.
Assert per-graph prompt identity against the unit manifest, and compare src-vs-gen at first / mid /
**last** frames (a content-wrong clip can match frame 0 and drift by the end). Also run a
declared-threshold mean-abs-diff cut scan on every source window BEFORE building units: a window that
spans a source cut rendered the start scene through the whole clip, so it must be split AT the cut —
one anchor (from its own first frame), prompt, receipt and span per segment — with the assembly
pinning file+sha+span per segment. Cache ON/OFF and overlap changes measured pixel-identical at the
same seed (cache OFF ~12 % cheaper) — isolation controls, not defaults. Detail:
`references/content-binding-and-source-cuts.md`. Orchestrator-side pixel review of a worker's
media claims (frame extraction recipe, cross-segment traps, supersede-chain discipline):
`references/manager-pixel-review-of-worker-media.md`.

Measured numbers, exact rejection strings and the fit/gate tables:
`references/video-model-fit-and-clip-gates.md`.
Template-reuse geometry trap, cost datapoints and the anchor-review pairing:
`references/template-reuse-geometry-and-cost.md`.
Conditioning-window semantics, submit counting and the 1/6-vs-6/6 probe:
`references/motion-window-and-submit-counting.md`.
Post-export verification of a delivered clip — the exact commands and the values a correct
deliverable produces (container/PTS order/audio/geometry/frame-map):
`references/delivered-clip-verification.md`.

## 4. Memory fit: measure, never predict

Do not predict OOM from parameter count. A 14B fp16 diffusion model (33,068 MB staged)
executed on a 12,227 MiB card using ComfyUI's dynamic VRAM loading with RAM offload: peak
≈ 9,180 MiB, ~30 GB RSS in the server, GPU 100 %. Plan **one heavy GPU job at a time**,
stage/unload the image model before the video job, and allow at most two reasoned memory
configurations per candidate (declared resolution/frame-count/FPS changes included). **Compare candidates on accepted-second throughput AND gate overlays.** Measured same-window,
same-seed on one 12 GB card: the INT8 + LightX2V distill baseline (6 steps / cfg 1 lcm) ran at
**38.67 s/output-s, 10,973 MiB peak** while the VACE 14B fp16 challenger (20 steps / cfg 6 uni_pc)
ran at **291.13 s/output-s, 11,680 MiB** — and the challenger **copied the source's watermark**
into its output while the baseline did not. A profile that passes the relational gates but
reproduces a source overlay is not interchangeable: name that as its own blocking-defect row and
make the challenger conditional, never default. Report cold vs warm load, inference and decode
separately, and quote throughput only as **seconds of render per second of video a reviewer
ACCEPTED** — never frames/second, never a vendor speedup.

## 5. Gate the clip from bytes, not from your own expectations

A ffprobe-only pass routinely coexists with a wrong deliverable. Measure all of:

* frame count derived **twice** (`nb_frames` and `-count_frames … nb_read_frames`), CFR,
  container duration;
* **dimensions against the SOURCE**, not against a value copied from the candidate (a
  640×368 candidate for a 640×360 source once scored `PASS` because the expectation came from
  the candidate itself). Keep W×H as its **own** row: a run can match frames, fps and duration
  while the output is a different *shape* (measured: 480×848 portrait vs 640×360 landscape
  where only the three time fields matched) — `match_source` on time fields is never a
  geometry PASS. Print source W×H and output W×H on the same line and fail the
  "keep composition/scale/crop" gate on any aspect change;
* **audio window**: packet count, first/last `pts_time`, `start_time`, `duration`, and the
  delta versus the intended window with a declared tolerance (AAC frame =
  1024/44100 = 0.023220 s ⇒ ±1 frame). `-c:a copy` plus `-avoid_negative_ts make_zero`
  produced a 9.241542 s audio stream (398 packets) inside a 4.000 s clip — always measure it.
  Then prove the window itself by **decoding both sides to raw PCM and comparing**: extract the
  candidate's audio and the source film's intended window (e.g. `-ss 55.000 -t 4.001995`) as
  `s16le`, then compare sample-by-sample. A correct remux gives an identical sample hash and
  `MAE == 0.0` (measured: 352,968 samples, 0 mismatches, both sha256 `af876599…`); anything
  else means the window is wrong no matter how close the duration looks. Decode the source with
  the SAME length as the candidate, not the nominal window, or the last block reads as a
  mismatch.
* **PTS contract**: a source-conditioned diffusion model writes its own timebase, so an
  absolute `pts == frame_id * 512` contract is not satisfiable for its output. Keep the FAIL
  rows, add an explicit `frame_map.json` (out frame i ↦ source frame N+i) plus the padding
  removal point, and normalise only the **container** (start 0, CFR, exact duration).
  Changing fps metadata (24↔30) or rescaling stays forbidden. Label the outcome
  `TECHNICAL_PARTIAL_WITH_DISCLOSED_PTS_LIMITATION`, never `TECHNICAL_PASS`.
* **Assert CFR on PRESENTATION pts, not on packet order.** A B-frame h264 stream has
  non-monotonic packet pts in decode order (`packet_pts_monotonic_decode_order: false`, deltas
  `{-1024,-512,+1024}`) while its presentation pts are exactly `i * 512`. A harness that reads
  packets in file order reports a false CFR failure on a correct clip — read the frame list /
  sorted pts and say which order you measured.
* **A frame map is NOT proven by similarity metrics on a flat window — say which it is.**
  Per-frame MAE argmin against the source frames spread over offsets −3…+3, with only **8/120**
  frames favouring offset 0 and a median advantage of **−0.0006** grey levels (flat cartoon
  window, median MAE ≈ 75). The map stood as a *derivation* (driving-clip order + padding
  removal), not as a pixel measurement. Report "supports the map, does not prove one-frame
  identity" and keep the derivation as the authority; a separation that small is noise, and
  quoting it as verification is a false pass.
* **A CORRECT remux still overshoots 4.000000 s by ~2 ms — state the arithmetic so nobody
  "fixes" it.** 4.000 s = 176,400 samples = **172.27** AAC frames, so whole-packet copy
  (`-c:a copy`, no re-encode) cannot land on the edge: measured container audio **4.001995 s /
  216 packets** for a 4.000000 s video, with the PCM still bit-identical to the source window.
  Disclose `+1.995 ms` as an expected limitation — the only ways to remove it are re-encoding
  (forbidden, it changes the source audio) or trimming real samples. Keep the superseded export
  as well (the earlier bad one, 9.241542 s audio, lives in a `media/superseded_r3/` dir with its
  own sha), never overwritten.

Vocabulary to keep separate in every report: `TECHNICAL_PASS` / `TECHNICAL_PARTIAL_*` /
`FAIL` / `UNMEASURED` / `NOT_REVIEWED` / `RUNNABLE_LOCAL` / `QUALITY_ACCEPTED`. No vision on
the LLM route ⇒ every semantic row stays `NOT_REVIEWED`, no row is ever `QUALITY_ACCEPTED`,
and the clip is handed to a human reviewer.

## 6. Padding and length

Models that need `4n+1` frames (or similar) must have the padding **declared in a map** and
removed exactly on export. Record the native length, the padding frames, the removal point,
and keep the raw render alongside the exported clip (raw = evidence, final = deliverable).
Never change metadata fps or rescale to fake the requested duration.

## 7. Disconnect / power-loss / resubmit discipline

The server queue is in-memory; history is on disk. After any disconnect or restart, read
`/queue` and `/history` **before** any resubmit, diff the `output/` tree against history
entries, and mark any file without a successful history entry
`INCOMPLETE_NOT_A_RESULT` — it must never be staged, exported, reviewed or counted.
Checkpoint after every run.

**Count submissions from the server's own history — never from progress bars or output files.**
One released template can run **several sampling passes per prompt** and emit **several output
nodes**. Measured 2026-09-23: an Animate-2 BOOK run printed two 6/6 progress bars and wrote two
`.mp4` files (a single-view `640×368` and a `1280×368` two-up composite), and that looked like
two submissions — it was **one** (`prompt_id` single, `submit_calls == 1`; the template's
normal `s1`+`s2` loop). Cross-check the ratio against a previous log: if every `Prompt executed`
line pairs 1:1 with a model-staging line, no pass is unaccounted for. Apply the same rule to a
"budget: one run" constraint — an apparent second run that is really the template's second pass
is not a budget breach, and calling it one wastes a review cycle. Conversely, a single
`Prompt executed` with **two** genuine `prompt_id`s *is* a duplicate submission.

## 8. Shutdown is part of the deliverable

Stop the engine with verified-pid discipline (listener pid + epoch pid, leaf → root, one at a
time; never `taskkill /T`, never `killall`/`pkill python`), then prove: port closed,
listener list empty, VRAM back to idle, pid-set diff of `python.exe` showing
**zero collateral**, and that the manager's own processes survived.

**`connect_ex` alone is NOT proof the port is closed — it must be a BLOCKING probe.** A
non-blocking socket returns `10035` (`WSAEWOULDBLOCK`, "would block") against a *refused* or
*dead* endpoint too, so a probe that never sets blocking mode can report a closed port on a
stack that would say something else the moment it mattered. Measured 2026-09-23: the same
endpoints answered `10035` from the old helper and `10061` (`WSAECONNREFUSED`) when re-probed
blocking. Record **both** values with the reason they differ, and treat `10035` as
INCONCLUSIVE; `10061` is the proof. Never let a stale helper's number stand as the shutdown
evidence.

 If an inline stop command
is refused by a permission parser, write the logic to a file in your write-set and run the
file. A run that leaves the engine alive is an incident to report first, not a footnote.
Also: a project tool with no `argparse` **executes** when passed `--help` — read it before
invoking it, and write each round's evidence to a NEW filename so a re-run cannot clobber a
confirmed record.

## 9. Report shape

Open the report with the clip result and the errors still visible — not with test counts.
Then: candidates with exact revisions/hashes and each outcome (including
`NOT_RENDERED_SERVER_REJECTED_GRAPH` with the raw rejection text), memory configs and why,
wall/VRAM/RAM, padding + frame maps, the full gate table with per-row disposition and declared
tolerances, audio measurements, file list with sha256 + duration + frame count, and an explicit
list of what is **not** claimed.
