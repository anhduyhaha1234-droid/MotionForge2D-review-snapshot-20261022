#!/usr/bin/env bash
# Live log watcher — copy per task; replace <SRC_LOG> and <TASK_TAG>.
# Syncs the worker log (UTF-16LE on Windows) into the user's desktop-watch
# folder every 10s, plus a UTF-8 LIVE tail file for preview/open_preview.
# Launch: terminal(background=true) — it is a daemon, no notify_on_complete.
SRC="<SRC_LOG>"            # e.g. /c/Users/Admin/.../output/s0X-tYY-hermes.log
DST_DIR="<DESKTOP_WATCH_DIR>"  # e.g. /c/Users/Admin/MotionForge2D/output/hermes-task-logs
TASK_TAG="<TASK_TAG>"      # e.g. s05-t03
while true; do
  if [ -f "$SRC" ]; then
    cp -f "$SRC" "$DST_DIR/${TASK_TAG}-hermes.log" 2>/dev/null
    iconv -f UTF-16LE -t UTF-8 "$SRC" 2>/dev/null | tail -300 > "$DST_DIR/${TASK_TAG}-LIVE.txt" 2>/dev/null || true
  fi
  sleep 10
done
