# -*- coding: utf-8 -*-
"""R4 structured-terminal consumer patches (Manager, 2026-10-11).

Applies byte-exact bounded replacements to dispatch_long.py + heartbeat_long.py:
  * dispatch: controller lock, invocation_id/revision/allowed-root binding, packet
    {{INVOCATION_ID}}/{{PACKET_SHA256}} substitution, GPU lease acquire/release
    (detached-safe), structured terminal validation (fail-closed), legacy prose
    outcome kept for reference only.
  * heartbeat: MF_RUN_ROOT isolation, psutil identity, structured outcome first
    (LEGACY_NO_STRUCTURED_TERMINAL for old receipts), controller-lock + lease rows.
Every anchor must occur EXACTLY once; preimages live in evidence/r4/preimages/.
Writes before/after facts + unified diffs to evidence/r4/diffs/.
"""
import difflib
import hashlib
import json
import os
import py_compile
import time
from pathlib import Path

TO = Path(__file__).resolve().parent
RUN = TO.parents[1]
EV = RUN / "manager" / "evidence" / "r4"
DIFF = EV / "diffs"
DIFF.mkdir(parents=True, exist_ok=True)

D = TO / "dispatch_long.py"
H = TO / "heartbeat_long.py"


def facts(p: Path):
    data = p.read_bytes()
    return {"bytes": len(data), "lines": data.count(b"\n") + (0 if data.endswith(b"\n") else 1),
            "sha256": hashlib.sha256(data).hexdigest()}


# ------------------------------------------------------------------ dispatch patch set
DISP = []

DISP.append(('''from datetime import datetime, timezone

PROVIDER = "custom"''',
'''from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import invocation_runtime as _ir  # noqa: E402
import terminal_contract as _tc  # noqa: E402

PROVIDER = "custom"'''))

DISP.append(('''usage: dispatch_long.py <packet.md> <task_id> <cwd> <log> <receipt.json> [--resume SID] [--max-turns N]''',
'''usage: dispatch_long.py <packet.md> <task_id> <cwd> <log> <receipt.json> [--resume SID] [--max-turns N] [--invocation-id ID] [--revision r4] [--allowed-root DIR]'''))

DISP.append(('''RUN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(RUN_ROOT, "DISPATCH_LEDGER.jsonl")''',
'''RUN_ROOT = os.environ.get("MF_RUN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(RUN_ROOT, "DISPATCH_LEDGER.jsonl")
RUN_ID = "20261005T1643Z-wan-long"
DEFAULT_ALLOWED_ROOT = os.path.join(RUN_ROOT, "tasks", "MF-DEMO-LONG-01",
                                    "corrections", "identity5m_20261008", "r4")'''))

DISP.append(('''    packet_path, task_id, cwd, log_path, receipt_path = sys.argv[1:6]
    extra = sys.argv[6:]
    prompt = open(packet_path, "r", encoding="utf-8").read()
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 28000:
        print("REFUSED: packet %d bytes > 28000 (Windows argv ceiling)" % nbytes)
        return 2''',
'''    packet_path, task_id, cwd, log_path, receipt_path = sys.argv[1:6]
    extra = sys.argv[6:]
    invocation_id = extra[extra.index("--invocation-id") + 1] if "--invocation-id" in extra else None
    revision = extra[extra.index("--revision") + 1] if "--revision" in extra else "r4"
    allowed_root = extra[extra.index("--allowed-root") + 1] if "--allowed-root" in extra else DEFAULT_ALLOWED_ROOT
    if invocation_id is None:
        invocation_id = "%s-%s-%s" % (task_id, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), os.urandom(3).hex())
    packet_bytes = open(packet_path, "rb").read()
    packet_file_sha256 = hashlib.sha256(packet_bytes).hexdigest()
    prompt = (packet_bytes.decode("utf-8")
              .replace("{{INVOCATION_ID}}", invocation_id)
              .replace("{{PACKET_SHA256}}", packet_file_sha256))
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > 28000:
        print("REFUSED: packet %d bytes > 28000 (Windows argv ceiling)" % nbytes)
        return 2

    lock, lock_meta = _ir.acquire_controller_lock(
        owner_sid=(extra[extra.index("--resume") + 1] if "--resume" in extra else "new"),
        note="dispatch_long %s" % os.path.basename(packet_path))
    if lock is None:
        append_ledger({"action": "dispatch_refused", "task_id": task_id, "at_utc": utc(),
                       "reason": "controller_locked", "holder": lock_meta})
        print("REFUSED: controller lock held by another controller: %s" % json.dumps(lock_meta))
        return 4'''))

