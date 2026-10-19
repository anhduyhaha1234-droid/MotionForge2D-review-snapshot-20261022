"""R6 terminal record writer (schema per packet §6; RECORD-LAST).

usage: python -B write_terminal_record_r6.py [--submitted] [--reason "..."]
"""
from __future__ import annotations
import hashlib, json, os, sys, time
from pathlib import Path

R6 = Path(__file__).resolve().parents[1]
EVID = R6 / "evidence"
TERM = EVID / "terminal"
TERM.mkdir(parents=True, exist_ok=True)
REC_PATH = TERM / "LONG01-R6-20261012T0810Z-2731.json"
MATRIX_PATH = EVID / "matrix.json"

BIND = {
    "schema_version": "1.0",
    "run_id": "20261005T1643Z-wan-long",
    "task_id": "MF-DEMO-LONG-01",
    "revision": "r6",
    "owner_sid": "20261007_234033_cc0b6d",
    "invocation_id": "LONG01-R6-20261012T0810Z-2731",
    "packet_sha256": "aa17a4d4185c6c1d76c9a6208284b9c31a38cbcab1b3ff96a371e542f2045933",
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    submitted = "--submitted" in sys.argv
    rows = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))["rows"] if MATRIX_PATH.exists() else {q: "UNKNOWN" for q in (f"Q{i:02d}" for i in range(1, 13))}
    if submitted:
        assert len(rows) == 12 and all(v == "PASS" for v in rows.values()), f"matrix not 12xPASS: {rows}"
        remaining, status = [], "TASK_SUBMITTED"
    else:
        status = "CONTINUE_REQUIRED"
        rp = R6 / "checkpoint/R6_REMAINING.json"
        remaining = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else []
    rec = dict(BIND)
    rec.update({"status": status,
                "reason": (sys.argv[sys.argv.index("--reason") + 1] if "--reason" in sys.argv else
                           "R6 invocation 1: gates restated; S1 ledger+binding done; S2 gates/cache+12/12 negative probes; S3 upstream crop+stitch path built and smoke-proven (E2E key S23 f1)."),
                "remaining_work": remaining, "artifacts": [], "matrix": rows})
    cand = [
        ("checkpoint", R6 / "checkpoint/R6_CHECKPOINT.md"),
        ("other", R6 / "checkpoint/R6_GATE_RESTATEMENT.md"),
        ("other", R6 / "source_actor_ledger.jsonl"),
        ("other", R6 / "cast_atlas.json"),
        ("other", R6 / "event_map.json"),
        ("other", R6 / "receipts/R6_LEDGER_VALIDATION.json"),
        ("other", R6 / "receipts/R6_NEGATIVE_PROBES.json"),
        ("other", R6 / "receipts/R6_SAM2_RUNS.jsonl"),
        ("other", R6 / "receipts/R6_KEYGEN_RUNS.jsonl"),
        ("other", R6 / "scripts/r6_common.py"),
        ("other", R6 / "scripts/r6_gate.py"),
        ("other", R6 / "scripts/r6_cache.py"),
        ("other", R6 / "scripts/r6_adapter.py"),
        ("other", R6 / "scripts/r6_graph.py"),
        ("other", R6 / "scripts/r6_upload.py"),
        ("other", R6 / "scripts/r6_sam2.py"),
        ("other", R6 / "scripts/r6_keygen.py"),
        ("other", R6 / "scripts/r6_probes.py"),
        ("other", R6 / "scripts/r6_ledger.py"),
        ("other", R6 / "evidence/R6_smoke_S23_f1.png"),
    ]
    allowed = R6.resolve()
    for kind, p in cand:
        if not p.exists():
            print("SKIP missing", p.name); continue
        pr = p.resolve()
        assert str(pr).startswith(str(allowed)) and str(pr) != str(REC_PATH.resolve())
        rec["artifacts"].append({"kind": kind, "path": str(pr), "sha256": sha(pr)})
    mfile = R6 / "outputs/IDENTITY5M_R6_MASTER.mp4"
    cfile = R6 / "outputs/IDENTITY5M_R6_COMPARISON.mp4"
    if mfile.exists():
        rec["artifacts"].append({"kind": "master", "path": str(mfile.resolve()), "sha256": sha(mfile)})
    if cfile.exists():
        rec["artifacts"].append({"kind": "comparison", "path": str(cfile.resolve()), "sha256": sha(cfile)})
    if MATRIX_PATH.exists():
        rec["artifacts"].append({"kind": "matrix", "path": str(MATRIX_PATH.resolve()), "sha256": sha(MATRIX_PATH)})
    man = R6 / "receipts/R6_MANIFEST.json"
    if man.exists():
        rec["artifacts"].append({"kind": "receipts", "path": str(man.resolve()), "sha256": sha(man)})
    tmp = REC_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, REC_PATH)
    print("RECORD_OK", REC_PATH.name, "| status", status, "| artifacts", len(rec["artifacts"]))
    try:
        sys.path.insert(0, str(R6 / "scripts"))
        import r6_gate as G
        if submitted:
            G.gate_submit(rec)
            print("SUBMIT GATE: PASS")
        else:
            print("SUBMIT GATE: n/a (CONTINUE_REQUIRED)")
    except Exception as e:
        print("SUBMIT GATE FAIL:", e)


if __name__ == "__main__":
    main()
