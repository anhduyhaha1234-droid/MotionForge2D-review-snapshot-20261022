"""Disposable fail-closed challenges for G2-PREP-01. Run with python -B."""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shutil
import sys
import uuid

from transport import CANDIDATE, SOURCE, WRITE_ROOT, execute


def challenge(label: str, expected: str, pilot: Path, receipt: Path, **overrides: Path) -> dict:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = execute(pilot, receipt, **overrides)
    line = output.getvalue().strip()
    actual_receipt = Path(line.rsplit("receipt=", 1)[-1])
    record = json.loads(actual_receipt.read_text(encoding="utf-8"))
    actual = record.get("block", {}).get("code")
    result = {
        "case": label,
        "expected_block": expected,
        "actual_block": actual,
        "transport_exit": exit_code,
        "pilot_exists": pilot.exists(),
        "receipt": str(actual_receipt),
        "stdout": line,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if exit_code != 2 or actual != expected or pilot.exists():
        raise AssertionError(result)
    return result


def main() -> int:
    tag = uuid.uuid4().hex[:12]
    run = WRITE_ROOT / "negative-repros" / tag
    run.mkdir(parents=True, exist_ok=False)
    results = []

    results.append(challenge(
        "missing_source", "INPUT_MISSING", WRITE_ROOT / f"neg-missing-source-{tag}",
        run / "missing-source-receipt.json", source=run / "missing.mp4",
    ))

    tampered_video = run / "tampered-same-size.mp4"
    shutil.copy2(SOURCE, tampered_video)
    with tampered_video.open("r+b") as stream:
        stream.seek(1024)
        original = stream.read(1)
        stream.seek(1024)
        stream.write(bytes([original[0] ^ 0x01]))
    assert tampered_video.stat().st_size == SOURCE.stat().st_size
    results.append(challenge(
        "tampered_source_same_size", "SOURCE_SHA_MISMATCH",
        WRITE_ROOT / f"neg-tampered-source-{tag}", run / "tampered-source-receipt.json",
        source=tampered_video,
    ))

    extra = run / "candidate-extra"
    shutil.copytree(CANDIDATE, extra)
    (extra / "task" / "unexpected.pyc").write_bytes(b"extra inventory")
    results.append(challenge(
        "candidate_extra_pyc", "CANDIDATE_INVENTORY_MISMATCH",
        WRITE_ROOT / f"neg-extra-inventory-{tag}", run / "extra-inventory-receipt.json",
        candidate=extra,
    ))

    missing = run / "candidate-missing"
    shutil.copytree(CANDIDATE, missing)
    (missing / "task" / "chunk_plan.json").unlink()
    results.append(challenge(
        "candidate_missing_file", "CANDIDATE_INVENTORY_MISMATCH",
        WRITE_ROOT / f"neg-missing-inventory-{tag}", run / "missing-inventory-receipt.json",
        candidate=missing,
    ))

    tampered = run / "candidate-tampered"
    shutil.copytree(CANDIDATE, tampered)
    chunk_plan = tampered / "task" / "chunk_plan.json"
    original_size = chunk_plan.stat().st_size
    with chunk_plan.open("r+b") as stream:
        first = stream.read(1)
        stream.seek(0)
        stream.write(bytes([first[0] ^ 0x01]))
    assert chunk_plan.stat().st_size == original_size
    results.append(challenge(
        "candidate_tampered_same_size", "CANDIDATE_BYTES_MISMATCH",
        WRITE_ROOT / f"neg-tampered-inventory-{tag}", run / "tampered-inventory-receipt.json",
        candidate=tampered,
    ))

    escaped = WRITE_ROOT.parent / f"g2p01-escape-must-not-exist-{tag}"
    assert not escaped.exists()
    results.append(challenge(
        "pilot_path_escape", "OUTPUT_PATH_ESCAPE", escaped,
        run / "escape-receipt.json",
    ))

    duplicate_pilot = WRITE_ROOT / f"neg-existing-pilot-{tag}"
    duplicate_pilot.mkdir(exist_ok=False)
    sentinel = duplicate_pilot / "sentinel.txt"
    sentinel.write_text("KEEP\n", encoding="utf-8")
    output = io.StringIO()
    receipt = run / "duplicate-pilot-receipt.json"
    with redirect_stdout(output):
        exit_code = execute(duplicate_pilot, receipt)
    record = json.loads(receipt.read_text(encoding="utf-8"))
    result = {
        "case": "duplicate_pilot",
        "expected_block": "PILOT_EXISTS",
        "actual_block": record.get("block", {}).get("code"),
        "transport_exit": exit_code,
        "sentinel": sentinel.read_text(encoding="utf-8"),
        "receipt": str(receipt),
        "stdout": output.getvalue().strip(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if exit_code != 2 or result["actual_block"] != "PILOT_EXISTS" or result["sentinel"] != "KEEP\n":
        raise AssertionError(result)
    results.append(result)

    duplicate_receipt = run / "existing-receipt.json"
    duplicate_receipt.write_text("KEEP\n", encoding="utf-8")
    results.append(challenge(
        "duplicate_receipt", "RECEIPT_EXISTS",
        WRITE_ROOT / f"neg-existing-receipt-{tag}", duplicate_receipt,
    ))
    if duplicate_receipt.read_text(encoding="utf-8") != "KEEP\n":
        raise AssertionError("existing receipt changed")

    summary = {
        "task_id": "G2-PREP-01", "created_utc": datetime.now(timezone.utc).isoformat(),
        "command": f"{sys.executable} -B {Path(__file__).resolve()}",
        "cases": results, "result": "NEGATIVE_CHALLENGES_PASSED",
    }
    summary_path = run / "NEGATIVE_SUMMARY.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"NEGATIVE_CHALLENGES_PASSED cases={len(results)} summary={summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
