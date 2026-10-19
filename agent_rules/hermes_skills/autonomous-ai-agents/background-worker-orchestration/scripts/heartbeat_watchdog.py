"""Heartbeat watchdog for long-running manager/worker lanes.

Polls a configured glob list (logs + packet files) every POLL_SECS, printing
HEARTBEAT_OK lines while anything advances. Exits (and via
notify_on_complete wakes the agent) on:
  - STALL_ALERT      nothing advanced for > STALL_SECS (align with the
                     8-minute liveness-audit rule -> 480)
  - DONE manager_exited  the manager process vanished (finished or died)
  - TIMEOUT          hard self-expiry after MAX_LOOPS polls (~3h) = HEALTHY

Re-arm a fresh instance after every expiry notification. Only act on
STALL_ALERT / manager_exited.

Usage: python heartbeat_watchdog.py [optional_manager_pid]
Configure WORKTREE / WATCH_GLOBS for the current sprint before launching.
"""
import glob
import os
import subprocess
import sys
import time

WORKTREE = r"C:\Users\Admin\MotionForge2D-worktrees\s08-integration"
WATCH_GLOBS = [
    # manager lane evidence log
    os.path.join(WORKTREE, r"output\<sprint>-review\<run>\manager_session.log"),
    # worker lanes
    os.path.join(WORKTREE, r"output\<task-dir>\*.log"),
    # packet state
    os.path.join(WORKTREE, r"docs\pm\sessions\<TASK-ID>\*.md"),
]
STALL_SECS = 480          # 8 min, matches liveness audit rule
POLL_SECS = 60
MAX_LOOPS = 190           # ~3h10m then healthy self-expiry
# Optional: also require the lane's marker process to be ALIVE (not just log
# motion). Set LANE_MARKER to a unique string from the worker's command line
# (e.g. "TASK ID: S09-T03") and the watchdog exits DONE lane_exited when no
# matching python.exe remains AND the log is simultaneously frozen — this
# distinguishes "quiet death" (wrapper + child both gone, no EXIT= line) from
# a healthy worker inside one long reasoning call (log frozen but PID alive).
LANE_MARKER = ""


def lane_alive(marker):
    if not marker:
        return True
    try:
        out = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'",
             "get", "CommandLine"],
            capture_output=True, text=True, timeout=30)
        return marker in out.stdout
    except Exception:
        return True  # fail-open: never false-alarm on probe failure


def latest_mtime():
    newest, newest_path = 0.0, ""
    for g in WATCH_GLOBS:
        for p in glob.glob(g):
            try:
                m = os.path.getmtime(p)
                if m > newest:
                    newest, newest_path = m, p
            except OSError:
                pass
    return newest, newest_path


def pid_alive(pid):
    if not pid:
        return True  # no probe configured -> rely on mtime stall only
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue) -ne $null"],
            capture_output=True, text=True, timeout=30)
        return "True" in out.stdout
    except Exception:
        return True  # fail-open: never false-alarm on probe failure


def main():
    pid = sys.argv[1] if len(sys.argv) > 1 else None
    start, last_newest = time.time(), 0.0
    for _ in range(MAX_LOOPS):
        time.sleep(POLL_SECS)
        if not pid_alive(pid):
            print(f"DONE manager_exited at {time.strftime('%H:%M:%S')}")
            return
        newest, path = latest_mtime()
        if newest == 0.0:
            continue
        if newest > last_newest:
            last_newest = newest
            print(f"HEARTBEAT_OK t+{int(time.time()-start)}s "
                  f"newest={os.path.basename(path)} age={int(time.time()-newest)}s",
                  flush=True)
            continue
        idle = time.time() - newest
        if idle > STALL_SECS:
            if LANE_MARKER and not lane_alive(LANE_MARKER):
                print(f"DONE lane_exited (log idle {int(idle)}s, no process "
                      f"matching '{LANE_MARKER}') — treat as worker end, audit "
                      f"for SUBMITTED vs quiet-death")
                return
            print(f"STALL_ALERT no progress for {int(idle)}s, newest: {path}")
            return
    print("TIMEOUT watchdog reached max runtime")


if __name__ == "__main__":
    main()
