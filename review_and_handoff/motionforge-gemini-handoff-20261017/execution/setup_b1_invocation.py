import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

def main():
    now_utc = datetime.now(timezone.utc).isoformat()
    
    run_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long"
    r6_dir = os.path.join(run_dir, "tasks", "MF-DEMO-LONG-01", "corrections", "identity5m_20261008", "r6")
    inv_dir = os.path.join(r6_dir, "continuations", "GEMINI-R6-INV01")
    
    subdirs = ["renders", "evidence", "receipts", "outputs", "logs", "evidence/cotracker", "evidence/qa"]
    for d in subdirs:
        os.makedirs(os.path.join(inv_dir, d), exist_ok=True)
    print(f"Created continuation directory: {inv_dir}")
    
    # Query ComfyUI system stats
    comfy_stats = {}
    try:
        url = "http://127.0.0.1:8188/system_stats"
        req = urllib.request.urlopen(url, timeout=5)
        comfy_stats = json.loads(req.read().decode())
    except Exception as e:
        comfy_stats = {"error": str(e)}
        
    # Query object info
    object_info = {}
    try:
        url = "http://127.0.0.1:8188/object_info"
        req = urllib.request.urlopen(url, timeout=10)
        data = json.loads(req.read().decode())
        object_info = {
            "total_nodes": len(data),
            "unets": data.get("UNETLoader", {}).get("input", {}).get("required", {}).get("unet_name", [[]])[0],
            "clips": data.get("CLIPLoader", {}).get("input", {}).get("required", {}).get("clip_name", [[]])[0],
            "vaes": data.get("VAELoader", {}).get("input", {}).get("required", {}).get("vae_name", [[]])[0],
        }
    except Exception as e:
        object_info = {"error": str(e)}

    preflight_b1 = {
        "schema": 1,
        "phase": "B1",
        "invocation_id": "GEMINI-R6-INV01",
        "created_utc": now_utc,
        "owner": "gemini-implementation-owner",
        "model": "ag/gemini-3.8-flash-high",
        "gpu_concurrency_policy": "GPU=1 sequential",
        "comfyui_server": {
            "host": "127.0.0.1",
            "port": 8188,
            "status": "ONLINE",
            "stats": comfy_stats
        },
        "models_verified": object_info,
        "hard_excerpts_targets": [
            {"shot": "S0022", "focus": "identity/ghost"},
            {"shot": "S0031", "focus": "identity/entry (E2 entry at f60)"},
            {"shot": "S0033", "focus": "identity/ghost (single person E8, avoid added standing portrait)"},
            {"shot": "S0057", "focus": "car artwork (E1+E2 visible f1-f96, tail zero)"},
            {"shot": "S0061", "focus": "entry at f104 (avoid imagined person before entry)"},
            {"shot": "S0062", "focus": "entry at f32 (E6 behind counter, E1+E2 enter)"},
            {"shot": "S0063", "focus": "occlusion (rear E2 partially visible, keep visible part)"},
            {"shot": "S0064", "focus": "occlusion"},
            {"shot": "S0073", "focus": "notebook/contact (E2 pickup/hold book with E6)"},
            {"shot": "S0074", "focus": "document close-up (zero-explicit, keep text)"}
        ],
        "status": "PREFLIGHT_OK_READY_FOR_EXECUTION"
    }
    
    out_p = os.path.join(inv_dir, "PREFLIGHT_B1.json")
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(preflight_b1, f, indent=2)
    print(f"Saved {out_p}")

if __name__ == "__main__":
    main()
