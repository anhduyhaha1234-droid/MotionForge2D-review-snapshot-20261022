"""R6 VACE 1.3B — native reference-v2v WITH TrimVideoLatent (packet S4/T05).

Graph contract: KSampler -> TrimVideoLatent.samples ; WanVaceToVideo.output3 -> TrimVideoLatent.trim_amount ;
TrimVideoLatent -> VAEDecode. 4n+1 lengths; missing mask = FAIL (no positional fallback);
control video/masks 640x368 (pad 4/4 explicit); refs via upload API.
usage: python -B r6_vace.py --shot S0073 --beg 1 --end 81 --entity E6 [--perturb-ref <cast_png>]
"""
from __future__ import annotations
import argparse, json, shutil, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_upload as U  # noqa: E402
import r6_upload_video as UV  # noqa: E402

REC = K.R6 / "receipts/R6_VACE_RUNS.jsonl"
OUT_SUB = "identity5m_20261008/r6/vace"


def verify_ok(n):
    assert (n - 1) % 4 == 0, f"VACE length must be 4n+1, got {n}"
    return n


def stage_control_video(sid, beg, end, tag):
    a0 = K.PLAN[sid]["start_frame"]
    g0 = a0 + beg - 1
    n = end - beg + 1
    out = K.INP / "vace" / f"{sid}_{tag}_control.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    r = K.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{g0/30:.6f}", "-i", str(K.SRC),
               "-frames:v", str(n), "-vf", "pad=640:368:0:4:black",
               "-r", "30", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
    assert r[1].returncode == 0 and out.exists() and out.stat().st_size > 0, "control video stage failed"
    return UV.upload_video(out, "identity5m_20261008/r6/vace")


def stage_control_masks(sid, entity, beg, end, tag):
    """R6 masks (canonical 360) -> white-on-black PNG seq -> pad 368 -> mp4. Missing in-range mask = FAIL."""
    mdir = K.R6 / "masks" / sid / entity
    assert mdir.exists(), f"no mask dir {mdir}"
    n = end - beg + 1
    tmp = K.TMPD / f"vace_{sid}_{tag}"
    tmp.mkdir(parents=True, exist_ok=True)
    nw = 0
    for i in range(beg, end + 1):
        src = mdir / f"f_{i:04d}.png"
        if not src.exists():
            raise SystemExit(f"VACE REJECT: mask missing {sid}/{entity}/f_{i:04d} (no fallback)")
        from PIL import Image as _I0
        a = np.asarray(_I0.open(src).convert("L"))
        a = np.pad(a, ((4, 4), (0, 0)))
        from PIL import Image as _I
        m = (a > 127).astype(np.uint8) * 255
        _I.fromarray(m).save(tmp / f"{i - beg + 1:05d}.png")
        nw += int((m > 0).any())
    assert nw > 0, "all-empty masks"
    out = K.INP / "vace" / f"{sid}_{tag}_masks.mp4"
    r = K.run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", str(tmp / "%05d.png"),
               "-frames:v", str(n), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out)])
    assert r[1].returncode == 0 and out.exists() and out.stat().st_size > 0, "masks stage failed"
    return UV.upload_video(out, "identity5m_20261008/r6/vace")


def build_graph(ctrl_video, ctrl_masks, ref_png, length, seed, prompt, neg="低 quality, blurry, extra person, extra limbs"):
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.1_vace_1.3B_fp16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": prompt}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": neg}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": "Wan2_1_VAE_bf16.safetensors"}},
        "7": {"class_type": "LoadVideo", "inputs": {"file": ctrl_video}},
        "8": {"class_type": "GetVideoComponents", "inputs": {"video": ["7", 0]}},
        "9": {"class_type": "LoadVideo", "inputs": {"file": ctrl_masks}},
        "10": {"class_type": "GetVideoComponents", "inputs": {"video": ["9", 0]}},
        "16": {"class_type": "ImageToMask", "inputs": {"image": ["10", 0], "channel": "red"}},
        "11": {"class_type": "LoadImage", "inputs": {"image": ref_png}},
        "12": {"class_type": "WanVaceToVideo",
               "inputs": {"positive": ["4", 0], "negative": ["5", 0], "vae": ["6", 0],
                          "width": 640, "height": 368, "length": length, "batch_size": 1, "strength": 1.0,
                          "control_video": ["8", 0], "control_masks": ["16", 0], "reference_image": ["11", 0]}},
        "13": {"class_type": "KSampler",
               "inputs": {"model": ["2", 0], "seed": seed, "steps": 20, "cfg": 6.0,
                          "sampler_name": "uni_pc", "scheduler": "simple",
                          "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2], "denoise": 1.0}},
        "17": {"class_type": "TrimVideoLatent",
               "inputs": {"samples": ["13", 0], "trim_amount": ["12", 3]}},
        "14": {"class_type": "VAEDecode", "inputs": {"samples": ["17", 0], "vae": ["6", 0]}},
        "15": {"class_type": "SaveWEBM", "inputs": {"images": ["14", 0], "filename_prefix": f"{OUT_SUB}/trial",
                                                    "codec": "vp9", "crf": 20.0, "fps": 30.0}},
    }
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--beg", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--entity", required=True)
    ap.add_argument("--seed", type=int, default=2026101300)
    ap.add_argument("--perturb-ref", default=None, help="cast png to swap the target's ref (actual-ref perturb run)")
    args = ap.parse_args()
    n = verify_ok(args.end - args.beg + 1)
    tag = f"{args.entity}_{args.beg}_{args.end}" + ("_perturb" if args.perturb_ref else "")
    ctrl = stage_control_video(args.shot, args.beg, args.end, tag)
    ctrlm = stage_control_masks(args.shot, args.entity, args.beg, args.end, tag)
    castpng = args.perturb_ref or str(K.R4 / "assets/cast_b" / K.CASTB_OF_ENTITY[args.entity])
    ref = U.upload_image(Path(castpng), "identity5m_20261008/r6/vace")
    prompt = ("Redraw the masked person as the same character from the reference image (same face, hair, "
              "clothing colours), flat 2D cel-shaded animation style. Keep the exact same pose, motion, "
              "camera and background; keep all other people and objects unchanged. No text, no watermark.")
    t0 = time.time()
    g = build_graph(ctrl, ctrlm, ref, n, args.seed, prompt)
    gp = K.R6 / "workflows" / f"r6_vace_{args.shot}_{tag}.json"
    gp.write_text(json.dumps(g, indent=1), encoding="utf-8")
    import torch
    torch.cuda.reset_peak_memory_stats()
    r = K.post(g)
    hist = K.wait(r["prompt_id"], timeout=3600)
    outs = K.collect_outputs(hist)
    wall = round(time.time() - t0, 1)
    peak = int(torch.cuda.max_memory_allocated() / (1024 ** 2))
    rec = {"shot": args.shot, "window": [args.beg, args.end], "length_4n1": n, "entity": args.entity,
           "seed": args.seed, "perturb_ref": args.perturb_ref, "prompt_id": r["prompt_id"],
           "outputs": [str(p) for p in outs], "wall_s": wall, "peak_vram_mb": peak,
           "graph": str(gp), "trim": "TrimVideoLatent(samples=KSampler, trim=output3)",
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("shot", "window", "length_4n1", "wall_s", "peak_vram_mb", "outputs")}))


if __name__ == "__main__":
    main()
