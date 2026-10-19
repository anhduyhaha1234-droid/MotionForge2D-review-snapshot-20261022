"""Dump presentation-order video PTS for a file (positions of every non-512 delta).

usage: python w2_pts_dump.py <file.mp4> [out.json]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TB_DEN = 15360
TICK = 512


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def main() -> int:
    path = _p(sys.argv[1])
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
                        "-show_entries", "frame=pts,pts_time,pict_type,key_frame",
                        "-of", "json", str(path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    frames = json.loads(r.stdout or "{}").get("frames", []) or []
    rows = [(int(f["pts"]), f.get("pict_type"), f.get("key_frame"), f.get("pts_time")) for f in frames
            if f.get("pts") is not None]
    dec_order = [x[0] for x in rows]
    pres = sorted(rows)
    ppts = [x[0] for x in pres]
    anomalies = []
    for i in range(1, len(ppts)):
        d = ppts[i] - ppts[i - 1]
        if d != TICK:
            anomalies.append({"presentation_index": i, "prev_pts": ppts[i - 1], "pts": ppts[i],
                              "delta": d, "delta_ticks": d / TICK})
    rec = {
        "file": str(path),
        "time_base": f"1/{TB_DEN}",
        "expected_tick": TICK,
        "frames": len(ppts),
        "presentation_first3": ppts[:3],
        "presentation_last3": ppts[-3:],
        "presentation_cfr": not anomalies,
        "anomalies": anomalies,
        "decode_order_first5": dec_order[:5],
        "decode_order_last5": dec_order[-5:],
        "decode_order_is_presentation_order": dec_order == ppts,
        "span_s": round((ppts[-1] - ppts[0]) / TB_DEN, 6) if ppts else None,
        "expected_span_s_for_n_frames": round((len(ppts) - 1) * TICK / TB_DEN, 6),
        "pict_types": sorted({x[1] for x in pres if x[1]}),
    }
    text = json.dumps(rec, indent=1, ensure_ascii=False)
    if len(sys.argv) > 2:
        _p(sys.argv[2]).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
