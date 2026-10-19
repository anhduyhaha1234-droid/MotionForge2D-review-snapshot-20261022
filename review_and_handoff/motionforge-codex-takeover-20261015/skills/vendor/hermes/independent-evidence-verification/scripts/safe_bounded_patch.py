#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Safe bounded patcher for EXISTING files (preimage + count-asserted replacements + tmp/replace).

Why: a direct `open(path, "w", newline=BAD)` truncates the target before the ValueError is
raised (measured file loss), and literal escape sequences in tool payloads/heredocs arrive
mangled. This helper never opens the target for writing and builds newline values via chr().

Usage:
    from safe_bounded_patch import BoundedPatch, verify_json, verify_py
    bp = BoundedPatch("C:/path/file.json", "C:/evidence/dir", label="registry")
    bp.repl(old_text, new_text, "manager.session_id")   # asserts exactly ONE occurrence
    bp.repl(old2, new2, "worker.status")
    bp.commit(post_check=verify_json)                   # tmp -> validate -> os.replace
    log = bp.commit()  # returns {before/after sha256, bytes, lines, preimage path}

Notes:
  - Patterns are written with plain \\n (the file is read with universal newlines).
  - Write-back preserves the original line-ending style (fully-CRLF detected by count).
  - The preimage copy + a JSON log are always written into the evidence dir.
  - repl() asserts BEFORE mutating, so a bad later anchor aborts with the file untouched.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

CR = chr(13)
LF = chr(10)
CRLF = CR + LF


class BoundedPatch:
    def __init__(self, path, evidence_dir, label=None):
        self.path = Path(path)
        self.ev = Path(evidence_dir)
        self.ev.mkdir(parents=True, exist_ok=True)
        self.label = label or self.path.name
        with open(self.path, "r", encoding="utf-8", newline=None) as fh:
            self.text = fh.read()
        self.before = self.path.read_bytes()
        self.crlf = (self.before.count(b"\r\n") == self.before.count(b"\n")) and (self.before.count(b"\n") > 0)
        self.preimage = self.ev / ("preimage__" + self.path.name)
        shutil.copyfile(self.path, self.preimage)
        with open(self.preimage, "rb") as fh:
            assert hashlib.sha256(fh.read()).hexdigest() == hashlib.sha256(self.before).hexdigest(), "preimage hash mismatch"
        self.replacements = []

    def repl(self, old, new, label="", count=1):
        n = self.text.count(old)
        assert n == count, "anchor %r (%s): expected %d occurrence(s), found %d" % (old[:70], label, count, n)
        self.text = self.text.replace(old, new)
        self.replacements.append(label)
        return self

    def commit(self, post_check=None):
        tmp = self.path.with_name(self.path.name + ".patched.tmp")
        newline = CRLF if self.crlf else ""
        with open(tmp, "w", encoding="utf-8", newline=newline) as fh:
            fh.write(self.text)
        if post_check is not None:
            post_check(tmp)  # validate the tmp BEFORE it can replace the target
        os.replace(str(tmp), str(self.path))
        after = self.path.read_bytes()
        log = {
            "label": self.label,
            "file": str(self.path),
            "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "before": {"sha256": hashlib.sha256(self.before).hexdigest(), "bytes": len(self.before),
                       "lines_lf": self.before.count(b"\n")},
            "after": {"sha256": hashlib.sha256(after).hexdigest(), "bytes": len(after),
                      "lines_lf": after.count(b"\n")},
            "crlf_preserved": (after.count(b"\r\n") == after.count(b"\n")) if self.crlf else True,
            "replacements": self.replacements,
            "preimage": str(self.preimage),
        }
        out = self.ev / ("patch__" + self.path.name + ".json")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(log, indent=1))
        return log


def verify_json(path):
    """post_check for JSON targets: parse or raise."""
    with open(path, "r", encoding="utf-8") as fh:
        json.loads(fh.read())


def verify_py(path, cfile):
    """post_check for .py targets: compile to an explicit cfile (evidence dir), or raise."""
    import py_compile
    py_compile.compile(str(path), doraise=True, cfile=str(cfile), optimize=0)
