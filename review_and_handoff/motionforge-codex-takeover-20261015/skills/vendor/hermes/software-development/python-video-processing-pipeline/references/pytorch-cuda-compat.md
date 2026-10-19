# PyTorch CUDA Compatibility for New GPUs

## Problem

New NVIDIA GPU architectures may not be supported by the current stable PyTorch release. The error is silent until runtime:

```
RuntimeError: CUDA error: no kernel image is available for execution on the device
```

PyTorch also emits a warning:
```
UserWarning: <GPU> with CUDA capability sm_XXX is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_61 sm_70 sm_75 sm_80 sm_86 sm_90.
```

## Verified Compatibility Matrix (as of 2026-07)

| GPU Architecture | Compute Capability | Min PyTorch Version | CUDA Index URL | Verified |
|---|---|---|---|---|
| Ampere (RTX 30xx) | sm_86 | 1.10+ | `cu118` or `cu121` | — |
| Ada Lovelace (RTX 40xx) | sm_89 | 2.0+ | `cu121` or `cu124` | — |
| Hopper (H100) | sm_90 | 2.1+ | `cu121` or `cu124` | — |
| **Blackwell (RTX 50xx)** | **sm_120** | **2.11+** | **`cu128`** | ✅ RTX 5070, PyTorch 2.11.0+cu128, CUDA 12.8, driver 610.47 |

### Verified on RTX 5070

```
nvidia-smi: NVIDIA-SMI 610.47, CUDA UMD Version: 13.3
GPU: NVIDIA GeForce RTX 5070, 12227MiB VRAM
PyTorch: 2.11.0+cu128
torch.cuda.is_available(): True
torch.cuda.get_device_capability(0): (12, 0)
torch.ones(2, device='cuda') + 1: tensor([2., 2.], device='cuda:0')
```

**Note:** CUDA UMD version 13.3 (from nvidia-smi) is the driver-supported maximum. PyTorch cu128 bundles CUDA 12.8 runtime. These are compatible — the driver supports up to 13.3, and the runtime uses 12.8.

## Detection

```python
import torch
print(torch.cuda.get_device_capability(0))  # Returns (major, minor) e.g. (12, 0)
print(torch.cuda.get_device_name(0))
```

## Install Commands

```bash
# For Blackwell (RTX 5070, 5080, 5090) — requires cu128
pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu128

# For Ada Lovelace (RTX 40xx) — cu124 works
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# For older GPUs — cu118 or cu121
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**Critical:** Use `--force-reinstall` when switching CUDA versions. Without it, pip sees "torch already satisfied" and keeps the CPU or wrong-CUDA build.

## Pitfalls

1. `torch.cuda.is_available()` returns True even with incompatible builds — the error only fires when you try to create a CUDA tensor.
2. Always verify with an actual computation: `torch.ones(2, device='cuda') + 1` — not just `is_available()`.
3. The `cu128` index URL was introduced in PyTorch 2.11. Earlier versions only have cu118/cu121/cu124.
4. CUDA toolkit version on the host must match or be compatible with the PyTorch wheel's CUDA version. Check: `nvidia-smi` shows driver-supported CUDA version.
