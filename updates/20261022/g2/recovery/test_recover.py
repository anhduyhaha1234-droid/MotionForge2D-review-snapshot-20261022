"""Bounded negative-first tests for the exact-byte G2-B2 vault."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

import recover as R


class RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = R.WRITE_ROOT / ("fixture-" + uuid4().hex)
        self.scratch.mkdir()

    def tearDown(self) -> None:
        parent = R.WRITE_ROOT.resolve(strict=True)
        target = self.scratch.resolve(strict=True)
        if target.parent != parent or not target.name.startswith("fixture-"):
            raise AssertionError(f"fixture cleanup escaped write-set: {target}")
        shutil.rmtree(target)

    def test_01_tampered_source_refused_before_copy(self) -> None:
        bad = self.scratch / "ledger.jsonl"
        bad.write_bytes(R.SOURCES[0].path.read_bytes() + b"x")
        specs = (replace(R.SOURCES[0], path=bad), *R.SOURCES[1:])
        vault = self.scratch / "vault"
        receipt = R.recover(vault, specs, use_authority=False)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertFalse(vault.exists())
        self.assertEqual([row for row in receipt["checks"] if row["check"] == "source:ledger"][0]["status"], "FAIL")

    def test_02_path_escape_refused_before_copy(self) -> None:
        specs = (replace(R.SOURCES[0], relative="../escape.jsonl"), *R.SOURCES[1:])
        vault = self.scratch / "vault"
        receipt = R.recover(vault, specs, use_authority=False)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertFalse(vault.exists())
        self.assertFalse((self.scratch / "escape.jsonl").exists())
        self.assertIn("unsafe relative", receipt["checks"][-1]["reason"])

    def test_03_duplicate_destination_refused_before_copy(self) -> None:
        specs = (R.SOURCES[0], replace(R.SOURCES[1], relative=R.SOURCES[0].relative.swapcase()), R.SOURCES[2])
        vault = self.scratch / "vault"
        receipt = R.recover(vault, specs, use_authority=False)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertFalse(vault.exists())
        self.assertIn("duplicate", receipt["checks"][-1]["reason"])

    def test_04_invalid_graph_schema(self) -> None:
        graph = R.strict_json(R.SOURCES[2].path)
        graph["R2_POS"]["inputs"]["conditioning"] = ["MISSING_NODE", 0]
        altered = self.scratch / "graph.json"
        altered.write_text(json.dumps(graph), encoding="utf-8")
        checks = R.validate_graph(altered, R.PILOT / "task/corrections/identity/r6/scripts/r6_graph.py", R.PILOT / "task/corrections/identity/r6/scripts/r6_key_recipe.py")
        self.assertEqual(checks[0]["status"], "FAIL")

    def test_05_positive_exact_sources(self) -> None:
        vault = self.scratch / "vault"
        receipt = R.recover(vault)
        self.assertEqual(receipt["status"], "SELF_VERIFIED_PENDING_ROOT_REVIEW", [row for row in receipt["checks"] if row["status"] == "FAIL"])
        self.assertEqual(len(receipt["copied"]), 3)
        self.assertEqual([row["status"] for row in receipt["checks"] if row["check"] == "graph_runtime_compatibility"], ["UNVERIFIED"])

    def test_06_no_overwrite(self) -> None:
        vault = self.scratch / "vault"
        self.assertEqual(R.recover(vault)["status"], "SELF_VERIFIED_PENDING_ROOT_REVIEW")
        second = R.recover(vault)
        self.assertEqual(second["status"], "BLOCKED")
        self.assertIn("refusing overwrite", second["checks"][-1]["reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
