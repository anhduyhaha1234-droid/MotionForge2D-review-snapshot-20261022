# Conditioning windows, submit counting, and the audit that caught a silent 1/6 config

Session evidence, 2026-09-23 (MotionForge `mf-core-tool-delivery-20260923` wave A/B, RTX 5070 12 GB).
Everything below is measured, not inferred; the point is the *check*, not these particular numbers.

## 1. The defect: a pose-conditioning window that silently disabled 5/6 of the sampler

Node `672:587` `WanAnimate2ToVideo` in the **submitted** graph carried:

```json
{"pose_strength":1, "pose_start_percent":0, "pose_end_percent":0, "reference_image_strength":1}
```

The official template in the same pinned commit carries `pose_start_percent 0`, `pose_end_percent 1`.

An independent CPU probe (AST-extract the real runtime functions `ModelSamplingDiscreteFlow`,
`simple_scheduler`, `get_area_and_mult`; no weights, no server) selected the steps that actually
receive the pose branch:

| window | steps conditioned | sigmas |
|---|---|---|
| submitted `0..0` | **1 / 6** | 1.0 |
| template `0..1` | **6 / 6** | 1.0, 0.961716, 0.909215, 0.833333, 0.714897, 0.500600 |

Runtime source that settles it: `comfy_extras/nodes_wan.py` (default `end=1`; the pose condition is
built only inside the window) and `comfy/ldm/wan/model_animate2.py` `apply_pose = pose_latents is
not None` — outside the window the branch is absent, so the cache cannot carry it forward.

Why it survived a careless gate: the clip **rendered**. Right frame count, right geometry, right
duration, real motion in the pixels — just not the source's motion. Only a graph-vs-template diff or
a step-level probe exposes it.

### How to check it on any template

1. Read the widget order for the node class from the **live** `/object_info`
   (`width, height, length, batch_size, video_frame_offset, pose_strength, pose_start_percent,
   pose_end_percent, reference_image_strength` for this class) — a UI template stores widget values
   as a **positional array**, so mapping by eye is how `0/0` gets mistaken for a default.
2. Diff your exported API graph against the official template **in the pinned commit**,
   structurally: walk both JSON trees and enumerate differences. A correct single-variable
   experiment produces **exactly one** difference; report that count, don't assert it.
3. Run the CPU probe before spending GPU time: extract the sampler/scheduler functions from the
   installed runtime and count steps per window. Cheap, deterministic, no weights.

## 2. Submit counting: two passes and two files were ONE submission

A BOOK 4 s Animate-2 run printed:

- two 6/6 sampling passes in one prompt (`Model Initializing … complete` 25.82 s → pass 1
  `6/6 = 1:11 @ 11.86 s/it`; pass 2 `6/6 = 0:33 @ 5.52 s/it`, the `s1`+`s2` loop the template does);
- two `.mp4` outputs: `…_00005_.mp4` (117,027 B, **640×368** single view = the candidate) and
  `…_00006_.mp4` (147,901 B, **1280×368** two-up composite = not a candidate);
- **one** `prompt_id`, `submit_calls == 1`, `status_str = success`, Δ execution 162.139 s.

Cross-check that removes the ambiguity: in a previous log every `Prompt executed` line pairs 1:1
with a model-staging line, so no pass is unaccounted for. Rule: count `prompt_id`s in the server
history, not progress bars and not output files. (The mirror-image trap is real too: one
`Prompt executed` carrying two `prompt_id`s IS a duplicate submission.)

## 3. Export contract actually delivered (what a correct clip looks like)

Raw render ≠ deliverable. The raw output was 121 frames at 640×368 with **no audio**; the exported
clip was:

| property | value |
|---|---|
| sha256 | `5C2175AE73056EA6552B7B50432F618F7255A09F7CF9E5C695A870FE22286A6D` |
| bytes | 1,071,337 |
| video | h264, **640×360**, **120** frames, `r_frame_rate 30/1`, `time_base 1/15360`, PTS 0…60928 step 512 |
| container | 4.001995 s (video 4.000000 s; see the AAC-tail arithmetic in the main skill) |
| audio | aac 44100 2ch, first 4.000 s **bit-exact** vs the source window `[55.000, 59.000)` |

Manager re-verification that reproduced it end-to-end:

```
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,nb_frames,r_frame_rate,time_base \
  -show_entries format=duration -of default=noprint_wrappers=1 <clip>
# audio like-for-like: decode BOTH sides, same length, then hash
ffmpeg -v error -y -i <clip> -map 0:a -t 4.000 -f s16le -acodec pcm_s16le -ar 44100 -ac 2 clip.pcm
ffmpeg -v error -y -ss 55.000 -t 4.000 -i <film> -map 0:a -f s16le -acodec pcm_s16le -ar 44100 -ac 2 film.pcm
sha256sum clip.pcm film.pcm   # both must be 2387eded24366afefdcf16cea122f4cc85366d0be086652fea8ee4e041129292
```

**The temp directory matters on Windows:** run these with the outputs under
`C:/Users/<user>/AppData/Local/Temp/…`. A `$(mktemp -d)` path (`/tmp/tmp.XXXX/…`) is bash-native
and `ffmpeg.exe` fails on it with `Error opening output …: No such file or directory` even though
the directory exists.

## 4. Evidence-integration lessons from the same rounds

- A worker reported its export clip at a path that did **not** exist; the file was real but sat
  under a **nested `NEW`** directory inside the evidence root. Locate claimed artifacts by name
  glob **plus** the claimed hash, quote the real path, and flag the layout defect — do not move
  hashed bytes to tidy it.
- A worker's "adapter canonical hash" (`97045d0f…`) did not reproduce from sorted-key JSON
  (`d33bb57b…`), so it was unverifiable. Keep only digests a reviewer can recompute with stdlib
  (raw bytes / LF-normalised / `sort_keys=True,separators=(",",":")`) and label which one it is.
- Shutdown evidence: `connect_ex` returning `10035` (`WSAEWOULDBLOCK`) proves nothing about a closed
  port — that is a non-blocking-socket artefact. Re-probe **blocking** and require `10061`
  (`WSAECONNREFUSED`); record both values and why they differ.
