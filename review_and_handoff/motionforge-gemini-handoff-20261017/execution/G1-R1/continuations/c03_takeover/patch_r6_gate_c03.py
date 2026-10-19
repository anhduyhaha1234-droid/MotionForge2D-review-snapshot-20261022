import os

gate_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_gate.py"
with open(gate_path, "r", encoding="utf-8") as f:
    src_gate = f.read()

# Update gate_batch_conformance
old_gate_batch = '''def gate_batch_conformance(record: dict, mode: str = "engineering") -> bool:
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

new_gate_batch = '''def gate_batch_conformance(record: dict, mode: str = "engineering") -> bool:
    """Validate batch submission:
    - 'engineering' (G1): Q05, Q07 must be PASS with verifiable supporting proof; media Qs remain honestly UNKNOWN/FAIL until G2.
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
        # Supporting proof validation: record must contain verifiable proof or evidence
        proof = record.get("proof") or record.get("evidence")
        if not proof or not isinstance(proof, dict):
            raise GateBlock("ENGINEERING_BATCH_NO_PROOF: missing supporting proof")
        if proof.get("Q05", {}).get("verdict") != "PASS" or proof.get("Q07", {}).get("verdict") != "PASS":
            raise GateBlock("ENGINEERING_BATCH_PROOF_INVALID: Q05 and Q07 must have verified PASS evidence")
    elif mode == "final":
        bad = {k: v for k, v in matrix.items() if v != "PASS"}
        if bad:
            raise GateBlock(f"FINAL_SUBMISSION_NOT_ALL_PASS {bad}")
        # Final mode requires full artifact verification
        gate_submit(record)
    return True'''

assert src_gate.count(old_gate_batch) == 1, "old_gate_batch not found"
src_gate = src_gate.replace(old_gate_batch, new_gate_batch)
with open(gate_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src_gate)
print("Updated r6_gate.py successfully")
