"""Compare two r4 guard manifests: changed/removed/added vs the r4 write-set. Read-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RUN = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long")
EV = RUN / "manager/evidence/r4"

ALLOWED_NEW_PREFIXES = (
    "corrections/identity5m_20261008/r4/",
    "input/identity5m_20261008/r4/",
    "output/identity5m_20261008/r4/",
)


def load(name: str):
    return json.loads((EV / name).read_text(encoding="utf-8"))


def main() -> int:
    pre_name, post_name, out_name = sys.argv[1], sys.argv[2], sys.argv[3]
    pre, post = load(pre_name), load(post_name)
    pre_map = {e["path"]: e for e in pre["entries"] if "sha256" in e}
    post_map = {e["path"]: e for e in post["entries"] if "sha256" in e}
    changed, removed, added = [], [], []
    for p, e in pre_map.items():
        q = post_map.get(p)
        if q is None:
            removed.append(p)
        elif q["sha256"] != e["sha256"] or q.get("size") != e.get("size"):
            changed.append({"path": p, "pre": e["sha256"][:16], "post": q["sha256"][:16],
                            "pre_size": e.get("size"), "post_size": q.get("size")})
    for p, e in post_map.items():
        if p not in pre_map:
            allowed = any(p.startswith(pref) for pref in ALLOWED_NEW_PREFIXES)
            added.append({"path": p, "size": e.get("size"), "allowed_new": allowed})
    bad_added = [a for a in added if not a["allowed_new"]]
    report = {
        "pre": pre_name, "post": post_name,
        "pre_files": len(pre_map), "post_files": len(post_map),
        "changed": changed, "removed": removed,
        "added_count": len(added), "added_violations": bad_added,
        "added_allowed_sample": [a["path"] for a in added if a["allowed_new"]][:20],
        "verdict": "CLEAN" if (not changed and not removed and not bad_added) else "VIOLATION",
        "note": "D/temp/** is outside the scanned set by design (scratch); the r4 temp write-set is not protected input.",
    }
    (EV / out_name).write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "changed": len(changed), "removed": len(removed),
                      "added": len(added), "added_violations": len(bad_added)}))
    return 0 if report["verdict"] == "CLEAN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
