"""R6 Canonical Evidence Contract — strict validation of artifacts and atomic publication.

Replaces heuristics with:
- Decodable PIL image validation
- Real ffprobe container and stream validation for video artifacts
- Strict schema and actual dependency verifier invocation
- Atomic stage-validate-publish protocol ensuring manifest hashes match published matrix exactly
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from PIL import Image


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def validate_evidence_image(path: Path) -> tuple[bool, str]:
    """Validate that path exists, is non-empty, and decodes to a valid image."""
    if not path.exists():
        return False, f"image file does not exist: {path}"
    if path.stat().st_size < 100:
        return False, f"image file too small: {path.stat().st_size} bytes"
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            w, h = im.size
            if w <= 0 or h <= 0:
                return False, f"invalid image dimensions: {im.size}"
        return True, "ok"
    except Exception as exc:
        return False, f"image decode error: {exc}"


def validate_evidence_video(path: Path, expected_frames: int | None = None) -> tuple[bool, str]:
    """Validate that path exists, passes ffprobe stream/container checks, and has expected frames."""
    if not path.exists():
        return False, f"video file does not exist: {path}"
    if path.stat().st_size < 1000:
        return False, f"video file too small: {path.stat().st_size} bytes"
    try:
        cmd = [
            "ffprobe", "-v", "error", "-count_frames",
            "-show_streams", "-show_format", "-of", "json",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            return False, f"ffprobe error: {res.stderr.strip()}"
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        v_streams = [s for s in streams if s.get("codec_type") == "video"]
        if not v_streams:
            return False, "no video streams found in container"
        v0 = v_streams[0]
        if expected_frames is not None:
            nb = v0.get("nb_read_frames") or v0.get("nb_frames")
            if nb is not None:
                try:
                    if int(nb) != expected_frames:
                        return False, f"expected {expected_frames} frames, got {nb}"
                except ValueError:
                    pass
        return True, "ok"
    except Exception as exc:
        return False, f"video validation error: {exc}"


def validate_evidence_json(path: Path, required_keys: set[str] | None = None) -> tuple[bool, dict[str, Any] | None, str]:
    """Validate that path exists, size >= 10 bytes, parses as valid JSON, and contains required keys."""
    if not path.exists():
        return False, None, f"json file does not exist: {path}"
    if path.stat().st_size < 10:
        return False, None, f"json file too small: {path.stat().st_size} bytes"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False, None, f"json root must be an object, got {type(data)}"
        if required_keys:
            missing = required_keys - set(data.keys())
            if missing:
                return False, None, f"json missing required keys {sorted(missing)} in {path}"
        return True, data, "ok"
    except Exception as exc:
        return False, None, f"json parse error: {exc}"


def validate_deps_evidence(dep_path: Path, shot: str | None = None, fid: int | None = None) -> tuple[bool, str]:
    """Validate that a dependency record exists, parses, and passes full dependency verification."""
    if not dep_path.exists():
        return False, f"deps file does not exist: {dep_path}"
    if dep_path.stat().st_size < 50:
        return False, f"deps file too small: {dep_path.stat().st_size} bytes"
    try:
        import r6_cache as CA
        dep = json.loads(dep_path.read_text(encoding="utf-8"))
        kind = dep.get("kind")
        if kind == "r6_key_deps_v4_per_actor":
            return CA.verify_complete_deps(dep, shot, fid)
        elif kind == "r6_key_deps_v4_asset":
            return CA.verify_complete_asset_deps(dep, shot, fid)
        else:
            return False, f"unknown or legacy deps kind: {kind}"
    except Exception as exc:
        return False, f"deps verification error: {exc}"


def run_q05_tests(test_file: Path, invocation_id: str) -> dict[str, Any]:
    """Run the exact test bytes and derive results from pytest's process and JUnit XML."""
    if not test_file.is_file() or not invocation_id:
        raise ValueError("Q05 test file or invocation missing")
    if os.environ.get("R6_Q05_RUNNER_ACTIVE"):
        raise RuntimeError("nested Q05 runner invocation blocked")
    with tempfile.TemporaryDirectory(prefix="r6-q05-") as temp_dir:
        junit = Path(temp_dir) / "junit.xml"
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   f"--junitxml={junit}", str(test_file)]
        runner_env = os.environ.copy()
        runner_env["R6_Q05_RUNNER_ACTIVE"] = invocation_id
        result = subprocess.run(command, cwd=str(test_file.parent), env=runner_env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=120, check=False)
        cases: list[str] = []
        failed = 0
        skipped = 0
        if junit.is_file():
            root = ET.parse(junit).getroot()
            for case in root.iter("testcase"):
                name = case.get("name")
                if not name:
                    raise ValueError("Q05 JUnit testcase has no name")
                cases.append(f"{test_file.name}::{name}")
                failed += any(case.find(tag) is not None for tag in ("failure", "error"))
                skipped += case.find("skipped") is not None
        return {
            "schema": "r6-q05-pytest-v1",
            "invocation_id": invocation_id,
            "test_file": str(test_file.resolve()),
            "test_file_sha256": sha256_file(test_file),
            "verifier": "pytest-junit-v1",
            "exit_code": result.returncode,
            "tests_run": len(cases),
            "node_ids": sorted(cases),
            "failed": failed,
            "skipped": skipped,
            "stdout_sha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "all_passed": result.returncode == 0 and bool(cases) and failed == 0 and skipped == 0,
        }