DISP.append(('''        "new_session": resume is None,
        "remaining_seconds_at_dispatch": (round(remaining, 1) if remaining is not None else None),
        "utc_start": started, "launcher_pid": os.getpid(),
    }''',
'''        "new_session": resume is None,
        "remaining_seconds_at_dispatch": (round(remaining, 1) if remaining is not None else None),
        "utc_start": started, "launcher_pid": os.getpid(),
        "run_id": RUN_ID, "revision": revision, "owner_sid": (resume or "new"),
        "invocation_id": invocation_id, "packet_file_sha256": packet_file_sha256,
        "allowed_root": allowed_root, "controller_lock": "held",
    }'''))

DISP.append(('''    append_ledger({"action": "dispatch", "task_id": task_id, "at_utc": started,
                   "model": MODEL, "cwd": cwd, "resume_session_requested": resume,
                   "packet": packet_path, "packet_sha256": receipt["packet_sha256"],
                   "packet_bytes": nbytes, "receipt": receipt_path, "log": log_path,
                   "launcher_pid": os.getpid(), "remaining_seconds": (round(remaining, 1) if remaining is not None else None),
                   "absolute_deadline_epoch": deadline_epoch,
                   "stall_kill_seconds": stall_kill_s})''',
'''    append_ledger({"action": "dispatch", "task_id": task_id, "at_utc": started,
                   "model": MODEL, "cwd": cwd, "resume_session_requested": resume,
                   "packet": packet_path, "packet_sha256": receipt["packet_sha256"],
                   "packet_bytes": nbytes, "receipt": receipt_path, "log": log_path,
                   "launcher_pid": os.getpid(), "remaining_seconds": (round(remaining, 1) if remaining is not None else None),
                   "absolute_deadline_epoch": deadline_epoch,
                   "stall_kill_seconds": stall_kill_s,
                   "run_id": RUN_ID, "revision": revision, "owner_sid": (resume or "new"),
                   "invocation_id": invocation_id, "packet_file_sha256": packet_file_sha256,
                   "allowed_root": allowed_root})'''))

DISP.append(('''def _child_identity(pid):
    """Identity snapshot of the spawned child (pid+creation+exe) so the heartbeat can
    prove liveness by identity, never by bare pid (PID reuse)."""
    try:
        r = subprocess.run(["wmic", "process", "where", "ProcessId=%d" % pid,
                            "get", "Name,CreationDate,CommandLine", "/format:list"],
                           capture_output=True, text=True, errors="replace", timeout=60)
        facts = {}
        for line in (r.stdout or "").replace("\\r", "").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                facts[k.strip()] = v.strip()
        if facts.get("CreationDate"):
            return {"child_created": facts.get("CreationDate"), "child_name": facts.get("Name", ""),
                    "child_cmd_sha1": hashlib.sha1(facts.get("CommandLine", "").encode("utf-8", "replace")).hexdigest()[:16]}
    except Exception:  # noqa: BLE001
        pass
    return {"child_created": None, "child_name": None, "child_cmd_sha1": None}''',
'''def _child_identity(pid):
    """Identity snapshot of the spawned child (pid+creation+exe) so the heartbeat can
    prove liveness by identity, never by bare pid (PID reuse). psutil first (R4 §4);
    wmic remains only as fallback when psutil cannot read the process."""
    f = _ir.pid_facts(pid)
    if isinstance(f, dict) and f:
        return {"child_created": f.get("created"), "child_name": f.get("name", ""),
                "child_cmd_sha1": hashlib.sha1((f.get("cmd") or "").encode("utf-8", "replace")).hexdigest()[:16],
                "child_created_epoch": f.get("create_epoch")}
    try:
        r = subprocess.run(["wmic", "process", "where", "ProcessId=%d" % pid,
                            "get", "Name,CreationDate,CommandLine", "/format:list"],
                           capture_output=True, text=True, errors="replace", timeout=60)
        facts = {}
        for line in (r.stdout or "").replace("\\r", "").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                facts[k.strip()] = v.strip()
        if facts.get("CreationDate"):
            return {"child_created": facts.get("CreationDate"), "child_name": facts.get("Name", ""),
                    "child_cmd_sha1": hashlib.sha1(facts.get("CommandLine", "").encode("utf-8", "replace")).hexdigest()[:16],
                    "child_created_epoch": None}
    except Exception:  # noqa: BLE001
        pass
    return {"child_created": None, "child_name": None, "child_cmd_sha1": None, "child_created_epoch": None}'''))

