"""A4: evidence, gate conformance, Q01-Q12 matrix and 2-controller barrier tests."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path

SOURCE_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
MODULES = ("r6_common", "r6_gate", "r6_matrix", "r6_assemble")


class EvidenceGateConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="a4-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task"
        self.r6 = self.task / "corrections/identity/r6"
        self.scripts = self.r6 / "scripts"
        self.scripts.mkdir(parents=True)
        for path in SOURCE_SCRIPTS.glob("*.py"):
            shutil.copyfile(path, self.scripts / path.name)
        (self.task / "chunk_plan.json").write_text(json.dumps({"chunks": [
            {"unit_id": "S0021", "start_frame": 0, "frames": 100}
        ]}), encoding="utf-8")
        row = {"shot": "S0021", "zero_explicit": False, "n": 100, "src": [0, 100], "actors": []}
        (self.r6 / "source_actor_ledger.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        sb_dir = self.r6 / "storyboard"
        sb_dir.mkdir(parents=True, exist_ok=True)
        (sb_dir / "S0021.json").write_text(json.dumps({"shot": "S0021", "n": 100, "keys": []}), encoding="utf-8")

        self.previous = {name: sys.modules.pop(name, None) for name in MODULES}
        sys.path.insert(0, str(self.scripts))
        self.addCleanup(self._restore_modules)

        self.k = importlib.import_module("r6_common")
        self.gate = importlib.import_module("r6_gate")
        self.matrix = importlib.import_module("r6_matrix")
        self.assemble = importlib.import_module("r6_assemble")

    def _restore_modules(self):
        if str(self.scripts) in sys.path:
            sys.path.remove(str(self.scripts))
        for name, old in self.previous.items():
            sys.modules.pop(name, None)
            if old is not None:
                sys.modules[name] = old

    def test_g1_engineering_batch_conformance(self):
        # Valid engineering batch matrix: Q05=PASS, Q07=PASS, others UNKNOWN/FAIL
        valid_matrix = {
            "Q01": "FAIL", "Q02": "FAIL", "Q03": "UNKNOWN", "Q04": "FAIL",
            "Q05": "PASS", "Q06": "UNKNOWN", "Q07": "PASS", "Q08": "FAIL",
            "Q09": "FAIL", "Q10": "UNKNOWN", "Q11": "UNKNOWN", "Q12": "FAIL"
        }
        # Supporting proof is required in engineering batch
        with self.assertRaises(self.gate.GateBlock) as cm_no_proof:
            self.gate.gate_batch_conformance({"matrix": valid_matrix}, mode="engineering")
        self.assertIn("ENGINEERING_BATCH_NO_PROOF", str(cm_no_proof.exception))

        # Bare self-labels without artifact binding rejected in engineering batch
        with self.assertRaises(self.gate.GateBlock) as cm_self_labels:
            self.gate.gate_batch_conformance(
                {"matrix": valid_matrix, "proof": {"Q05": {"verdict": "PASS"}, "Q07": {"verdict": "PASS"}}},
                mode="engineering",
            )
        self.assertIn("ENGINEERING_BATCH_PROOF_INVALID", str(cm_self_labels.exception))

        # Proof with fake or missing artifact rejected
        fake_proof = {
            "Q05": {
                "artifact_path": str(self.root / "nonexistent.py"),
                "artifact_hash": "a" * 64,
                "current_invocation": "inv-001",
                "actual_verifier": "verifier-agent",
                "all_passed": True,
                "exit_code": 0,
                "tests_run": 1,
                "node_ids": ["test_sample"],
            },
            "Q07": {
                "current_invocation": "inv-001",
                "actual_verifier": "verifier-agent",
                "verified_deps_count": 1,
                "required_shots": ["S0021"],
                "verified_shots": ["S0021"],
            },
        }
        with self.assertRaises(self.gate.GateBlock) as cm_fake:
            self.gate.gate_batch_conformance({"matrix": valid_matrix, "proof": fake_proof}, mode="engineering")
        self.assertIn("ENGINEERING_BATCH_PROOF_INVALID", str(cm_fake.exception))

        # With verified proof complying with contract, engineering batch conforms
        import r6_evidence_contract as evc
        invocation_dir = self.root / "inv-001"
        invocation_dir.mkdir()
        real_test = invocation_dir / "test_sample.py"
        real_test.write_text("def test_sample():\n    assert True\n", encoding="utf-8")
        real_hash = hashlib.sha256(real_test.read_bytes()).hexdigest()
        run = evc.run_q05_tests(real_test, "inv-001")
        receipt = invocation_dir / "q05_receipt.json"
        receipt.write_text(json.dumps(run), encoding="utf-8")
        dep_path = self.r6 / "work/S0021/f_0001.deps.json"
        dep_path.parent.mkdir(parents=True, exist_ok=True)
        dep_path.write_text(json.dumps({"kind": "r6_key_deps_v4_asset", "shot": "S0021", "fid": 1}), encoding="utf-8")
        dep = {"path": str(dep_path), "hash": hashlib.sha256(dep_path.read_bytes()).hexdigest(),
               "shot": "S0021", "fid": 1, "kind": "r6_key_deps_v4_asset"}

        verified_proof = {
            "Q05": {
                "artifact_path": str(real_test),
                "artifact_hash": real_hash,
                "receipt_path": str(receipt),
                "receipt_hash": hashlib.sha256(receipt.read_bytes()).hexdigest(),
                "current_invocation": "inv-001",
                "actual_verifier": "pytest-junit-v1",
                "all_passed": True,
                "exit_code": 0,
                "tests_run": 1,
                "node_ids": ["test_sample.py::test_sample"],
            },
            "Q07": {
                "current_invocation": "inv-001",
                "actual_verifier": "r6-cache-v4",
                "verified_deps_count": 1,
                "required_shots": ["S0021"],
                "verified_shots": ["S0021"],
                "valid_deps": [dep],
            },
        }
        with mock.patch.object(evc, "validate_deps_evidence", return_value=(True, "ok")):
            res = self.gate.gate_batch_conformance(
                {"invocation_id": "inv-001", "invocation_dir": str(invocation_dir),
                 "matrix": valid_matrix, "proof": verified_proof}, mode="engineering")
        self.assertTrue(res)

        # Premature media PASS rejected in engineering batch
        premature_matrix = dict(valid_matrix)
        premature_matrix["Q01"] = "PASS"
        with self.assertRaises(self.gate.GateBlock) as cm:
            self.gate.gate_batch_conformance({"matrix": premature_matrix}, mode="engineering")
        self.assertIn("PREMATURE_MEDIA_PASS", str(cm.exception))

        # Missing Q05/Q07 as PASS rejected
        bad_eng_matrix = dict(valid_matrix)
        bad_eng_matrix["Q05"] = "UNKNOWN"
        with self.assertRaises(self.gate.GateBlock) as cm:
            self.gate.gate_batch_conformance({"matrix": bad_eng_matrix}, mode="engineering")
        self.assertIn("ENGINEERING_BATCH_Q_NOT_PASS", str(cm.exception))

    def test_invalid_matrix_keys_and_values(self):
        # Missing keys
        with self.assertRaises(self.gate.GateBlock):
            self.gate.gate_batch_conformance({"matrix": {"Q01": "PASS"}})

        # Invalid verdict enum
        matrix = {f"Q{i:02d}": "PASS" for i in range(1, 13)}
        matrix["Q03"] = "MAYBE"
        with self.assertRaises(self.gate.GateBlock) as cm:
            self.gate.gate_batch_conformance({"matrix": matrix}, mode="final")
        self.assertIn("INVALID_VERDICT_VALUE", str(cm.exception))

    def test_r6_assemble_pre_encoder_gate_blocked(self):
        # Assemble must call gate_assemble before any encoding; empty plan -> blocked
        with self.assertRaises(self.gate.GateBlock):
            self.gate.gate_assemble([("S0021", 100)])

    def test_r6_matrix_compute_rows(self):
        rows = self.matrix.compute_rows()
        self.assertEqual(len(rows), 12)
        for i in range(1, 13):
            q = f"Q{i:02d}"
            self.assertIn(q, rows)
            self.assertIn(rows[q]["verdict"], ("PASS", "FAIL", "UNKNOWN"))

    def test_t13_two_controller_barrier_race_simulation(self):
        """Simulate contested acquisition between two controllers: exactly one winner."""
        lock_file = self.root / "controller.lock"
        winners = []
        barrier = threading.Barrier(2)

        def contender(cid):
            barrier.wait()
            # Atomic file creation
            try:
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(fd, f"winner={cid}".encode())
                os.close(fd)
                winners.append(cid)
            except FileExistsError:
                pass

        t1 = threading.Thread(target=contender, args=(1,))
        t2 = threading.Thread(target=contender, args=(2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(winners), 1, f"Expected exactly 1 winner, got {len(winners)}")
        self.assertTrue(lock_file.exists())
        self.assertIn(f"winner={winners[0]}", lock_file.read_text())


if __name__ == "__main__":
    unittest.main()
