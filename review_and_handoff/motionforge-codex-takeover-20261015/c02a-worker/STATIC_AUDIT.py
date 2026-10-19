"""Read-only syntax, duplicate-definition and C01 assertion preservation audit."""
import ast
import json
import sys
from collections import Counter
from pathlib import Path

root, preimages, output = map(Path, sys.argv[1:4])
paths = ("scripts/r6_cache.py", "scripts/r6_gate.py",
         "tests/test_codex_c01_review_binding.py",
         "tests/test_codex_c02a_dependency_verification.py")
errors = []
results = {}
trees = {}
for relative in paths:
    source = (root / relative).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative)
    compile(tree, relative, "exec")
    trees[relative] = tree
    names = [node.name for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    repeated = [name for name, count in Counter(names).items() if count > 1]
    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        methods = [node.name for node in cls.body
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        repeated += [f"{cls.name}.{name}" for name, count in Counter(methods).items() if count > 1]
    if repeated:
        errors.append(f"{relative}: duplicate definitions {repeated}")
    results[relative] = {"syntax": "ok", "duplicates": repeated,
                         "top_level_definitions": len(names)}


def c01_tests(tree):
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "ReviewBindingTests")
    return {node.name: [ast.dump(call, include_attributes=False)
                        for call in ast.walk(node)
                        if isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr.startswith("assert")]
            for node in cls.body if isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")}


old = c01_tests(ast.parse((preimages / "tests/test_codex_c01_review_binding.py").read_text(encoding="utf-8")))
new = c01_tests(trees["tests/test_codex_c01_review_binding.py"])
if len(old) != 17 or set(old) != set(new):
    errors.append(f"C01 test names/count changed: old={len(old)} new={len(new)}")
for name in old:
    if old[name] != new.get(name):
        errors.append(f"C01 assertions changed: {name}")
results["c01_assertions"] = {"old_tests": len(old), "new_tests": len(new),
                             "assertions_preserved": not any("C01 assertions changed" in e for e in errors)}
receipt = {"ok": not errors, "files": results, "errors": errors}
output.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps({"ok": receipt["ok"], "errors": errors, "receipt": str(output)}))
raise SystemExit(0 if receipt["ok"] else 1)
