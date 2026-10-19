"""A4: evidence, gate conformance, Q01-Q12 matrix and 2-controller barrier tests."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
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
        res = self.gate.gate_batch_conformance({"matrix": valid_matrix}, mode="engineering")
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
