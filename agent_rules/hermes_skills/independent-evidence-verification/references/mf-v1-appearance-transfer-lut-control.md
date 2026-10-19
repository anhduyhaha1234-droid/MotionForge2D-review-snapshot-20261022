# MF-V1 — verifying an appearance-transfer engine with numbers only (2026-09-17)

Context: a wave had to prove it could replace a 2D animation's **appearance** (characters,
props, backgrounds) while **holding geometry** (scale, layout, silhouette, grip/touch
contact), from an MP4-only source. The LLM route had **no vision**, so every verdict had to
be numeric. Two lanes existed: `MF-V1-GOLDEN` (frozen source/annotation contract) and
`MF-V1-COMFY` (engine side). This file is the engine-side verification record.

## 1. The frozen inputs the engine consumed

| Input | Value |
|---|---|
| Reference film SHA-256 | `5A175454C2C2965BAC5013A53926E210A9F70A185D802D0F2E0083A6FB399FA2` (36,971,916 B) |
| Fixture freeze hash | `2c558ce1…fa684` (canonical JSON, `sort_keys=True`, `separators=(',',':')`, `freeze` key removed) |
| Fixture file sha256 | `7e1627e4…cd0dab` — Manager recomputed on disk, MATCH |
| Timebase | `t = frame_id / 30` exactly; `pts = frame_id * 512` exactly (timebase 1/15360) |
| Windows | 7 × 4.0 s = 28.0 s; 8 anchors each (cadence 15) → **56 keyframes**, **88 role cutouts** |
| Role-level references | `references_<tag>.json`, `references_index.json` |

Manager independently re-hashed the fixture and READ the load-bearing values out of it
(window count/duration, holdout presence, assertion flags, 39,634 decoded frames, 208/224
scene candidates matching the locked profile) before accepting "the analysis half is done".

## 2. Engine-proven baseline (before any artwork attempt)

Local ComfyUI **v0.28.2**, pinned commit `306af3a8…`, task-local server on loopback, **808**
node classes, node-inventory sha `52674207…f745`, checkpoint
`Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors` sha `c9e3e68f…8bca` (Manager measured
it independently; the lane then recomputed it itself and both matched — that is the actual
verification of a "pinned model hash").

Measured real inference: 768×768 / 20 steps / 10.719 s / peak VRAM **8,656 of 12,227 MiB**,
PNG sha `9e885a9e…cb61` recomputed MATCH. Its 68-test suite was re-run by the Manager in the
lane's own venv → `68 passed, 1 warning in 9.06s`.

## 3. The pre-registered gate and its 0/4 verdict

The lane wrote its denoise-selection rule **before** rendering (`raw/215_denoise_choice.json`)
and then held it:

| denoise | edge IoU 1/1 | edge IoU 1/8 | envelope | best_shift | edgeIoU(LUT(src),res) | edgeIoU(src,res) |
|---|---|---|---|---|---|---|
| 0.40 | 0.427 | 0.805 | 0.808–0.980 | **0.0 px** | **0.927** | 0.388 |
| 0.52 | 0.321 | 0.719 | 0.800–0.966 | **0.0 px** | 0.909 | 0.297 |
| 0.64 | 0.213 | 0.612 | 0.690–0.745 | **0.0 px** | 0.812 | 0.173 |
| 0.76 | 0.085 | 0.445 | 0.679–0.735 | 1.4 px | 0.677 | 0.041 |

12/12 renders `validated`, 64.41 s total, peak VRAM **9,078 / 12,227 MiB**.

Reading it:

1. **Layout held** — template-match best shift **0.0 px** at every denoise (peak corr
   0.51–0.93). Mask-independent, therefore the trustworthy headline number.
2. **The appearance change was a colour map.** A per-channel LUT fitted source→render
   restored edge IoU from 0.388 to **0.927**, and **92.7 %** of pixels in the frozen-mask
   region sat within ≤16/255 of the LUT prediction. The contract said palette-only is not a
   reskin ⇒ fail, correctly detected rather than papered over.
3. **Escaping the LUT cost the structure.** At 0.76 the LUT stopped explaining the output
   (0.677) but edge IoU at 1/8 fell to 0.445. The two requirements move in **opposite
   directions** under img2img denoise alone.
4. **Contact was fine.** `role_1|role_2` = 0.672–0.691 against the source's own
   **0.653** ⇒ no contact loss; three sibling pairs scored 1.000.

## 4. Two measurement defects the lane found in its own metric code

- **`WALK_7927` f7927: `source_ratio = 0.0` over 3,170 px.** The lane's derived foreground
  mask did not cover the contact band **on the source itself**, voiding `fg_iou`/envelope
  for that window while still printing a number. Fix adopted: use the **frozen mask union**
  as the metric subject (derivation-free); keep the derived value only as a labelled
  secondary with its bias stated.
- **`CAM_4212` f4212 (and f4227): pure-black source frame** (mean/std = 0, 1 unique colour).
  Every geometry metric returned 1.0/None ⇒ would have read as "geometry perfectly held".
  Fix: detect degeneracy from the **source** first, mark `degenerate_source_frame`, exclude
  from gates, report separately.

Both were surfaced by the lane unprompted, in its own report. Worth requiring in the packet:
a metric bug can fake a PASS as easily as a fail.

## 5. The coverage gap that was carried, not patched

`W05_CAM_4212` was the window chosen to demonstrate **camera motion**, and its anchors are
degenerate. Freeze discipline forbids editing the fixture, window list or tolerances once a
candidate exists — that would silently change what "correct" means. So it was recorded as an
explicit **open coverage gap** with frame ids and measurements, for the next wave.

Related honest gaps carried the same way: hands not resolvable as two distinct roles at
640×360; occlusion class `PARTIAL — NOT_DEMONSTRATED` with z-order `unresolved` (not
guessed); `mask_count != role_count` because SAM 2.1 automatic masks nest rather than
partition; between-anchor frames explicitly not interpolated.

## 6. Transferable checklist

- [ ] Pre-register the acceptance rule **before** rendering; never widen it after seeing output.
- [ ] Run the **LUT/codebook-residual control** — if a fitted colour map reconstructs the
      output's high-frequency structure, it is a grade, not a reskin.
- [ ] Chart structure vs identity-change across the tuning parameter; if they trade off
      monotonically, that is an engine-capability finding, not a tuning problem.
- [ ] Prefer **mask-independent** geometry evidence (template-match shift) as the headline.
- [ ] Decompose any low similarity score across comparison scales before calling it a defect.
- [ ] Validate every derivation against the SOURCE before using it as ground truth.
- [ ] Detect degenerate/blank frames first; exclude from gates; never count as perfect.
- [ ] Score contact against the source's own ratio, not against 1.0.
- [ ] Confirm the route has no vision **at the API boundary** before accepting text-only
      structural evidence as sufficient — and tell the user a human owns the visual gate.
- [ ] Carry frozen-input coverage defects as labelled gaps; do not re-freeze mid-comparison.
