"""Read-only schema/identity survey of existing R6 review records.

This supplies recorded inputs as the comparison side to isolate record shape;
it does not attest that producer dependencies are fresh today.
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch


r6 = Path(sys.argv[1]).resolve()
fake_k = types.ModuleType("r6_common")
fake_k.R6 = r6
fake_k.sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location("c01_schema_gate", r6 / "scripts" / "r6_gate.py")
gate = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"r6_common": fake_k}):
    spec.loader.exec_module(gate)

counts = collections.Counter()
examples = {}
for review_path in sorted((r6 / "reviews").rglob("*.review.json")):
    kind = review_path.parent.name
    name = review_path.name.removesuffix(".review.json")
    try:
        record = json.loads(review_path.read_text(encoding="utf-8"))
        gate.require_review(kind, name, Path(record["artifact"]["path"]), record["inputs"])
        outcome = "ACCEPTED_RECORD_SHAPE_AND_ARTIFACT"
    except Exception as exc:
        outcome = str(exc).split(" ")[0] if isinstance(exc, gate.GateBlock) else type(exc).__name__
        examples.setdefault((kind, outcome), str(review_path))
    counts[(kind, outcome)] += 1

print(json.dumps({"counts": [{"kind": k, "outcome": outcome, "count": n}
                             for (k, outcome), n in sorted(counts.items())],
                  "examples": [{"kind": k, "outcome": outcome, "path": p}
                               for (k, outcome), p in sorted(examples.items())]}, indent=2))
