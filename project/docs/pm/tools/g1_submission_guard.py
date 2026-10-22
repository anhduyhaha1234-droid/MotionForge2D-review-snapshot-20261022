"""Replay a frozen G1 submission without executing code inside that submission.

The guard reports observed evidence only.  It never grants a Codex gate.
Example:
    python g1_submission_guard.py --candidate C:/path/candidate-07 \
        --output C:/path/verification-001 \
        --suite task/corrections/identity/r6/tests/test_g1_r1_correction.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def safe_relative(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe relative path: {value!r}")
    if ":" in path.parts[0]:
        raise ValueError(f"drive-qualified path: {value!r}")
    return path.as_posix()


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest().lower()


def inventory(candidate: Path) -> dict[str, Any]:
    manifest_path = candidate / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest.files must be a list")

    declared: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            issues.append("manifest entry is not an object")
            continue
        try:
            relative = safe_relative(str(entry["relative"]))
        except (KeyError, ValueError) as exc:
            issues.append(str(exc))
            continue
        if relative == "MANIFEST.json":
            issues.append("MANIFEST.json must not self-declare")
        if relative in declared:
            issues.append(f"duplicate entry: {relative}")
        if "path" in entry and Path(str(entry["path"])).resolve() != (candidate / Path(relative)).resolve():
            issues.append(f"absolute path points outside this candidate: {relative}")
        declared[relative] = entry

    actual: dict[str, Path] = {}
    for path in candidate.rglob("*"):
        relative = path.relative_to(candidate).as_posix()
        if path.is_symlink():
            issues.append(f"symlink is forbidden: {relative}")
        elif path.is_file() and relative != "MANIFEST.json":
            actual[relative] = path

    missing = sorted(declared.keys() - actual.keys())
    extra = sorted(actual.keys() - declared.keys())
    for relative in sorted(declared.keys() & actual.keys()):
        entry = declared[relative]
        path = actual[relative]
        if path.stat().st_size != entry.get("bytes"):
            issues.append(f"byte mismatch: {relative}")
        if digest(path) != str(entry.get("sha256", "")).lower():
            issues.append(f"sha256 mismatch: {relative}")
    if manifest.get("total_files") != len(declared):
        issues.append("manifest.total_files disagrees with entries")
    if missing:
        issues.append(f"missing: {missing}")
    if extra:
        issues.append(f"unmanifested: {extra}")
    return {
        "manifest_sha256": digest(manifest_path),
        "declared_files": len(declared),
        "actual_files": len(actual),
        "issues": issues,
        "ok": not issues,
    }


def run_command(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = utc_now()
    start = time.monotonic()
    try:
        process = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True,
            errors="replace", timeout=timeout, check=False,
        )
        exit_code = process.returncode
        stdout = process.stdout
        stderr = process.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stderr += "\nTIMEOUT_EXPIRED"
    return {
        "command": command, "cwd": str(cwd), "started_utc": started,
        "ended_utc": utc_now(), "duration_seconds": round(time.monotonic() - start, 3),
        "exit_code": exit_code, "stdout": stdout, "stderr": stderr,
    }


def verify(candidate: Path, output: Path, suites: list[str], timeout: int) -> dict[str, Any]:
    candidate = candidate.resolve(strict=True)
    output = output.resolve()
    if output == candidate or candidate in output.parents:
        raise ValueError("output must be outside frozen candidate")
    if output.exists():
        raise FileExistsError(f"verification output already exists: {output}")
    if not suites:
        raise ValueError("at least one --suite is required")
    suites = [safe_relative(suite) for suite in suites]
    if len(suites) != len(set(suites)):
        raise ValueError("duplicate suite argument")

    before = inventory(candidate)
    output.mkdir(parents=True)
    replay = output / "candidate_copy"
    shutil.copytree(candidate, replay)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    c02b1_scratch = output / "c02b1-worker"
    c02b1_scratch.mkdir()
    env["C02B1_WORKER_DIR"] = str(c02b1_scratch)
    runs: list[dict[str, Any]] = []
    for suite in suites:
        path = replay / Path(suite)
        if not path.is_file():
            runs.append({"suite": suite, "exit_code": 2, "error": "suite file absent from package"})
            continue
        collect = run_command(
            [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", suite],
            replay, env, timeout,
        )
        test = run_command(
            [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", suite],
            replay, env, timeout,
        ) if collect["exit_code"] == 0 else None
        runs.append({"suite": suite, "collection": collect, "test": test,
                     "exit_code": test["exit_code"] if test else collect["exit_code"]})
    after = inventory(candidate)
    ok = before["ok"] and after["ok"] and before == after and all(run["exit_code"] == 0 for run in runs)
    return {
        "schema": "motionforge.g1-submission-guard.v1", "candidate": str(candidate),
        "output": str(output), "verified_utc": utc_now(),
        "environment": {"python": sys.executable, "PYTHONPATH": "REMOVED",
                        "PYTEST_ADDOPTS": "REMOVED", "PYTHONDONTWRITEBYTECODE": "1",
                        "C02B1_WORKER_DIR": str(c02b1_scratch)},
        "inventory_before": before, "inventory_after": after, "runs": runs,
        "overall_verdict": "VERIFY_PASS" if ok else "VERIFY_FAILED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suite", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    try:
        result = verify(args.candidate, args.output, args.suite, args.timeout)
        result_path = args.output / "VERIFICATION.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{result['overall_verdict']} {result_path}")
        return 0 if result["overall_verdict"] == "VERIFY_PASS" else 1
    except Exception as exc:
        print(f"VERIFY_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
