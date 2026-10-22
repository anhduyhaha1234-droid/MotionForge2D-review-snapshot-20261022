"""Package a Codex G1 correction without inventing test or media results.

The output is a frozen source candidate. Run g1_submission_guard.py separately
and keep its raw VERIFICATION.json outside the candidate.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_source(source: Path, destination: Path, exclude_work: bool = False) -> None:
    patterns = ["__pycache__", "*.pyc", ".pytest_cache", ".coverage"]
    if exclude_work:
        patterns.append("work")  # test scratch/media; never part of a source candidate
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*patterns))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, base, output = (p.resolve() for p in (args.source, args.base, args.output))
    if not (source / "task/chunk_plan.json").is_file():
        raise SystemExit("source task/chunk_plan.json missing")
    if not (base / "MANIFEST.json").is_file():
        raise SystemExit("base MANIFEST.json missing")
    if output.exists():
        raise SystemExit(f"refusing existing output: {output}")
    output.mkdir(parents=True)
    copy_source(source / "task", output / "task", exclude_work=True)
    copy_source(base / "dependencies_snapshot", output / "dependencies_snapshot")
    copy_source(base / "source_snapshot", output / "source_snapshot")

    script_dir = output / "task/corrections/identity/r6/scripts"
    test_dir = output / "task/corrections/identity/r6/tests"
    for snap in (output / "source_snapshot").iterdir():
        original = script_dir / snap.name if (script_dir / snap.name).is_file() else test_dir / snap.name
        if original.is_file():
            shutil.copyfile(original, snap)
    shutil.copyfile(Path(__file__), output / "BUILD_SOURCE.py")

    changed: list[dict] = []
    diff: list[str] = []
    for path in sorted((output / "task").rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output).as_posix()
        previous = base / relative
        if previous.is_file() and sha(previous) == sha(path):
            continue
        changed.append({
            "relative": relative,
            "base_sha256": sha(previous) if previous.is_file() else None,
            "current_sha256": sha(path),
            "bytes": path.stat().st_size,
        })
        if path.suffix == ".py":
            old = previous.read_text(encoding="utf-8").splitlines(keepends=True) if previous.is_file() else []
            new = path.read_text(encoding="utf-8").splitlines(keepends=True)
            diff.extend(difflib.unified_diff(old, new, fromfile=f"C11/{relative}",
                                             tofile=f"new/{relative}"))
    (output / "DIFF.patch").write_text("".join(diff), encoding="utf-8")
    (output / "SOURCE_CHANGES.json").write_text(json.dumps(changed, indent=2), encoding="utf-8")

    now = datetime.now(UTC).isoformat()
    base_sha = sha(base / "MANIFEST.json")
    report = (
        f"# MotionForge2D G1 candidate: {output.name}\n\n"
        f"Trạng thái: CODE_DONE / PENDING_FROZEN_REPLAY. Chưa có verdict G1; "
        f"Media/GPU/render vẫn bị chặn.\n\n"
        f"Base: {base.name}, manifest SHA-256: {base_sha}.\n"
        f"Đã sửa {len(changed)} file nguồn trong bản sao Codex; "
        f"chi tiết và preimage/postimage ở SOURCE_CHANGES.json, DIFF.patch.\n\n"
        "Q05 hiện chạy lại test thật bằng pytest/JUnit, so node IDs/exit với receipt và hash "
        "test; Q07 yêu cầu dependency record v4 cho từng shot, so hash và chạy lại validator. "
        "Adapter không phát TASK_SUBMITTED khi gate từ chối.\n\n"
        "Bản này cần chạy guard độc lập trên candidate copy trước khi nêu số test PASS. "
        "Không dùng kết quả test của owner worktree thay cho guard.\n"
    )
    (output / "REPORT_VI.md").write_text(report, encoding="utf-8")
    checkpoint = {"candidate": output.name, "status": "CODE_DONE_PENDING_FROZEN_REPLAY",
                  "created_utc": now, "base_manifest_sha256": base_sha,
                  "source_changes": len(changed), "media_status": "BLOCKED_DEPENDENCY"}
    (output / "CHECKPOINT.json").write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    files = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json":
            files.append({"relative": path.relative_to(output).as_posix(),
                          "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {"schema": 1, "submission_id": output.name, "gate": "G1",
                "status": "PENDING_FROZEN_REPLAY", "created_utc": now,
                "base_manifest_sha256": base_sha, "total_files": len(files), "files": files}
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"candidate": str(output), "files": len(files),
                      "source_changes": len(changed), "manifest_sha256": sha(output / "MANIFEST.json")}))


if __name__ == "__main__":
    main()
