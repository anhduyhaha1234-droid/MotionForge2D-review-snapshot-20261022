"""Launch the task-local ComfyUI server for MF-V1-VIDEO14B on loopback :8210
and record the instance epoch.

The epoch file is written by the *server process itself* (same pid, via runpy),
so a restart is detectable as an instance_id change plus pid liveness.

Usage:
  python serve_video14b.py --port 8210
"""
from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

RT = Path(r"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b")
WT_PKG = Path(r"C:\Users\Admin\Documents\Codex\work\mfv1\wt-comfy\experiments\mf_reskin_v1\comfy")
CUI = RT / "ComfyUI"

sys.path.insert(0, str(WT_PKG))
from mf_comfy.lease import InstanceEpoch  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8210)
    ap.add_argument("--listen", default="127.0.0.1")
    ap.add_argument("--reserve-vram", type=float, default=1.0)
    a = ap.parse_args()

    if a.listen not in ("127.0.0.1", "localhost", "::1"):
        print("REFUSED: this adapter is loopback-only", file=sys.stderr)
        return 2

    base_url = f"http://{a.listen}:{a.port}"
    epoch = InstanceEpoch(RT / "instance_epoch.json")
    rec = epoch.write(
        base_url=base_url,
        comfyui_version="0.37.0",
        extra={
            "port": a.port,
            "comfyui_dir": str(CUI),
            "owner": "video14b",
            "reserve_vram_gb": a.reserve_vram,
            "comfyui_commit": "73c9bad4d21e7addbe1d13bc92eee0f1431b017d",
        },
    )
    print(f"[mf] instance epoch written: {rec['instance_id']} pid={rec['pid']} {base_url}", flush=True)

    sys.argv = [
        str(CUI / "main.py"),
        "--listen", a.listen,
        "--port", str(a.port),
        "--base-directory", str(RT),
        "--reserve-vram", str(a.reserve_vram),
        "--disable-auto-launch",
    ]
    os.chdir(CUI)
    sys.path.insert(0, str(CUI))
    runpy.run_path(str(CUI / "main.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
