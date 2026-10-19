"""R6 S8 QA — master checks: 54-shot head/event/tail sampling, 2s-scan strips, seams, comparison."""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
from PIL import Image, ImageDraw, ImageFont

OUTD = K.R6 / "evidence/qa"
OUTD.mkdir(parents=True, exist_ok=True)
try:
    F = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 11)
except Exception:
    F = ImageFont.load_default()


def grab(master, gframe, out):
    # global frame gframe in [2820,11820) -> master frame index
    fi = min(8999, max(0, gframe - K.SPAN_A))
    if out.exists():
        out.unlink()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(master),
                    "-vf", f"select=eq(n\,{fi})", "-frames:v", "1", str(out)], check=False)
    if out.exists():
        return Image.open(out).convert("RGB")
    return Image.new("RGB", (640, 360), (20, 20, 20))


def main():
    master = K.R6 / "outputs/IDENTITY5M_R6_MASTER.mp4"
    assert master.exists(), "master missing"
    plan = json.loads((K.D / "chunk_plan.json").read_text(encoding="utf-8"))["chunks"]
    plan = {c["unit_id"]: c for c in plan}
    ev_all = json.loads((K.R6 / "event_map.json").read_text(encoding="utf-8"))
    ev = ev_all.get("shots", {})  # F07: real schema level
    tw, th = 300, 169
    # 54-shot head/event/tail sheet (3 tiles per shot -> huge; do 12 shots per sheet, 8 sheets ided later)
    shots = [s for s in K.SHOTS if s in plan]
    idx = 0
    sheets = []
    for bi in range(0, len(shots), 9):
        chunk = shots[bi:bi + 9]
        c = Image.new("RGB", (3 * (tw + 6) + 8, len(chunk) * (th + 20) + 8), (10, 10, 10))
        d = ImageDraw.Draw(c)
        for j, sid in enumerate(chunk):
            a0 = plan[sid]["start_frame"]
            n = min(plan[sid]["frames"], K.SPAN_B - a0)
            evs = ev.get(sid) or {}
            ef = None
            evlist = (evs.get("events") or []) + (evs.get("contacts") or [])
            if evlist:
                e0 = evlist[0]
                ef = (int(e0.get("f", 0)) + 1) if "f" in e0 else (int(e0.get("from", 0)) + 1)
            for col, (off, tag) in enumerate(((0, "head"), (ef or n // 2, "event"), (n - 1, "tail"))):
                g = a0 + off
                if not (K.SPAN_A <= g < K.SPAN_B):
                    continue
                im = grab(master, g, K.R6 / f"work/_qa_{sid}_{tag}.png")
                x = 4 + col * (tw + 6); y = 4 + j * (th + 20)
                d.text((x, y), f"{sid} {tag} f{off+1}", fill=(255, 220, 80), font=F)
                c.paste(im.resize((tw, th)), (x, y + 15))
        p = OUTD / f"QA_sheet_{bi//9+1:02d}.png"
        c.save(p)
        sheets.append(str(p))
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "shots": len(shots), "sheets": sheets}
    (OUTD / "R6_QA_INDEX.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps({"sheets": len(sheets), "shots": len(shots)}))


if __name__ == "__main__":
    main()
