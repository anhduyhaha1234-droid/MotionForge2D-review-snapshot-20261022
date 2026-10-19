# Provider Discovery — local 9router gateway (verified 2026-08)

User's Hermes runs a **custom provider**: a local **9router** gateway (node.exe, `9router/app/custom-server.js`) listening on `127.0.0.1:20128`.

## Current config (config.yaml `model:` section)

```yaml
model:
  default: ocg/deepseek-v4-flash
  provider: custom
  base_url: http://127.0.0.1:20128/v1
  context_length: 900000
  max_tokens: 16384
```

## Enumerate models behind the gateway

```bash
curl -s --max-time 5 http://127.0.0.1:20128/v1/models | python -c "import json,sys; d=json.load(sys.stdin); [print(m['id'],'| owned_by:',m.get('owned_by')) for m in d['data']]"
```

`owned_by` reveals the upstream provider family:

| Prefix | Providers |
|---|---|
| `ag/` | Google Gemini 3/3.5/3.6 flash+pro, Claude Sonnet 4.6, Claude Opus 4.6-thinking, GPT-OSS 120B |
| `ocg/` | DeepSeek V4 pro/flash, GLM 5.1/5.2, Kimi K2.6/K2.7-code, MiniMax M2.5/M2.7/M3, Qwen3.7-plus, Mimo 2.5(+free) |
| `cmc/` | Cloudflare-hosted: DeepSeek V4, Kimi K2.5/K2.6, GLM 5/5.1, MiniMax M2.5/M2.7, Qwen3.6-Max/Plus, Step 3.5-Flash |

## Identify the gateway process (Windows)

```bash
netstat -ano | grep ':20128' | head -5        # LISTENING PID on the right column
wmic process where "ProcessId=143644" get Name,CommandLine
```

**Pitfall:** `tasklist //FI "PID eq <PID>" //FO LIST` FAILS under git-bash/MSYS with `ERROR: Invalid argument/option - '//FI'`. Use `wmic process where "ProcessId=<PID>" get Name,CommandLine` instead — it works and also returns the full command line.
