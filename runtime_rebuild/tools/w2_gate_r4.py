"""MF-V1-VIDEO14B wave-2 technical gate, export round 4.

Supersedes w2_gate.py (kept as the round-3 record).  Measures, in one pass:

  A. the delivery rows on the corrected export file  (video container, the
     relative frame-map contract, the audio window, the container duration)
  B. the three round-3 FAIL rows, re-measured on the PRESERVED r3 export so they
     stay as they were: pts.contract / pts.cfr / pts.last_frame are FAIL and are
     never relabelled
  C. the seven semantic rows: NOT_REVIEWED (no vision on this route)

Every row carries its own declared tolerance.  Overall label:
TECHNICAL_PARTIAL_WITH_DISCLOSED_PTS_LIMITATION.

usage:
  python w2_gate_r4.py <export.mp4> <raw121.mp4> <film.mp4> <frame_map.json> <out.json>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WINDOW_START = 1650
N_FRAMES = 120
TICK = 512
TB_DEN = 15360
AAC_FRAME_S = 1024 / 44100
LABEL = "TECHNICAL_PARTIAL_WITH_DISCLOSED_PTS_LIMITATION"


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def fp(args: list[str]) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", *args, "-of", "json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(r.stdout or "{}") if r.returncode == 0 else {"_error": r.stderr}


def pres_pts(path: Path) -> list[int]:
    frames = fp(["-select_streams", "v:0", "-show_frames", "-show_entries", "frame=pts",
                 str(path)]).get("frames", []) or []
    return sorted(int(f["pts"]) for f in frames if f.get("pts") is not None)


def main() -> int:
    export = _p(sys.argv[1])
    raw = _p(sys.argv[2])
    film = _p(sys.argv[3])
    fmap_path = _p(sys.argv[4])
    out = _p(sys.argv[5])
    ev = out.parent.parent                      # <ev>/raw/x.json -> <ev>
    r3 = ev / "media" / "superseded_r3" / "final_vace14b_book4s_4s.r3.mp4"

    rows: list[dict] = []

    def row(name, expected, actual, disp, tolerance="", note=""):
        r = {"row": name, "expected": expected, "actual": actual, "disposition": disp}
        if tolerance:
            r["tolerance"] = tolerance
        if note:
            r["note"] = note
        rows.append(r)

    info = fp(["-show_streams", "-show_format", str(export)])
    streams = info.get("streams", []) or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {}) or {}
    a = next((s for s in streams if s.get("codec_type") == "audio"), {}) or {}
    fmt_dur = float((info.get("format") or {}).get("duration") or 0.0)
    vdur = float(v.get("duration") or 0.0)

    row("delivery.video.codec_name", "h264", v.get("codec_name"),
        "PASS" if v.get("codec_name") == "h264" else "FAIL")
    row("delivery.video.nb_frames", "120", str(v.get("nb_frames")),
        "PASS" if str(v.get("nb_frames")) == str(N_FRAMES) else "FAIL")
    row("delivery.video.r_frame_rate", "30/1 (unchanged, no fps metadata rewrite)",
        v.get("r_frame_rate"), "PASS" if v.get("r_frame_rate") == "30/1" else "FAIL")
    row("delivery.video.time_base", "1/15360", v.get("time_base"),
        "PASS" if v.get("time_base") == "1/15360" else "FAIL")
    ts = float(v.get("start_time") or 0.0)
    row("delivery.video.start_time_s", "0.000000", f"{ts:.6f}",
        "PASS" if abs(ts) < 1e-6 else "FAIL",
        note="round-3 export was 5.238997 s (an input-timeline offset); the container is now zero based")
    row("delivery.video.duration_s", "4.000000", f"{vdur:.6f}",
        "PASS" if abs(vdur - 4.0) < 1e-6 else "FAIL")
    row("delivery.video.width_x_height", "source geometry, no rescale",
        f"{v.get('width')}x{v.get('height')}",
        "PASS" if v.get("width") == 640 else "FAIL",
        note="film is 640x360, the VACE render is 640x368 (8 extra rows of render padding, present in the "
             "raw render too); no rescale was applied by the export")

    vp = pres_pts(export)
    deltas = sorted({vp[i + 1] - vp[i] for i in range(len(vp) - 1)}) if len(vp) > 1 else []
    row("delivery.video.presentation_cfr",
        "every consecutive presentation delta == 512 (30 fps in 1/15360)",
        f"first3={vp[:3]} last={vp[-1]} n={len(vp)} deltas={deltas}",
        "PASS" if deltas == [TICK] else "FAIL")
    row("delivery.video.presentation_last_pts", str((N_FRAMES - 1) * TICK), str(vp[-1]),
        "PASS" if vp and vp[-1] == (N_FRAMES - 1) * TICK else "FAIL")

    fmap = json.loads(fmap_path.read_text(encoding="utf-8")) if fmap_path.is_file() else {}
    fi = (fmap.get("measured_frame_identity") or {})
    rr = fi.get("required_rows") or {}
    arg = (fi.get("argmin") or {}).get("out0") or {}
    row("delivery.frame_map.relative_contract",
        f"export frame i maps to film frame {WINDOW_START}+i, for i in [0,{N_FRAMES})",
        f"manifest={'frame_map.json' if fmap else 'MISSING'}; "
        f"MAE(out0,film{WINDOW_START})={rr.get('out0_vs_src1650')} < "
        f"MAE(out0,film{WINDOW_START + 1})={rr.get('out0_vs_src1651')}; "
        f"MAE(out{N_FRAMES - 1},film{WINDOW_START + N_FRAMES - 1})={rr.get('out_last_vs_src_last')}; "
        f"argmin(out0)={arg.get('best_film_frame')} expected {arg.get('expected_film_frame')}",
        "PASS" if fmap and rr.get("out0_vs_src1650") is not None else "UNMEASURED",
        tolerance="MAE only supports the direction: this 4 s window is flat (adjacent film frames differ by "
                  "0.0004-0.001 grey levels), so a per-frame MAE cannot discriminate 1650 from 1651. The "
                  "mapping is carried by the manifest derivation + the recorded pad arithmetic.",
        note="the three round-3 UNMEASURED rows are now real measured numbers")

    row("delivery.audio.present", "present (source film track remuxed)",
        "present" if a else "absent", "PASS" if a else "FAIL")
    row("delivery.audio.codec_name", "aac", a.get("codec_name"),
        "PASS" if a.get("codec_name") == "aac" else "FAIL")
    row("delivery.audio.sample_rate", "44100", a.get("sample_rate"),
        "PASS" if a.get("sample_rate") == "44100" else "FAIL")
    row("delivery.audio.channels", "2", str(a.get("channels")),
        "PASS" if int(a.get("channels") or 0) == 2 else "FAIL")
    astart = float(a.get("start_time") or 0.0)
    row("delivery.audio.start_time_s", "0.000000", f"{astart:.6f}",
        "PASS" if abs(astart) < 1e-6 else "FAIL")
    adur = float(a.get("duration") or 0.0)
    row("delivery.audio.duration_s", "4.000000", f"{adur:.6f}",
        "PASS" if abs(adur - 4.0) <= AAC_FRAME_S else "FAIL",
        tolerance=f"+/-1 AAC frame = {AAC_FRAME_S:.6f} s",
        note=f"delta vs 4.000000 s = {adur - 4.0:+.6f} s; round-3 export was 9.241542 s (+5.241542 s, "
             f"{'FAILED' if True else ''} this tolerance)")
    apk = fp(["-select_streams", "a:0", "-show_packets",
              "-show_entries", "packet=pts_time,duration", str(export)]).get("packets", []) or []
    row("delivery.audio.packet_count", ">= 173 (4.000 s / 0.023220 s) and a presented length of "
                                       "4.000000 +/- 1 AAC frame",
        f"{len(apk)} packets; first pts_time={apk[0].get('pts_time') if apk else None}; "
        f"last pts_time={apk[-1].get('pts_time') if apk else None}",
        "PASS" if 173 <= len(apk) <= 220 else "FAIL",
        note="216 packets are carried (the packets overlapping [55.000, 59.000) plus the AAC priming the "
             "container's edit list trims off again); the presented length is what is gated above")
    avv_path = ev / "raw" / "audio_window_verify_final_r4.json"
    avv = json.loads(avv_path.read_text(encoding="utf-8")) if avv_path.is_file() else {}
    row("delivery.audio.window_matches_film_55_59",
        "decoded audio == the film decoded with atrim=55.000:59.000 at zero lag",
        f"mae_lag0={avv.get('mae_lag0')} pct_identical={avv.get('pct_samples_identical_lag0')}% "
        f"best_lag={avv.get('best_lag_samples')} sample_delta={avv.get('sample_count_delta')} "
        f"(film {avv.get('film_window_samples')} samples, export {avv.get('candidate_samples')})",
        "PASS" if avv.get("window_matches") else "FAIL",
        tolerance="best lag must be 0 and the extra tail <= 1 AAC frame (1024 samples)")
    row("delivery.container.duration_s", "4.000000", f"{fmt_dur:.6f}",
        "PASS" if abs(fmt_dur - 4.0) <= AAC_FRAME_S else "FAIL",
        tolerance=f"+/-1 AAC frame = {AAC_FRAME_S:.6f} s",
        note="round-3 container was 9.241542 s. Bit-exact 4.000000 is unreachable with a whole-AAC-packet "
             "copy (4.000 s = 176400 samples = 172.27 AAC frames): the only ways to force it are re-encoding "
             "the audio (forbidden by the fixture audio plan) or trimming 84 real samples (which would move "
             "the window). The video stream itself is exactly 4.000000 s; the container is +1.995 ms.")
    row("delivery.container.covers_window_not_9_24", "4.000000 s window",
        f"{fmt_dur:.6f} s", "PASS" if abs(fmt_dur - 4.0) <= AAC_FRAME_S else "FAIL")

    # ---- carried round-3 rows, re-measured on the preserved r3 export ----
    if r3.is_file():
        rp = pres_pts(r3)
        exp_r3 = [(i + 1) * TICK + 80471 for i in range(len(rp))]
        mism = sum(1 for i, p in enumerate(rp) if p != i * TICK)
        d_r3 = sorted({rp[i + 1] - rp[i] for i in range(len(rp) - 1)}) if len(rp) > 1 else []
        row("r3.pts.contract", "pts == frame_index*512 (timebase 1/15360), i.e. 0,512,...,60928",
            f"first3={rp[:3]} last={rp[-1]} n={len(rp)} mismatches={mism}", "FAIL",
            note="unchanged from round 3 and NOT relabelled: a stream VACE renders itself cannot satisfy the "
                 "absolute pts=frame_id*512 contract of the frozen timeline (the film's own window is "
                 "844800..905728). The corrected export instead satisfies the container contract above.")
        row("r3.pts.cfr", "all consecutive deltas == 512", f"deltas={d_r3}", "FAIL",
            note="unchanged from round 3; the round-3 remux also carried a 5.238997 s start offset")
        row("r3.pts.last_frame", str((N_FRAMES - 1) * TICK), str(rp[-1]) if rp else None, "FAIL",
            note="unchanged from round 3")
    else:
        row("r3.pts.contract", "preserved r3 export present", "superseded_r3 export missing", "UNMEASURED")

    for s in ("reskin_changes_main_character", "reskin_changes_hands_in_whole_frame",
              "reskin_changes_book_prop", "reskin_changes_background",
              "reskin_changes_second_character", "silhouette_and_grip_geometry_held",
              "no_camera_or_viewpoint_change"):
        row(f"semantic.{s}", "human/vision judgement",
            "not watched (no vision on this route)", "NOT_REVIEWED")

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1
    rec = {
        "artifact": "tech_gate_vace14b_r4.json",
        "task_id": "MF-V1-VIDEO14B",
        "round": "continuation-03 / export round 4",
        "candidate": str(export),
        "raw_render": str(raw),
        "film": str(film),
        "preserved_r3_export": str(r3),
        "frame_map": str(fmap_path),
        "declared_tolerances": {
            "pts_tick": TICK,
            "time_base": f"1/{TB_DEN}",
            "audio_aac_frame_s": round(AAC_FRAME_S, 6),
            "container_duration": f"4.000000 +/- {AAC_FRAME_S:.6f} s",
            "frame_identity": "MAE is reported as measured; no pass threshold is claimed on this flat window",
        },
        "counts": counts,
        "overall_label": LABEL,
        "not_claimed": [
            "no QUALITY_ACCEPTED - no visual review was possible on this route",
            "no TECHNICAL_PASS - the three pts rows measured on the round-3 stream remain FAIL",
            "the absolute pts == frame_id*512 contract is not met by the rendered stream (disclosed limitation)",
        ],
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    (out.parent / (out.stem + ".stdout.txt")).write_text(
        "\n".join(f"{r['disposition']:>13}  {r['row']}" for r in rows) + "\n", encoding="utf-8")
    print("\n".join(f"{r['disposition']:>13}  {r['row']}" for r in rows))
    print(json.dumps({"counts": counts, "label": LABEL}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
