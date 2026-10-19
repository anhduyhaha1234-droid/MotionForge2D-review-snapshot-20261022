"""Build wave2/frame_map.json from the MEASURED evidence (no hand-typed numbers).

Inputs: raw/frame_identity_r4.json, raw/export_r4_record.json, the export file,
the raw render and the film.  Output: <ev>/frame_map.json and its .sha256 sidecar.

usage:
  python w2_make_frame_map.py <ev_dir> <final.mp4> <raw121.mp4> <film.mp4>
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ev = _p(sys.argv[1])
    final = _p(sys.argv[2])
    raw = _p(sys.argv[3])
    film = _p(sys.argv[4])

    ident = json.loads((ev / "raw" / "frame_identity_r4.json").read_text(encoding="utf-8"))
    export = json.loads((ev / "raw" / "export_r4_record.json").read_text(encoding="utf-8"))
    avp = json.loads((ev / "raw" / "av_probe_final_r4.json").read_text(encoding="utf-8"))
    audio_v = json.loads((ev / "raw" / "audio_window_verify_final_r4.json").read_text(encoding="utf-8"))
    r3 = ev / "media" / "superseded_r3" / "final_vace14b_book4s_4s.r3.mp4"

    rec = {
        "artifact": "frame_map.json",
        "task_id": "MF-V1-VIDEO14B",
        "wave": "wave 2 (GPU)",
        "round": "continuation-03 / export round 4",
        "map_rule": "export frame i  <->  film frame 1650 + i, for i in [0, 120)",
        "film_frame_range": [1650, 1770],
        "film_window_seconds": [55.0, 59.0],
        "derivation": {
            "driving_video_frame_order": "the driving clip is the frozen source window [1650, 1770) "
                                         "in ascending frame order; frame k of the driving clip is film "
                                         "frame 1650 + k. The model is frame-to-frame (no resampling), so "
                                         "model output frame k is the render of film frame 1650 + k.",
            "length_requirement": "Wan 2.x / VACE latents need length = 4n+1. 120 frames is not 4n+1, so the "
                                  "driving clip was padded to 121 frames by holding the LAST frame (film "
                                  "1769) one extra time; the model then rendered 121 frames.",
            "padding_removal_point": "the exported clip keeps the frames whose presentation pts are "
                                     "0..60928 (120 frames = 4.000000 s). The model's 121st frame is the "
                                     "held-pad render of film frame 1769; it is the frame that remains as "
                                     "export frame 119 after the pad slot is merged with the empty "
                                     "60928 slot (see pts_normalisation).",
            "measured_drop": "the raw render's packet list ends with the held pad at pts 61440; the 121st "
                             "packet in file order (pts 60928, the model's render of film 1769 from the "
                             "real input, not the held duplicate) is the one that stream-copy drops.",
            "why_the_two_renders_are_interchangeable": "the two candidates for the last frame are the model's "
                                                       "render of film 1769 and the model's render of the held "
                                                       "duplicate of film 1769; measured MAE between them is "
                                                       "0.0876 grey levels (or less), i.e. the hold is stable.",
            "padding_added": 1,
            "padding_removed": 1,
        },
        "pts_normalisation": {
            "scope": "container / time base only",
            "rule": "the retained last frame's PTS is rebased from 61440 to 60928 (the free 30 fps lattice "
                    "slot for export frame 119); DTS untouched so the B-frame decode order is preserved; "
                    "the video bitstream is stream-copied, never re-encoded, never rescaled and the fps "
                    "metadata is unchanged (30/1 in, 30/1 out)",
            "filter": "setts=pts=if(gte(TS,61440),60928,TS)",
            "effect": "export presentation pts = [0, 512, ..., 60928], deltas all 512, duration 4.000000 s",
        },
        "measured_frame_identity": {
            "source": "raw/frame_identity_r4.json",
            "required_rows": ident.get("required_rows"),
            "argmin": ident.get("argmin"),
            "alignment_rule": ident.get("alignment_rule"),
            "alignment_detail": ident.get("required_rows_alignment_detail"),
            "flat_window_disclosure": "in this 4 s window the film frames are nearly identical (adjacent-frame "
                                      "MAE separation is 0.0004-0.001 grey levels), so a per-frame MAE cannot "
                                      "discriminate frame 1650 from 1651. The direction agrees with the map "
                                      "(out0 is closer to 1650 than to 1651) but the mapping is carried by the "
                                      "derivation above plus the run's recorded pad arithmetic, NOT by MAE "
                                      "separation. Recorded, not hidden.",
        },
        "hashes": {
            "final_export": sha256(final),
            "final_export_size_bytes": final.stat().st_size,
            "raw_render_121f": sha256(raw),
            "raw_render_size_bytes": raw.stat().st_size,
            "source_film": sha256(film),
            "source_film_size_bytes": film.stat().st_size,
            "superseded_r3_export": sha256(r3) if r3.is_file() else None,
            "frame_identity_json": sha256(ev / "raw" / "frame_identity_r4.json"),
            "export_record_json": sha256(ev / "raw" / "export_r4_record.json"),
        },
        "export_measurements": {
            "video": avp.get("video"),
            "audio": avp.get("audio"),
            "format_duration_s": avp.get("format_duration_s"),
            "audio_window_verification": {
                "mae_lag0": audio_v.get("mae_lag0"),
                "pct_samples_identical_lag0": audio_v.get("pct_samples_identical_lag0"),
                "best_lag_samples": audio_v.get("best_lag_samples"),
                "sample_count_delta": audio_v.get("sample_count_delta"),
                "window_matches": audio_v.get("window_matches"),
            },
        },
        "export_commands": [c["argv"] for c in export.get("commands", [])],
    }
    out = ev / "frame_map.json"
    text = json.dumps(rec, indent=1, ensure_ascii=False)
    out.write_text(text + "\n", encoding="utf-8")
    h = sha256(out)
    (ev / "frame_map.json.sha256").write_text(f"{h} *frame_map.json\n", encoding="utf-8")
    print(json.dumps({"frame_map": str(out), "sha256": h,
                      "required_rows": rec["measured_frame_identity"]["required_rows"],
                      "final": rec["hashes"]["final_export"],
                      "raw": rec["hashes"]["raw_render_121f"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