DISP.append(('''            append_ledger({"action": "child_spawned", "task_id": task_id, "at_utc": utc(),
                           "child_pid": proc.pid, "launcher_pid": os.getpid(),
                           "child_created": ident["child_created"], "child_name": ident["child_name"],
                           "child_cmd_sha1": ident["child_cmd_sha1"],
                           "hermes_max_tokens_env": env.get("HERMES_MAX_TOKENS")})''',
'''            append_ledger({"action": "child_spawned", "task_id": task_id, "at_utc": utc(),
                           "child_pid": proc.pid, "launcher_pid": os.getpid(),
                           "child_created": ident["child_created"], "child_name": ident["child_name"],
                           "child_cmd_sha1": ident["child_cmd_sha1"],
                           "child_created_epoch": ident.get("child_created_epoch"),
                           "hermes_max_tokens_env": env.get("HERMES_MAX_TOKENS")})
            _ir.lease_acquire(invocation_id, job=os.path.basename(packet_path),
                              owner_sid=(resume or "new"),
                              children=[{"pid": proc.pid, "created": ident["child_created"],
                                         "name": ident["child_name"]}],
                              extra={"launcher_pid": os.getpid()})'''))

DISP.append(('''    ended = utc()
    meta = parse_session_meta(log_path)
    outcome = classify_outcome(log_path, rc)
    receipt.update({"exit_code": rc, "utc_end": ended, "timed_out": timed_out,''',
'''    ended = utc()
    meta = parse_session_meta(log_path)
    legacy_outcome = classify_outcome(log_path, rc)
    expected = {"run_id": RUN_ID, "task_id": task_id, "revision": revision,
                "owner_sid": (resume or "new"), "invocation_id": invocation_id,
                "packet_sha256": packet_file_sha256}
    infra = bool(timed_out) or _ir.log_has_infra_error(log_path)
    child_state = _ir.identity_alive(child.get("child_pid"), child.get("child_created"),
                                     child.get("child_name"))
    child_reconciled = child.get("child_pid") is not None and child_state is not True
    try:
        import pathlib as _pl
        verdict = _tc.validate_result(
            _pl.Path(allowed_root) / "evidence" / "terminal" / (invocation_id + ".json"),
            _tc.Binding(**expected), _pl.Path(allowed_root),
            invocation_terminal=child_reconciled, exit_code=rc, infrastructure_error=infra)
    except Exception as _e:  # noqa: BLE001
        verdict = {"decision": "NEEDS_RECONCILIATION", "quality_accepted": False,
                   "error": "binding/setup: %s: %s" % (type(_e).__name__, _e)}
    if verdict.get("decision") == "NEEDS_RECONCILIATION":
        outcome = {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                   "error": verdict.get("error"), "legacy_prose_class": legacy_outcome.get("class")}
    else:
        outcome = {"class": verdict["result"]["status"], "source": "structured_terminal",
                   "decision": verdict["decision"], "legacy_prose_class": legacy_outcome.get("class")}
    lease_result = _ir.lease_release_if_children_gone(invocation_id)
    receipt.update({"exit_code": rc, "utc_end": ended, "timed_out": timed_out,'''))

DISP.append(('''                    "note": "exit code alone is NOT completion proof - read the log payload; check for finish_reason='length' / 'API call failed' / UsageLimit"})''',
'''                    "note": "exit code alone is NOT completion proof - read the log payload; check for finish_reason='length' / 'API call failed' / UsageLimit",
                    "invocation_id": invocation_id, "terminal_validation": verdict,
                    "legacy_prose_outcome": legacy_outcome, "gpu_lease_release": lease_result})'''))

