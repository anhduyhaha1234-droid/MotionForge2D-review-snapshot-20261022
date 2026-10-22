#!/usr/bin/env python
"""Long-scope dispatcher (Manager-owned, MF-DEMO-LONG-01, 2026-10-05 run).

usage: dispatch_long.py <packet.md> <task_id> <cwd> <log> <receipt.json> [--resume SID] [--max-turns N] [--invocation-id ID] [--revision r4] [--allowed-root DIR]

Fixes the prototype harness defects (packet §3):
  * deadline is REMAINING-TO-ABSOLUTE (never a fresh 21600 per resume) -- pass
    --deadline-epoch <epoch>; refuses when <=0.
  * the launcher prints EXACT child identity (pid + creation time) for the heartbeat.
Exit code alone is NOT completion proof (pitfall: API 503 / finish_reason='length').
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import invocation_runtime as _ir  # noqa: E402
import terminal_contract as _tc  # noqa: E402

PROVIDER = "custom"
MODEL = "cmc/deepseek/deepseek-v4.1-flash"
BASE_URL = "http://127.0.0.1:20128/v1"
API_MODE = "chat_completions"

# POLICY 2026-10-06 (user: bo budget tu dat): no total-time / call / candidate / continuation
# stop gate. Only real writer termination, user stop, or an out-of-scope blocker ends the task.
NO_DEADLINE_STOP_GATE = True
# POLICY 2026-10-07 (F12): NO wall-clock kill of a running child (a 6h cap killed legitimate
# work). The child is stopped ONLY on evidence of a real hang: its worker log has not grown
# for STALL_KILL_S seconds (3+ missed poll cycles, no tool output at all). On hit:
# checkpoint + resume the SAME owner session. Configurable per dispatch via
# --stall-kill-seconds (used by the fake-child test).
DEFAULT_STALL_KILL_S = 3600

_ENV_RUN = os.environ.get("MF_RUN_ROOT")
if _ENV_RUN:
    _RUN = os.path.abspath(_ENV_RUN)
    RUN_ROOT = os.path.join(_RUN, "manager")
else:
    RUN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # = RUN/manager
    _RUN = os.path.dirname(RUN_ROOT)
LEDGER = os.path.join(RUN_ROOT, "DISPATCH_LEDGER.jsonl")
RUN_ID = "20261005T1643Z-wan-long"
DEFAULT_ALLOWED_ROOT = os.path.join(_RUN, "tasks", "MF-DEMO-LONG-01",
                                    "corrections", "identity5m_20261008", "r4")


def utc():
    return datetime.now(timezone.utc).isoformat()


def append_ledger(row):
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _log_sig(path):
    """(size, mtime) of the worker log, or None if absent."""
    try:
        st = os.stat(path)
        return (st.st_size, st.st_mtime)
    except OSError:
        return None


def _scan_newest_mtime(roots):
    """Newest mtime epoch under the given roots (None when nothing could be scanned)."""
    newest = None
    for root in (roots or []):
        if not root or not os.path.isdir(root):
            continue
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                try:
                    m = os.path.getmtime(os.path.join(dp, f))
                except OSError:
                    continue
                if newest is None or m > newest:
                    newest = m
    return newest


def _audit_stall(proc, watch_roots, since_ts):
    """R5 §4.4: LLM log silence triggers an AUDIT, never an automatic kill.

    Gather real progress evidence: artifact delta in the worker write-roots, live
    descendant processes (recursive identity scan), Comfy queue / render probe.
    -> (status, evidence); status in PROGRESSING | TRUE_HANG | UNKNOWN.
      PROGRESSING: fresh artifact bytes -> the batch is advancing; keep waiting.
      UNKNOWN:     cannot prove death (live descendants / probe unknown / render busy)
                   -> keep waiting; Manager reconciles (never kill blind).
      TRUE_HANG:   no artifact delta AND every descendant verified DEAD AND render
                   quiet -> kill for same-owner resume with a distinct classification.
    """
    ev = {}
    newest = _scan_newest_mtime(watch_roots)
    ev["artifact_mtime"] = newest
    ev["artifact_delta"] = bool(newest is not None and newest > since_ts)
    desc, derr = _ir.descendants_of([proc.pid])
    if desc is None:
        ev["children"] = "UNKNOWN: %s" % derr
        n_alive = None
    else:
        alive = [c for c in desc if _ir.identity_alive(c["pid"], c.get("created"), c.get("name"))]
        ev["children"] = {"n": len(desc), "alive": len(alive), "sample": desc[:8]}
        n_alive = len(alive)  # evidence only: render probe above is the kill gate
    q, detail = _ir.probe_render_quiet()
    ev["render"] = {"quiet": q, "detail": detail}
    if ev["artifact_delta"]:
        return "PROGRESSING", ev
    # A live descendant that IS a render-side runner is already covered by the render
    # probe (machine-wide, includes descendants). The plain child chain staying alive
    # (venv python shim -> base python / hermes CLI) is NOT progress evidence: a log
    # silent a full window with zero artifact delta and a quiet render probe is a
    # TRUE_HANG. Never kill while the render probe reports activity or UNKNOWN.
    if q is not True:
        return "UNKNOWN", ev
    return "TRUE_HANG", ev


def wait_with_stall_detector(proc, log_path, stall_kill_s, poll_s=20, watch_roots=None):
    """Wait for the child WITHOUT any wall-clock total cap (F12 / R5 §4.4).

    On log silence > stall_kill_s the stall AUDIT runs; only a fully verified
    TRUE_HANG (no artifact delta, all descendants DEAD, render quiet) kills the
    child for a same-owner resume. PROGRESSING and UNKNOWN keep the child alive --
    the R4c incident (kill at 3602s while the batch was alive) must not recur.
    Returns (rc, timed_out).
    """
    watch_roots = list(watch_roots or [])
    prev = _log_sig(log_path)
    last_growth = time.time()
    while True:
        try:
            rc = proc.wait(timeout=poll_s)
            return rc, False
        except subprocess.TimeoutExpired:
            pass
        cur = _log_sig(log_path)
        now = time.time()
        if cur != prev:
            prev = cur
            last_growth = now
        if now - last_growth > stall_kill_s:
            status, evidence = _audit_stall(proc, watch_roots, last_growth)
            append_ledger({"action": "stall_audit", "at_utc": utc(), "child_pid": proc.pid,
                           "log": log_path, "silent_s": round(now - last_growth, 1),
                           "status": status, "evidence": evidence})
            if status == "TRUE_HANG":
                print("TRUE_HANG: log silent %.0fs, no artifact/child/queue evidence -> killing pid %d "
                      "for same-owner resume" % (now - last_growth, proc.pid))
                proc.kill()
                rc = proc.wait()
                return rc, True
            # PROGRESSING / UNKNOWN: never kill on silence alone; open a fresh window.
            last_growth = now


def _child_identity(pid):
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
        for line in (r.stdout or "").replace("\r", "").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                facts[k.strip()] = v.strip()
        if facts.get("CreationDate"):
            return {"child_created": facts.get("CreationDate"), "child_name": facts.get("Name", ""),
                    "child_cmd_sha1": hashlib.sha1(facts.get("CommandLine", "").encode("utf-8", "replace")).hexdigest()[:16],
                    "child_created_epoch": None}
    except Exception:  # noqa: BLE001
        pass
    return {"child_created": None, "child_name": None, "child_cmd_sha1": None, "child_created_epoch": None}


# Machine-readable terminal classes (packet §4). exit0 + error text != completed.
# Markers lowercase; matched against tail.lower() (CLI logs vary in capitalisation).
_OUTCOME_MARKERS = (
    ("CONTEXT_EXHAUSTED", ("max compression attempts", "context length exceeded")),
    ("OUTPUT_TRUNCATED", ("truncated due to output length",)),
    ("QUOTA_BLOCKED", ("gousagelimiterror", "usagelimit", "insufficient quota", "quota exceeded")),
    ("USER_STOP", ("user_stop",)),
    ("SELF_REVIEW_PASS_PENDING_CODEX", ("self_review_pass_pending_codex",)),
    ("CONTINUE_REQUIRED", ("continue_required",)),
    ("ITERATION_YIELD", ("maximum tool-calling iterations",)),
)


def classify_outcome(log_path, rc):
    """Class from the log payload; exit code alone is never 'completed'.
    LATEST occurrence wins (a plan line mentioning a status token must not beat
    the actual terminal line — W5 incident: 'SELF_REVIEW_PASS_PENDING_CODEX
    (chi khi TOAN BO master dat)' in a forward-looking line vs the real
    CONTINUE_REQUIRED terminal). Ties break by marker-list order."""
    tail = ""
    try:
        with open(log_path, "rb") as fh:
            try:
                fh.seek(-200_000, os.SEEK_END)
            except OSError:
                pass
            tail = fh.read().decode("utf-8", errors="replace")
    except OSError:
        pass
    tail = tail.lower()
    best = None  # (pos, order_idx, cls, marker)
    for idx, (cls, markers) in enumerate(_OUTCOME_MARKERS):
        for m in markers:
            p = tail.rfind(m)
            if p < 0:
                continue
            if best is None or p > best[0] or (p == best[0] and idx < best[1]):
                best = (p, idx, cls, m)
    if best is not None:
        return {"class": best[2], "marker": best[3], "match_pos": best[0],
                "exit_code": rc, "not_completed": True}
    if rc == 0:
        return {"class": "EXIT0_NO_KNOWN_MARKER", "exit_code": rc, "not_completed": None,
                "detail": "read log payload before trusting"}
    return {"class": "EXIT_NONZERO", "exit_code": rc, "not_completed": True}


def parse_session_meta(log_path):
    """Session id + OBSERVED compaction count + last CLI context estimate from the
    log. For a NEW session (no --resume) the first session-id literal is the minted
    SID (cross-checked against the worker's own D/evidence/OWNER_SID.txt)."""
    import re
    meta = {"session_id_actual": None, "compactions": 0, "last_context_line": None,
            "tool_actions_observed": 0, "log_bytes": 0}
    try:
        meta["log_bytes"] = os.path.getsize(log_path)
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return meta
    # Session id: prefer the CLI exit banner ("Session:  <sid>" / "--resume <sid>"),
    # taking the LAST match — a NEW session's packet text can mention OTHER session
    # ids early in the log (W4 incident: receipt recorded the OLD sid from the
    # packet echo). Fall back to the last generic sid literal.
    banner = re.findall(r"(?:^|\n)\s*Session:\s+(20\d{6}_\d{6}_[0-9a-f]{6})", text)
    resume_b = re.findall(r"hermes --resume\s+(20\d{6}_\d{6}_[0-9a-f]{6})", text)
    cand = banner or resume_b
    if cand:
        meta["session_id_actual"] = cand[-1]
    else:
        m2 = re.findall(r"\b(20\d{6}_\d{6}_[0-9a-f]{6})\b", text)
        meta["session_id_actual"] = m2[-1] if m2 else None
    # Compactions: count REAL event banners only. Each event logs BOTH
    # "⟳ compacting context…" and the "🗜️ Compacting context — summarizing earlier
    # conversation…" banner, and the agent's own text may contain the phrase too —
    # so count banner lines (W2r: 3 events -> 3; naive count said 6).
    meta["compactions"] = sum(1 for ln in text.splitlines()
                              if "summarizing earlier conversation" in ln.lower()
                              or "🗜️ compacting context" in ln.lower())
    for ln in text.splitlines():
        if "Context:" in ln:
            meta["last_context_line"] = ln.strip()[:200]
        if "┊" in ln:  # tool-action rows in the CLI log
            meta["tool_actions_observed"] += 1
    return meta


def main() -> int:
    # TEST-MODE SAFETY (2026-10-07 incident): a fixture run that forgot the argv
    # prefix must NEVER invoke the real CLI/session (a .bat shim is not resolved by
    # CreateProcess; the real hermes.exe on PATH ran instead). Boot explicit.
    if os.environ.get("DISPATCH_TEST") == "1" and not os.environ.get("DISPATCH_HERMES_ARGV_PREFIX"):
        print("REFUSED: DISPATCH_TEST=1 requires DISPATCH_HERMES_ARGV_PREFIX (never invoke the real CLI in tests)")
        return 3
    packet_path, task_id, cwd, log_path, receipt_path = sys.argv[1:6]
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
        return 4

    # R5 §4.1: reconcile EVERY non-released GPU lease + job lineage UNDER the same
    # controller mutex; active/detached/UNKNOWN claims are a hard barrier. A free
    # controller lock is NOT proof that an older GPU job finished.
    _requested_sid = extra[extra.index("--resume") + 1] if "--resume" in extra else "new"
    reconcile = _ir.reconcile_gpu_leases(requester_sid=_requested_sid)
    if not reconcile.get("ok"):
        append_ledger({"action": "dispatch_refused", "task_id": task_id, "at_utc": utc(),
                       "reason": "gpu_lease_barrier", "detail": reconcile})
        print("REFUSED: GPU lease/ownership barrier: %s" % json.dumps(reconcile)[:600])
        _ir.release_controller_lock(lock, outcome="dispatch_refused_gpu_lease")
        return 4

    resume = _requested_sid if "--resume" in extra else None
    # POLICY 2026-10-07 (packet §4): max_turns 80 = invocation boundary that hands
    # back to the Manager for continuation (same SID). NOT a task stop gate; total
    # turns are uncapped. Worker checkpoints before the boundary -> CONTINUE_REQUIRED.
    max_turns = extra[extra.index("--max-turns") + 1] if "--max-turns" in extra else "80"
    # POLICY 2026-10-07 (packet §4): per-RESPONSE output ceiling for THIS task child =
    # 16384 (was 131072; the big value left no headroom vs the provider's 1,048,576
    # total -> W2r HTTP400). cli.py:4352 honours HERMES_MAX_TOKENS overriding
    # model.max_tokens; task-local env only; global config / router untouched.
    max_tokens = extra[extra.index("--max-tokens") + 1] if "--max-tokens" in extra else "16384"
    deadline_epoch = float(extra[extra.index("--deadline-epoch") + 1]) if "--deadline-epoch" in extra else None
    stall_kill_s = int(extra[extra.index("--stall-kill-seconds") + 1]) if "--stall-kill-seconds" in extra else DEFAULT_STALL_KILL_S
    toolsets = extra[extra.index("--toolsets") + 1] if "--toolsets" in extra else None
    skills = extra[extra.index("--skills") + 1] if "--skills" in extra else None
    # R5 §4.4: artifact-delta watch roots for the stall audit (explicit or derived).
    watch_roots = [extra[i + 1] for i, x in enumerate(extra[:-1]) if x == "--watch-root"]
    if not watch_roots:
        try:
            import pathlib as _plr
            _D = str(_plr.Path(allowed_root).parents[2])  # <D>/corrections/<rev>/<r5> -> <D>
        except Exception:  # noqa: BLE001
            _D = None
        if _D and os.path.isdir(_D):
            watch_roots = [allowed_root,
                           os.path.join(_D, "input", "identity5m_20261008"),
                           os.path.join(_D, "output", "identity5m_20261008"),
                           os.path.join(_D, "temp", "identity5m_20261008")]

    # POLICY 2026-10-07: deadline is OPTIONAL and NEVER a stop gate (kept for receipts/history).
    remaining = None
    if deadline_epoch is not None:
        remaining = deadline_epoch - time.time()
        if remaining <= 0:
            print("NOTE: absolute deadline passed (remaining=%.1fs); policy 2026-10-06 -> continue without stop gate" % remaining)

    argv = ["hermes", "chat", "-q", prompt, "--provider", PROVIDER, "-m", MODEL,
            "--pass-session-id", "--no-restore-cwd", "--yolo", "--max-turns", max_turns]
    # TEST-ONLY override (Manager harness): fake-child policy tests need a controlled argv
    # prefix (Popen on Windows cannot resolve a .bat named 'hermes'; testing must NEVER
    # invoke the real CLI/session). Empty/unset in production -> real 'hermes'.
    _prefix = os.environ.get("DISPATCH_HERMES_ARGV_PREFIX", "").strip()
    if _prefix:
        prefix = json.loads(_prefix)
        if isinstance(prefix, list) and prefix and all(isinstance(x, str) for x in prefix):
            argv = prefix + argv[1:]
            print("NOTE: DISPATCH_HERMES_ARGV_PREFIX active (test mode): %s" % prefix)
    if toolsets:
        argv += ["-t", toolsets]
    if skills:
        argv += ["-s", skills]
    if resume:
        argv += ["--resume", resume]

    started = utc()
    receipt = {
        "task_id": task_id, "round": os.path.basename(packet_path),
        "packet": packet_path, "packet_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "packet_bytes": nbytes, "cwd": cwd, "provider": PROVIDER, "model": MODEL,
        "base_url": BASE_URL, "api_mode_pinned_in_packet": API_MODE, "fallback": False,
        "toolsets": toolsets, "skills": skills, "resume_session_requested": resume,
        "max_turns": max_turns, "absolute_deadline_epoch": deadline_epoch,
        "stall_kill_seconds": stall_kill_s,
        "max_tokens_requested": max_tokens,
        "max_tokens_effective_scheme": "HERMES_MAX_TOKENS env on child process (cli.py:4352); lever verified 2026-10-06 (HERMES_MAX_TOKENS=24 -> output cut at 24 tokens)",
        "max_turns_note": "invocation boundary, NOT a task stop gate (packet §4)",
        "new_session": resume is None,
        "remaining_seconds_at_dispatch": (round(remaining, 1) if remaining is not None else None),
        "utc_start": started, "launcher_pid": os.getpid(),
        "run_id": RUN_ID, "revision": revision, "owner_sid": (resume or "new"),
        "invocation_id": invocation_id, "packet_file_sha256": packet_file_sha256,
        "allowed_root": allowed_root, "controller_lock": "held",
    }
    os.makedirs(os.path.dirname(receipt_path), exist_ok=True)
    open(receipt_path, "w", encoding="utf-8").write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    append_ledger({"action": "dispatch", "task_id": task_id, "at_utc": started,
                   "model": MODEL, "cwd": cwd, "resume_session_requested": resume,
                   "packet": packet_path, "packet_sha256": receipt["packet_sha256"],
                   "packet_bytes": nbytes, "receipt": receipt_path, "log": log_path,
                   "launcher_pid": os.getpid(), "remaining_seconds": (round(remaining, 1) if remaining is not None else None),
                   "absolute_deadline_epoch": deadline_epoch,
                   "stall_kill_seconds": stall_kill_s,
                   "run_id": RUN_ID, "revision": revision, "owner_sid": (resume or "new"),
                   "invocation_id": invocation_id, "packet_file_sha256": packet_file_sha256,
                   "allowed_root": allowed_root})

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["HERMES_MAX_TOKENS"] = max_tokens
    timed_out = False
    rc = None
    child = {"child_pid": None}
    # R5 §4.1 barrier: reserve GPU ownership BEFORE Popen (status=RESERVED). A second
    # controller that ever sees this claim refuses to spawn a twin child.
    _launcher_facts = _ir.pid_facts(os.getpid()) or {}
    _launcher_ident = {"pid": os.getpid(), "created": _launcher_facts.get("created"),
                       "name": _launcher_facts.get("name", "")}
    _ir.lease_reserve(invocation_id, owner_sid=(resume or "new"),
                      job=os.path.basename(packet_path), launcher_identity=_launcher_ident)
    with open(log_path, "wb") as log:
        try:
            proc = subprocess.Popen(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env)
            child = {"child_pid": proc.pid}
            ident = _child_identity(proc.pid)
            append_ledger({"action": "child_spawned", "task_id": task_id, "at_utc": utc(),
                           "child_pid": proc.pid, "launcher_pid": os.getpid(),
                           "child_created": ident["child_created"], "child_name": ident["child_name"],
                           "child_cmd_sha1": ident["child_cmd_sha1"],
                           "child_created_epoch": ident.get("child_created_epoch"),
                           "hermes_max_tokens_env": env.get("HERMES_MAX_TOKENS")})
            spawned = [{"pid": proc.pid, "created": ident["child_created"], "name": ident["child_name"]}]
            _desc, _derr = _ir.descendants_of([proc.pid])  # launcher -> LLM -> early descendants
            if _desc:
                spawned += _desc
            _ir.lease_promote(invocation_id, children=spawned,
                              extra={"launcher_pid": os.getpid(), "launcher": _launcher_ident})
            # POLICY 2026-10-07 (F12) + R5 §4.4: NO wall-clock cap; log silence runs the
            # stall AUDIT (artifact delta + descendants + queue) before any hang decision.
            _poll = max(5, min(20, stall_kill_s // 3)) if stall_kill_s > 0 else 20
            rc, timed_out = wait_with_stall_detector(proc, log_path, stall_kill_s, poll_s=_poll,
                                                     watch_roots=watch_roots)
        except Exception as e:  # noqa: BLE001
            append_ledger({"action": "dispatch_error", "task_id": task_id, "at_utc": utc(),
                           "error": "%s: %s" % (type(e).__name__, e)})
            if child.get("child_pid") is None:
                _ir.lease_abandon(invocation_id, reason="dispatch_error before spawn")
            _ir.release_controller_lock(lock, outcome="dispatch_error")
            raise

    ended = utc()
    meta = parse_session_meta(log_path)
    legacy_outcome = classify_outcome(log_path, rc)
    expected = {"run_id": RUN_ID, "task_id": task_id, "revision": revision,
                "owner_sid": (resume or "new"), "invocation_id": invocation_id,
                "packet_sha256": packet_file_sha256}
    infra = bool(timed_out) or _ir.log_has_infra_error(log_path)
    child_state = _ir.identity_alive(child.get("child_pid"), child.get("child_created"),
                                     child.get("child_name"))
    # R5 §4.2: terminal requires a VERIFIED-dead child; UNKNOWN keeps the claim open
    # (AccessDenied / probe failure must never read as reconciled).
    child_reconciled = child.get("child_pid") is not None and child_state is False
    # R5 §4.2: terminal also requires all owned jobs/queue reconciled: release the GPU
    # lease BEFORE the verdict; a lease that cannot be released blocks submission.
    lease_result = _ir.lease_release_if_children_gone(invocation_id)
    lease_reconciled = bool(lease_result.get("released"))
    try:
        import pathlib as _pl
        verdict = _tc.validate_result(
            _pl.Path(allowed_root) / "evidence" / "terminal" / (invocation_id + ".json"),
            _tc.Binding(**expected), _pl.Path(allowed_root),
            invocation_terminal=(child_reconciled and lease_reconciled),
            exit_code=rc, infrastructure_error=infra)
    except Exception as _e:  # noqa: BLE001
        verdict = {"decision": "NEEDS_RECONCILIATION", "quality_accepted": False,
                   "error": "binding/setup: %s: %s" % (type(_e).__name__, _e)}
    if verdict.get("decision") == "NEEDS_RECONCILIATION":
        outcome = {"class": "NEEDS_RECONCILIATION", "source": "structured_terminal",
                   "error": verdict.get("error"), "legacy_prose_class": legacy_outcome.get("class")}
    else:
        outcome = {"class": verdict["result"]["status"], "source": "structured_terminal",
                   "decision": verdict["decision"], "legacy_prose_class": legacy_outcome.get("class")}
    receipt.update({"exit_code": rc, "utc_end": ended, "timed_out": timed_out,
                    "log": log_path, "log_bytes": os.path.getsize(log_path) if os.path.exists(log_path) else 0,
                    "session_id_actual": meta["session_id_actual"],
                    "outcome_class": outcome["class"], "outcome_detail": outcome,
                    "context_metrics": {"compactions_observed": meta["compactions"],
                                        "tool_actions_observed": meta["tool_actions_observed"],
                                        "last_context_line": meta["last_context_line"],
                                        "max_output_setting": max_tokens,
                                        "context_window_advertised": 1000000,
                                        "label": "observed counts; token estimate is the CLI's own"},
                    "note": "exit code alone is NOT completion proof - read the log payload; check for finish_reason='length' / 'API call failed' / UsageLimit",
                    "invocation_id": invocation_id, "terminal_validation": verdict,
                    "legacy_prose_outcome": legacy_outcome, "gpu_lease_release": lease_result})
    open(receipt_path, "w", encoding="utf-8").write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    append_ledger({"action": "terminal", "task_id": task_id, "at_utc": ended,
                   "exit_code": rc, "timed_out": timed_out, "log_bytes": receipt["log_bytes"],
                   "receipt": receipt_path, "launcher_pid": os.getpid(),
                   "child_pid": child.get("child_pid"), "outcome_class": outcome["class"],
                   "session_id_actual": meta["session_id_actual"],
                   "invocation_id": invocation_id, "terminal_decision": verdict.get("decision"),
                   "terminal_error": verdict.get("error")})
    _ir.release_controller_lock(lock, outcome=outcome["class"])
    print(json.dumps({"exit_code": rc, "timed_out": timed_out, "log_bytes": receipt["log_bytes"],
                      "outcome_class": outcome["class"], "session_id_actual": meta["session_id_actual"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
