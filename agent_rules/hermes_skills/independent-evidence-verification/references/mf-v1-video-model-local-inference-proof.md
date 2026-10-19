# Verifying a local video-model inference claim (MF-V1 VIDEO14B wave 2, 2026-09-22)

Companion detail for §25. The lane under review had to prove that a **published** video model,
driven through a pinned local ComfyUI runtime, actually produced a 4-second clip on an RTX 5070
with 12,227 MiB — no hand-written renderer anywhere in the path. This is what the manager checked,
and what each check caught.

## Layout

| Thing | Path |
|---|---|
| Task worktree | `ROOT/wt-video14b` (branch `codex/mf-reskin-v1-video14b`, HEAD unchanged at the wave base; the work was untracked `experiments/`) |
| Task-local runtime | `ROOT/runtime/video14b` — pin file `RUNTIME_PIN.json`, epoch `instance_epoch.json`, engine `ComfyUI` @ `v0.37.0`, port **8210** |
| Engine log | `ROOT/runtime/video14b/logs/server_gpu.log` |
| Evidence root | `NEW_EV/VIDEO14B/` → `wave2/{api,raw,runs}` |
| Frozen adapter (other task, read-only) | `ROOT/wt-comfy/.../mf_comfy` at commit `cc3222b1bed6680480ab6d63fb869b02d749259b`, interface frozen in `NEW_EV/COMFY/HANDOFF.md` |

Rule that made the reuse auditable: the adapter is imported from the **other** task's frozen commit
and pointed at this task's engine/epoch/lease/port, so there is exactly one adapter in the project
and the video lane's runs are attributable to a reviewed interface rather than a fresh one.

## Candidate 1 (Wan-Animate-2) — rejected by the server, four attempts

The released template is **UI format** (carries `nodes`, `links`, `definitions.subgraphs`); `POST
/prompt` needs **API format**. The pinned backend has no converter — the lane measured it:

```
grep -rn "graph_to_prompt\|graphToPrompt\|workflow_to_prompt" --include=*.py .   → no hits
```

so conversion is a frontend job (the shipped `comfyui_frontend_package` bundle does carry
`graphToPrompt`), and the Animate2 template's subgraph instance (`Motion Transfer (Wan Animate 2)`,
instance id `672`, 48 internal nodes) is what has to be flattened. Signature of a partial flatten:
node ids in the converted graph look like **`parent:child`** (`672:648`).

| Attempt | Server response | Wall |
|---|---|---|
| `1A` | `[MF_COMFY_INVALID_GRAPH] node is missing a required input` — `required_input_missing` on `672:648` (class `CreateList`, `inputs.input0`), plus several `ComfyMathExpression` nodes | 0.338 s |
| `r2` | identical | 0.290 s |
| `r3` | still `required_input_missing` (lane had produced `api.fixed.json`) | — |
| `r4` | **error moved**: `prompt_outputs_failed_validation` for output `246` | 0.508 s |

Interpretation used for the verdict: the converted graph *looked* healthy (64 API nodes / 33
classes, `missing_classes: []`, `WanAnimate2ToVideo` present, `LoadVideo` = driving clip,
`LoadImage` = anchor) yet the **subgraph internals never resolved**, and the error type moving
across attempts means the lane was converging rather than guessing. All four payloads were kept as
the candidate's capability result — not deleted, not retried forever.

## Candidate 2 (VACE 14B, pre-authorised fallback) — converted cleanly, then ran

Preflight on the flat template (`mf_vace14b_book4s.api.json`): **15 API nodes / 14 classes**,
`missing_classes: []`, `excluded_weight_hits: []`, with `LoadVideo` id 145, `LoadImage` id 134,
`WanVaceToVideo` id 49, `SaveVideo` id 114. Loaded weights named in the assert: `wan2.1_vace_14B_fp16`,
`wan_2.1_vae`, `umt5_xxl_fp16`.

**Reference anchor (FLUX.2 klein 4B) first, then unload — the image model nearly filled the card:**

| Field | Value |
|---|---|
| status | `validated` (only success signal; `generated` alone is not) |
| timing | preflight 0.265 s / submit 0.015 s / wait 10.172 s / validate 0.062 s / total **10.578 s** |
| peak VRAM | **11,590 / 12,227 MiB (94.8 %)** · peak RAM 22,727 / 65,325 MiB |
| artifact | PNG sha256 `06171d1d…`, staged under the stage root |

**Then the video run — the real proof:**

| Evidence | Value |
|---|---|
| Engine boot | `127.0.0.1:8210`, PID 30060, `READY_ROUND=3 elapsed~15s` |
| CUDA probe | `torch 2.14.0+cu130`, `cuda 13.0`, arch list contains **`sm_120`**, capability `[12, 0]`, total 12,226 MiB |
| Model load line | `Model WAN21_Vace prepared for dynamic VRAM loading. 33068MB Staged` |
| Sampling | 20 steps at a steady **56.5 s/it** → ~19 min; observed 9/20 → 14/20 during the check |
| VRAM during run | **9,176 – 9,264 MiB / 12,227 MiB**, util **100 %** |
| Holder RSS | PID 30060 at `30,357,600 K` ≈ 30 GB (staged weights offloading through host RAM) |
| GPU probe artifact | `wave2/raw/gpu_probe_wave2.txt`, `wave2/raw/vram_baseline.txt` (`1982, 12227, 0` idle) |

## The verification commands actually run (manager side)

```bash
# liveness + progress of a carriage-return tqdm log
tail -c 300 ROOT/runtime/video14b/logs/server_gpu.log | tr '\r' '\n' | tail -3
stat -c "%y %s bytes" ROOT/runtime/video14b/logs/server_gpu.log; date +"now: %F %T"

# independent counters, same moment
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
tasklist /FI "IMAGENAME eq python.exe" /FO CSV

# is anyone listening yet
netstat -ano | grep LISTENING | grep -E ":8210\b"

# adapter receipts, read as fields
python -c "import json;d=json.load(open('…/runs/anchor_a1/adapter_stage_output.json'));print(d['status'],d['timing'],d['resources'])"
cat …/wave2/raw/api_assert_animate2.json     # the converted-graph asserts
```

## Caveats worth carrying into the next round

- **`nvidia-smi --query-compute-apps` shows every desktop process** (`dwm.exe`, `explorer.exe`,
  browser helpers) with `[N/A]` memory on Windows — it is not a per-process VRAM breakdown. Use
  `memory.used` totals plus the holder's RSS instead of trying to attribute VRAM by PID.
- **A foreground shell `sleep 240` inside one terminal call died at the tool's 180 s cap**
  (`[Command timed out after 180s]`, exit 124) — pass an explicit `timeout=` for any wait, or poll
  in shorter slices. Same cap that makes a `du -sh` over a tens-of-GB model tree hang (§22).
- **The worker's own stdout log for an agent CLI can stay 0 bytes for minutes** (§20) while the
  *engine* log is the informative one — two different logs, do not conflate them.
- The 4 s target window is 120 frames at 30 fps (`pts = frame_id * 512`, timebase `1/15360`); the
  lane's native-length padding plan was internal 121 frames → `ImageFromBatch` cut back to exactly
  120. **Duration/frame count being right is not evidence the animation is right** — the technical
  gate (frames / PTS / CFR / audio) and a human's visual review are separate rows, and a text-only
  route can only ever sign the first.
