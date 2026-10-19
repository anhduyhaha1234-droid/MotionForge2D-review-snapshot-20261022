"""Capture and verify critical write-set bytes for MotionForge2D workers.

This guard is intentionally small and dependency-free.  It protects existing,
dirty, or untracked files that cannot be recovered safely from Git by recording
their exact bytes before a writer starts and detecting unexpected removal,
protected-file drift, or destructive shrinkage after the writer stops.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 1


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _line_count(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def _inside(root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve()
    try:
        return resolved.relative_to(root)
    except ValueError as err:
        raise ValueError(f"path is outside guarded root: {resolved}") from err


def _entry(root: Path, relative: Path) -> dict[str, Any]:
    target = root / relative
    if not target.is_file():
        return {
            "path": relative.as_posix(),
            "exists": False,
            "size": None,
            "lines": None,
            "sha256": None,
        }
    data = target.read_bytes()
    return {
        "path": relative.as_posix(),
        "exists": True,
        "size": len(data),
        "lines": _line_count(data),
        "sha256": _sha256(data),
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def capture(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest).resolve()
    snapshot_root = Path(args.snapshot_dir).resolve() if args.snapshot_dir else None
    entries: list[dict[str, Any]] = []

    for raw in args.path:
        relative = _inside(root, root / raw)
        item = _entry(root, relative)
        if snapshot_root is not None and item["exists"]:
            snapshot = snapshot_root / relative
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, snapshot)
            snapshot_bytes = snapshot.read_bytes()
            item["snapshot"] = str(snapshot)
            item["snapshot_sha256"] = _sha256(snapshot_bytes)
            if item["snapshot_sha256"] != item["sha256"]:
                raise RuntimeError(f"snapshot hash mismatch while capturing {relative}")
        entries.append(item)

    manifest = {
        "version": MANIFEST_VERSION,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "root": str(root),
        "entries": entries,
    }
    _write_json(manifest_path, manifest)
    print(
        json.dumps(
            {"status": "CAPTURED", "manifest": str(manifest_path), "entries": len(entries)}
        )
    )
    return 0


def verify(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != MANIFEST_VERSION:
        raise ValueError(f"unsupported manifest version: {manifest.get('version')!r}")

    root = Path(args.root or manifest["root"]).resolve()
    allowed = {Path(value).as_posix() for value in args.allow_change}
    failures: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    shrink_limit = float(args.max_shrink_percent) / 100.0

    for baseline in manifest["entries"]:
        relative = Path(baseline["path"])
        current = _entry(root, relative)
        changed = current["sha256"] != baseline["sha256"] or current["exists"] != baseline["exists"]
        result = {
            "path": baseline["path"],
            "changed": changed,
            "allowed_change": baseline["path"] in allowed,
            "before": baseline,
            "after": current,
        }

        snapshot = baseline.get("snapshot")
        if snapshot:
            snapshot_path = Path(snapshot)
            snapshot_invalid = not snapshot_path.is_file() or (
                _sha256(snapshot_path.read_bytes()) != baseline.get("snapshot_sha256")
            )
            if snapshot_invalid:
                result["failure"] = "snapshot_missing_or_changed"
                failures.append(result)

        if not current["exists"] and baseline["exists"]:
            result["failure"] = "guarded_file_missing"
            failures.append(result)
        elif changed and baseline["path"] not in allowed:
            result["failure"] = "protected_file_changed"
            failures.append(result)
        elif changed and baseline["path"] in allowed and baseline["exists"]:
            before_size = int(baseline["size"] or 0)
            after_size = int(current["size"] or 0)
            before_lines = int(baseline["lines"] or 0)
            after_lines = int(current["lines"] or 0)
            size_floor = before_size * (1.0 - shrink_limit)
            line_floor = before_lines * (1.0 - shrink_limit)
            if after_size < size_floor or after_lines < line_floor:
                result["failure"] = "destructive_shrink"
                failures.append(result)

        results.append(result)

    report = {
        "status": "FAILED" if failures else "VERIFIED",
        "manifest": str(manifest_path),
        "root": str(root),
        "max_shrink_percent": args.max_shrink_percent,
        "failures": failures,
        "results": results,
    }
    if args.report:
        _write_json(Path(args.report).resolve(), report)
    print(
        json.dumps(
            {"status": report["status"], "failures": len(failures), "entries": len(results)}
        )
    )
    return 1 if failures else 0


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)

    capture_parser = subcommands.add_parser(
        "capture", help="capture hashes and optional byte snapshots"
    )
    capture_parser.add_argument("--root", required=True)
    capture_parser.add_argument("--manifest", required=True)
    capture_parser.add_argument("--snapshot-dir")
    capture_parser.add_argument("--path", action="append", required=True)
    capture_parser.set_defaults(func=capture)

    verify_parser = subcommands.add_parser(
        "verify", help="verify protected drift and destructive shrinkage"
    )
    verify_parser.add_argument("--root")
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument("--allow-change", action="append", default=[])
    verify_parser.add_argument("--max-shrink-percent", type=float, default=20.0)
    verify_parser.add_argument("--report")
    verify_parser.set_defaults(func=verify)
    return command


def main() -> int:
    args = parser().parse_args()
    if not 0.0 <= getattr(args, "max_shrink_percent", 20.0) < 100.0:
        raise ValueError("max-shrink-percent must be in [0, 100)")
    return int(args.func(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as err:
        print(json.dumps({"status": "ERROR", "detail": str(err)}), file=sys.stderr)
        raise SystemExit(2) from err
