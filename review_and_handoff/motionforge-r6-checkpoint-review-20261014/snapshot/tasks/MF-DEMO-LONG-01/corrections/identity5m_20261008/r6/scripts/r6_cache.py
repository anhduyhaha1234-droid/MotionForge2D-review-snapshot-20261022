"""R6 cache/deps contract (S2 / F05 / T07): cache key = exact consumed bytes + settings.

Skip is allowed ONLY when: deps json exists AND every consumed file hash matches AND output exists
AND semantic review PASS. Same-path same-size mutation invalidates; unchanged verified control reuses.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402


def h(p: Path):
    p = Path(p)
    if not p.exists():
        return None
    return K.sha(p)


def build_deps(sid: str, fid: int, consumed: dict, settings: dict) -> dict:
    """consumed: {"source_span_lo": a0, "source_span_hi": b0, "gframe": g,
                  "casts": [paths], "masks": [paths], "graph": path}"""
    dep = {"kind": "r6_key_deps_v2", "shot": sid, "fid": fid,
           "source": {"path": str(K.SRC), "gframe": consumed["gframe"],
                      "span": [consumed["source_span_lo"], consumed["source_span_hi"]]},
           "casts": [{"path": str(Path(p)), "sha256": h(Path(p))} for p in consumed.get("casts", [])],
           "masks": [{"path": str(Path(p)), "sha256": h(Path(p))} for p in consumed.get("masks", [])],
           "graph": ({"path": str(Path(consumed["graph"])), "sha256": h(Path(consumed["graph"]))}
                     if consumed.get("graph") else None),
           "settings": settings}
    served = []
    for c in ("casts", "masks"):
        for x in dep.get(c, []):
            if x["sha256"] is None:
                served.append(f"{c}:{x['path']}")
    g = dep.get("graph")
    if g is not None and g["sha256"] is None:
        served.append(f"graph:{g['path']}")
    if served:
        raise ValueError(f"deps contain unhashable/missing files: {served}")
    dep["deps_sha"] = hashlib.sha256(json.dumps(dep, sort_keys=True).encode()).hexdigest()
    return dep


def verify_deps(dep: dict) -> tuple[bool, str]:
    """True only if every recorded hash still matches on disk."""
    for group in ("casts", "masks"):
        for e in dep.get(group, []):
            now = h(Path(e["path"]))
            if now != e["sha256"]:
                return False, f"{group}:{e['path']} hash {e['sha256']} -> {now}"
    g = dep.get("graph", {})
    if g.get("path"):
        now = h(Path(g["path"]))
        if now != g["sha256"]:
            return False, f"graph {g['path']} {g['sha256']} -> {now}"
    return True, "ok"


def skip_allowed(sid: str, fid: int, key_png: Path) -> tuple[bool, str]:
    """The ONLY legal skip: deps verified + key exists + review PASS (gate enforces)."""
    from r6_gate import require_review, key_inputs_now, GateBlock
    dp = K.R6 / "work" / sid / f"f_{fid:04d}.deps.json"
    if not dp.exists():
        return False, "no deps"
    dep = json.loads(dp.read_text(encoding="utf-8"))
    ok, why = verify_deps(dep)
    if not ok:
        return False, f"dep changed: {why}"
    if not (key_png.exists() and key_png.stat().st_size > 0):
        return False, "key missing/empty"
    try:
        require_review("keys", f"{sid}_f{fid:04d}", key_png, key_inputs_now(sid, fid, key_png))
    except GateBlock as e:
        return False, f"review: {e}"
    return True, "verified-reuse"
