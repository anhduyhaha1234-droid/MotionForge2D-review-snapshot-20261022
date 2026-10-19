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
                 evidence: str, reviewer: str = "worker-vision+hash (vision-capable, artifact-bound)",
                 frames: list | None = None):
    d = REV / kind
    d.mkdir(parents=True, exist_ok=True)
    rec = {"review_id": f"{kind}:{name}", "reviewer": reviewer,
           "reviewed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "artifact": {"path": str(artifact), "sha256": K.sha(artifact)},
           "inputs": inputs, "expected": expected, "frames": frames or [], "verdict": verdict,
           "evidence": evidence}
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
    """Block unless a PASS review exists that binds this exact artifact + current inputs.

    F02: mandatory review fields — inputs/expected/reviewer/evidence/frames must all be present
    and non-empty; an empty binding ({}) may never be accepted.
    """
    r = load_review(kind, name)
    if r is None:
        raise GateBlock(f"SEMANTIC_REVIEW_ABSENT {kind}:{name}")
    if not str(r.get("reviewer") or "").strip():
        raise GateBlock(f"SEMANTIC_REVIEW_REVIEWER_MISSING {kind}:{name}")
    if not str(r.get("evidence") or "").strip():
        raise GateBlock(f"SEMANTIC_REVIEW_EVIDENCE_MISSING {kind}:{name}")
    if not isinstance(r.get("inputs"), dict) or not r["inputs"]:
        raise GateBlock(f"SEMANTIC_REVIEW_INPUTS_EMPTY {kind}:{name}")
    if not isinstance(r.get("expected"), dict) or not r["expected"]:
        raise GateBlock(f"SEMANTIC_REVIEW_EXPECTED_EMPTY {kind}:{name}")
    frames = r.get("frames")
    if not isinstance(frames, list) or not frames:
        raise GateBlock(f"SEMANTIC_REVIEW_FRAMES_MISSING {kind}:{name}")
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
    # F03: event keys must exist at the EXACT event frame — no ±5 tolerance, no snap.
    kf_set = set(key_fids)
    missing_ev = [f for f in sorted(ev_fids) if f <= n and f not in kf_set]
    if missing_ev:
        raise GateBlock(f"EVENT_KEY_MISSING {sid}: events {missing_ev} have no key at the exact fid")
    for fid in key_fids:
        if fid <= n:
            gate_key(sid, fid)
    return {"shot": sid, "keys": len([f for f in key_fids if f <= n]), "event_fids": sorted(ev_fids)}


def blend_inputs_now(sid: str):
    """F06-style exact identity for a blend: ledger row + per-frame manifest + key-set hashes."""
    man_p = K.R6 / "work" / sid / "blend_manifest.json"
    deps = {"ledger_row_sha": ledger_row_sha(sid)}
    if man_p.exists():
        m = json.loads(man_p.read_text(encoding="utf-8"))
        deps["blend_manifest_sha"] = K.sha(man_p)
        deps["frames"] = m.get("frames")
        deps["key_set_sha"] = m.get("key_set_sha")
        deps["child_outcomes_sha"] = m.get("child_outcomes_sha")
    return deps


def gate_blend_fresh(sid: str, expect_frames: int, started_at: float):
    """F05: full-frame verification via the run's own manifest + child outcomes + decode samples.

    No max-mtime. A blend is fresh only if its manifest proves: exact expected frame count,
    every frame's sha256 matches on disk now, no extra frames, child outcomes present and all
    rc==0, and a decode of head/mid/tail succeeds.
    """
    man_p = K.R6 / "work" / sid / "blend_manifest.json"
    if not man_p.exists():
        raise GateBlock(f"BLEND_MANIFEST_MISSING {sid}")
    m = json.loads(man_p.read_text(encoding="utf-8"))
    frames = m.get("frames")
    if not isinstance(frames, list) or len(frames) != expect_frames:
        raise GateBlock(f"BLEND_MANIFEST_COUNT {sid}: {0 if not frames else len(frames)}/{expect_frames}")
    outcomes = m.get("child_outcomes") or []
    if not outcomes or any(o.get("rc") != 0 for o in outcomes):
        raise GateBlock(f"BLEND_CHILD_FAILURE {sid}: {[o for o in outcomes if o.get('rc') != 0][:3]}")
    if m.get("decode_ok") is not True:
        raise GateBlock(f"BLEND_DECODE_NOT_OK {sid}")
    bd = Path(m.get("blend_dir") or (K.R6 / "work" / sid / "blend"))
    on_disk = sorted(p.name for p in bd.glob("*") if p.is_file()) if bd.exists() else []
    man_names = sorted(fr["name"] for fr in frames)
    if on_disk != man_names:
        raise GateBlock(f"BLEND_MANIFEST_MISMATCH {sid}: disk {len(on_disk)} vs manifest {len(man_names)}")
    for fr in frames:
        p = bd / fr["name"]
        if K.sha(p) != fr["sha256"]:
            raise GateBlock(f"BLEND_FRAME_TAMPERED {sid}:{fr['name']}")
    return {"shot": sid, "frames": len(frames), "fresh": True, "manifest": str(man_p)}


def gate_assemble(shot_plan: list):
    """Pre-encoder: every planned shot must have (1) all keys reviewed PASS at exact event fids,
    (2) a fresh+complete blend per its manifest (F05), (3) a PASS semantic review of the FINAL
    blend over its exact output hashes (F02) — the key gate does not substitute for this.
    """
    problems = []
    for sid, expect in shot_plan:
        try:
            gate_shot_before_propagate(sid)
            gate_blend_fresh(sid, expect, 0.0)
            man_p = K.R6 / "work" / sid / "blend_manifest.json"
            require_review("blend", f"{sid}_blend", man_p, blend_inputs_now(sid))
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
