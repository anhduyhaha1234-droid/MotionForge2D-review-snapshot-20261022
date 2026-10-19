#!/usr/bin/env python
"""Freeze files/dirs into an evidence subtree with a hash manifest (freeze-before-evaluate).

usage: freeze_subtree.py <freeze_id> <dest_root> <src1> [<src2> ...]

Copies each source (file or directory) into <dest_root>/<freeze_id>/files/<name>/<rel>,
re-hashes every copied file against its source, and writes FREEZE_MANIFEST.json with
per-file sha256 + bytes + mtime, totals, a skipped list, and a `hash_mismatch` count.

Why: an evaluator must read a copy that CANNOT move while it reads. Never let a reviewer
score a live evidence root that a producing lane is still writing into
(see independent-evidence-verification §26/§27/§29).

Rules this tool enforces for you:
  * refuses to write into an existing non-empty freeze id unless --overwrite is passed
    (a correction means a NEW candidate id and a NEW freeze, never a mutated reviewed path);
  * skips __pycache__/.pyc and files over MAX_MB (weights etc.) and LISTS them under
    "skipped" so a reader can see what is not covered;
  * exits 1 if any copied byte does not match its source hash.

Pair the output with a short SNAPSHOT.md stating which parts are frozen and which are
deliberately not yet frozen (e.g. a candidate that has no freeze id yet).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_MB = 512.0


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    freeze_id, dest_root = sys.argv[1], Path(sys.argv[2])
    srcs = [Path(a) for a in sys.argv[3:] if not a.startswith("--")]
    dest = dest_root / freeze_id
    if dest.exists() and any(dest.iterdir()) and "--overwrite" not in sys.argv:
        print(json.dumps({"error": "freeze id exists and is not empty", "dest": str(dest)}))
        return 2
    files_dir = dest / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    records, skipped = [], []
    for s in srcs:
        if not s.exists():
            skipped.append({"src": str(s), "reason": "missing"})
            continue
        base = s.parent if s.is_file() else s
        items = [s] if s.is_file() else sorted(p for p in s.rglob("*") if p.is_file())
        for p in items:
            if "__pycache__" in str(p) or p.suffix == ".pyc":
                continue
            if p.stat().st_size > MAX_MB * 1024 * 1024:
                skipped.append({"src": str(p), "reason": f">{MAX_MB}MB"})
                continue
            rel = p.relative_to(base).as_posix()
            prefix = s.name if s.is_dir() else ""
            target = files_dir / (f"{prefix}/{rel}" if prefix else rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            h_src, h_dst = sha(p), sha(target)
            records.append({
                "src": str(p).replace("\\", "/"),
                "frozen": str(target).replace("\\", "/"),
                "rel": (f"{prefix}/{rel}" if prefix else rel),
                "bytes": target.stat().st_size,
                "sha256": h_src,
                "match": h_src == h_dst,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
            })

    manifest = {
        "freeze_id": freeze_id,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [str(s) for s in srcs],
        "file_count": len(records),
        "bytes_total": sum(r["bytes"] for r in records),
        "hash_mismatch": sum(1 for r in records if not r["match"]),
        "skipped": skipped,
        "files": records,
    }
    out = dest / "FREEZE_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("freeze_id", "file_count", "bytes_total", "hash_mismatch")}
                     | {"manifest": str(out), "skipped": len(skipped)}))
    return 0 if manifest["hash_mismatch"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
