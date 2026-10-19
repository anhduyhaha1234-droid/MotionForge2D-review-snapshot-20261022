# GPM Login Global API Reference

**Version tested:** v5.0.3-stable (July 2026)  
**App path:** `C:\Users\Admin\AppData\Local\Programs\GPMLoginGlobal\GPMLoginGlobal.exe`  
**Data path:** `C:\Users\Admin\Downloads\gpm\` (configurable in setting.dat)  
**DB:** SQLite at `{data_path}/database.db`

## Ports

| Port | Purpose | Notes |
|------|---------|-------|
| 9495 | REST API (HTTP) | Default. Check with `netstat -ano \| grep 9495` |
| 9496 | WebSocket (UI) | Electron frontend ↔ backend. NOT the automation API |
| 19996 | Config in setting.dat | IGNORED by the running process — the actual API port is 9495 |

**Finding the real port:** If 9495 is busy, GPM picks a port in 8000-10000 and writes it to `http.port` in the app's local data folder.

## Base URL

```
http://127.0.0.1:9495/api/v1
```

No auth token required — localhost only.

## Response Envelope

```json
{
  "success": true,
  "data": {},
  "message": "OK",
  "sender": "GPMLoginGlobal v5.0.3-stable"
}
```

## Pagination

Query params: `page` (default 1), `page_size` (default 30), `search`, `sort` (0=newest, 1=oldest, 2=name A-Z, 3=name Z-A)

Response shape:
```json
{"current_page": 1, "per_page": 30, "total": 120, "last_page": 4, "data": []}
```

## Endpoints — Profiles

### List Profiles
```
GET /api/v1/profiles?page=1&page_size=30&search=&sort=0
```
Returns lightweight list (no full fingerprint data).

### Get Profile Detail
```
GET /api/v1/profiles/{id}
```
Returns full fingerprint data.

### Create Profile
```
POST /api/v1/profiles/create
Content-Type: application/json
```

**Required:** `name` (string)

**Optional fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| group_id | string | null | Group UUID |
| raw_proxy | string | - | `socks5://user:pass@host:port` |
| bypass_proxy_extensions | string | - | Domains bypassing proxy |
| browser_type | enum | chrome (1) | 1=Chrome, 2=Firefox |
| browser_version | string | newest | See /browsers/versions |
| os_type | enum | current OS | 1=Win, 2=macOS Intel, 3=macOS ARM, 4=Linux, 5=Android |
| custom_user_agent | string | - | Manual UA override |
| task_bar_title | string | - | Window title |
| webrtc_mode | enum | - | 1=BasedOnIP, 2=Fixed, 3=Real, 4=Disabled |
| fixed_webrtc_public_ip | string | - | Required when webrtc_mode=2 |
| port_protect | string | - | Protected ports |
| geolocation_mode | enum | - | 1=Allow, 2=Prompt, 3=Block |
| canvas_mode | enum | - | 1=Noise, 2=Real, 3=Block |
| client_rect_mode | enum | - | 1=Noise, 2=Real |
| webgl_image_mode | enum | - | 1=Noise, 2=Real |
| webgl_metadata_mode | enum | - | 1=Masked, 2=Real |
| audio_mode | enum | - | 1=Noise, 2=Real |
| is_masked_media | bool | false | Mask camera/mic/speaker |
| font_mode | enum | - | 1=Masked, 2=Real |
| timezone_base_on_ip | bool | true | Follow proxy timezone |
| timezone | string | - | Fixed timezone (e.g. Asia/Ho_Chi_Minh) |
| is_language_base_on_ip | bool | true | Follow proxy language |
| fixed_language | string | - | Fixed language (vi, en, zh) |
| startup_urls | string | - | URLs on startup (newline separated) |
| note | string | - | Profile note |

### Update Profile
```
POST /api/v1/profiles/{id}
Content-Type: application/json
```
Same fields as create. Only send fields to change.

### Delete Profile(s)
```
POST /api/v1/profiles/delete
Content-Type: application/json
{"ids": ["uuid1", "uuid2"]}
```
Note: Uses soft-delete. Profile may still appear in list with `is_deleted` flag.

### Start Browser
```
GET /api/v1/profiles/start/{id}
```
Response:
```json
{
  "success": true,
  "data": {
    "profile_id": "uuid",
    "driver_path": "C:\\...\\gpmdriver.exe",
    "remote_debugging_port": 62466,
    "websocket_debugging_url": "",
    "addition_info": {
      "process_id": 30532,
      "profile_name": "Profile 01",
      "window_handle": 0,
      "exec_time": 4401
    }
  }
}
```
**Key:** Use `remote_debugging_port` for Selenium `debugger_address`.

### Stop Browser
```
GET /api/v1/profiles/stop/{id}
```

## Endpoints — Groups

```
GET    /api/v1/groups                    # List
POST   /api/v1/groups/create             # Create (name required)
POST   /api/v1/groups/{id}               # Update
DELETE /api/v1/groups/{id}               # Delete
```

## Endpoints — Proxies

```
GET    /api/v1/proxies                   # List
POST   /api/v1/proxies/create            # Create
DELETE /api/v1/proxies/{id}              # Delete
```

## Endpoints — Browser Versions

```
GET /api/v1/browsers/versions
```
Returns available Chromium and Firefox versions. First use downloads the browser binary.

## Selenium Integration

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests

API = "http://127.0.0.1:9495/api/v1"

# 1. Create profile
resp = requests.post(f"{API}/profiles/create", json={
    "name": "My Profile",
    "raw_proxy": "socks5://user:pass@host:port"
})
profile_id = resp.json()["data"]["id"]

# 2. Start browser
resp = requests.get(f"{API}/profiles/start/{profile_id}")
data = resp.json()["data"]
debug_port = data["remote_debugging_port"]
driver_path = data["driver_path"]

# 3. Connect Selenium
options = Options()
options.debugger_address = f"127.0.0.1:{debug_port}"
service = Service(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=options)

# 4. Automate
driver.get("https://example.com")
assert driver.execute_script("return navigator.webdriver") == False

# 5. Cleanup
driver.quit()  # close Selenium session
requests.get(f"{API}/profiles/stop/{profile_id}")  # close browser
```

## DB Schema (SQLite)

Tables: `groups`, `profiles`, `proxies`, `tags`, `profile_tags`, `proxy_tags`

Key profile columns: `id`, `name`, `group_id`, `storage_path`, `fingerprint_data` (JSON), `dynamic_data` (JSON), `is_deleted`, `created_at`

## setting.dat Location

`C:\Users\Admin\AppData\Roaming\GPMLoginGlobal\setting.dat` — JSON format, editable.

Key settings:
- `api.port` — configured API port (may differ from actual)
- `storage_type` — "Local" or cloud
- `local_storage_path` — where profile data and DB live
- `use_gpu` — enable GPU rendering
- `default_profile_setting.*` — defaults for new profiles
