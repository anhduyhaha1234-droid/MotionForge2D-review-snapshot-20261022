import os

test_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\tests\test_g1_r1_correction.py"
with open(test_path, "r", encoding="utf-8") as f:
    src = f.read()

old_imp = "import unittest\n"
new_imp = "import unittest\nfrom unittest import mock\n"
assert src.count(old_imp) == 1
src = src.replace(old_imp, new_imp)

with open(test_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated test_g1_r1_correction.py with mock import")
