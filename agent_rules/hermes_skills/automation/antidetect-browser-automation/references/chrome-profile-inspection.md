# Chrome/Chromium Profile Inspection on Windows

## Finding Browser Profiles

### Chrome
```
C:\Users\<user>\AppData\Local\Google\Chrome\User Data\
├── Default\              # Primary profile
├── Profile 1\            # Additional profiles
├── Profile 2\
├── Profile 3\
└── System Profile\       # Internal, skip
```

### Edge
```
C:\Users\<user>\AppData\Local\Microsoft\Edge\User Data\
├── Default\
```

### GPM Login
```
<install_path>/gpm/
├── database.db
├── <uuid-1>/             # Each profile is a UUID folder
│   └── Default\          # Full Chrome profile structure inside
│       ├── Network/Cookies
│       ├── Login Data
│       ├── History
│       └── ...
```

### Other Chromium-based
```
C:\Users\<user>\AppData\Local\BraveSoftware\Brave-Browser\User Data\
C:\Users\<user>\AppData\Local\Chromium\User Data\
C:\Users\<user>\AppData\Local\Opera Software\Opera Stable\
```

## Cookie Database Location (Modern Chrome)

**PITFALL:** Modern Chrome stores cookies in `Network/Cookies`, NOT in `Cookies` at the profile root.
```
<profile>/Network/Cookies      ← actual cookies DB
<profile>/Cookies-journal      ← WAL journal (may also exist at Network/ level)
```

## Cookie DB Locking When Chrome Is Running

When Chrome processes are active (`tasklist | grep chrome`), the Cookies SQLite database gets locked. Copying it produces an **empty database** (no tables, 0 rows) — the copy appears to succeed but is useless.

**Workaround — use History instead:**
- `History` DB (table `urls`) can be copied and queried even while Chrome runs
- `Login Data` DB (table `logins`) can also be copied and queried
- Only `Cookies` is reliably locked

```python
import sqlite3, shutil

# Copy History (works even with Chrome running)
src = 'C:/Users/Admin/AppData/Local/Google/Chrome/User Data/Profile 3/History'
dst = '/tmp/history_copy.db'
shutil.copy2(src, dst)
db = sqlite3.connect(dst)
cur = db.cursor()
cur.execute("SELECT url, title, last_visit_time FROM urls WHERE url LIKE '%target-site%' ORDER BY last_visit_time DESC")
```

## Determining If a Profile Is Logged In (Without Cookies)

When cookies are inaccessible, check History for authenticated-page URLs:

| Site Pattern | Authenticated URLs |
|---|---|
| Gumroad | `gumroad.com/dashboard`, `gumroad.com/settings`, `gumroad.com/payouts` |
| Google | `myaccount.google.com`, `mail.google.com` |
| GitHub | `github.com/dashboard`, `github.com/settings` |
| Generic | `/dashboard`, `/account`, `/settings`, `/profile` |

Also check for OAuth callback URLs confirming successful auth:
```
gumroad.com/users/auth/google_oauth2/callback?...&code=...
```

## Chrome Timestamps

Chrome uses WebKit epoch (1601-01-01), microseconds:
```python
import datetime

def chrome_time_to_datetime(chrome_ts):
    if not chrome_ts:
        return None
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=chrome_ts)
```

## Python sqlite3 for Profile Inspection

sqlite3 CLI may not be installed on Windows. Python's built-in `sqlite3` module always works:
```python
import sqlite3
db = sqlite3.connect('path/to/copied/db')
cur = db.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")  # list tables
```

**PITFALL:** If `sqlite_master` returns empty list `[]`, the copy was likely corrupted by file locking. Copy the source file again or ensure the browser is closed.

## Checking Saved Credentials

```python
cur.execute("SELECT origin_url, username_value FROM logins WHERE origin_url LIKE '%target%'")
```

Note: OAuth-based logins (Google, Apple) typically do NOT save passwords in Login Data. The session cookie is the only credential, and it lives in the locked Cookies DB.
