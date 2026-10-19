"""Frame-identity measurement for MF-V1-VIDEO14B wave 2 (round 4 fix).

Old extractor returned UNMEASURED (null) for all three rows.  This one extracts
the source pixels from the FROZEN SOURCE FILM itself and measures:

  out frame 0   vs film frame 1650   (required row)
  out frame 0   vs film frame 1651   (required row)
  out frame 119 vs film frame 1769   (required row)
  plus a control row out 119 vs film 1768, and a full argmin matrix
  out i in {0,1,2,3,119} x film j in {1648..1653, 1767..1770} so the mapping
  is read off the measurements instead of being asserted.

Source extraction is frame-INDEX exact (select=eq(n,IDX) on a full decode), not
time-seek approximation.  Output PNGs are kept as evidence.

usage:
  python w2_frame_identity.py <clip.mp4> <film.mp4> <out.json> [--pngs <dir>]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WINDOW_START = 1650
N_FRAMES = 120
OUT_PROBES = [0, 1, 2, 3, N_FRAMES - 1]
FILM_PROBES = list(range(WINDOW_START - 2, WINDOW_START + 4)) + \
              list(range(WINDOW_START + N_FRAMES - 3, WINDOW_START + N_FRAMES + 1))


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def extract(video: Path, frame: int, dst: Path) -> list[str]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                        "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", "-f", "image2", str(dst)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return ["ffmpeg", "-i", str(video), "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", str(dst)], \
        (r.returncode, (r.stderr or "")[-200:])


def mae_variants(a: Path, b: Path) -> dict:
    """MAE for every sane alignment of two frames.

    The VACE render is 640x368 while the frozen source film is 640x360, so a raw
    MAE has no defined value.  Rather than silently resizing, both candidate
    alignments are measured (drop the extra rows from the top, or from the
    bottom) plus a resized comparison, and the caller reports which one it used.
    """
    import numpy as np
    from PIL import Image
    x = np.asarray(Image.open(a).convert("RGB"), dtype="float32")
    y = np.asarray(Image.open(b).convert("RGB"), dtype="float32")
    out: dict = {"shape_a": list(x.shape), "shape_b": list(y.shape)}
    if x.shape == y.shape:
        out["exact"] = round(float(np.abs(x - y).mean()), 4)
        return out
    if x.shape[1] != y.shape[1]:
        out["error"] = "width mismatch, no alignment attempted"
        return out
    dh = x.shape[0] - y.shape[0]
    if dh > 0:  # a is taller
        out["drop_top_rows"] = round(float(np.abs(x[dh:] - y).mean()), 4)
        out["drop_bottom_rows"] = round(float(np.abs(x[: y.shape[0]] - y).mean()), 4)
    elif dh < 0:
        out["drop_top_rows"] = round(float(np.abs(x - y[-dh:]).mean()), 4)
        out["drop_bottom_rows"] = round(float(np.abs(x - y[: x.shape[0]]).mean()), 4)
    small = x if x.shape[0] < y.shape[0] else y
    big = y if x.shape[0] < y.shape[0] else x
    big_img = Image.fromarray(big.astype("uint8")).resize(
        (small.shape[1], small.shape[0]), Image.BILINEAR)
    out["resized_to_shorter"] = round(float(np.abs(np.asarray(big_img, dtype="float32") - small).mean()), 4)
    return out


def mae(a: Path, b: Path):
    v = mae_variants(a, b)
    if "exact" in v:
        return v["exact"]
    cands = [v.get("drop_top_rows"), v.get("drop_bottom_rows"), v.get("resized_to_shorter")]
    cands = [c for c in cands if c is not None]
    return min(cands) if cands else None


def main() -> int:
    clip = _p(sys.argv[1])
    film = _p(sys.argv[2])
    dst = _p(sys.argv[3])
    png_dir = _p(sys.argv[sys.argv.index("--pngs") + 1]) if "--pngs" in sys.argv else \
        dst.parent / "frames_r4"

    cmds: list[dict] = []
    out_png: dict[int, Path] = {}
    film_png: dict[int, Path] = {}
    for i in OUT_PROBES:
        p = png_dir / f"out_frame{i:03d}.png"
        argv, (rc, err) = extract(clip, i, p)
        cmds.append({"argv": argv, "returncode": rc, "stderr_tail": err})
        out_png[i] = p
    for j in FILM_PROBES:
        p = png_dir / f"film_frame{j}.png"
        argv, (rc, err) = extract(film, j, p)
        cmds.append({"argv": argv, "returncode": rc, "stderr_tail": err})
        film_png[j] = p

    matrix: dict[str, dict[str, float | None]] = {}
    for i in OUT_PROBES:
        row: dict[str, float | None] = {}
        for j in FILM_PROBES:
            row[str(j)] = (round(mae(out_png[i], film_png[j]), 4)
                           if out_png[i].is_file() and film_png[j].is_file() else None)
        matrix[f"out{i}"] = row

    argmin = {}
    for i in OUT_PROBES:
        vals = [(j, v) for j, v in ((int(k), v) for k, v in matrix[f"out{i}"].items()) if v is not None]
        if vals:
            best = min(vals, key=lambda t: t[1])
            srt = sorted(vals, key=lambda t: t[1])
            argmin[f"out{i}"] = {
                "best_film_frame": best[0], "best_mae": round(best[1], 4),
                "expected_film_frame": WINDOW_START + i,
                "matches_expected": best[0] == WINDOW_START + i,
                "runner_up_film_frame": srt[1][0] if len(srt) > 1 else None,
                "runner_up_mae": round(srt[1][1], 4) if len(srt) > 1 else None,
                "separation": (round(srt[1][1] - best[1], 4) if len(srt) > 1 else None),
            }

    rows = {
        "out0_vs_src1650": matrix.get("out0", {}).get("1650"),
        "out0_vs_src1651": matrix.get("out0", {}).get("1651"),
        "out_last_vs_src_last": matrix.get(f"out{N_FRAMES - 1}", {}).get(str(WINDOW_START + N_FRAMES - 1)),
        "control_out_last_vs_src_prev": matrix.get(f"out{N_FRAMES - 1}", {}).get(str(WINDOW_START + N_FRAMES - 2)),
    }
    row_variants = {}
    for name, i, j in (("out0_vs_src1650", 0, WINDOW_START),
                       ("out0_vs_src1651", 0, WINDOW_START + 1),
                       ("out_last_vs_src_last", N_FRAMES - 1, WINDOW_START + N_FRAMES - 1),
                       ("control_out_last_vs_src_prev", N_FRAMES - 1, WINDOW_START + N_FRAMES - 2)):
        if out_png[i].is_file() and film_png[j].is_file():
            row_variants[name] = mae_variants(out_png[i], film_png[j])
    rec = {
        "artifact": "frame_identity_r4.json",
        "clip": str(clip),
        "film": str(film),
        "window_start_frame": WINDOW_START,
        "out_frames_probed": OUT_PROBES,
        "film_frames_probed": FILM_PROBES,
        "required_rows": rows,
        "required_rows_alignment_detail": row_variants,
        "alignment_rule": "min over (drop_top_rows, drop_bottom_rows, resized_to_shorter) because the "
                          "render is 640x368 and the frozen film is 640x360",
        "matrix": matrix,
        "argmin": argmin,
        "png_dir": str(png_dir),
        "commands": cmds,
        "all_expected_argmin": all(v.get("matches_expected") for v in argmin.values()),
    }
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"required_rows": rows, "argmin": argmin,
                      "all_expected_argmin": rec["all_expected_argmin"],
                      "png_dir": str(png_dir)}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
