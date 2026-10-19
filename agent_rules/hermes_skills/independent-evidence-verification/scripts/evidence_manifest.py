#!/usr/bin/env python
"""Deterministic evidence-manifest builder, aware of self-referential files.

Why the exclusions exist
------------------------
A manifest that hashes every file under its root reports phantom CHANGED entries on
every regeneration, because the files that CARRY the manifest's own digest (a seal /
verify log written after the build, or a report quoting the digest) are themselves
inside the root. Measured 2026-09-30: `T019_seal.txt CHANGED`, then one layer down
`unlisted_on_disk: [T023_manifest_verify.txt]`.

Set EXCLUDE below to exactly those files, by name, and write the reason next to each.

Usage
-----
    python evidence_manifest.py            # build (prints count + entries_digest)
    python evidence_manifest.py verify     # read-only check against the frozen tree

Determinism proof: run the build twice; `entries_digest` (a hash of the sorted
entries array, which contains no timestamps) must be identical. Then verify.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

# --- point these at the run root -------------------------------------------------
RUN = Path(os.environ.get("EVIDENCE_ROOT", ".")).resolve()
MAN = RUN / "manager" / "EVIDENCE_MANIFEST.json"

# Files that legitimately carry (or are produced by) the manifest's own digest.
# Including them makes every regeneration invalidate its own output.
EXCLUDE = {
    "manager/EVIDENCE_MANIFEST.json",
    # "manager/T019_seal.txt",           # prints the manifest digest
    # "manager/T023_manifest_verify.txt",# output of the verify step itself
}


def build() -> dict:
    entries = []
    for dp, _dn, fn in os.walk(RUN):
        for f in sorted(fn):
            p = Path(dp) / f
            rel = p.relative_to(RUN).as_posix()
            if rel in EXCLUDE:
                continue
            data = p.read_bytes()
            entries.append({"rel": rel, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    entries.sort(key=lambda e: e["rel"])
    return {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "root": str(RUN), "count": len(entries),
            "excluded_self_referential": sorted(EXCLUDE),
            "entries": entries}


def verify(doc: dict) -> dict:
    mismatch = []
    for e in doc["entries"]:
        p = RUN / e["rel"]
        if not p.is_file():
            mismatch.append((e["rel"], "MISSING"))
        elif hashlib.sha256(p.read_bytes()).hexdigest() != e["sha256"]:
            mismatch.append((e["rel"], "CHANGED"))
    listed = {e["rel"] for e in doc["entries"]}
    on_disk = set()
    for dp, _dn, fn in os.walk(RUN):
        for f in fn:
            rel = (Path(dp) / f).relative_to(RUN).as_posix()
            if rel not in EXCLUDE:
                on_disk.add(rel)
    return {"mismatch": mismatch, "unlisted_on_disk": sorted(on_disk - listed)}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        doc = json.loads(MAN.read_text(encoding="utf-8"))
        print(json.dumps(verify(doc), indent=1))
        return 0
    doc = build()
    MAN.parent.mkdir(parents=True, exist_ok=True)
    MAN.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    r = verify(doc)
    print(json.dumps({
        "count": doc["count"],
        "mismatch": len(r["mismatch"]),
        "unlisted": len(r["unlisted_on_disk"]),
        "entries_digest": hashlib.sha256(
            json.dumps(doc["entries"], sort_keys=True).encode()).hexdigest(),
        "manifest_sha256": hashlib.sha256(MAN.read_bytes()).hexdigest(),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
