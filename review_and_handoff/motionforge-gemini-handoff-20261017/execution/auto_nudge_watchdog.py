"""Auto Nudge Watchdog for MotionForge2D.

Runs in the background and every 30 minutes:
1. Checks if the agent session 20261017_115944_b2a338 needs a nudge to continue working.
2. If state is WAITING_CODEX_REVIEW / PENDING_CODEX_REVIEW, model nudge is SKIPPED to preserve quota.
3. Injects the exact phrase "tiếp tục làm việc đi" into the chat via hermes CLI resume only when active work is in flight.
4. If nonzero exit: differentiates quota/auth (no retry, reports blocker) vs transient connection errors (waits 5m per rules §7).
5. Sends an updated Telegram heartbeat with real productive liveness audit.
6. Logs each event with timestamp into remind_motionforge.log.
"""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
SID = "20261017_115944_b2a338"
MODEL = "ag/gemini-3.8-flash-high"
PROVIDER = "custom"
MSG = "tiếp tục làm việc đi"
LOG = r"C:\Users\Admin\AppData\Local\hermes\logs\remind_motionforge.log"
STATE_DB = r"C:\Users\Admin\AppData\Local\hermes\state.db"

# Import telegram heartbeat helper
WORK_DIR = r"C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-gemini-handoff-20261017\execution"
STATE_FILE = os.path.join(WORK_DIR, "STATE.json")
sys.path.insert(0, WORK_DIR)
try:
    import telegram_heartbeat
except Exception:
    telegram_heartbeat = None

INTERVAL = 1800  # 30 minutes


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_waiting_codex_review() -> bool:
    """Check if task is currently waiting for independent Codex review."""
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            st = json.load(f)
            status = st.get("status", "")
            return "WAITING" in status or "PENDING" in status
    except Exception:
        return False


def is_session_idle(threshold_seconds=600):
    """Check if the session has had no new messages in the last threshold_seconds."""
    if not os.path.exists(STATE_DB):
        return True
    try:
        conn = sqlite3.connect(STATE_DB, timeout=5)
        cur = conn.cursor()
        row = cur.execute(
            "SELECT timestamp FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 1",
            (SID,)
        ).fetchone()
        conn.close()
        if not row or not row[0]:
            return True
        last_ts = float(row[0])
        elapsed = time.time() - last_ts
        return elapsed > threshold_seconds
    except Exception as e:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{now_str()}] DB check error: {e}\n")
        return True


def run_nudge():
    cmd = [HERMES, "chat", "-q", MSG, "-r", SID, "-m", MODEL, "--provider", PROVIDER, "-Q"]
    with open(LOG, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n=== {now_str()} [GIỜ NHẮC] start ===\n")
        f.flush()
        res = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=600)
        rc = res.returncode
        f.write(f"exit={rc}\n")
        
        # Differentiate error types according to canonical rules §7
        if rc != 0:
            # Check log tail for error classification
            try:
                tail_lines = open(LOG, "r", encoding="utf-8", errors="ignore").readlines()[-20:]
                tail_text = "".join(tail_lines).lower()
            except Exception:
                tail_text = ""
                
            is_quota_auth = any(term in tail_text for term in ("quota", "credit", "auth", "401", "403", "429", "gousagelimiterror"))
            is_transient = any(term in tail_text for term in ("502", "503", "504", "disconnect", "timeout", "network", "socket"))
            
            if is_quota_auth:
                f.write(f"[{now_str()}] Quota/Auth hard error detected -> NO BLIND RETRY. Blocker logged.\n")
                if telegram_heartbeat:
                    telegram_heartbeat.send_tg(
                        f"🚨 <b>[MotionForge2D CẢNH BÁO QUOTA / AUTH]</b>\n\n"
                        f"• Phát hiện lỗi quota/xác thực: <code>exit={rc}</code>\n"
                        f"• Không tự động retry để tránh khóa tài khoản."
                    )
            elif is_transient:
                f.write(f"[{now_str()}] Transient connection error -> Waiting 300s (5m per rules §7) before retry...\n")
                f.flush()
                time.sleep(300)
                res = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=600)
                rc = res.returncode
                f.write(f"retry exit={rc}\n")
        f.write(f"=== {now_str()} end ===\n")
    return rc


def main():
    Path(LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now_str()}] Auto Nudge Watchdog started for session {SID} (interval: {INTERVAL}s).\n")
    
    while True:
        time.sleep(INTERVAL)
        
        # 1. Telegram Heartbeat
        if telegram_heartbeat:
            try:
                hb_msg = telegram_heartbeat.build_status_msg()
                telegram_heartbeat.send_tg(hb_msg)
            except Exception as e:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(f"[{now_str()}] Telegram error: {e}\n")
                    
        # 2. Check if waiting for review: DO NOT model-nudge
        if is_waiting_codex_review():
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{now_str()}] State is WAITING_CODEX_REVIEW -> Model nudge skipped to preserve quota.\n")
            continue

        # 3. Check if agent is idle and nudge
        if is_session_idle(threshold_seconds=600):
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{now_str()}] Session {SID} idle > 10m -> Nudging to continue work...\n")
            try:
                rc = run_nudge()
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(f"[{now_str()}] Nudge finished with rc={rc}\n")
                if rc != 0 and telegram_heartbeat:
                    telegram_heartbeat.send_tg(
                        f"🚨 <b>[MotionForge2D CẢNH BÁO TOOL STALL]</b>\n\n"
                        f"• Lệnh resume phiên làm việc trả về mã lỗi <code>rc={rc}</code>.\n"
                        f"• Xem log chi tiết tại: <code>{LOG}</code>\n"
                        f"• Bạn vui lòng mở chat kiểm tra!"
                    )
            except Exception as e:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(f"[{now_str()}] Nudge exception: {e}\n")
                if telegram_heartbeat:
                    telegram_heartbeat.send_tg(
                        f"🚨 <b>[MotionForge2D CẢNH BÁO LỖI HỆ THỐNG]</b>\n\n"
                        f"• Gặp ngoại lệ khi đánh thức agent: <code>{e}</code>\n"
                        f"• Bạn vui lòng mở chat kiểm tra!"
                    )
        else:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{now_str()}] Session {SID} currently ACTIVE -> Nudge skipped this tick.\n")


if __name__ == "__main__":
    main()
