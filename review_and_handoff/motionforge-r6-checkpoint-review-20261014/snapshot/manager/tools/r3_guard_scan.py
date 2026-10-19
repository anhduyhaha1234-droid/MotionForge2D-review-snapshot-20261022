"""R3 protected-input guard scan (Manager tool; writes manifest to RUN/manager/evidence/r3/).

Hashes every existing file that r3 must NOT modify:
  - everything under D except scratch dirs (work/env/temp/user/__pycache__),
    worker_*.log, *.pyc, and the 3 patch-only exception files
  - the reviewer packet docs (read-only for us)
The 3 patch-only exceptions are captured separately with write_set_guard.py
(capture mode with snapshots). Re-run semantics: this file is a NEW file each
round (PRE/POST); never overwrite an earlier manifest.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

D = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01")
OUT = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager/evidence/r3")
REV = Path("C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-c2-review-20261008")

SKIP_DIRS = {"work", "env", "temp", "user", "__pycache__", ".git"}
EXCEPTIONS = {"state_gate.json", "RESUME_STATE.md", "evidence/MATRIX_F1_F15.json"}
REV_FILES = [
    "REVIEW_VI.md", "CORRECTION_MATRIX.md", "RESEARCH_UPDATE.md",
    "SESSION_OPENING_PROPOSAL.md", "GATE_REPRO.json",
    "NEXT_HERMES_MANAGER_PROMPT.md", "ARTIFACT_INDEX.json", "FINAL_VERIFICATION.json",
]


def sha256f(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def line_count(p: Path):
    try:
        data = p.read_bytes()
    except OSError:
        return None
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def entry_for(rel_s: str, p: Path) -> dict:
    st = p.stat()
    e = {
        "path": rel_s,
        "size": st.st_size,
        "sha256": sha256f(p),
        "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
    }
    if st.st_size <= 4_000_000:
        try:
            p.read_text(encoding="utf-8")
            e["lines"] = line_count(p)
        except (UnicodeDecodeError, OSError):
            pass
    return e


def main() -> int:
    out_name = sys.argv[1] if len(sys.argv) > 1 else "PROTECTED_MANIFEST_PRE.json"
    OUT.mkdir(parents=True, exist_ok=True)
    entries, total, nfiles = [], 0, 0
    for root, dirs, files in os.walk(D):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = Path(root).relative_to(D)
        for f in sorted(files):
            rel_s = (rel_root / f).as_posix()
            if rel_s in EXCEPTIONS:
                continue
            if f.startswith("worker_") and f.endswith(".log"):
                continue
            if f.endswith(".pyc"):
                continue
            p = Path(root) / f
            try:
                e = entry_for(rel_s, p)
            except OSError as err:
                e = {"path": rel_s, "error": str(err)}
            if "size" in e:
                total += e["size"]
                nfiles += 1
            entries.append(e)
    rev_entries = []
    for name in REV_FILES:
        p = REV / name
        if p.is_file():
            rev_entries.append(entry_for(name, p))
    manifest = {
        "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(D),
        "excluded_dirs": sorted(SKIP_DIRS),
        "patch_only_exceptions": sorted(EXCEPTIONS),
        "manifest_note": "exceptions captured separately via write_set_guard.py capture (snapshots)",
        "file_count": nfiles,
        "total_bytes": total,
        "reviewer_packet_dir": str(REV),
        "reviewer_packet_files": rev_entries,
        "entries": entries,
    }
    dest = OUT / out_name
    dest.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"status": "OK", "manifest": str(dest), "files": nfiles, "bytes": total}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
