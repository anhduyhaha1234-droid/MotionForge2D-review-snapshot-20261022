#!/usr/bin/env python3
"""Batch-probe model identity/health on an OpenAI-compatible proxy provider.

Reads the named provider's base_url + api_key from Hermes config.yaml
(custom_providers block), lists its models, and probes each with an
identity question. Prints one line per model: status / latency /
response.model / self-identity / reasoning_tokens.

Usage:
  python probe_models.py                      # provider VietAPI, all models
  python probe_models.py --provider 9Router   # another provider
  python probe_models.py --models deepseek-v4-flash,deepseek-v4-pro
  python probe_models.py --prompt "What model are you? Be honest."
  python probe_models.py --timeout 25

Notes:
  - Use the Windows-native config path when invoking from MSYS bash.
  - Long batches (30 models x ~25s) can take 10+ min: run with
    terminal(background=True, notify_on_complete=True) and report
    progress/ETA to the user.
  - The API key is parsed but never printed.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DEFAULT_CONFIG = r"C:/Users/Admin/AppData/Local/hermes/config.yaml"
DEFAULT_PROMPT = "Tru lai bang 1 cau: ban la model gi va ai tao ra ban? Hay thanh that."


def load_provider(cfg_path: str, name: str):
    """Extract base_url + api_key for a named custom_providers entry."""
    with open(cfg_path, encoding="utf-8") as f:
        cfg = f.read()
    # custom_providers blocks look like:
    #   - name: VietAPI
    #     base_url: https://...
    #     api_key: sk-...
    #     models:
    #       - ...
    m = re.search(r"name:\s*" + re.escape(name) + r"\n(.*?)(?=\n  - name:|\n\S)", cfg, re.DOTALL)
    if not m:
        sys.exit(f"provider {name!r} not found in {cfg_path}")
    block = m.group(1)
    base = re.search(r"base_url:\s*(\S+)", block)
    key = re.search(r"api_key:\s*(\S+)", block)
    if not base or not key:
        sys.exit(f"base_url/api_key missing for provider {name!r}")
    return base.group(1).strip(), key.group(1).strip()


def list_models(base_url: str, api_key: str):
    req = urllib.request.Request(base_url.rstrip("/") + "/models")
    req.add_header("Authorization", "Bearer " + api_key)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return [m["id"] for m in data.get("data", [])]


def probe(base_url: str, api_key: str, model: str, prompt: str, timeout: int):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body)
    req.add_header("Authorization", "Bearer " + api_key)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return "OK", json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}", json.loads(e.read().decode())
    except Exception as e:  # noqa: BLE001 - any probe failure is data
        return "ERR", str(e)[:200]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--provider", default="VietAPI")
    ap.add_argument("--models", default="", help="comma-separated; default = all from /models")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--timeout", type=int, default=25)
    args = ap.parse_args()

    base_url, api_key = load_provider(args.config, args.provider)
    print(f"provider={args.provider} base={base_url}", flush=True)

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        models = list_models(base_url, api_key)
    print(f"models to probe: {len(models)}", flush=True)

    for model in models:
        t0 = time.time()
        status, data = probe(base_url, api_key, model, args.prompt, args.timeout)
        dt = time.time() - t0
        if status == "OK" and isinstance(data, dict) and "choices" in data:
            content = data["choices"][0]["message"]["content"].strip().replace("\n", " ")
            rt = data.get("usage", {}).get("completion_tokens_details", {}).get("reasoning_tokens", 0)
            print(f"OK  {model:28s} {dt:5.1f}s resp={data.get('model')} rt={rt} | {content[:120]}", flush=True)
        else:
            err = json.dumps(data)[:180] if isinstance(data, dict) else str(data)[:180]
            print(f"{status:8s} {model:28s} {dt:5.1f}s | {err[:150]}", flush=True)


if __name__ == "__main__":
    main()
