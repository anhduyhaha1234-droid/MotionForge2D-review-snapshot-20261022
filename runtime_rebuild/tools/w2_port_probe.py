"""Blocking connect_ex probe for the task engine port (MF-V1-VIDEO14B).

A socket with a timeout set is non-blocking under the hood and reports
WSAEWOULDBLOCK (10035) even when nothing is listening, so this probe uses a
plain BLOCKING socket to get a real verdict: 0 = something is listening,
ECONNREFUSED/WSAECONNREFUSED (10061) = port closed, anything else = reported raw.

usage: python w2_port_probe.py <host> <port> [out.json]
"""
from __future__ import annotations

import errno
import json
import socket
import sys
from pathlib import Path


def probe(host: str, port: int) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(None)  # blocking: connect_ex returns the real errno
    try:
        rc = s.connect_ex((host, port))
    finally:
        s.close()
    return {
        "host": host,
        "port": port,
        "mode": "blocking",
        "connect_ex": rc,
        "errno_name": (errno.errorcode.get(rc) or ("SUCCESS" if rc == 0 else "UNKNOWN")),
        "listening": rc == 0,
        "port_closed": rc != 0,
    }


def main() -> int:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8210
    rec = probe(host, port)
    text = json.dumps(rec, indent=1)
    if len(sys.argv) > 3:
        Path(str(sys.argv[3]).replace("\\", "/")).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
