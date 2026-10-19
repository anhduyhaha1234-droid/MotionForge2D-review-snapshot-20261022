"""R6g blend review sheets — r6_qa-style rows (9 shots/sheet, 3 tiles per shot)."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
from PIL import Image, ImageDraw, ImageFont

NS = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))


def main():
    outd = NS / "evidence/blend_reviews"
    outd.mkdir(parents=True, exist_ok=True)
    for old in outd.glob("blend_sheet_*.png"):
        old.unlink()
    ev_map = json.loads((K.R6 / "event_map.json").read_text(encoding="utf-8")).get("shots", {})
    plan = {c["unit_id"]: c for c in json.loads((K.D / "chunk_plan.json").read_text(encoding="utf-8"))["chunks"]}
    shots = [s for s in K.SHOTS if s in plan]
    try:
        F = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 11)
    except Exception:
        F = ImageFont.load_default()
    tw, th = 300, 169
    for bi in range(0, len(shots), 9):
        chunk = shots[bi:bi + 9]
        c = Image.new("RGB", (3 * (tw + 6) + 8, len(chunk) * (th + 20) + 8), (10, 10, 10))
        d = ImageDraw.Draw(c)
        for j, sid in enumerate(chunk):
            man = json.loads((K.R6 / "work" / sid / "blend_manifest.json").read_text(encoding="utf-8"))
            bd = Path(man["blend_dir"])
            frames = man["frames"]
            m = len(frames)
            evs = (ev_map.get(sid) or {})
            evl = (evs.get("events") or []) + (evs.get("contacts") or [])
            ef = None
            if evl:
                e0 = evl[0]
                ef = (int(e0.get("f", 0)) + 1) if "f" in e0 else (int(e0.get("from", 0)) + 1)
            picks = [1, ef or (m // 2), m]
            for k, fid in enumerate(picks):
                idx = min(m, max(1, int(fid)))
                p = bd / frames[idx - 1]["name"]
                im = Image.open(p).convert("RGB")
                x = 4 + k * (tw + 6)
                y = 4 + j * (th + 20)
                d.text((x, y), f"{sid} " + ("head" if k == 0 else ("event" if k == 1 else "tail")) + f" f{idx}",
                       fill=(255, 220, 80), font=F)
                c.paste(im.resize((tw, th)), (x, y + 15))
        out = outd / f"blend_sheet_{bi//9+1:02d}.png"
        c.save(out)
        print("saved", out.name, len(chunk))
    print("done", len(shots))


if __name__ == "__main__":
    main()
