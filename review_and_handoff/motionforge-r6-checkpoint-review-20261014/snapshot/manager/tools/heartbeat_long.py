#!/usr/bin/env python
"""Long-scope heartbeat monitor v2 (Manager-owned, MF-DEMO-LONG-01).

Patched 2026-10-07 (context-recovery packet §4):
  * receipt resolved at RUN/manager/LONG01_receipt_*.json via the DISPATCH LEDGER
    invocation (v1 joined "manager" onto the already-manager dir -> manager/manager
    and had no invocation match; the resolved path is recorded in each row).
  * process identity = PID + creation time + exe (wmic), NOT a bare pid (v1 read a
    recycled pid — conhost — as worker-alive), and never a machinewide exe count.
  * terminal rows carry launcher_pid (dispatcher v2) so spawned-child sets close on
    terminal; legacy v1 rows close by receipt-path match.
  * separate llm_worker_alive / render_worker_alive / controller_alive, machine
    outcome classification and pending_work. Query failure = UNKNOWN, never zero.
  * STOP file manager/HEARTBEAT_STOP exits the loop; --once for offline fixtures.

Writes manager/HEARTBEAT.jsonl every INTERVAL s; stall_8min is an audit trigger
only (it never kills anything).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import invocation_runtime as _ir  # noqa: E402

_ENV_RUN = os.environ.get("MF_RUN_ROOT")
if _ENV_RUN:
    RUN = os.path.abspath(_ENV_RUN)
    MANAGER = os.path.join(RUN, "manager")
else:
    MANAGER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # = RUN/manager
    RUN = os.path.dirname(MANAGER)
LEDGER = os.path.join(MANAGER, "DISPATCH_LEDGER.jsonl")
HB = os.path.join(MANAGER, "HEARTBEAT.jsonl")
STOP_FILE = os.path.join(MANAGER, "HEARTBEAT_STOP")
D = os.path.join(RUN, "tasks", "MF-DEMO-LONG-01")
INTERVAL = 120
# POLICY 2026-10-06 (user: bo budget tu dat): no self-imposed stop gate.
STOP_AFTER_S = None


def utc():
    return datetime.now(timezone.utc).isoformat()


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return "ERR %s" % e


def read_ledger():
    rows = []
    if os.path.exists(LEDGER):
        for line in open(LEDGER, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def current_invocation(rows):
    """(dispatch_row|None, is_open, how). Current invocation = the LATEST dispatch
    row. Closed when a terminal row matches its launcher_pid (v2) OR its receipt
    basename (covers legacy v1 spelling differences and historical rows whose
    terminal used a different path spelling). Older dispatches are history —
    their receipts/logs are superseded."""
    closed_lp = {r.get("launcher_pid") for r in rows
                 if r.get("action") == "terminal" and r.get("launcher_pid") is not None}
    closed_rcb = {os.path.basename(str(r.get("receipt") or "")).lower()
                  for r in rows if r.get("action") == "terminal"}
    last = None
    for r in rows:
        if r.get("action") == "dispatch":
            last = r
    if last is None:
        return None, False, "no dispatch rows"
    lp = last.get("launcher_pid")
    rcb = os.path.basename(str(last.get("receipt") or "")).lower()
    if lp in closed_lp:
        return last, False, "closed by launcher_pid terminal"
    if rcb and rcb in closed_rcb:
        return last, False, "closed by receipt-basename terminal"
    return last, True, "no closing terminal row"


def spawned_children(rows, launcher_pid):
    """child_spawned rows for launcher_pid (identity fields kept for verification)."""
    return [r for r in rows
            if r.get("action") == "child_spawned" and r.get("launcher_pid") == launcher_pid]


def latest_receipt_for(disp_row):
    """Receipt PATH for a dispatch row: the row's own receipt if it exists, else the
    newest LONG01_receipt_*.json in RUN/manager (NEVER manager/manager — v1 bug)."""
    if disp_row and disp_row.get("receipt"):
        p = disp_row["receipt"]
        if os.path.exists(p):
            return p
    cands = []
    if os.path.isdir(MANAGER):
        cands = [os.path.join(MANAGER, f) for f in os.listdir(MANAGER)
                 if f.startswith("LONG01_receipt") and f.endswith(".json")]
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return cands[0] if cands else None


def proc_facts(pid):
    """(name, created, cmdline) via psutil (R4 §4). {} if gone; None if the probe
    itself failed (caller must treat as UNKNOWN, not as dead)."""
    f = _ir.pid_facts(pid)
    if f is None:
        return None
    if not f:
        return {}
    return {"name": f.get("name", ""), "created": f.get("created", ""), "cmd": f.get("cmd", "")}


def identity_alive(pid, created=None, name=None):
    """True iff same pid AND same creation time (±2ms) AND (if given) same exe name.
    psutil-backed via invocation_runtime; None = probe UNKNOWN (never read as dead)."""
    return _ir.identity_alive(pid, created, name)


def newest_log():
    cands = sorted([p for p in os.listdir(D) if p.startswith("worker") and p.endswith(".log")],
                   key=lambda n: os.path.getmtime(os.path.join(D, n)), reverse=True) if os.path.isdir(D) else []
    return os.path.join(D, cands[0]) if cands else os.path.join(D, "worker.log")


def newest_receipt():
    """Newest receipt inside RUN/manager (explicitly the manager dir; v1 double-joined)."""
    return latest_receipt_for(None)


def tree_files(root):
    out = {}
    if not os.path.isdir(root):
        return out
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                out[os.path.relpath(p, root)] = os.path.getsize(p)
            except OSError:
                pass
    return out


def read_tail(path, nbytes=200_000):
    try:
        with open(path, "rb") as fh:
            try:
                fh.seek(-nbytes, os.SEEK_END)
            except OSError:
                pass
            return fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


# Machine-readable terminal classes (packet §4). exit0 + an error marker is NOT
# 'completed' (W2r precedent: exit0 with CONTEXT_EXHAUSTED). All markers lowercase;
# matched against tail.lower() — CLI logs vary in capitalisation.
OUTCOME_MARKERS = (
    ("CONTEXT_EXHAUSTED", ("max compression attempts", "context length exceeded")),
    ("OUTPUT_TRUNCATED", ("truncated due to output length",)),
    ("QUOTA_BLOCKED", ("gousagelimiterror", "usagelimit", "insufficient quota", "quota exceeded")),
    ("USER_STOP", ("user_stop",)),
    ("SELF_REVIEW_PASS_PENDING_CODEX", ("self_review_pass_pending_codex",)),
    ("CONTINUE_REQUIRED", ("continue_required",)),
    ("ITERATION_YIELD", ("maximum tool-calling iterations",)),
)


def classify_outcome(receipt, log_path):
    """Class from receipt + log tail. Never trusts exit code alone.
    LATEST occurrence wins (a plan line mentioning a status token must not beat
    the real terminal line). Ties break by marker-list order."""
    if receipt is None:
        return {"class": "NO_RECEIPT", "detail": "invocation open or receipt unreadable"}
    tail = (read_tail(log_path) if log_path else "").lower()
    best = None  # (pos, order_idx, cls, marker)
    for idx, (cls, markers) in enumerate(OUTCOME_MARKERS):
        for m in markers:
            p = tail.rfind(m)
            if p < 0:
                continue
            if best is None or p > best[0] or (p == best[0] and idx < best[1]):
                best = (p, idx, cls, m)
    if best is not None:
        return {"class": best[2], "marker": best[3], "match_pos": best[0],
                "exit_code": receipt.get("exit_code"), "not_completed": True}
    rc = receipt.get("exit_code")
    if rc == 0:
        return {"class": "EXIT0_NO_KNOWN_MARKER", "exit_code": rc,
                "detail": "read log payload before trusting", "not_completed": None}
    return {"class": "EXIT_NONZERO", "exit_code": rc, "not_completed": True}


def effective_outcome(disp, receipt, log_path):
    """Structured terminal FIRST (R4 §4 + R5 §4.3): a terminal record is an authority
    ONLY when it is bound to THIS dispatch (immutable ledger row) and carries a known
    decision. A stale receipt, another invocation's record, or an unknown decision is
    NEVER accepted -> NEEDS_RECONCILIATION. Legacy prose stays reference-only.
    Self-contained on purpose: the review probe extracts this function alone."""
    if receipt is None:
        return {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                "error": "no receipt record for a closed invocation"}
    legacy = classify_outcome(receipt, log_path)
    tv = receipt.get("terminal_validation")
    if not isinstance(tv, dict):
        return {"class": "LEGACY_NO_STRUCTURED_TERMINAL", "source": "legacy_receipt (NOT authority)",
                "legacy_prose_class": legacy.get("class"), "exit_code": legacy.get("exit_code")}
    disp = disp or {}
    problems = []
    BIND_KEYS = ("invocation_id", "owner_sid", "run_id", "task_id", "revision")
    for k in BIND_KEYS:
        want = disp.get(k)
        if want in (None, ""):
            continue
        got = receipt.get(k)
        if got != want:
            problems.append("binding %s: receipt=%r dispatch=%r" % (k, got, want))
    want_p = disp.get("packet_file_sha256") or disp.get("packet_sha256")
    if want_p:
        got_p = receipt.get("packet_file_sha256") or receipt.get("packet_sha256")
        if got_p != want_p:
            problems.append("binding packet_sha256 mismatch")
    KNOWN = ("VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA", "PENDING_SAME_OWNER_CONTINUATION",
             "VERIFY_USER_STOP_AUTHORITY", "VERIFY_EXTERNAL_BLOCKER", "NEEDS_RECONCILIATION")
    dec = tv.get("decision")
    if dec not in KNOWN:
        problems.append("unknown decision: %r" % (dec,))
    res = tv.get("result")
    if dec != "NEEDS_RECONCILIATION":
        if not isinstance(res, dict):
            problems.append("structured terminal without result record")
        else:
            for k in BIND_KEYS:
                want = disp.get(k)
                if want in (None, ""):
                    continue
                got = res.get(k)
                if got != want:
                    problems.append("result %s: %r != %r" % (k, got, want))
    if problems:
        return {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                "errors": problems, "error": "; ".join(problems),
                "legacy_prose_class": legacy.get("class")}
    if dec == "NEEDS_RECONCILIATION":
        return {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                "error": tv.get("error"), "legacy_prose_class": legacy.get("class")}
    return {"class": (res or {}).get("status", "NEEDS_RECONCILIATION"), "source": "structured_terminal",
            "decision": dec, "legacy_prose_class": legacy.get("class")}


def revalidate_terminal(disp, receipt, log_path, llm_alive, rend_alive_):
    """R5 §4.3: re-validate the terminal against the IMMUTABLE dispatch row and the
    CURRENT artifact bytes (run/task/owner/invocation/packet/revision/allowed root/
    artifact hashes). Missing/truncated/duplicate-key/wrong-hash -> NEEDS_RECONCILIATION.
    Never trusts the cached terminal_validation."""
    try:
        if not disp:
            return {"decision": "NEEDS_RECONCILIATION", "error": "no dispatch row"}
        expected = _ir.expected_binding_from_row(disp)
        allowed_root = disp.get("allowed_root") or (receipt or {}).get("allowed_root")
        if not allowed_root:
            return {"decision": "NEEDS_RECONCILIATION", "error": "dispatch row without allowed_root"}
        import terminal_contract as _tcl
        root = Path(allowed_root)
        invocation_terminal = (llm_alive is False) and (rend_alive_ is False)
        return _tcl.validate_result(root / "evidence" / "terminal" / (expected["invocation_id"] + ".json"),
                                    _tcl.Binding(**expected), root,
                                    invocation_terminal=invocation_terminal,
                                    exit_code=(receipt or {}).get("exit_code"),
                                    infrastructure_error=_ir.log_has_infra_error(log_path or ""))
    except Exception as e:  # noqa: BLE001
        return {"decision": "NEEDS_RECONCILIATION", "error": "revalidate: %s: %s" % (type(e).__name__, e)}


def render_alive():
    """(bool|None, evidence). R5 §4.2: a non-empty Comfy queue OR any render-side runner
    process (native exe, or interpreter+script: ebsynth / video_blend / SAM2 / rerender /
    VACE / ...) means a render is live. None = UNKNOWN probe (never collapse to False)."""
    q, detail = _ir.probe_render_quiet()
    if q is True:
        return False, detail
    if q is False:
        return True, detail
    return None, detail


def pending_work():
    try:
        gate = json.loads(open(os.path.join(D, "state_gate.json"), encoding="utf-8").read())
    except Exception:  # noqa: BLE001
        gate = {}
    armed = gate.get("armed_range") or []
    try:
        plan = json.loads(open(os.path.join(D, "chunk_plan.json"), encoding="utf-8").read())["chunks"]
    except Exception:  # noqa: BLE001
        plan = []
    base = Path(D) / "output" / "chunks_r2"
    done, nxt = 0, None
    for c in plan:
        if (base / ("%s.mp4" % c["unit_id"])).exists():
            done += 1
        elif nxt is None:
            nxt = c["unit_id"]
    return {"gate": gate.get("gate"), "armed_last": (armed[-1] if armed else None),
            "chunks_done": done, "chunks_total": len(plan), "next_missing": nxt}


def main():
    once = "--once" in sys.argv[1:]
    started = time.time()
    prev_size, last_growth, prev_files = -1, time.time(), {}
    while True:
        if os.path.exists(STOP_FILE):
            print("heartbeat: STOP file present (%s) -> exit" % STOP_FILE)
            break
        rows = read_ledger()
        disp, inv_open, inv_how = current_invocation(rows)
        # --- llm worker + controller (identity-verified, never a bare pid) ---
        llm_alive, controller_alive = None, None
        llm_detail, ctl_detail = [], []
        if disp is not None:
            llm_alive, controller_alive = False, False
            if inv_open:
                lp = disp.get("launcher_pid")
                for kr in spawned_children(rows, lp):
                    st = identity_alive(kr.get("child_pid"), kr.get("child_created"), kr.get("child_name"))
                    if st:
                        llm_alive = True
                    llm_detail.append({"child_pid": kr.get("child_pid"), "created": kr.get("child_created"),
                                       "identity": ("ALIVE" if st else ("UNKNOWN" if st is None else "DEAD"))})
                lts = identity_alive(lp)
                if lts:
                    controller_alive = True
                ctl_detail.append({"launcher_pid": lp,
                                   "identity": ("ALIVE" if lts else ("UNKNOWN" if lts is None else "DEAD"))})
            else:
                llm_detail.append({"note": inv_how})
                ctl_detail.append({"note": inv_how})
        # --- render worker (Comfy queue / runner process) ---
        rend, rend_detail = render_alive()
        # --- receipt + log for the current invocation ---
        rpath = latest_receipt_for(disp)
        receipt = None
        if rpath and os.path.exists(rpath):
            try:
                receipt = json.loads(open(rpath, encoding="utf-8").read())
            except Exception:  # noqa: BLE001
                receipt = None
        log = (disp or {}).get("log") or newest_log()
        if not os.path.isabs(log):
            log = os.path.join(RUN, log)
        size = os.path.getsize(log) if os.path.exists(log) else 0
        mtime = os.path.getmtime(log) if os.path.exists(log) else 0
        now = time.time()
        grew = size != prev_size
        if grew:
            last_growth = now
        files = tree_files(D)
        new_files = sorted(set(files) - set(prev_files))[:12]
        if inv_open:
            outcome = {"class": "INVOCATION_OPEN"}
        else:
            outcome = effective_outcome(disp, receipt, log)
            if outcome.get("source") == "structured_terminal":
                rv = revalidate_terminal(disp, receipt, log, llm_alive, rend)
                if rv.get("decision") == "NEEDS_RECONCILIATION":
                    outcome = {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                               "error": rv.get("error"), "cached_class": outcome.get("class"),
                               "legacy_prose_class": outcome.get("legacy_prose_class")}
                elif outcome.get("decision") is not None and rv.get("decision") != outcome.get("decision"):
                    outcome = {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                               "error": "revalidation decision mismatch: %s vs %s" % (outcome.get("decision"), rv.get("decision")),
                               "cached_class": outcome.get("class")}
                else:
                    outcome["revalidated"] = True
        row = {
            "at_utc": utc(), "elapsed_s": int(now - started),
            "invocation": {"launcher_pid": (disp or {}).get("launcher_pid"), "receipt": rpath,
                           "log": log, "round": (disp or {}).get("round"),
                           "open": inv_open, "how": inv_how},
            "llm_worker_alive": llm_alive, "llm_detail": llm_detail,
            "render_worker_alive": rend, "render_detail": rend_detail,
            "controller_alive": controller_alive, "controller_detail": ctl_detail,
            "outcome": outcome,
            "pending_work": pending_work(),
            "watching_log": os.path.basename(log), "log_bytes": size,
            "log_mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime)) if mtime else None,
            "log_grew": grew, "sec_since_growth": int(now - last_growth),
            "stall_8min": (now - last_growth) > 480,
            "files_in_D": len(files), "new_files": new_files,
            "gpu": sh("nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits"),
            "port_listen": sh('netstat -ano | findstr "LISTENING" | findstr ":8188 :8321"'),
            "receipt_exit_code": (receipt or {}).get("exit_code", "<none>"),
            "receipt_timed_out": (receipt or {}).get("timed_out", "<none>"),
            "controller_lock": _ir.controller_status(),
            "leases": _ir.leases_status(),
        }
        with open(HB, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        prev_size, prev_files = size, files
        print("tick", row["at_utc"], "llm", llm_alive, "render", rend, "ctl", controller_alive,
              "outcome", outcome.get("class"), "log", size, "gpu", row["gpu"], flush=True)
        if once:
            break
        time.sleep(INTERVAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
