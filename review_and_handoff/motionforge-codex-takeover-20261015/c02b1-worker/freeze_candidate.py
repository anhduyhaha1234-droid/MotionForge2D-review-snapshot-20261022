"""Freeze the exact C02B1 candidate and command receipts after validation."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


WORKER = Path(__file__).resolve().parent
PACKET = WORKER.parent
PREFLIGHT = json.loads((PACKET / "C02B1_PREFLIGHT.json").read_text(encoding="utf-8"))
COMMON = Path(next(row["path"] for row in PREFLIGHT["files"]
                   if row["relative"] == "scripts/r6_common.py"))
TEST = Path(PREFLIGHT["new_test"])
PY = Path("C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe")
ROOT_PROBE = PACKET / "root_probe_c02b1_staging.py"
CANDIDATE = WORKER / "candidate-01"
if CANDIDATE.exists():
    raise SystemExit("candidate-01 exists; freeze is single-use")
if not json.loads((WORKER / "AUDIT.json").read_text(encoding="utf-8"))["ok"]:
    raise SystemExit("scope audit did not pass")


def stats(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "lines": len(data.splitlines())}


commands = []
for name, argv, exit_code, log in [
    ("baseline_root_probe", [str(PY), str(ROOT_PROBE), "--source", str(COMMON),
                             "--out", str(WORKER / "baseline-probe")], 1,
     WORKER / "baseline-probe-stdout.json"),
    ("red_regression", [str(PY), "-m", "unittest", "discover", "-s", str(TEST.parent),
                        "-p", TEST.name, "-v"], 1, WORKER / "test_red_01.log"),
    ("new_full_module", [str(PY), "-m", "unittest", "discover", "-s", str(TEST.parent),
                        "-p", TEST.name, "-v"], 0, WORKER / "test_matrix_s1_s6.log"),
    ("post_root_probe", [str(PY), str(ROOT_PROBE), "--source", str(COMMON),
                         "--out", str(WORKER / "post-probe")], 0,
     WORKER / "post-probe-stdout.json"),
    ("c01_full_module", [str(PY), "-m", "unittest", "discover", "-s", str(TEST.parent),
                        "-p", "test_codex_c01_review_binding.py", "-v"], 0,
     WORKER / "test_c01_full.log"),
    ("c02a_full_module", [str(PY), "-m", "unittest", "discover", "-s", str(TEST.parent),
                         "-p", "test_codex_c02a_dependency_verification.py", "-v"], 0,
     WORKER / "test_c02a_full.log"),
    ("scope_audit", [str(PY), str(WORKER / "audit_candidate.py")], 0,
     WORKER / "AUDIT.json"),
]:
    commands.append({"name": name, "argv": argv, "exit_code": exit_code,
                     "raw_output": stats(log)})
(WORKER / "COMMANDS.json").write_text(json.dumps({
    "environment": {"PYTHONDONTWRITEBYTECODE": "1", "C02B1_WORKER_DIR": str(WORKER),
                    "C01_WORKER_DIR": str(WORKER), "C02A_WORKER_DIR": str(WORKER)},
    "commands": commands,
    "real_ffmpeg_commands": str(next(WORKER.glob("real-ffmpeg-*/RESULT.json"))),
}, indent=2), encoding="utf-8")

CANDIDATE.mkdir()
snapshots = {}
for label, live in (("r6_common.py", COMMON), ("test_codex_c02b1_staged_source.py", TEST)):
    snap = CANDIDATE / label
    shutil.copyfile(live, snap)
    if stats(live)["sha256"] != stats(snap)["sha256"]:
        raise SystemExit(f"snapshot mismatch: {label}")
    snapshots[label] = {"live": stats(live), "snapshot": stats(snap)}

checkpoint = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "status": "TASK_SUBMITTED_PENDING_ROOT_REVIEW",
    "task": "CODEX-C02B1-STAGED-SOURCE-FRESHNESS",
    "owner": "/root/motionforge_c02b1_coder", "model": "gpt-6-sol", "reasoning": "max",
    "fallback": "disabled", "allowlist": [str(COMMON), str(TEST), str(WORKER / "**")],
    "files": snapshots, "tests": {"new_module": "10/10", "root_probe": "7/7",
                                 "C01": "17/17", "C02A": "13/13"},
    "decisions": ["versioned exact provenance", "pending marker before frame publication",
                  "WIP1, no lock framework"],
    "blockers": [], "live_jobs": [], "remaining": ["independent root review"],
    "next_command": "Root independently verify candidate-01/MANIFEST.json, live hashes and focused probes",
}
(WORKER / "TERMINAL_CHECKPOINT.json").write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

evidence = [WORKER / name for name in (
    "preimages/r6_common.py", "common.diff", "AUDIT.json", "COMMANDS.json",
    "REPORT.md", "LOG.md", "TERMINAL_CHECKPOINT.json", "baseline-probe/RESULT.json",
    "post-probe/RESULT.json", "test_red_01.log", "test_matrix_s1_s6.log",
    "test_c01_full.log", "test_c02a_full.log")]
evidence += [next(WORKER.glob("real-ffmpeg-*/RESULT.json"))]
manifest = {"utc": datetime.now(timezone.utc).isoformat(),
            "task": checkpoint["task"], "status": checkpoint["status"],
            "files": snapshots, "evidence": [stats(path) for path in evidence],
            "protected_count": 27, "protected_drift": [], "no_live_jobs": True,
            "review_authority": "root only"}
manifest_path = CANDIDATE / "MANIFEST.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"manifest": stats(manifest_path), "files": snapshots,
                  "evidence_count": len(evidence)}, indent=2))