DISP.append(('''    append_ledger({"action": "terminal", "task_id": task_id, "at_utc": ended,
                   "exit_code": rc, "timed_out": timed_out, "log_bytes": receipt["log_bytes"],
                   "receipt": receipt_path, "launcher_pid": os.getpid(),
                   "child_pid": child.get("child_pid"), "outcome_class": outcome["class"],
                   "session_id_actual": meta["session_id_actual"]})
    print(json.dumps({"exit_code": rc, "timed_out": timed_out, "log_bytes": receipt["log_bytes"],
                      "outcome_class": outcome["class"], "session_id_actual": meta["session_id_actual"]}))
    return 0''',
'''    append_ledger({"action": "terminal", "task_id": task_id, "at_utc": ended,
                   "exit_code": rc, "timed_out": timed_out, "log_bytes": receipt["log_bytes"],
                   "receipt": receipt_path, "launcher_pid": os.getpid(),
                   "child_pid": child.get("child_pid"), "outcome_class": outcome["class"],
                   "session_id_actual": meta["session_id_actual"],
                   "invocation_id": invocation_id, "terminal_decision": verdict.get("decision"),
                   "terminal_error": verdict.get("error")})
    _ir.release_controller_lock(lock, outcome=outcome["class"])
    print(json.dumps({"exit_code": rc, "timed_out": timed_out, "log_bytes": receipt["log_bytes"],
                      "outcome_class": outcome["class"], "session_id_actual": meta["session_id_actual"]}))
    return 0'''))

DISP.append(('''        except Exception as e:  # noqa: BLE001
            append_ledger({"action": "dispatch_error", "task_id": task_id, "at_utc": utc(),
                           "error": "%s: %s" % (type(e).__name__, e)})
            raise''',
'''        except Exception as e:  # noqa: BLE001
            append_ledger({"action": "dispatch_error", "task_id": task_id, "at_utc": utc(),
                           "error": "%s: %s" % (type(e).__name__, e)})
            _ir.release_controller_lock(lock, outcome="dispatch_error")
            raise'''))

# ------------------------------------------------------------------ heartbeat patch set
HB = []

HB.append(('''from pathlib import Path

MANAGER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # = RUN/manager
RUN = os.path.dirname(MANAGER)''',
'''from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import invocation_runtime as _ir  # noqa: E402

_ENV_RUN = os.environ.get("MF_RUN_ROOT")
if _ENV_RUN:
    RUN = os.path.abspath(_ENV_RUN)
    MANAGER = os.path.join(RUN, "manager")
else:
    MANAGER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # = RUN/manager
    RUN = os.path.dirname(MANAGER)'''))

HB.append(('''def proc_facts(pid):
    """(name, created, cmdline) from wmic for pid. {} if gone; None if the QUERY
    itself failed (caller must treat as UNKNOWN, not as dead)."""
    try:
        r = subprocess.run(["wmic", "process", "where", "ProcessId=%d" % pid,
                            "get", "Name,CreationDate,CommandLine", "/format:list"],
                           capture_output=True, text=True, errors="replace", timeout=60)
    except Exception:  # noqa: BLE001
        return None
    out = ((r.stdout or "") + (r.stderr or "")).replace("\\r", "")
    if "No Instance(s) Available" in out:
        return {}
    facts = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            facts[k.strip()] = v.strip()
    if not facts.get("CreationDate"):
        return None  # empty/odd output -> UNKNOWN
    return {"name": facts.get("Name", ""), "created": facts.get("CreationDate", ""),
            "cmd": facts.get("CommandLine", "")}''',
'''def proc_facts(pid):
    """(name, created, cmdline) via psutil (R4 §4). {} if gone; None if the probe
    itself failed (caller must treat as UNKNOWN, not as dead)."""
    f = _ir.pid_facts(pid)
    if f is None:
        return None
    if not f:
        return {}
    return {"name": f.get("name", ""), "created": f.get("created", ""), "cmd": f.get("cmd", "")}'''))

