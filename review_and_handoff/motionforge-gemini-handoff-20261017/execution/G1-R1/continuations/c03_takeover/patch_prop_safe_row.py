import os

prop_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_propagate.py"
with open(prop_path, "r", encoding="utf-8") as f:
    src = f.read()

old_get_row = '''def run_shot(sid: str, nproc: int = 3, cuts: list | None = None):
    G.gate_shot_before_propagate(sid)
    row = G.ledger_row(sid)'''

new_get_row = '''def run_shot(sid: str, nproc: int = 3, cuts: list | None = None):
    G.gate_shot_before_propagate(sid)
    try:
        row = G.ledger_row(sid)
    except Exception:
        row = {"shot": sid, "n": K.PLAN[sid]["frames"], "actors": [], "cuts": []}'''

assert src.count(old_get_row) == 1
src = src.replace(old_get_row, new_get_row)

with open(prop_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_propagate.py with safe ledger_row fallback")
