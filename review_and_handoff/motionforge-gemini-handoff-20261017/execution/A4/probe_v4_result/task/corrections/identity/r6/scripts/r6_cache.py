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
COMPLETE_KIND = "r6_key_deps_v4_per_actor"
COMPLETE_ASSET_KIND = "r6_key_deps_v4_asset"


def settings_now(sid: str, fid: int) -> dict:
    """Consumer-side CURRENT settings (F06): what this consumer would use NOW, not what it wrote."""
    import os
    sb = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
    return {"mode": "zero_shot_asset_restyle" if sb.get("zero_explicit") else "per_actor_klein",
            "steps": 4, "ctx_factor": os.environ.get("R6_CTX_FACTOR", "1.02"),
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


def _file_record(path: Path, role: str, entity: str | None = None) -> dict:
    current = Path(path).resolve(strict=True)
    if not current.is_file():
        raise ValueError(f"{role} is not a file: {current}")
    record = {"role": role, "path": str(current), "sha256": K.sha(current)}
    if entity is not None:
        record["entity"] = entity
    return record


def build_complete_deps(sid: str, fid: int, recipe: dict, consumed: dict) -> dict:
    """Build the new complete per-actor contract; legacy build_deps stays v3."""
    from r6_key_recipe import current_recipe

    if json.dumps(recipe, sort_keys=True, allow_nan=False) != json.dumps(
            current_recipe(sid, fid, MODEL_PATH), sort_keys=True, allow_nan=False):
        raise ValueError("recipe changed during generation")
    actors = []
    for actor in consumed["actors"]:
        item = {"entity": actor["entity"], "class": actor["class"], "status": actor["status"]}
        if item["status"] == "generated":
            for role in ("auth_front", "auth_profile", "staged_front", "staged_profile",
                         "crop", "edit", "graph"):
                item[role] = _file_record(actor[role], role, item["entity"])
        actors.append(item)
    dep = {"kind": COMPLETE_KIND, "shot": sid, "fid": fid,
           "source": _file_record(K.SRC, "source"),
           "model": _file_record(MODEL_PATH, "model"),
           "recipe": recipe,
           "consumed": {"staged_source": _file_record(consumed["staged_source"], "staged_source"),
                        "stage_receipt": _file_record(consumed["stage_receipt"], "stage_receipt"),
                        "masks": [_file_record(path, "mask", entity) for entity, path in consumed["masks"]],
                        "actors": actors},
           "exclusion": "R3_LOAD gray upload is unreachable from GUIDER; it cannot affect the saved key"}
    dep["deps_sha"] = hashlib.sha256(json.dumps(dep, sort_keys=True).encode()).hexdigest()
    ok, why = verify_deps(dep, sid, fid)
    if not ok:
        raise ValueError(f"complete dependency claim invalid: {why}")
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


MAX_DEPS_JSON_DEPTH = 256


def _json_value(value):
    """Reject non-JSON values and deep records without recursive Python calls."""
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if item is None or type(item) in (str, bool, int):
            continue
        if type(item) is float:
            if not math.isfinite(item):
                return False
            continue
        if type(item) is list:
            if depth >= MAX_DEPS_JSON_DEPTH:
                return False
            pending.extend((child, depth + 1) for child in item)
            continue
        if type(item) is dict:
            if depth >= MAX_DEPS_JSON_DEPTH:
                return False
            for key, child in item.items():
                if type(key) is not str or not key.strip():
                    return False
                pending.append((child, depth + 1))
            continue
        return False
    return True


def _check_complete_file(item, role: str, expected: Path | None = None,
                         entity: str | None = None, root: Path | None = None) -> Path:
    keys = {"role", "path", "sha256"} | ({"entity"} if entity is not None else set())
    if type(item) is not dict or set(item) != keys or item.get("role") != role:
        raise ValueError(f"{role} file record malformed")
    if entity is not None and item.get("entity") != entity:
        raise ValueError(f"{role} entity mismatch")
    raw, sha = item.get("path"), item.get("sha256")
    if type(raw) is not str or not raw.strip() or not Path(raw).is_absolute():
        raise ValueError(f"{role} path malformed")
    if type(sha) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
        raise ValueError(f"{role} hash malformed")
    current = Path(raw).resolve(strict=True)
    if not current.is_file():
        raise ValueError(f"{role} path is not a file")
    if expected is not None and current != Path(expected).resolve(strict=True):
        raise ValueError(f"{role} differs from current canonical path")
    if root is not None and not current.is_relative_to(Path(root).resolve(strict=True)):
        raise ValueError(f"{role} outside allowed output root")
    if K.sha(current).lower() != sha.lower():
        raise ValueError(f"{role} hash changed")
    return current


def _verify_actor_graph(path: Path, recipe: dict, actor: dict, crop: Path,
                        staged_front: Path, staged_profile: Path) -> None:
    from r6_key_recipe import _strict_json
    import r6_graph as G

    graph = _strict_json(path)
    inp = lambda node, field: graph[node]["inputs"][field]
    if (type(inp("NOISE", "noise_seed")) is not int or inp("NOISE", "noise_seed") != recipe["seed"] or
            type(inp("SIGMAS", "steps")) is not int or inp("SIGMAS", "steps") != recipe["steps"] or
            inp("SAMPLER", "sampler_name") != recipe["sampler"] or
            type(inp("GUIDER", "cfg")) not in (int, float) or
            not math.isfinite(inp("GUIDER", "cfg")) or
            inp("GUIDER", "cfg") != recipe["cfg"] or
            inp("UNET", "unet_name") != recipe["model_name"] or
            inp("CLIP", "clip_name") != recipe["clip_name"] or
            inp("VAE", "vae_name") != recipe["vae_name"]):
        raise ValueError("generated graph effective model/settings differ from recipe")
    for node, file in (("KEY_LOAD", crop), ("R1_LOAD", staged_front),
                       ("R2_LOAD", staged_profile)):
        image = inp(node, "image")
        if type(image) is not str or Path(image).name != file.name:
            raise ValueError(f"generated graph {node} input differs from consumed file")
    cast = next(c for c in recipe["casts"] if c["entity"] == actor["entity"])
    if inp("PROMPT", "text") != cast["prompt"]:
        raise ValueError("generated graph prompt differs from recipe")
    if (inp("GUIDER", "positive") != ["R2_POS", 0] or
            inp("GUIDER", "negative") != ["R2_NEG", 0]):
        raise ValueError("generated graph guider chain changed")
    reachable = G.reachable_nodes(graph, ["R2_POS", 0]) | G.reachable_nodes(graph, ["R2_NEG", 0])
    if not {"KEY_LOAD", "R1_LOAD", "R2_LOAD"} <= reachable or "R3_LOAD" in reachable:
        raise ValueError("generated graph input reachability changed")
    dimensions = [inp(node, axis) for node in ("LATENT", "SIGMAS") for axis in ("width", "height")]
    if any(type(v) is not int or v < 1 for v in dimensions) or dimensions[:2] != dimensions[2:]:
        raise ValueError("generated graph crop dimensions malformed")


def verify_complete_deps(dep: dict, sid: str | None = None,
                         fid: int | None = None) -> tuple[bool, str]:
    """Verify current recipe, complete selected inputs and actual generated graphs."""
    from r6_key_recipe import current_recipe

    try:
        if type(dep) is not dict or set(dep) != {"kind", "shot", "fid", "source", "model",
                                                "recipe", "consumed", "exclusion", "deps_sha"}:
            raise ValueError("complete record fields malformed")
        if dep["kind"] != COMPLETE_KIND or type(dep["shot"]) is not str or type(dep["fid"]) is not int:
            raise ValueError("complete record kind/identity malformed")
        if sid is not None and (type(sid) is not str or dep["shot"] != sid):
            raise ValueError("complete record shot differs from request")
        if fid is not None and (type(fid) is not int or dep["fid"] != fid):
            raise ValueError("complete record fid differs from request")
        if not _json_value(dep):
            raise ValueError("complete record contains deep, non-JSON or nonfinite values")
        seal = dep["deps_sha"]
        if type(seal) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", seal):
            raise ValueError("complete self-digest malformed")
        body = {key: value for key, value in dep.items() if key != "deps_sha"}
        if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != seal.lower():
            raise ValueError("complete self-digest mismatch")
        recipe = current_recipe(dep["shot"], dep["fid"], MODEL_PATH)
        if (type(dep["recipe"]) is not dict or
                json.dumps(dep["recipe"], sort_keys=True) != json.dumps(recipe, sort_keys=True)):
            raise ValueError("current per-actor recipe changed")
        _check_complete_file(dep["source"], "source", K.SRC)
        _check_complete_file(dep["model"], "model", MODEL_PATH)
        consumed = dep["consumed"]
        if type(consumed) is not dict or set(consumed) != {"staged_source", "stage_receipt", "masks", "actors"}:
            raise ValueError("complete consumed collection malformed")
        work = K.R6 / "work" / dep["shot"]
        staged = _check_complete_file(consumed["staged_source"], "staged_source",
                                      work / f"f_{dep['fid']:04d}_src.png")
        receipt = _check_complete_file(consumed["stage_receipt"], "stage_receipt",
                                       staged.with_name(staged.name + ".stage.json"))
        stage = K._stage_record(receipt)
        if (stage is None or stage["contract"] != K._STAGE_CONTRACT or
                stage["source_path"] != str(Path(K.SRC).resolve(strict=True)) or
                stage["source_sha256"] != dep["source"]["sha256"] or
                stage["sid"] != dep["shot"] or stage["gframe"] != recipe["gframe"] or
                stage["output_path"] != str(staged) or
                stage["output_sha256"] != consumed["staged_source"]["sha256"] or
                stage["output_size"] != staged.stat().st_size):
            raise ValueError("staged source receipt differs from source/frame/output")
        selection = recipe["selection"]
        masks, actors = consumed["masks"], consumed["actors"]
        if type(masks) is not list or len(masks) != len(selection):
            raise ValueError("selected mask collection incomplete")
        if type(actors) is not list or len(actors) != len(selection):
            raise ValueError("selected actor outcome collection incomplete")
        import numpy as np
        from PIL import Image
        used_masks = []
        for idx, selected in enumerate(selection):
            entity = selected["entity"]
            mask_path = _check_complete_file(masks[idx], "mask",
                                             K.R6 / "masks" / dep["shot"] / entity / f"f_{dep['fid']:04d}.png",
                                             entity)
            # Exact r6_adapter.load_mask threshold, without importing its
            # vendored CropAndStitch processor into key/assembly gates.
            with Image.open(mask_path) as image:
                mask = (np.asarray(image.convert("L"), dtype=np.float32) / 255.0) > 0.5
            if mask.ndim != 2 or int(mask.sum()) < 4:
                raise ValueError(f"selected mask empty/malformed: {entity}")
            effective = mask.copy()
            for prior in used_masks:
                if prior.shape == mask.shape:
                    effective &= ~prior
            status = "fully_covered" if int(effective.sum()) < 4 else "generated"
            actor = actors[idx]
            if (type(actor) is not dict or actor.get("entity") != entity or
                    actor.get("class") != selected["class"] or actor.get("status") != status):
                raise ValueError(f"actor outcome differs from current masks/selection: {entity}")
            if status == "fully_covered":
                if set(actor) != {"entity", "class", "status"}:
                    raise ValueError("covered actor claims generated inputs")
                continue
            used_masks.append(mask)
            if set(actor) != {"entity", "class", "status", "auth_front", "auth_profile",
                              "staged_front", "staged_profile", "crop", "edit", "graph"}:
                raise ValueError("generated actor consumed collection incomplete")
            cast = recipe["casts"][idx]
            front = _check_complete_file(actor["auth_front"], "auth_front",
                                         K.R4 / "assets/cast_b" / cast["front"], entity)
            profile = _check_complete_file(actor["auth_profile"], "auth_profile",
                                           K.R4 / "assets/cast_b" / cast["profile"], entity)
            staged_front = _check_complete_file(actor["staged_front"], "staged_front",
                                                K.INP / "keys/cast_refs" / front.name, entity)
            staged_profile = _check_complete_file(actor["staged_profile"], "staged_profile",
                                                  K.INP / "keys/cast_refs" / profile.name, entity)
            if K.sha(front) != K.sha(staged_front) or K.sha(profile) != K.sha(staged_profile):
                raise ValueError("staged CAST reference differs from authority")
            crop = _check_complete_file(actor["crop"], "crop",
                                        work / f"f_{dep['fid']:04d}_{entity}_crop.png", entity)
            _check_complete_file(actor["edit"], "edit", entity=entity, root=K.D / "output")
            graph = _check_complete_file(actor["graph"], "graph",
                                         K.R6 / "workflows" / f"r6_crop_{dep['shot']}_f{dep['fid']}_{entity}.json", entity)
            _verify_actor_graph(graph, recipe, actor, crop, staged_front, staged_profile)
        if dep["exclusion"] != "R3_LOAD gray upload is unreachable from GUIDER; it cannot affect the saved key":
            raise ValueError("R3 exclusion statement changed")
        return True, "ok"
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError,
            AttributeError, RecursionError, OverflowError, StopIteration) as exc:
        return False, f"complete deps invalid: {exc}"



