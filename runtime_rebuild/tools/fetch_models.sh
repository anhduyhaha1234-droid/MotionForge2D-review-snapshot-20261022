#!/usr/bin/env bash
# MF-V1-VIDEO14B — resumable model fetch for the pinned Wan-Animate-2 (Comfy-Org) release.
# Pinned revision: ed158470869ff31fa51cf56012dac33fb00f494b (repo lastModified 2026-08-17T05:28:11Z, license apache-2.0)
# Resume-safe: curl -C - ; a partial file is never treated as complete (validation happens in validate_models.py).
set -u
REPO="Comfy-Org/Wan-Animate-2"
REV="ed158470869ff31fa51cf56012dac33fb00f494b"
RT="C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b"
LOG="$RT/logs/fetch_models.log"
mkdir -p "$RT/logs"
BASE="https://huggingface.co/$REPO/resolve/$REV"

fetch () {
  local rel="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  echo "=== $(date -u +%FT%TZ) FETCH $rel -> $dest" >>"$LOG"
  curl -L --fail --retry 5 --retry-delay 10 --retry-all-errors -C - \
       --connect-timeout 30 --speed-time 120 --speed-limit 1024 \
       -o "$dest" "$BASE/$rel" >>"$LOG" 2>&1
  local rc=$?
  echo "=== $(date -u +%FT%TZ) EXIT $rc $rel size=$( [ -f "$dest" ] && stat -c %s "$dest" || echo 0 )" >>"$LOG"
  echo "$rc $rel" >>"$RT/logs/fetch_exit_codes.txt"
}

fetch "diffusion_models/wan_animate_2_int8_convrot.safetensors"      "$RT/models/diffusion_models/wan_animate_2_int8_convrot.safetensors"
fetch "text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"        "$RT/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
fetch "vae/Wan2_1_VAE_bf16.safetensors"                             "$RT/models/vae/Wan2_1_VAE_bf16.safetensors"
fetch "clip_vision/clip_vision_h.safetensors"                       "$RT/models/clip_vision/clip_vision_h.safetensors"
echo "=== $(date -u +%FT%TZ) FETCH_SET_DONE" >>"$LOG"
