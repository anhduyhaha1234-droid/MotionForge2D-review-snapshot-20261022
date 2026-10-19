#!/usr/bin/env bash
# MF-V1-VIDEO14B — CPU-only server probe on a task-local port (8210).
# No model is loaded and no inference is submitted: this only proves the pinned
# ComfyUI commit boots and registers the video-node classes on this machine.
set -u
RT="C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b"
mkdir -p "$RT/logs"
cd "$RT/ComfyUI" || exit 1
exec >"$RT/logs/server_cpu_probe.log" 2>&1
echo "PROBE_START $(date -u +%FT%TZ) cwd=$(pwd)"
echo "ARGV: $RT/venv/Scripts/python.exe main.py --cpu --listen 127.0.0.1 --port 8210 --base-directory $RT"
echo "BASH_PID=$$"
exec "$RT/venv/Scripts/python.exe" main.py --cpu --listen 127.0.0.1 --port 8210 --base-directory "$RT"
