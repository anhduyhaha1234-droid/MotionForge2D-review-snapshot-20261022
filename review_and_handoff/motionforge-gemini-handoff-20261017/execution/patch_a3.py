import os

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"

# 1. Patch r6_cotracker.py
cotracker_p = os.path.join(scripts_dir, "r6_cotracker.py")
with open(cotracker_p, "r", encoding="utf-8") as f:
    cotracker_src = f.read()

validator_func = '''
def validate_cotracker_tensors(tr: np.ndarray, vis: np.ndarray, expected_T: int, expected_N: int) -> tuple[bool, str]:
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
    return True, "ok"
'''

if "def validate_cotracker_tensors" not in cotracker_src:
    old_ckpt = "def ckpt():\n"
    new_ckpt = validator_func + "\n\n" + old_ckpt
    assert cotracker_src.count(old_ckpt) == 1
    cotracker_src = cotracker_src.replace(old_ckpt, new_ckpt)

old_loop_save = '''        wall = round(time.time() - t0, 1)
        np.save(OUTD / f"{sid}_{kind}_tracks.npy", tr)
        np.save(OUTD / f"{sid}_{kind}_vis.npy", vis)
        out[kind] = {"wall_s": wall, "T": int(tr.shape[0]), "N": int(tr.shape[1])}'''

new_loop_save = '''        wall = round(time.time() - t0, 1)
        ok, why = validate_cotracker_tensors(tr, vis, T, len(sq["pts"]))
        if not ok:
            raise SystemExit(f"COTRACKER_TENSOR_INVALID {sid} {kind}: {why}")
        np.save(OUTD / f"{sid}_{kind}_tracks.npy", tr)
        np.save(OUTD / f"{sid}_{kind}_vis.npy", vis)
        out[kind] = {"wall_s": wall, "T": int(tr.shape[0]), "N": int(tr.shape[1])}'''
assert cotracker_src.count(old_loop_save) == 1
cotracker_src = cotracker_src.replace(old_loop_save, new_loop_save)

old_ev_dir = '    ev_dir = K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572/evidence/cotracker"\n'
new_ev_dir = '    ev_dir = Path(os.environ.get("R6_COTRACKER_EV_DIR", OUTD))\n'
assert cotracker_src.count(old_ev_dir) == 1
cotracker_src = cotracker_src.replace(old_ev_dir, new_ev_dir)

old_paste_b = '        c.paste(_I.fromarray(b).resize((320, 180)), (x, 20 + 190)) if False else None\n'
new_paste_b = '        c.paste(_I.fromarray(b).resize((320, 180)), (x, 20 + 190))\n'
assert cotracker_src.count(old_paste_b) == 1
cotracker_src = cotracker_src.replace(old_paste_b, new_paste_b)

