#!/usr/bin/env bash
# Live-log watcher: keeps a background Hermes task log visible in the user's MAIN project folder.
# Usage: edit SRC/DST_DIR for the task, then: bash live-log-watcher.sh  (run in background, long-lived)
# Why: Tee-Object logs are UTF-16LE; the preview pane needs a UTF-8 tail file that refreshes.
SRC="/c/Users/Admin/MotionForge2D-worktrees/s06-t01-review/output/s06-t05-deepseek-hermes.log"
DST_DIR="/c/Users/Admin/MotionForge2D/output/hermes-task-logs"
while true; do
  if [ -f "$SRC" ]; then
    cp -f "$SRC" "$DST_DIR/$(basename "$SRC")" 2>/dev/null
    iconv -f UTF-16LE -t UTF-8 "$SRC" 2>/dev/null | tail -200 > "$DST_DIR/$(basename "$SRC" .log)-LIVE.txt" 2>/dev/null || true
  fi
  sleep 10
done
