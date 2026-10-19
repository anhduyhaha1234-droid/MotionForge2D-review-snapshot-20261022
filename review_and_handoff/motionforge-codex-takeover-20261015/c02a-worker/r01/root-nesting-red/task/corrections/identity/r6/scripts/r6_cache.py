"""R6 cache/deps contract (S2 / F05 / T07): cache key = exact consumed bytes + settings.

Skip is allowed ONLY when: deps json exists AND every consumed file hash matches AND output exists
AND semantic review PASS. Same-path same-size mutation invalidates; unchanged verified control reuses.
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402


def h(p: Path):
    p = Path(p)
    if not p.exists():
        return None
    return K.sha(p)


MODEL_PATH = Path("C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/models/diffusion_models/flux-2-klein-4b-fp8.safetensors")


def settings_now(sid: str, fid: int) -> dict:
    """Consumer-side CURRENT settings (F06): what this consumer would use NOW, not what it wrote."""
    import os
    sb = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
    return {"mode": "zero_shot_asset_restyle" if sb.get("zero_explicit") else "per_actor_klein",
            "steps": 4, "ctx_factor": os.environ.get("R6_CTX_FACTOR", "1.3"),
            "seed_off": os.environ.get("R6_SEED_OFF", "0"),
            "model": {"path": str(MODEL_PATH), "sha256": h(MODEL_PATH)}}


def build_deps(sid: str, fid: int, consumed: dict, settings: dict) -> dict:
    """consumed: {"source_span_lo": a0, "source_span_hi": b0, "gframe": g,
                  "casts": [paths], "masks": [paths], "graph": path}"""
    if not K.SRC.exists():
        raise ValueError(f"source missing: {K.SRC}")
    if not MODEL_PATH.exists():
        raise ValueError(f"model missing: {MODEL_PATH}")
    dep = {"kind": "r6_key_deps_v3", "shot": sid, "fid": fid,
           "source": {"path": str(K.SRC), "sha256": h(K.SRC), "gframe": consumed["gframe"],
                      "span": [consumed["source_span_lo"], consumed["source_span_hi"]]},
           "model": {"path": str(MODEL_PATH), "sha256": h(MODEL_PATH)},
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


def load_deps(path: Path) -> tuple[object | None, str]:
    """Read a recorded dependency as strict JSON; never bless duplicate keys/NaN."""
    def unique_keys(pairs):
        record = {}
        for key, value in pairs:
            if key in record:
                raise ValueError(f"duplicate field {key}")
            record[key] = value
        return record

    def reject_constant(value):
        raise ValueError(f"non-JSON constant {value}")

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          object_pairs_hook=unique_keys, parse_constant=reject_constant), "ok"
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        return None, f"deps unreadable/malformed: {exc}"


def _json_value(value):
    """Reject Python-only and non-finite values before the v3 digest is computed."""
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and bool(key.strip()) and _json_value(item)
                   for key, item in value.items())
    return False


def verify_deps(dep: dict, sid: str | None = None, fid: int | None = None) -> tuple[bool, str]:
    """Verify a complete recorded v3 dependency against current files and request."""
    required = {"kind", "shot", "fid", "source", "model", "casts", "masks",
                "graph", "settings", "deps_sha"}
    if type(dep) is not dict:
        return False, "deps record must be an object"
    missing = required - set(dep)
    if missing:
        return False, f"deps missing fields: {sorted(missing)}"
    if dep["kind"] != "r6_key_deps_v3" or type(dep["kind"]) is not str:
        return False, "deps kind mismatch"
    if type(dep["shot"]) is not str or not re.fullmatch(r"S[0-9]{4}", dep["shot"]):
        return False, "deps shot malformed"
    if type(dep["fid"]) is not int or dep["fid"] < 1:
        return False, "deps fid malformed"
    if sid is not None and (type(sid) is not str or dep["shot"] != sid):
        return False, "deps shot does not match consumer request"
    if fid is not None and (type(fid) is not int or dep["fid"] != fid):
        return False, "deps fid does not match consumer request"
    plan = K.PLAN.get(dep["shot"])
    if (type(plan) is not dict or type(plan.get("start_frame")) is not int or
            type(plan.get("frames")) is not int or plan["frames"] < 1 or
            dep["fid"] > plan["frames"]):
        return False, "deps shot/fid absent from current plan"
    src = dep["source"]
    if type(src) is not dict:
        return False, "deps source malformed"
    if type(src.get("gframe")) is not int or src["gframe"] != plan["start_frame"] + dep["fid"] - 1:
        return False, "deps source gframe does not match current plan"
    span = src.get("span")
    if (type(span) is not list or len(span) != 2 or
            any(type(v) is not int for v in span) or
            span != [plan["start_frame"], plan["start_frame"] + plan["frames"]]):
        return False, "deps source span does not match current plan"
    for group in ("casts", "masks"):
        if type(dep[group]) is not list:
            return False, f"deps {group} must be a list"
    settings = dep["settings"]
    if type(settings) is not dict or not settings or not _json_value(settings):
        return False, "deps settings malformed/empty"
    mode = settings.get("mode")
    if "mode" in settings and (type(mode) is not str or not mode.strip()):
        return False, "deps settings.mode malformed"
    passthrough = mode == "keep_source_no_visible_actor"
    if passthrough:
        if dep["casts"] or dep["masks"] or dep["graph"] is not None:
            return False, "deps source passthrough must not claim generated inputs"
    elif dep["graph"] is None:
        return False, "deps generated key missing graph"
    recorded_sha = dep["deps_sha"]
    if type(recorded_sha) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", recorded_sha):
        return False, "deps_sha malformed"
    if not _json_value(dep):
        return False, "deps contain non-JSON or non-finite values"
    body = {key: value for key, value in dep.items() if key != "deps_sha"}
    actual_sha = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    if recorded_sha.lower() != actual_sha:
        return False, "deps_sha self-digest mismatch"

    records = [("source", src, K.SRC), ("model", dep["model"], MODEL_PATH)]
    for group in ("casts", "masks"):
        records.extend((f"{group}[{i}]", item, None) for i, item in enumerate(dep[group]))
    if dep["graph"] is not None:
        records.append(("graph", dep["graph"], None))
    for label, item, canonical in records:
        if type(item) is not dict or set(item) < {"path", "sha256"}:
            return False, f"deps {label} file record malformed"
        raw_path, sha = item.get("path"), item.get("sha256")
        if type(raw_path) is not str or not raw_path.strip():
            return False, f"deps {label} path malformed"
        if type(sha) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
            return False, f"deps {label} hash malformed"
        path = Path(raw_path)
        if not path.is_absolute():
            return False, f"deps {label} path is not absolute"
        try:
            current = path.resolve(strict=True)
            if canonical is not None and current != Path(canonical).resolve(strict=True):
                return False, f"deps {label} path differs from current canonical path"
            now = K.sha(current)
        except (OSError, ValueError, TypeError) as exc:
            return False, f"deps {label} unreadable: {exc}"
        if now.lower() != sha.lower():
            return False, f"deps {label} hash changed: {sha} -> {now}"
    return True, "ok"


def skip_allowed(sid: str, fid: int, key_png: Path) -> tuple[bool, str]:
    """The ONLY legal skip: deps verified + key exists + review PASS (gate enforces)."""
    from r6_gate import require_review, key_inputs_now, GateBlock
    dp = K.R6 / "work" / sid / f"f_{fid:04d}.deps.json"
    if not dp.exists():
        return False, "no deps"
    dep, why = load_deps(dp)
    if why != "ok":
        return False, why
    ok, why = verify_deps(dep, sid, fid)
    if not ok:
        return False, f"dep changed: {why}"
    try:
        cur = settings_now(sid, fid)
        if dep.get("settings") != cur:
            return False, f"settings changed now: {dep.get('settings')} vs {cur}"
    except Exception as e:  # noqa: BLE001
        return False, f"settings unverifiable: {e}"
    if not (key_png.exists() and key_png.stat().st_size > 0):
        return False, "key missing/empty"
    try:
        require_review("keys", f"{sid}_f{fid:04d}", key_png, key_inputs_now(sid, fid, key_png))
    except GateBlock as e:
        return False, f"review: {e}"
    return True, "verified-reuse"
