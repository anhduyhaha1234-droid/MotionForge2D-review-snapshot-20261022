"""J1-v4 direct re-hash: 13/13 bytes + EOL guard (12 LF + composite CRLF).

Run this from ANY cwd; paths are hard-wired to the MotionForge2D integration
worktree. Exit 0 = full pass, 1 = any DRIFT/MISSING or EOL guard failure.
Usage: python j1v4_rehash.py  (optionally pass --worktree / --manifest overrides)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_WT = Path(r"C:/Users/Admin/MotionForge2D-worktrees/s08-integration")
DEFAULT_MANIFEST = (
    DEFAULT_WT
    / "output/s09/20260823_sprint_full/freeze-c4-meta/freeze_manifest_v4_after.json"
)

parser = argparse.ArgumentParser()
parser.add_argument("--worktree", type=Path, default=DEFAULT_WT)
parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
args = parser.parse_args()

WT = args.worktree
data = json.loads(args.manifest.read_text(encoding="utf-8"))
files = data["manifest"]["files"]
print(
    f"entries={len(files)} manifest_version={data['manifest']['version']} "
    f"frozen_at={data['manifest']['frozen_at']}"
)

ok = 0
crlf_files = []
for rel, expected in files.items():
    p = WT / rel
    if not p.exists():
        print(f"MISSING  {rel}")
        continue
    raw = p.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    n_lf = raw.count(b"\n")
    n_crlf = raw.count(b"\r\n")
    eol = "CRLF" if (n_crlf == n_lf and n_lf > 0) else "LF"
    if eol == "CRLF":
        crlf_files.append(rel)
    match = "OK " if actual == expected else "DRIFT"
    if match == "OK ":
        ok += 1
    print(
        f"{match} {rel} eol={eol} sha={actual[:16]}"
        + (f" (expected {expected[:16]}...)" if match != "OK " else "")
    )

print(f"\nRESULT: {ok}/{len(files)} byte-match | CRLF files: {crlf_files}")
eol_ok = len(crlf_files) == 1 and "composite" in crlf_files[0]
print("EOL_GUARD:", "PASS" if eol_ok else "FAIL")
sys.exit(0 if ok == len(files) and eol_ok else 1)