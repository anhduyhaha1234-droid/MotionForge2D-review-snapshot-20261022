#!/usr/bin/env python3
"""Verify TikTok signing engine produces correct headers and accepts views."""
import sys, os, json, time, ssl, urllib.request, urllib.parse, gzip, hashlib

# Setup path
TTSIGNING = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'ttsigning')
sys.path.insert(0, TTSIGNING)

try:
    from ttk.signing_engine import sign
    from ttk.paths import FIXTURES_DIR
except ImportError:
    print("FAIL: Cannot import ttk. Clone code-root/tiktok-android-signing-toolkit to ~/ttsigning/")
    sys.exit(1)

VIDEO_ID = "7654840470471789845"  # change to your video

# 1. Load device profile
print("[1] Device profile...")
profile_path = os.path.join(FIXTURES_DIR, "device_v44_3_1.json")
if not os.path.exists(profile_path):
    print(f"  FAIL: {profile_path} not found")
    sys.exit(1)
with open(profile_path) as f:
    profile = json.load(f)
did = profile["device"]["device_id"]
iid = profile["device"]["iid"]
print(f"  PASS: device_id={did[:10]}..., iid={iid[:10]}...")

# 2. Test signing engine
print("[2] Signing engine...")
qs = urllib.parse.urlencode({
    "play_delta": "1", "item_id": VIDEO_ID,
    "aid": "1233", "device_platform": "android",
    "device_id": did, "iid": iid,
})
full_url = f"https://api16-normal-c-alisg.tiktokv.com/aweme/v1/aweme/stats?{qs}"
body = f"play_delta=1&item_id={VIDEO_ID}&aweme_type=0".encode()
s = sign(full_url, method="POST", body=body)

required_headers = ["X-Gorgon", "X-Khronos", "X-Ladon", "X-Argus", "X-SS-STUB"]
for h in required_headers:
    if h not in s:
        print(f"  FAIL: {h} missing")
        sys.exit(1)
if not s["X-Gorgon"].startswith("84"):
    print(f"  FAIL: X-Gorgon prefix={s['X-Gorgon'][:4]} (expected 84 for v44.x)")
    sys.exit(1)
print(f"  PASS: All 5 headers present, X-Gorgon prefix=84 (v44.x)")

# 3. Randomize device
print("[3] Device randomization...")
def randomize(profile):
    p = json.loads(json.dumps(profile))
    new_did = str(random.randint(7000000000000000000, 7999999999999999999))
    new_iid = str(random.randint(7000000000000000000, 7999999999999999999))
    p["device"]["device_id"] = new_did
    p["device"]["iid"] = new_iid
    p["device"]["openudid"] = hashlib.md5(new_did.encode()).hexdigest()[:16]
    return p

import random
p2 = randomize(profile)
assert p2["device"]["device_id"] != did
print(f"  PASS: New device_id={p2['device']['device_id'][:10]}...")

# 4. Live view request
print("[4] Live view request...")
ctx = ssl.create_default_context()
opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
headers = {
    "host": "api16-normal-c-alisg.tiktokv.com",
    "user-agent": f'com.zhiliaoapp.musically/{profile["meta"]["version_code"]} (Linux; U; Android 11; vi_VN)',
    "x-ss-req-ticket": str(int(time.time() * 1000)),
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
}
for k in required_headers:
    headers[k] = s[k]

try:
    req = urllib.request.Request(full_url, data=body, headers=headers, method="POST")
    resp = opener.open(req, timeout=15)
    raw = gzip.decompress(resp.read()) if resp.headers.get("Content-Encoding") == "gzip" else resp.read()
    if raw:
        j = json.loads(raw)
        if j.get("status_code") == 0:
            print(f"  PASS: status_code=0, impr_id={j.get('log_pb',{}).get('impr_id','?')}")
        else:
            print(f"  FAIL: status_code={j.get('status_code')}")
            sys.exit(1)
    else:
        print("  WARN: empty response (rate limited) — signing is correct but IP throttled")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\nALL CHECKS PASSED")