def build_complete_asset_deps(sid: str, fid: int, recipe: dict, consumed: dict, mode: str) -> dict:
    """Build the complete v4 asset contract."""
    from r6_key_recipe import current_asset_recipe
    if mode not in ("zero_shot_asset_restyle", "asset_black_passthrough"):
        raise ValueError(f"invalid asset mode: {mode}")
    cur_recipe = current_asset_recipe(sid, fid, MODEL_PATH)
    if json.dumps(recipe, sort_keys=True, allow_nan=False) != json.dumps(
            cur_recipe, sort_keys=True, allow_nan=False):
        raise ValueError("asset recipe changed during generation")

    consumed_rec = {
        "staged_source": _file_record(consumed["staged_source"], "staged_source"),
        "stage_receipt": _file_record(consumed["stage_receipt"], "stage_receipt")
    }
    if mode == "zero_shot_asset_restyle":
        consumed_rec["graph"] = _file_record(consumed["graph"], "graph")
        if "grey_ref" in consumed and consumed["grey_ref"]:
            consumed_rec["grey_ref"] = _file_record(consumed["grey_ref"], "grey_ref")
    else:
        consumed_rec["graph"] = None

    dep = {
        "kind": COMPLETE_ASSET_KIND,
        "shot": sid,
        "fid": fid,
        "mode": mode,
        "source": _file_record(K.SRC, "source"),
        "model": _file_record(MODEL_PATH, "model"),
        "recipe": recipe,
        "consumed": consumed_rec
    }
    dep["deps_sha"] = hashlib.sha256(json.dumps(dep, sort_keys=True).encode()).hexdigest()
    ok, why = verify_complete_asset_deps(dep, sid, fid)
    if not ok:
        raise ValueError(f"complete asset dependency claim invalid: {why}")
    return dep


