"""Read-only C02B1 byte, scope and duplicate-definition audit."""
import ast
import difflib
import hashlib
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent
PACKET = OUT.parent
preflight = json.loads((PACKET / "C02B1_PREFLIGHT.json").read_text(encoding="utf-8"))
files = preflight["files"]
common = next(row for row in files if row["relative"] == "scripts/r6_common.py")
common_path = Path(common["path"])
test_path = Path(preflight["new_test"])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "lines": len(data.splitlines())}


protected_drift = []
snapshot_drift = []
for row in files:
    if sha(Path(row["snapshot"])) != row["sha256"]:
        snapshot_drift.append(row["relative"])
    if row["role"] == "protected" and sha(Path(row["path"])) != row["sha256"]:
        protected_drift.append(row["relative"])

old = (OUT / "preimages" / "r6_common.py").read_text(encoding="utf-8")
new = common_path.read_text(encoding="utf-8")
diff = "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                   fromfile="preimages/r6_common.py", tofile=str(common_path)))
(OUT / "common.diff").write_text(diff, encoding="utf-8")


def definitions(source):
    names = [node.name for node in ast.parse(source).body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    return names, sorted({name for name in names if names.count(name) > 1})


old_defs, old_duplicates = definitions(old)
new_defs, new_duplicates = definitions(new)
test_source = test_path.read_text(encoding="utf-8")
test_tree = ast.parse(test_source)
test_duplicates = []
for cls in [n for n in test_tree.body if isinstance(n, ast.ClassDef)]:
    names = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
    test_duplicates.extend(name for name in set(names) if names.count(name) > 1)

r6 = common_path.parents[1]
pinned_python = {Path(row["path"]).resolve() for row in files}
current_python = {path.resolve() for folder in (r6 / "scripts", r6 / "tests")
                  for path in folder.glob("*.py")}
unexpected_python = sorted(str(path) for path in current_python - pinned_python - {test_path.resolve()})
missing_python = sorted(str(path) for path in pinned_python - current_python)
result = {
    "task": "CODEX-C02B1-STAGED-SOURCE-FRESHNESS",
    "common": stats(common_path), "common_preimage": stats(OUT / "preimages" / "r6_common.py"),
    "test": stats(test_path), "protected_count": sum(row["role"] == "protected" for row in files),
    "protected_drift": protected_drift, "snapshot_drift": snapshot_drift,
    "old_definitions": old_defs, "new_definitions": new_defs,
    "old_duplicate_definitions": old_duplicates,
    "new_duplicate_definitions": new_duplicates,
    "test_duplicate_definitions": test_duplicates,
    "unexpected_python": unexpected_python, "missing_python": missing_python,
    "diff_sha256": sha(OUT / "common.diff"),
}
result["ok"] = not any((protected_drift, snapshot_drift, old_duplicates, new_duplicates,
                         test_duplicates, unexpected_python, missing_python)) and set(old_defs) <= set(new_defs)
(OUT / "AUDIT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in result.items() if key not in
                  ("old_definitions", "new_definitions")}, indent=2))
raise SystemExit(0 if result["ok"] else 1)
