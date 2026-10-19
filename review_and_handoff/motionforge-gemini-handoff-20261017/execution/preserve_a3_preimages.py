import os, shutil, hashlib

r6_scripts = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"
preimages_a3 = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\preimages\a3_takeover"
os.makedirs(preimages_a3, exist_ok=True)

files = ["r6_propagate.py", "r6_cotracker.py", "r6_ledger.py", "r6_gate.py"]
for f in files:
    src = os.path.join(r6_scripts, f)
    dst = os.path.join(preimages_a3, f)
    shutil.copy2(src, dst)
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    print(f"Preserved A3 preimage {f}: {sha} ({os.path.getsize(dst)} bytes)")
