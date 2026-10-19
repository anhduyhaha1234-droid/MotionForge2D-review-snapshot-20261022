"""R6 common — paths, canonical canvas contract, CAST B binding, frame map.

CANONICAL CONTRACT (R6):
  - source canvas 640x360; padded canvas 640x368 = pad top4/bottom4 applied ONCE, inverse explicit.
  - frame map: shot f0001 = source global frame a0 (NO 1-frame shift); gframe = a0 + fid - 1.
  - every image/mask in one pipeline shares shape/time; masks 640x360 canonical.
Paths: ALL outputs under R6/C or INPUT-root r6. R4/R5 strictly read-only.
"""
from __future__ import annotations
import hashlib, json, os, subprocess, tempfile, time
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


_STAGE_CONTRACT = "r6.stage_frame.v1.ffmpeg-ss-30fps-1frame-no-pad"
_STAGE_RECORD_LIMIT = 4096
_STAGE_KEYS = {"contract", "source_path", "source_sha256", "sid", "gframe",
               "output_path", "output_sha256", "output_size"}


def _stage_source_identity() -> tuple[str, str]:
    try:
        source = Path(SRC).resolve(strict=True)
        if not source.is_file():
            raise OSError("source is not a regular file")
        return str(source), sha(source)
    except OSError as exc:
        raise RuntimeError(f"stage_frame source unavailable: {SRC}") from exc


def _stage_record(path: Path) -> dict | None:
    """Reject old, malformed, duplicated, oversized or wrongly typed receipts."""
    def unique_pairs(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate staged-source receipt key")
            obj[key] = value
        return obj

    try:
        if path.is_symlink() or path.stat().st_size > _STAGE_RECORD_LIMIT:
            return None
        raw = path.read_bytes()
        if len(raw) > _STAGE_RECORD_LIMIT:
            return None
        record = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
    except (OSError, UnicodeError, ValueError, RecursionError):
        return None
    if type(record) is not dict or set(record) != _STAGE_KEYS:
        return None
    if any(type(record[key]) is not str for key in
           ("contract", "source_path", "source_sha256", "sid", "output_path", "output_sha256")):
        return None
    if type(record["gframe"]) is not int or type(record["output_size"]) is not int:
        return None
    return record


def _stage_temp(target: Path, suffix: str) -> Path:
    fd, name = tempfile.mkstemp(prefix=f".{target.stem}.stage-", suffix=suffix, dir=target.parent)
    os.close(fd)
    return Path(name)


def stage_frame(sid: str, gframe: int, dst: Path) -> Path:
    """Extract one canonical 640x360 source frame with exact staged provenance."""
    if type(sid) is not str or sid not in PLAN:
        raise ValueError(f"stage_frame unknown shot: {sid!r}")
    shot = PLAN[sid]
    if (type(gframe) is not int or gframe < 0 or
            not shot["start_frame"] <= gframe < shot["start_frame"] + shot["frames"]):
        raise ValueError(f"stage_frame invalid global frame {gframe!r} for {sid}")
    dst = Path(dst)
    if dst.is_symlink():
        raise ValueError(f"stage_frame destination is a symlink: {dst}")
    output_path = str(dst.resolve(strict=False))
    source_path, source_sha = _stage_source_identity()
    identity = {"contract": _STAGE_CONTRACT, "source_path": source_path,
                "source_sha256": source_sha, "sid": sid, "gframe": gframe,
                "output_path": output_path}
    receipt = dst.with_name(dst.name + ".stage.json")
    record = _stage_record(receipt)
    if record is not None and all(record[key] == value for key, value in identity.items()):
        try:
            if (dst.is_file() and dst.stat().st_size > 0 and
                    record["output_size"] == dst.stat().st_size and
                    record["output_sha256"] == sha(dst) and
                    _stage_source_identity() == (source_path, source_sha)):
                return dst
        except OSError:
            pass

    output_tmp = pending_tmp = record_tmp = None
    try:
        output_tmp = _stage_temp(dst, dst.suffix)
        try:
            result = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{gframe/30:.6f}",
                                     "-i", str(SRC), "-frames:v", "1", str(output_tmp)],
                                    capture_output=True, text=True)
        except OSError as exc:
            raise RuntimeError(f"stage_frame extractor unavailable {sid} g{gframe}") from exc
        if result.returncode != 0 or not output_tmp.is_file() or output_tmp.stat().st_size == 0:
            raise RuntimeError(f"stage_frame failed {sid} g{gframe}: {(result.stderr or '')[-300:]}")
        if _stage_source_identity() != (source_path, source_sha):
            raise RuntimeError(f"stage_frame source changed during extraction {sid} g{gframe}")

        record = {**identity, "output_sha256": sha(output_tmp), "output_size": output_tmp.stat().st_size}
        pending_tmp = _stage_temp(receipt, ".tmp")
        pending_tmp.write_bytes(b'{"state":"pending"}')
        record_tmp = _stage_temp(receipt, ".tmp")
        record_tmp.write_text(json.dumps(record, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        # Invalidate the old receipt first. A failure after frame publication cannot bless it.
        os.replace(pending_tmp, receipt)
        pending_tmp = None
        os.replace(output_tmp, dst)
        output_tmp = None
        os.replace(record_tmp, receipt)
        record_tmp = None
        return dst
    except OSError as exc:
        raise RuntimeError(f"stage_frame staging failed {sid} g{gframe}: {exc}") from exc
    finally:
        for temp in (output_tmp, pending_tmp, record_tmp):
            if temp is not None:
                temp.unlink(missing_ok=True)


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
