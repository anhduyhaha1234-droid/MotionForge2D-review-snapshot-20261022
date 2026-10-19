"""R6 SAM2 — canonical 640x360 masks per entity; class-aware validation; r6-only outputs.

Writes R6/masks/<sid>/<entity>/f_XXXX.png (640x360) + receipts/R6_SAM2_RUNS.jsonl.
Validation: in VISIBLE/PARTIALLY_VISIBLE windows a mask must be non-empty for every frame;
violations are recorded and the run exits rc=2 (block) while keeping masks for repair.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402

SEEDS = {
    "S0022": {"E1": {"pos": [(155, 110), (157, 175)], "neg": [(240, 160), (320, 160), (40, 130)]},
              "E2": {"pos": [(467, 115), (462, 180)], "neg": [(420, 160), (560, 200)]}},
    "S0023": {"E2": {"pos": [(320, 150), (320, 250)], "neg": [(150, 290), (520, 280)]}},
    "S0024": {"E1": {"pos": [(160, 220), (160, 250)], "neg": [(420, 300), (200, 120)]},
              "E2": {"pos": [(500, 150), (505, 200), (500, 250)], "neg": [(300, 300), (200, 300)]}},
    "S0031": {"E1": {"pos": [(105, 85), (105, 130)], "neg": [(240, 160)]},
              "E3": {"pos": [(262, 90), (262, 135)], "neg": []},
              "E2": {"pos": [(518, 162), (518, 200)], "neg": [], "seed_frame": 59}},
    "S0041": {"E1": {"pos": [(100, 85), (100, 130)], "neg": []},
              "E3": {"pos": [(255, 88), (255, 135)], "neg": []},
              "E2": {"pos": [(570, 210), (570, 155)], "neg": [], "seed_frame": 29}},
    "S0057": {"E1": {"pos": [(295, 185), (295, 240)], "neg": []},
              "E2": {"pos": [(365, 185), (365, 240)], "neg": []}},
    "S0061": {"E1": {"pos": [(410, 216), (408, 235)], "neg": [], "seed_frame": 103},
              "E2": {"pos": [(452, 217), (450, 236)], "neg": [], "seed_frame": 103}},
    "S0062": {"E6": {"pos": [(140, 100), (140, 140)], "neg": [(300, 250), (500, 300)]},
              "E1": {"pos": [(510, 200), (510, 250)], "neg": [], "seed_frame": 31},
              "E2": {"pos": [(600, 175), (600, 240)], "neg": [], "seed_frame": 31}},
    "S0063": {"E6": {"pos": [(150, 175), (150, 230)], "neg": []},
              "E1": {"pos": [(470, 148), (470, 210)], "neg": []},
              "E2": {"pos": [(425, 132), (430, 140)], "neg": [], "partial_head": True}},
    "S0067": {"E6": {"pos": [(140, 182), (140, 240)], "neg": []},
              "E1": {"pos": [(465, 165), (465, 228)], "neg": []},
              "E2": {"pos": [(425, 150), (430, 155)], "neg": [], "partial_head": True}},
    "S0073": {"E6": {"pos": [(155, 182), (155, 240)], "neg": []},
              "E1": {"pos": [(465, 160), (465, 222)], "neg": []},
              "E2": {"pos": [(415, 145), (420, 150)], "neg": [], "partial_head": True}},
    "S0034": {"E8": {"pos": [(440, 190), (305, 140)], "neg": [(560, 320), (100, 320)]}},
    # --- R6b seed pass (from vision sheet reads; entry shots seeded at entry frame) ---
    "S0021": {"E1": {"pos": [(150, 228), (152, 262)], "neg": []},
              "E5": {"pos": [(200, 235), (198, 270)], "neg": []},
              "E7": {"pos": [(398, 230), (396, 272)], "neg": []},
              "E4": {"pos": [(585, 262), (585, 300)], "neg": [(450, 120), (430, 80), (600, 60), (350, 100)], "seed_frame": 42}},
    "S0025": {"E1": {"pos": [(270, 125), (265, 212)], "neg": []}},
    "S0026": {"E2": {"pos": [(378, 152), (375, 248)], "neg": []}},
    "S0027": {"E1": {"pos": [(170, 130), (170, 205)], "neg": []},
              "E2": {"pos": [(480, 130), (480, 205)], "neg": []}},
    "S0028": {"E1": {"pos": [(140, 258), (133, 200)], "neg": []},
              "E5": {"pos": [(190, 210), (190, 250)], "neg": []},
              "E2": {"pos": [(345, 245), (345, 192)], "neg": []},
              "E7": {"pos": [(415, 260), (410, 200)], "neg": []},
              "E4": {"pos": [(512, 244), (512, 288)], "neg": []}},
    "S0029": {"E7": {"pos": [(365, 235), (362, 172)], "neg": []}},
    "S0030": {"E4": {"pos": [(440, 195), (445, 95)], "neg": []}},
    "S0033": {"E8": {"pos": [(189, 170), (164, 138)], "neg": []}},
    "S0036": {"E8": {"pos": [(320, 170), (415, 197)], "neg": []}},
    "S0038": {"E8": {"pos": [(315, 175), (420, 205)], "neg": []}},
    "S0039": {"E8": {"pos": [(320, 140), (320, 220)], "neg": []}},
    "S0043": {"E1": {"pos": [(135, 175), (135, 250)], "neg": []},
              "E2": {"pos": [(480, 170), (485, 250)], "neg": []}},
    "S0044": {"E1": {"pos": [(110, 100), (110, 175)], "neg": []},
              "E2": {"pos": [(272, 100), (272, 172)], "neg": []}},
    "S0046": {"E1": {"pos": [(110, 65), (92, 125)], "neg": []},
              "E2": {"pos": [(235, 60), (248, 120)], "neg": []}},
    "S0048": {"E1": {"pos": [(108, 68), (90, 128)], "neg": []},
              "E2": {"pos": [(238, 62), (248, 122)], "neg": []}},
    "S0051": {"E1": {"pos": [(110, 65), (92, 125)], "neg": []},
              "E2": {"pos": [(240, 62), (250, 120)], "neg": []}},
    "S0053": {"E1": {"pos": [(115, 120), (115, 205)], "neg": []},
              "E2": {"pos": [(270, 110), (272, 195)], "neg": []}},
    "S0055": {"E1": {"pos": [(110, 110), (112, 195)], "neg": []},
              "E2": {"pos": [(275, 100), (275, 185)], "neg": []}},
    "S0056": {"E1": {"pos": [(108, 105), (110, 190)], "neg": []},
              "E2": {"pos": [(270, 105), (272, 190)], "neg": []}},
    "S0064": {"E1": {"pos": [(360, 130), (360, 200)], "neg": []},
              "E2": {"pos": [(145, 115), (150, 200)], "neg": []}},
    "S0068": {"E6": {"pos": [(150, 85), (150, 165)], "neg": []},
              "E1": {"pos": [(235, 160), (235, 235)], "neg": []},
              "E2": {"pos": [(365, 110), (365, 175)], "neg": []}},
    "S0069": {"E1": {"pos": [(45, 225), (60, 295)], "neg": []},
              "E2": {"pos": [(345, 155), (360, 300)], "neg": []}},
    "S0070": {"E6": {"pos": [(140, 185), (140, 265)], "neg": []},
              "E1": {"pos": [(455, 135), (455, 225)], "neg": []}},
    "S0071": {"E6": {"pos": [(150, 95), (150, 170)], "neg": []},
              "E1": {"pos": [(230, 180), (230, 260)], "neg": []},
              "E2": {"pos": [(350, 115), (350, 190)], "neg": []}},
    "S0072": {"E1": {"pos": [(105, 195), (110, 280)], "neg": []},
              "E2": {"pos": [(355, 130), (365, 275)], "neg": []}},
}
REC = K.R6 / "receipts/R6_SAM2_RUNS.jsonl"


def frames_dir(sid, n):
    """canonical 640x360 jpgs, %05d from 0 (f0001 = source frame a0)."""
    a0 = K.PLAN[sid]["start_frame"]
    d = K.R6 / "work" / sid / "frames_360"
    have = len(list(d.glob("*.jpg"))) if d.exists() else 0
    if have < n:
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.jpg"):
            old.unlink()
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a0/30:.6f}", "-i", str(K.SRC),
                            "-frames:v", str(n), "-q:v", "2", "-start_number", "0", str(d / "%05d.jpg")],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-300:]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--ckpt", default="large")
    ns = ap.parse_args()
    sys.path.insert(0, str(K.R4 / "vendor/sam2"))
    sys.path.insert(0, str(K.ENVPYLIBS))
    import torch
    from sam2.build_sam import build_sam2_video_predictor

    sid = ns.shot
    row = None
    for line in (K.R6 / "source_actor_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["shot"] == sid:
            row = r
    if row is None:
        raise SystemExit(f"no ledger row {sid}")
    actors = SEEDS.get(sid)
    if not actors:
        raise SystemExit(f"no seed points for {sid}")
    import os as _os
    grp = _os.environ.get("R6_GROUP")
    if grp == "base":
        actors = {k: v for k, v in actors.items() if int(v.get("seed_frame", 0)) == 0}
    elif grp == "late":
        actors = {k: v for k, v in actors.items() if int(v.get("seed_frame", 0)) > 0}
    skip_validate = _os.environ.get("R6_SKIP_VALIDATE") == "1"
    n = row["n"]
    fdir = frames_dir(sid, n)
    ckpt = K.R4 / "models" / ("sam2.1_hiera_large.pt" if ns.ckpt == "large" else "sam2.1_hiera_small.pt")
    cfg = "configs/sam2.1/sam2.1_hiera_l.yaml" if ns.ckpt == "large" else "configs/sam2.1/sam2.1_hiera_s.yaml"

    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    predictor = build_sam2_video_predictor(cfg, str(ckpt), device="cuda")
    load_s = round(time.time() - t0, 2)
    t1 = time.time()
    state = predictor.init_state(video_path=str(fdir))
    ids = {name: i + 1 for i, name in enumerate(actors)}
    start = 10**9
    for name, spec in actors.items():
        pts = np.array(spec["pos"] + spec.get("neg", []), dtype=np.float32)
        labels = np.array([1] * len(spec["pos"]) + [0] * len(spec.get("neg", [])), dtype=np.int32)
        sf = int(spec.get("seed_frame", 0))
        if sf < start:
            start = sf
        predictor.add_new_points_or_box(state, frame_idx=sf, obj_id=ids[name], points=pts, labels=labels)
    if start == 10**9:
        start = 0
    t_seed = round(time.time() - t1, 2)

    out_root = K.R6 / "masks" / sid
    for name in actors:
        (out_root / name).mkdir(parents=True, exist_ok=True)
    # prefill empties for frames before the seed
    for name in actors:
        for k in range(0, int(actors[name].get("seed_frame", 0))):
            from PIL import Image
            Image.fromarray(np.zeros((360, 640), np.uint8), "L").save(out_root / name / f"f_{k+1:04d}.png")
    t2 = time.time()
    wrote = {name: 0 for name in actors}
    for fi, obj_ids, mask_logits in predictor.propagate_in_video(state, start_frame_idx=start, max_frame_num_to_track=n):
        mm = (mask_logits > 0.0)
        for k, oid in enumerate(obj_ids):
            name = [nm for nm, i in ids.items() if i == oid][0]
            m = (mm[k, 0].cpu().numpy() * 255).astype(np.uint8)
            from PIL import Image
            Image.fromarray(m, "L").save(out_root / name / f"f_{fi+1:04d}.png")
            wrote[name] += 1
    prop_s = round(time.time() - t2, 2)
    peak = int(torch.cuda.max_memory_allocated() / (1024 ** 2))
    torch.cuda.empty_cache()

    # class-aware validation — over ALL ledger actors with visible windows (not just seeded)
    violations = []
    vis = {}
    ledger_visible = []
    for a in row["actors"]:
        if any(w["class"] in ("VISIBLE", "PARTIALLY_VISIBLE") for w in a["class_windows"]):
            ledger_visible.append(a["entity"])
    for name in ledger_visible:
        if name not in actors:
            violations.append(f"{name}: ledger-visible but NOT SEEDED (masks absent)")
        cls_for = {}
        for a in row["actors"]:
            if a["entity"] != name:
                continue
            for w in a["class_windows"]:
                for f in range(w["from"], min(w["to"], n) + 1):
                    cls_for[f] = w["class"]
        nvis = 0
        if name not in actors:
            vis[name] = {"frames_total": n, "frames_visible_masked": 0, "not_seeded": True}
            continue
        for f in range(1, n + 1):
            p = out_root / name / f"f_{f:04d}.png"
            if not p.exists():
                if cls_for.get(f, "NOT_PRESENT") in ("VISIBLE", "PARTIALLY_VISIBLE"):
                    violations.append(f"{name} f{f}: mask file missing while {cls_for.get(f)}")
                continue
            from PIL import Image as _I
            a = np.asarray(_I.open(p)) > 127
            nz = int(a.sum()) > 0
            cl = cls_for.get(f, "NOT_PRESENT")
            if cl in ("VISIBLE", "PARTIALLY_VISIBLE"):
                if nz:
                    nvis += 1
                else:
                    violations.append(f"{name} f{f}: empty mask while {cl}")
            elif nz and cl in ("NOT_PRESENT", "ZERO_VISIBLE"):
                violations.append(f"{name} f{f}: mask present while {cl} (discrepancy; kept for review)")
        vis[name] = {"frames_total": n, "frames_visible_masked": nvis}
    if skip_validate:
        violations = []
    rec = {"shot": sid, "ckpt": ns.ckpt, "frames": n, "load_s": load_s, "seed_s": t_seed, "prop_s": prop_s,
           "wrote": wrote, "peak_vram_mb": peak, "visibility": vis, "violations": violations[:12],
           "violation_count": len(violations), "group": grp or "all",
           "canonical": "640x360 (no pad; f0001 = source frame a0)",
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "actor_dirs": {k: str(out_root / k) for k in actors}}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("shot", "frames", "prop_s", "peak_vram_mb", "visibility", "violation_count")}, ensure_ascii=False))
    if violations:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
