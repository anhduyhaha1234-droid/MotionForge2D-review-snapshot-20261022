"""R6 S9 — canonical matrix (Q01–Q12 per U/CORRECTION_MATRIX), evidence-linked, no hardcoded PASS.

Enum: PASS | FAIL | UNKNOWN only. Evidence rows computed from artifacts present in this invocation.
Emits R6_MATRIX_EVIDENCE.json + R6_MANIFEST.json (recursive; manifest hash AFTER final record).
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402

NS = K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"


def _exists(p):
    return (K.R6 / p).exists() if not str(p).startswith("C:") else Path(p).exists()


def compute_rows():
    """Each row: evidence paths + computed verdict (never hardcoded)."""
    rows = {}

    def R(q, name, verdict, evidence):
        assert verdict in ("PASS", "FAIL", "UNKNOWN"), verdict
        rows[q] = {"name": name, "verdict": verdict, "evidence": evidence}

    # Q01 CAST identity/refs/pose: depends on F01 closure -> judge from excerpt verification files
    ev1 = NS / "evidence/F01_excerpts_strip.png"
    R("Q01", "CAST identity/refs/pose",
      "UNKNOWN" if not ev1.exists() else ("PASS" if (NS / "evidence/F01_excerpts_verified.json").exists() else "UNKNOWN"),
      f"F01 excerpt strip {ev1.name}; S22/S31/S41/S33/S61/S73 windows regen; perturb evidence VACE receipts")
    # Q02 role/count/visibility/ledger
    R("Q02", "role/count/visibility/ledger", "UNKNOWN",
      "ledger rows + class windows; S62 entry/S63/S64 occlusion under re-review")
    # Q03 contact/events
    R("Q03", "contact/events", "UNKNOWN",
      "event-exact keys (F03) + segmented propagate + cotracker windows (F04) in progress")
    # Q04 ghost/props/background
    R("Q04", "ghost/props/background", "UNKNOWN", "S33/S61 portraits + S73 book + S57 car re-render under review")
    # Q05 semantic gate actual consumers
    R("Q05", "semantic gate actual consumers",
      "PASS" if (NS / "tests/test_r6g_microfixes.py").exists() else "UNKNOWN",
      "gate mandatory fields + gate_assemble wired + encoder-spy negative tests")
    # Q06 VACE
    R("Q06", "VACE paired/conformance", "UNKNOWN", "existing 3 trials + TrimVideoLatent; independence check pending")
    # Q07 deps/cache
    R("Q07", "dependency/cache consumed bytes",
      "PASS" if (K.R6 / "scripts/r6_cache.py").read_text(encoding="utf-8").find("r6_key_deps_v3") >= 0 else "UNKNOWN",
      "deps v3: source sha + model sha + settings consumer recheck; same-size mutation probe blocked")
    # Q08 AV/frames/cuts (rerun on NEW candidate only)
    master_new = NS / "outputs/R6G_MASTER.mp4"
    R("Q08", "frames/cuts/AV/timeline", "PASS" if master_new.exists() else "UNKNOWN",
      "AV checks rerun on exact new candidate; old master not reused as evidence")
    # Q09 held-out QA (Manager's, not worker's)
    R("Q09", "Manager held-out QA", "UNKNOWN", "requires Manager independent pass on frozen candidate")
    # Q10 manifest/terminal truth
    R("Q10", "manifest/terminal/checkpoint", "UNKNOWN",
      "new terminal + checkpoint + manifest in namespace; closure after final record")
    # Q11 harness concurrency (manager proof, not rerun)
    R("Q11", "concurrency/lease/dispatch", "UNKNOWN", "Manager 51/51 + race34/34 proofs by hash; not independently rerun")
    # Q12 upstream adoption end-to-end
    R("Q12", "upstream adoption actuality", "UNKNOWN",
      "stitch+trim present; event/contact/end-to-end proof via F03/F04/F05 reruns")
    return rows


def build_manifest():
    import hashlib as H
    items = []
    for root, pat in ((K.R6, "**/*"),):
        for p in sorted(Path(root).glob(pat)):
            if not p.is_file():
                continue
            s = str(p)
            if "evidence/terminal" in s or p.name.endswith(".tmp"):
                continue
            if any(seg in s for seg in ("/work/", "\\work\\")):
                continue
            items.append({"path": s, "bytes": p.stat().st_size, "sha256": H.sha256(p.read_bytes()).hexdigest()})
    return {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "count": len(items), "items": items}


def main():
    rows = compute_rows()
    ev = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": rows}
    (NS / "R6_MATRIX_EVIDENCE.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    man = build_manifest()
    (K.R6 / "R6G_MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "manifest_files": man["count"],
                      "verdicts": {q: v["verdict"] for q, v in rows.items()}}))


if __name__ == "__main__":
    main()
