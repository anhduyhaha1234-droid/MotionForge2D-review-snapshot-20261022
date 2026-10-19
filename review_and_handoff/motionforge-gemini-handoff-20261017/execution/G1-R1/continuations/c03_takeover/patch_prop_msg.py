import os

prop_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_propagate.py"
with open(prop_path, "r", encoding="utf-8") as f:
    src = f.read()

old_err = 'raise RuntimeError(f"run {ri} expected {expect} frames, got {len(frames)}: {[f.name for f in frames]}")'
new_err = 'raise RuntimeError(f"run {ri} partial/extra frames {len(frames)}/{expect}: {[f.name for f in frames]}")'

assert src.count(old_err) == 1, "old_err not found"
src = src.replace(old_err, new_err)

with open(prop_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_propagate.py error message to include 'partial'")
