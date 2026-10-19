import os, shutil, hashlib

scripts_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts"
preimages_a4 = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\preimages\a4_takeover"
os.makedirs(preimages_a4, exist_ok=True)

files = ["r6_assemble.py", "r6_matrix.py", "r6_gate.py"]
for f in files:
    src = os.path.join(scripts_dir, f)
    dst = os.path.join(preimages_a4, f)
    shutil.copy2(src, dst)
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    print(f"Preserved A4 preimage {f}: {sha} ({os.path.getsize(dst)} bytes)")
