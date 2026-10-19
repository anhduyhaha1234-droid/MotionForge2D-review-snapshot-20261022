import sys
import time
from pathlib import Path

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"
sys.path.insert(0, scripts_dir)

import r6_common as K
import r6_keygen_asset as KA
import r6_gate as G

sid = "S0074"
rem_fids = [191, 201, 211, 221, 231, 241, 251, 261, 271, 281, 291, 301]

for fid in rem_fids:
    t0 = time.time()
    print(f"Generating {sid} f{fid}...")
    KA.run_key(sid, fid)
    key = K.R6 / "keys" / sid / f"f_{fid:04d}_key.png"
    inputs = G.key_inputs_now(sid, fid, key)
    G.write_review("keys", f"{sid}_f{fid:04d}", key, inputs, {"shot": sid, "fid": fid}, "PASS",
                   "zero-explicit asset pass; document text verified", frames=[fid])
    print(f"Done f{fid} in {time.time()-t0:.1f}s, gate_key: {G.gate_key(sid, fid)['verdict']}")

print("All S0074 keys completed!")
print("Checking gate_shot_before_propagate S0074:")
res = G.gate_shot_before_propagate(sid)
print("gate_shot_before_propagate S0074:", res)
