import os

gate_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_gate.py"
with open(gate_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Update event_fids in gate_shot_before_propagate to use canonical event_fids_for
old_gate_shot_ev = '''    ev_fids = set()
    for e in row.get("events", []):
        if isinstance(e, dict):
            if "frame" in e:
                ev_fids.add(int(e["frame"]))
            elif "f" in e:
                ev_fids.add(int(e["f"]) + 1)
    for c in row.get("contacts", []):
        if isinstance(c, dict) and "from" in c:
            ev_fids.add(int(c["from"]) + 1)  # r3 'from' 0-based -> fid 1-based
    for a in row["actors"]:
        for w in a["class_windows"]:
            if w["from"] > 1 and w["class"] in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev_fids.add(int(w["from"]))  # entry boundary = event (must have a key at/near it)'''

new_gate_shot_ev = '''    from r6_propagate import event_fids_for
    ev_fids = event_fids_for(sid, row)'''

assert src.count(old_gate_shot_ev) == 1
src = src.replace(old_gate_shot_ev, new_gate_shot_ev)

# 2. Update gate_batch_conformance to strictly reject unknown modes and enforce artifacts in final mode
old_batch_conf = '''def gate_batch_conformance(record: dict, mode: str = "engineering") -> bool:
    """Validate batch submission:
    - 'engineering' (G1): Q05, Q07 must be PASS; media Qs remain honestly UNKNOWN/FAIL until G2.
    - 'final' (G3): all 12 Qs must be PASS.
    """
    matrix = record.get("matrix", {})
    exp_keys = {f"Q{i:02d}" for i in range(1, 13)}
    if set(matrix.keys()) != exp_keys:
        raise GateBlock(f"MATRIX_KEYS {sorted(matrix.keys())}")
    for q, val in matrix.items():
        if val not in ("PASS", "FAIL", "UNKNOWN"):
            raise GateBlock(f"INVALID_VERDICT_VALUE {q}={val}")
    if mode == "engineering":
        if matrix.get("Q05") != "PASS" or matrix.get("Q07") != "PASS":
            raise GateBlock(f"ENGINEERING_BATCH_Q_NOT_PASS Q05={matrix.get('Q05')}, Q07={matrix.get('Q07')}")
        # Disallow false claims of media PASS before actual media rendering
        for mq in ("Q01", "Q04", "Q06", "Q09", "Q12"):
            if matrix.get(mq) == "PASS":
                raise GateBlock(f"PREMATURE_MEDIA_PASS_IN_ENGINEERING_BATCH {mq}")
    elif mode == "final":
        bad = {k: v for k, v in matrix.items() if v != "PASS"}
        if bad:
            raise GateBlock(f"FINAL_SUBMISSION_NOT_ALL_PASS {bad}")
    return True'''

new_batch_conf = '''def gate_batch_conformance(record: dict, mode: str = "engineering") -> bool:
    """Validate batch submission:
    - 'engineering' (G1): Q05, Q07 must be PASS; media Qs remain honestly UNKNOWN/FAIL until G2.
    - 'final' (G3): all 12 Qs must be PASS and all artifacts verified.
    """
    if mode not in ("engineering", "final"):
        raise GateBlock(f"UNKNOWN_BATCH_MODE: {mode}")
    matrix = record.get("matrix", {})
    exp_keys = {f"Q{i:02d}" for i in range(1, 13)}
    if set(matrix.keys()) != exp_keys:
        raise GateBlock(f"MATRIX_KEYS {sorted(matrix.keys())}")
    for q, val in matrix.items():
        if val not in ("PASS", "FAIL", "UNKNOWN"):
            raise GateBlock(f"INVALID_VERDICT_VALUE {q}={val}")
    if mode == "engineering":
        if matrix.get("Q05") != "PASS" or matrix.get("Q07") != "PASS":
            raise GateBlock(f"ENGINEERING_BATCH_Q_NOT_PASS Q05={matrix.get('Q05')}, Q07={matrix.get('Q07')}")
        # Disallow false claims of media PASS before actual media rendering
        for mq in ("Q01", "Q04", "Q06", "Q09", "Q12"):
            if matrix.get(mq) == "PASS":
                raise GateBlock(f"PREMATURE_MEDIA_PASS_IN_ENGINEERING_BATCH {mq}")
    elif mode == "final":
        bad = {k: v for k, v in matrix.items() if v != "PASS"}
        if bad:
            raise GateBlock(f"FINAL_SUBMISSION_NOT_ALL_PASS {bad}")
        # Final mode requires full artifact verification
        gate_submit(record)
    return True'''

assert src.count(old_batch_conf) == 1
src = src.replace(old_batch_conf, new_batch_conf)

with open(gate_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_gate.py successfully")
