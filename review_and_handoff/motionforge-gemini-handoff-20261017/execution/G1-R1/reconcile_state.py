import json
from datetime import datetime, timezone

state_p = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\STATE.json"
with open(state_p, "r", encoding="utf-8") as f:
    st = json.load(f)

now_utc = datetime.now(timezone.utc).isoformat()
st["updated_utc"] = now_utc
st["phase"] = "G1-R1"
st["status"] = "G1_CANDIDATE_02_READY_PENDING_CODEX_REVIEW"
st["active_task"] = "G1_CANDIDATE_02_SUBMISSION"
st["allowlist"] = [
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cache.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_keygen.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_key_recipe.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_keygen_asset.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_propagate.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cotracker.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_ledger.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_gate.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_assemble.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_matrix.py",
    r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\tests\test_g1_r1_correction.py",
    r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\submissions\g1-candidate-02\**"
]

st["verified_facts"] = [
    "89/89 unit and regression tests pass across all suites (duration 11.173s)",
    "20/20 matrix rows M01-M20 verified pass in test_g1_r1_correction.py",
    "7 findings P1 and 2 findings P2 from Codex G1 review completely resolved",
    "All 18 GPU leases released, controller lock absent, zero concurrent writers",
    "Candidate 02 frozen and fully packaged at submissions/g1-candidate-02",
    "All 9 hard excerpts B1 completed and verified (1945 frames)",
    "Clean porcelain on INTEGRATION worktree"
]

st["open_findings"] = [
    "Pending independent Codex review for g1-candidate-02"
]

st["tests"] = [
    {
        "test": "full test suite + G1-R1 correction matrix",
        "command": "python -B -m unittest discover -s R6/tests -p test_*.py",
        "exit": 0,
        "result": "89 passed in 11.173s"
    },
    {
        "test": "producer replay probe",
        "command": "python -B probe_c02b2_v4.py --scripts R6/scripts --out G1-R1/probe_v4_g1_r1",
        "exit": 0,
        "result": "initial 1, replay 0, verified-reuse"
    }
]

st["next_command"] = "Await Codex G1 verdict on g1-candidate-02 to unlock Gate G2"
st["next_task"] = "G2_PILOT_300S_ASSEMBLY"
st["next_phase"] = "G2"

with open(state_p, "w", encoding="utf-8") as f:
    json.dump(st, f, indent=2)
print("Updated WORK/STATE.json with full G1-R1 reconciliation!")
