"""Standalone class validation for a shot's masks (no propagation)."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
import numpy as np
from PIL import Image


def validate(sid):
    row = None
    for line in (K.R6 / "source_actor_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["shot"] == sid:
            row = r
    n = row["n"]
    violations, vis = [], {}
    for a in row["actors"]:
        e = a["entity"]
        cls_for = {}
        for w in a["class_windows"]:
            for f in range(w["from"], min(w["to"], n) + 1):
                cls_for[f] = w["class"]
        if not any(c in ("VISIBLE", "PARTIALLY_VISIBLE") for c in cls_for.values()):
            continue
        p_dir = K.R6 / "masks" / sid / e
        nvis = 0
        for f in range(1, n + 1):
            cl = cls_for.get(f, "NOT_PRESENT")
            p = p_dir / f"f_{f:04d}.png"
            if not p.exists():
                if cl in ("VISIBLE", "PARTIALLY_VISIBLE"):
                    violations.append(f"{e} f{f}: mask missing while {cl}")
                continue
            nz = int((np.asarray(Image.open(p)) > 127).sum()) > 0
            if cl in ("VISIBLE", "PARTIALLY_VISIBLE"):
                if nz:
                    nvis += 1
                else:
                    violations.append(f"{e} f{f}: empty mask while {cl}")
            elif nz and cl in ("NOT_PRESENT", "ZERO_VISIBLE"):
                violations.append(f"{e} f{f}: mask present while {cl} (discrepancy)")
        vis[e] = {"frames_total": n, "frames_visible_masked": nvis}
    return {"shot": sid, "violations": violations, "violation_count": len(violations), "visibility": vis}


if __name__ == "__main__":
    for sid in sys.argv[1:]:
        r = validate(sid)
        print(json.dumps({"shot": r["shot"], "viol": r["violation_count"], "vis": {k: v["frames_visible_masked"] for k, v in r["visibility"].items()}, "sample": r["violations"][:3]}))
