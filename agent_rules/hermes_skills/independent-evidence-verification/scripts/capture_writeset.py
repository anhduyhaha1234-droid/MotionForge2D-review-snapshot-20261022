#!/usr/bin/env python
"""Byte-safe write-set / protected baseline capture with byte snapshots.

Enforces the pre-dispatch half of a byte-safe write-set guard: for every path in
a listing it records absolute path, repo-relative path, tracked / untracked /
dirty attribution (from `git status --porcelain`), SHA-256, byte size, logical
line count and mtime — and optionally writes a byte-for-byte SNAPSHOT of the
untracked/dirty (i.e. not Git-recoverable) files into an evidence root, verifying
each snapshot hash against the source hash.

Snapshots are RECOVERY EVIDENCE ONLY. Never copy a snapshot back over the
implementation: recovery bytes belong to the exact worker owner.

Usage
-----
  python capture_writeset.py LABEL listing.txt out-manifest.json \
      [--cwd C:/path/to/repo] [--snapshot-root C:/evidence/snapshots] \
      [--snapshot-only-untracked]

Listing format: one path per line, blank lines and `#` comments ignored.
Relative paths and globs (`*`, `?`, `[`) are resolved against `--cwd`.
Run it ONCE before dispatch, then re-run with the same listing after the worker
exits and diff `sha256` + `lines` per file; a file that disappeared or shrank
abnormally is a stop-and-freeze event, not something to rebuild from memory.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sh(args: list[str], cwd: str) -> tuple[int, str]:
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, errors="replace")
    return p.returncode, (p.stdout or "").strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git_status_map(repo: str) -> dict[str, str]:
    rc, out = sh(["git", "status", "--porcelain"], repo)
    if rc != 0:
        return {}
    m: dict[str, str] = {}
    for line in out.splitlines():
        if len(line) > 3:
            m[line[3:].strip()] = line[:2]
    return m


def tracked_set(repo: str) -> set[str]:
    rc, out = sh(["git", "ls-files"], repo)
    return set(out.splitlines()) if rc == 0 else set()


def expand(pattern: str, cwd: Path) -> list[Path]:
    if any(ch in pattern for ch in "*?["):
        return sorted(p for p in cwd.glob(pattern) if p.is_file())
    p = Path(pattern)
    return [p if p.is_absolute() else (cwd / p)]


def relativize(p: Path, repo: Path) -> str:
    try:
        return p.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def entry(p: Path, repo: Path, status: dict[str, str], tracked: set[str],
          snapshot_root: Path | None, snapshot_only_untracked: bool) -> dict:
    rel = relativize(p, repo)
    code = status.get(rel)
    if code is None:
        lowered = {k.lower(): v for k, v in status.items()}
        code = lowered.get(rel.lower())
    if not p.is_file():
        return {"path": p.as_posix(), "rel": rel, "exists": False,
                "tracked": rel in tracked, "git_code": code,
                "size": None, "lines": None, "sha256": None, "mtime": None,
                "snapshot": None}
    data = p.read_bytes()
    lines = 0 if not data else data.count(b"\n") + (0 if data.endswith(b"\n") else 1)
    st = p.stat()
    rec = {
        "path": p.as_posix(),
        "rel": rel,
        "exists": True,
        "tracked": rel in tracked,
        "git_code": code,
        "size": len(data),
        "lines": lines,
        "sha256": sha256_file(p),
        "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
        "snapshot": None,
    }
    if snapshot_root is not None:
        needs = (code is not None) or (rel not in tracked)
        if needs or not snapshot_only_untracked:
            dest = snapshot_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            got = sha256_file(dest)
            rec["snapshot"] = {"path": dest.as_posix(), "sha256": got,
                               "match": got == rec["sha256"], "bytes": len(data)}
    return rec


def main() -> int:
    label, listing, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    cwd = Path(".").resolve()
    snapshot_root: Path | None = None
    snapshot_only_untracked = False
    args = sys.argv[4:]
    i = 0
    while i < len(args):
        if args[i] == "--cwd":
            cwd = Path(args[i + 1]); i += 2
        elif args[i] == "--snapshot-root":
            snapshot_root = Path(args[i + 1]); i += 2
        elif args[i] == "--snapshot-only-untracked":
            snapshot_only_untracked = True; i += 1
        else:
            raise SystemExit(f"unknown arg {args[i]!r}")

    status = git_status_map(cwd.as_posix())
    tracked = tracked_set(cwd.as_posix())
    paths: list[Path] = []
    for line in listing.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.extend(expand(line, cwd))

    files = [entry(p, cwd, status, tracked, snapshot_root, snapshot_only_untracked)
             for p in paths]
    payload = {
        "version": 1,
        "label": label,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo": cwd.as_posix(),
        "listing": listing.as_posix(),
        "count": len(files),
        "present": sum(1 for f in files if f["exists"]),
        "tracked": sum(1 for f in files if f["tracked"]),
        "untracked": sum(1 for f in files if not f["tracked"]),
        "dirty": sum(1 for f in files if f["git_code"]),
        "bytes_total": sum(f["size"] or 0 for f in files),
        "missing": [f["path"] for f in files if not f["exists"]],
        "files": files,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    snaps = [f["snapshot"] for f in files if f["snapshot"]]
    print(json.dumps({
        "label": label,
        "manifest": out.as_posix(),
        "count": payload["count"],
        "present": payload["present"],
        "tracked": payload["tracked"],
        "untracked": payload["untracked"],
        "dirty": payload["dirty"],
        "bytes_total": payload["bytes_total"],
        "missing": payload["missing"],
        "snapshots": len(snaps),
        "snapshot_hash_mismatch": sum(1 for s in snaps if not s["match"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
