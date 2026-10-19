#!/bin/bash
# MotionForge 2D — Download SAM 2.1 Model Checkpoints
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_ROOT/models_checkpoints"

mkdir -p "$MODELS_DIR"

echo "=== Downloading SAM 2.1 Model Checkpoints ==="

# SAM 2.1 Hiera Large (recommended for best quality)
MODEL_URL="https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
MODEL_FILE="$MODELS_DIR/sam2.1_hiera_large.pt"

if [ -f "$MODEL_FILE" ]; then
    echo "Checkpoint already exists: $MODEL_FILE"
    echo "Size: $(du -h "$MODEL_FILE" | cut -f1)"
else
    echo "Downloading sam2.1_hiera_large.pt..."
    if command -v wget &>/dev/null; then
        wget -O "$MODEL_FILE" "$MODEL_URL"
    elif command -v curl &>/dev/null; then
        curl -L -o "$MODEL_FILE" "$MODEL_URL"
    else
        echo "ERROR: Neither wget nor curl found. Please install one."
        exit 1
    fi
    echo "Downloaded: $(du -h "$MODEL_FILE" | cut -f1)"
fi

# Verify file exists and has reasonable size (> 100MB)
FILE_SIZE=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null || echo "0")
if [ "$FILE_SIZE" -lt 100000000 ]; then
    echo "WARNING: Checkpoint file seems too small ($FILE_SIZE bytes). Download may have failed."
    echo "Try downloading manually from: $MODEL_URL"
    exit 1
fi

echo ""
echo "=== Model Download Complete ==="
echo "Checkpoint: $MODEL_FILE"
echo "Size: $(du -h "$MODEL_FILE" | cut -f1)"
echo ""
echo "This checkpoint is released under the Apache 2.0 license by Meta AI."
echo "See: https://github.com/facebookresearch/sam2"
