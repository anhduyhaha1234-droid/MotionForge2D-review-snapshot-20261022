#!/bin/bash
# MotionForge 2D — Run Vertical Spike
# Usage: bash scripts/run_spike.sh [video_path] [replacement_png] [scene_index]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate venv if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -f "$PROJECT_ROOT/.venv/Scripts/activate" ]; then
    source "$PROJECT_ROOT/.venv/Scripts/activate"
fi

# Arguments
VIDEO="${1:-$PROJECT_ROOT/examples/test_video.mp4}"
REPLACEMENT="${2:-}"
SCENE="${3:-0}"
OUTPUT_DIR="$PROJECT_ROOT/output"
BACKEND="contour"  # Use "sam2" for GPU segmentation

echo "=== MotionForge 2D — Vertical Spike ==="
echo "Video: $VIDEO"
echo "Replacement: ${REPLACEMENT:-none (original will be rendered)}"
echo "Scene: $SCENE"
echo "Backend: $BACKEND"
echo "Output: $OUTPUT_DIR"
echo ""

# Check inputs
if [ ! -f "$VIDEO" ]; then
    echo "ERROR: Video file not found: $VIDEO"
    echo ""
    echo "Usage: bash scripts/run_spike.sh <video.mp4> [replacement.png] [scene_index]"
    echo ""
    echo "Provide a short MP4 video file as the first argument."
    exit 1
fi

# Create a test video if using default path and it doesn't exist
if [ "$VIDEO" = "$PROJECT_ROOT/examples/test_video.mp4" ] && [ ! -f "$VIDEO" ]; then
    echo "Creating test video..."
    mkdir -p "$PROJECT_ROOT/examples"
    ffmpeg -y \
        -f lavfi -i "testsrc=duration=3:size=320x240:rate=30" \
        -f lavfi -i "sine=frequency=440:duration=3" \
        -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p \
        -c:a aac -b:a 128k -shortest \
        "$VIDEO" 2>/dev/null
    echo "Test video created: $VIDEO"
fi

# Create test replacement PNG if needed
if [ -z "$REPLACEMENT" ]; then
    REPLACEMENT="$PROJECT_ROOT/examples/replacement.png"
    if [ ! -f "$REPLACEMENT" ]; then
        echo "Creating test replacement PNG..."
        python -c "
import cv2, numpy as np
img = np.zeros((100, 100, 4), dtype=np.uint8)
cv2.circle(img, (50, 50), 40, (255, 200, 0, 220), -1)
cv2.rectangle(img, (30, 30), (70, 70), (0, 100, 255, 180), -1)
cv2.imwrite('$REPLACEMENT', img)
print('Created: $REPLACEMENT')
"
    fi
fi

# Run the spike
echo ""
echo "Running spike pipeline..."
cd "$PROJECT_ROOT"

python -m app.spike_runner \
    --video "$VIDEO" \
    --replacement "$REPLACEMENT" \
    --scene "$SCENE" \
    --backend "$BACKEND" \
    --output-dir "$OUTPUT_DIR" \
    --name "spike_run"

echo ""
echo "=== Spike Complete ==="
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Key outputs:"
echo "  Project JSON: $OUTPUT_DIR/project.json"
echo "  Motion data:  $OUTPUT_DIR/motion_data.json"
echo "  Benchmark:    $OUTPUT_DIR/benchmark.json"
echo "  Debug overlays: $OUTPUT_DIR/debug/"
echo "  Masks:        $OUTPUT_DIR/masks/"
echo "  Renders:      $OUTPUT_DIR/renders/"
