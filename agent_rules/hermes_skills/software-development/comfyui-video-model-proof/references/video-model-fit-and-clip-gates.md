# Measured fit + clip-gate tables (VACE 14B / Wan-Animate-2, RTX 5070 12 GB)

Session detail behind the rules in SKILL.md. Host: Windows, RTX 5070 **12,227 MiB**, 65,325 MiB
RAM, ComfyUI **v0.37.0** (`73c9bad4…`) task-local on `127.0.0.1:8210`, torch **2.14.0+cu130**,
CUDA 13.0, arch list `[sm_75, sm_80, sm_86, sm_90, sm_100, sm_120]`, driver 610.47. Task-local
venv only — global torch (2.11.0+cu128) untouched.

## 1. Tile the work: what ran, what refused

| Step | Outcome |
|---|---|
| CUDA probe | `available True`, capability `(12,0)`, `sm_120` present, total 12,226 MiB |
| Engine boot | ready in ~15 s, VRAM baseline 1,970–1,982 MiB |
| UI→API conversion (`graphToPrompt`) | Animate2 template → **64 nodes / 33 classes**, `missing_classes: []`; VACE template → **15 nodes / 14 classes**, `missing_classes: []`, `excluded_weight_hits: []` |
| Anchor image (FLUX.2 klein 4B edit) | `validated` in **10.578 s** (preflight 0.265 / submit 0.015 / wait 10.172 / validate 0.062), **peak VRAM 11,590 / 12,227 MiB**, peak RAM 22,727 MiB, 864 KB PNG |
| **C1 Wan-Animate-2 14B int8** | **NOT RENDERED** — 4 `/prompt` rejections (0.34 / 0.29 / 0.36 / 0.51 s) |
| **C2 Wan-Animate…VACE 14B fp16** | **RENDERED** — `prompt_id … = success`, wall **1,170.705 s** |

## 2. Why C1 refused (the autogrow signatures)

```
"[MF_COMFY_INVALID_GRAPH] node is missing a required input"
  node 672:648  class CreateList           errors[0].type=required_input_missing details=input0
  node 672:636  class ComfyMathExpression  missing 'values'
→ later: required_input_missing … input_name: "values.a"
→ final attempt: prompt_outputs_failed_validation
```
Top-level classes all resolved (`missing_classes == []`), only **subgraph-internal** ids
(`672:*`) failed. Cause: the frontend emits autogrow in dotted form; reshaping to dict/list
breaks the contract. Fix: pass the frontend payload through verbatim (the retry after that is
the correction, not more reshaping). Keep the raw `node_errors` blob, the wall time and the
graph sha of each rejected attempt — those are results, not noise.

## 3. Fit numbers for a 14B video model on 12 GB

```
[INFO] Model WAN21_Vace prepared for dynamic VRAM loading. 33068MB Staged.
  5%|▌         | 1/20  [00:59<18:41, 59.03s/it]
 70%|███████   | 14/20 [13:13<05:39, 56.53s/it]      ← stable, no drift
[INFO] Prompt executed in 00:19:29
```
* peak VRAM during sampling ≈ **9,176–9,264 MiB / 12,227**; GPU util 100 %;
  server process RSS ≈ **30.7 GB** (the offload side).
* 20 steps × ~56.5 s/it → **1,170 s for 121 frames @ 640×368** ⇒ **≈ 293 s render per second
  of video** (≈ 4.9 min per 1 s). Budget multi-second extensions from this shape, not from
  vendor numbers.
* A 4B image model peaked at **11,590 MiB** — near the ceiling. Stage image first, unload,
  then video; never both.

## 4. Clip gate table (final clip: 120 f / 30·1 / tb 1/15360 / 640×368, 4.000000 s)

Counts: **11 PASS / 3 FAIL / 3 UNMEASURED / 7 NOT_REVIEWED** (24 rows).

| Row | Measured | Verdict |
|---|---|---|
| codec / nb_frames / r_frame_rate / time_base / duration | h264, 120, 30/1, 1/15360, 4.000000 | PASS |
| dimensions | 640×368 vs **source 640×360** | was scored PASS against itself — must be compared to source |
| `pts.contract` | first pts **80471** (≠0), 12/120 mismatch vs `frame_id*512` | FAIL (keep) |
| `pts.cfr` | deltas `{512, 1024}` | FAIL (keep) |
| `pts.last_frame` | 141911 vs expected 60928 | FAIL (keep) |
| audio | **398 AAC packets = 9.241542 s**, start_time 0.0, 44100 / 2ch | window wrong; container 9.24 s for a 4 s clip |
| frame-identity MAE (out0↔src1650, out1↔src1651, outLast↔src1769) | extractor returned `None` | UNMEASURED — must become numbers |
| semantic (chars/hands/book/background/second person/silhouette-grip) | not viewed | NOT_REVIEWED (no vision on the LLM route) |

Delivery: raw render **121 f / 4.033333 s** kept beside the export **120 f / 4.000000 s**
(padding = hold last frame; export with `-frames:v 120 -c:v copy`), each with its own
`.sha256` file. The source film is 640×360 / 30 fps; the BOOK window is film frames
`[1650, 1770)`, i.e. audio `[55.000 s, 59.000 s)`.

## 5. Adapter integration note

Importing a frozen adapter read-only from another task's worktree worked, but a config
allowlist (`allowed_types=("output",)`) that is stricter than the real history entry produced
`MF_COMFY_ARTIFACT_MISSING: artifact type is not publishable` and aborted validation — the
clip bytes had to be taken from `output/` after reconciling against a `success` history entry.
Verify the adapter's allowed-types/kind list against a real history entry **before** the long
run, not after.
