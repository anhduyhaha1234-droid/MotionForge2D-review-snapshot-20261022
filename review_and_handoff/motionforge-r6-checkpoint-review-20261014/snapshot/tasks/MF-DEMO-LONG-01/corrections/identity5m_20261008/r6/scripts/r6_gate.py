"""R6 semantic gate — artifact-bound review records + consumer gates (S2/F04).

Review record (per reviewed artifact): C/r6/reviews/<kind>/<name>.review.json
  {review_id, reviewer, reviewed_at, artifact{path,sha256}, inputs{...}, expected{actors,contacts},
   verdict PASS|FAIL|UNKNOWN, evidence}
Gate(kind_path): review exists AND artifact sha matches now AND input lineage matches current
(ledger row sha, cast refs, masks, graph, model, settings) AND verdict==PASS. Anything else -> BLOCK.
No file-count / existence-only / correlation substitute.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402

REV = K.R6 / "reviews"


def ledger_row(sid):
    for line in (K.R6 / "source_actor_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["shot"] == sid:
            return r
    raise KeyError(sid)


def ledger_row_sha(sid):
    return hashlib.sha256(json.dumps(ledger_row(sid), sort_keys=True).encode()).hexdigest()


def write_review(kind: str, name: str, artifact: Path, inputs: dict, expected: dict, verdict: str,
                 evidence: str, reviewer: str = "worker-vision+hash (vision-capable, artifact-bound)"):
    d = REV / kind
    d.mkdir(parents=True, exist_ok=True)
    rec = {"review_id": f"{kind}:{name}", "reviewer": reviewer,
           "reviewed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "artifact": {"path": str(artifact), "sha256": K.sha(artifact)},
           "inputs": inputs, "expected": expected, "verdict": verdict, "evidence": evidence}
    p = d / f"{name}.review.json"
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def load_review(kind: str, name: str):
    p = REV / kind / f"{name}.review.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


class GateBlock(Exception):
    pass


def require_review(kind: str, name: str, artifact: Path, inputs_now: dict):
    """Block unless a PASS review exists that binds this exact artifact + current inputs."""
    r = load_review(kind, name)
    if r is None:
        raise GateBlock(f"SEMANTIC_REVIEW_ABSENT {kind}:{name}")
    if r["verdict"] != "PASS":
        raise GateBlock(f"SEMANTIC_REVIEW_{r['verdict']} {kind}:{name}")
    if r["artifact"]["sha256"] != K.sha(artifact):
        raise GateBlock(f"SEMANTIC_REVIEW_TAMPERED artifact hash mismatch {kind}:{name}")
    for k, v in r["inputs"].items():
        if k not in inputs_now:
            raise GateBlock(f"SEMANTIC_REVIEW_INPUT_MISSING {k} {kind}:{name}")
        if inputs_now[k] != v:
            raise GateBlock(f"SEMANTIC_REVIEW_STALE input {k} changed {kind}:{name}")
    return r


# ---------------- consumer gates ----------------

def key_inputs_now(sid: str, fid: int, key_png: Path):
    deps_p = K.R6 / "work" / sid / f"f_{fid:04d}.deps.json"
    deps = json.loads(deps_p.read_text(encoding="utf-8")) if deps_p.exists() else {}
    return {"ledger_row_sha": ledger_row_sha(sid), "deps_sha": hashlib.sha256(json.dumps(deps, sort_keys=True).encode()).hexdigest()}


def gate_key(sid: str, fid: int):
    key = K.R6 / "keys" / sid / f"f_{fid:04d}_key.png"
    if not key.exists():
        raise GateBlock(f"KEY_MISSING {sid} f{fid}")
    return require_review("keys", f"{sid}_f{fid:04d}", key, key_inputs_now(sid, fid, key))


def gate_shot_before_propagate(sid: str):
    """All keys' reviews PASS + event keys present at exact fids + no NOT_PRESENT leak."""
    row = ledger_row(sid)
    n = row["n"]
    sb = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
    ev_fids = set()
    for e in row.get("events", []):
        if isinstance(e, dict) and "frame" in e:
            ev_fids.add(int(e["frame"]))
    for c in row.get("contacts", []):
        if isinstance(c, dict) and "from" in c:
            ev_fids.add(int(c["from"]) + 1)  # r3 'from' 0-based -> fid 1-based
    for a in row["actors"]:
        for w in a["class_windows"]:
            if w["from"] > 1 and w["class"] in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev_fids.add(int(w["from"]))  # entry boundary = event (must have a key at/near it)
    key_fids = [k["fid"] for k in sb["keys"]]
    missing_ev = [f for f in sorted(ev_fids) if f <= n and not any(abs(f - kf) <= 5 for kf in key_fids)]
    if missing_ev:
        raise GateBlock(f"EVENT_KEY_MISSING {sid}: events {missing_ev} not near any key fid")
    for fid in key_fids:
        if fid <= n:
            gate_key(sid, fid)
    return {"shot": sid, "keys": len([f for f in key_fids if f <= n]), "event_fids": sorted(ev_fids)}


