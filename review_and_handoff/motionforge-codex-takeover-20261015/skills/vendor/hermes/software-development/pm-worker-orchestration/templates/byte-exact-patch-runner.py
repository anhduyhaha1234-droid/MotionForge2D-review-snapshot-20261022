#!/usr/bin/env python
"""Byte-exact bounded patch runner for EXISTING files -- copy next to your patch work,
fill PATCHES, run --dry first, then run for real.

Safety rails encoded (each measured on a live harness round; see
references/byte-exact-patching-crlf-escaping-and-truncation.md):
  * tmp-file + os.replace ONLY: open(dest,'w') truncates BEFORE validation errors, and a
    crash mid-script leaves the destination empty. Keep a preimage copy + sha first --
    that snapshot is the recovery you will actually use.
  * CRLF-safe: read with universal newlines so anchors use plain newline chars, then write
    the file's ORIGINAL convention back and post-check line-ending uniformity.
  * count(old) == 1 asserts are the preimage proof; a miss means re-read the file and fix
    the anchor -- never switch to fuzzier matching.
  * Escape sentinels are built from chr() -- never type literal backslash escapes in a
    tool payload; they get mangled between you and the file.
  * Post-verify sha256/bytes/lines; write a patch-log JSON for evidence.

Usage:
  python -B byte-exact-patch-runner.py --dest <file> --log <evidence.json> --dry
  python -B byte-exact-patch-runner.py --dest <file> --log <evidence.json> [--json-check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

CRLF = chr(13) + chr(10)   # never write this sequence literally in a tool payload
LF_BYTE = bytes([10])
CRLF_BYTES = bytes([13, 10])

# ---- FILL ME: (label, old_text, new_text); old_text must occur EXACTLY once -------------
PATCHES = [
    # ("example", "exact old text", "replacement text"),
]
# ------------------------------------------------------------------------------------------


def sha256f(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, help="existing file to patch (never rewritten before validation)")
    ap.add_argument("--log", required=True, help="patch-log JSON path (evidence)")
    ap.add_argument("--dry", action="store_true", help="validate anchors only; no write")
    ap.add_argument("--json-check", action="store_true", help="JSON-parse the result before writing")
    args = ap.parse_args()

    dest = Path(args.dest)
    raw_before = dest.read_bytes()
    crlf = raw_before.count(CRLF_BYTES) > 0

    with open(dest, "r", encoding="utf-8", newline=None) as fh:
        text = fh.read()

    for label, old, new in PATCHES:
        n = text.count(old)
        assert n == 1, "anchor %r: expected 1 occurrence, found %d" % (label, n)
        text = text.replace(old, new)

    if args.json_check:
        json.loads(text)  # must parse before any write

    if args.dry:
        print("DRY OK: %d anchors, all count==1, json_ok=%s" % (len(PATCHES), args.json_check))
        return 0

    tmp = dest.with_name(dest.name + ".patched.tmp")
    with open(tmp, "w", encoding="utf-8", newline=(CRLF if crlf else "")) as fh:
        fh.write(text)
    os.replace(tmp, dest)

    after = dest.read_bytes()
    if after.count(CRLF_BYTES) != after.count(LF_BYTE):
        raise SystemExit("POST-CHECK FAILED: mixed line endings after write")

    if dest.suffix == ".py":
        import py_compile
        py_compile.compile(str(dest), doraise=True,
                           cfile=str(Path(args.log).with_suffix(".check.pyc")), optimize=0)

    log = {
        "file": str(dest),
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "anchors": [p[0] for p in PATCHES],
        "crlf": crlf,
        "before": {"sha256": hashlib.sha256(raw_before).hexdigest(),
                   "bytes": len(raw_before), "lines_lf": raw_before.count(LF_BYTE)},
        "after": {"sha256": hashlib.sha256(after).hexdigest(),
                  "bytes": len(after), "lines_lf": after.count(LF_BYTE)},
    }
    Path(args.log).write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(json.dumps({"file": log["file"], "anchors": log["anchors"]}))
    print("before %s -> after %s (%d bytes)" % (log["before"]["sha256"][:16],
                                                log["after"]["sha256"][:16], log["after"]["bytes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
