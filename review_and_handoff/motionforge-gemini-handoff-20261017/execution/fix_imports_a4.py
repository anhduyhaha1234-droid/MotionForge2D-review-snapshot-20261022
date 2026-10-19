import os

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"

# 1. Fix r6_matrix.py
mat_p = os.path.join(scripts_dir, "r6_matrix.py")
with open(mat_p, "r", encoding="utf-8") as f:
    mat_src = f.read()

old_mat_imp = "import hashlib, json, sys, time\n"
new_mat_imp = "import hashlib, json, os, sys, time\n"
assert mat_src.count(old_mat_imp) == 1
mat_src = mat_src.replace(old_mat_imp, new_mat_imp)
with open(mat_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(mat_src)

# 2. Fix r6_assemble.py
asm_p = os.path.join(scripts_dir, "r6_assemble.py")
with open(asm_p, "r", encoding="utf-8") as f:
    asm_src = f.read()

old_asm_imp = "import json, shutil, sys, time\n"
new_asm_imp = "import json, os, shutil, sys, time\n"
assert asm_src.count(old_asm_imp) == 1
asm_src = asm_src.replace(old_asm_imp, new_asm_imp)
with open(asm_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(asm_src)

print("Added import os to r6_matrix.py and r6_assemble.py successfully")
