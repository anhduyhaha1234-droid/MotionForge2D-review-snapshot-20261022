"""R6 semantic gate — artifact-bound review records + consumer gates (S2/F04).

Review record (per reviewed artifact): C/r6/reviews/<kind>/<name>.review.json
  {review_id, reviewer, reviewed_at, artifact{path,sha256}, inputs{...}, expected{actors,contacts},
   verdict PASS|FAIL|UNKNOWN, evidence}
Gate(kind_path): review exists AND artifact sha matches now AND input lineage matches current
(ledger row sha, cast refs, masks, graph, model, settings) AND verdict==PASS. Anything else -> BLOCK.
No file-count / existence-only / correlation substitute.
"""
from __future__ import annotations
import hashlib, json, math, re, time
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_cache as CA  # noqa: E402

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
    try:
        def unique_keys(pairs):
            record = {}
            for key, value in pairs:
                if key in record:
                    raise ValueError(f"duplicate field {key}")
                record[key] = value
            return record

        def reject_constant(value):
            raise ValueError(f"non-JSON constant {value}")

        return json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=unique_keys,
                          parse_constant=reject_constant)
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, ValueError) as exc:
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: {exc}") from exc


class GateBlock(Exception):
    pass


def _nonempty_text(value):
    return type(value) is str and bool(value.strip())


def _binding_value(value):
    """Accept complete JSON dependency values without Python's bool/int equality alias."""
    if type(value) is str:
        return bool(value.strip())
    if type(value) is int:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return bool(value) and all(_binding_value(v) for v in value)
    if type(value) is dict:
        return bool(value) and all(_nonempty_text(k) and _binding_value(v) for k, v in value.items())
    return False


def _valid_inputs(inputs):
    if type(inputs) is not dict or not inputs:
        return False
    for key, value in inputs.items():
        if not _nonempty_text(key) or not _binding_value(value):
            return False
        if key.endswith(("_sha", "_sha256")) and (
            type(value) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", value)
        ):
            return False
    return True


def _current_blend_frame_ids(inputs_now, kind, name):
    """Derive frame identity from the current manifest entries, not the review."""
    current = inputs_now.get("frames") if type(inputs_now) is dict else None
    if type(current) is not list or not current:
        raise GateBlock(f"SEMANTIC_REVIEW_CURRENT_FRAMES_MALFORMED {kind}:{name}")
    for fid, frame in enumerate(current, 1):
        if (type(frame) is not dict or
                type(frame.get("name")) is not str or
                not re.fullmatch(r"[0-9]{4,}\.jpg", frame["name"]) or
                type(frame.get("size")) is not int or frame["size"] < 1 or
                type(frame.get("sha256")) is not str or
                not re.fullmatch(r"[0-9a-fA-F]{64}", frame["sha256"])):
            raise GateBlock(f"SEMANTIC_REVIEW_CURRENT_FRAMES_MALFORMED {kind}:{name}")
        if frame["name"] != f"{fid:04d}.jpg":
            raise GateBlock(f"SEMANTIC_REVIEW_FRAME_IDENTITY_MISMATCH {kind}:{name}: current manifest")
    return list(range(1, len(current) + 1))