with open(cotracker_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(cotracker_src)
print("Patched r6_cotracker.py successfully")


# 2. Patch r6_propagate.py
prop_p = os.path.join(scripts_dir, "r6_propagate.py")
with open(prop_p, "r", encoding="utf-8") as f:
    prop_src = f.read()

old_ns = 'NS = K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"\n'
new_ns = 'NS = Path(os.environ.get("R6_PROPAGATE_NS", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))\n'
assert prop_src.count(old_ns) == 1
prop_src = prop_src.replace(old_ns, new_ns)

old_event_fids = '''def event_fids_for(sid: str, row: dict) -> set:
    ev = set()
    for e in row.get("events", []):
        if isinstance(e, dict) and "frame" in e:
            ev.add(int(e["frame"]))
    for c in row.get("contacts", []):
        if isinstance(c, dict) and "from" in c:
            ev.add(int(c["from"]) + 1)
    for a in row["actors"]:
        for w in a["class_windows"]:
            if w["from"] > 1 and w["class"] in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev.add(int(w["from"]))
    return ev'''

new_event_fids = '''def event_fids_for(sid: str, row: dict) -> set:
    ev = set()
    for e in row.get("events", []):
        if isinstance(e, dict):
            if "frame" in e:
                ev.add(int(e["frame"]))
            elif "f" in e:
                ev.add(int(e["f"]) + 1)
    for c in row.get("contacts", []):
        if isinstance(c, dict) and "from" in c:
            ev.add(int(c["from"]) + 1)
    for a in row.get("actors", []):
        for w in a.get("class_windows", []):
            if w.get("from", 0) > 1 and w.get("class") in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev.add(int(w["from"]))
    return ev'''
assert prop_src.count(old_event_fids) == 1
prop_src = prop_src.replace(old_event_fids, new_event_fids)

old_plan_runs = '''def plan_runs(key_fids: list, m: int) -> list:
    """Decompose [1..m] into runs whose internal spacing is uniform: consecutive runs split where
    the spacing between consecutive key fids changes."""
    seq = sorted(set(key_fids) | {1, m})
    runs = []
    cur = [seq[0]]
    for a, b in zip(seq, seq[1:]):
        d = b - a
        if len(cur) >= 2 and (cur[-1] - cur[-2]) != d:
            runs.append(cur)
            cur = [cur[-1]]
        cur.append(b)
    runs.append(cur)
    return runs'''

new_plan_runs = '''def plan_runs(key_fids: list, m: int, cuts: list | None = None) -> list:
    """Decompose [1..m] into runs whose internal spacing is uniform: consecutive runs split where
    the spacing between consecutive key fids changes, and never interpolate across hard cuts."""
    cut_set = set(cuts or [])
    seq = sorted(set(key_fids) | {1, m} | cut_set)
    runs = []
    cur = [seq[0]]
    for a, b in zip(seq, seq[1:]):
        d = b - a
        is_cut = (b in cut_set) or (a in cut_set and len(cur) >= 2)
        if len(cur) >= 2 and ((cur[-1] - cur[-2]) != d or is_cut):
            runs.append(cur)
            cur = [cur[-1]]
        cur.append(b)
    if cur not in runs:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]'''
assert prop_src.count(old_plan_runs) == 1
prop_src = prop_src.replace(old_plan_runs, new_plan_runs)

with open(prop_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(prop_src)
print("Patched r6_propagate.py successfully")


# 3. Patch r6_ledger.py
ledger_p = os.path.join(scripts_dir, "r6_ledger.py")
with open(ledger_p, "r", encoding="utf-8") as f:
    ledger_src = f.read()

old_sb_keys = '''        grid = json.loads((R5_SB / f"{sid}.json").read_text(encoding="utf-8"))
        fids = [k["fid"] for k in grid["keys"]]
        keys = []
        for fid in fids:'''

new_sb_keys = '''        grid = json.loads((R5_SB / f"{sid}.json").read_text(encoding="utf-8"))
        fids = [k["fid"] for k in grid["keys"]]
        ev_fids = set()
        for e in r.get("events", []):
            if isinstance(e, dict):
                if "f" in e:
                    ev_fids.add(int(e["f"]) + 1)
                elif "frame" in e:
                    ev_fids.add(int(e["frame"]))
        for c in r.get("contacts", []):
            if isinstance(c, dict) and "from" in c:
                ev_fids.add(int(c["from"]) + 1)
        for a in r.get("actors", []):
            for w in a.get("class_windows", []):
                if w.get("from", 0) > 1 and w.get("class") in ("VISIBLE", "PARTIALLY_VISIBLE"):
                    ev_fids.add(int(w["from"]))
        all_fids = sorted(set(fids) | {f for f in ev_fids if 1 <= f <= r["n"]})
        keys = []
        for fid in all_fids:'''
assert ledger_src.count(old_sb_keys) == 1
ledger_src = ledger_src.replace(old_sb_keys, new_sb_keys)

with open(ledger_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(ledger_src)
print("Patched r6_ledger.py successfully")


# 4. Patch r6_gate.py
gate_p = os.path.join(scripts_dir, "r6_gate.py")
with open(gate_p, "r", encoding="utf-8") as f:
    gate_src = f.read()

old_gate_events = '''    for e in row.get("events", []):
        if isinstance(e, dict) and "frame" in e:
            ev_fids.add(int(e["frame"]))'''

new_gate_events = '''    for e in row.get("events", []):
        if isinstance(e, dict):
            if "frame" in e:
                ev_fids.add(int(e["frame"]))
            elif "f" in e:
                ev_fids.add(int(e["f"]) + 1)'''
assert gate_src.count(old_gate_events) == 1
gate_src = gate_src.replace(old_gate_events, new_gate_events)

with open(gate_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(gate_src)
print("Patched r6_gate.py successfully")
