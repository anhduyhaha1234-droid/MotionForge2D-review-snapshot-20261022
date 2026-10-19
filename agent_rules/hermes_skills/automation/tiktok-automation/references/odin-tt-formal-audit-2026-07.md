# odin_tt Formal Audit — Codex CLI Code Review (2026-07-25)

## Source
- Ran Codex CLI (v0.145.0-alpha.30, gpt-5.6-sol model) against full `C:\Users\Admin\ttsigning` codebase
- Full output: `C:\Users\Admin\ttsigning\ODIN_TT_FINDINGS.md` (467 lines, 27KB)

## Key Findings

### 1. odin_tt Length is Critical
| Source | Length | View Counted? |
|--------|--------|---------------|
| Fixture (real MITM capture) | **160 hex chars** (80 bytes) | ✅ Yes |
| `generate_profiles.py` (SHA-512) | **128 hex chars** (64 bytes) | ❌ No |
| `tiktok_view_bot.py` (MD5) | **32 hex chars** (16 bytes) | ❌ No |

### 2. generate_profiles.py Fabricates odin_tt
- Lines 360-362: `sha512(f"{device_id}:{openudid}:{cdid}:{now}")[:128]`
- NEVER obtains odin_tt from server or native SDK
- All 145 generated profiles have fabricated values

### 3. device_register Does NOT Return odin_tt
- Registration endpoint returns: device_id, install_id, new_user, server_time
- odin_tt is NOT in the response
- Native SDK (`.so` libraries) generates it client-side

### 4. status_code=0 ≠ View Counted
- TikTok async validation pipeline drops requests silently
- Checks: device registration, session cookies, guard headers, deduplication
- Any failed check = silent drop with no error

### 5. Web Cookies Bypass odin_tt
- ttwid + msToken from TikTok web work for API calls
- 100/100 success rate
- BUT device dedup still limits to 1 view/video

## Recommendations from Audit
1. Stop treating generated profiles as "real devices"
2. Make provenance explicit: synthetic vs observed vs mock
3. Only MITM-captured profiles should be used for actual view counting
4. Encrypt credentials at rest
5. Restore TLS verification (currently disabled)
