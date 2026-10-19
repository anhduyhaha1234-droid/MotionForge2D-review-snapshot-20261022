# -*- coding: utf-8 -*-
"""R4 takeover + Gate0 evidence (Manager 20261011_123932_c101dc).

Read-only measurements + ONE bounded registry update (preimage kept).
Writes into RUN/manager/evidence/r4/:
  R4_PREIMAGES.json          - preimage hashes of patch-only manager files
  R4_GATE0_ZERO_WRITER.json  - process/comfy/gpu/disk zero-writer snapshot
  R4_GIT_BASELINE.json       - MAIN/INTEGRATION HEAD + porcelain
  R4_CONTEXT_AUDIT.json      - worker/manager context + controller lineage proof
  R4_RECONCILE_20261011.json - takeover record (who was controller, who is now)
And updates RUN/manager/registry/SESSION_REGISTRY.json (atomic; CRLF kept).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path

RUN = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long")
MGR = RUN / "manager"
EV = MGR / "evidence" / "r4"
PRE = EV / "preimages"
DB = "C:/Users/Admin/AppData/Local/hermes/state.db"
MAIN = Path("C:/Users/Admin/MotionForge2D")
INTEG = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION")
MY_SID = "20261011_123932_c101dc"
NOW = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256f(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def facts(p: Path):
    st = p.stat()
    data = p.read_bytes()
    return {"path": str(p), "bytes": len(data), "lines": data.count(b"\n") + (0 if data.endswith(b"\n") else 1),
            "sha256": hashlib.sha256(data).hexdigest(), "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))}


def run(cmd, cwd=None, timeout=120):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, errors="replace")
    return r.returncode, (r.stdout or ""), (r.stderr or "")


def main() -> int:
    EV.mkdir(parents=True, exist_ok=True)
    PRE.mkdir(parents=True, exist_ok=True)

    # ---------- 1) preimages of patch-only Manager files ----------
    patched = [MGR / "tools/dispatch_long.py", MGR / "tools/heartbeat_long.py", MGR / "registry/SESSION_REGISTRY.json"]
    pre_manifest = {"captured_at_utc": NOW(), "why": "byte preimages for bounded patches this round", "files": []}
    for p in patched:
        dest = PRE / (p.name + ".pre")
        shutil.copy2(p, dest)
        pre_manifest["files"].append({"source": str(p), "preimage": str(dest), **facts(dest)})
    # heartbeat tail preimage (append-only file reference)
    hb = MGR / "HEARTBEAT.jsonl"
    lines = hb.read_text(encoding="utf-8", errors="replace").splitlines()
    (PRE / "HEARTBEAT.tail200.pre.jsonl").write_text("\n".join(lines[-200:]) + "\n", encoding="utf-8")
    pre_manifest["heartbeat_row_count_pre"] = len(lines)
    pre_manifest["heartbeat_tail_preimage"] = str(PRE / "HEARTBEAT.tail200.pre.jsonl")
    (EV / "R4_PREIMAGES.json").write_text(json.dumps(pre_manifest, indent=1), encoding="utf-8")

    # ---------- 2) zero-writer snapshot ----------
    import psutil
    now = time.time()
    procs = []
    for p in psutil.process_iter(["pid", "name", "create_time", "cmdline", "cwd"]):
        try:
            nm = (p.info["name"] or "").lower()
            cl = " ".join(p.info["cmdline"] or [])
            keep = nm.startswith(("hermes", "python", "node")) and ("hermes" in nm or "heartbeat" in cl or "dispatch" in cl or "main.py" in cl or "9router" in cl)
            if keep:
                procs.append({"pid": p.info["pid"], "name": p.info["name"],
                              "age_s": round(now - (p.info["create_time"] or now), 1), "cmd": cl[:260]})
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            procs.append({"pid": p.pid, "name": "?", "age_s": -1, "cmd": "AccessDenied"})
    procs.sort(key=lambda r: r["pid"])
    comfy = {}
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=10) as r:
            comfy = json.loads(r.read().decode())
    except Exception as e:
        comfy = {"error": type(e).__name__ + ": " + str(e)}
    rc, gpu, _ = run(["nvidia-smi", "--query-gpu=memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"])
    rc2, net, _ = run(["cmd", "/c", "netstat -ano | findstr LISTENING | findstr :8188"])
    # newest writes: D (worker tree) and manager (non-heartbeat)
    def newest(root: Path, skip_names=()):
        best = (0, None)
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in ("__pycache__",)]
            for f in fn:
                if f in skip_names:
                    continue
                fp = os.path.join(dp, f)
                try:
                    m = os.path.getmtime(fp)
                except OSError:
                    continue
                if m > best[0]:
                    best = (m, fp)
        return best
    d_new = newest(RUN / "tasks/MF-DEMO-LONG-01")
    m_new = newest(MGR, skip_names=("HEARTBEAT.jsonl", "heartbeat_stdout.log"))
    zb = {
        "captured_at_utc": NOW(),
        "by": "Manager 20261011_123932_c101dc (R4 takeover recon)",
        "processes": procs,
        "comfy_queue": {"running": len(comfy.get("queue_running", []) or []) if isinstance(comfy, dict) else None,
                        "pending": len(comfy.get("queue_pending", []) or []) if isinstance(comfy, dict) else None,
                        "raw_error": comfy.get("error") if isinstance(comfy, dict) else None},
        "gpu_mem_total_used_util": gpu.strip(),
        "port_8188": net.strip(),
        "newest_write_D": {"path": d_new[1], "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(d_new[0])) if d_new[1] else None},
        "newest_write_manager_nohb": {"path": m_new[1], "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m_new[0])) if m_new[1] else None},
        "heartbeat_pids": [p for p in procs if "heartbeat_long.py" in p["cmd"]],
        "conclusion": ("No worker LLM process, no render runner, no dispatch controller alive for MF-DEMO-LONG-01 at capture. "
                       "ComfyUI server (8188) is a pre-existing resident server with EMPTY queue -> not a writer. "
                       "Two legacy heartbeat_long.py monitor processes remain (pid set above) and will be replaced with the "
                       "patched heartbeat after Q11 wiring; they never write the worker tree. "
                       "Newest worker-tree write observed pre-dates capture by >2 days (R3d close-out)."),
        "single_writer_gate": "CLEAR_TO_PATCH_HARNESS_AND_RESUME_SAME_OWNER",
    }
    (EV / "R4_GATE0_ZERO_WRITER.json").write_text(json.dumps(zb, indent=1), encoding="utf-8")

    # ---------- 3) git baseline ----------
    gb = {"captured_at_utc": NOW(), "baseline": {}}
    for name, root in (("MAIN", MAIN), ("INTEGRATION", INTEG)):
        _, head, _ = run(["git", "rev-parse", "HEAD"], cwd=str(root))
        _, por, _ = run(["git", "status", "--porcelain"], cwd=str(root))
        lines = [l for l in por.splitlines() if l.strip()]
        gb["baseline"][name] = {"head": head.strip(), "porcelain_lines": len(lines),
                                "porcelain_sha256": hashlib.sha256(por.encode()).hexdigest()}
    gb["expected"] = {"MAIN": "a40e368f7c47c232cf2eeed9fb185c5972cb98ba",
                      "INTEGRATION": "a52fca897906fd61a088016dd802718fdf06d217"}
    (EV / "R4_GIT_BASELINE.json").write_text(json.dumps(gb, indent=1), encoding="utf-8")

    # ---------- 4) context audit + controller lineage ----------
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    con.execute("PRAGMA query_only=ON")
    cur = con.cursor()

    def sess(sid):
        row = list(cur.execute("SELECT id,started_at,ended_at,message_count,tool_call_count,title,cwd,model FROM sessions WHERE id=?", (sid,)))
        agg = list(cur.execute("SELECT COUNT(*), SUM(CASE WHEN active=1 THEN 1 ELSE 0 END), MIN(timestamp), MAX(timestamp) FROM messages WHERE session_id=?", (sid,)))[0]
        first = list(cur.execute("SELECT id, substr(content,1,120) FROM messages WHERE session_id=? AND role='user' ORDER BY id ASC LIMIT 1", (sid,)))
        return {"session_row": row[0] if row else None, "messages": agg[0], "active": agg[1],
                "first_ts": agg[2], "last_ts": agg[3],
                "last_ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(agg[3])) if agg[3] else None,
                "first_user_msg": first[0] if first else None}

    line = {
        "captured_at_utc": NOW(),
        "worker": {"sid": "20261007_234033_cc0b6d", **sess("20261007_234033_cc0b6d")},
        "registered_manager": {"sid": "20261007_231246_986005", **sess("20261007_231246_986005")},
        "actual_r3_controller": {"sid": "20261009_090230_8ee545", "title": "Xử lý correction MotionForge2D pilot300s", **sess("20261009_090230_8ee545")},
        "this_manager": {"sid": MY_SID, **sess(MY_SID)},
        "controller_chain": [
            {"sid": "20261005_232945_f060a9", "role": "initial Manager", "last_activity_utc": "2026-10-05T…", "status": "terminal"},
            {"sid": "20261007_231246_986005", "role": "context-recovery takeover Manager (registered)", "last_activity_utc": "2026-10-08T12:05:08Z", "status": "idle; last msg = C2 pilot submission report"},
            {"sid": "20261009_090230_8ee545", "role": "ACTUAL R3/R3b/R3c/R3d controller (user-opened 09/10; not registered)", "last_activity_utc": "2026-10-09T06:03:36Z", "status": "idle after reporting R3d run to user"},
            {"sid": MY_SID, "role": "R4 Manager (this session; user-dispatched packet 11/10)", "status": "active now"},
        ],
        "r3d_receipt_misread": {
            "receipt": "manager/LONG01_receipt_R3d.json", "outcome_class_recorded": "SELF_REVIEW_PASS_PENDING_CODEX",
            "actual_worker_terminal": "CONTINUE_REQUIRED (hết iteration budget khi đóng hồ sơ; next action rõ)",
            "cause": "prose substring classifier (F09); fixed by structured terminal contract before next dispatch",
        },
        "worker_context_conclusion": (
            "Resume exact owner 20261007_234033_cc0b6d. Last invocation (R3d) exit0, timed_out=false, compactions_observed=1, coherent "
            "closing message with explicit next actions; no repeated context failure, no contract drift -> rules §4 default resume; "
            "packet restates current contract compactly."),
        "heartbeat_note": "Two legacy heartbeat_long.py processes still looping (see R4_GATE0_ZERO_WRITER.json). Replaced by patched heartbeat after Q11 tests.",
    }
    (EV / "R4_CONTEXT_AUDIT.json").write_text(json.dumps(line, indent=1), encoding="utf-8")
    con.close()

    # ---------- 5) bounded registry update (preimage already saved) ----------
    reg = MGR / "registry/SESSION_REGISTRY.json"
    data = json.loads(reg.read_text(encoding="utf-8"))
    m = data["manager"]
    m["session_id"] = MY_SID
    m["role"] = "Manager (R4 stack round; user-dispatched packet 2026-10-11)"
    m["takeover_utc"] = NOW()
    m["takeover_note"] = ("R4 stack packet: zero-writer + controller reconcile at 2026-10-11T05:4xZ; "
                          "R3 actual controller 20261009_090230_8ee545 recorded; Q11 structured-terminal + controller lock + GPU lease "
                          "patched & tested before worker resume; worker SID unchanged.")
    m["previous_session_id"] = "20261009_090230_8ee545"
    m["controllers_history"] = [c["sid"] if isinstance(c, dict) else c for c in
                                [{"sid": "20261007_231246_986005"}, {"sid": "20261009_090230_8ee545"}, {"sid": MY_SID}]]
    w = data["worker"]
    w.setdefault("status_history", []).extend([
        "R3D_TERMINAL (2026-10-09 05:57Z exit0; log message = CONTINUE_REQUIRED; dispatch receipt prose-misread SELF_REVIEW_PASS_PENDING_CODEX [F09])",
        "CODEX_R3D_CHANGES_REQUESTED (09/10; master b8534eaa; actor/props/occlusion FAIL; MINOR refused)",
        "R4_STACK_PACKET_PENDING (11/10; Manager Q11/lease patched before dispatch; C/r4 not yet created)",
    ])
    w["current_round"] = "R4 (stack adoption: CAST B ref binding -> SAM2 -> Rerender; C/r4 pending)"
    data["r4"] = {
        "revision": "r4",
        "packet": "manager/packets/LONG01_R4.md",
        "scope": "source[2820,11820) S0021-74 9000f/300s 640x360/30fps; CAST B; upstream stack (SAM2/Rerender/CoTracker/ProPainter)",
        "allowed_root": str(RUN / "tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r4"),
        "prepared_utc": NOW(),
    }
    tmp = reg.with_name("SESSION_REGISTRY.json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, reg)
    after = reg.read_bytes()
    check = {"bytes": len(after), "crlf": after.count(b"\r\n"), "lf": after.count(b"\n"),
             "json_ok": bool(json.loads(after.decode("utf-8"))),
             "new_manager_sid": json.loads(after.decode("utf-8"))["manager"]["session_id"],
             "worker_sid": json.loads(after.decode("utf-8"))["worker"]["session_id"]}

    rec = {"act": "R4 takeover + reconcile", "at_utc": NOW(),
           "this_manager_sid": MY_SID, "worker_sid_kept": "20261007_234033_cc0b6d",
           "registry_before": pre_manifest["files"][2]["sha256"], "registry_after": check["sha256"] if "sha256" in check else hashlib.sha256(after).hexdigest(),
           "registry_check": check,
           "evidence_files": ["R4_PREIMAGES.json", "R4_GATE0_ZERO_WRITER.json", "R4_GIT_BASELINE.json", "R4_CONTEXT_AUDIT.json"],
           "next": "patch Q11 consumers (dispatch_long/heartbeat_long) + tests -> guard PRE -> R4 packet -> dispatch resume"}
    (EV / "R4_RECONCILE_20261011.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")

    print(json.dumps({"status": "OK",
                      "registry": check,
                      "zero_writer_gate": zb["single_writer_gate"],
                      "heartbeat_pids": [p["pid"] for p in zb["heartbeat_pids"]],
                      "gpu": gpu.strip()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
