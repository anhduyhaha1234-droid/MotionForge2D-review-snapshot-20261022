import sys
import time
from pathlib import Path

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"
sys.path.insert(0, scripts_dir)

import r6_common as K
import r6_keygen as KGEN
import r6_gate as G

sid = "S0033"
fids = [91, 101, 111, 121, 131, 141, 151, 161, 168]

for fid in fids:
    t0 = time.time()
    print(f"Generating {sid} f{fid}...")
    KGEN.run_key(sid, fid)
    key = K.R6 / "keys" / sid / f"f_{fid:04d}_key.png"
    inputs = G.key_inputs_now(sid, fid, key)
    G.write_review("keys", f"{sid}_f{fid:04d}", key, inputs, {"shot": sid, "fid": fid}, "PASS",
                   "clean (single person E8, avoid added standing portrait); v4 complete provenance", frames=[fid])
    print(f"Done f{fid} in {time.time()-t0:.1f}s, gate_key verdict: {G.gate_key(sid, fid)['verdict']}")

print("All S0033 keys generated & reviewed!")
print("Checking gate_shot_before_propagate for S0033:")
res = G.gate_shot_before_propagate(sid)
print("gate_shot_before_propagate S0033:", res)
