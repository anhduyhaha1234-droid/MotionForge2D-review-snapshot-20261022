"""R6 video upload helper (multipart, server-managed listing)."""
from __future__ import annotations
import json, mimetypes, sys, urllib.request, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402


def upload_video(local_path: Path, subfolder: str) -> str:
    local_path = Path(local_path)
    boundary = "----r6v" + uuid.uuid4().hex
    CRLF = "\r\n"
    parts = []
    for name, val in (("subfolder", subfolder), ("type", "input"), ("overwrite", "true")):
        parts.append((f"--{boundary}{CRLF}Content-Disposition: form-data; name=\"{name}\"{CRLF}{CRLF}{val}{CRLF}").encode())
    ctype = mimetypes.guess_type(local_path.name)[0] or "video/mp4"
    parts.append((f"--{boundary}{CRLF}Content-Disposition: form-data; name=\"image\"; "
                  f"filename=\"{local_path.name}\"{CRLF}Content-Type: {ctype}{CRLF}{CRLF}").encode()
                 + local_path.read_bytes() + CRLF.encode())
    parts.append(f"--{boundary}--{CRLF}".encode())
    body = b"".join(parts)
    req = urllib.request.Request(K.BASE + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        j = json.loads(resp.read().decode())
    sub = j.get("subfolder", "") or subfolder
    return f"{sub}/{j['name']}" if sub else j["name"]
