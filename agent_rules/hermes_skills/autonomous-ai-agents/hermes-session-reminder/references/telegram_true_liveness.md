# Telegram True-Liveness Heartbeat & Daemon Architecture

## 1. Context & Pitfall
When operating turn-based CLI coding agents, naive heartbeat scripts that merely inspect static `state.json` (`status: "RUNNING"`) will continue to emit false "RUNNING 24/24" status messages even when the agent is idle, crashed, or waiting for user turns. This creates the "Heartbeat báo 1 đằng, tiến độ chạy 1 nẻo" defect.

## 2. True Liveness Audit Algorithm
A heartbeat daemon must compute liveness from observable OS and filesystem evidence:
1. **Filesystem Activity**: Walk designated project directories (`work/`, `scripts/`, `tests/`, `outputs/`) tracking `max(mtime)`.
2. **Threshold Classification**:
   - `elapsed = now - max_mtime`
   - If `elapsed < 600s` (10 min): `🟢 ACTIVE — Đang có tiến trình ghi nhận (File mới nhất: <filename> cách đây X phút)`
   - If `elapsed >= 600s`: `⚠️ STALL / IDLE — Không có file nào thay đổi trong X phút (Agent đang chờ lệnh hoặc không có worker chạy nền!)`
3. **OS Process Liveness**: Verify PID existence via `tasklist /FI "PID eq <pid>"` or `os.kill(pid, 0)` rather than assuming the process is alive from a lockfile.

## 3. Telegram API Notification Seam
```python
import urllib.request, urllib.parse, json

def send_telegram_html(token: str, chat_id: str, text: str, timeout: int = 15) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
        res = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
        return bool(res.get("ok"))
    except Exception as e:
        return False
```

## 4. Watchdog + Heartbeat Unified Daemon
Run as a background process via `terminal(background=True)`:
- Wakes every 30 minutes (`time.sleep(1800)`).
- Audits filesystem liveness and dispatches Telegram notification.
- Checks `state.db` messages table for session IDLE status (`now - last_message_ts > 600s`).
- If IDLE, executes `hermes.exe chat -q "<short_nudge>" -r <SID> -m <MODEL> --provider <PROVIDER> -Q` to resume work autonomously.
- Logs each nudge execution with `[GIỜ NHẮC]` header to preserve verification audit trail.
