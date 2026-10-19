#!/bin/bash
# MotionForge 2D — Setup Script
# Installs all dependencies and prepares the environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== MotionForge 2D Setup ==="
echo "Project root: $PROJECT_ROOT"

# Check Python version
PYTHON=${PYTHON:-python3}
PYTHON_VERSION=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
echo "Python version: $PYTHON_VERSION"

if ! $PYTHON -c "import sys; assert sys.version_info >= (3, 11)" 2>/dev/null; then
    echo "ERROR: Python 3.11+ is required"
    exit 1
fi

# Check FFmpeg — try common locations
FFMPEG=""
for candidate in \
    "$(command -v ffmpeg 2>/dev/null)" \
    "/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe" \
    "/c/ffmpeg/bin/ffmpeg.exe" \
    "/usr/bin/ffmpeg"; do
    if [ -x "$candidate" ] || command -v "$candidate" &>/dev/null; then
        FFMPEG="$candidate"
        break
    fi
done

if [ -z "$FFMPEG" ]; then
    echo "ERROR: ffmpeg not found. Please install FFmpeg first."
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: winget install Gyan.FFmpeg"
    exit 1
fi

# Add FFmpeg's directory to PATH if not already there
FFMPEG_DIR="$(dirname "$(realpath "$FFMPEG" 2>/dev/null || echo "$FFMPEG")")"
case ":$PATH:" in
    *":$FFMPEG_DIR:"*) ;;
    *) export PATH="$PATH:$FFMPEG_DIR" ;;
esac

# Also check WinGet Links dir
WINGET_LINKS="/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"
if [ -d "$WINGET_LINKS" ]; then
    case ":$PATH:" in
        *":$WINGET_LINKS:"*) ;;
        *) export PATH="$PATH:$WINGET_LINKS" ;;
    esac
fi

echo "FFmpeg: $(ffmpeg -version 2>&1 | head -1)"
echo "ffprobe: $(ffprobe -version 2>&1 | head -1)"

# Create virtual environment
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate"

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA (adjust cu124 to your CUDA version)
echo "Installing PyTorch with CUDA support..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# Install project dependencies
echo "Installing project dependencies..."
cd "$PROJECT_ROOT"
pip install -e ".[dev]"

# Install SAM 2 from source
echo "Installing SAM 2..."
pip install git+https://github.com/facebookresearch/sam2.git

# Download models
echo "Downloading SAM 2.1 model checkpoints..."
bash "$SCRIPT_DIR/download_models.sh"

# Verify installation
echo ""
echo "=== Verification ==="
$PYTHON -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
$PYTHON -c "import cv2; print(f'OpenCV {cv2.__version__}')"
$PYTHON -c "import sam2; print('SAM 2 OK')"
$PYTHON -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
$PYTHON -c "import scenedetect; print(f'PySceneDetect {scenedetect.__version__}')"
ffmpeg -version 2>&1 | head -1

echo ""
echo "=== Setup Complete ==="
echo "Activate venv: source .venv/bin/activate"
echo "Run spike: bash scripts/run_spike.sh"
