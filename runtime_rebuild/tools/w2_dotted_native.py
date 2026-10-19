"""C1 retry graph fix: emit the frontend's NATIVE dotted autogrow form.

The round-3/4 attempts hand-reshaped the autogrow widgets of the converted
Wan-Animate-2 graph into NESTED objects, e.g.

    "291:96": {"inputs": {"expression": "a & ~1", "values": {"a": ["291:90", 1]}}}

which the engine rejects with:
    required_input_missing / input_name "values.a" / details "a"

The ComfyUI frontend's own API export writes those widgets as flat DOTTED keys
(name confirmed against the official template video_wan_animate2.json, which
carries the literal names "values.a", "inputs.input0", "terminations.termination0",
"resize_type.width", "mode.num_iterations"):

    "291:96": {"inputs": {"expression": "a & ~1", "values.a": ["291:90", 1]}}

This tool flattens exactly that one level and nothing else.  It does not invent
values, does not touch already-dotted keys, and writes a per-change report.

usage:
  python w2_dotted_native.py <in.api.json> <out.api.json> <report.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _p(s: str) -> Path:
    r = str(s).replace("\\", "/")
    if len(r) > 2 and r[0] == "/" and r[2] == "/":
        r = r[1].upper() + ":" + r[2:]
    return Path(r)


def flatten_inputs(inputs: dict, keep_parent: bool = False) -> tuple[dict, list[dict], list[dict]]:
    out: dict = {}
    changes: list[dict] = []
    kept: list[dict] = []
    for key, val in inputs.items():
        if isinstance(val, dict) and val and not any("." in str(k) for k in val):
            if keep_parent:
                # The frozen adapter's pre-check (mf_comfy/adapter.py:150-158) does an exact
                # inputs.get(name) for every declared required name, and the engine's
                # autogrow node declares BOTH the container ("values") and the expanded
                # dotted names ("values.a", ...).  Carrying both forms satisfies each side
                # without inventing or dropping any value.
                out[key] = val
            for sub, subval in val.items():
                out[f"{key}.{sub}"] = subval
                changes.append({"from": key, "to": f"{key}.{sub}", "value_shape":
                                (f"link -> node {subval[0]} slot {subval[1]}"
                                 if isinstance(subval, list) and len(subval) == 2 else repr(subval)[:60])})
        else:
            out[key] = val
            if isinstance(val, dict):
                kept.append({"key": key, "reason": "already dotted or non-flattenable", "keys": list(val)[:6]})
    return out, changes, kept


def main() -> int:
    src = _p(sys.argv[1])
    dst = _p(sys.argv[2])
    rep = _p(sys.argv[3])
    graph = json.loads(src.read_text(encoding="utf-8"))
    keep_parent = "--keep-parent" in sys.argv

    report = {"src": str(src), "dst": str(dst), "keep_parent": keep_parent,
              "fixed": [], "left_as_is": [], "node_count": len(graph)}
    for nid, node in graph.items():
        if not isinstance(node, dict) or "inputs" not in node:
            continue
        new_inputs, changes, kept = flatten_inputs(node.get("inputs") or {}, keep_parent)
        if changes:
            node["inputs"] = new_inputs
            report["fixed"].append({"node": nid, "class_type": node.get("class_type"),
                                    "changes": changes, "new_keys": [c["to"] for c in changes]})
        for k in kept:
            report["left_as_is"].append({"node": nid, "class_type": node.get("class_type"), **k})

    # invariant: no node may keep a nested values/inputs/terminations object
    bad = [nid for nid, n in graph.items()
           if isinstance(n, dict) and isinstance((n.get("inputs") or {}).get("values"), dict)]
    bad += [nid for nid, n in graph.items()
            if isinstance(n, dict) and isinstance((n.get("inputs") or {}).get("inputs"), dict)]
    bad += [nid for nid, n in graph.items()
            if isinstance(n, dict) and isinstance((n.get("inputs") or {}).get("terminations"), dict)]
    report["residual_nested_autogrow_nodes"] = sorted(set(bad))
    report["fixed_count"] = len(report["fixed"])
    report["left_count"] = len(report["left_as_is"])

    dst.write_text(json.dumps(graph, indent=1, ensure_ascii=False), encoding="utf-8")
    rep.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"fixed_count": report["fixed_count"], "left_count": report["left_count"],
                      "residual_nested": report["residual_nested_autogrow_nodes"],
                      "fixed_nodes": [f"{f['node']} -> {f['new_keys']}" for f in report["fixed"]]},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
