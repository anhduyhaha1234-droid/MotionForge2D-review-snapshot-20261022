"""Generic lane-watchdog template for PM-gated correction sprints.

Derived from the S11-C1 watchdog (2026-09-04). Copy to
%LocalAppData%/hermes/scripts/<sprint>_watchdog.py and configure LANES.

Behavior: read-only health check over N resumed worker lanes. A lane is
STALLED when BOTH hold for > STALL_S: dispatch.log mtime frozen AND owner
session quiet/absent in `hermes sessions list`. On stall, sends ONE short
status-demand nudge into the EXACT owner session via DETACHED
`hermes chat --resume` (same session, pinned model — never a new worker),
max MAX_NUDGE_PER_TIP nudges per git tip. SILENT (no stdout) when all lanes
healthy — designed for cron --no-agent mode (empty stdout = silent).

Scheduling: cron `*/10` no-agent + --deliver origin (--workdir = canonical
worktree). If the Hermes gateway is OFF, cron never fires — ALSO start a
`while true; sleep 570; python <script>` background loop as fallback and
kill it once the gateway is up (else double-nudge).

State: <evidence>/<sprint>/manager/watchdog_state.json (+ watchdog.log).
Never touches git state, never dispatches new sessions.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# ---- CONFIGURE PER SPRINT ----
EV = Path("C:/Users/Admin/MotionForge2D-evidence/<sprint>")
WT = Path("C:/Users/Admin/MotionForge2D-worktrees")
HERMES = "C:/Users/Admin/AppData/Local/Programs/Python/Python311/Scripts/hermes.exe"
NUDGE_MODEL = "ocgfree/muse-spark-1.3-contributor-free"  # pin: zero fallback
NUDGE_PROVIDER = "custom"
STALL_S = 30 * 60
MAX_NUDGE_PER_TIP = 2
LANES = [
    # {"lane": "C1-A", "task": "S11-T03G", "sid": "20260903_170546_0d42f6",
    #  "wt": "s11-t03g-0903w8", "dlog": "lanes/c1a-t03g/dispatch.log"},
    # Optional: {"done_tip": "<7+ hex>"} marks lane DONE_SUBMITTED when the
    # tip matches; TIP CHANGED after submit => manager review needed.
]
# ------------------------------

STATE = EV / "manager" / "watchdog_state.json"
LOG = EV / "manager" / "watchdog.log"
DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NO_WINDOW


def run(args, cwd=None, timeout=60):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 99, f"ERR:{e}"


def git_tip(wt):
    code, out = run(["git", "log", "--oneline", "-1"], cwd=str(WT / wt))
    return out.strip().split("\n")[0] if code == 0 and out.strip() else "GIT_FAIL"


def session_quiet_minutes(sid):
    """Minutes since session last active; -1 = unknown, -2 = absent."""
    code, out = run([HERMES, "sessions", "list", "--limit", "60"], timeout=90)
    if code != 0:
        return -1
    for line in out.splitlines():
        if sid in line:
            low = line.lower()
            if "just now" in low or "second" in low:
                return 0
            m = re.search(r"(\d+)\s*m\b", low)
            if m:
                return int(m.group(1))
            m = re.search(r"(\d+)\s*h", low)
            if m:
                return int(m.group(1)) * 60
            return -1
    return -2


def lane_terminal(dlog):
    """Worker terminal marker from the dispatch log — check BEFORE stall logic.

    S11-C1 lesson (2026-09-04): judging lanes by log-silence + session-quiet
    alone misreads a SUBMITTED lane as STALLED (it goes quiet by design) and
    produced 2h of false-BLOCKED nudges. Ground truth is the worker's own
    terminal line, not silence. Returns (marker, detail), marker in
    {SUBMITTED, NEEDS_T04B, NONE}.
    """
    try:
        raw = (EV / dlog).read_bytes().decode("utf-8", "replace")
    except Exception:
        return ("NONE", "unreadable")
    term_lines = [ln for ln in raw.splitlines()
                  if re.match(r"^[\s*#+\->]*\*?\*?(TASK_SUBMITTED|NEEDS_T04B_PRODUCT_FIX|WATCHDOG-SIGNAL)\b", ln)
                  or ("WATCHDOG-SIGNAL" in ln and "TASK_SUBMITTED" in ln)]
    if any("NEEDS_T04B_PRODUCT_FIX" in ln for ln in term_lines):
        return ("NEEDS_T04B", term_lines[-1].strip()[:120])
    # TASK_SUBMITTED counts only with an EXIT=/NUDGE*_EXIT= trailer anywhere
    # (wrapper finished) — not a mid-log quote or REPORT citation.
    if any("TASK_SUBMITTED" in ln for ln in term_lines) and re.search(
            r"(EXIT|NUDGE\d?_EXIT)=\d+", raw):
        return ("SUBMITTED", term_lines[-1].strip()[:120])
    return ("NONE", raw.strip().splitlines()[-1][:120] if raw.strip() else "empty")


def main():
    (EV / "manager").mkdir(parents=True, exist_ok=True)
    try:
        state = json.loads(STATE.read_text())
    except Exception:
        state = {}
    now = time.time()
    actions = []
    for lane in LANES:
        key = lane["lane"]
        st = state.get(key, {})
        tip = git_tip(lane["wt"])
        try:
            log_age = now - (EV / lane["dlog"]).stat().st_mtime
        except Exception:
            log_age = -1
        st["tip"], st["log_age_s"] = tip, int(log_age)
        term, detail = lane_terminal(lane["dlog"])  # terminal-marker FIRST
        st["terminal"] = term
        if term == "SUBMITTED":
            if st.get("status") != "DONE_SUBMITTED":
                actions.append(f"{key}: DONE lane terminal SUBMITTED tip={tip[:40]}")
            st["status"] = "DONE_SUBMITTED"
            state[key] = st
            continue
        if term == "NEEDS_T04B":
            st["status"] = "NEEDS_T04B_PRODUCT_FIX"
            actions.append(f"{key}: NEEDS_T04B — open conditional lane ({detail})")
            state[key] = st
            continue
        if lane.get("done_tip"):
            ok = tip.startswith(lane["done_tip"][:7])
            st["status"] = "DONE_SUBMITTED" if ok else "DONE_TIP_CHANGED"
            if not ok:
                actions.append(f"{key}: TIP CHANGED after submit ({tip}) — review needed")
            state[key] = st
            continue
        quiet = session_quiet_minutes(lane["sid"])
        st["session_quiet_min"] = quiet
        if log_age > STALL_S and (quiet in (-2,) or quiet >= 30):
            nudges = st.get("nudges", {})
            n = nudges.get(tip, 0)
            if n < MAX_NUDGE_PER_TIP:
                msg = (f"Watchdog [{lane['lane']} {lane['task']}]: no signal "
                       f">30m (log {int(log_age)}s, quiet={quiet}m, tip {tip[:40]}). "
                       f"Reply status + ETA in one short message, then continue — do not stop.")
                nlog = EV / "manager" / f"nudge_{key}_{int(now)}.log"
                try:
                    with open(nlog, "w") as fh:
                        subprocess.Popen(
                            [HERMES, "chat", "--resume", lane["sid"],
                             "-m", NUDGE_MODEL, "--provider", NUDGE_PROVIDER,
                             "-q", msg, "-Q"],
                            stdout=fh, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL,
                            creationflags=DETACHED, close_fds=True)
                    nudges[tip] = n + 1
                    st["nudges"] = nudges
                    actions.append(f"{key}: STALL nudged (#{n + 1}) {lane['sid']}")
                except Exception as e:
                    actions.append(f"{key}: NUDGE_FAIL {e}")
            else:
                actions.append(f"{key}: STALL persists after {n} nudges — manager (BLOCKED?)")
                st["status"] = "STALLED_AFTER_NUDGES"
        else:
            st["status"] = "RUNNING"
        state[key] = st
    STATE.write_text(json.dumps(state, indent=1))
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
    with open(LOG, "a") as fh:
        fh.write(stamp + " " + ("OK " + json.dumps(
            {k: v.get("status") for k, v in state.items()}) if not actions
            else "ACTION " + " | ".join(actions)) + "\n")
    if actions:
        print(f"Watchdog {stamp}")
        for a in actions:
            print("- " + a)


if __name__ == "__main__":
    sys.exit(main())
