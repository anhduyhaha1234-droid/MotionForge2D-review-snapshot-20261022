import os

a4_test_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\tests\test_gemini_a4_evidence_conformance.py"
with open(a4_test_path, "r", encoding="utf-8") as f:
    src = f.read()

old_test_g1 = '''        res = self.gate.gate_batch_conformance({"matrix": valid_matrix}, mode="engineering")
        self.assertTrue(res)'''

new_test_g1 = '''        # Supporting proof is required in engineering batch
        with self.assertRaises(self.gate.GateBlock) as cm_no_proof:
            self.gate.gate_batch_conformance({"matrix": valid_matrix}, mode="engineering")
        self.assertIn("ENGINEERING_BATCH_NO_PROOF", str(cm_no_proof.exception))

        # With verified proof, engineering batch conforms
        res = self.gate.gate_batch_conformance({"matrix": valid_matrix, "proof": {"Q05": {"verdict": "PASS"}, "Q07": {"verdict": "PASS"}}}, mode="engineering")
        self.assertTrue(res)'''

assert src.count(old_test_g1) == 1
src = src.replace(old_test_g1, new_test_g1)

with open(a4_test_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated test_gemini_a4_evidence_conformance.py to assert proof requirement")
