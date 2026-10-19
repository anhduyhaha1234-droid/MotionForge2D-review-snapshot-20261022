"""R6d — write per-key semantic review records from the verified review results.

Sources of truth: receipts/R6_REVIEW_RESULTS.json (per-shot fail fids + notes) + addenda below
(S67/S69 verdicts captured this invocation). PASS keys of REVIEWED shots get a review record;
FAIL keys get FAIL records (blocking, repair queue); PENDING shots get NO records (gate blocks).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402

ADDENDA = {
    "S0067": {"fails": [1, 11, 21, 61, 111, 121, 122], "notes": "face-swap (bald/moustache) f1/11/21/61/122; f111 E2 full-body leak; f121 headset added; E2-visible-hair absent overall"},
    "S0069": {"fails": [11, 21, 51, 101, 118], "notes": "E2 outfit flicker (grey<->olive<->be) f11/21/51/101; f118 expression/hair change"},
}
PENDING = {"S0070", "S0071", "S0072", "S0073"}


def main():
    R = json.loads((K.R6 / "receipts/R6_REVIEW_RESULTS.json").read_text(encoding="utf-8"))
    shots = dict(R["shots"])
    shots.update({k: v for k, v in ADDENDA.items()})
    n_pass = n_fail = 0
    for sid, info in sorted(shots.items()):
        if sid in PENDING:
            print(f"{sid}: PENDING -> no records (gate blocks)")
            continue
        if "PENDING" in info.get("notes", "") and sid not in ADDENDA:
            print(f"{sid}: pending -> skip")
            continue
        fails = set(int(f) for f in info.get("fails", []))
        kd = K.R6 / "keys" / sid
        if not kd.exists():
            print(f"{sid}: no keys dir"); continue
        for kp in sorted(kd.glob("f_*_key.png")):
            fid = int(kp.name[2:6])
            name = f"{sid}_f{fid:04d}"
            if fid in fails:
                G.write_review("keys", name, kp, G.key_inputs_now(sid, fid, kp), {"shot": sid, "fid": fid},
                               "FAIL", f"{info.get('notes','')[:200]} | fid {fid} flagged; repair queue")
                n_fail += 1
            else:
                G.write_review("keys", name, kp, G.key_inputs_now(sid, fid, kp), {"shot": sid, "fid": fid},
                               "PASS", f"sheet reviewed (even-sampled, boundaries incl.); {info.get('notes','')[:160]}")
                n_pass += 1
        print(f"{sid}: {len(list(kd.glob('f_*_key.png')))} keys -> fails {len(fails)}")
    print(json.dumps({"pass": n_pass, "fail": n_fail}))


if __name__ == "__main__":
    main()
