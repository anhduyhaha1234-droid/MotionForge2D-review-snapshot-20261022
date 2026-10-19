import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def count_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    return data.count(b"\n") + (0 if data.endswith(b"\n") or len(data) == 0 else 1)

def run_cmd(args, cwd=None):
    res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, errors="replace")
    return {
        "exit_code": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }

def main():
    print("=== STARTING PREFLIGHT AUDIT ===")
    now_utc = datetime.now(timezone.utc).isoformat()
    
    # 1. Environment & Python
    py_info = {
        "executable": sys.executable,
        "version": sys.version,
        "platform": sys.platform
    }
    print(f"Python: {py_info['executable']}")
    
    # 2. Git Repositories
    main_dir = r"C:\Users\Admin\MotionForge2D"
    integration_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-20260927\INTEGRATION"
    
    main_head = run_cmd(["git", "rev-parse", "HEAD"], cwd=main_dir)
    main_status = run_cmd(["git", "status", "--porcelain"], cwd=main_dir)
    
    integration_head = run_cmd(["git", "rev-parse", "HEAD"], cwd=integration_dir)
    integration_status = run_cmd(["git", "status", "--porcelain"], cwd=integration_dir)
    
    print(f"MAIN HEAD: {main_head['stdout'].strip()}, dirty lines: {len(main_status['stdout'].strip().splitlines()) if main_status['stdout'].strip() else 0}")
    print(f"INTEGRATION HEAD: {integration_head['stdout'].strip()}, dirty lines: {len(integration_status['stdout'].strip().splitlines()) if integration_status['stdout'].strip() else 0}")
    
    # 3. Running processes audit
    ps_cmd = run_cmd(["tasklist", "/FO", "CSV", "/V"])
    running_processes = []
    if ps_cmd["exit_code"] == 0:
        lines = ps_cmd["stdout"].splitlines()
        for l in lines[1:]:
            parts = [p.strip('"\r') for p in l.split('","')]
            if len(parts) >= 5:
                img_name = parts[0]
                pid = parts[1]
                window_title = parts[-1] if len(parts) > 8 else ""
                if any(k in img_name.lower() for k in ["python", "hermes", "codex", "node", "comfy"]):
                    running_processes.append({
                        "name": img_name,
                        "pid": pid,
                        "title": window_title
                    })
    print(f"Target running processes count: {len(running_processes)}")
    for rp in running_processes[:10]:
        print(f"  PID {rp['pid']}: {rp['name']} ({rp['title']})")
        
    # Check controller lock and leases
    run_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long"
    lock_path = os.path.join(run_dir, "manager", "locks", "controller.lock")
    lock_meta_path = os.path.join(run_dir, "manager", "locks", "controller.lock.meta.json")
    
    controller_lock_exists = os.path.exists(lock_path)
    controller_lock_meta = None
    if os.path.exists(lock_meta_path):
        with open(lock_meta_path, "r", encoding="utf-8") as f:
            controller_lock_meta = json.load(f)
            
    wan_lock_path = os.path.join(run_dir, "tasks", "MF-DEMO-LONG-01", "work", "wan_runner.lock")
    wan_lock_exists = os.path.exists(wan_lock_path)
    
    leases_dir = os.path.join(run_dir, "manager", "leases")
    leases_files = os.listdir(leases_dir) if os.path.exists(leases_dir) else []
    leases_status = []
    for lf in leases_files:
        if lf.endswith(".json"):
            lp = os.path.join(leases_dir, lf)
            try:
                with open(lp, "r", encoding="utf-8") as f:
                    ldata = json.load(f)
                    leases_status.append({
                        "file": lf,
                        "status": ldata.get("status"),
                        "invocation_id": ldata.get("invocation_id"),
                        "released_utc": ldata.get("released_utc")
                    })
            except Exception as e:
                leases_status.append({"file": lf, "error": str(e)})
                
    print(f"controller.lock exists: {controller_lock_exists}")
    print(f"wan_runner.lock exists: {wan_lock_exists}")
    print(f"Leases count: {len(leases_status)}")
    for ls in leases_status:
        print(f"  Lease {ls.get('file')}: status={ls.get('status')}")

    # 4. Checkpoint 015 4 files audit
    r6_dir = os.path.join(run_dir, "tasks", "MF-DEMO-LONG-01", "corrections", "identity5m_20261008", "r6")
    c02b2_files_expected = {
        os.path.join(r6_dir, "scripts", "r6_cache.py"): "8d4b0c7ad5336e7e6c2a68a12f2a622fbccf900575afd2c1249f31863ae4243d",
        os.path.join(r6_dir, "scripts", "r6_keygen.py"): "4082b9d59afbab5416ed6c4784e713612d16553b98a307ccc428a0e7975bd282",
        os.path.join(r6_dir, "scripts", "r6_key_recipe.py"): "e18fc9d20de1cbf2a3a8f7da2e68fc99c59260701bfbd3dca75106a7cbe8e2bd",
        os.path.join(r6_dir, "tests", "test_codex_c02b2_per_actor_reuse.py"): "c8e272a60340683c0128bdfd980a078975030dfa7ec6d98977bcc55a304abd99",
    }
    
    c02b2_audit = []
    c02b2_all_match = True
    for fpath, exp_hash in c02b2_files_expected.items():
        exists = os.path.exists(fpath)
        actual_hash = sha256_file(fpath) if exists else None
        size = os.path.getsize(fpath) if exists else None
        lines = count_lines(fpath) if exists else None
        matches = (actual_hash == exp_hash)
        if not matches:
            c02b2_all_match = False
        c02b2_audit.append({
            "path": fpath,
            "exists": exists,
            "expected_sha256": exp_hash,
            "actual_sha256": actual_hash,
            "bytes": size,
            "lines": lines,
            "matches": matches
        })
        print(f"C02B2 file {os.path.basename(fpath)}: matches={matches} ({size} B, {lines} L, {actual_hash})")
        
    # 5. Check 27 protected files from C02B2_PREFLIGHT.json
    preflight_json_path = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-codex-takeover-20261015\C02B2_PREFLIGHT.json"
    with open(preflight_json_path, "r", encoding="utf-8") as f:
        old_preflight = json.load(f)
        
    protected_audit = []
    protected_all_match = True
    for item in old_preflight.get("files", []):
        fpath = item["path"]
        role = item.get("role")
        exp_hash = item["sha256"]
        exists = os.path.exists(fpath)
        actual_hash = sha256_file(fpath) if exists else None
        size = os.path.getsize(fpath) if exists else None
        lines = count_lines(fpath) if exists else None
        
        # Note: r6_cache and r6_keygen were 'writable' in C02B2_PREFLIGHT and were patched by worker during C02B2 to reach CHECKPOINT_015.
        # For role == 'protected', they MUST match.
        if role == "protected":
            matches = (actual_hash == exp_hash)
            if not matches:
                protected_all_match = False
        else:
            matches = (actual_hash == c02b2_files_expected.get(fpath, exp_hash))
            
        protected_audit.append({
            "path": fpath,
            "relative": item.get("relative"),
            "role": role,
            "expected_sha256": exp_hash,
            "actual_sha256": actual_hash,
            "bytes": size,
            "lines": lines,
            "matches": matches
        })
    print(f"Protected 27 files check: all protected match = {protected_all_match}")
    
    # 6. Media and Source Pins
    media_pins = {
        r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\source\source_full.mp4": "5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2",
        os.path.join(r6_dir, "outputs", "IDENTITY5M_R6_MASTER.mp4"): "e3107a52c9f10bc36faf7d5aa3aa2e4c4186edae3cd916c52dff9b24eed9e48e",
        os.path.join(r6_dir, "outputs", "IDENTITY5M_R6_SOURCE_W7_R6_COMPARISON.mp4"): "f11f43becf58fa5d9ada18af4ab9dcaac494e47ed8b4d8b41fb87bbe33b140a8"
    }
    media_audit = []
    for mp, exp_h in media_pins.items():
        exists = os.path.exists(mp)
        actual_h = sha256_file(mp) if exists else None
        matches = (actual_h == exp_h)
        media_audit.append({
            "path": mp,
            "exists": exists,
            "expected_sha256": exp_h,
            "actual_sha256": actual_h,
            "matches": matches
        })
        print(f"Media pin {os.path.basename(mp)}: matches={matches}")

    audit_summary = {
        "timestamp_utc": now_utc,
        "python": py_info,
        "main_head": main_head["stdout"].strip(),
        "main_dirty": bool(main_status["stdout"].strip()),
        "integration_head": integration_head["stdout"].strip(),
        "integration_dirty": bool(integration_status["stdout"].strip()),
        "controller_lock_exists": controller_lock_exists,
        "wan_lock_exists": wan_lock_exists,
        "leases_all_released": all(ls.get("status") == "RELEASED" for ls in leases_status),
        "c02b2_files_all_match_checkpoint015": c02b2_all_match,
        "protected_files_all_match": protected_all_match,
        "media_pins_all_match": all(m["matches"] for m in media_audit),
        "c02b2_audit": c02b2_audit,
        "protected_audit": protected_audit,
        "media_audit": media_audit,
        "leases_status": leases_status,
        "controller_lock_meta": controller_lock_meta
    }
    
    out_path = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\preflight_audit_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"Audit result saved to {out_path}")
    print("=== PREFLIGHT AUDIT FINISHED ===")

if __name__ == "__main__":
    main()
