import os, json
from datetime import datetime, timezone

state_p = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution\STATE.json"
st = json.load(open(state_p, encoding="utf-8"))
now_utc = datetime.now(timezone.utc).isoformat()
st["updated_utc"] = now_utc
st["status"] = "B1_HARD_EXCERPTS_COMPLETED"
st["phase"] = "B2"
st["active_task"] = "GEMINI-B2-PILOT-300S-ASSEMBLY"
st["b1_hard_excerpts"] = {
    "status": "ALL_9_COMPLETED",
    "completed_shots": ["S0022", "S0031", "S0033", "S0057", "S0061", "S0062", "S0063", "S0073", "S0074"],
    "total_frames_rendered": 1945,
    "completed_at_utc": now_utc
}
json.dump(st, open(state_p, "w", encoding="utf-8"), indent=2)
print("Updated STATE.json with B1 completion")
