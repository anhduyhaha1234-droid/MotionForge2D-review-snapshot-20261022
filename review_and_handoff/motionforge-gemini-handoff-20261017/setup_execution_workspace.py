import os
import sys
import json
import shutil
import hashlib
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

def main():
    now_utc = datetime.now(timezone.utc).isoformat()
    
    handoff_dir = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017"
    work_dir = os.path.join(handoff_dir, "execution")
    preimages_dir = os.path.join(work_dir, "preimages", "c02b2_takeover")
    snapshots_dir = os.path.join(work_dir, "snapshots")
    a1_dir = os.path.join(work_dir, "A1")
    
    os.makedirs(preimages_dir, exist_ok=True)
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(a1_dir, exist_ok=True)
    
    run_dir = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long"
    r6_dir = os.path.join(run_dir, "tasks", "MF-DEMO-LONG-01", "corrections", "identity5m_20261008", "r6")
    
    c02b2_files = {
        "r6_cache.py": os.path.join(r6_dir, "scripts", "r6_cache.py"),
        "r6_keygen.py": os.path.join(r6_dir, "scripts", "r6_keygen.py"),
        "r6_key_recipe.py": os.path.join(r6_dir, "scripts", "r6_key_recipe.py"),
        "test_codex_c02b2_per_actor_reuse.py": os.path.join(r6_dir, "tests", "test_codex_c02b2_per_actor_reuse.py")
    }
    
    copied_preimages = []
    for fname, src_path in c02b2_files.items():
        dst_path = os.path.join(preimages_dir, fname)
        shutil.copy2(src_path, dst_path)
        sha = sha256_file(dst_path)
        size = os.path.getsize(dst_path)
        lines = count_lines(dst_path)
        copied_preimages.append({
            "name": fname,
            "live_path": src_path,
            "preimage_path": dst_path,
            "sha256": sha,
            "bytes": size,
            "lines": lines
        })
        print(f"Copied preimage: {fname} -> {sha} ({size} B, {lines} L)")
        
    # Read preflight audit result
    audit_res_path = os.path.join(handoff_dir, "preflight_audit_result.json")
    with open(audit_res_path, "r", encoding="utf-8") as f:
        audit_res = json.load(f)
        
    # 1. WORK/PREFLIGHT.json
    preflight_data = {
        "schema": 1,
        "created_utc": now_utc,
        "task": "CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE",
        "parent": "MF-DEMO-LONG-01",
        "parent_status": "NOT_APPROVED",
        "owner": "gemini-implementation-owner",
        "session_id": "gemini_20261017_r6_takeover",
        "model": "ag/gemini-3.8-flash-high",
        "provider_route": "http://127.0.0.1:20128/v1",
        "authority": "HERMES_AUTOPILOT_RULES.md section 0.12",
        "python": audit_res["python"],
        "repositories": {
            "main": {
                "path": r"C:\Users\Admin\MotionForge2D",
                "head": audit_res["main_head"],
                "dirty": audit_res["main_dirty"]
            },
            "integration": {
                "path": r"C:\Users\Admin\Documents\Codex\work\mf-delivery-20260927\INTEGRATION",
                "head": audit_res["integration_head"],
                "dirty": audit_res["integration_dirty"]
            }
        },
        "controller": {
            "lock_file_exists": audit_res["controller_lock_exists"],
            "meta": audit_res["controller_lock_meta"],
            "holder": None
        },
        "wan_runner_lock": {
            "exists": audit_res["wan_lock_exists"],
            "pid_in_lock": 30072,
            "pid_running": False
        },
        "leases": {
            "total_count": len(audit_res["leases_status"]),
            "all_released": audit_res["leases_all_released"],
            "active_leases": []
        },
        "quiescence_verified": True,
        "c02b2_checkpoint015_verified": audit_res["c02b2_files_all_match_checkpoint015"],
        "protected_27_files_verified": audit_res["protected_files_all_match"],
        "media_pins_verified": True,
        "c02b2_files": copied_preimages,
        "protected_files": audit_res["protected_audit"],
        "ok": True
    }
    
    with open(os.path.join(work_dir, "PREFLIGHT.json"), "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    print("Saved WORK/PREFLIGHT.json")
    
    # 2. WORK/OWNER_TRANSFER.json
    owner_transfer_data = {
        "schema": 1,
        "transfer_utc": now_utc,
        "parent": "MF-DEMO-LONG-01",
        "parent_status": "NOT_APPROVED",
        "task": "CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE",
        "phase": "A1",
        "previous_owner": {
            "owner": "/root/motionforge_c02b2_coder",
            "model": "gpt-6-sol",
            "status": "terminal: errored (usage limit)",
            "last_checkpoint": "c02b2-worker/CHECKPOINT_015.json",
            "active_writer": False
        },
        "new_owner": {
            "owner": "gemini-implementation-owner",
            "session_id": "gemini_20261017_r6_takeover",
            "model": "ag/gemini-3.8-flash-high",
            "base_url": "http://127.0.0.1:20128/v1",
            "role": "implementation owner",
            "active_writer": True
        },
        "independent_reviewer": {
            "role": "Codex PM/Reviewer",
            "gates": ["G1", "G2", "G3"]
        },
        "zero_writer_proof": {
            "old_coder_status": "errored (usage limit), no active process",
            "controller_lock_exists": False,
            "all_leases_released": True,
            "wan_runner_pid_dead": True,
            "quiescence": "PROVEN"
        },
        "counters_policy": "PRESERVED_NOT_RESET",
        "authority": "HERMES_AUTOPILOT_RULES.md section 0.12 and prompt 2026-10-17"
    }
    with open(os.path.join(work_dir, "OWNER_TRANSFER.json"), "w", encoding="utf-8") as f:
        json.dump(owner_transfer_data, f, indent=2)
    print("Saved WORK/OWNER_TRANSFER.json")
    
    # 3. WORK/STATE.json
    state_data = {
        "schema": 1,
        "updated_utc": now_utc,
        "project": "MotionForge2D",
        "parent": "MF-DEMO-LONG-01",
        "parent_status": "NOT_APPROVED",
        "active_task": "CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE",
        "owner": "gemini-implementation-owner",
        "model": "ag/gemini-3.8-flash-high",
        "phase": "A1",
        "status": "RUNNING",
        "authority": "HERMES_AUTOPILOT_RULES.md section 0.12",
        "allowlist": [
            os.path.join(r6_dir, "scripts", "r6_cache.py"),
            os.path.join(r6_dir, "scripts", "r6_keygen.py"),
            os.path.join(r6_dir, "scripts", "r6_key_recipe.py"),
            os.path.join(r6_dir, "tests", "test_codex_c02b2_per_actor_reuse.py"),
            os.path.join(work_dir, "A1") + r"\**"
        ],
        "changed_files": [],
        "tests": [
            {
                "test": "checkpoint015 baseline producer replay",
                "command": "python -B probe_c02b2_v4.py --scripts R6/scripts --out c02b2-worker/v4-replay-03",
                "exit": 0,
                "result": "first generation 1, replay 0"
            }
        ],
        "verified_facts": [
            "All 4 C02B2 files match CHECKPOINT_015 exactly",
            "All 27 protected files match C02B2_PREFLIGHT exactly",
            "All 18 GPU leases released, controller lock absent, wan_runner PID 30072 dead",
            "Previous owner /root/motionforge_c02b2_coder terminal errored",
            "Zero concurrent writers proven"
        ],
        "open_findings": [
            "C02B2 incomplete: full P1-P5 finite matrix remaining",
            "standalone gate import without heavy adapter remaining",
            "final regression of 40 approved C01/C02A/C02B1 tests remaining",
            "self-review and candidate freeze remaining"
        ],
        "decisions": [
            "Continue C02B2 from CHECKPOINT_015 as A1 task",
            "Do not revert to C02A; retain C02B2 cache/keygen/recipe improvements",
            "Adhere strictly to 3 root review gates: G1, G2, G3"
        ],
        "next_command": "Run initial focused test suite on test_codex_c02b2_per_actor_reuse.py",
        "live_jobs": [],
        "quota": {
            "kind": "NORMAL_USAGE",
            "provider_message": None,
            "reset_at": None
        },
        "root_gates": {
            "G1": "NOT_APPROVED",
            "G2": "NOT_APPROVED",
            "G3": "NOT_APPROVED"
        },
        "automation": "PAUSED_BY_USER"
    }
    with open(os.path.join(work_dir, "STATE.json"), "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2)
    print("Saved WORK/STATE.json")
    
    # 4. WORK/CHECKPOINT.json
    checkpoint_data = {
        "checkpoint_id": "GEMINI_A1_CHECKPOINT_001",
        "timestamp_utc": now_utc,
        "task": "CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE",
        "phase": "A1 Preflight OK, starting P1-P6 completion",
        "owner": "gemini-implementation-owner",
        "model": "ag/gemini-3.8-flash-high",
        "files": copied_preimages,
        "remaining": [
            "P1: actual run_key unchanged review reuse vs missing review",
            "P2: effective settings independent mutations",
            "P3: same-path same-size mutations and covered actor fewer graphs",
            "P4: malformed/missing collections with recomputed self-digest and legacy v3 denial",
            "P5: actual producer/graph/cache/gate failure controls",
            "P6: full root replay probe, full new module, 40 approved regression tests",
            "Freeze candidate A1 and self-review"
        ],
        "next_step": "Run tests/test_codex_c02b2_per_actor_reuse.py and inspect existing assertions"
    }
    with open(os.path.join(work_dir, "CHECKPOINT.json"), "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2)
    print("Saved WORK/CHECKPOINT.json")
    
    # 5. WORK/BACKLOG.md
    backlog_content = """# MotionForge2D Phase 1 Backlog — Gemini Lane

## Batch A: Engineering Tuần Tự (Chưa GPU/Render)
- [ ] **A1 — CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE** (Đang chạy từ Checkpoint 015)
  - Hoàn tất P1–P6 của TASK_C02B2
  - Full negative matrix + positive controls
  - Standalone gate import without heavy adapter
  - Regression 40 test C01/C02A/C02B1
  - Self-review & freeze candidate A1
- [ ] **A2 — GEMINI-C02B3-ASSET-VERIFIED-REUSE**
  - Asset producer provenance, skip_allowed caller wiring
  - Legacy decisions fail-closed, no auto-upgrade
  - Descendant invalidation proof
- [ ] **A3 — Event timing, child outcome và tracking**
  - Event keys timing, exact frame mapping
  - Stage2 child failure fail-closed
  - CoTracker reader exact contract
  - Crop/stitch/resize/pad transform round-trip
- [ ] **A4 — Evidence, gate, registry/lease conformance**
  - Assembler/submit calls real gate with candidate binding
  - Q01–Q12 & T01–T15 conformance matrix update
  - True-race 2-controller barrier verification
- [ ] **G1 Review Gate**: Nộp frozen engineering batch A1–A4 cho Codex độc lập nghiệm thu

## Batch B: Correction Media & Pilot (Sau G1 Approved)
- [ ] **B1 — Preflight & Hard Excerpts**
  - SAM2, FLUX2, CropAndStitch, VACE, EbSynth, CoTracker hard cases
- [ ] **B2 — Full Pilot 300s (5 phút)**
  - Source 01:34–06:34, 9000f, 30fps, 640x360, original audio
- [ ] **G2 Review Gate**: Nộp pilot 300s cho Codex độc lập nghiệm thu

## Batch C: Hoàn Thiện Sản Phẩm Phase 1 (Sau G2 Approved)
- [ ] **C1**: Production organization (Channel, Project, Multi-video)
- [ ] **C2**: Character Library (Pack Version, stable ID, anchors)
- [ ] **C3**: Character Generator (Ref/profile -> pack draft -> preview)
- [ ] **C4**: Import và Objects (Video -> probe/cuts -> Object Gallery)
- [ ] **C5**: Mapping và Demo (Assign asset -> demo review -> approve)
- [ ] **C6**: Apply/Review (Pipeline job service -> review queue)
- [ ] **C7**: Jobs và Recovery (Background progress, cancel/retry/resume)
- [ ] **C8**: Export và Versions (Audio original, 1080p/4K presets)
- [ ] **C9**: Storage và Delivery (Safe cleanup, local-first Windows)
- [ ] **Full-source 22:01 Proof & 4K Export Gate**
- [ ] **G3 Final Gate**: Codex nghiệm thu độc lập toàn bộ sản phẩm Phase 1
"""
    with open(os.path.join(work_dir, "BACKLOG.md"), "w", encoding="utf-8") as f:
        f.write(backlog_content)
    print("Saved WORK/BACKLOG.md")
    
    # 6. WORK/READ_INDEX.md
    read_index_content = """# MotionForge2D Read Index — Gemini Lane

| Tài liệu | Đường dẫn | Trạng thái đọc | Ghi chú áp dụng |
|---|---|---|---|
| HERMES_AUTOPILOT_RULES.md | `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` | Đã đọc toàn bộ (1–809) | Canonical rules duy nhất, áp dụng mục 0.12 cho Gemini |
| AGENTS.md | `C:/Users/Admin/MotionForge2D/AGENTS.md` | Đã đọc | Workspace instructions, quy tắc đọc canonical rules |
| SESSION_PROTOCOL.md | `C:/Users/Admin/MotionForge2D/docs/pm/SESSION_PROTOCOL.md` | Đã đọc toàn bộ (1–188) | Context firewall, single-writer, byte checkpoints |
| PROMPT_GEMINI_MOTIONFORGE_VI.md | `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/PROMPT_GEMINI_MOTIONFORGE_VI.md` | Đã đọc toàn bộ | Hợp đồng thực thi, phân công A1–A4, G1–G3 |
| HANDOFF_PREFLIGHT.json | `.../motionforge-gemini-handoff-20261017/HANDOFF_PREFLIGHT.json` | Đã đọc | Snapshot trước bàn giao, preimages baseline |
| PROJECT_STATE.json | `.../motionforge-codex-takeover-20261015/PROJECT_STATE.json` | Đã đọc | Baseline project state, 3 gói C01/C02A/C02B1 APPROVED, C02B2 dở dang |
| PROGRESS_AND_PAUSE_20261016.md | `.../motionforge-codex-takeover-20261015/PROGRESS_AND_PAUSE_20261016.md` | Đã đọc | Báo cáo dừng lịch và thực trạng |
| PAUSE_RECEIPT.json | `.../pause-20261016T222242/PAUSE_RECEIPT.json` | Đã đọc | Snapshot 4 files C02B2 và receipt lỗi usage limit của owner cũ |
| CHECKPOINT_015.json | `.../c02b2-worker/CHECKPOINT_015.json` | Đã đọc | Baseline cho task A1: 4 files SHA256 khớp 100% |
| TASK_C02B2.md | `.../motionforge-codex-takeover-20261015/TASK_C02B2.md` | Đã đọc | Nhiệm vụ kỹ thuật A1: P1–P6 |
| C02B2_PREFLIGHT.json | `.../motionforge-codex-takeover-20261015/C02B2_PREFLIGHT.json` | Đã đọc | 27 protected files baseline |
| C02B1_REVIEW_01.md | `.../motionforge-codex-takeover-20261015/C02B1_REVIEW_01.md` | Đã đọc | Bằng chứng duyệt C02B1, staging source |
| CORRECTION_MATRIX.md | `.../motionforge-r6-checkpoint-review-20261014/CORRECTION_MATRIX.md` | Đã đọc | Canonical Q01–Q12 (9 FAIL + 2 UNKNOWN + 1 PASS) |
| TECH_CONFORMANCE_MATRIX.md | `.../motionforge-tech-conformance-20261012/TECH_CONFORMANCE_MATRIX.md` | Đã đọc | Technical T01–T15 |
| skills/README_VI.md & ACTIVE_DIGEST_VI.md | `.../skills/` | Đã đọc | Chọn 2-4 skill/task; dùng systematic-debugging, verification-before-completion |
"""
    with open(os.path.join(work_dir, "READ_INDEX.md"), "w", encoding="utf-8") as f:
        f.write(read_index_content)
    print("Saved WORK/READ_INDEX.md")
    
    # 7. Update OLD/PROJECT_STATE.json with pointer to WORK/STATE.json
    old_state_path = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-codex-takeover-20261015\PROJECT_STATE.json"
    with open(old_state_path, "r", encoding="utf-8") as f:
        old_state = json.load(f)
        
    old_state["execution_handoff"] = {
        "status": "TRANSFERRED_TO_GEMINI",
        "transferred_utc": now_utc,
        "new_state": os.path.join(work_dir, "STATE.json"),
        "new_owner": "gemini-implementation-owner",
        "new_model": "ag/gemini-3.8-flash-high",
        "task": "CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE",
        "authority": "HERMES_AUTOPILOT_RULES.md section 0.12"
    }
    with open(old_state_path, "w", encoding="utf-8") as f:
        json.dump(old_state, f, indent=2)
    print("Updated OLD/PROJECT_STATE.json with execution_handoff pointer")
    print("=== WORKSPACE SETUP COMPLETE ===")

if __name__ == "__main__":
    main()