def _verify_asset_graph(path: Path, recipe: dict, staged_source: Path) -> None:
    from r6_key_recipe import _strict_json
    graph = _strict_json(path)
    inp = lambda node, field: graph[node]["inputs"][field]
    if (type(inp("NOISE", "noise_seed")) is not int or inp("NOISE", "noise_seed") != recipe["seed"] or
            type(inp("SIGMAS", "steps")) is not int or inp("SIGMAS", "steps") != recipe["steps"] or
            type(inp("GUIDER", "cfg")) not in (int, float) or
            not math.isfinite(inp("GUIDER", "cfg")) or
            inp("GUIDER", "cfg") != recipe["cfg"] or
            inp("UNET", "unet_name") != recipe["model_name"] or
            inp("CLIP", "clip_name") != recipe["clip_name"] or
            inp("VAE", "vae_name") != recipe["vae_name"]):
        raise ValueError("generated asset graph effective model/settings differ from recipe")
    key_img = inp("KEY_LOAD", "image")
    if type(key_img) is not str or Path(key_img).name != staged_source.name:
        raise ValueError("generated asset graph KEY_LOAD input differs from consumed staged source")
    if inp("PROMPT", "text") != recipe["prompt"]:
        raise ValueError("generated asset graph prompt differs from recipe")
    if (inp("GUIDER", "positive") != ["R2_POS", 0] or
            inp("GUIDER", "negative") != ["R2_NEG", 0]):
        raise ValueError("generated asset graph guider chain changed")