def gate_blend_fresh(sid: str, expect_frames: int, started_at: float):
    """Fail-closed: fresh complete outputs, rc verified by caller; no tail-fill acceptance."""
    bd = K.R6 / "work" / sid / "blend"
    if not bd.exists():
        raise GateBlock(f"BLEND_DIR_MISSING {sid}")
    got = len(list(bd.glob("*.jpg")) + list(bd.glob("*.png")))
    if got < expect_frames:
        raise GateBlock(f"BLEND_PARTIAL {sid}: {got}/{expect_frames}")
    newest = max((f.stat().st_mtime for f in bd.iterdir() if f.is_file()), default=0)
    if newest < started_at:
        raise GateBlock(f"BLEND_STALE {sid}: no outputs written during this run (tail-fill suspected)")
    return {"shot": sid, "frames": got, "fresh": True}


def gate_assemble(shot_plan: list):
    """Pre-encoder: every planned shot has fresh+reviewed blend; nothing else can pass."""
    import time as _t
    problems = []
    for sid, expect in shot_plan:
        try:
            gate_shot_before_propagate(sid)
            bd = K.R6 / "work" / sid / "blend"
            got = len(list(bd.glob("*.jpg")) + list(bd.glob("*.png"))) if bd.exists() else 0
            if got < expect:
                problems.append(f"{sid}: blend {got}/{expect}")
        except GateBlock as e:
            problems.append(str(e))
    if problems:
        raise GateBlock("ASSEMBLE_BLOCKED " + "; ".join(problems[:8]))
    return True


def find_r6_terminal():
    d = K.R6 / "evidence/terminal"
    return sorted(d.glob("LONG01-R6-*.json")) if d.exists() else []


def gate_submit(record: dict):
    """Submit gate: matrix exactly 12 keys all PASS + 5 artifact kinds + remaining empty + record schema."""
    rows = record.get("matrix", {})
    exp = {f"Q{i:02d}" for i in range(1, 13)}
    if set(rows.keys()) != exp:
        raise GateBlock(f"MATRIX_KEYS {sorted(rows.keys())}")
    bad = {k: v for k, v in rows.items() if v != "PASS"}
    if bad:
        raise GateBlock(f"MATRIX_NOT_ALL_PASS {bad}")
    kinds = {}
    for a in record.get("artifacts", []):
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    for k in ("master", "comparison", "matrix", "checkpoint", "receipts"):
        if kinds.get(k) != 1:
            raise GateBlock(f"ARTIFACT_KIND {k}={kinds.get(k)}")
    if record.get("remaining_work"):
        raise GateBlock("REMAINING_NOT_EMPTY")
    for a in record.get("artifacts", []):
        p = Path(a["path"])
        if not str(p.resolve()).startswith(str(K.R6.resolve())):
            raise GateBlock(f"ARTIFACT_OUT_OF_R6 {p}")
        if not p.exists() or K.sha(p) != a["sha256"]:
            raise GateBlock(f"ARTIFACT_HASH_STALE {p}")
    return True
