"""R6 source ledger + storyboard + cast atlas (S1).

Builds C/r6/source_actor_ledger.jsonl, storyboard/<sid>.json, cast_atlas.json, event_map.json.
Source of truth: r3 SOURCE_EVENT_LEDGER (source-derived) + R6 review scene corrections + fresh vision
(S57/S61). Classes: VISIBLE / PARTIALLY_VISIBLE / FULLY_OCCLUDED / NOT_PRESENT / ZERO_VISIBLE / UNKNOWN.
Missing/empty mask is allowed ONLY where class says NOT_PRESENT / FULLY_OCCLUDED / ZERO_VISIBLE.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402

R3_LEDGER = K.C / "r3/SOURCE_EVENT_LEDGER.json"
R5_SB = K.R5 / "storyboard"

# --- overrides from O/REVIEW_VI.md (R6 scene list) + fresh vision classification (evidence file) ---
# windows are 1-based shot-local frame ids [from, to] inclusive.
OVR = {
    "S0021": {"actors": {"E4": [(1, 42, "NOT_PRESENT"), (43, 9999, "VISIBLE")]},
              "unknown": [{"entity": "S21_TRANSIENT_BACKTURN", "class": "UNKNOWN",
                           "note": "back-turned transient actor; identity unknown until verified; keeps source pixels; does NOT exempt E1/E5/E7/E4"}]},
    "S0031": {"actors": {"E2": [(1, 59, "NOT_PRESENT"), (60, 9999, "VISIBLE")]},
              "note": "E2 (entrant): SAM2 seed position verified at f60 (R6c vision); frames 20-59 keep-source (entry position unverified) - documented limitation, review may close."},
    "S0041": {"actors": {"E2": [(1, 29, "NOT_PRESENT"), (30, 9999, "VISIBLE")]}},
    "S0033": {"note": "R5 added a standing portrait - model fault; source = single lying person E8 only. E8 = E2 identity HOME state."},
    "S0034": {"note": "E8 = E2 identity HOME state; hand_R-phone contact."},
    "S0040": {"zero": True, "note": "source empty of actors (mansion/car); S7: prop/background asset reskin, keep checked text."},
    "S0057": {"actors": {"E1": [(1, 96, "VISIBLE"), (97, 9999, "ZERO_VISIBLE")],
                          "E2": [(1, 96, "VISIBLE"), (97, 9999, "ZERO_VISIBLE")]},
              "note": "head has E1+E2 (vision f1/f40); R6b SAM2 propagation measured the visible window = 96 frames; tail zero (vision f235). R5 entities=[] was wrong."},
    "S0058": {"zero": True, "note": "source empty of actors (car/building entrance); S7 asset reskin."},
    "S0059": {"zero": True, "note": "source empty of actors (car/villa); S7 asset reskin."},
    "S0060": {"zero": True, "note": "source empty of actors (sedan/riverside); S7 asset reskin."},
    "S0061": {"actors": {"E1": [(1, 103, "NOT_PRESENT"), (104, 9999, "VISIBLE")],
                          "E2": [(1, 103, "NOT_PRESENT"), (104, 9999, "VISIBLE")]},
              "note": "vision: f1/f90 empty, f130 E1+E2 at car; entry=104. R5 'imagined person before entry' = fault."},
    "S0062": {"actors": {"E6": [(1, 9999, "VISIBLE")],
                          "E1": [(1, 31, "NOT_PRESENT"), (32, 9999, "VISIBLE")],
                          "E2": [(1, 31, "NOT_PRESENT"), (32, 9999, "VISIBLE")]},
              "note": "E6 behind counter all shot; E1+E2 walk in at 32 (must reskin from entry). R5 UNBOUND_ABSENT was wrong."},
    "S0063": {"actors": {"E2": [(1, 9999, "PARTIALLY_VISIBLE")]},
              "note": "rear E2 partially visible - keep the visible part reskinned, never drop."},
    "S0067": {"actors": {"E2": [(1, 9999, "PARTIALLY_VISIBLE")]}, "note": "rear E2 partially visible."},
    "S0070": {"actors": {"E2": [(1, 9999, "FULLY_OCCLUDED")]},
              "note": "R5 wrong person/position fault. R6b fresh vision f1+f60: third person NOT visible - reclass PARTIALLY_VISIBLE -> FULLY_OCCLUDED (no mask demanded, empty tolerated)."},
    "S0073": {"actors": {"E2": [(1, 9999, "PARTIALLY_VISIBLE")]},
              "contacts_keep": True,
              "note": "pickup/hold book with E6 must persist; rear E2 partially visible; R5 lost both."},
    "S0074": {"zero": True, "note": "document close-up, source-confirmed zero actors (r3 props 'doc close-up whole shot'); R5 E1/E2 + two portraits = regression."},
}

CONTACT_MISS_KEEP = {"S0043": "hand_R folder from 40", "S0044": "folder continuity", "S0053": "folder", "S0055": "folder", "S0034": "hand_R phone", "S0024": "hand_R phone"}


def main():
    led = json.loads(R3_LEDGER.read_text(encoding="utf-8"))
    rows = []
    for sid in K.SHOTS:
        if sid not in led["shots"]:
            raise SystemExit(f"missing r3 row {sid}")
        r3 = led["shots"][sid]
        a0, b0 = r3["src"]
        n = b0 - a0
        ovr = OVR.get(sid, {})
        actors = []
        for act in r3["actors"]:
            e = act["entity"]
            cast = K.CASTB_OF_ENTITY[e]
            wins = ovr.get("actors", {}).get(e)
            if wins is None:
                wins = [(1, n, "VISIBLE")]
            wins = [(f, min(t, n), c) for f, t, c in wins]
            actors.append({"entity": e, "cast": cast, "role": act.get("role", ""),
                           "class_windows": [{"from": f, "to": t, "class": c} for f, t, c in wins],
                           "evidence": (["O/REVIEW_VI.md scene corrections"] if e in ovr.get("actors", {}) else ["r3 SOURCE_EVENT_LEDGER (carried)"])})
        for e, wins in ovr.get("actors", {}).items():
            if any(a["entity"] == e for a in actors):
                continue
            fw = [(f, min(t, n), c) for f, t, c in wins]
            actors.append({"entity": e, "cast": K.CASTB_OF_ENTITY[e], "role": "",
                           "class_windows": [{"from": f, "to": t, "class": c} for f, t, c in fw],
                           "evidence": ["O/REVIEW_VI.md + fresh vision (r6/evidence/R6_classify_S57_S61.png)"]})
        row = {
            "shot": sid, "src": [a0, b0], "n": n, "fps": K.FPS,
            "zero_explicit": len(actors) == 0,
            "actors": actors,
            "unknown_entities": ovr.get("unknown", []),
            "props": r3.get("props", []), "camera": r3.get("camera", ""),
            "events": r3.get("events", []), "contacts": r3.get("contacts", []),
            "notes": ovr.get("note", ""),
            "provenance": ["r3/SOURCE_EVENT_LEDGER.json", "O/REVIEW_VI.md", "r6/evidence/R6_classify_S57_S61.png (fresh vision)"],
        }
        if sid in CONTACT_MISS_KEEP:
            row["contact_keep"] = CONTACT_MISS_KEEP[sid]
        rows.append(row)
    out = K.R6 / "source_actor_ledger.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # storyboard per shot: keys fids from r5 grid (structure only), expected classes per key
    sb_dir = K.R6 / "storyboard"
    nevents = 0
    for r in rows:
        sid = r["shot"]
        grid = json.loads((R5_SB / f"{sid}.json").read_text(encoding="utf-8"))
        fids = [k["fid"] for k in grid["keys"]]
        from r6_propagate import event_fids_for
        ev_fids = event_fids_for(sid, r)
        all_fids = sorted(set(fids) | ev_fids)
        keys = []
        for fid in all_fids:
            exp = {}
            for a in r["actors"]:
                cls = "NOT_PRESENT"
                for w in a["class_windows"]:
                    if w["from"] <= fid <= w["to"]:
                        cls = w["class"]
                        break
                exp[a["entity"]] = cls
            keys.append({"fid": fid, "expected": exp})
            nevents += 0
        sb = {"shot": sid, "src": [r["src"][0], r["src"][1]], "n": r["n"], "fps": K.FPS,
              "entities": [a["entity"] for a in r["actors"]], "zero_explicit": r["zero_explicit"],
              "unknown_entities": r["unknown_entities"], "keys": keys, "contacts": r["contacts"],
              "notes": r["notes"]}
        (sb_dir / f"{sid}.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
    # cast atlas
    refdir = K.R4 / "assets/cast_b"
    atlas = {"at": "2026-10-12", "board_sha256": "95572075bd72010854b5e82c5d97e1a5d83199409999370e0a506821dda95415",
             "entities": {}}
    for e, cast in K.CASTB_OF_ENTITY.items():
        front = refdir / cast
        prof = refdir / cast.replace("_front_bust", "_profile")
        atlas["entities"][e] = {"cast": cast, "desc": K.CASTB_DESC[cast],
                                "front": {"file": cast, "sha256": K.sha(front) if front.exists() else None},
                                "profile": {"file": prof.name, "sha256": K.sha(prof) if prof.exists() else None},
                                "provisional": e in ("E4", "E8")}
    (K.R6 / "cast_atlas.json").write_text(json.dumps(atlas, ensure_ascii=False, indent=1), encoding="utf-8")
    # event map (events + contacts per shot at fids)
    em = {"at": "2026-10-12", "shots": {r["shot"]: {"events": r["events"], "contacts": r["contacts"]} for r in rows}}
    (K.R6 / "event_map.json").write_text(json.dumps(em, ensure_ascii=False, indent=1), encoding="utf-8")
    # validation receipt
    zc = [r["shot"] for r in rows if r["zero_explicit"]]
    unk = [r["shot"] for r in rows if r["unknown_entities"]]
    vis = sum(1 for r in rows for a in r["actors"] if any(w["class"] == "VISIBLE" for w in a["class_windows"]))
    part = sum(1 for r in rows for a in r["actors"] if any(w["class"] == "PARTIALLY_VISIBLE" for w in a["class_windows"]))
    np_ = sum(1 for r in rows for a in r["actors"] if any(w["class"] == "NOT_PRESENT" for w in a["class_windows"]))
    val = {"shots": len(rows), "zero_explicit": zc, "unknown_entities": unk,
           "visible_actors": vis, "partially_visible_actors": part, "not_present_windows": np_,
           "ledger": str(out), "at": "2026-10-12"}
    (K.R6 / "receipts/R6_LEDGER_VALIDATION.json").write_text(json.dumps(val, indent=1), encoding="utf-8")
    print(json.dumps(val, ensure_ascii=False))


if __name__ == "__main__":
    main()
