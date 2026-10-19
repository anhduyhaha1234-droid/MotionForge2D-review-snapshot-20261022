"""Deterministic, read-only effective recipe for R6 per-actor keys."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path

import r6_common as K


def _strict_json(path: Path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate field {key} in {path}")
            value[key] = item
        return value

    def reject(value):
        raise ValueError(f"nonfinite JSON value {value} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=reject)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def _node_input(graph, node, field, expected_type):
    value = graph[node]["inputs"][field]
    if type(value) is not expected_type or (expected_type is str and not value.strip()):
        raise ValueError(f"template {node}.{field} invalid")
    return value


def current_recipe(sid: str, fid: int, model_path: Path) -> dict:
    """Resolve effective selection/settings without staging, crop, upload or graph generation."""
    import r6_graph as G

    if type(sid) is not str or not re.fullmatch(r"S[0-9]{4}", sid):
        raise ValueError("invalid shot")
    if type(fid) is not int or fid < 1:
        raise ValueError("invalid fid")
    plan = K.PLAN.get(sid)
    if type(plan) is not dict or type(plan.get("start_frame")) is not int or type(plan.get("frames")) is not int:
        raise ValueError("shot absent from plan")
    if fid > plan["frames"]:
        raise ValueError("fid outside shot plan")
    row = None
    for line in (K.R6 / "source_actor_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        candidate = json.loads(line)
        if candidate.get("shot") == sid:
            row = candidate
            break
    if type(row) is not dict or row.get("zero_explicit") is not False:
        raise ValueError("per-actor ledger row absent or ZERO_EXPLICIT")
    if (type(row.get("n")) is not int or row["n"] != plan["frames"] or
            row.get("src") != [plan["start_frame"], plan["start_frame"] + plan["frames"]] or
            type(row.get("actors")) is not list):
        raise ValueError("ledger row disagrees with current plan")
    board = _strict_json(K.R6 / "storyboard" / f"{sid}.json")
    if type(board) is not dict or board.get("zero_explicit") is not False:
        raise ValueError("per-actor storyboard absent or ZERO_EXPLICIT")
    if "n" in board and (type(board["n"]) is not int or board["n"] != row["n"]):
        raise ValueError("storyboard span disagrees with ledger")

    only = os.environ.get("R6_ONLY_ENTITY") or None
    if only is not None and only not in [a.get("entity") for a in row["actors"] if type(a) is dict]:
        raise ValueError("R6_ONLY_ENTITY absent from ledger")
    selected = []
    for actor in row["actors"]:
        if type(actor) is not dict or type(actor.get("entity")) is not str or type(actor.get("class_windows")) is not list:
            raise ValueError("actor ledger malformed")
        cls = None
        for window in actor["class_windows"]:
            if window["from"] <= fid <= window["to"]:
                cls = window["class"]
                break
        if cls in ("VISIBLE", "PARTIALLY_VISIBLE") and (only is None or actor["entity"] == only):
            selected.append({"entity": actor["entity"], "class": cls})
    if len({a["entity"] for a in selected}) != len(selected):
        raise ValueError("duplicate selected entity")

    try:
        ctx = float(os.environ.get("R6_CTX_FACTOR", "1.02"))
        off = int(os.environ.get("R6_SEED_OFF", "0"))
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid crop context or seed offset") from exc
    if not math.isfinite(ctx) or ctx <= 0:
        raise ValueError("crop context must be positive finite")
    seed = 2026101400 + int(sid[1:]) * 1000 + fid + off
    if seed < 0 or seed > (1 << 64) - 1:
        raise ValueError("effective seed outside uint64")

    graph = _strict_json(G.TPL)
    try:
        steps = _node_input(graph, "SIGMAS", "steps", int)
        sampler = _node_input(graph, "SAMPLER", "sampler_name", str)
        cfg = graph["GUIDER"]["inputs"]["cfg"]
        unet = _node_input(graph, "UNET", "unet_name", str)
        clip = _node_input(graph, "CLIP", "clip_name", str)
        vae = _node_input(graph, "VAE", "vae_name", str)
        _node_input(graph, "NOISE", "noise_seed", int)
        graph["LATENT"]["inputs"]["width"]
        graph["LATENT"]["inputs"]["height"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"incomplete graph template: {exc}") from exc
    if (steps < 1 or type(cfg) not in (int, float) or not math.isfinite(cfg) or cfg <= 0 or
            unet != Path(model_path).name):
        raise ValueError("invalid effective template steps/CFG/model")
    cast = []
    for item in selected:
        entity = item["entity"]
        front = K.CASTB_OF_ENTITY[entity]
        description = K.CASTB_DESC[front]
        cast.append({"entity": entity, "front": front,
                     "profile": front.replace("_front_bust", "_profile"),
                     "description": description, "prompt": G.actor_edit_prompt(front)})
    code = {name: K.sha(Path(__file__).parent / name) for name in
            ("r6_key_recipe.py", "r6_keygen.py", "r6_graph.py", "r6_adapter.py",
             "r6_upload.py", "r6_common.py")}
    return {"mode": "per_actor_klein" if selected else "keep_source_no_visible_actor",
            "shot": sid, "fid": fid, "gframe": plan["start_frame"] + fid - 1,
            "span": [plan["start_frame"], plan["start_frame"] + plan["frames"]],
            "ledger_row_sha": _digest(row), "storyboard_sha": _digest(board),
            "only_entity": only, "selection": selected, "casts": cast,
            "ctx_factor": ctx, "seed_off": off, "seed": seed,
            "steps": steps, "sampler": sampler, "cfg": float(cfg),
            "model_name": unet, "clip_name": clip, "vae_name": vae,
            "template": {"path": str(G.TPL.resolve(strict=True)), "sha256": K.sha(G.TPL)},
            "code_sha256": code}
