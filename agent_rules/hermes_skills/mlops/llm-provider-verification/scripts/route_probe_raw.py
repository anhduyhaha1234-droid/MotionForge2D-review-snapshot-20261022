#!/usr/bin/env python
"""Effective-route probe for an OpenAI-compatible proxy: metadata + tool roundtrip.

Why: a proxied route can answer text and still (a) stop publishing capability flags in
/v1/models, (b) mangle tool calls, or (c) append an SSE terminator to a JSON body so a naive
json.loads raises "Extra data". This script reports the real shape of all three, without ever
printing the API key.

Usage:
    python route_probe_raw.py [model_id] [base_url]

Defaults: model_id=ocg/deepseek-v4.1-flash, base_url resolved from the config entry for that
model (falls back to the first provider pointing at the local router).

Key resolution order: HERMES config providers.<name>.api_key (exact model match, else the first
provider whose base_url matches the target host). The value is never echoed - only its length.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("need pyyaml: pip install pyyaml")
    raise SystemExit(2)

CFG_CANDIDATES = [
    Path.home() / "AppData/Local/hermes/config.yaml",      # Windows
    Path.home() / ".config/hermes/config.yaml",            # Linux
    Path.home() / "Library/Application Support/hermes/config.yaml",  # macOS
]

DEFAULT_MODEL = "ocg/deepseek-v4.1-flash"
DEFAULT_BASE = "http://127.0.0.1:20128/v1"
NONCE = "TOOLRT-7Q2"


def load_cfg() -> dict:
    for p in CFG_CANDIDATES:
        if p.is_file():
            return yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
    return {}


def find_route(model: str, base_hint: str) -> tuple[str, str]:
    cfg = load_cfg()
    provs = cfg.get("providers") or cfg.get("custom_providers") or {}
    if isinstance(provs, list):  # some configs use a list of provider blocks
        provs = {str(i): p for i, p in enumerate(provs)}
    for _, p in provs.items():
        if isinstance(p, dict) and str(p.get("model", "")).strip() == model:
            return str(p.get("api_key", "")), str(p.get("base_url", base_hint))
    host = base_hint.split("/v1")[0]
    for _, p in provs.items():
        if isinstance(p, dict) and host in str(p.get("base_url", "")):
            return str(p.get("api_key", "")), str(p.get("base_url", base_hint))
    return "", base_hint


def post(url: str, payload: dict, key: str, timeout: int = 150) -> tuple[int, str]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


def first_json(text: str):
    """Decode the FIRST JSON object even when an SSE terminator follows it."""
    dec = json.JSONDecoder()
    i = 0
    while i < len(text) and text[i] in " \r\n\t":
        i += 1
    obj, _ = dec.raw_decode(text, i)
    return obj


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    base = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE
    key, base = find_route(model, base)
    print(f"model={model} base={base} key_present={bool(key)} key_len={len(key)}")
    if not key:
        print("NO_KEY_FOUND - set the provider entry in config.yaml")
        return 1

    # 1) metadata (may legitimately return null capability flags - report, do not conclude)
    try:
        req = urllib.request.Request(base + "/models", headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=45) as r:
            md = json.loads(r.read().decode())
        row = next((m for m in md.get("data", []) if m.get("id") == model), None)
        print("metadata=" + json.dumps(
            {k: row.get(k) for k in ("id", "vision", "tools", "reasoning",
                                     "thinkingEffortSupported", "context_length")} if row else None,
            ensure_ascii=False))
        print("metadata_note=null capability flags mean UNDECLARED in this build, not absent"
              if row and row.get("vision") is None else "")
    except Exception as e:  # noqa: BLE001
        print(f"metadata_error={type(e).__name__}: {str(e)[:160]}")

    # 2) tool roundtrip - the proof is the ARGUMENT it emits, not that a call appeared
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": f'Call read_nonce with nonce="{NONCE}".'}],
        "tools": [{"type": "function", "function": {
            "name": "read_nonce", "description": "Report the nonce",
            "parameters": {"type": "object", "properties": {"nonce": {"type": "string"}},
                           "required": ["nonce"]}}}],
        "tool_choice": "auto", "max_tokens": 300,
    }
    try:
        status, raw = post(base + "/chat/completions", payload, key)
        body = first_json(raw)  # tolerates a trailing `data: [DONE]`
        ch = (body.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        tc = msg.get("tool_calls") or []
        print(json.dumps({
            "http": status,
            "returned_model": body.get("model"),
            "finish_reason": ch.get("finish_reason"),
            "tool_calls": len(tc),
            "tool_name": (tc[0].get("function", {}).get("name") if tc else None),
            "tool_args": (tc[0].get("function", {}).get("arguments") if tc else None),
            "args_match_requested_nonce": (NONCE in (tc[0].get("function", {}).get("arguments", "") if tc else "")),
            "body_tail_sample": raw[-40:].replace("\n", "\\n"),
        }, ensure_ascii=False, indent=1))
        if raw.rstrip().endswith("[DONE]"):
            print("note=body carries a trailing data: [DONE] SSE terminator -> decode with raw_decode, "
                  "a naive json.loads would raise 'Extra data'")
    except Exception as e:  # noqa: BLE001
        print(f"tool_roundtrip_error={type(e).__name__}: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
