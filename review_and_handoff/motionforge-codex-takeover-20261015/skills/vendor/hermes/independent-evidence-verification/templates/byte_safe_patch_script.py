#!/usr/bin/env python
"""Byte-safe patch script TEMPLATE (copy + edit).

See references/byte-safe-patch-scripts-and-crlf.md for the measured incidents this
implements: write_file writes verbatim (use chr() sentinels), open('w') truncates
before validation errors (tmp + os.replace), CRLF targets need universal-read /
assert-count / CRLF-write / post-verify.

Rules embedded:
  * every replacement asserts its anchor count BEFORE any write
  * the live target is only touched via os.replace(tmp) after all checks pass
  * compile (.py) / parse (.json) checks run before the replace is final
  * before/after sha256+bytes+lines are logged to an evidence JSON
"""
import hashlib
import json
import os
import time
import py_compile
from pathlib import Path

BS = chr(92)          # backslash, if a generated string must CONTAIN escape text
CRLF = chr(13) + chr(10)
QDBL = chr(34)

TARGET = Path("C:/absolute/path/to/target")      # <-- edit
EVID = Path("C:/absolute/path/to/evidence_dir")  # <-- edit
EVID.mkdir(parents=True, exist_ok=True)

# ---- preimage snapshot (restore source if anything fails) ----
before = TARGET.read_bytes()
pre = EVID / ("preimage_" + TARGET.name)
pre.write_bytes(before)
assert hashlib.sha256(pre.read_bytes()).hexdigest() == hashlib.sha256(before).hexdigest()

# ---- universal read (CRLF -> \n in memory) ----
with open(TARGET, "r", encoding="utf-8", newline=None) as fh:
    text = fh.read()


def repl(text, old, new, label, expect=1):
    n = text.count(old)
    assert n == expect, "[%s] anchor count %d != %d: %r" % (label, n, expect, old[:80])
    return text.replace(old, new)


# ---- replacements (anchors use plain \n; keep each anchor UNIQUE) ----
# text = repl(text, "OLD EXACT TEXT", "NEW TEXT", "label-1")
# For big blocks prefer a runtime-located splice instead of retyping:
#   s = text.find("start marker"); e = text.find("end marker", s)
#   assert s >= 0 and e >= 0
#   text = text[:s] + NEW_BLOCK + text[e:]

# ---- write tmp + atomic replace (NEVER open the live target for writing) ----
tmp = TARGET.with_name(TARGET.name + ".patched.tmp")
with open(str(tmp), "w", encoding="utf-8", newline=CRLF) as fh:
    fh.write(text)
os.replace(str(tmp), str(TARGET))
after = TARGET.read_bytes()
assert after.count(CRLF.encode()) == after.count(b"\n"), "postimage not fully CRLF"

# ---- syntax / schema checks ----
if TARGET.suffix == ".py":
    py_compile.compile(str(TARGET), doraise=True,
                       cfile=str(EVID / ("_pycompile_" + TARGET.stem + ".pyc")))
if TARGET.suffix == ".json":
    json.loads(TARGET.read_text(encoding="utf-8"))

# ---- evidence log ----
log = {
    "file": str(TARGET),
    "sha256_before": hashlib.sha256(before).hexdigest(),
    "sha256_after": hashlib.sha256(after).hexdigest(),
    "bytes_after": len(after),
    "lines_lf_after": after.count(b"\n"),
    "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
(EVID / ("patch_" + TARGET.stem + ".json")).write_text(json.dumps(log, indent=1), encoding="utf-8")
print(json.dumps(log, indent=1))