def require_review(kind: str, name: str, artifact: Path, inputs_now: dict):
    """Block unless a PASS review exists that binds this exact artifact + current inputs.

    F02: review identity, artifact path+bytes and the entire typed dependency map
    must match the consumer; a subset binding cannot authorize assembly.
    """
    r = load_review(kind, name)
    if r is None:
        raise GateBlock(f"SEMANTIC_REVIEW_ABSENT {kind}:{name}")
    if type(r) is not dict:
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: record is not an object")
    if r.get("review_id") != f"{kind}:{name}" or type(r.get("review_id")) is not str:
        raise GateBlock(f"SEMANTIC_REVIEW_IDENTITY_MISMATCH {kind}:{name}")
    if r.get("reviewer") is None or r.get("reviewer") == "":
        raise GateBlock(f"SEMANTIC_REVIEW_REVIEWER_MISSING {kind}:{name}")
    if not _nonempty_text(r["reviewer"]):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: reviewer")
    if r.get("evidence") is None or r.get("evidence") == "":
        raise GateBlock(f"SEMANTIC_REVIEW_EVIDENCE_MISSING {kind}:{name}")
    if not _nonempty_text(r["evidence"]):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: evidence")
    if not _nonempty_text(r.get("reviewed_at")):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: reviewed_at")
    try:
        datetime.strptime(r["reviewed_at"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: reviewed_at") from exc
    if type(r.get("inputs")) is dict and not r["inputs"]:
        raise GateBlock(f"SEMANTIC_REVIEW_INPUTS_EMPTY {kind}:{name}")
    if not _valid_inputs(r.get("inputs")) or not _valid_inputs(inputs_now):
        raise GateBlock(f"SEMANTIC_REVIEW_INPUTS_MALFORMED {kind}:{name}")
    expected = r.get("expected")
    if type(expected) is dict and not expected:
        raise GateBlock(f"SEMANTIC_REVIEW_EXPECTED_EMPTY {kind}:{name}")
    if type(expected) is not dict or not expected or any(not _nonempty_text(k) for k in expected):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: expected")
    if "shot" in expected and not _nonempty_text(expected["shot"]):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: expected.shot")
    for field in ("fid", "frames"):
        if field in expected and (type(expected[field]) is not int or expected[field] < 1):
            raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: expected.{field}")
    frames = r.get("frames")
    if type(frames) is list and not frames:
        raise GateBlock(f"SEMANTIC_REVIEW_FRAMES_MISSING {kind}:{name}")
    if type(frames) is not list or not frames or any(type(f) is not int or f < 1 for f in frames):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: frames")
    if len(set(frames)) != len(frames):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: duplicate frames")
    key_name = re.fullmatch(r"(S\d+)_f(\d+)", name) if kind == "keys" else None
    blend_name = re.fullmatch(r"(S\d+)_blend", name) if kind == "blend" else None
    if key_name:
        fid = int(key_name.group(2))
        if expected.get("shot") != key_name.group(1) or expected.get("fid") != fid:
            raise GateBlock(f"SEMANTIC_REVIEW_IDENTITY_MISMATCH {kind}:{name}: expected")
        if frames != [fid]:
            raise GateBlock(f"SEMANTIC_REVIEW_FRAME_IDENTITY_MISMATCH {kind}:{name}")
    if blend_name:
        if expected.get("shot") != blend_name.group(1):
            raise GateBlock(f"SEMANTIC_REVIEW_IDENTITY_MISMATCH {kind}:{name}: expected")
        current_frame_ids = _current_blend_frame_ids(inputs_now, kind, name)
        if expected.get("frames") != len(current_frame_ids) or frames != current_frame_ids:
            raise GateBlock(f"SEMANTIC_REVIEW_FRAME_IDENTITY_MISMATCH {kind}:{name}")
    verdict = r.get("verdict")
    if not _nonempty_text(verdict):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: verdict")
    if verdict != "PASS":
        raise GateBlock(f"SEMANTIC_REVIEW_{r['verdict']} {kind}:{name}")
    reviewed_artifact = r.get("artifact")
    if type(reviewed_artifact) is not dict or not _nonempty_text(reviewed_artifact.get("path")):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: artifact.path")
    reviewed_sha = reviewed_artifact.get("sha256")
    if type(reviewed_sha) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", reviewed_sha):
        raise GateBlock(f"SEMANTIC_REVIEW_MALFORMED {kind}:{name}: artifact.sha256")
    try:
        current_path = Path(artifact).resolve(strict=True)
        review_path = Path(reviewed_artifact["path"])
        if not review_path.is_absolute() or review_path.resolve(strict=True) != current_path:
            raise GateBlock(f"SEMANTIC_REVIEW_ARTIFACT_PATH_MISMATCH {kind}:{name}")
        current_sha = K.sha(current_path)
    except (OSError, TypeError, ValueError) as exc:
        raise GateBlock(f"SEMANTIC_REVIEW_ARTIFACT_PATH_MISMATCH {kind}:{name}: {exc}") from exc
    if reviewed_sha.lower() != current_sha.lower():
        raise GateBlock(f"SEMANTIC_REVIEW_TAMPERED artifact hash mismatch {kind}:{name}")
    recorded_keys, current_keys = set(r["inputs"]), set(inputs_now)
    if recorded_keys != current_keys:
        raise GateBlock(f"SEMANTIC_REVIEW_INPUT_SET_MISMATCH {kind}:{name}: "
                        f"unrecorded={sorted(current_keys - recorded_keys)} "
                        f"no_longer_current={sorted(recorded_keys - current_keys)}")
    for key in sorted(current_keys):
        recorded = json.dumps(r["inputs"][key], sort_keys=True, separators=(",", ":"), allow_nan=False)
        current = json.dumps(inputs_now[key], sort_keys=True, separators=(",", ":"), allow_nan=False)
        if recorded != current:
            raise GateBlock(f"SEMANTIC_REVIEW_STALE input {key} changed {kind}:{name}")
    return r


# ---------------- consumer gates ----------------

def key_inputs_now(sid: str, fid: int, key_png: Path):
    deps_p = K.R6 / "work" / sid / f"f_{fid:04d}.deps.json"
    deps, why = CA.load_deps(deps_p)
    if why != "ok":
        raise GateBlock(f"KEY_DEPS_MALFORMED {sid} f{fid}: {why}")
    ok, why = CA.verify_deps(deps, sid, fid)
    if not ok:
        raise GateBlock(f"KEY_DEPS_INVALID {sid} f{fid}: {why}")
    try:
        ledger_sha = ledger_row_sha(sid)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        raise GateBlock(f"KEY_LEDGER_UNREADABLE {sid}: {exc}") from exc
    return {"ledger_row_sha": ledger_sha,
            "deps_sha": hashlib.sha256(json.dumps(deps, sort_keys=True).encode()).hexdigest()}


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
        if isinstance(e, dict):
            if "frame" in e:
                ev_fids.add(int(e["frame"]))
            elif "f" in e:
                ev_fids.add(int(e["f"]) + 1)
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
    if type(frames) is not list or len(frames) != expect_frames:
        observed = len(frames) if type(frames) is list else "malformed"
        raise GateBlock(f"BLEND_MANIFEST_COUNT {sid}: {observed}/{expect_frames}")
    _current_blend_frame_ids({"frames": frames}, "blend", f"{sid}_blend")
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

def gate_batch_conformance(record: dict, mode: str = "engineering") -> bool:
    """Validate batch submission:
    - 'engineering' (G1): Q05, Q07 must be PASS; media Qs remain honestly UNKNOWN/FAIL until G2.
    - 'final' (G3): all 12 Qs must be PASS.
    """
    matrix = record.get("matrix", {})
    exp_keys = {f"Q{i:02d}" for i in range(1, 13)}
    if set(matrix.keys()) != exp_keys:
        raise GateBlock(f"MATRIX_KEYS {sorted(matrix.keys())}")
    for q, val in matrix.items():
        if val not in ("PASS", "FAIL", "UNKNOWN"):
            raise GateBlock(f"INVALID_VERDICT_VALUE {q}={val}")
    if mode == "engineering":
        if matrix.get("Q05") != "PASS" or matrix.get("Q07") != "PASS":
            raise GateBlock(f"ENGINEERING_BATCH_Q_NOT_PASS Q05={matrix.get('Q05')}, Q07={matrix.get('Q07')}")
        # Disallow false claims of media PASS before actual media rendering
        for mq in ("Q01", "Q04", "Q06", "Q09", "Q12"):
            if matrix.get(mq) == "PASS":
                raise GateBlock(f"PREMATURE_MEDIA_PASS_IN_ENGINEERING_BATCH {mq}")
    elif mode == "final":
        bad = {k: v for k, v in matrix.items() if v != "PASS"}
        if bad:
            raise GateBlock(f"FINAL_SUBMISSION_NOT_ALL_PASS {bad}")
    return True

