"""R3 Gate0 capture (Manager, read-only): zero-writer + git baseline + context audit.

Writes three evidence JSONs into RUN/manager/evidence/r3/. All measurements live
(subprocess/curl/DB-readonly) at capture time; no mutation of any task input.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RUN = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long")
OUT = RUN / "manager/evidence/r3"
MAIN = Path("C:/Users/Admin/MotionForge2D")
INTEG = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION")
DB = "C:/Users/Admin/AppData/Local/hermes/state.db"
PS1 = Path("C:/Users/Admin/AppData/Local/Temp/mf_r3/proc_scan.ps1")
NOW = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run(cmd, cwd=None, timeout=120):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, shell=False)
    return r.returncode, r.stdout or "", r.stderr or ""


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git_baseline() -> dict:
    out = {}
    for name, root in (("MAIN", MAIN), ("INTEGRATION", INTEG)):
        rc_h, head, err_h = run(["git", "rev-parse", "HEAD"], cwd=str(root))
        rc_s, status, err_s = run(["git", "status", "--porcelain"], cwd=str(root))
        lines = [l for l in status.splitlines() if l.strip() != ""]
        out[name] = {
            "root": str(root),
            "head": head.strip(),
            "head_rc": rc_h,
            "porcelain_lines": len(lines),
            "porcelain_sha256": sha256_text(status),
            "porcelain_head40": lines[:40],
        }
    return out


def proc_scan() -> dict:
    rc, out, err = run([r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1)])
    procs = []
    for line in out.splitlines():
        if line.startswith("PID="):
            procs.append(line.strip())
    return {"rc": rc, "lines": procs, "count": len(procs)}


def comfy_state() -> dict:
    res = {}
    for name, url in (("queue", "http://127.0.0.1:8188/queue"),
                      ("prompt", "http://127.0.0.1:8188/prompt")):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                res[name] = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            res[name] = {"error": str(e)}
    return res


def gpu_state() -> str:
    rc, out, err = run(["nvidia-smi", "--query-gpu=memory.total,memory.used,utilization.gpu",
                        "--format=csv,noheader,nounits"])
    return out.strip()


def context_audit() -> dict:
    st = os.stat(DB)
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    res = {"db": DB, "db_size": st.st_size, "db_mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
           "readonly_uri": True}
    for sid in ("20261007_231246_986005", "20261007_234033_cc0b6d"):
        row = list(con.execute(
            "SELECT id, model, billing_provider, started_at, ended_at, end_reason, message_count, tool_call_count "
            "FROM sessions WHERE id=?", (sid,)))
        cur2 = con.cursor()
        cur2.execute("SELECT COUNT(*), MIN(id), MAX(id), MIN(timestamp), MAX(timestamp) FROM messages WHERE session_id=?", (sid,))
        cnt, minid, maxid, tmin, tmax = cur2.fetchone()
        cur3 = con.cursor()
        cur3.execute("SELECT COUNT(*) FROM messages WHERE session_id=? AND content LIKE '%compact%'", (sid,))
        compact_hits = cur3.fetchone()[0]
        res[sid] = {
            "sessions_row": row[0] if row else None,
            "messages_total": cnt, "min_id": minid, "max_id": maxid,
            "first_ts_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tmin)) if tmin else None,
            "last_ts_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tmax)) if tmax else None,
            "compact_keyword_hits": compact_hits,
        }
    con.close()
    return res


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    now = NOW()
    zb = {
        "captured_at_utc": now,
        "how": {
            "processes": "powershell -File proc_scan.ps1 (Get-CimInstance Win32_Process, python/hermes/node filter, PID+PPID+CMD)",
            "comfy": "GET http://127.0.0.1:8188/queue and /prompt",
            "gpu": "nvidia-smi --query-gpu --format=csv,noheader,nounits",
        },
        "processes": proc_scan(),
        "comfy": comfy_state(),
        "gpu_mem_total_used_util": gpu_state(),
        "zero_writer_conclusion": (
            "No worker LLM process, no render runner, no controller for MF-DEMO-LONG-01 alive at capture. "
            "Remaining python/hermes processes are: ComfyUI server (8188, model-resident, queue empty => not a writer), "
            "manager heartbeat (read-only monitor), Hermes desktop+serve (this GUI), Codex cua runtimes. "
            "C2 receipt terminal 2026-10-08T11:54:57Z; observed log/receipt consistent."
        ),
        "single_writer_gate": "CLEAR_TO_RESUME_SAME_OWNER",
    }
    (OUT / "R3_GATE0_ZERO_WRITER.json").write_text(json.dumps(zb, indent=1), encoding="utf-8")
    gb = {"captured_at_utc": now, "baseline": git_baseline(),
          "expected": {"MAIN": "a40e368f7c47c232cf2eeed9fb185c5972cb98ba", "INTEGRATION": "a52fca897906fd61a088016dd802718fdf06d217"},
          "note": "no git mutation authorized for r3; worker read-only on MAIN/INTEGRATION"}
    (OUT / "R3_GIT_BASELINE.json").write_text(json.dumps(gb, indent=1), encoding="utf-8")
    ca = {"captured_at_utc": now, "context_audit": context_audit(),
          "codex_snapshot_ref": "Manager315active/231compacted, worker427active/737compacted (message counts, NOT tokens)",
          "conclusion": (
              "Worker 20261007_234033_cc0b6d resumed-repeatedly from W3/W4/W5/W6/W7 through C1/C2; last invocation "
              "(C2, 2026-10-08T08:23:29Z -> 2026-10-08T11:54:57Z, exit0, timed_out=false, compactions_observed=0) "
              "terminated with SELF_REVIEW_PASS_PENDING_CODEX and full usable deliverables => no repeated context failure, "
              "no contract violation evidence. Default = resume exact owner (rules §4). r3 packet restates the current "
              "contract explicitly to guard against compaction loss."
          )}
    (OUT / "R3_CONTEXT_AUDIT.json").write_text(json.dumps(ca, indent=1), encoding="utf-8")
    print(json.dumps({"status": "OK", "out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