HB.append(('''def render_alive():
    """(bool|None, evidence). Comfy queue non-empty OR p4_wan_run runner alive.''',
'''def effective_outcome(disp, receipt, log_path):
    """Structured terminal FIRST (R4 §4): the terminal record validated against the
    immutable dispatch binding is the only authority for completion. Legacy prose
    classification is retained as reference only (F09 misread: plan token vs terminal)."""
    if receipt is None:
        return {"class": "NO_RECEIPT", "detail": "invocation open or receipt unreadable"}
    tv = receipt.get("terminal_validation")
    legacy = classify_outcome(receipt, log_path)
    if isinstance(tv, dict):
        if tv.get("decision") == "NEEDS_RECONCILIATION":
            return {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                    "error": tv.get("error"), "legacy_prose_class": legacy.get("class")}
        res = tv.get("result") or {}
        return {"class": res.get("status", "NEEDS_RECONCILIATION"), "source": "structured_terminal",
                "decision": tv.get("decision"), "legacy_prose_class": legacy.get("class")}
    return {"class": "LEGACY_NO_STRUCTURED_TERMINAL", "source": "legacy_receipt (NOT authority)",
            "legacy_prose_class": legacy.get("class"), "exit_code": legacy.get("exit_code")}


def render_alive():
    """(bool|None, evidence). Comfy queue non-empty OR p4_wan_run runner alive.'''))

HB.append(('''        if inv_open:
            outcome = {"class": "INVOCATION_OPEN"}
        elif receipt is not None:
            outcome = classify_outcome(receipt, log)
        else:
            outcome = {"class": "NO_RECEIPT", "detail": "no dispatch row and no receipt"}''',
'''        if inv_open:
            outcome = {"class": "INVOCATION_OPEN"}
        else:
            outcome = effective_outcome(disp, receipt, log)'''))

HB.append(('''def identity_alive(pid, created=None, name=None):
    """True iff same pid AND same creation time AND (if given) same exe name.
    None = probe UNKNOWN (query failure) — caller must not read it as dead."""
    if not pid:
        return False
    f = proc_facts(pid)
    if f is None:
        return None
    if not f:
        return False
    if created and f.get("created") != created:
        return False
    if name and f.get("name", "").lower() != name.lower():
        return False
    return True''',
'''def identity_alive(pid, created=None, name=None):
    """True iff same pid AND same creation time (±2ms) AND (if given) same exe name.
    psutil-backed via invocation_runtime; None = probe UNKNOWN (never read as dead)."""
    return _ir.identity_alive(pid, created, name)'''))

HB.append(('''            "receipt_exit_code": (receipt or {}).get("exit_code", "<none>"),
            "receipt_timed_out": (receipt or {}).get("timed_out", "<none>"),
        }''',
'''            "receipt_exit_code": (receipt or {}).get("exit_code", "<none>"),
            "receipt_timed_out": (receipt or {}).get("timed_out", "<none>"),
            "controller_lock": _ir.controller_status(),
            "leases": _ir.leases_status(),
        }'''))


def main() -> int:
    dry = os.environ.get("DRY") == "1"
    results = {}
    combined = []
    for path, patches, tag in ((D, DISP, "dispatch_long.py"), (H, HB, "heartbeat_long.py")):
        orig = path.read_bytes().decode("utf-8")
        before = facts(path)
        text = orig
        for i, (old, new) in enumerate(patches, 1):
            c = text.count(old)
            if c != 1:
                raise SystemExit("ANCHOR FAIL %s #%d: count=%d" % (tag, i, c))
            text = text.replace(old, new)
        if dry:
            results[tag] = {"anchors_ok": len(patches), "dry_run": True, "before": before}
            continue
        path.write_text(text, encoding="utf-8", newline="")
        after = facts(path)
        diff = "".join(difflib.unified_diff(orig.splitlines(True), text.splitlines(True),
                                            fromfile=tag + ".pre", tofile=tag + ".post"))
        (DIFF / (tag + ".diff")).write_text(diff, encoding="utf-8")
        py_compile.compile(str(path), doraise=True)
        results[tag] = {"anchors_applied": len(patches), "before": before, "after": after,
                        "diff_path": str(DIFF / (tag + ".diff")),
                        "gains": after["bytes"] - before["bytes"], "lines_delta": after["lines"] - before["lines"]}
    report = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "patches": results,
              "smoke_markers": {
                  "dispatch": all(m in (D.read_text(encoding="utf-8")) for m in
                                  ("acquire_controller_lock", "lease_release_if_children_gone",
                                   "terminal_validation", "{{INVOCATION_ID}}", "packet_file_sha256")),
                  "heartbeat": all(m in (H.read_text(encoding="utf-8")) for m in
                                   ("effective_outcome", "MF_RUN_ROOT", "controller_status", "leases_status")),
              }}
    (EV / "R4_CONSUMER_PATCHES.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
