"""MF-V1-VIDEO14B wave-2 engine shutdown with proof (S8).

Stops ONLY the verified pids of this task's own serve_video14b.py chain,
leaf -> root, one pid at a time, with taskkill /PID <p> /F (never /T, never
killall/pkill).  Every pid is identity-checked from its own command line before
it is touched; a pid whose command line does not contain serve_video14b.py is
never stopped, so `hermes desktop`, `hermes serve`, the manager monitors and the
worker session itself cannot be collateral.

Writes into <out_dir>:
  wave2_pids_before_stop.txt   full python.exe table before
  wave2_pids_after_stop.txt    full python.exe table after
  wave2_netstat_after.txt      netstat -ano output after
  wave2_vram_after.txt         nvidia-smi memory.used after
  wave2_shutdown_evidence.json machine-readable record
  SHUTDOWN.md                  the human proof block

Usage:
  python w2_stop_engine.py <out_dir> [--dry-run]
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RT = Path(r"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b")
PS_DUMP = RT / "tools" / "w2_proc_dump.ps1"
EPOCH = RT / "instance_epoch.json"
ENGINE_MARK = "serve_video14b.py"
# wave B: the port is READ from the epoch the server itself wrote (this wave
# reserves 8310).  A hard-coded 8210 would probe -- and then mis-attribute -- a
# port this wave never listened on.
PORT = int(json.loads(EPOCH.read_text(encoding="utf-8"))["port"]) if EPOCH.is_file() else 8310
HOST = "127.0.0.1"


def sh(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.returncode, r.stdout, r.stderr
    except Exception as exc:  # noqa: BLE001
        return 999, "", f"{type(exc).__name__}: {exc}"


def dump_python(out_path: Path) -> list[dict]:
    sh(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS_DUMP),
        "-Filter", "python.exe", "-Out", str(out_path)])
    rows: list[dict] = []
    if not out_path.is_file():
        return rows
    text = out_path.read_text(encoding="utf-8-sig", errors="replace")
    for line in text.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 5:
            try:
                rows.append({"pid": int(parts[0]), "ppid": int(parts[1]), "name": parts[2],
                             "ws_mb": parts[3], "cmdline": parts[4]})
            except ValueError:
                continue
    return rows


def pid_alive(pid: int) -> bool:
    rc, out, _ = sh(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"])
    return rc == 0 and f'"{pid}"' in out


def connect_ex(host: str, port: int) -> int:
    s = socket.socket()
    s.settimeout(2.0)
    try:
        return s.connect_ex((host, port))
    finally:
        s.close()


def netstat_listeners(port: int) -> dict:
    rc, out, _ = sh(["netstat", "-ano"])
    rows = []
    for line in out.splitlines():
        if f":{port} " in line or line.rstrip().endswith(f":{port}"):
            rows.append(" ".join(line.split()))
    return {"returncode": rc, "lines": rows}


def vram() -> dict:
    rc, out, _ = sh(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                     "--format=csv,noheader,nounits"])
    used = total = None
    line = (out or "").strip().splitlines()[0] if (out or "").strip() else ""
    if line:
        nums = [int("".join(c for c in p if c.isdigit()) or 0) for p in line.split(",")]
        if len(nums) >= 2:
            used, total = nums[0], nums[1]
    return {"returncode": rc, "raw": (out or "").strip(), "used_mib": used, "total_mib": total}


def owner_of(cmdline: str) -> str:
    c = cmdline or ""
    low = c.lower()
    if "hermes" in low and ("serve --host" in low or "desktop" in low or " -z " in low):
        return "hermes"
    if "manager-tools" in low or "manager/tools" in low:
        return "manager-tool"
    if ENGINE_MARK in c:
        return "engine"
    return "other"


def build_chain(rows: list[dict], epoch_pid: int) -> list[dict]:
    """Verify identity from cmdline: epoch pid plus ancestors that are the SAME
    script, deepest (leaf) first.  Nothing else is ever included."""
    by_pid = {r["pid"]: r for r in rows}
    chain: list[dict] = []
    pid = epoch_pid
    hops = 0
    while pid and hops < 6:
        row = by_pid.get(pid)
        if row is None or ENGINE_MARK not in (row.get("cmdline") or ""):
            break
        chain.append(row)
        pid = row["ppid"]
        hops += 1
    return chain


def main() -> int:
    out_dir = Path(str(sys.argv[1]).replace("\\", "/"))
    dry = "--dry-run" in sys.argv
    out_dir.mkdir(parents=True, exist_ok=True)

    epoch = json.loads(EPOCH.read_text(encoding="utf-8")) if EPOCH.is_file() else {}
    epoch_pid = int(epoch.get("pid") or 0)
    instance_id = epoch.get("instance_id")

    before_path = out_dir / "wave2_pids_before_stop.txt"
    after_path = out_dir / "wave2_pids_after_stop.txt"

    rows_before = dump_python(before_path)
    listeners_before = netstat_listeners(PORT)
    vram_before = vram()
    cx_before = connect_ex(HOST, PORT)
    chain = build_chain(rows_before, epoch_pid)

    protected = sorted({r["pid"] for r in rows_before if owner_of(r.get("cmdline", "")) != "engine"})

    # ComfyUI's own source-backed unload, before the pids go away.
    free_result = {"status": None, "body": None}
    try:
        req = urllib.request.Request(
            f"http://{HOST}:{PORT}/free",
            data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            free_result = {"status": resp.status, "body": resp.read()[:200].decode(errors="replace")}
    except Exception as exc:  # noqa: BLE001
        free_result = {"status": "error", "body": f"{type(exc).__name__}: {exc}"}

    stop_log: list[dict] = []
    if not dry:
        for row in chain:  # already leaf -> root
            pid = row["pid"]
            if owner_of(row.get("cmdline", "")) != "engine":
                stop_log.append({"pid": pid, "action": "REFUSED_NOT_ENGINE"})
                continue
            rc, out, err = sh(["taskkill", "/PID", str(pid), "/F"])
            stop_log.append({"pid": pid, "argv": ["taskkill", "/PID", str(pid), "/F"],
                             "returncode": rc, "stdout": out.strip(), "stderr": err.strip()})
            time.sleep(0.4)
        deadline = time.time() + 40
        while time.time() < deadline:
            if not any(pid_alive(r["pid"]) for r in chain) and connect_ex(HOST, PORT) != 0:
                break
            time.sleep(1.0)

    rows_after = dump_python(after_path)
    listeners_after = netstat_listeners(PORT)
    (out_dir / "wave2_netstat_after.txt").write_text(
        "".join(l + "\n" for l in listeners_after["lines"]) or "(no line matching :{PORT})\n",
        encoding="utf-8")
    vram_after = vram()
    (out_dir / "wave2_vram_after.txt").write_text(
        f"raw: {vram_after['raw']}\nused_mib: {vram_after['used_mib']}\ntotal_mib: {vram_after['total_mib']}\n",
        encoding="utf-8")
    cx_after = connect_ex(HOST, PORT)

    pids_before = {r["pid"] for r in rows_before}
    pids_after = {r["pid"] for r in rows_after}
    removed = sorted(pids_before - pids_after)
    added = sorted(pids_after - pids_before)
    chain_pids = sorted(r["pid"] for r in chain)
    collateral = sorted(set(removed) - set(chain_pids))
    # Survivors are DERIVED from the live table, not hard-coded: a pid list frozen
    # from an earlier wave reports a healthy machine as damaged (and vice versa)
    # once the session ids move on.  Every non-engine python.exe is protected; the
    # hermes / manager-tool rows are the ones that MUST still be there afterwards.
    survivor_rows = {r["pid"]: {"owner": owner_of(r.get("cmdline", "")),
                                "cmdline": r.get("cmdline")}
                     for r in rows_before
                     if owner_of(r.get("cmdline", "")) in ("hermes", "manager-tool")}
    survivors = {str(p): {"expected": v["owner"], "alive": pid_alive(p)}
                 for p, v in survivor_rows.items()}
    survivors_survived = all(v["alive"] for v in survivors.values()) and bool(survivors)

    rec = {
        "artifact": "wave2_shutdown_evidence.json",
        "instance_epoch": epoch,
        "port": PORT,
        "connect_ex_before": cx_before,
        "connect_ex_after": cx_after,
        "port_closed": cx_after != 0,
        "listeners_before": listeners_before,
        "listeners_after": listeners_after,
        "vram_before": vram_before,
        "vram_after": vram_after,
        "comfy_free_response": free_result,
        "engine_chain_leaf_to_root": chain_pids,
        "engine_chain_rows": {str(r["pid"]): {"ppid": r["ppid"], "ws_mb": r["ws_mb"],
                                              "cmdline": r["cmdline"]} for r in chain},
        "stop_log": stop_log,
        "python_pids_before": sorted(pids_before),
        "python_pids_after": sorted(pids_after),
        "pids_removed": removed,
        "pids_added": added,
        "collateral_removed": collateral,
        "protected_before": protected,
        "hermes_survivors": survivors,
        "hermes_survivors_all_alive": survivors_survived,
        "survivor_cmdlines": {str(p): v["cmdline"] for p, v in survivor_rows.items()},
        "dry_run": dry,
    }
    (out_dir / "wave2_shutdown_evidence.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    sh_l = [
        "# SHUTDOWN — MF-V1-VIDEO14B wave 2 (S8 proof)", "",
        f"- engine instance_epoch: instance_id={instance_id} pid={epoch_pid} port={PORT}",
        f"- engine chain stopped leaf -> root (one pid at a time, taskkill /PID <p> /F, no /T): {chain_pids}",
        f"- stop log: {json.dumps(stop_log, ensure_ascii=False)}",
        f"- port {PORT} connect_ex BEFORE: {cx_before} (0 = open) ; AFTER: {cx_after} "
        f"({'CLOSED/REFUSED' if cx_after != 0 else 'STILL OPEN — INCIDENT'})",
        f"- listener lines before: {listeners_before['lines']}",
        f"- listener lines after : {listeners_after['lines'] or '[]'}",
        f"- ComfyUI /free (unload_models+free_memory) response: {json.dumps(free_result, ensure_ascii=False)}",
        f"- python.exe pid set BEFORE: {sorted(pids_before)}",
        f"- python.exe pid set AFTER : {sorted(pids_after)}",
        f"- pid-set diff removed: {removed}  (must equal the engine chain {chain_pids})",
        f"- pid-set diff ADDED  : {added}",
        f"- COLLATERAL (removed but not in the engine chain): {collateral} -> "
        f"{'ZERO COLLATERAL' if not collateral else 'COLLATERAL DAMAGE — INCIDENT'}",
        f"- VRAM before {vram_before['used_mib']} MiB / after {vram_after['used_mib']} MiB (total {vram_after['total_mib']} MiB)",
        f"- manager processes survived: "
        + "; ".join(f"{v['expected']} pid {p} alive={v['alive']}" for p, v in survivors.items()),
        f"- other non-engine python pids left untouched: {protected}",
        f"- verdict: {'SHUTDOWN_CONFIRMED' if (cx_after != 0 and not collateral and survivors_survived) else 'SHUTDOWN_UNPROVEN'}"
        f" (collateral={collateral or 'ZERO'}, hermes/manager survivors all alive={survivors_survived})",
        "",
    ]
    (out_dir / "SHUTDOWN.md").write_text("\n".join(sh_l), encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("connect_ex_after", "port_closed", "engine_chain_leaf_to_root",
                                          "pids_removed", "collateral_removed", "hermes_survivors",
                                          "hermes_survivors_all_alive", "listeners_after",
                                          "vram_before", "vram_after")}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
