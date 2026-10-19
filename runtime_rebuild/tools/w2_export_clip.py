"""MF-V1-VIDEO14B wave-2 corrective export (round 4).

Builds the delivered clip from the raw VACE 14B render with:
  video  : stream copy of the render, exactly 120 frames (the 121st packet in
           file order is dropped = the model's held pad frame), then the PTS of
           the single retained pad frame is re-based from 61440 to 60928 so the
           presentation timeline is an exact 30 fps lattice 0..60928
           (container/time-base normalisation only: no re-encode, no rescale,
           no fps metadata change).
  audio  : stream copy of the FROZEN SOURCE FILM's [55.000, 59.000) window
           taken with -ss/-t BEFORE the input, aac 44100 2 ch. -avoid_negative_ts
           is never used.
  mux    : both streams copied into one mp4.

Every step is recorded (argv, exit code, output) and both measurement probes are
run against the result.

usage:
  python w2_export_clip.py <raw_121f.mp4> <film.mp4> <out.mp4> <workdir> <evidence_dir>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAW_START_TICKS = 0
PAD_PTS_ORIGINAL = 61440          # held pad frame, pts 120*512
PAD_PTS_REBASED = 60928           # free lattice slot = frame 119 (film 1769)
WINDOW_START_S = 55.000
WINDOW_LEN_S = 4.000
N_FRAMES = 120

HERE = Path(__file__).resolve().parent


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def run(argv: list[str], log: list[dict]) -> tuple[int, str]:
    r = subprocess.run(argv, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    log.append({"argv": argv, "returncode": r.returncode,
                "stdout_tail": (r.stdout or "")[-400:], "stderr_tail": (r.stderr or "")[-400:]})
    if r.returncode != 0:
        print(json.dumps(log[-1], indent=1))
        raise SystemExit(f"command failed: {argv}")
    return r.returncode, r.stderr or ""


def main() -> int:
    raw = _p(sys.argv[1])
    film = _p(sys.argv[2])
    out = _p(sys.argv[3])
    work = _p(sys.argv[4])
    ev = _p(sys.argv[5])
    work.mkdir(parents=True, exist_ok=True)
    ev.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)

    log: list[dict] = []
    v_cut = work / "video_120f_pad_kept.mp4"
    v_cfr = work / "video_120f_cfr.mp4"
    a_win = work / "audio_window_55_59.m4a"

    # 1. video: exactly 120 frames out of the 121-frame render (drop the 121st
    #    packet in file order = the model's held pad frame), stream copy only.
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-map", "0:v:0",
         "-c:v", "copy", "-frames:v", str(N_FRAMES), str(v_cut)], log)

    # 2. container/time-base normalisation of the retained pad frame: pts 61440
    #    -> 60928 (the empty lattice slot), PTS only, DTS untouched so the
    #    B-frame decode order survives. Video bitstream is byte-identical.
    expr = f"setts=pts=if(gte(TS\\,{PAD_PTS_ORIGINAL})\\,{PAD_PTS_REBASED}\\,TS)"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(v_cut), "-map", "0:v:0",
         "-c:v", "copy", "-bsf:v", expr, str(v_cfr)], log)

    # 3. audio: the source film's [55.000, 59.000) window, cut with -ss/-t
    #    BEFORE the input, stream copy, no -avoid_negative_ts.
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{WINDOW_START_S:.3f}", "-i", str(film),
         "-map", "0:a:0", "-c:a", "copy", "-t", f"{WINDOW_LEN_S:.3f}", str(a_win)], log)

    # 4. mux video + audio, both copied.
    run(["ffmpeg", "-v", "error", "-y", "-i", str(v_cfr), "-i", str(a_win),
         "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
         "-movflags", "+faststart", str(out)], log)

    # 5. measure the result with both probes
    probe_out = ev / "av_probe_final_r4.json"
    r = subprocess.run([sys.executable, str(HERE / "w2_av_probe.py"), str(out), str(probe_out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    probe = json.loads(probe_out.read_text(encoding="utf-8"))
    verify_out = ev / "audio_window_verify_final_r4.json"
    r2 = subprocess.run([sys.executable, str(HERE / "w2_audio_verify.py"), str(out), str(film),
                         "--start", f"{WINDOW_START_S:.3f}", "--end", "59.000", "--out", str(verify_out)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    verify = json.loads(verify_out.read_text(encoding="utf-8")) if verify_out.is_file() else {}

    rec = {
        "artifact": "w2_export_clip.py run record",
        "raw_input": str(raw),
        "film_input": str(film),
        "output": str(out),
        "video_rule": "stream copy, 120 frames, pad packet pts rebound 61440->60928 (container/timebase only)",
        "audio_rule": f"-ss {WINDOW_START_S:.3f} -t {WINDOW_LEN_S:.3f} before the input, -c:a copy, aac 44100 2ch",
        "commands": log,
        "measured": probe,
        "audio_window_verification": verify,
    }
    (ev / "export_r4_record.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False),
                                              encoding="utf-8")
    print(json.dumps({
        "output": str(out),
        "size_bytes": out.stat().st_size,
        "format_duration_s": probe["format_duration_s"],
        "video": {k: probe["video"][k] for k in ("codec_name", "nb_frames", "r_frame_rate", "time_base",
                                                "start_time_s", "duration_s", "frames_presented",
                                                "frames_presented_first3", "frames_presented_last",
                                                "presentation_delta_set", "presentation_cfr_512",
                                                "pts_zero_based_cfr")},
        "audio": {k: probe["audio"][k] for k in ("codec_name", "sample_rate", "channels", "start_time_s",
                                                 "duration_s", "packets", "first_pts_time",
                                                 "last_pts_time", "delta_vs_4s_s", "within_1_aac_frame")},
        "audio_window_matches_film": verify.get("window_matches"),
        "audio_mae_lag0": verify.get("mae_lag0"),
        "audio_samples": [verify.get("candidate_samples"), verify.get("film_window_samples")],
        "cmd_count": len(log),
        "probe_stderr": (r.stderr or "")[-200:],
        "verify_stderr": (r2.stderr or "")[-200:],
    }, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
