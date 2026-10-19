import os

test_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\tests\test_g1_r1_correction.py"
with open(test_path, "r", encoding="utf-8") as f:
    src = f.read()

old_tpl_assign = '''        tpl_path.write_text(json.dumps(graph), encoding="utf-8")

        self.cache = importlib.import_module("r6_cache")'''

new_tpl_assign = '''        tpl_path.write_text(json.dumps(graph), encoding="utf-8")
        graph_mod = importlib.import_module("r6_graph")
        graph_mod.TPL = tpl_path

        self.cache = importlib.import_module("r6_cache")'''

assert src.count(old_tpl_assign) == 1
src = src.replace(old_tpl_assign, new_tpl_assign)

with open(test_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated graph_mod.TPL dynamically in setUp")
