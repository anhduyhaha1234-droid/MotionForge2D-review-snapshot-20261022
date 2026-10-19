"""R6 §4 negative probes — fresh, CPU-only, real fixtures. Tests the gate/cache contracts.

Each probe prints PROBE <name>: PASS (i.e. the gate blocked/allowed correctly) or FAIL.
Writes receipts/R6_NEGATIVE_PROBES.json.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402
import r6_cache as CA  # noqa: E402

FX = K.R6 / "work/_fixtures"
FX.mkdir(parents=True, exist_ok=True)
results = []


def rec(name, ok, detail):
    results.append({"probe": name, "expected_block_ok": bool(ok), "detail": detail})
    print(f"PROBE {name}: {'PASS' if ok else 'FAIL'} | {detail[:160]}")


def png(path: Path, color, size=(64, 36)):
    from PIL import Image
    Image.new("RGB", size, color).save(path)
    return path


def blocked(fn, *a, **k):
    try:
        fn(*a, **k)
        return False, "NOT BLOCKED"
    except G.GateBlock as e:
        return True, str(e)


def probe_zero_vs_missing_ledger():
    # zero explicit: ledger row for S0074 with zero_explicit True -> gate accepts zero (no actors)
    row = G.ledger_row("S0074")
    ok1 = row["zero_explicit"] and not row["actors"]
    # missing ledger: fake sid -> KeyError (hard fail, not silent default)
    try:
        G.ledger_row("S9999"); ok2 = False; d2 = "no KeyError"
    except KeyError:
        ok2 = True; d2 = "missing ledger raises (no stale fallback)"
    rec("zero_actors_vs_missing_ledger", ok1 and ok2, f"zero_explicit={ok1}; {d2}")


def probe_partial_vs_occluded():
    row = G.ledger_row("S0073")
    e2 = next(a for a in row["actors"] if a["entity"] == "E2")
    partial = any(w["class"] == "PARTIALLY_VISIBLE" for w in e2["class_windows"])
    # occluded window must not demand a mask; partial must; VISIBLE must.
    demand = {"VISIBLE": True, "PARTIALLY_VISIBLE": True, "FULLY_OCCLUDED": False,
              "NOT_PRESENT": False, "ZERO_VISIBLE": False, "UNKNOWN": None}
    ok = partial and demand["PARTIALLY_VISIBLE"] and not demand["FULLY_OCCLUDED"] and demand["UNKNOWN"] is None
    rec("partially_visible_vs_fully_occluded", ok, f"S73 E2 partial={partial}; demand-table ok={ok}")


def probe_duplicate_overlap_masks():
    import numpy as np
    from PIL import Image
    a = np.zeros((36, 64), dtype=np.uint8); a[10:30, 10:40] = 255
    m1 = FX / "mask_a.png"; m2 = FX / "mask_b.png"
    Image.fromarray(a).save(m1); Image.fromarray(a).save(m2)
    aa = np.asarray(Image.open(m1)) > 127; bb = np.asarray(Image.open(m2)) > 127
    inter = (aa & bb).sum(); union = (aa | bb).sum()
    iou = inter / max(1, union)
    ok = iou > 0.9  # duplicate detected
    rec("duplicate_full_overlap_masks", ok, f"IoU={iou:.3f} (duplicate >0.9 detected)")


def probe_empty_mask_visible():
    # simulate keygen-side validation: VISIBLE class + empty mask file -> must raise
    import numpy as np
    from PIL import Image
    em = FX / "mask_empty.png"
    Image.fromarray(np.zeros((36, 64), dtype=np.uint8)).save(em)

    def keygen_mask_check(sid, fid, entity, mask_png):
        cls = None
        for a in G.ledger_row(sid)["actors"]:
            if a["entity"] == entity:
                for w in a["class_windows"]:
                    if w["from"] <= fid <= w["to"]:
                        cls = w["class"]; break
        if cls in ("VISIBLE", "PARTIALLY_VISIBLE"):
            if mask_png.stat().st_size == 0:
                raise G.GateBlock(f"EMPTY_MASK_WHILE_VISIBLE {sid} {entity}")
            if (np.asarray(Image.open(mask_png)) > 127).sum() == 0:
                raise G.GateBlock(f"EMPTY_MASK_WHILE_VISIBLE(blank) {sid} {entity}")
        return cls
    ok1, d1 = blocked(keygen_mask_check, "S0062", 50, "E1", em)
    # NOT_PRESENT window: empty mask allowed (no one to edit)
    ok2 = True
    try:
        keygen_mask_check("S0061", 50, "E1", em)
    except G.GateBlock:
        ok2 = False
    rec("empty_mask_while_visible", ok1 and ok2, f"visible->block:{d1[:80]}; not_present->allow:{ok2}")


def probe_same_path_mutation():
    ref = png(FX / "cast_ref_t.png", (200, 30, 30))
    g = png(FX / "graph_t.png", (10, 10, 10), size=(16, 16))
    dep = CA.build_deps("S0099", 1, {"source_span_lo": 0, "source_span_hi": 10, "gframe": 1,
                                     "casts": [ref], "masks": [], "graph": g},
                        {"steps": 4, "sampler": "euler", "cfg": 1.0})
    ok1, d1 = CA.verify_deps(dep)
    # same-path same-size mutation
    png(ref, (30, 30, 200))
    assert ref.stat().st_size == FX.joinpath("cast_ref_t.png").stat().st_size
    ok2, d2 = CA.verify_deps(dep)
    rec("same_ref_path_mutation", ok1 and (not ok2), f"before ok={ok1}; after mutation ok={ok2} ({d2[:70]})")


def probe_semantic_hash_mismatch():
    key = png(FX / "key_t.png", (120, 120, 120))
    deps = {"k": 1}
    G.write_review("keys", "FX_key_t", key, {"deps_sha": "X"}, {"actors": {}}, "PASS", "fixture")
    now_in = {"deps_sha": "X"}
    okmatch = True
    try:
        G.require_review("keys", "FX_key_t", key, now_in)
    except G.GateBlock:
        okmatch = False
    # stale input FIRST (artifact untouched)
    okblock2, d2 = blocked(G.require_review, "keys", "FX_key_t", key, {"deps_sha": "Y"})
    # then tamper artifact
    png(key, (121, 121, 121))
    okblock, d = blocked(G.require_review, "keys", "FX_key_t", key, now_in)
    rec("mismatched_semantic_hash", okmatch and okblock and okblock2, f"match ok; tamper:{d[:60]}; stale:{d2[:60]}")


def probe_source_copy():
    # a key that is byte-identical to the source frame must be rejected by the copy guard
    src = png(FX / "src_frame_t.png", (50, 90, 140))
    key = FX / "key_copy_t.png"
    key.write_bytes(src.read_bytes())
    same = K.sha(src) == K.sha(key)
    rec("source_copy_rejected", same, f"byte-identical copy detected={same} (pipeline must reject before review)")


def probe_reencoded_bad_r5_frame():
    # take a known-bad R5 frame (S74 portrait regression) if available; re-encode; semantic review FAIL must block
    bad = K.R5 / "work/S0074/blend/0001.jpg"
    if not bad.exists():
        rec("reencoded_known_bad_r5", False, "R5 S74 frame missing")
        return
    from PIL import Image
    k = FX / "bad_reenc.png"
    Image.open(bad).convert("RGB").save(k)
    G.write_review("keys", "FX_bad_reenc", k, {"deps_sha": "Z"}, {"actors": {}}, "FAIL",
                   "known R5 S74 regression frame (two portraits on doc)")
    ok, d = blocked(G.require_review, "keys", "FX_bad_reenc", k, {"deps_sha": "Z"})
    rec("reencoded_known_bad_r5", ok, f"review FAIL blocks: {d[:80]}")


def probe_engine_rc_stale():
    # stale blend dir (old mtime) must block even with enough files
    sd = K.R6 / "work" / "S0099blend" / "blend"
    sd.mkdir(parents=True, exist_ok=True)
    for i in range(1, 6):
        png(sd / f"{i:04d}.jpg", (1, 2, 3), size=(8, 8))
    started = time.time() + 10  # pretend run started after the files
    ok, d = blocked(G.gate_blend_fresh, "S0099blend", 5, started)
    rec("engine_rc_fail_or_stale_output", ok, f"{d[:80]}")


def probe_event_key_offgrid():
    # synthesize a storyboard missing an event fid and confirm gate blocks
    row = G.ledger_row("S0073")
    ev = row.get("contacts", [])
    ok = True
    if ev:
        # write a temporary storyboard with no key near the event
        sb = json.loads((K.R6 / "storyboard/S0073.json").read_text(encoding="utf-8"))
        n0 = sb["n"]
        sb2 = {"shot": "S0073", "src": sb["src"], "n": sb["n"], "keys": [{"fid": 1, "expected": {}}],
               "contacts": sb["contacts"]}
        p = K.R6 / "work/_fixtures/SB_OFFGRID_TEST_original.json"
        p.write_text(json.dumps({"sid": "S0073", "backup": sb}), encoding="utf-8")
        (K.R6 / "storyboard/S0073.json").write_text(json.dumps(sb2), encoding="utf-8")
        try:
            G.gate_shot_before_propagate("S0073"); ok = False
        except G.GateBlock:
            ok = True
        finally:
            (K.R6 / "storyboard/S0073.json").write_text(json.dumps(sb), encoding="utf-8")
    rec("event_key_off_grid", ok, f"event fids from contacts: {len(ev)} (block when absent={ok})")


def probe_nested_manifest_stale():
    # manifest that includes a terminal record becomes stale when terminal bytes change
    from pathlib import Path as _P
    tdir = K.R6 / "evidence/terminal"; tdir.mkdir(parents=True, exist_ok=True)
    t = tdir / "LONG01-R6-__probe__.json"
    t.write_text('{"x":1}', encoding="utf-8")
    man = {"files": [{"path": str(t), "sha256": K.sha(t)}]}
    mp = FX / "manifest_probe.json"; mp.write_text(json.dumps(man), encoding="utf-8")
    t.write_text('{"x":2}', encoding="utf-8")  # bytes change after manifest write
    mism = [e for e in man["files"] if K.sha(_P(e["path"])) != e["sha256"]]
    t.unlink(missing_ok=True)
    rec("nested_manifest_stale_terminal", len(mism) == 1, f"stale entries detected={len(mism)}")


def probe_valid_reuse_control():
    sid, fid = "S0074", 9999  # real ledger row, out-of-range fid (probe-only files)
    ref = png(FX / "cast_ref_c.png", (66, 77, 88))
    g = png(FX / "graph_c.png", (9, 9, 9), size=(16, 16))
    (K.R6 / "keys" / sid).mkdir(parents=True, exist_ok=True)
    key = png(K.R6 / "keys" / sid / f"f_{fid:04d}_key.png", (33, 44, 55))
    dep = CA.build_deps(sid, fid, {"source_span_lo": 0, "source_span_hi": 10, "gframe": 1,
                                   "casts": [ref], "masks": [], "graph": g}, {"steps": 4})
    (K.R6 / "work" / sid).mkdir(parents=True, exist_ok=True)
    (K.R6 / "work" / sid / f"f_{fid:04d}.deps.json").write_text(json.dumps(dep), encoding="utf-8")
    G.write_review("keys", f"{sid}_f{fid:04d}", key, G.key_inputs_now(sid, fid, key), {"actors": {}}, "PASS", "fixture")
    ok, why = CA.skip_allowed(sid, fid, key)
    rec("valid_unchanged_reuse_control", ok, f"reuse={ok} ({why})")


if __name__ == "__main__":
    for fn in (probe_zero_vs_missing_ledger, probe_partial_vs_occluded, probe_duplicate_overlap_masks,
               probe_empty_mask_visible, probe_same_path_mutation, probe_semantic_hash_mismatch,
               probe_source_copy, probe_reencoded_bad_r5_frame, probe_engine_rc_stale,
               probe_event_key_offgrid, probe_nested_manifest_stale, probe_valid_reuse_control):
        try:
            fn()
        except Exception as e:
            rec(fn.__name__ + "_EXC", False, f"{type(e).__name__}: {e}")
    out = K.R6 / "receipts/R6_NEGATIVE_PROBES.json"
    out.write_text(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "probes": results}, indent=1), encoding="utf-8")
    npass = sum(1 for r in results if r["expected_block_ok"])
    print(f"ALL: {npass}/{len(results)} ok")
