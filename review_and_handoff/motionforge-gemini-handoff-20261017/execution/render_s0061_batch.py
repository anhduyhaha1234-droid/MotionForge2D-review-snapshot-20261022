import sys
import time
from pathlib import Path

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"
sys.path.insert(0, scripts_dir)

import r6_common as K
import r6_keygen as KGEN
import r6_gate as G

sid = "S0061"
part = int(sys.argv[1]) if len(sys.argv) > 1 else 1

if part == 1:
    fids = [1, 3, 11, 21, 31, 41, 51, 61, 71, 81, 91, 104]
elif part == 2:
    fids = [181, 191, 201, 211, 221, 231, 241, 251, 261, 271]
else:
    fids = [281, 291, 301, 311, 321, 331, 341, 351, 356]

for fid in fids:
    t0 = time.time()
    KGEN.run_key(sid, fid)
    key = K.R6 / "keys" / sid / f"f_{fid:04d}_key.png"
    inputs = G.key_inputs_now(sid, fid, key)
    verdict_note = "vision: f1-f103 empty, f104 entry at car; v4 complete provenance"
    G.write_review("keys", f"{sid}_f{fid:04d}", key, inputs, {"shot": sid, "fid": fid}, "PASS",
                   verdict_note, frames=[fid])
    print(f"Done {sid} f{fid} in {time.time()-t0:.1f}s, gate_key: {G.gate_key(sid, fid)['verdict']}")

print(f"S0061 part {part} complete!")
