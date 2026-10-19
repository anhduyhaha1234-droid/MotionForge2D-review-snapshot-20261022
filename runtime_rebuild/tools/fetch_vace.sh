#!/usr/bin/env bash
# MF-V1-VIDEO14B — resumable fetch for candidate 2 (Wan2.1 VACE 14B) official Comfy set.
# Pinned revision: 617a7633e636506f850e043bc4605f290a466a8e (Comfy-Org/Wan_2.1_ComfyUI_repackaged, apache-2.0)
set -u
REPO="Comfy-Org/Wan_2.1_ComfyUI_repackaged"
REV="617a7633e636506f850e043bc4605f290a466a8e"
RT="C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b"
LOG="$RT/logs/fetch_vace.log"
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

fetch "split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors" "$RT/models/diffusion_models/wan2.1_vace_14B_fp16.safetensors"
fetch "split_files/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors" "$RT/models/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors"
fetch "split_files/text_encoders/umt5_xxl_fp16.safetensors"           "$RT/models/text_encoders/umt5_xxl_fp16.safetensors"
fetch "split_files/vae/wan_2.1_vae.safetensors"                        "$RT/models/vae/wan_2.1_vae.safetensors"
echo "=== $(date -u +%FT%TZ) FETCH_SET_DONE" >>"$LOG"