def verify_complete_asset_deps(dep: dict, sid: str | None = None,
                               fid: int | None = None) -> tuple[bool, str]:
    """Verify current asset recipe, complete selected inputs and actual generated graphs."""
    from r6_key_recipe import current_asset_recipe
    try:
        if type(dep) is not dict or set(dep) != {"kind", "shot", "fid", "mode", "source", "model",
                                                "recipe", "consumed", "deps_sha"}:
            raise ValueError("complete asset record fields malformed")
        if dep["kind"] != COMPLETE_ASSET_KIND or type(dep["shot"]) is not str or type(dep["fid"]) is not int:
            raise ValueError("complete asset record kind/identity malformed")
        if sid is not None and (type(sid) is not str or dep["shot"] != sid):
            raise ValueError("complete asset record shot differs from request")
        if fid is not None and (type(fid) is not int or dep["fid"] != fid):
            raise ValueError("complete asset record fid differs from request")
        mode = dep["mode"]
        if mode not in ("zero_shot_asset_restyle", "asset_black_passthrough"):
            raise ValueError(f"invalid asset mode: {mode}")
        if not _json_value(dep):
            raise ValueError("complete asset record contains deep, non-JSON or nonfinite values")
        seal = dep["deps_sha"]
        if type(seal) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", seal):
            raise ValueError("complete asset self-digest malformed")
        body = {k: v for k, v in dep.items() if k != "deps_sha"}
        if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != seal.lower():
            raise ValueError("complete asset self-digest mismatch")

        recipe = current_asset_recipe(dep["shot"], dep["fid"], MODEL_PATH)
        if (type(dep["recipe"]) is not dict or
                json.dumps(dep["recipe"], sort_keys=True) != json.dumps(recipe, sort_keys=True)):
            raise ValueError("current asset recipe changed")

        _check_complete_file(dep["source"], "source", K.SRC)
        _check_complete_file(dep["model"], "model", MODEL_PATH)
        consumed = dep["consumed"]
        if type(consumed) is not dict or not ({"staged_source", "stage_receipt"} <= set(consumed)):
            raise ValueError("complete asset consumed collection malformed")
        work = K.R6 / "work" / dep["shot"]
        staged = _check_complete_file(consumed["staged_source"], "staged_source",
                                      work / f"f_{dep['fid']:04d}_src.png")
        receipt = _check_complete_file(consumed["stage_receipt"], "stage_receipt",
                                       staged.with_name(staged.name + ".stage.json"))
        stage = K._stage_record(receipt)
        if (stage is None or stage["contract"] != K._STAGE_CONTRACT or
                stage["source_path"] != str(Path(K.SRC).resolve(strict=True)) or
                stage["source_sha256"] != dep["source"]["sha256"] or
                stage["sid"] != dep["shot"] or stage["gframe"] != recipe["gframe"] or
                stage["output_path"] != str(staged) or
                stage["output_sha256"] != consumed["staged_source"]["sha256"] or
                stage["output_size"] != staged.stat().st_size):
            raise ValueError("staged source receipt differs from source/frame/output")

        from PIL import Image
        import numpy as np
        with Image.open(staged) as img:
            arr = np.asarray(img.convert("RGB"))
        std = float(arr.std())
        if mode == "asset_black_passthrough":
            if std >= 6.0:
                raise ValueError(f"black passthrough claimed on non-flat frame (std={std:.2f} >= 6.0)")
            if consumed.get("graph") is not None:
                raise ValueError("black passthrough must not claim generated graph")
        else:
            if std < 6.0:
                raise ValueError(f"restyle claimed on flat black frame (std={std:.2f} < 6.0)")
            if "graph" not in consumed or consumed["graph"] is None:
                raise ValueError("restyle mode missing graph")
            gp = _check_complete_file(consumed["graph"], "graph",
                                      K.R6 / "workflows" / f"r6_asset_{dep['shot']}_f{dep['fid']}.json")
            if "grey_ref" in consumed and consumed["grey_ref"]:
                _check_complete_file(consumed["grey_ref"], "grey_ref", K.INP / "_grey_64.png")
            _verify_asset_graph(gp, recipe, staged)
        return True, "ok"
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError,
            AttributeError, RecursionError, OverflowError) as exc:
        return False, f"complete asset deps invalid: {exc}"


