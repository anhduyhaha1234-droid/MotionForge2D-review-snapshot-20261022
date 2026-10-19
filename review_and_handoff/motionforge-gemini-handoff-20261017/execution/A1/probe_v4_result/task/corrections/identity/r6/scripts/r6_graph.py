"""R6 klein graph builder — per-actor crop edit; CAST refs reachable in EVERY branch.

Invariant: GUIDER chain contains KEY + EACH used CAST loader. STYLE image never used.
Template: D/graph/reuse_bundle/shot_anchor_v1.baseline.api.json (read-only).
"""
from __future__ import annotations
import hashlib, json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_upload as U  # noqa: E402

TPL = K.D / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
_GRAY = None


def _gray():
    global _GRAY
    _GRAY = K.INP / "_unused_r3_slot.png"
    if not _GRAY.exists():
        from PIL import Image
        Image.new("RGB", (64, 64), (127, 127, 127)).save(_GRAY)
    return _GRAY


def reachable_nodes(g, start):
    seen, stack = set(), [start[0]]
    while stack:
        nid = stack.pop()
        if nid in seen or nid not in g:
            continue
        seen.add(nid)
        for v in g[nid].get("inputs", {}).values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                stack.append(v[0])
    return seen


def actor_edit_prompt(cast_file: str) -> str:
    return (
        "Reference image 1 is a close crop of exactly ONE animation character (possibly small, lying, "
        "seated or partially out of frame). Repaint EXACTLY that one existing character IN ITS PLACE, "
        "pixel region and pose. NEVER draw a second figure, a standing figure, a portrait or any new "
        "person anywhere. If the character is small in the crop, repaint them small; do not enlarge or "
        "move them. " + "Reference image 1 is a close crop of one animation frame. Redraw ONLY the ONE main person of "
        "reference image 1 (the person it is centred on) to look EXACTLY like "
        f"{K.CASTB_DESC[cast_file]} shown in reference image 2 (front view) and reference image 3 "
        "(profile view): same face, same hair, same clothing design and colours. The person must stay in "
        "EXACTLY the same position, scale, pose and silhouette as in reference image 1, with the same "
        "action, hand positions and held objects. Do NOT redraw, move or change any other person, object "
        "or the background that may be visible at the edges of reference image 1 - keep every non-person "
        "element identical. Do not shift, rescale or re-render the background: every background pixel in "
        "your output must match reference image 1 exactly - the background must look untouched. "
        "CRITICAL: do NOT add ANY face, head, portrait, figure or person that is not already present in "
        "reference image 1. Draw NOTHING in empty areas, sky, walls or background regions. Every object "
        "and prop of reference image 1 (book, folder, car, furniture, glass, phone) must remain EXACTLY "
        "in place - never remove, move, repaint or restyle any object. " + K.STYLE_TXT + " No text, captions, subtitles, logo or watermark anywhere in the image."
    )


def build_actor_crop_graph(sid, entity, key_crop: Path, seed, crop_size):
    cast_front = K.R4 / "assets/cast_b" / K.CASTB_OF_ENTITY[entity]
    cast_profile = K.R4 / "assets/cast_b" / K.CASTB_OF_ENTITY[entity].replace("_front_bust", "_profile")
    if not (cast_front.exists() and cast_profile.exists()):
        raise FileNotFoundError(f"cast refs missing for {entity}")
    refdir = K.INP / "keys/cast_refs"
    refdir.mkdir(parents=True, exist_ok=True)
    fr, pr = refdir / cast_front.name, refdir / cast_profile.name
    for src, dst in ((cast_front, fr), (cast_profile, pr)):
        if not dst.exists() or K.sha(dst) != K.sha(src):
            shutil.copyfile(src, dst)
    _gray()
    g = json.loads(TPL.read_text(encoding="utf-8"))
    # upload via API (server-managed listing; avoids input-dir listing cache misses)
    key_ref = U.upload_image(key_crop, "identity5m_20261008/r6/work")
    r1_ref = U.upload_image(fr, "identity5m_20261008/r6/keys/cast_refs")
    r2_ref = U.upload_image(pr, "identity5m_20261008/r6/keys/cast_refs")
    gray_ref = U.upload_image(_gray(), "identity5m_20261008/r6")
    g["KEY_LOAD"]["inputs"]["image"] = key_ref
    g["R1_LOAD"]["inputs"]["image"] = r1_ref
    g["R2_LOAD"]["inputs"]["image"] = r2_ref
    g["R3_LOAD"]["inputs"]["image"] = gray_ref
    g["PROMPT"]["inputs"]["text"] = actor_edit_prompt(K.CASTB_OF_ENTITY[entity])
    g["NOISE"]["inputs"]["noise_seed"] = seed
    for n in ("LATENT", "SIGMAS"):
        g[n]["inputs"]["width"] = crop_size[0]
        g[n]["inputs"]["height"] = crop_size[1]
    g["GUIDER"]["inputs"]["positive"] = ["R2_POS", 0]
    g["GUIDER"]["inputs"]["negative"] = ["R2_NEG", 0]
    g["SAVE"]["inputs"]["filename_prefix"] = f"identity5m_20261008/r6/r6_keys/{sid}_crop_{entity}"
    reach = reachable_nodes(g, ["R2_POS", 0]) | reachable_nodes(g, ["R2_NEG", 0])
    for need in ("KEY_LOAD", "R1_LOAD", "R2_LOAD"):
        assert need in reach, f"REACHABILITY FAIL: {need} not in GUIDER chain"
    assert "R3_LOAD" not in reach, "R3 must stay out of chain"
    refmap = [{"slot": "KEY", "role": "crop_of_source_frame", "file": key_crop.name, "sha256": K.sha16(key_crop)},
              {"slot": "R1", "role": f"{entity}:front", "file": fr.name, "sha256": K.sha16(fr)},
              {"slot": "R2", "role": f"{entity}:profile", "file": pr.name, "sha256": K.sha16(pr)}]
    return g, refmap
