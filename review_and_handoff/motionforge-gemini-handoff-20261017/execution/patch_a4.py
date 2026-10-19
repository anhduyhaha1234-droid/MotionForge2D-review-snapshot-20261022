import os

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"

# 1. Patch r6_assemble.py
asm_p = os.path.join(scripts_dir, "r6_assemble.py")
with open(asm_p, "r", encoding="utf-8") as f:
    asm_src = f.read()

old_asm_ns = 'NS = K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"\n'
new_asm_ns = 'NS = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))\n'
assert asm_src.count(old_asm_ns) == 1
asm_src = asm_src.replace(old_asm_ns, new_asm_ns)

with open(asm_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(asm_src)
print("Patched r6_assemble.py successfully")


# 2. Patch r6_matrix.py
mat_p = os.path.join(scripts_dir, "r6_matrix.py")
with open(mat_p, "r", encoding="utf-8") as f:
    mat_src = f.read()

old_mat_ns = 'NS = K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"\n'
new_mat_ns = 'NS = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))\n'
assert mat_src.count(old_mat_ns) == 1
mat_src = mat_src.replace(old_mat_ns, new_mat_ns)

with open(mat_p, "w", encoding="utf-8", newline="\n") as f:
    f.write(mat_src)
print("Patched r6_matrix.py successfully")


# 3. Patch r6_gate.py
gate_p = os.path.join(scripts_dir, "r6_gate.py")
with open(gate_p, "r", encoding="utf-8") as f:
    gate_src = f.read()

batch_func = '''

def gate_batch_conformance(record: dict, mode: str = "engineering") -> bool:
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
    return True
'''

if "def gate_batch_conformance" not in gate_src:
    gate_src = gate_src.rstrip() + batch_func + "\n"
    with open(gate_p, "w", encoding="utf-8", newline="\n") as f:
        f.write(gate_src)
    print("Patched r6_gate.py successfully with gate_batch_conformance")
