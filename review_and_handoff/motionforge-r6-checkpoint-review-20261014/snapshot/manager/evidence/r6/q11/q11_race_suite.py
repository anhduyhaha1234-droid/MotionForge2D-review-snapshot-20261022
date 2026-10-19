# -*- coding: utf-8 -*-
"""R6 Q11 race suite — TRUE two-controller rendezvous at the contested
acquire/reserve, on ACTUAL patched consumers (dispatch_long / invocation_runtime /
terminal_contract). No Hermes/Comfy/renderer: DISPATCH_TEST=1 + python fake child.

Cases (all outputs under manager/evidence/r6/** only):
  R1..R3  RACE: two LIVE controller processes rendezvous at a wall-clock barrier
          immediately before acquire_controller_lock/reconcile/lease_reserve ->
          exactly ONE winner (rc0, spawns the only child) and one refusal (rc4).
          Bounded joins; full ledger row audit per round; lease/lock end-state checked.
  CONTROL_ORDERED  winner -> +1s -> loser (held-lock control; NOT race proof).
  SENTINEL  single dispatch after the races still succeeds (refusal not sticky).
  NEG_R5_IN_R6  an r5-result record cannot satisfy an r6 dispatch -> NEEDS_RECONCILIATION.
Exit 0 iff every row passes. Evidence: manager/evidence/r6/q11/Q11_R6_RACE_RESULTS.json
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

MG = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager")
RUN = MG.parent
EV6 = RUN / "manager" / "evidence" / "r6"
Q11 = EV6 / "q11"
Q11.mkdir(parents=True, exist_ok=True)
VENV = r"C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe"
T = Path(r"C:/Users/Admin/AppData/Local/Temp/mf_r6_q11_race")
if T.exists():
    shutil.rmtree(T)
(T / "_lib").mkdir(parents=True)
RES = []
sys.dont_write_bytecode = True

FAKE_CHILD = T / "_lib" / "r6_race_fake_child.py"
FAKE_CHILD.write_text(r'''# -*- coding: utf-8 -*-
import hashlib, json, os, re, sys
from pathlib import Path
argv = sys.argv[1:]
prompt = argv[2] if len(argv) > 2 else ""
def pick(pat, text=prompt):
    m = re.search(pat, text)
    return m.group(1) if m else None
inv = pick(r"Invocation ID:\s*(\S+)")
psha = pick(r"Packet SHA256:\s*([0-9a-f]{64})")
sid = argv[argv.index("--resume") + 1] if "--resume" in argv else None
root = Path(os.environ.get("FAKE_ALLOWED_ROOT", "."))
rev = os.environ.get("FAKE_REVISION", "r6")
mark = os.environ.get("FAKE_MARK")
if mark:
    Path(mark).write_text("R6_RACE_CHILD_BOOT %s" % rev)
print("[fake] boot inv=%s rev=%s" % (inv, rev))
rec = {"run_id": "20261005T1643Z-wan-long", "task_id": "MF-DEMO-LONG-01", "revision": rev,
       "owner_sid": sid or "new", "invocation_id": inv, "packet_sha256": psha,
       "schema_version": "1.0", "status": "CONTINUE_REQUIRED", "reason": "r6 race fixture",
       "remaining_work": ["fixture step"], "artifacts": [], "matrix": {}}
tdir = root / "evidence" / "terminal"
tdir.mkdir(parents=True, exist_ok=True)
tp = tdir / (inv + ".json")
tmp = tp.with_name(tp.name + ".tmp")
tmp.write_text(json.dumps(rec, indent=1), encoding="utf-8")
os.replace(tmp, tp)
print("[fake] terminal written: %s" % tp)
sys.exit(0)
''', encoding="utf-8")

WRAPPER = T / "_lib" / "r6_race_wrapper.py"
WRAPPER.write_text(r'''# -*- coding: utf-8 -*-
import os, runpy, sys, time
sys.dont_write_bytecode = True
barrier = float(os.environ["R6_BARRIER_EPOCH"])
while time.time() < barrier:
    time.sleep(0.002)
sys.path.insert(0, os.environ["R6_TOOLS"])
runpy.run_path(os.environ["R6_DISPATCH"], run_name="__main__")
''', encoding="utf-8")

PACKET = """# r6 race fixture packet
Invocation ID: {{INVOCATION_ID}}
Packet SHA256: {{PACKET_SHA256}}
Resume SID: 20261007_234033_cc0b6d
"""

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def record(name, ok, detail=None):
    RES.append({"name": name, "pass": bool(ok), "detail": detail})
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", name, "" if ok else json.dumps(detail)[:300]))
    return ok

def ledger_rows(root: Path):
    p = root / "manager" / "DISPATCH_LEDGER.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def make_root(tag: str) -> Path:
    r = T / tag
    for d in ("manager/locks", "manager/leases", "r6/evidence/terminal", "logs", "receipts"):
        (r / d).mkdir(parents=True, exist_ok=True)
    (r / "packet.md").write_text(PACKET, encoding="utf-8")
    return r

def base_env(root: Path, side: str, barrier: float, extra=None):
    env = dict(os.environ)
    env.update({
        "MF_RUN_ROOT": str(root),
        "DISPATCH_TEST": "1",
        "DISPATCH_HERMES_ARGV_PREFIX": json.dumps([VENV, str(FAKE_CHILD)]),
        "FAKE_ALLOWED_ROOT": str(root / "r6"),
        "FAKE_MARK": str(root / ("spawned_%s.txt" % side)),
        "FAKE_MODE": "ok_continue",
        "FAKE_REVISION": "r6",
        "R6_BARRIER_EPOCH": "%r" % barrier,
        "R6_TOOLS": str(MG / "tools"),
        "R6_DISPATCH": str(MG / "tools" / "dispatch_long.py"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    if extra:
        env.update(extra)
    return env

def cmd_for(root: Path, side: str, inv: str, entry: Path):
    return [VENV, "-B", str(entry),
            str(root / "packet.md"), "MF-DEMO-LONG-01", ".",
            str(root / ("logs/%s.log" % side)), str(root / ("receipts/%s.json" % side)),
            "--invocation-id", inv, "--revision", "r6", "--allowed-root", str(root / "r6"),
            "--stall-kill-seconds", "6"]

def lease_state(root: Path, inv: str):
    p = root / "manager" / "leases" / ("gpu_lease.%s.json" % inv)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("status")

# ---------------- RACE rounds ----------------
for i in (1, 2, 3):
    tag = "race_r%d" % i
    root = make_root(tag)
    invW, invL = "R6-RACE-%d-W" % i, "R6-RACE-%d-L" % i
    barrier = time.time() + 4.0
    envW = base_env(root, "W", barrier)
    envL = base_env(root, "L", barrier)
    t0 = time.time()
    pW = subprocess.Popen(cmd_for(root, "W", invW, WRAPPER), env=envW, cwd=str(root),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pL = subprocess.Popen(cmd_for(root, "L", invL, WRAPPER), env=envL, cwd=str(root),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    oW, _ = pW.communicate(timeout=90)
    oL, _ = pL.communicate(timeout=90)
    wall = time.time() - t0
    rcW, rcL = pW.returncode, pL.returncode
    winner, loser = ("W", envW) if rcW == 0 else ("L", envL)
    invWin, invLose = (invW, invL) if winner == "W" else (invL, invW)
    rows = ledger_rows(root)
    n_disp = sum(1 for r in rows if r.get("action") == "dispatch")
    n_child = sum(1 for r in rows if r.get("action") == "child_spawned")
    n_ref = sum(1 for r in rows if r.get("action") == "dispatch_refused" and r.get("reason") == "controller_locked")
    markW = (root / "spawned_W.txt").exists()
    markL = (root / "spawned_L.txt").exists()
    term = sorted(p.name for p in (root / "r6" / "evidence" / "terminal").glob("*.json"))
    recp = root / "receipts" / ("%s.json" % winner)
    receipt = json.loads(recp.read_text(encoding="utf-8")) if recp.exists() else {}
    lock_meta = json.loads((root / "manager" / "locks" / "controller.lock.meta.json").read_text(encoding="utf-8"))
    det = {"pass_rc": [rcW, rcL], "wall_s": round(wall, 1), "refusals": n_ref, "children": n_child,
           "dispatches": n_disp, "markers": [markW, markL], "terminal_records": term,
           "lease_W": lease_state(root, invW), "lease_L": lease_state(root, invL),
           "lock_released": lock_meta.get("released_utc"), "loser_stdout_head": (oL if winner == "W" else oW)[:200],
           "ledger_rows": rows}
    ok = record("R%d.one_winner_rc" % i, sorted([rcW, rcL]) == [0, 4], det)
    ok &= record("R%d.loser_lock_msg" % i, "controller lock held" in det["loser_stdout_head"], det["loser_stdout_head"])
    ok &= record("R%d.one_child" % i, n_child == 1 and (markW != markL), {"n_child": n_child, "markers": det["markers"]})
    ok &= record("R%d.one_refusal" % i, n_ref == 1 and n_disp == 1 and n_child == 1 and len(rows) == 4,
                 {"n_ref": n_ref, "n_disp": n_disp, "n_child": n_child, "rows": len(rows)})
    ok &= record("R%d.winner_continue" % i,
                 receipt.get("outcome_class") == "CONTINUE_REQUIRED"
                 and (receipt.get("terminal_validation") or {}).get("decision") == "PENDING_SAME_OWNER_CONTINUATION",
                 {"outcome": receipt.get("outcome_class"), "decision": (receipt.get("terminal_validation") or {}).get("decision")})
    ok &= record("R%d.exactly_one_terminal" % i, term == ["%s.json" % invWin], term)
    ok &= record("R%d.lease_endstate" % i, lease_state(root, invWin) == "RELEASED" and lease_state(root, invLose) is None,
                 {"win": lease_state(root, invWin), "lose": lease_state(root, invLose)})
    ok &= record("R%d.lock_released" % i, bool(lock_meta.get("released_utc")), lock_meta.get("released_utc"))
    ok &= record("R%d.bounded_join" % i, wall < 90, wall)

# ---------------- CONTROL: ordered held-lock (NOT race proof) ----------------
rootC = make_root("control_ordered")
invCW, invCL = "R6-CTRL-W", "R6-CTRL-L"
envCW = base_env(rootC, "W", 0.0)
envCL = base_env(rootC, "L", 0.0)
pW = subprocess.Popen(cmd_for(rootC, "W", invCW, WRAPPER), env=envCW, cwd=str(rootC),
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1.0)
pL = subprocess.run(cmd_for(rootC, "L", invCL, WRAPPER), env=envCL, cwd=str(rootC),
                    capture_output=True, text=True, timeout=90)
oW, _ = pW.communicate(timeout=90)
rowsC = ledger_rows(rootC)
okC = record("CONTROL.ordered_winner_rc0", pW.returncode == 0, pW.returncode)
okC &= record("CONTROL.ordered_loser_rc4", pL.returncode == 4, pL.returncode)
okC &= record("CONTROL.ordered_one_child",
              sum(1 for r in rowsC if r.get("action") == "child_spawned") == 1,
              [r.get("action") for r in rowsC])
record("CONTROL.label", True, "ordered held-lock control; NOT used as race proof")

# ---------------- SENTINEL: not sticky ----------------
rootS = make_root("sentinel")
invS = "R6-SENT"
envS = base_env(rootS, "W", 0.0)
pS = subprocess.run(cmd_for(rootS, "W", invS, WRAPPER), env=envS, cwd=str(rootS),
                    capture_output=True, text=True, timeout=90)
recS = json.loads((rootS / "receipts" / "W.json").read_text(encoding="utf-8"))
record("SENTINEL.rc0_continue", pS.returncode == 0 and recS.get("outcome_class") == "CONTINUE_REQUIRED",
       {"rc": pS.returncode, "outcome": recS.get("outcome_class")})

# ---------------- NEG: r5 result cannot satisfy an r6 dispatch ----------------
rootN = make_root("neg_r5_in_r6")
invN = "R6-NEG"
envN = base_env(rootN, "W", 0.0, {"FAKE_REVISION": "r5"})
pN = subprocess.run(cmd_for(rootN, "W", invN, WRAPPER), env=envN, cwd=str(rootN),
                    capture_output=True, text=True, timeout=90)
recN = json.loads((rootN / "receipts" / "W.json").read_text(encoding="utf-8"))
record("NEG.r5_result_vs_r6_dispatch",
       pN.returncode == 0 and recN.get("outcome_class") == "NEEDS_RECONCILIATION"
       and (recN.get("terminal_validation") or {}).get("decision") == "NEEDS_RECONCILIATION",
       {"rc": pN.returncode, "outcome": recN.get("outcome_class"),
        "err": str((recN.get("terminal_validation") or {}).get("error"))[:140]})

# ---------------- No stray children ----------------
try:
    import psutil
    stray = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        cl = " ".join(p.info["cmdline"] or [])
        if "r6_race_fake_child" in cl and str(T) in cl:
            stray.append(p.info["pid"])
    record("FINAL.no_stray_children", not stray, stray)
except Exception as e:  # noqa: BLE001
    record("FINAL.no_stray_children", False, {"psutil_error": str(e)})

passed = sum(1 for r in RES if r["pass"])
report = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "suite": "r6_q11_race", "passed": passed, "total": len(RES),
          "rows": RES,
          "provenance": {"dispatch_sha256": sha(MG / "tools/dispatch_long.py"),
                         "invocation_runtime_sha256": sha(MG / "tools/invocation_runtime.py"),
                         "terminal_contract_sha256": sha(MG / "tools/terminal_contract.py"),
                         "wrapper_sha256": sha(WRAPPER), "fake_child_sha256": sha(FAKE_CHILD)}}
out = Q11 / "Q11_R6_RACE_RESULTS.json"
out.write_text(json.dumps(report, indent=1), encoding="utf-8")
print(json.dumps({"passed": passed, "total": len(RES), "evidence": str(out)}))
sys.exit(0 if passed == len(RES) else 1)
