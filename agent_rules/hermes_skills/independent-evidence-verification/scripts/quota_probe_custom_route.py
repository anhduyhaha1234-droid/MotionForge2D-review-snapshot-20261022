# -*- coding: utf-8 -*-
"""Minimal route/quota health probe for an OpenAI-compatible local proxy (pre-dispatch gate).

Usage (Windows-native paths):
    python -B quota_probe_custom_route.py <config.yaml> <provider> <model_id> <out.json>

Reads `providers.<provider>.base_url` + `.api_key` from a Hermes-style config YAML. The key is
NEVER printed or written to the evidence file. Verdict:
  HEALTHY                  -> HTTP 200 on a minimal chat_completions (max_tokens=8)
  BLOCKED_QUOTA_OR_ROUTE   -> 429/503/401/403
  UNKNOWN                  -> anything else / exception

Lessons baked in (measured 2026-10):
- 401 in ~15 ms WITHOUT an Authorization header is an auth-middleware response, NOT a quota signal —
  always send the Authorization header from config.
- Provider "reset" timestamps passing in the log do NOT prove quota recovery; only a real 200 does.
- Keep the probe minimal but REAL (a tiny completion); save the evidence JSON next to the review data
  so the decision (dispatch vs blocker) is auditable.
- If verdict is BLOCKED: keep the task checkpoint and report the blocker with the exact error text;
  do not retry blindly, do not switch model/route, do not call it a PM budget event.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def main(cfg_path: str, provider: str, model: str, out_path: str) -> None:
    import yaml  # PyYAML; config is YAML

    cfg = yaml.safe_load(Path(cfg_path).read_text(encoding="utf-8"))
    prov = cfg["providers"][provider]
    base = prov["base_url"].rstrip("/")
    key = prov["api_key"]

    out = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "endpoint": base, "model": model, "probe": "minimal chat_completions max_tokens=8"}

    # 1) free check: model list (no quota consumed)
    try:
        req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=20) as r:
            ids = [m.get("id") for m in json.loads(r.read().decode()).get("data", [])]
        out["models_total"] = len(ids)
        out["pinned_model_listed"] = model in ids
    except Exception as e:  # noqa: BLE001
        out["models_error"] = type(e).__name__ + ": " + str(e)[:120]

    # 2) the actual quota/route check
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": "Reply with exactly: PONG"}],
                       "max_tokens": 8}).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            out["http_status"] = r.status
            out["wall_s"] = round(time.time() - t0, 2)
            try:
                j = json.loads(raw)
                out["reply"] = (j.get("choices") or [{}])[0].get("message", {}).get("content", "")[:60]
                out["usage"] = j.get("usage")
            except Exception:  # noqa: BLE001
                out["body_head"] = raw[:200]
    except urllib.error.HTTPError as e:
        out["http_status"] = e.code
        out["wall_s"] = round(time.time() - t0, 2)
        out["error_body_head"] = e.read().decode()[:300]
    except Exception as e:  # noqa: BLE001
        out["http_status"] = None
        out["exception"] = type(e).__name__ + ": " + str(e)[:160]

    out["verdict"] = ("HEALTHY" if out.get("http_status") == 200 else
                      "BLOCKED_QUOTA_OR_ROUTE" if out.get("http_status") in (429, 503, 401, 403)
                      else "UNKNOWN")
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:5])
