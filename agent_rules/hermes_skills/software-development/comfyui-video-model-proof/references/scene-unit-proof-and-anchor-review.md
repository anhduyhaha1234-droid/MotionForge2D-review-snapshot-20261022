# Scene-unit proof pass P0/P1 + target-anchor review (measured 2026-09-27, RTX 5070 / ComfyUI 0.37)

Context: before writing any product code for a "reskin an existing MP4 with a real model"
delivery, a proof pass established (P0) the runtime's real capabilities and (P1) the scene-unit
manifests, then generated one target anchor per stress shot (P2) on GPU. Everything below is
measured on the pinned runtime, not predicted.

## P0 recipe (CPU-only, ~30 min, zero GPU)

1. Task-local dirs: `proof/{graphs,tools,inputs,output,temp,user,evidence}`; launch the pinned
   ComfyUI source (read-only) with
   `python -u main.py --port <dedicated> --listen 127.0.0.1 --disable-auto-launch --cpu
   --input-directory <proof>/inputs --output-directory <proof>/output --temp-directory <proof>/temp
   --user-directory <proof>/user --cache-none`.
2. Capture: cmdline, pid, port, `instance_epoch` (instance_id + launched_at), `/system_stats`,
   full `/object_info` dump. Measured: **960 nodes, 1,857,638 B, sha256 `80850af2…`** — the count
   + bytes + sha is the receipt that makes later "node X exists" claims checkable.
3. Fill the 5-column matrix (source-present | imported | weights-present | inference-tested |
   quality-accepted). What the CPU pass CANNOT fill: `inference-tested` (stays NOT YET RUN) and
   `quality-accepted` (False). Never infer across columns.
4. Model-roots inventory: per group (diffusion_models/loras/vae/text_encoders/clip_vision/
   sam3/sam2/checkpoints) list real files (path/size/sha16). Missing groups are the honest
   blocker list. Measured: 12 files / 88.7 GB; **sam3, sam2, checkpoints absent**.
5. Node-interface extraction from `/object_info` (NOT from `nodes_*.py`): required inputs per
   node, e.g. `WanAnimate2ToVideo` = positive/negative/vae/width/height/length/batch_size/
   `video_frame_offset`/`pose_strength`/`pose_start_percent`/`pose_end_percent`/
   `reference_image_strength`; `WanSCAILToVideo` = …/`previous_frame_count`;
   `SCAIL2ColoredMask` = `driving_track_data`/`object_indices`/`sort_by`/`replacement_mode`.
6. Shutdown proof: port_listening False + pid_exists False + epoch match → POST_STOP_VERIFIED.

## P1 scene-unit manifests

Per shot: unit_id, source span `[start,end)` + rational fps + PTS map, camera/framing,
cast/version hashes, `elements[]` (role_id, kind, source track/bbox, visibility, frame spans),
`interactions[]`, `assets[]` (staged copies WITH hashes — copy into `proof/inputs/`, never
move/modify the source), `execution{}` (mark PLACEHOLDER fields `measured_here: false`), and
`acceptance{}` hard events. Include partial/edge roles explicitly (measured example: a
12×53-px partial person at the right frame edge `[628,254,639,306]` present in every frame).
Record source-event indices with frames AND seconds (measured: "open_two_pages" first appears at
frame **72 / 2.4 s**, must not be shown at frame 0).

## Target-anchor (P2) review checklist — LOOK at the pixels

A manager/reviewer must open each generated anchor AND the matching source frame with native
vision (not a hash, not the worker's prose), then check:

* **Role coverage** — every declared element present, incl. the partial edge person; nobody
  merged/duplicated; holder identity and prop STATE match the event map at that frame
  (measured: book CLOSED at f000 because the open state starts at index 72).
* **Pad-to-multiple of 8/16.** Measured: anchors came back **640×368 for a 640×360 source**
  (+8 rows of latent padding). The pipeline MUST declare the crop/pad policy and trim back to
  the source geometry before assembly/timeline; an undeclared +8 px silently breaks scale/PTS
  maps. This is the single most likely silent defect in image-anchor pipelines.
* **Watermark/overlay policy must be DECLARED.** Source frames carried a channel watermark
  (logo + handle). The anchors dropped it — defensible, but it must be written as an explicit
  policy decision, never left as an unexplained difference.
* **Content vs appearance.** For document/certificate shots the anchor kept the source TEXT
  (content) while restyling the hand holding the pen (appearance). Record that split as policy:
  text on a prop is content; the hand/paper/scene is appearance.
* **Metadata recorded per artifact**: size, PIL mode (measured RGB), sha256, generating graph
  + params (seed/steps/guidance), prompt_id, wall time, VRAM peak sample.

## Anti-patterns seen and how they were caught

* Research doc said a node/template exists; the live server had it unregistered → the anchor
  graph was rebuilt from the graph shape that had already RUN on this exact commit. Caught by
  P0 step 5 diffing class_types against `/object_info`.
* Worker searched for the research document on the host and could not find it (it lived in the
  packet root, not on the host) → put the ABSOLUTE path of every authority doc in the packet;
  workers cannot be assumed to have your host's file layout.
* Pixel-diff counts between two independent preview implementations differed while max-delta
  matched (11,856 vs 10,545 px; max Δ 69/41/27 identical) → the counting rule must be declared
  and the worker must say "max deltas match, counts differ, here is my counting rule" instead of
  claiming equality.
