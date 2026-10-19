"""Export user-visible messages from one local Codex JSONL session.

The output is a readable snapshot, not a restorable session database. Stop if
common credential forms appear; manually review before publishing.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path


PATTERNS = {
    "GitHub token": r"gh[pousr]_[A-Za-z0-9_]{20,}",
    "OpenAI key": r"sk-[A-Za-z0-9_-]{20,}",
    "Google key": r"AIza[0-9A-Za-z_-]{20,}",
    "JWT": r"eyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{10,}",
    "private key": r"-----BEGIN (?:OPENSSH|RSA|EC|PRIVATE) PRIVATE KEY-----",
    "Bearer token": r"(?i)Bearer\s+[A-Za-z0-9._~-]{12,}",
    "credential assignment": (
        r"(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|password)\s*[=:]\s*\S{10,}"
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    raw = args.session.read_bytes()
    messages = []
    for line in raw.decode("utf-8").splitlines():
        record = json.loads(line)
        payload = record.get("payload", {})
        if (
            record.get("type") != "response_item"
            or payload.get("type") != "message"
            or payload.get("role") not in ("user", "assistant")
        ):
            continue
        content = "\n".join(
            part.get("text", "")
            for part in payload.get("content", [])
            if part.get("type") in ("input_text", "output_text")
        )
        content = "\n".join(
            row.rstrip() for row in content.replace("\r\n", "\n").split("\n")
        ).strip()
        if not content:
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, content):
                raise RuntimeError(f"Potential {label} in visible message; export stopped")
        messages.append(
            {
                "timestamp_utc": record["timestamp"],
                "role": payload["role"],
                "phase": payload.get("phase"),
                "text": content,
            }
        )

    if not messages:
        raise RuntimeError("No visible messages found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    session_id = args.session.stem.rsplit("-", 5)[-5:]
    session_id = "-".join(session_id)
    header = [
        "# Lịch sử hội thoại MotionForge2D — bản đọc trên máy khác",
        "",
        "Đây là ảnh chụp các tin nhắn **hiển thị** của cuộc chat Codex hiện tại. "
        "Thứ tự và nội dung văn bản được lấy từ bản ghi phiên cục bộ; không gồm "
        "suy luận nội bộ, log lệnh/công cụ, tài khoản đăng nhập hay cơ sở dữ liệu "
        "phiên. Đây là tài liệu đọc và bàn giao, không khôi phục được chính session ID trong app.",
        "",
        f"- Session ID nguồn: `{session_id}`",
        f"- Số tin nhắn: **{len(messages)}** "
        f"(người dùng: {sum(m['role'] == 'user' for m in messages)}, "
        f"trợ lý: {sum(m['role'] == 'assistant' for m in messages)})",
        f"- Mốc cuối trong bản chụp: **{messages[-1]['timestamp_utc']}**",
        "- Quy tắc và trạng thái hiện hành nằm ở "
        "`../project/docs/pm/HERMES_AUTOPILOT_RULES.md` và "
        "`../PAUSE_STATE_20261019.json`; lời chat cũ không thay thế các file đó.",
        "",
        "---",
        "",
    ]
    body = []
    for number, message in enumerate(messages, 1):
        label = "Người dùng"
        if message["role"] == "assistant":
            label = (
                "Trợ lý · trả lời cuối"
                if message["phase"] == "final_answer"
                else "Trợ lý · cập nhật"
            )
        body.extend(
            [
                f"## {number:03d} · {message['timestamp_utc']} · {label}",
                "",
                message["text"],
                "",
                "---",
                "",
            ]
        )
    transcript = args.output_dir / "LICH_SU_HOI_THOAI_20261019.md"
    transcript.write_text("\n".join(header + body), encoding="utf-8", newline="\n")
    manifest = {
        "session_id": session_id,
        "source_record_sha256_at_snapshot": hashlib.sha256(raw).hexdigest(),
        "last_message_utc": messages[-1]["timestamp_utc"],
        "visible_message_count": len(messages),
        "user_message_count": sum(m["role"] == "user" for m in messages),
        "assistant_message_count": sum(m["role"] == "assistant" for m in messages),
        "transcript_sha256": hashlib.sha256(transcript.read_bytes()).hexdigest(),
        "scope": "Visible user and assistant text only; no tool logs, reasoning, credentials, or session database.",
    }
    (args.output_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Exported {len(messages)} messages, {transcript.stat().st_size} bytes")


if __name__ == "__main__":
    main()
