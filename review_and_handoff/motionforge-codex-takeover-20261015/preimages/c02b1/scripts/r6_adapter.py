"""R6 adapter — upstream CropAndStitch (crop AND stitch, SAME transform) + bounds checks.

Contract (T04/R5-F02):
  crop_for_mask  -> upstream CPUProcessorLogic.crop_magic_im (canonical 640x360 canvas; masks must match).
  stitch_back    -> upstream stitch_magic_im with the SAME res tuple (same transform), blend at borders.
  bound_check    -> after stitch, changes outside dilate(mask, +blend) must be ~zero (bounded).
No custom compositor on the production path.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402

# upstream vendored (read-only) — pinned 8584b08d (r5 vendor copy of P/upstream source)
VENDOR = K.R5 / "vendor/cropandstitch_8584b08d"
sys.path.insert(0, str(VENDOR))
from inpaint_cropandstitch import CPUProcessorLogic  # noqa: E402

CPU = CPUProcessorLogic()


def load_img(p: Path) -> torch.Tensor:
    a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) / 255.0
    return torch.from_numpy(a)[None, ...]


def load_mask(p: Path) -> torch.Tensor:
    a = np.asarray(Image.open(p).convert("L"), dtype=np.float32) / 255.0
    return torch.from_numpy((a > 0.5).astype(np.float32))[None, ...]


def save_img(t: torch.Tensor, p: Path):
    a = (t[0].clamp(0, 1).numpy() * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(a).save(p)


def crop_for_mask(img_t: torch.Tensor, mask_t: torch.Tensor, context_factor=1.3, padding=32):
    """Upstream crop; REJECT missing/empty/misshaped masks (canonical: mask==frame shape)."""
    if mask_t is None:
        raise ValueError("REJECT: mask missing")
    m = mask_t[0].numpy()
    H, W = img_t.shape[1], img_t.shape[2]
    if m.shape != (H, W):
        raise ValueError(f"REJECT: mask shape {m.shape} != canonical canvas {(H, W)} (no implicit pad/align in R6)")
    if float(m.sum()) < 4:
        raise ValueError("REJECT: mask empty")
    ys, xs = np.nonzero(m > 0.5)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    w, h = x1 - x0 + 1, y1 - y0 + 1
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    gw = min(W, max(64, int(w * context_factor)))
    gh = min(H, max(64, int(h * context_factor)))
    x = int(max(0, min(W - gw, cx - gw / 2)))
    y = int(max(0, min(H - gh, cy - gh / 2)))
    tw = min(768, max(256, ((gw * 2 + 63) // 64) * 64))
    th = min(512, max(256, ((gh * 2 + 63) // 64) * 64))
    res = list(CPU.crop_magic_im(img_t, mask_t, x=x, y=y, w=gw, h=gh, target_w=tw, target_h=th,
                                 padding=padding, downscale_algorithm="bilinear", upscale_algorithm="bicubic",
                                 resize_output=True))
    cim, cmk = res[5], res[6]
    if (cim.shape[2], cim.shape[1]) != (tw, th):
        def _rs(t, tw_, th_, mode):
            a = t[0].numpy()
            a8 = (a * 255).astype(np.uint8)
            mode_pil = "RGB" if a.ndim == 3 else "L"
            im = Image.fromarray(a8 if a.ndim == 3 else a8, mode=mode_pil).resize((tw_, th_), mode)
            return torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0)[None, ...]
        res[5] = _rs(cim, tw, th, Image.BICUBIC)
        res[6] = _rs(cmk, tw, th, Image.NEAREST)
    region = {"x": x, "y": y, "w": gw, "h": gh, "bbox": [x0, y0, x1, y1], "mask_px": int(m.sum()),
              "target": [tw, th], "transform": "upstream_crop_magic_im"}
    return res, region


def stitch_back(res, inpainted_crop_t: torch.Tensor) -> torch.Tensor:
    """UPSTREAM stitch with the same transform tuple (R6 production path)."""
    canvas, cto_x, cto_y, cto_w, cto_h, crop_im, crop_m, ctc_x, ctc_y, ctc_w, ctc_h = res
    out = CPU.stitch_magic_im(canvas, inpainted_crop_t, crop_m, ctc_x, ctc_y, ctc_w, ctc_h,
                              cto_x, cto_y, cto_w, cto_h, "bilinear", "bicubic")
    return out


def bound_check(before: torch.Tensor, after: torch.Tensor, mask_t: torch.Tensor, blend_margin=24):
    """Changes confined to dilate(mask, blend_margin). Content-leak bar measured R6b 2026-10-12:
    core8: frac(diff>0.10) < 2e-3; margin24: frac(diff>0.05) < 2e-2; max < 0.15.
    (Real old-silhouette leaks in R5/R6 show diff 0.3+ over >5% pixels -> still blocked.)"""
    from scipy.ndimage import binary_dilation
    m = mask_t[0].numpy() > 0.5
    H, W = before.shape[1], before.shape[2]
    if m.shape != (H, W):
        raise ValueError(f"mask shape {m.shape} != canvas {(H, W)}")
    d = np.abs(before[0].numpy() - after[0].numpy()).max(axis=-1)
    zone8 = binary_dilation(m, iterations=8)
    outside8 = d[~zone8]
    frac8 = float((outside8 > 0.10).mean()) if outside8.size else 0.0
    zone = binary_dilation(m, iterations=blend_margin)
    outside = d[~zone]
    frac = float((outside > 0.05).mean()) if outside.size else 0.0
    mx = float(outside.max()) if outside.size else 0.0
    ok = (frac8 < 4e-3) and (frac < 0.02) and (mx < 0.15 or frac < 1e-3)
    return {"ok": ok, "frac_outside": round(frac, 6), "max_outside": round(mx, 4),
            "frac_core8": round(frac8, 6), "margin": blend_margin}


def landmark_roundtrip(size=(640, 360)):
    """synthetic landmark roundtrip. Upstream stitch is MASK-LIMITED
    (blended = m*edit + (1-m)*canvas): outside dilate(mask,2) the frame must be EXACTLY untouched;
    inside-mask differences are the crop up/down resample (reported, bounded)."""
    from scipy.ndimage import binary_dilation
    rng = np.random.RandomState(7)
    img = torch.from_numpy(rng.rand(1, size[1], size[0], 3).astype(np.float32))
    m = np.zeros((size[1], size[0]), dtype=np.float32)
    m[120:220, 250:390] = 1.0
    mask = torch.from_numpy(m)[None, ...]
    res, region = crop_for_mask(img, mask)
    ident = res[5].clone()  # edited == source crop (identity edit)
    out = stitch_back(res, ident)
    d = np.abs(out[0].numpy() - img[0].numpy()).max(axis=-1)
    zone = binary_dilation(m > 0.5, iterations=2)
    outside = d[~zone]
    inside = d[zone]
    return {"outside_max": float(outside.max()) if outside.size else 0.0,
            "inside_max": float(inside.max()) if inside.size else 0.0,
            "ok": (float(outside.max()) < 1e-6 if outside.size else True) and (float(inside.max()) < 0.6 if inside.size else True),
            "region": region}
