"""Run unchanged safe F02 function bodies from the historic R6g gate suite.

The historic module executes all probes on import and several overwrite R6
artifacts, so only its F02 definitions are compiled against isolated paths.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch


worker = Path(__file__).resolve().parent
r6 = Path(sys.argv[1]).resolve()
historic = r6 / "continuations" / "LONG01-R6g-20261014T0725Z-1572" / "tests" / "test_r6g_microfixes.py"
source = historic.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(historic))
names = {"expect_block", "t_empty_binding", "t_encoder_spy"}
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
if {node.name for node in functions} != names:
    raise RuntimeError("historic F02 function missing")

with tempfile.TemporaryDirectory(prefix="c01-existing-gate-", dir=worker) as scratch:
    root = Path(scratch)
    (root / "reviews" / "keys").mkdir(parents=True)
    fake_k = types.ModuleType("r6_common")
    fake_k.R6 = root
    fake_k.sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("c01_safe_existing_gate", r6 / "scripts" / "r6_gate.py")
    gate = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"r6_common": fake_k}):
        spec.loader.exec_module(gate)
    isolated_tempfile = types.SimpleNamespace(
        mkdtemp=lambda prefix: tempfile.mkdtemp(prefix=prefix, dir=root)
    )
    scope = {"G": gate, "K": fake_k, "R6": root, "Path": Path, "json": json,
             "tempfile": isolated_tempfile, "shutil": shutil}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(historic), "exec"), scope)
    for name in ("t_empty_binding", "t_encoder_spy"):
        scope[name]()
        print(f"PASS unchanged historic {name}")