def verify_deps(dep: dict, sid: str | None = None, fid: int | None = None) -> tuple[bool, str]:
    """Verify a complete recorded v3 dependency against current files and request."""
    if type(dep) is dict:
        if dep.get("kind") == COMPLETE_KIND:
            return verify_complete_deps(dep, sid, fid)
        if dep.get("kind") == COMPLETE_ASSET_KIND:
            return verify_complete_asset_deps(dep, sid, fid)
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
    try:
        actual_sha = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    except (RecursionError, TypeError, ValueError, OverflowError) as exc:
        return False, f"deps digest unencodable: {exc}"
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
    if dep.get("kind") not in (COMPLETE_KIND, COMPLETE_ASSET_KIND):
        # v3 remains available to historical recorded-file gates, but cannot
        # authorize a new per-actor skip even if its shallow settings align.
        try:
            cur = settings_now(sid, fid)
            if dep.get("settings") != cur:
                return False, f"settings changed now: {dep.get('settings')} vs {cur}"
        except Exception as e:  # noqa: BLE001
            return False, f"settings unverifiable: {e}"
        return False, "legacy v3 lacks complete per-actor provenance"
    if not (key_png.exists() and key_png.stat().st_size > 0):
        return False, "key missing/empty"
    try:
        require_review("keys", f"{sid}_f{fid:04d}", key_png, key_inputs_now(sid, fid, key_png))
    except GateBlock as e:
        return False, f"review: {e}"
    return True, "verified-reuse"
