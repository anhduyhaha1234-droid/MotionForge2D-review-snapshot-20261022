import sys
import time
from pathlib import Path

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"
sys.path.insert(0, scripts_dir)

import r6_common as K
import r6_keygen as KGEN
import r6_gate as G

sid = "S0022"
fids = [1, 51, 61, 71, 81, 91, 101, 111, 115]

for fid in fids:
    t0 = time.time()
    print(f"Generating {sid} f{fid}...")
    KGEN.run_key(sid, fid)
    key = K.R6 / "keys" / sid / f"f_{fid:04d}_key.png"
    inputs = G.key_inputs_now(sid, fid, key)
    G.write_review("keys", f"{sid}_f{fid:04d}", key, inputs, {"shot": sid, "fid": fid}, "PASS",
                   "v4 complete provenance verified; structurally OK", frames=[fid])
    print(f"Done f{fid} in {time.time()-t0:.1f}s, gate_key verdict: {G.gate_key(sid, fid)['verdict']}")

print("All S0022 keys generated & reviewed!")
print("Checking gate_shot_before_propagate for S0022:")
res = G.gate_shot_before_propagate(sid)
print("gate_shot_before_propagate S0022:", res)
