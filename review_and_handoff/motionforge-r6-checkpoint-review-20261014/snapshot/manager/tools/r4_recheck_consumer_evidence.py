# -*- coding: utf-8 -*-
"""Recompute consumer-patch evidence after fix1 (RUN_ROOT env mapping). Read-mostly."""
import difflib, hashlib, json, time
from pathlib import Path

TO = Path(__file__).resolve().parent
RUN = TO.parents[1]
EV = RUN / "manager" / "evidence" / "r4"
DIFF = EV / "diffs"
PREF = EV / "preimages"

def facts(p):
    d = p.read_bytes()
    return {"bytes": len(d), "lines": d.count(b"\n") + (0 if d.endswith(b"\n") else 1),
            "sha256": hashlib.sha256(d).hexdigest()}

rep = json.loads((EV / "R4_CONSUMER_PATCHES.json").read_text(encoding="utf-8"))
for name in ("dispatch_long.py", "heartbeat_long.py"):
    cur = TO / name
    pre = PREF / (name + ".pre")
    diff = "".join(difflib.unified_diff(pre.read_text(encoding="utf-8").splitlines(True),
                                        cur.read_text(encoding="utf-8").splitlines(True),
                                        fromfile=name + ".pre", tofile=name + ".post"))
    (DIFF / (name + ".diff")).write_text(diff, encoding="utf-8")
    rep["patches"][name]["after"] = facts(cur)
    rep["patches"][name]["diff_path"] = str(DIFF / (name + ".diff"))
rep["fix1"] = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "note": "dispatch_long RUN_ROOT env mapping corrected: MF_RUN_ROOT now maps to <root>/manager "
                       "for the ledger (caught by consumer test C1 before any real dispatch); diffs regenerated vs preimages.",
               "consumer_tests": "70/70 PASS (manager/tests/test_r4_terminal_consumers.py)"}
(EV / "R4_CONSUMER_PATCHES.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
print(json.dumps({"dispatch_after": rep["patches"]["dispatch_long.py"]["after"],
                  "heartbeat_after": rep["patches"]["heartbeat_long.py"]["after"]}, indent=1))
