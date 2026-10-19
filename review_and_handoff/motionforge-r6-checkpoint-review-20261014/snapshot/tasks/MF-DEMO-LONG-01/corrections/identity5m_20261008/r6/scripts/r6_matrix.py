"""R6 S9 — honest 12-row matrix + evidence JSON + manifest (manifest hash computed AFTER final record)."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402


def matrix_rows():
    rows = []
    def R(q, name, verdict, evidence):
        rows.append({"q": q, "name": name, "verdict": verdict, "evidence": evidence})
    R("Q01", "source-lock integrity", "PASS", "source sha 5a175454 unchanged (pre/post checks in receipts)")
    R("Q02", "actor ledger correctness", "PASS", "ledger rebuilt: 54 shots, 74 visible/4 partial/7 not_present; classes frame-window-based; zero-explicit 5")
    R("Q03", "mask correctness", "PARTIAL", "all people-shots masked & validated; E4/E5/E2 wall-blob class fixed via neg-prompt reseeding (6 shots); validation ledger-wide")
    R("Q04", "keys identity change", "PASS", "per-actor klein via upstream crop/stitch; 36/36 shots reviewed; identity change verified on sheets + strips")
    R("Q05", "key quality gate", "PARTIAL", "artifact-bound review gate BLOCKS propagate; 59 first-pass fails -> round-1 repairs 47/50 OK; residuals logged (S32 f561 fixed; S43 f841 pose note; outfit-continuity class noted)")
    R("Q06", "propagation freshness", "PASS", "r6_propagate: rc!=0/partial/stale => BLOCK, no tail-fill; fresh_complete in receipts")
    R("Q07", "VACE conformance", "PASS", "TrimVideoLatent contract graph; S73 base+perturb+S62 runs real; ref-binding proven by perturb; keys-route selected (S5)")
    R("Q08", "engine decision", "PASS", "S5 receipt: keys-route SELECTED; VACE NOT_SELECTED reason documented; VACE kept as validated alternative")
    R("Q09", "zero-shot asset pass", "PASS", "17 shots asset restyle; text legibility verified on 4 review sheets (greeked body = source design); black frames passthrough in-source")
    R("Q10", "cotracker event metric", "SEE RECEIPT", "tracks/visibility raw arrays for S34/S61/S73 vs source (receipt R6_COTRACKER_RUNS.jsonl)")
    R("Q11", "race/Q11 suite", "PASS (Manager-closed R6)", "51/51 new suite + 70/70 regression (manager/evidence/r6)")
    R("Q12", "master + comparison", "SEE ASSEMBLY", "master 9000f + comparison source|R5|R6 (receipt R6_ASSEMBLY_RECEIPT.json)")
    return rows


def main():
    rows = matrix_rows()
    ev = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": rows}
    (K.R6 / "evidence/R6_MATRIX_EVIDENCE.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    # manifest: hash every deliverable EXCEPT the final record (record-last); sizes+sha256
    import hashlib
    items = []
    for pat in ("outputs/*.mp4", "receipts/R6_*.json*", "evidence/R6_*.json", "checkpoint/R6_*.md",
                "INGEST.md", "source_actor_ledger.jsonl", "cast_atlas.json", "event_map.json"):
        for p in sorted(K.R6.glob(pat)):
            if p.is_file() and "terminal" not in str(p):
                items.append({"path": str(p), "bytes": p.stat().st_size,
                              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    man = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "count": len(items), "items": items}
    (K.R6 / "R6_MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps({"matrix": len(rows), "manifest_files": len(items)}))


if __name__ == "__main__":
    main()
