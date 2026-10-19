# TikTok Lite API Test (aid=1340) — 2026-07-25

## Summary

**TikTok Lite (aid=1340, app_name=musically_go) is HARD-BLOCKED on standard TikTok API hosts.** This is an app-identity rejection (`Tt_block: 2022`), NOT a rate limit. Standard TikTok (aid=1233) works fine through the same proxy.

## Comparative Test Results

### Test Setup
- **Proxy**: SOCKS5 `ehzte_duyho@117.0.113.155:40917` (IP: 171.229.223.93)
- **Video**: `7654840470471789845`
- **Profile**: `device_v44_3_1.json` fixture (modified for aid=1340)
- **Signing**: `sign_with_aid()` — passes correct aid to `compute_ladon()` and `compute_argus()`

### Results by Host

| Host | aid=1233 (musical_ly) | aid=1340 (musically_go) |
|------|----------------------|------------------------|
| `api16-normal-c-alisg.tiktokv.com` | ✅ HTTP 200, status_code=0, impr_id present | ❌ HTTP 403, Tt_block=2022, empty body |
| `api22-normal-c-alisg.tiktokv.com` | ✅ HTTP 200, status_code=0, impr_id present | ❌ HTTP 403, Tt_block=2022, empty body |
| `api16-normal-sg.tiktokv.com` | ❌ Connection refused | ❌ Connection refused |
| `api16-normal-useast5.tiktokv.com` | ❌ Connection refused | ❌ Connection refused |
| `api16-core-useast5.tiktokv.us` | ❌ HTTP 404 | ❌ HTTP 404 |

### Key Observations

1. **aid=1233 succeeds on both `.tiktokv.com` hosts** — 2/5 hosts work, returning status_code=0 with unique impr_id
2. **aid=1340 blocked on ALL reachable hosts** — 403 with `Tt_block: 2022`
3. **Same proxy, same profile, same signing engine** — only the aid value differs
4. **`.tiktokv.us` returns 404 for both** — different API path structure, not aid-specific
5. **Warmup `/get_domains/v5/` also returns 404** for aid=1340 on `.tiktokv.us`

### HTTP 403 Response Headers (aid=1340)

```
Content-Type: application/json
Content-Length: 0
Tt_stable: 1
Tt_block: 2022
X-Janus-Info: <base64 challenge token>
X-Tt-Logid: 20260725132021...
Server: TLB
```

- `Tt_block: 2022` = app identity rejection
- `Content-Length: 0` = no response body (no error details)
- `X-Janus-Info` = anti-bot challenge (not useful for bypass)

### Warmup Test (aid=1340)

```
GET /get_domains/v5/ → HTTP 404
```

The warmup endpoint also rejects TikTok Lite, confirming the host-level block.

## Technical Details

### `sign_with_aid()` Pattern

The default `sign()` function in `ttk/signing_engine.py` silently defaults to `aid=1233` for X-Ladon and X-Argus. To test alternative aids:

```python
def sign_with_aid(url, method, body, cookie, ts, aid_int):
    """Sign with correct aid in Ladon/Argus signatures."""
    parsed = urlparse(url)
    qs = parsed.query
    body_bytes = body.encode("utf-8") if isinstance(body, str) else (body or b"")
    stub = compute_stub(body_bytes) if body_bytes and method.upper() != "GET" else ""

    gorgon_data = compute_gorgon(query_string=qs, stub=stub, cookie=cookie, ts=ts)
    argus = compute_argus(query_string=qs, stub=stub or None, ts=ts, aid=aid_int)
    ladon = compute_ladon(ts=ts, aid=aid_int)

    result = {
        "X-Khronos": gorgon_data["X-Khronos"],
        "X-Gorgon": gorgon_data["X-Gorgon"],
        "X-Ladon": ladon,
        "X-Argus": argus,
    }
    if stub:
        result["X-SS-STUB"] = stub
    return result
```

### Signature Differences by Aid

Verified that changing aid produces different Ladon/Argus but identical Gorgon:

```
aid=1233: Ladon=..., Argus=...
aid=1340: Ladon=DIFFERENT, Argus=DIFFERENT
Gorgon: IDENTICAL (URL-hash-based, doesn't embed aid)
Khronos: IDENTICAL (same timestamp)
```

## Conclusions

1. **TikTok Lite API is NOT a viable rate-limit bypass** — the server validates app identity at the gateway level
2. **`Tt_block: 2022` is a hard rejection**, not a soft rate limit — no amount of delays, headers, or cookie manipulation will help
3. **Different aid values don't access different rate-limit pools** — they access different (or no) endpoints entirely
4. **The standard API hosts only serve standard TikTok (aid=1233)** — TikTok Lite would need its own dedicated host
5. **The `sign()` function needs aid parameter** for any cross-app testing — defaulting to 1233 creates signature mismatches

## Test Scripts

- `test_tiktok_lite.py` — Standalone TikTok Lite test with warmup + view sending
- `test_comparative.py` — Head-to-head comparison across aids and hosts
- `test_tiktok_lite_results.json` — Raw results from Lite-only test
- `test_comparative_results.json` — Raw results from comparative test
