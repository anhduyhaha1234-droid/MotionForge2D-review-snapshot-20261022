#!/usr/bin/env bash
# MF-V1-VIDEO14B — isolate runtime venv + install ComfyUI v0.37.0 requirements (CPU-side only this wave).
# Nothing here touches the global python, CUDA toolkit, or the NVIDIA driver.
set -u
RT="C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b"
cd "$RT" || exit 1
python -m venv venv
./venv/Scripts/python.exe -V
./venv/Scripts/python.exe -m pip install --upgrade pip 2>&1 | tail -2
./venv/Scripts/python.exe -m pip install -r "$RT/ComfyUI/requirements.txt" 2>&1 | tail -25
echo "=== PIP_EXIT=$? ==="
./venv/Scripts/python.exe -m pip list 2>&1 > "$RT/logs/venv_pip_list.txt"
./venv/Scripts/python.exe -c "import torch,sys;print('torch',torch.__version__);print('cuda_available',torch.cuda.is_available());print('cuda_build',torch.version.cuda);print('sm_arch_list',torch.cuda.get_arch_list() if torch.cuda.is_available() else 'n/a')" 2>&1 | tee "$RT/logs/venv_torch_probe.txt"
echo "=== INSTALL_DONE ==="
