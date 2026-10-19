"""Independent proof that a remuxed audio track is the source film's [55,59) window.

Two decodes are compared as raw PCM (signed 16-bit LE, 2 ch, 44100):
  X = the candidate file's audio stream, decoded whole
  Y = the SOURCE FILM decoded with -af atrim=start=55:end=59, i.e. a
      sample-accurate cut that does not go through the packet-copy path at all

Reported: sample counts, MAE at zero lag, MAE at the best lag inside a +/-4096
sample search window, and the best lag itself.  A correct window gives
best_lag == 0 and MAE ~ 0.  A wrong window (the R3 file) is run as a
non-vacuous control: it must NOT come out clean.

usage:
  python w2_audio_verify.py <candidate.mp4> <film.mp4> [out.json]
      [--start 55.000] [--end 59.000]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SR = 44100
CH = 2


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def decode_pcm(args: list[str]) -> bytes:
    cmd = ["ffmpeg", "-v", "error", *args, "-f", "s16le", "-acodec", "pcm_s16le",
           "-ac", str(CH), "-ar", str(SR), "-"]
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout


def to_samples(buf: bytes):
    import numpy as np
    if len(buf) % 4:
        buf = buf[: len(buf) - (len(buf) % 4)]
    return np.frombuffer(buf, dtype="<i2").reshape(-1, CH).astype("float32")


def main() -> int:
    cand = _p(sys.argv[1])
    film = _p(sys.argv[2])
    start = float(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 55.0
    end = float(sys.argv[sys.argv.index("--end") + 1]) if "--end" in sys.argv else 59.0

    x = to_samples(decode_pcm(["-i", str(cand)]))
    y = to_samples(decode_pcm(["-i", str(film), "-af",
                               f"atrim=start={start:.6f}:end={end:.6f},asetpts=N/SR/TB"]))

    rec = {
        "candidate": str(cand),
        "film": str(film),
        "window_s": [start, end],
        "candidate_samples": int(x.shape[0]),
        "film_window_samples": int(y.shape[0]),
        "film_window_duration_s": round(y.shape[0] / SR, 6),
        "candidate_duration_s": round(x.shape[0] / SR, 6),
        "sample_count_delta": int(x.shape[0] - y.shape[0]),
    }

    n = min(x.shape[0], y.shape[0])
    best_lag, best_mae = None, None
    if n > 0:
        import numpy as np
        a = x[:n]
        b = y[:n]
        rec["mae_lag0"] = round(float(np.abs(a - b).mean()), 6)
        # zero-lag identity fraction at 16-bit resolution
        rec["pct_samples_identical_lag0"] = round(
            float((a == b).all(axis=1).mean() * 100.0), 4)
        for lag in range(-4096, 4097):
            if lag >= 0:
                aa, bb = a[: n - lag] if lag else a, b[lag:]
            else:
                aa, bb = a[-lag:], b[: n + lag]
            if aa.shape[0] < 1000:
                continue
            m = float(np.abs(aa - bb).mean())
            if best_mae is None or m < best_mae:
                best_mae, best_lag = m, lag
        rec["best_lag_samples"] = best_lag
        rec["best_lag_ms"] = round(best_lag / SR * 1000.0, 4) if best_lag is not None else None
        rec["mae_at_best_lag"] = round(best_mae, 6)
    # Declared tolerance: one AAC frame (1024 samples) of extra tail is allowed,
    # because a whole-packet copy cannot end mid-frame; anything beyond that, or
    # any non-zero best lag, means the window is NOT the source window.
    rec["declared_tolerance_samples"] = 1024
    rec["window_matches"] = bool(
        rec.get("best_lag_samples") == 0
        and rec.get("mae_lag0") is not None and rec["mae_lag0"] < 1.0
        and 0 <= rec.get("sample_count_delta", 10 ** 9) <= 1024)

    text = json.dumps(rec, indent=1, ensure_ascii=False)
    if "--out" in sys.argv:
        _p(sys.argv[sys.argv.index("--out") + 1]).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
