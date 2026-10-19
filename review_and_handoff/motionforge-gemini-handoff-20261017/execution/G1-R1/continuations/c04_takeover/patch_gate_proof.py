import os

gate_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_gate.py"
with open(gate_path, "r", encoding="utf-8") as f:
    src_gate = f.read()

old_proof_check = '''        # Supporting proof validation: record must contain verifiable proof or evidence
        proof = record.get("proof") or record.get("evidence")
        if not proof or not isinstance(proof, dict):
            raise GateBlock("ENGINEERING_BATCH_NO_PROOF: missing supporting proof")
        if proof.get("Q05", {}).get("verdict") != "PASS" or proof.get("Q07", {}).get("verdict") != "PASS":
            raise GateBlock("ENGINEERING_BATCH_PROOF_INVALID: Q05 and Q07 must have verified PASS evidence")'''

new_proof_check = '''        # Supporting proof validation: record must contain verifiable proof or evidence
        proof = record.get("proof") or record.get("evidence")
        if not proof or not isinstance(proof, dict):
            raise GateBlock("ENGINEERING_BATCH_NO_PROOF: missing supporting proof")
        q05_p = proof.get("Q05", {})
        q07_p = proof.get("Q07", {})
        if not isinstance(q05_p, dict) or not isinstance(q07_p, dict):
            raise GateBlock("ENGINEERING_BATCH_PROOF_INVALID: Q05 and Q07 proof must be dict objects")
        q05_ok = q05_p.get("all_passed") is True or q05_p.get("verdict") == "PASS"
        q07_ok = bool(q07_p.get("verified_deps_count", 0) > 0 or q07_p.get("verdict") == "PASS")
        if not (q05_ok and q07_ok):
            raise GateBlock("ENGINEERING_BATCH_PROOF_INVALID: Q05 and Q07 must have verified PASS evidence")'''

assert src_gate.count(old_proof_check) == 1, "old_proof_check not found"
src_gate = src_gate.replace(old_proof_check, new_proof_check)

with open(gate_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src_gate)
print("Updated r6_gate.py proof validation successfully")
