#!/usr/bin/env python
"""Lag-scan a candidate against a reference to tell an OFFSET from a CONTENT mismatch.

Use when a validator/comparator reports a negative or near-zero similarity score and
you need to know whether the artifact is wrong or merely shifted in time.

    python content_compare_lag_scan.py <candidate> <reference> [max_lag_ms] [window_sec]

Prints: sample counts, RMS/peak, best alignment (lag + correlation), and a
SELF-CONTROL of the reference against itself. The self-control is not optional: if it
does not reach ~1.0 the measurement path is broken and no verdict from it is valid.

Decoding is mono s16le at 48 kHz via ffmpeg -- adjust SR / channels for other media.
Exit code is always 0; read the numbers, don't gate on rc.
"""
from __future__ import annotations

import struct
import subprocess
import sys

FFMPEG = "ffmpeg"
SR = 48000


def decode(path: str, seconds: float = 12.0) -> list[float]:
    """Decode the first audio stream to mono float samples."""
    cmd = [FFMPEG, "-v", "error", "-i", path, "-map", "0:a:0", "-t", str(seconds),
           "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // 2
    return [s / 32768.0 for s in struct.unpack(f"<{n}h", raw[: n * 2])]


def rms(xs: list[float]) -> float:
    return (sum(x * x for x in xs) / len(xs)) ** 0.5 if xs else 0.0


def corr(a: list[float], b: list[float], lag: int, win: int) -> float:
    """Pearson correlation of a[lag:lag+win] against b[0:win] (zero-lag if lag==0)."""
    xa = a[lag: lag + win]
    xb = b[:win]
    n = min(len(xa), len(xb))
    if n < 2:
        return float("nan")
    xa, xb = xa[:n], xb[:n]
    ma, mb = sum(xa) / n, sum(xb) / n
    va = sum((v - ma) ** 2 for v in xa) ** 0.5
    vb = sum((v - mb) ** 2 for v in xb) ** 0.5
    if va == 0 or vb == 0:
        return float("nan")
    return sum((xa[i] - ma) * (xb[i] - mb) for i in range(n)) / (va * vb)


def sweep(primary: list[float], other: list[float], max_lag_ms: int, win: int) -> tuple:
    best = (None, -2.0)
    for lag_ms in range(max_lag_ms):
        lag = int(SR * lag_ms / 1000)
        if lag + win > len(primary):
            break
        c = corr(primary, other, lag, win)
        if c == c and c > best[1]:
            best = (lag_ms, c)
    return best


def main() -> int:
    cand_path, ref_path = sys.argv[1], sys.argv[2]
    max_lag_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    win_sec = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0

    cand, ref = decode(cand_path), decode(ref_path)
    win = int(SR * win_sec)

    print(f"candidate={cand_path}")
    print(f"  samples={len(cand)} rms={rms(cand):.1f} peak={max(abs(v) for v in cand):.3f}")
    print(f"reference={ref_path}")
    print(f"  samples={len(ref)} rms={rms(ref):.1f} peak={max(abs(v) for v in ref):.3f}")

    lag_ms, c = sweep(cand, ref, max_lag_ms, win)
    print(f"best_alignment: lag={lag_ms}ms  correlation={c:+.4f}")

    print("lag sweep (the comparator's own verdict is the lag=0 row):")
    for probe_ms in (0, 1, 2, 5, 10):
        if probe_ms >= max_lag_ms:
            continue
        print(f"  lag={probe_ms:>2}ms corr={corr(cand, ref, int(SR * probe_ms / 1000), win):+.4f}")

    ctrl_ms, ctrl = sweep(ref, ref, max_lag_ms, win)
    print(f"SELF-CONTROL (reference vs itself): lag={ctrl_ms}ms correlation={ctrl + 0:.4f}")
    if not (ctrl > 0.99):
        print("WARNING: self-control did not reach ~1.0 -- the measurement path is "
              "broken; do NOT read the candidate numbers as a verdict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
