import os

cotracker_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cotracker.py"
with open(cotracker_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Add argparse and math to imports
old_imp = "import json, os, sys, time\n"
new_imp = "import argparse, json, math, os, sys, time\n"
assert src.count(old_imp) == 1
src = src.replace(old_imp, new_imp)

# 2. Update validate_cotracker_tensors
old_val = '''def validate_cotracker_tensors(tr: np.ndarray, vis: np.ndarray, expected_T: int, expected_N: int) -> tuple[bool, str]:
    """Validate cotracker outputs: (T,N,2) float32, (T,N) bool/uint8, finite, within canvas bounds."""
    if not isinstance(tr, np.ndarray) or not isinstance(vis, np.ndarray):
        return False, "tracks and vis must be numpy arrays"
    if tr.shape != (expected_T, expected_N, 2):
        return False, f"tracks shape mismatch: {tr.shape} vs {(expected_T, expected_N, 2)}"
    if vis.shape != (expected_T, expected_N):
        return False, f"vis shape mismatch: {vis.shape} vs {(expected_T, expected_N)}"
    if not np.isfinite(tr).all():
        return False, "tracks contain non-finite values (NaN or Inf)"
    if (tr[..., 0] < -32).any() or (tr[..., 0] > 672).any() or (tr[..., 1] < -32).any() or (tr[..., 1] > 400).any():
        return False, "tracks coordinates far outside canvas bounds"
    return True, "ok"'''

new_val = '''def validate_cotracker_tensors(tr: np.ndarray, vis: np.ndarray, expected_T: int, expected_N: int) -> tuple[bool, str]:
    """Validate cotracker outputs: (T,N,2) float32, (T,N) bool/uint8/float in [0,1], non-empty, finite, within canvas bounds."""
    if expected_T <= 0 or expected_N <= 0:
        return False, "expected_T and expected_N must be strictly positive"
    if not isinstance(tr, np.ndarray) or not isinstance(vis, np.ndarray):
        return False, "tracks and vis must be numpy arrays"
    if tr.size == 0 or vis.size == 0 or tr.shape[0] == 0 or tr.shape[1] == 0:
        return False, "tracks and vis arrays must not be empty"
    if tr.shape != (expected_T, expected_N, 2):
        return False, f"tracks shape mismatch: {tr.shape} vs {(expected_T, expected_N, 2)}"
    if vis.shape != (expected_T, expected_N):
        return False, f"vis shape mismatch: {vis.shape} vs {(expected_T, expected_N)}"
    if not np.isfinite(tr).all():
        return False, "tracks contain non-finite values (NaN or Inf)"
    if not np.isfinite(vis).all():
        return False, "vis contains non-finite values (NaN or Inf)"
    if vis.dtype != bool:
        if (vis < 0.0).any() or (vis > 1.0).any():
            return False, "vis values must be binary or within [0, 1] range"
    if (tr[..., 0] < -32).any() or (tr[..., 0] > 672).any() or (tr[..., 1] < -32).any() or (tr[..., 1] > 400).any():
        return False, "tracks coordinates far outside canvas bounds"
    return True, "ok"'''

assert src.count(old_val) == 1
src = src.replace(old_val, new_val)

# 3. Update window drift calculation to eliminate NaN completely
old_win_calc = '''    d = np.linalg.norm(tr_g - tr_s, axis=-1)  # (T,N)
    both = np.logical_and(np.load(OUTD / f"{sid}_source_vis.npy") > 0,
                          np.load(OUTD / f"{sid}_r6_vis.npy") > 0)  # (T,N)
    dm = float(d[both].mean()) if both.any() else None
    # F04 windows: from events (f) and contacts (from, 0-based -> fid from+1); non-empty required.
    windows = []
    for e in events:
        f0 = int(e.get("f", 1)) + 1  # event f is 0-based in the map; fid = f+1
        f1 = min(T, f0 + 12)
        windows.append({"kind": "event", "event": e.get("event", "?"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": float(np.nanmean(d[max(0, f0 - 1):min(T, f0 + 3)][both[max(0, f0 - 1):min(T, f0 + 3)]])) if both.any() else None})
    for c in contacts:
        f0 = int(c.get("from", 0)) + 1  # 0-based -> fid
        f1 = min(T, f0 + 12)
        windows.append({"kind": "contact", "entity": c.get("entity"), "prop": c.get("prop"),
                        "part": c.get("part"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": float(np.nanmean(d[max(0, f0 - 1):min(T, f0 + 3)][both[max(0, f0 - 1):min(T, f0 + 3)]])) if both.any() else None})'''

new_win_calc = '''    d = np.linalg.norm(tr_g - tr_s, axis=-1)  # (T,N)
    both = np.logical_and(np.load(OUTD / f"{sid}_source_vis.npy") > 0,
                          np.load(OUTD / f"{sid}_r6_vis.npy") > 0)  # (T,N)
    dm = float(d[both].mean()) if both.any() and math.isfinite(float(d[both].mean())) else None

    def _calc_window_drift(beg_f, end_f):
        idx_beg = max(0, beg_f - 1)
        idx_end = min(T, end_f)
        if idx_beg >= idx_end:
            return None
        w_both = both[idx_beg:idx_end]
        if not w_both.any():
            return None
        w_diff = d[idx_beg:idx_end][w_both]
        if w_diff.size == 0:
            return None
        val = float(np.mean(w_diff))
        return val if math.isfinite(val) else None

    # F04 windows: from events (f) and contacts (from, 0-based -> fid from+1); non-empty required.
    windows = []
    for e in events:
        f0 = int(e.get("f", 1)) + 1  # event f is 0-based in the map; fid = f+1
        f1 = min(T, f0 + 12)
        windows.append({"kind": "event", "event": e.get("event", "?"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": _calc_window_drift(f0, min(T, f0 + 3))})
    for c in contacts:
        f0 = int(c.get("from", 0)) + 1  # 0-based -> fid
        f1 = min(T, f0 + 12)
        windows.append({"kind": "contact", "entity": c.get("entity"), "prop": c.get("prop"),
                        "part": c.get("part"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": _calc_window_drift(f0, min(T, f0 + 3))})'''

assert src.count(old_win_calc) == 1
src = src.replace(old_win_calc, new_win_calc)

with open(cotracker_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_cotracker.py with argparse, strict tensor contract & window drift checks successfully")
