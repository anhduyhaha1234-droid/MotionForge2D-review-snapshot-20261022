import os

ledger_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_ledger.py"
with open(ledger_path, "r", encoding="utf-8") as f:
    src = f.read()

old_sb_ev = '''        ev_fids = set()
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
        all_fids = sorted(set(fids) | {f for f in ev_fids if 1 <= f <= r["n"]})'''

new_sb_ev = '''        from r6_propagate import event_fids_for
        ev_fids = event_fids_for(sid, r)
        all_fids = sorted(set(fids) | ev_fids)'''

assert src.count(old_sb_ev) == 1
src = src.replace(old_sb_ev, new_sb_ev)

with open(ledger_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_ledger.py with canonical event_fids_for successfully")
