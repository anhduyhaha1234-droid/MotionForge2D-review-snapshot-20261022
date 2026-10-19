# TikTok API Endpoints

## View Sending (WORKING as of 2026-07)

### POST /aweme/v1/aweme/stats
```
Host: api16-normal-c-alisg.tiktokv.com
Method: POST
Content-Type: application/x-www-form-urlencoded

Query params:
  play_delta=1
  item_id={VIDEO_ID}
  aweme_type=0
  aid=1233
  device_platform=android
  device_id={RANDOM_19_DIGIT}
  iid={RANDOM_19_DIGIT}
  os_api={25-34}
  device_type={Samsung model}
  ssmix=a
  manifest_version_code={version_code * 10}
  dpi={420-640}
  region=VN
  carrier_region=VN
  uoo=0
  app_name=musical_ly
  version_name={version}
  timezone_offset=-25200
  ts={unix_timestamp}
  ab_version={version}
  ac=wifi
  app_type=normal
  channel=googleplay
  update_version_code={version_code * 10}
  _rticket={unix_ms}
  locale=vi_VN
  version_code={version_code}
  timezone_name=Asia/Ho_Chi_Minh
  openudid={md5 of device_id, first 16 chars}
  sys_region=VN
  app_language=vi_VN
  resolution={width}x{height}
  device_brand=samsung
  language=vi_VN

POST body (form-urlencoded):
  play_delta=1&item_id={VIDEO_ID}&aweme_type=0

Required headers:
  host: api16-normal-c-alisg.tiktokv.com
  user-agent: com.zhiliaoapp.musically/{version_code} (Linux; U; Android {ver}; vi_VN; {device}; Build/...)
  x-ss-req-ticket: {unix_ms}
  content-type: application/x-www-form-urlencoded; charset=UTF-8
  X-Gorgon: {v44.x signed}
  X-Khronos: {unix_timestamp}
  X-Ladon: {encrypted}
  X-Argus: {encrypted}
  X-SS-STUB: {MD5 of POST body, uppercase}

Response (success):
  {"extra":{"now":TIMESTAMP},"log_pb":{"impr_id":"UUID"},"status_code":0}

Response (rate limited):
  empty body with HTTP 200
```

## Video Detail

### GET /aweme/v1/aweme/detail/
```
Query: aweme_id={VIDEO_ID}&aid=1233
Requires: Same signing headers as stats
Response: {"aweme_detail": {"statistics": {"play_count": N, "digg_count": N, ...}}}
Note: Returns 403 without proper signing
```

## Device Registration

### POST /device/register
```
Requires: TTEncrypt body encryption
Full implementation in: ttsigning/ttk/device_register.py
Generates: device_id, install_id, openudid, cdid
```

## Available API Hosts (resolving from VN)
```
api16-normal-c-alisg.tiktokv.com  (Singapore CDN - 113.171.230.x)
api19-normal-c-alisg.tiktokv.com
api16.tiktokv.com
api19.tiktokv.com
api.tiktokv.com
```

## Dead/Blocked Hosts
```
api-v4.tikapis.com  — DNS non-existent
api16-core-c-useast1a.tiktokv.com  — returns empty 200, views not counted
api22-core-c-useast1a.tiktokv.com  — same
api16-normal-c-useast5.tiktokv.com  — DNS non-existent
```

## TikTok Lite (aid=1340) — BLOCKED (2026-07-25)

**All standard hosts reject aid=1340 (musically_go) with HTTP 403, `Tt_block: 2022`.**

| Host | aid=1233 (musical_ly) | aid=1340 (musically_go) |
|------|----------------------|------------------------|
| api16-normal-c-alisg.tiktokv.com | ✅ HTTP 200, status_code=0 | ❌ HTTP 403, Tt_block=2022 |
| api22-normal-c-alisg.tiktokv.com | ✅ HTTP 200, status_code=0 | ❌ HTTP 403, Tt_block=2022 |
| api16-core-useast5.tiktokv.us | ❌ HTTP 404 | ❌ HTTP 404 |

**The block is at the API gateway level**: the server validates the `aid` parameter and rejects unrecognized apps. The `sign()` function also defaults to `aid=1233` for X-Ladon/X-Argus — changing only the URL `aid` creates a signature mismatch. Use `sign_with_aid()` pattern for any aid changes. Full details: `references/tiktok-lite-api-test-2026-07.md`.
