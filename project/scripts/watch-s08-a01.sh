#!/usr/bin/env bash
# Live log watcher for S08-A01 (Source-Locked 2D Role Taxonomy Bridge writer).
SRC="/c/Users/Admin/MotionForge2D-worktrees/s08-integration/output/s08-a01-hermes.log"
DST_DIR="/c/Users/Admin/MotionForge2D/output/hermes-task-logs"
mkdir -p "$DST_DIR"
while true; do
  if [ -f "$SRC" ]; then
    cp -f "$SRC" "$DST_DIR/$(basename "$SRC")" 2>/dev/null
    iconv -f UTF-16LE -t UTF-8 "$SRC" 2>/dev/null | tail -200 > "$DST_DIR/$(basename "$SRC" .log)-LIVE.txt" 2>/dev/null || true
  fi
  sleep 10
done
