import os

cotracker_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cotracker.py"
with open(cotracker_path, "r", encoding="utf-8") as f:
    src = f.read()

old_win_block = '''    # F04 windows: from events (f) and contacts (from, 0-based -> fid from+1); non-empty required.
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

new_win_block = '''    # Canonical event & contact parsing using r6_event_contract
    import r6_event_contract as EC
    windows = []
    for e in events:
        try:
            f0 = EC.parse_event_fid(e, T, sid)
        except ValueError as exc:
            raise SystemExit(f"COTRACKER_INVALID_EVENT {sid}: {exc}")
        f1 = min(T, f0 + 12)
        windows.append({"kind": "event", "event": e.get("event", "?"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": _calc_window_drift(f0, min(T, f0 + 3))})
    for c in contacts:
        try:
            fid_from, fid_to = EC.parse_contact_fids(c, T, sid)
        except ValueError as exc:
            raise SystemExit(f"COTRACKER_INVALID_CONTACT {sid}: {exc}")
        f0 = fid_from
        f1 = fid_to if fid_to is not None else min(T, f0 + 12)
        windows.append({"kind": "contact", "entity": c.get("entity"), "prop": c.get("prop"),
                        "part": c.get("part"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": _calc_window_drift(f0, min(T, f0 + 3))})'''

assert src.count(old_win_block) == 1, "old_win_block not found"
src = src.replace(old_win_block, new_win_block)

with open(cotracker_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_cotracker.py with canonical event/contact parsing successfully")
