#!/usr/bin/env bash
# Manager-side LIVENESS watcher for S08-T02-C1 (READ-ONLY — never writes).
# Fires when: (a) log stable (no growth) for STABLE_EXIT seconds → candidate exit,
#             (b) death marker "Resume this session with" appears in tail,
#             (c) hard cap CAP seconds → writer still active, re-evaluate.
LOG=/c/Users/Admin/MotionForge2D-worktrees/s08-integration/output/s08-t02-c1-hermes.log
START=$(date +%s)
CAP=7200
STABLE_EXIT=360
POLL=20
last_size=-1
stable_since=$START

while true; do
  now=$(date +%s)
  elapsed=$((now - START))
  if [ "$elapsed" -ge "$CAP" ]; then
    echo "WATCHER_TIMEOUT: writer still active after ${CAP}s — bounded check required"
    exit 3
  fi
  size=0; mtime=0
  if [ -f "$LOG" ]; then
    size=$(stat -c %s "$LOG")
    mtime=$(stat -c %Y "$LOG")
  fi
  if [ "$size" -ne "$last_size" ]; then
    last_size=$size
    stable_since=$now
  fi
  if [ $((now - stable_since)) -ge "$STABLE_EXIT" ]; then
    echo "LOG_STABLE: size=${size}B last_mtime=$(date -d @"$mtime" '+%H:%M:%S') no_growth=${STABLE_EXIT}s — CHECK writer exit / REPORT status"
    exit 0
  fi
  if tr -d '\0' < "$LOG" 2>/dev/null | tail -c 3000 | grep -q "Resume this session with"; then
    echo "DEATH_MARKER: writer session ended — size=${size}B mtime=$(date -d @"$mtime" '+%H:%M:%S')"
    exit 0
  fi
  sleep "$POLL"
done
