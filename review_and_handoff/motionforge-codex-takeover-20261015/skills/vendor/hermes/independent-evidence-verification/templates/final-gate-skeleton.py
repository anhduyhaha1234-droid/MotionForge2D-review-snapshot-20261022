#!/usr/bin/env python
"""Final-gate skeleton for a manager review packet — copy, fill the CONFIG block, run.

Asserts the packet's OWN honesty invariants from disk, so the transcript can ship inside the
packet. Exit 0 only when `failures == 0`. Re-run it after EVERY edit to a deliverable; a gate
transcript older than your last edit is not evidence.

Install: copy next to your run root, edit CONFIG, run `python final_gate.py > STEP5_GATE.txt`.
Rationale and the measured cases behind each check: ../references/evaluator-output-integrity.md
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import socket
import subprocess
import sys

# --------------------------------------------------------------------------- CONFIG
RUN = pathlib.Path(r"C:/path/to/RUN_ROOT")          # packet root
DOCS = [                                             # required deliverables -> min bytes
    ("REPORT.md", 2000), ("MATRIX.md", 2000), ("NEXT_REVIEW_PACKET.md", 1500),
    ("SESSION_REGISTRY.md", 1500),                   # adjust to your packet
]
STATE_CLAIMING_DOCS = ["REPORT.md", "MATRIX.md", "NEXT_REVIEW_PACKET.md"]   # must name the run state
FREEZES = [
    # RUN / "manager/frozen/<freeze-id>/<freeze-id>/FREEZE_MANIFEST.json",
]
HASHED_ARTIFACTS = [                              # (path, sha256_hex, bytes) - recomputed from disk
    # (RUN / "…/candidate.mp4", "ABCDEF…", 1071337),
]
TREES = {                                         # name -> (repo, expected HEAD, expected parent or "")
    # "wt-x": (pathlib.Path(r"C:/…/wt-x"), "abc123…", "def456…"),
}
MAIN_BRANCH = (pathlib.Path(r"C:/path/to/main"), "expected-main-head-sha")
ENGINE_PORTS = [8188, 8199, 8210, 8301, 8302, 8310]
PROTECTED_LEDGERS = [                             # submitted packets that must not gain bytes
    # (path, prefix_bytes, prefix_sha256),
]
HONESTY_ABSENT = ["QUALITY_ACCEPTED = 1", "STATUS: APPROVED", "STATUS: CLOSED", "APPROVED_BY_MANAGER"]
HONESTY_PRESENT = {                               # doc -> tokens that must appear
    # "REPORT.md": ["NOT_APPROVED", "QUALITY_ACCEPTED = 0"],
}
TABLE_DOCS = [n for n, _ in DOCS]
EXPECTED_ROWS = ["lane-a", "lane-b"]              # rows the lane table must still carry
# --------------------------------------------------------------------------- /CONFIG

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(repo: pathlib.Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return (r.stdout or r.stderr).strip()


# 1. deliverables exist and are not stubs ------------------------------------------------
for name, minimum in DOCS:
    p = RUN / name
    check(f"deliverable {name}", p.is_file() and p.stat().st_size >= minimum,
          f"{p.stat().st_size if p.is_file() else 0} B")

# 2. freezes re-hash clean ---------------------------------------------------------------
for man_path in FREEZES:
    if not man_path.is_file():
        check(f"freeze manifest {man_path.name} present", False, "missing")
        continue
    man = json.loads(man_path.read_text(encoding="utf-8"))
    check(f"{man_path.parent.name} hash_mismatch == 0", man.get("hash_mismatch") == 0,
          str(man.get("hash_mismatch")))
    bad = []
    for row in man.get("files", []):
        fp = pathlib.Path(row.get("frozen") or row.get("path") or "")
        want = str(row.get("sha256") or "").strip().lower()
        if not fp.is_file():
            bad.append(f"missing:{fp.name}")
        elif want and sha(fp).lower() != want:
            bad.append(f"hash:{fp.name}")
    check(f"{man_path.parent.name} every file present + hash-matched", not bad,
          f"{len(man.get('files', []))} rows, {len(bad)} bad")

# 3. named artifacts byte-for-byte -------------------------------------------------------
for path, want_sha, want_len in HASHED_ARTIFACTS:
    if not path.is_file():
        check(f"{path.name} present", False, "missing")
        continue
    check(f"{path.name} sha matches", sha(path).upper() == want_sha.upper(), sha(path)[:24])
    check(f"{path.name} size matches", path.stat().st_size == want_len, str(path.stat().st_size))

# 4. submitted packets keep every byte (and lose none) -----------------------------------
for path, prefix_len, prefix_sha in PROTECTED_LEDGERS:
    if not path.is_file():
        check(f"{path.name} present", False, "missing")
        continue
    got = hashlib.sha256(path.read_bytes()[:prefix_len]).hexdigest()
    check(f"{path.name} prefix unchanged", got == prefix_sha, got[:24])
    check(f"{path.name} extra rows still attributed", path.stat().st_size > prefix_len,
          f"{path.stat().st_size} B")

# 5. git: local, parent intact, nothing pushed -------------------------------------------
for name, (repo, head, parent) in TREES.items():
    got = git(repo, "rev-parse", "HEAD")
    check(f"{name} HEAD == expected", got == head, got[:12] or "no-repo")
    if parent:
        check(f"{name} parent reachable", git(repo, "cat-file", "-e", parent) == "", parent[:12])
    check(f"{name} not pushed", git(repo, "branch", "-r", "--contains", head) == "", "remote has it")
main_repo, main_head = MAIN_BRANCH
check("main branch HEAD unchanged", git(main_repo, "rev-parse", "HEAD") == main_head,
      git(main_repo, "rev-parse", "HEAD")[:12])

# 6. machine state: no engine left listening + GPU idle ----------------------------------
open_ports = []
for port in ENGINE_PORTS:
    s = socket.socket()
    s.settimeout(1.5)
    try:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            open_ports.append(port)
    finally:
        s.close()
check("no engine port accepting connections", not open_ports, f"open: {open_ports}")
nvsmi = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
used = re.sub(r"\D", "", nvsmi.stdout or "0") or "0"
check("GPU near idle", int(used) < 3000, f"{used} MiB")

# 7. honesty — absence of self-approval, presence of required claims ----------------------
for name, _ in DOCS:
    t = (RUN / name).read_text(encoding="utf-8")
    bad = [tok for tok in HONESTY_ABSENT if tok in t]
    check(f"{name} has no self-approval token", not bad, ",".join(bad))
for name, tokens in HONESTY_PRESENT.items():
    t = (RUN / name).read_text(encoding="utf-8")
    missing = [tok for tok in tokens if tok not in t]
    check(f"{name} carries its required honesty tokens", not missing, ",".join(missing))

# 8. markdown table integrity (an inserted paragraph silently orphans a row) --------------
for name in TABLE_DOCS:
    t = (RUN / name).read_text(encoding="utf-8")
    check(f"{name} no corrupted table row ('||')", "\n||" not in t)
if EXPECTED_ROWS:
    joined = "\n".join((RUN / n).read_text(encoding="utf-8") for n, _ in DOCS)
    missing = [row for row in EXPECTED_ROWS if row not in joined]
    check("expected table rows all still present", not missing, ",".join(missing))

# 9. registry provenance is genuinely graded ---------------------------------------------
reg_p = RUN / "SESSION_REGISTRY.md"
if reg_p.is_file():
    reg = reg_p.read_text(encoding="utf-8")
    check("registry grades its provenance", "PROVEN" in reg or "INFERRED" in reg or "CONFIRMED" in reg)

# --------------------------------------------------------------------------- report
fails = [r for r in results if not r[1]]
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not ok else ""))
print(f"\nRESULT: {len(fails)} failure(s) out of {len(results)} checks")
sys.exit(1 if fails else 0)
