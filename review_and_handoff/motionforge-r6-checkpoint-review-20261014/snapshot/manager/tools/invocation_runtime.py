#!/usr/bin/env python
"""R4 invocation runtime (Manager harness, 2026-10-11) -- controller lock + GPU lease + identity.

Shared by dispatch_long.py and heartbeat_long.py (Manager write-set only). Semantics
fixed by packet R4 section 4:
  * ONE controller at a time (filelock). A second live controller is refused; a dead
    holder is superseded explicitly (meta recorded).
  * GPU lease spans the whole invocation INCLUDING detached render children: it is
    released only when every recorded child identity is gone AND the Comfy queue /
    runner probe is quiet. Controller exit never releases a lease while a detached
    child still runs.
  * Process identity = pid + create_time (+ name) via psutil; AccessDenied => UNKNOWN,
    never DEAD. wmic-format create_time strings keep compatibility with legacy rows.

Test isolation: set MF_RUN_ROOT to a scaffold root; every path is derived lazily from
it, so the real dispatcher/heartbeat code can run against fixtures.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import time
from pathlib import Path

import psutil
from filelock import FileLock, Timeout


# ---------------------------------------------------------------- paths
def run_root() -> Path:
    env = os.environ.get("MF_RUN_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[2]  # RUN/manager/tools -> RUN


def manager_dir() -> Path:
    return run_root() / "manager"


def locks_dir() -> Path:
    return manager_dir() / "locks"


def leases_dir() -> Path:
    return manager_dir() / "leases"


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------- io helpers
def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def atomic_write_json(path, obj, indent=2) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp%d" % os.getpid())
    tmp.write_text(json.dumps(obj, indent=indent, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return str(path)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def read_tail(path, nbytes=200_000) -> str:
    try:
        with open(path, "rb") as fh:
            try:
                fh.seek(-nbytes, os.SEEK_END)
            except OSError:
                pass
            return fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------- identity (psutil)
def wmic_like(create_epoch: float) -> str:
    """psutil create_time -> wmic CreationDate format 'YYYYMMDDHHMMSS.ffffff+HHMM' (local)."""
    lt = time.localtime(create_epoch)
    frac = create_epoch - int(create_epoch)
    micros = int(round(frac * 1_000_000))
    if micros >= 1_000_000:
        micros = 999_999
    offs_secs = -(time.timezone if not time.daylight else time.altzone)
    offs_min = int(offs_secs // 60)
    sign = "+" if offs_min >= 0 else "-"
    return time.strftime("%Y%m%d%H%M%S", lt) + (".%06d" % micros) + ("%s%03d" % (sign, abs(offs_min)))


def pid_facts(pid):
    """-> {'name','created','create_epoch','cmd'} | {} gone | None UNKNOWN (AccessDenied/error)."""
    if not pid:
        return {}
    try:
        p = psutil.Process(int(pid))
        with p.oneshot():
            ct = p.create_time()
            nm = p.name()
            try:
                cmd = " ".join(p.cmdline())
            except Exception:  # noqa: BLE001
                cmd = ""
        return {"name": nm, "created": wmic_like(ct), "create_epoch": ct, "cmd": cmd}
    except psutil.NoSuchProcess:
        return {}
    except (psutil.AccessDenied, psutil.ZombieProcess, Exception):  # noqa: BLE001
        return None


def _created_matches(a: str, b: str) -> bool:
    if not a or not b:
        return True  # nothing recorded to compare
    if a == b:
        return True
    # tolerate sub-2ms fraction read differences between wmic and psutil for the same instant
    try:
        da, fa = a.split(".", 1)
        db, fb = b.split(".", 1)
        fa6 = int(fa[:6]) if fa[:6].isdigit() else None
        fb6 = int(fb[:6]) if fb[:6].isdigit() else None
        if da[:14] == db[:14] and fa6 is not None and fb6 is not None and abs(fa6 - fb6) <= 2000:
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


def identity_alive(pid, created=None, name=None):
    """True iff same pid AND created(±2ms) AND name. False gone. None UNKNOWN."""
    f = pid_facts(pid)
    if f is None:
        return None
    if not f:
        return False
    if created and not _created_matches(str(created), f.get("created", "")):
        return False
    if name and f.get("name", "").lower() != str(name).lower():
        return False
    return True


# ---------------------------------------------------------------- controller lock
def _lock_paths():
    return locks_dir() / "controller.lock", locks_dir() / "controller.lock.meta.json"


def acquire_controller_lock(owner_sid: str, note: str = "", timeout: float = 0.0, poll: float = 0.05):
    """(lock, meta) on success; (None, refusal-detail) when another LIVE controller holds it.

    A dead holder (identity check False) is superseded via break_lock; UNKNOWN holder
    is NOT superseded (fail closed).
    """
    lp, mp = _lock_paths()
    lp.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lp), timeout=timeout, poll_interval=max(poll, 0.05))
    try:
        lock.acquire()
    except Timeout:
        meta = read_json(mp, default={}) or {}
        st = identity_alive(meta.get("pid"), meta.get("created"), meta.get("name"))
        if st is False:
            try:
                lock.break_lock()
                lock.acquire(timeout=5)
            except Exception as e:  # noqa: BLE001
                return None, {"held_by": meta, "holder_state": "DEAD_SupersedeFailed", "error": str(e)}
        else:
            return None, {"held_by": meta, "holder_state": "ALIVE" if st else "UNKNOWN"}
    me = psutil.Process(os.getpid())
    meta = {"owner_sid": owner_sid, "pid": os.getpid(), "created": wmic_like(me.create_time()),
            "name": me.name(), "acquired_utc": now_utc(), "note": note, "run": str(run_root())}
    atomic_write_json(mp, meta)
    return lock, meta


def release_controller_lock(lock, outcome=None) -> None:
    try:
        _lp, mp = _lock_paths()
        meta = read_json(mp, default={}) or {}
        meta["released_utc"] = now_utc()
        if outcome is not None:
            meta["release_outcome"] = outcome
        atomic_write_json(mp, meta)
    except Exception:  # noqa: BLE001
        pass
    try:
        lock.release()
    except Exception:  # noqa: BLE001
        pass


def controller_status() -> dict:
    lp, mp = _lock_paths()
    out = {"lock_file_exists": lp.exists(), "meta": None, "holder": None}
    meta = read_json(mp, default=None)
    if meta is not None:
        out["meta"] = meta
        if not meta.get("released_utc"):
            st = identity_alive(meta.get("pid"), meta.get("created"), meta.get("name"))
            out["holder"] = "ALIVE" if st else ("UNKNOWN" if st is None else "DEAD")
    return out


# ---------------------------------------------------------------- GPU lease
# R5 §4.2: render-side runner detection. Match the REAL spawn shapes:
#   (A) native executable  (argv0 basename e.g. ebsynth.exe)
#   (B) interpreter + script (python -B .../sam2_masks.py, video_blend.py, r4_build*.py, ...)
# The old '-B + r4_build only' substring filter missed native exes and every other script
# (fresh review probe: ebsynth / video_blend / sam2 all read as quiet). Whole-cmdline
# substring matching is NOT safe: the LLM child carries the packet text in its argv, so
# only basenames of executable-ish argv items are considered.
RUNNER_PATTERNS = ("ebsynth", "video_blend", "r4_build", "r4_render", "render_run",
                   "wan_run", "p4_wan_run", "sam2", "co-tracker", "cotracker",
                   "gmflow", "rerender", "vace", "propainter", "inpaint")
RUNNER_EXCLUDES = ("dispatch_long", "heartbeat_long", "invocation_runtime", "probe_",
                   "terminal_contract", "test_")
_EXEC_EXTS = (".py", ".exe", ".bat", ".cmd", ".pyd")


def _runner_hit(cmdline):
    """Return a description when this process is a render-side runner, else None."""
    if not cmdline:
        return None
    toks = [str(t) for t in cmdline if t is not None]
    if not toks:
        return None
    import os as _os
    prog = _os.path.basename(toks[0]).lower()
    if any(x in prog for x in RUNNER_EXCLUDES):
        return None
    for w in RUNNER_PATTERNS:  # (A) native executable
        if w in prog:
            return "native %s" % prog
    if "python" in prog:  # (B) interpreter + script; never the packet-text argv item
        for t in toks[1:]:
            if len(t) > 400 or "\n" in t or "\r" in t:
                continue
            base = _os.path.basename(t).lower()
            if not base.endswith(_EXEC_EXTS):
                continue
            if any(x in base for x in RUNNER_EXCLUDES):
                continue
            for w in RUNNER_PATTERNS:
                if w in base:
                    return "script %s" % base
    return None


def probe_render_quiet(timeout=6, watch=None):
    """(quiet|None, detail). False when the Comfy queue is busy OR a render-side runner
    process exists (any spawn shape). True only when both are verified quiet.
    None = probe UNKNOWN (callers must fail closed, never read as 'quiet')."""
    watch = tuple(watch) if watch else RUNNER_PATTERNS
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=timeout) as r:
            q = json.loads(r.read().decode())
        if q.get("queue_running") or q.get("queue_pending"):
            return False, "comfy queue active"
    except Exception as e:  # noqa: BLE001
        return None, "queue probe failed: %s" % type(e).__name__
    try:
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                info = p.info or {}
                cl = info.get("cmdline") or []
            except Exception:  # noqa: BLE001
                continue
            hit = _runner_hit(cl)
            if hit:
                return False, "render runner present (%s)" % hit
        return True, "no queue job, no runner process"
    except Exception:  # noqa: BLE001
        return None, "process probe failed"


def lease_acquire(invocation_id, job, owner_sid, children, extra=None) -> dict:
    rec = {"run": run_root().name, "run_path": str(run_root()), "owner_sid": owner_sid,
           "invocation_id": invocation_id, "job": job, "acquired_utc": now_utc(),
           "status": "ACTIVE", "detached": False, "children": children,
           "released_utc": None, "release_attempts": []}
    if extra:
        rec.update(extra)
    atomic_write_json(leases_dir() / ("gpu_lease.%s.json" % invocation_id), rec)
    return rec


def lease_release_if_children_gone(invocation_id, context="controller_exit") -> dict:
    """Release ONLY when every child identity is gone and render probe is quiet.

    A detached child / unknown probe / active queue keeps the lease ACTIVE with
    detached=true -- controller exit must never free a busy GPU lease.
    """
    lp = leases_dir() / ("gpu_lease.%s.json" % invocation_id)
    rec = read_json(lp, default=None)
    if rec is None:
        return {"released": False, "reason": "no lease file"}
    if rec.get("status") != "ACTIVE":
        return {"released": False, "reason": "already %s" % rec.get("status")}
    states = []
    for c in rec.get("children", []):
        st = identity_alive(c.get("pid"), c.get("created"), c.get("name"))
        states.append({"pid": c.get("pid"), "state": "ALIVE" if st else ("UNKNOWN" if st is None else "DEAD")})
    q, qdetail = probe_render_quiet()
    attempt = {"at_utc": now_utc(), "context": context, "children": states,
               "render_probe": {"quiet": q, "detail": qdetail}}
    rec.setdefault("release_attempts", []).append(attempt)
    if any(s["state"] == "ALIVE" for s in states):
        rec["detached"] = True
        rec["detached_note"] = "child detached still running at %s" % context
        atomic_write_json(lp, rec)
        return {"released": False, "reason": "child alive", "children": states}
    if any(s["state"] == "UNKNOWN" for s in states):
        rec["detached"] = True
        rec["detached_note"] = "child state UNKNOWN at %s (fail closed)" % context
        atomic_write_json(lp, rec)
        return {"released": False, "reason": "child state UNKNOWN", "children": states}
    if q is None:
        rec["detached"] = True
        rec["detached_note"] = "render probe unknown at %s (fail closed)" % context
        atomic_write_json(lp, rec)
        return {"released": False, "reason": "render probe unknown", "detail": qdetail}
    if q is False:
        rec["detached"] = True
        rec["detached_note"] = "render runner/queue active at %s" % context
        atomic_write_json(lp, rec)
        return {"released": False, "reason": "render active", "detail": qdetail}
    rec["status"] = "RELEASED"
    rec["released_utc"] = now_utc()
    rec["release_reason"] = qdetail
    atomic_write_json(lp, rec)
    return {"released": True, "detail": qdetail, "children": states}


def leases_status() -> list:
    out = []
    d = leases_dir()
    if not d.is_dir():
        return out
    for f in sorted(d.glob("gpu_lease.*.json")):
        rec = read_json(f, default=None)
        if not isinstance(rec, dict) or rec.get("status") != "ACTIVE":
            continue
        ch = []
        for c in rec.get("children", []):
            st = identity_alive(c.get("pid"), c.get("created"), c.get("name"))
            ch.append({"pid": c.get("pid"), "state": "ALIVE" if st else ("UNKNOWN" if st is None else "DEAD")})
        out.append({"file": f.name, "invocation_id": rec.get("invocation_id"), "job": rec.get("job"),
                    "owner_sid": rec.get("owner_sid"), "detached": rec.get("detached", False), "children": ch})
    return out


# ---------------------------------------------------------------- descendants + lease barrier
def descendants_of(root_pids, max_depth=4):
    """Exact recursive descendants (pid + create_time + name) of root_pids.
    -> (list, None) on success; (None, reason) when the probe is unavailable (fail closed:
    callers must treat it as UNKNOWN, never as 'no children')."""
    roots = [int(p) for p in (root_pids or []) if p]
    if not roots:
        return [], None
    try:
        table = {}
        for p in psutil.process_iter():
            try:
                table[p.pid] = p.ppid()
            except Exception:  # noqa: BLE001
                continue
    except Exception as e:  # noqa: BLE001
        return None, "process_iter failed: %s" % type(e).__name__
    frontier = list(roots)
    seen = set(roots)
    out = []
    depth = 0
    while frontier and depth < max_depth:
        depth += 1
        nxt = [pid for pid, ppid in table.items() if ppid in frontier and pid not in seen]
        for pid in nxt:
            seen.add(pid)
        for pid in nxt:
            f = pid_facts(pid)
            if isinstance(f, dict) and f:
                out.append({"pid": pid, "created": f.get("created"), "name": f.get("name", "")})
        frontier = nxt
    return out, None


def lease_reserve(invocation_id, owner_sid, job, launcher_identity=None) -> dict:
    """R5 §4.1 barrier: reserve GPU ownership BEFORE Popen. status=RESERVED is a live
    claim -- reconcile_gpu_leases refuses to proceed while a reservation with a live
    launcher (or an unverifiable one) exists, so a second controller can never spawn
    a twin child even if it never saw the filelock."""
    rec = {"run": run_root().name, "run_path": str(run_root()), "owner_sid": owner_sid,
           "invocation_id": invocation_id, "job": job, "reserved_utc": now_utc(),
           "status": "RESERVED", "detached": False, "children": [],
           "launcher": launcher_identity or {},
           "released_utc": None, "release_attempts": []}
    atomic_write_json(leases_dir() / ("gpu_lease.%s.json" % invocation_id), rec)
    return rec


def lease_promote(invocation_id, children=None, extra=None) -> dict:
    """RESERVED -> ACTIVE with the exact child identities recorded at/after spawn.
    New identities are MERGED (detached descendants discovered later are kept)."""
    lp = leases_dir() / ("gpu_lease.%s.json" % invocation_id)
    rec = read_json(lp, default=None)
    if rec is None:
        return {}
    rec["status"] = "ACTIVE"
    rec["acquired_utc"] = rec.get("acquired_utc") or now_utc()
    rec["released_utc"] = None
    merged = list(rec.get("children", []))
    have = {int(c.get("pid")) for c in merged if c.get("pid")}
    for c in (children or []):
        cpid = c.get("pid")
        if cpid and int(cpid) not in have:
            merged.append({"pid": cpid, "created": c.get("created"), "name": c.get("name", "")})
            have.add(int(cpid))
    rec["children"] = merged
    if extra:
        rec.update(extra)
    atomic_write_json(lp, rec)
    return rec


def lease_update_children(invocation_id, children=None, extra=None) -> dict:
    """Merge newly observed identities (e.g. detached render descendants found by a
    later scan) into an ACTIVE lease."""
    return lease_promote(invocation_id, children=children, extra=extra)


def lease_abandon(invocation_id, reason) -> dict:
    """A reservation with NO spawn evidence and a dead launcher -> RELEASED (adopted)."""
    lp = leases_dir() / ("gpu_lease.%s.json" % invocation_id)
    rec = read_json(lp, default=None)
    if rec is None:
        return {}
    rec["status"] = "RELEASED"
    rec["released_utc"] = now_utc()
    rec["release_reason"] = "abandoned: %s" % reason
    atomic_write_json(lp, rec)
    return rec


def _ledger_child_identities(launcher_pid):
    """child_spawned identities recorded in the dispatch ledger for a launcher pid."""
    out = []
    led = manager_dir() / "DISPATCH_LEDGER.jsonl"
    if not led.exists():
        return out
    for line in led.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if r.get("action") == "child_spawned" and r.get("launcher_pid") == launcher_pid:
            out.append({"pid": r.get("child_pid"), "created": r.get("child_created"),
                        "name": r.get("child_name")})
    return out


def _iso_age_s(ts):
    try:
        return time.time() - datetime.datetime.fromisoformat(str(ts)).timestamp()
    except Exception:  # noqa: BLE001
        return None


ADOPT_RESERVED_AFTER_S = 120


def reconcile_gpu_leases(requester_sid):
    """R5 §4.1/§4.2: under the controller mutex, reconcile EVERY non-released GPU lease
    (and its ledger lineage) before a new writer may spawn anything.

      * any child ALIVE                     -> BLOCK (live job; never start a twin)
      * any child / probe UNKNOWN           -> BLOCK (fail closed -> needs reconciliation)
      * RESERVED with live/unverifiable launcher, or recent -> BLOCK (spawn barrier)
      * ACTIVE / old-dead RESERVED, all children verified DEAD + render quiet
                                            -> ADOPT (release the stale claim with evidence)
    Returns {'ok': bool, 'blockers': [...], 'unknown': [...], 'adopted': [...]}.
    """
    out = {"ok": True, "blockers": [], "adopted": [], "unknown": []}
    d = leases_dir()
    if not d.is_dir():
        return out
    for f in sorted(d.glob("gpu_lease.*.json")):
        rec = read_json(f, default=None)
        if not isinstance(rec, dict):
            out["unknown"].append({"file": f.name, "reason": "unreadable lease record"})
            out["ok"] = False
            continue
        if rec.get("status") == "RELEASED":
            continue
        inv = rec.get("invocation_id") or f.stem
        cands = list(rec.get("children", []))
        launcher = rec.get("launcher") or {}
        lpid = launcher.get("pid") or rec.get("launcher_pid")
        if lpid:
            cands = cands + _ledger_child_identities(lpid)
        states = []
        for c in cands:
            st = identity_alive(c.get("pid"), c.get("created"), c.get("name"))
            states.append({"pid": c.get("pid"), "created": c.get("created"),
                           "name": c.get("name"),
                           "state": "ALIVE" if st else ("UNKNOWN" if st is None else "DEAD")})
        if any(s["state"] == "ALIVE" for s in states):
            out["blockers"].append({"invocation_id": inv, "file": f.name, "reason": "child ALIVE",
                                    "children": states})
            out["ok"] = False
            continue
        if any(s["state"] == "UNKNOWN" for s in states):
            out["unknown"].append({"invocation_id": inv, "file": f.name,
                                   "reason": "child state UNKNOWN (fail closed)", "children": states})
            out["ok"] = False
            continue
        if rec.get("status") == "RESERVED":
            lst = identity_alive(lpid, launcher.get("created"), launcher.get("name")) if lpid else None
            if lst is None:
                out["unknown"].append({"invocation_id": inv, "file": f.name,
                                       "reason": "reservation launcher UNKNOWN (fail closed)"})
                out["ok"] = False
                continue
            if lst is True:
                out["blockers"].append({"invocation_id": inv, "file": f.name,
                                        "reason": "reservation in flight (launcher ALIVE)"})
                out["ok"] = False
                continue
            age = _iso_age_s(rec.get("reserved_utc"))
            if age is None or age < ADOPT_RESERVED_AFTER_S:
                out["blockers"].append({"invocation_id": inv, "file": f.name,
                                        "reason": "reservation recent/unverifiable (age=%s s)" % age})
                out["ok"] = False
                continue
        q, detail = probe_render_quiet()
        if q is None:
            out["unknown"].append({"invocation_id": inv, "file": f.name,
                                   "reason": "render probe unknown (fail closed)", "detail": detail})
            out["ok"] = False
            continue
        if q is False:
            out["blockers"].append({"invocation_id": inv, "file": f.name,
                                    "reason": "render active", "detail": detail})
            out["ok"] = False
            continue
        rec["status"] = "RELEASED"
        rec["released_utc"] = now_utc()
        rec["release_reason"] = "adopted by %s: children DEAD, render quiet" % requester_sid
        rec["adopted_by"] = requester_sid
        atomic_write_json(f, rec)
        out["adopted"].append({"invocation_id": inv, "file": f.name, "children": states,
                               "detail": detail})
    return out


# ---------------------------------------------------------------- terminal helpers
def log_has_infra_error(log_path) -> bool:
    """True on hard batch-failure text in the log tail (fail closed to reconciliation)."""
    tail = read_tail(log_path).lower()
    markers = ("api call failed after 3 retries",)
    return any(m in tail for m in markers)


def find_dispatch_row(invocation_id: str):
    """The immutable dispatch row for an invocation (append-only ledger). None if absent."""
    led = manager_dir() / "DISPATCH_LEDGER.jsonl"
    row = None
    if led.exists():
        for line in led.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if r.get("action") == "dispatch" and r.get("invocation_id") == invocation_id:
                row = r
    return row


def expected_binding_from_row(row: dict) -> dict:
    return {"run_id": row["run_id"], "task_id": row["task_id"], "revision": row["revision"],
            "owner_sid": row["owner_sid"], "invocation_id": row["invocation_id"],
            "packet_sha256": row["packet_file_sha256"]}
