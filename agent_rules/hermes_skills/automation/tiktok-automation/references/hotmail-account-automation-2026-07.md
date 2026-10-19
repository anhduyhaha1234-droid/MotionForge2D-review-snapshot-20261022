# Hotmail Account Automation for TikTok Views (2026-07-25)

## Account Format

```
email|password|microsoft_cookie
```

Example:
```
gabrielhugowilliams0034@outlook.com|gabriel@290501|M.C553_BAY.0.U.-Ct*SJfEZ!xO5O6NOa30WRpgGn3ALx6e02jn7bNJgt9jKhRIjl46oXG62udjRXHFYneHEtukest4tuWyUBK0CQ0Q1l3*pHQkF!Ac6SBrhlPyJUVxyDCY2j3oeAaatWf!*UzRy9DhhqmhBlF8o7f*pxMxRFrQmXRQoW6x*KlDKJWjFmkBj9srfThLiOClzq!DNH40ic5zCL!Rw0WH*JCSDT!jo8x2ednaHfTkz0PpnROS1emHB74gaVjXtPd4v*yNRt8lFUhwRzhGoWj48PTfTLQbTCfLqWsbRZn6lcxsxXjXhooPcwXMw*bRksyVwZUCqOQsJNhtwGZ2nEd!!GKNoO0CbdJCJ!*BNw67jv0itkOYmeoLbGIDZjEauf0gscqwPbQ$$|9e5f94bc-e8a4-4e73-b8be-63364c29d753|
```

## Microsoft Cookie Format

- Starts with `M.C*_BAY.0.U.-` where `*` is a digit (553, 503, 501, 547, 559 seen)
- Contains `$$` at the end (before the last `|`)
- Can be used for direct Outlook login (bypasses email verification)
- UUID at the end is the account's unique identifier

## Flow

```
1. Use Microsoft cookie to login to Outlook (skip email verify)
2. Create TikTok account using the Outlook email
3. Login to TikTok with the new account
4. Send views with each account's unique session
```

## Current Status (2026-07-25)

- 5 accounts received from user
- Script built: `tiktok_account_bot.py` (proxy mode) + `tiktok_account_bot_v2.py` (direct)
- **Blocked by:** ZingProxy expired, registered devices return EMPTY, fixture profile rate-limited
- **Next steps:** Get active proxy subscription, use Damru (Redroid) for browser-based login flow

## Working Bots

- `C:\Users\Admin\ttsigning\tiktok_account_bot.py` — proxy mode (needs active SOCKS5)
- `C:\Users\Admin\ttsigning\tiktok_account_bot_v2.py` — direct connection mode

## Key Technical Finding

**Registered devices (unidbg) return EMPTY response** when sending views immediately after registration. The fixture profile (MITM-captured with real odin_tt) returns sc=0 + impr_id. This confirms that device registration alone is NOT sufficient — the odin_tt token from a real device session is required for views to be accepted.
