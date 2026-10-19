"""A/V measurement probe for MF-V1-VIDEO14B wave 2.

Reports, per file, exactly the numbers the gate needs:
  video stream fields, video packet PTS (first 3 / last / delta set / count)
  audio stream fields, audio packet count, first+last pts_time/dts_time,
  audio start_time, audio duration, and the delta of the audio duration versus
  the declared 4.000000 s window.

usage:
  python w2_av_probe.py <file.mp4> [out.json]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WINDOW_S = 4.0
AAC_FRAME_S = 1024 / 44100  # 0.023219954648526078


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def fp(args: list[str]) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", *args, "-of", "json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return {"_error": (r.stderr or "").strip()}
    return json.loads(r.stdout or "{}")


def probe(path: Path) -> dict:
    info = fp(["-show_streams", "-show_format", str(path)])
    streams = info.get("streams", []) or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {}) or {}
    a = next((s for s in streams if s.get("codec_type") == "audio"), {}) or {}

    vpk = fp(["-select_streams", "v:0", "-show_packets",
              "-show_entries", "packet=pts,dts,duration,pts_time", str(path)]).get("packets", []) or []
    apk = fp(["-select_streams", "a:0", "-show_packets",
              "-show_entries", "packet=pts,dts,duration,pts_time", str(path)]).get("packets", []) or []

    vpts = [int(p["pts"]) for p in vpk if p.get("pts") is not None]
    deltas = sorted({vpts[i + 1] - vpts[i] for i in range(len(vpts) - 1)}) if len(vpts) > 1 else []

    # Presentation order matters: decoded packets come back in DECODE order, so a
    # B-frame stream looks non-CFR there. Sort the frame pts ascending first.
    vfr = fp(["-select_streams", "v:0", "-show_frames",
              "-show_entries", "frame=pts,pts_time", str(path)]).get("frames", []) or []
    fpts = sorted(int(f["pts"]) for f in vfr if f.get("pts") is not None)
    fdeltas = sorted({fpts[i + 1] - fpts[i] for i in range(len(fpts) - 1)}) if len(fpts) > 1 else []

    def f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    a_first = f(apk[0].get("pts_time")) if apk else None
    a_last = f(apk[-1].get("pts_time")) if apk else None
    a_last_end = None
    if apk:
        d = apk[-1].get("duration")
        try:
            a_last_end = float(apk[-1]["pts_time"]) + (float(d) / 44100.0 if d else AAC_FRAME_S)
        except (TypeError, ValueError, KeyError):
            a_last_end = None

    a_dur_s = f(a.get("duration"))
    rec = {
        "file": str(path),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "format_duration_s": f((info.get("format") or {}).get("duration")),
        "format_start_time_s": f((info.get("format") or {}).get("start_time")),
        "video": {
            "codec_name": v.get("codec_name"),
            "nb_frames": v.get("nb_frames"),
            "r_frame_rate": v.get("r_frame_rate"),
            "avg_frame_rate": v.get("avg_frame_rate"),
            "time_base": v.get("time_base"),
            "start_time_s": f(v.get("start_time")),
            "duration_s": f(v.get("duration")),
            "width": v.get("width"),
            "height": v.get("height"),
            "packets": len(vpts),
            "pts_first3": vpts[:3],
            "pts_last": vpts[-1] if vpts else None,
            "packet_order_delta_set": deltas[:5],
            "frames_presented": len(fpts),
            "frames_presented_first3": fpts[:3],
            "frames_presented_last": fpts[-1] if fpts else None,
            "presentation_delta_set": fdeltas[:5],
            "presentation_cfr_512": fdeltas == [512],
            "pts_zero_based_cfr": bool(fpts) and fpts[0] == 0 and fdeltas == [512],
            "delta_set": deltas[:5],
            "delta_count": len(deltas),
        },
        "audio": {
            "present": bool(a),
            "codec_name": a.get("codec_name"),
            "sample_rate": a.get("sample_rate"),
            "channels": a.get("channels"),
            "time_base": a.get("time_base"),
            "start_time_s": f(a.get("start_time")),
            "duration_s": a_dur_s,
            "packets": len(apk),
            "first_pts_time": a_first,
            "last_pts_time": a_last,
            "last_packet_end_s": a_last_end,
        },
    }
    if a_dur_s is not None:
        rec["audio"]["delta_vs_4s_s"] = round(a_dur_s - WINDOW_S, 6)
        rec["audio"]["within_1_aac_frame"] = abs(a_dur_s - WINDOW_S) <= AAC_FRAME_S + 1e-9
    rec["declared_tolerance_s"] = round(AAC_FRAME_S, 6)
    return rec


def main() -> int:
    path = _p(sys.argv[1])
    rec = probe(path)
    text = json.dumps(rec, indent=1, ensure_ascii=False)
    if len(sys.argv) > 2:
        out = _p(sys.argv[2])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
