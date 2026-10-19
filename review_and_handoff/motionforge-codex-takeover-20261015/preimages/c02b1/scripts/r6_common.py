"""R6 common — paths, canonical canvas contract, CAST B binding, frame map.

CANONICAL CONTRACT (R6):
  - source canvas 640x360; padded canvas 640x368 = pad top4/bottom4 applied ONCE, inverse explicit.
  - frame map: shot f0001 = source global frame a0 (NO 1-frame shift); gframe = a0 + fid - 1.
  - every image/mask in one pipeline shares shape/time; masks 640x360 canonical.
Paths: ALL outputs under R6/C or INPUT-root r6. R4/R5 strictly read-only.
"""
from __future__ import annotations
import hashlib, json, subprocess, time
from pathlib import Path

R6 = Path(__file__).resolve().parents[1]
C = R6.parent
D = C.parents[1]
SRC = D / "source/source_full.mp4"
PLAN = {c["unit_id"]: c for c in json.loads((D / "chunk_plan.json").read_text(encoding="utf-8"))["chunks"]}
SHOTS = sorted(s for s in PLAN if "S0021" <= s <= "S0074")
FPS = 30.0
SPAN_A, SPAN_B = 2820, 11820
AUDIO_SS, AUDIO_T = 94, 300.0

INP_ROOT = D / "input"
INP = INP_ROOT / "identity5m_20261008/r6"
OUTPUT = D / "output/identity5m_20261008/r6"
TMPD = D / "temp/identity5m_20261008/r6"
for _p in (INP, OUTPUT, TMPD, R6 / "work", R6 / "masks", R6 / "keys", R6 / "receipts",
           R6 / "evidence", R6 / "checkpoint", R6 / "storyboard", R6 / "workflows"):
    _p.mkdir(parents=True, exist_ok=True)

R4 = C / "r4"
R5 = C / "r5"
ENVPY = "C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe"
ENVPYLIBS = R4 / "env/pylibs"
BASE = "http://127.0.0.1:8188"

# ---- CAST B binding (packet S1 + P3/CAST_B_SPEC) ----
CASTB_OF_ENTITY = {
    "E1": "B01_Khang_front_bust.png",
    "E2": "B02_Lam_front_bust.png",
    "E8": "B02_Lam_front_bust.png",   # E8 = E2 same identity, HOME costume state (provisional; source-audit tracked)
    "E3": "B03_Mai_front_bust.png",
    "E4": "B04_Phuc_front_bust.png",  # provisional - subject to source identity audit
    "E5": "B05_Van_front_bust.png",
    "E6": "B06_Linh_front_bust.png",
    "E7": "B07_Thu_front_bust.png",
}
CASTB_DESC = {
    "B01_Khang_front_bust.png": "B01 Khang (wide square face, short black coily hair, straight brows, short wide nose, small chin stubble; forest-green shirt)",
    "B02_Lam_front_bust.png": "B02 Lam (long narrow face, prominent ears, short copper-brown hair, thin slanted brows, long nose; be jacket / grey-blue shirt; HOME state = light-blue tee + messy silver)",
    "B03_Mai_front_bust.png": "B03 Mai (round face, black bob with straight fringe, wide-set eyes, round nose; terracotta top)",
    "B04_Phuc_front_bust.png": "B04 Phuc (rectangular face, shaved head, thick brows, short moustache, round ears; slate-blue shirt)",
    "B05_Van_front_bust.png": "B05 Van (heart-shaped face, shoulder-length wavy brown hair, high cheekbones; earth-yellow dress)",
    "B06_Linh_front_bust.png": "B06 Linh (compact oval face, black pixie cut off-centre, low thick brows; cream/teal vest)",
    "B07_Thu_front_bust.png": "B07 Thu (wide oval face, auburn hair in high bun, arched brows; plum-violet dress)",
}
STYLE_TXT = ("Flat 2D cel-shaded animation style: solid flat colour fills, one hard shadow tone per shape, "
             "thin clean outlines, no gradients, no photographic texture, no 3D rendering.")


def sha(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha16(p: Path):
    return sha(p)[:16]


def gframe_of(sid: str, fid: int) -> int:
    """shot-local 1-based fid -> global source frame; f0001 = a0 (NO shift)."""
    return PLAN[sid]["start_frame"] + fid - 1


def stage_frame(sid: str, gframe: int, dst: Path) -> Path:
    """Extract ONE source frame at canonical canvas 640x360 (no pad)."""
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{gframe/30:.6f}", "-i", str(SRC),
                        "-frames:v", "1", str(dst)], capture_output=True, text=True)
    if r.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"stage_frame failed {sid} g{gframe}: {r.stderr[-300:]}")
    return dst


def pad_to_368(img):
    """explicit pad top4/bottom4 (the ONE canonical transform)."""
    import numpy as np
    return np.pad(img, ((4, 4), (0, 0), (0, 0)) if img.ndim == 3 else ((4, 4), (0, 0)))


def unpad_368(img):
    """explicit inverse; asserts the row band."""
    import numpy as np
    if img.shape[0] != 368:
        raise ValueError(f"unpad expects 368 rows, got {img.shape[0]}")
    return img[4:364]


def run(cmd, env=None, cwd=None):
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd)
    return round(time.time() - t0, 1), r


def post(graph):
    import urllib.request
    req = urllib.request.Request(BASE + "/prompt", data=json.dumps({"prompt": graph}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def wait(pid, timeout=1800):
    import urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(f"{BASE}/history/{pid}", timeout=30) as resp:
            h = json.loads(resp.read().decode())
        if pid in h:
            return h[pid]
        time.sleep(3)
    raise TimeoutError(f"prompt {pid}")

def collect_outputs(hist):
    """Resolve Comfy Save* outputs to real files under D/output."""
    outs = []
    for node in hist.get("outputs", {}).values():
        for v in node.values():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and "filename" in item:
                        cand = D / "output" / item.get("subfolder", "") / item["filename"]
                        outs.append(cand)
    return outs
