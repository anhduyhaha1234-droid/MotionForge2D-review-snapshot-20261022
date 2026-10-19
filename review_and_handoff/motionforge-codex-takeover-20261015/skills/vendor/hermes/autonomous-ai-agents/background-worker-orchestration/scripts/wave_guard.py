#!/usr/bin/env python
"""Wave-level byte-safe guard: capture / verify.

`docs/pm/tools/write_set_guard.py` (or the promoted equivalent) guards files
under ONE root. A full parallel WAVE needs more than that, because the things
that must not drift live in several places:

  * each protected repo/worktree's HEAD + porcelain  (head movement / new dirt)
  * the wave base's FULL tracked-blob manifest       (git ls-tree -r HEAD)
  * binary/media protected inputs                    (source films, before/after
    MP4s) that a whole-file SHA over text tooling would not cover well

Capture BEFORE creating child worktrees or dispatching any writer, then:

    capture  -> immediately verify (must be VERIFIED / 0 failures — proves the
                check is real, not post-hoc)
    verify   -> again at the wave's final gate
    verify   -> after EVERY worker terminal

Usage
-----
  python wave_guard.py capture <manifest.json> <report.json> <targets.txt>
  python wave_guard.py verify  <manifest.json> <report.json>

`<targets.txt>` is one absolute Windows-native path per line; `#` starts a
comment. Edit PROTECTED_REPOS / WAVE_BASE below, or pass them via the
WAVE_BASE / WAVE_REPOS env vars (newline- or ';'-separated).

Exit codes: 0 = VERIFIED, 1 = FAILED (failures listed in the report JSON).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- configuration
WAVE_BASE = os.environ.get("WAVE_BASE", r"C:\path\to\wave-base-worktree")

_FROM_ENV = [p for p in os.environ.get("WAVE_REPOS", "").replace(";", "\n").splitlines() if p.strip()]
PROTECTED_REPOS = _FROM_ENV or [
    r"C:\path\to\main-repo",
    WAVE_BASE,
]
# ------------------------------------------------------------------------------


def sh(args: list[str], cwd: str) -> tuple[int, str]:
    """Run a command; return (returncode, stdout). Never use git -C with MSYS paths."""
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, errors="replace")
    return p.returncode, (p.stdout or "").strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def file_entry(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "exists": False, "size": None, "lines": None,
                "sha256": None, "mtime": None}
    data = path.read_bytes()
    lines = 0 if not data else data.count(b"\n") + (0 if data.endswith(b"\n") else 1)
    st = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size": len(data),
        "lines": lines,
        "sha256": sha256_file(path),
        "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
    }


def repo_entry(path: str) -> dict:
    p = Path(path)
    if not p.is_dir():
        return {"path": path, "exists": False}
    # cd into the repo rather than `git -C <msys path>` — git -C on MSYS/C: paths
    # is either a hard error or a silent 0, both indistinguishable from clean.
    rc_h, head = sh(["git", "rev-parse", "HEAD"], path)
    rc_b, branch = sh(["git", "branch", "--show-current"], path)
    _, status = sh(["git", "status", "--porcelain"], path)
    dirty = [ln for ln in status.splitlines() if ln.strip()]
    return {
        "path": path,
        "exists": True,
        "head": head if rc_h == 0 else None,
        "branch": branch if rc_b == 0 else None,
        "dirty_count": len(dirty),
        "dirty_sample": dirty[:40],
    }


def tree_manifest(path: str) -> dict:
    """name -> blob sha for every tracked file at HEAD."""
    rc, out = sh(["git", "ls-tree", "-r", "HEAD"], path)
    if rc != 0:
        return {"error": "ls-tree failed"}
    blobs = {}
    for line in out.splitlines():
        meta, _, name = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 3:
            blobs[name] = parts[2]
    return {"entry_count": len(blobs), "blobs": blobs}


def capture(targets: list[str], out: Path) -> int:
    payload = {
        "version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "wave_base": WAVE_BASE,
        "repos": [repo_entry(r) for r in PROTECTED_REPOS],
        "wave_base_tree": tree_manifest(WAVE_BASE),
        "files": [file_entry(Path(t)) for t in targets],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    live = [f for f in payload["files"] if f["exists"]]
    print(json.dumps({
        "status": "CAPTURED",
        "manifest": str(out),
        "repos": len(payload["repos"]),
        "tracked_blobs": payload["wave_base_tree"].get("entry_count"),
        "files_present": len(live),
        "files_missing": len(payload["files"]) - len(live),
    }))
    return 0


def verify(manifest_path: Path, out: Path) -> int:
    base = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[dict] = []

    for before in base["repos"]:
        if not before.get("exists"):
            continue
        now = repo_entry(before["path"])
        if not now.get("exists"):
            failures.append({"path": before["path"], "failure": "repo_missing"})
        elif now["head"] != before["head"]:
            failures.append({"path": before["path"], "failure": "head_moved",
                             "before": before["head"], "after": now["head"]})

    now_tree = tree_manifest(base["wave_base"])
    if now_tree.get("blobs") != base["wave_base_tree"].get("blobs"):
        b, a = base["wave_base_tree"].get("blobs", {}), now_tree.get("blobs", {})
        changed = [n for n in sorted(set(b) | set(a)) if b.get(n) != a.get(n)]
        failures.append({"path": base["wave_base"], "failure": "wave_base_tree_changed",
                         "changed_count": len(changed), "changed_sample": changed[:40]})

    file_results = []
    for before in base["files"]:
        now = file_entry(Path(before["path"]))
        changed = (now["sha256"] != before["sha256"]) or (now["exists"] != before["exists"])
        file_results.append({"path": before["path"], "changed": changed,
                             "before": before, "after": now})
        if changed:
            failures.append({"path": before["path"], "failure": "protected_file_changed",
                             "before_sha": before["sha256"], "after_sha": now["sha256"]})

    report = {
        "status": "FAILED" if failures else "VERIFIED",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "failures": failures,
        "repos": [repo_entry(r) for r in PROTECTED_REPOS],
        "file_results": file_results,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "failures": len(failures),
                      "files_checked": len(file_results), "report": str(out)}))
    return 1 if failures else 0


def main() -> int:
    cmd, manifest, report = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if cmd == "capture":
        listing = Path(sys.argv[4])
        targets = [ln.strip() for ln in listing.read_text(encoding="utf-8").splitlines()
                   if ln.strip() and not ln.strip().startswith("#")]
        return capture(targets, manifest)
    if cmd == "verify":
        return verify(manifest, report)
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    raise SystemExit(main())
