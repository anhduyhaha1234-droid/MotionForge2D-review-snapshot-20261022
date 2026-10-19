# Telegram Gateway Setup — Windows (verified 2026-08-05)

Real-session recipe: Hermes desktop on Windows, user provided bot token, wanted to chat
with Hermes via Telegram. Gateway installed as Windows Scheduled Task.

## Verified sequence (commands + observed output)

### 1. Locate config + check current state

```bash
grep -n -i -A12 "telegram" ~/AppData/Local/hermes/config.yaml   # empty = not configured
cat ~/AppData/Local/hermes/.env                                  # check existing keys (token NOT here yet)
```

Telegram platform settings live in config.yaml under `telegram:` (reactions,
channel_prompts, allowed_chats, extra.rich_messages) — but the BOT TOKEN is a
secret → `.env` only.

### 2. Verify token with Bot API (before wiring anything)

```bash
curl -s --max-time 20 "https://api.telegram.org/bot<TOKEN>/getMe"
# valid → {"ok":true,"result":{"id":8925737787,"is_bot":true,"first_name":"hermescontrol",
#          "username":"hermescontrolduybot", ...}}
curl -s --max-time 15 "https://api.telegram.org/bot<TOKEN>/getUpdates"
# [] = nobody has messaged the bot yet
```

### 3. Append token to .env (append — never overwrite existing keys)

```bash
printf '\n# Telegram bot (hermescontrol @hermescontrolduybot)\nTELEGRAM_BOT_TOKEN=<token>\n' >> ~/AppData/Local/hermes/.env
grep -c "TELEGRAM_BOT_TOKEN" ~/AppData/Local/hermes/.env   # → 1
```

### 4. Install gateway (creates Scheduled Task + starts process)

```bash
hermes gateway install
# Output (prompts accept defaults when stdin is not a TTY):
#   ✓ Created Scheduled Task 'Hermes_Gateway'
#   Task script: C:\Users\Admin\AppData\Local\hermes\gateway-service\Hermes_Gateway.cmd
#   ℹ Gateway auto-start installed for Windows login.
#   ✓ Gateway started via direct spawn (PID 128440)
```

### 5. Verify status + log

```bash
hermes gateway status
#   ✓ Scheduled Task registered: Hermes_Gateway  (Status: Ready)
#   ✓ Gateway process running (PID: 128440)

sleep 5; tail -30 ~/AppData/Local/hermes/logs/gateway.log
# Key lines:
#   [Telegram] Connected to Telegram (polling mode)
#   ✓ telegram connected
#   Gateway running with 1 platform(s)
#   [Telegram] set_my_commands OK for scope BotCommandScopeDefault (57 cmds)
```

Connect takes ~10-20s (DNS-over-HTTPS fallback IP discovery happens first).

## Authorization — mandatory, gateway denies unknown senders

Warning logged when no allowlist configured:
> "No env user allowlists configured. Messaging platforms default to
> pairing/allowlist policies and will deny unknown senders unless you configure
> platform allowlists (e.g., TELEGRAM_ALLOWED_USERS=your_id) or explicitly opt
> in with GATEWAY_ALLOW_ALL_USERS=true"

Two paths:

| Path | How | When |
|---|---|---|
| `TELEGRAM_ALLOWED_USERS=<id1,id2>` in `.env` | Get numeric ID via @userinfobot, add to .env, restart gateway | User knows their ID / wants zero pairing friction |
| DM pairing | User sends ANY message to bot → gateway emits pairing code → approve with `hermes pairing approve telegram <code>` | Recommended; no ID lookup needed |

Catch the pairing code live (watcher pattern):

```bash
# background=true, watch_patterns=["pair","code","allow"]
tail -f ~/AppData/Local/hermes/logs/gateway.log
```

## Source discovery — docs URLs 404, source is ground truth

- `hermes` CLI on Windows is a PyInstaller .exe at `...\Python311\Scripts\hermes.exe` (MZ header).
- Real source: `C:\Users\Admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\hermes_cli\`
  - `config_defaults.py` — documents EVERY env var with description/prompt/url/category; grep `TELEGRAM_` for the full list
  - `gateway.py` — install/run/status/pairing logic (Windows Scheduled Task path, PID-file fallback)
  - `telegram_managed_bot.py` — bot command management
- Deep docs URLs (e.g. `/docs/user-guide/gateway/telegram`) return GitHub Pages 404 → grep installed source instead of guessing docs paths.
- Version check: `hermes_agent-<ver>.dist-info` in site-packages.

## Key env vars (from config_defaults.py)

| Var | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Complete bot token from @BotFather (numeric ID + colon + secret) |
| `TELEGRAM_ALLOWED_USERS` | Optional comma-separated numeric Telegram user IDs allowed immediately; blank = DM pairing |
| `TELEGRAM_PROXY` | Proxy URL for Telegram (http/https/socks5), overrides HTTPS_PROXY |

## config.yaml telegram section (defaults)

```yaml
telegram:
  reactions: false            # 👀/✅/❌ reactions during processing
  channel_prompts: {}         # per-chat/topic ephemeral system prompts
  allowed_chats: ""           # if set, ONLY responds in these group/supergroup IDs
  extra:
    rich_messages: false      # Bot API 10.1 rich messages (opt-in)
    rich_drafts: false        # experimental rich draft previews (opt-in)
```

## Restart / stop / uninstall

```bash
hermes gateway restart   # refuses to run from inside the gateway process (self-target loop guard)
hermes gateway stop      # stops profile gateway or service
hermes gateway uninstall # remove Scheduled Task
hermes gateway list      # all profiles + gateway status
```
