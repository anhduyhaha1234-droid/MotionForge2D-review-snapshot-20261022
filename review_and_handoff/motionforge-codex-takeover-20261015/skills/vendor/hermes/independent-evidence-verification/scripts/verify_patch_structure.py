#!/usr/bin/env python
"""Detect truncation damage: functions spliced into the WRONG SCOPE.

A truncated `patch` can land syntactically valid but structurally wrong code -- most
commonly new `def`s dedented one level short, so they nest inside the preceding
function instead of landing at module level. The file still compiles, imports, and
looks fine in a diff, so `py_compile` will NOT catch it.

Measured 2026-09-29 (MF2D C19): py_compile rc 0 while 13 tests were red and six
functions (`_canonical_json`, `s10_unit_prompt_sha256`, `s10_window_basename`,
`s10_unit_control`, `s10_unit_time_map`, `s10_unit_binding_digest`) were nested inside
`_graph_object_sha256`, leaving its body referencing an undefined `canonical`.

usage:
  python verify_patch_structure.py <file.py> [--expect-toplevel NAME ...]

exit 0 = no unexpected nesting found; exit 5 = nesting/expectation problem (RED).
Print-only; never edits the file.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# Functions whose nesting inside a host body is a normal, known pattern. Extend per
# project if a module legitimately defines closures.
ALLOWED_NESTING: set[str] = set()


def nesting_report(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top = [n.name for n in tree.body
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    nested: list[tuple[str, str, int]] = []  # (host, inner, inner_lineno)
    hosts: dict[str, tuple[int, int]] = {}

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        hosts[node.name] = (node.lineno, node.end_lineno or node.lineno)
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested.append((node.name, child.name, child.lineno))

    return {"path": str(path), "top_level": top, "nested": nested, "hosts": hosts}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    expect: list[str] = []
    if "--expect-toplevel" in sys.argv:
        expect = sys.argv[sys.argv.index("--expect-toplevel") + 1:]

    try:
        rep = nesting_report(path)
    except SyntaxError as exc:
        print(f"SYNTAX_ERROR {path}:{exc.lineno}: {exc.msg}")
        return 5

    print(f"PATH {rep['path']}")
    print(f"TOP_LEVEL_FUNCS {len(rep['top_level'])}")
    for name in rep["top_level"]:
        lo, hi = rep["hosts"].get(name, (0, 0))
        print(f"  {name}  (lines {lo}..{hi})")

    unexpected = [n for n in rep["nested"] if n[1] not in ALLOWED_NESTING]
    print(f"NESTED_TOTAL {len(rep['nested'])}")
    for host, inner, lineno in rep["nested"]:
        flag = "" if inner in ALLOWED_NESTING else "  <-- UNEXPECTED"
        print(f"  {inner} (line {lineno}) inside {host}{flag}")

    missing = [e for e in expect if e not in rep["top_level"]]
    if missing:
        print(f"EXPECTED_TOPLEVEL_MISSING {missing}")

    red = bool(unexpected or missing)
    print("VERDICT " + ("RED unexpected nesting/expectation" if red else "OK no unexpected nesting"))
    return 5 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
