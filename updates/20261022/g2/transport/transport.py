"""G2-PREP-01: byte-verified, CPU-only transport of approved G1 C16.

The CLI uses immutable authority and input paths. ``execute`` accepts alternate
read paths solely so negative tests can use disposable copies without changing
the frozen submission or the source video.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import traceback
import uuid


WRITE_ROOT = Path(r"C:\Users\Admin\Documents\Codex\g2p01-transport")
CANDIDATE = Path(
    r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2"
    r"\outputs\motionforge-g1-review-04-20261020\submissions\g1-candidate-16"
)
SOURCE = Path(
    r"C:\Users\Admin\.gemini\antigravity\scratch\goha_mmo_clone\backend"
    r"\downloads\Tại sao thật tệ khi ĐỨNG TÊN HỘ công ty？.mp4"
)
REVIEW = Path(r"C:\Users\Admin\Documents\Codex\g1c16-review\REVIEW_G1_C16_VI.md")
GUARD = Path(r"C:\Users\Admin\Documents\Codex\g1c16-r2\VERIFICATION.json")
GUARD_PROCESS = Path(
    r"C:\Users\Admin\Documents\Codex\g1c16-review\GUARD_PROCESS_RECEIPT.json"
)
MANIFEST_SHA = "4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82"
REVIEW_SHA = "8a466b1aa14b1a1761b69c75540213bcd631c5add749ea8e9acdceb90f8fcfdc"
GUARD_SHA = "ccc43a4808f10772128c490c2aa227d3708714fceaf9f275160e61acb35799a7"
GUARD_PROCESS_SHA = "47d092661bf5c86c61ffc569ffe02861bf60f67ae1d2b608e20debafbee1c47e"
SOURCE_SHA = "5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2"
SOURCE_BYTES = 36_971_916
SOURCE_DEST = "task/source/source_full.mp4"
EXPECTED_DURATION = Decimal("1321.215420")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class Block(Exception):
    def __init__(self, code: str, detail: object):
        super().__init__(str(detail))
        self.code = code
        self.detail = detail


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def regular_file(path: Path) -> os.stat_result:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise Block("INPUT_MISSING", str(path)) from exc
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE:
        raise Block("NONREGULAR_INPUT", str(path))
    return info


def sha256_file(path: Path) -> str:
    regular_file(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=json_no_duplicate_keys)
    except (OSError, UnicodeError, ValueError) as exc:
        raise Block("INVALID_JSON", {"path": str(path), "error": str(exc)}) from exc
    if not isinstance(value, dict):
        raise Block("INVALID_JSON", {"path": str(path), "error": "root is not object"})
    return value


def relative_name(raw: object) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
        raise Block("INVALID_MANIFEST_PATH", raw)
    name = PurePosixPath(raw)
    if name.is_absolute() or name.as_posix() != raw:
        raise Block("INVALID_MANIFEST_PATH", raw)
    for part in name.parts:
        if part in ("", ".", "..") or ":" in part or part.endswith((" ", ".")):
            raise Block("INVALID_MANIFEST_PATH", raw)
        if part.upper().split(".")[0] in WINDOWS_RESERVED:
            raise Block("INVALID_MANIFEST_PATH", raw)
    return raw


def scan_tree(root: Path) -> dict[str, Path]:
    try:
        info = root.lstat()
    except FileNotFoundError as exc:
        raise Block("TREE_MISSING", str(root)) from exc
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE:
        raise Block("NONREGULAR_TREE", str(root))
    found = {}
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise Block("TREE_SCAN_FAILED", {"path": str(directory), "error": str(exc)}) from exc
        for entry in entries:
            path = Path(entry.path)
            item = entry.stat(follow_symlinks=False)
            if getattr(item, "st_file_attributes", 0) & REPARSE or entry.is_symlink():
                raise Block("REPARSE_IN_TREE", str(path))
            if stat.S_ISDIR(item.st_mode):
                stack.append(path)
            elif stat.S_ISREG(item.st_mode):
                rel = path.relative_to(root).as_posix()
                relative_name(rel)
                found[rel] = path
            else:
                raise Block("NONREGULAR_IN_TREE", str(path))
    return found


def verify_authority(observed: dict) -> None:
    pins = {
        "review": (REVIEW, REVIEW_SHA),
        "guard": (GUARD, GUARD_SHA),
        "guard_process": (GUARD_PROCESS, GUARD_PROCESS_SHA),
    }
    observed["authority"] = {}
    for label, (path, expected) in pins.items():
        actual = sha256_file(path)
        observed["authority"][label] = {"path": str(path), "expected_sha256": expected, "actual_sha256": actual}
        if actual != expected:
            raise Block("AUTHORITY_SHA_MISMATCH", label)
    review_text = REVIEW.read_text(encoding="utf-8")
    if "G1_APPROVED" not in review_text or MANIFEST_SHA not in review_text:
        raise Block("REVIEW_PIN_MISMATCH", str(REVIEW))
    guard = read_json(GUARD)
    process = read_json(GUARD_PROCESS)
    before = guard.get("inventory_before", {})
    after = guard.get("inventory_after", {})
    if (
        guard.get("overall_verdict") != "VERIFY_PASS"
        or guard.get("candidate") != str(CANDIDATE)
        or any(x.get("manifest_sha256") != MANIFEST_SHA or x.get("ok") is not True for x in (before, after))
        or process.get("exit_code") != 0
        or process.get("guard_json_sha256") != GUARD_SHA
    ):
        raise Block("GUARD_PIN_MISMATCH", "guard verdict, candidate, inventory, or process exit")


def verify_candidate(root: Path, observed: dict) -> dict[str, dict]:
    manifest_path = root / "MANIFEST.json"
    manifest_actual = sha256_file(manifest_path)
    observed["candidate"] = {"path": str(root), "manifest_sha256": manifest_actual}
    if manifest_actual != MANIFEST_SHA:
        raise Block("MANIFEST_SHA_MISMATCH", {"expected": MANIFEST_SHA, "actual": manifest_actual})
    manifest = read_json(manifest_path)
    rows = manifest.get("files")
    if (
        manifest.get("schema") != 1
        or manifest.get("submission_id") != "g1-candidate-16"
        or manifest.get("total_files") != 74
        or not isinstance(rows, list)
        or len(rows) != 74
    ):
        raise Block("MANIFEST_SCHEMA_MISMATCH", "C16 schema, identity, or count")
    expected = {}
    names_folded = set()
    for row in rows:
        if not isinstance(row, dict):
            raise Block("MANIFEST_SCHEMA_MISMATCH", row)
        rel = relative_name(row.get("relative"))
        size, digest = row.get("bytes"), row.get("sha256")
        if rel == "MANIFEST.json" or rel == SOURCE_DEST or rel.casefold() in names_folded:
            raise Block("MANIFEST_PATH_COLLISION", rel)
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
            raise Block("MANIFEST_SCHEMA_MISMATCH", rel)
        expected[rel] = {"bytes": size, "sha256": digest}
        names_folded.add(rel.casefold())
    for needed in ("task/chunk_plan.json", "task/corrections/identity/r6/scripts/r6_gate.py", "dependencies_snapshot/r6_common.py", "source_snapshot/r6_gate.py"):
        if needed not in expected:
            raise Block("REQUIRED_SNAPSHOT_MISSING", needed)
    actual = scan_tree(root)
    observed["candidate"]["actual_inventory"] = sorted(actual)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected) - {"MANIFEST.json"})
    if missing or extra or "MANIFEST.json" not in actual:
        raise Block("CANDIDATE_INVENTORY_MISMATCH", {"missing": missing, "extra": extra})
    mismatches = []
    verified = []
    for rel in sorted(expected):
        size = regular_file(actual[rel]).st_size
        digest = sha256_file(actual[rel])
        verified.append({"relative": rel, "bytes": size, "sha256": digest})
        if size != expected[rel]["bytes"] or digest != expected[rel]["sha256"]:
            mismatches.append(rel)
    observed["candidate"]["verified_files"] = verified
    if mismatches:
        raise Block("CANDIDATE_BYTES_MISMATCH", mismatches)
    return expected


def verify_source(path: Path, observed: dict, *, ffprobe: bool = True) -> None:
    info = regular_file(path)
    observed["source"] = {"path": str(path), "bytes": info.st_size, "expected_bytes": SOURCE_BYTES}
    if info.st_size != SOURCE_BYTES:
        raise Block("SOURCE_SIZE_MISMATCH", {"expected": SOURCE_BYTES, "actual": info.st_size})
    digest = sha256_file(path)
    observed["source"]["sha256"] = digest
    if digest != SOURCE_SHA:
        raise Block("SOURCE_SHA_MISMATCH", {"expected": SOURCE_SHA, "actual": digest})
    if not ffprobe:
        return
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate",
        "-of", "json", str(path),
    ]
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Block("FFPROBE_FAILED", str(exc)) from exc
    observed["source"]["ffprobe"] = {
        "command": command, "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr
    }
    if run.returncode != 0:
        raise Block("FFPROBE_FAILED", run.returncode)
    try:
        probe = json.loads(run.stdout)
        streams = probe["streams"]
        video = [s for s in streams if s.get("codec_type") == "video"]
        audio = [s for s in streams if s.get("codec_type") == "audio"]
        duration = Decimal(probe["format"]["duration"])
        shape_ok = (
            len(streams) == 2 and len(video) == 1 and len(audio) == 1
            and video[0].get("index") == 0 and audio[0].get("index") == 1
            and video[0].get("codec_name") == "h264" and audio[0].get("codec_name") == "aac"
            and video[0].get("width") == 640 and video[0].get("height") == 360
            and Fraction(video[0]["r_frame_rate"]) == 30
            and Fraction(video[0]["avg_frame_rate"]) == 30
            and duration == EXPECTED_DURATION
        )
    except (KeyError, TypeError, ValueError, InvalidOperation, ZeroDivisionError) as exc:
        raise Block("FFPROBE_SHAPE_MISMATCH", str(exc)) from exc
    if not shape_ok:
        raise Block("FFPROBE_SHAPE_MISMATCH", probe)


def checked_output_paths(pilot: Path, receipt: Path, candidate: Path, source: Path) -> None:
    root = WRITE_ROOT.resolve(strict=True)
    root_info = WRITE_ROOT.lstat()
    if not stat.S_ISDIR(root_info.st_mode) or getattr(root_info, "st_file_attributes", 0) & REPARSE:
        raise Block("WRITE_ROOT_UNSAFE", str(WRITE_ROOT))
    pilot_r, receipt_r = pilot.resolve(strict=False), receipt.resolve(strict=False)
    candidate_r, source_r = candidate.resolve(strict=False), source.resolve(strict=False)
    if not pilot.is_absolute() or not receipt.is_absolute():
        raise Block("OUTPUT_PATH_NOT_ABSOLUTE", {"pilot": str(pilot), "receipt": str(receipt)})
    if not pilot_r.is_relative_to(root) or pilot_r == root or not receipt_r.is_relative_to(root):
        raise Block("OUTPUT_PATH_ESCAPE", {"pilot": str(pilot), "receipt": str(receipt)})
    if (
        receipt_r == root or receipt_r.is_relative_to(pilot_r)
        or receipt_r.is_relative_to(candidate_r) or receipt_r == source_r
        or pilot_r.is_relative_to(candidate_r) or candidate_r.is_relative_to(pilot_r)
        or source_r.is_relative_to(pilot_r)
    ):
        raise Block("OUTPUT_PATH_COLLISION", {"pilot": str(pilot), "receipt": str(receipt)})
    if pilot_r.parent != root:
        raise Block("PILOT_NOT_DIRECT_CHILD", str(pilot))
    if pilot.exists() or pilot.is_symlink():
        raise Block("PILOT_EXISTS", str(pilot))
    if receipt.exists() or receipt.is_symlink():
        raise Block("RECEIPT_EXISTS", str(receipt))


def safe_receipt_path(requested: Path, pilot: Path, candidate: Path, source: Path) -> Path:
    root = WRITE_ROOT.resolve(strict=True)
    resolved = requested.resolve(strict=False)
    forbidden = (pilot.resolve(strict=False), candidate.resolve(strict=False))
    if (
        requested.is_absolute() and resolved.is_relative_to(root) and resolved != root
        and not any(resolved.is_relative_to(path) for path in forbidden)
        and resolved != source.resolve(strict=False)
        and not requested.exists() and not requested.is_symlink()
    ):
        return requested
    return WRITE_ROOT / "receipts" / f"blocked-{uuid.uuid4().hex}.json"


def copy_exact(source: Path, destination: Path, size: int, digest: str) -> None:
    regular_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    measured = hashlib.sha256()
    written = 0
    with source.open("rb") as incoming, destination.open("xb") as outgoing:
        while chunk := incoming.read(1024 * 1024):
            outgoing.write(chunk)
            measured.update(chunk)
            written += len(chunk)
    if written != size or measured.hexdigest() != digest:
        raise Block("COPY_BYTES_MISMATCH", {"path": str(source), "bytes": written, "sha256": measured.hexdigest()})


def transport(candidate: Path, source: Path, pilot: Path, expected: dict[str, dict], observed: dict) -> None:
    pilot.mkdir(parents=False, exist_ok=False)
    observed["pilot_path"] = str(pilot)
    manifest_size = regular_file(candidate / "MANIFEST.json").st_size
    copy_exact(candidate / "MANIFEST.json", pilot / "MANIFEST.json", manifest_size, MANIFEST_SHA)
    for rel in sorted(expected):
        row = expected[rel]
        copy_exact(candidate / rel, pilot / rel, row["bytes"], row["sha256"])
    copy_exact(source, pilot / SOURCE_DEST, SOURCE_BYTES, SOURCE_SHA)
    actual = scan_tree(pilot)
    expected_names = set(expected) | {"MANIFEST.json", SOURCE_DEST}
    if set(actual) != expected_names:
        raise Block("PILOT_INVENTORY_MISMATCH", {"missing": sorted(expected_names - set(actual)), "extra": sorted(set(actual) - expected_names)})
    copied = []
    for rel in sorted(actual):
        target_size = SOURCE_BYTES if rel == SOURCE_DEST else manifest_size if rel == "MANIFEST.json" else expected[rel]["bytes"]
        target_sha = SOURCE_SHA if rel == SOURCE_DEST else MANIFEST_SHA if rel == "MANIFEST.json" else expected[rel]["sha256"]
        size, digest = regular_file(actual[rel]).st_size, sha256_file(actual[rel])
        copied.append({"relative": rel, "bytes": size, "sha256": digest})
        if (size, digest) != (target_size, target_sha):
            raise Block("PILOT_BYTES_MISMATCH", rel)
    observed["copied_files"] = copied
    observed["origin_after_copy"] = {}
    verify_candidate(candidate, observed["origin_after_copy"])
    verify_source(source, observed["origin_after_copy"], ffprobe=False)
    observed["authority_after_copy"] = {}
    verify_authority(observed["authority_after_copy"])


def execute(pilot: Path, receipt: Path, *, candidate: Path = CANDIDATE, source: Path = SOURCE) -> int:
    evidence = {
        "task_id": "G2-PREP-01",
        "started_utc": utc_now(),
        "inputs": {"candidate": str(candidate), "source": str(source)},
        "outputs": {"pilot": str(pilot), "receipt": str(receipt)},
        "pins": {
            "candidate_id": "g1-candidate-16", "gate": "G1_APPROVED",
            "manifest_sha256": MANIFEST_SHA, "source_bytes": SOURCE_BYTES,
            "source_sha256": SOURCE_SHA, "duration_seconds": str(EXPECTED_DURATION),
            "video": "h264 640x360 30/1", "audio": "aac",
            "review_path": str(REVIEW), "review_sha256": REVIEW_SHA,
            "guard_path": str(GUARD), "guard_sha256": GUARD_SHA,
            "guard_process_path": str(GUARD_PROCESS), "guard_process_sha256": GUARD_PROCESS_SHA,
        },
        "observed": {},
        "media_readiness": "NOT_ASSESSED",
        "g2_exact_300s_pilot": "NOT_RUN",
    }
    try:
        checked_output_paths(pilot, receipt, candidate, source)
        verify_authority(evidence["observed"])
        expected = verify_candidate(candidate, evidence["observed"])
        verify_source(source, evidence["observed"])
        transport(candidate, source, pilot, expected, evidence["observed"])
        evidence["transport_status"] = "SELF_VERIFIED_PENDING_ROOT_REVIEW"
        code = 0
    except Block as exc:
        evidence["transport_status"] = "BLOCKED"
        evidence["block"] = {"code": exc.code, "detail": exc.detail}
        code = 2
    except Exception as exc:
        evidence["transport_status"] = "BLOCKED"
        evidence["block"] = {"code": "UNEXPECTED_ERROR", "detail": str(exc), "traceback": traceback.format_exc()}
        code = 3
    evidence["ended_utc"] = utc_now()
    evidence["process_exit_code"] = code
    actual_receipt = safe_receipt_path(receipt, pilot, candidate, source)
    evidence["outputs"]["actual_receipt"] = str(actual_receipt)
    try:
        actual_receipt.parent.mkdir(parents=True, exist_ok=True)
        with actual_receipt.open("x", encoding="utf-8") as stream:
            json.dump(evidence, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except OSError as exc:
        print(f"RECEIPT_WRITE_FAILED {exc}", file=sys.stderr)
        return 3
    print(f"{evidence['transport_status']} exit={code} receipt={actual_receipt}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True, help="new, non-existing pilot directory within G2-PREP-01 write root")
    parser.add_argument("--receipt", type=Path, required=True, help="new receipt path within G2-PREP-01 write root")
    args = parser.parse_args()
    return execute(args.pilot, args.receipt)


if __name__ == "__main__":
    sys.exit(main())