def stage_and_publish_matrix(rows: dict[str, Any], manifest_data: dict[str, Any], ns_dir: Path, batch_mode: str = "engineering") -> None:
    """Atomic stage-validate-publish protocol ensuring manifest hashes match published matrix exactly.
    
    1. Writes matrix evidence to matrix_tmp.
    2. Updates manifest_data so R6_MATRIX_EVIDENCE.json entry contains the exact hash and size of matrix_tmp.
    3. Writes manifest_tmp.
    4. Validates gate_batch_conformance on staged matrix and manifest items.
    5. Atomically replaces final files and creates commit marker.
    """
    import r6_gate as G
    
    ns_dir.mkdir(parents=True, exist_ok=True)
    matrix_tmp = ns_dir / "R6_MATRIX_EVIDENCE.json.tmp"
    manifest_tmp = ns_dir / "R6G_MANIFEST.json.tmp"
    
    matrix_final = ns_dir / "R6_MATRIX_EVIDENCE.json"
    manifest_final = ns_dir / "R6G_MANIFEST.json"
    marker_final = ns_dir / ".submission_freeze.json"

    # Remove any existing freeze marker during staging to prevent stale validated state
    if marker_final.exists():
        try:
            marker_final.unlink()
        except Exception:
            pass
    
    matrix_payload = {
        "at": manifest_data.get("at"),
        "rows": rows
    }
    
    # 1. Stage matrix evidence
    matrix_tmp.write_text(json.dumps(matrix_payload, ensure_ascii=False, indent=1), encoding="utf-8")
    matrix_sha = sha256_file(matrix_tmp)
    matrix_size = matrix_tmp.stat().st_size
    
    # 2. Update manifest items to bind exact staged matrix hash
    items = manifest_data.get("items", [])
    updated_items = []
    matrix_rel_found = False
    for item in items:
        if item.get("path") == "R6_MATRIX_EVIDENCE.json" or Path(item.get("path", "")).name == "R6_MATRIX_EVIDENCE.json":
            item["bytes"] = matrix_size
            item["sha256"] = matrix_sha
            matrix_rel_found = True
        updated_items.append(item)
    if not matrix_rel_found:
        updated_items.append({
            "path": "R6_MATRIX_EVIDENCE.json",
            "absolute_path": str(matrix_final),
            "bytes": matrix_size,
            "sha256": matrix_sha
        })
    manifest_data["items"] = updated_items
    manifest_data["count"] = len(updated_items)
    
    # 3. Stage manifest
    manifest_tmp.write_text(json.dumps(manifest_data, indent=1), encoding="utf-8")
    
    try:
        # 4. Validate gate on staged matrix and manifest items
        verdicts = {q: v["verdict"] for q, v in rows.items()}
        proof = {q: v.get("proof", {}) for q, v in rows.items() if "proof" in v}
        G.gate_batch_conformance({"invocation_id": ns_dir.name, "invocation_dir": str(ns_dir.resolve()), "matrix": verdicts,
                                  "evidence": rows, "proof": proof,
                                  "artifacts": updated_items}, mode=batch_mode)
        
        # 5. Publish atomically
        shutil.move(str(matrix_tmp), str(matrix_final))
        shutil.move(str(manifest_tmp), str(manifest_final))
        
        marker_data = {
            "at": manifest_data.get("at"),
            "manifest_sha256": sha256_file(manifest_final),
            "matrix_sha256": sha256_file(matrix_final),
            "status": "FROZEN_VALIDATED"
        }
        marker_final.write_text(json.dumps(marker_data, indent=2), encoding="utf-8")
    except Exception as exc:
        if matrix_tmp.exists():
            try:
                matrix_tmp.unlink()
            except Exception:
                pass
        if manifest_tmp.exists():
            try:
                manifest_tmp.unlink()
            except Exception:
                pass
        if marker_final.exists():
            try:
                marker_final.unlink()
            except Exception:
                pass
        raise exc


def verify_submission_freeze(ns_dir: Path) -> tuple[bool, str]:
    """Verify that a published namespace has an intact and consistent freeze marker.
    
    Checks that:
    1. .submission_freeze.json exists and parses
    2. R6G_MANIFEST.json exists and sha256 matches marker
    3. R6_MATRIX_EVIDENCE.json exists and sha256 matches marker
    4. status is 'FROZEN_VALIDATED'
    """
    marker_p = ns_dir / ".submission_freeze.json"
    matrix_p = ns_dir / "R6_MATRIX_EVIDENCE.json"
    manifest_p = ns_dir / "R6G_MANIFEST.json"
    
    if not marker_p.exists():
        return False, f"freeze marker missing: {marker_p}"
    if not matrix_p.exists():
        return False, f"matrix evidence missing: {matrix_p}"
    if not manifest_p.exists():
        return False, f"manifest missing: {manifest_p}"
        
    try:
        marker_data = json.loads(marker_p.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"freeze marker corrupt: {exc}"
        
    if marker_data.get("status") != "FROZEN_VALIDATED":
        return False, f"freeze marker status invalid: {marker_data.get('status')}"
        
    cur_matrix_sha = sha256_file(matrix_p)
    if cur_matrix_sha != marker_data.get("matrix_sha256"):
        return False, f"matrix hash mismatch against marker: {cur_matrix_sha} vs {marker_data.get('matrix_sha256')}"
        
    cur_manifest_sha = sha256_file(manifest_p)
    if cur_manifest_sha != marker_data.get("manifest_sha256"):
        return False, f"manifest hash mismatch against marker: {cur_manifest_sha} vs {marker_data.get('manifest_sha256')}"
        
    return True, "ok"

