#!/usr/bin/env python3
"""
Standalone batch profile generator.
Combines: unidbg device registration + EC P-256 keys + full profile assembly.

Usage:
    python batch_generate_profiles_standalone.py -n 10 --region US
    python batch_generate_profiles_standalone.py -n 5 --region VN -o ./profiles

Requirements:
    - Java JDK 21+ in PATH
    - pycryptodome: pip install pycryptodome
    - requests: pip install requests
    - unidbg.jar + native DLLs in Libs/prebuilt/<platform>/
"""
import argparse, base64, binascii, hashlib, json, os, platform, random
import re, secrets, shutil, subprocess, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

try:
    from Crypto.PublicKey import ECC
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome"])
    from Crypto.PublicKey import ECC

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# ── Config ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
LIBS_PATH = SCRIPT_DIR / "Libs"
JNI_PATH = LIBS_PATH / "prebuilt"
DEVICE_REGISTER_URL = "https://log-va.tiktokv.com/service/2/device_register/"

DEVICE_MODELS = [
    ("SM-S928B","samsung","35","15","1440*3120","560","arm64-v8a"),
    ("SM-S921B","samsung","35","15","1080*2340","420","arm64-v8a"),
    ("Pixel 8 Pro","google","35","15","1344*2992","489","arm64-v8a"),
    ("Pixel 7","google","34","14","1080*2400","416","arm64-v8a"),
    ("2311DRK48C","Xiaomi","34","14","1440*3200","522","arm64-v8a"),
    ("CPH2449","OnePlus","34","14","1440*3216","526","arm64-v8a"),
    ("M2101K6G","Xiaomi","34","14","1080*2400","440","arm64-v8a"),
    ("NE2215","OnePlus","34","14","1080*2400","420","arm64-v8a"),
    ("V2109","vivo","34","14","1080*2400","440","arm64-v8a"),
    ("RMX3085","realme","34","14","1080*2400","409","arm64-v8a"),
]

REGION_TZ = {
    "US":("America/New_York","-18000"), "VN":("Asia/Ho_Chi_Minh","25200"),
    "GB":("Europe/London","0"), "JP":("Asia/Tokyo","32400"),
    "KR":("Asia/Seoul","32400"), "IN":("Asia/Kolkata","19800"),
    "SG":("Asia/Singapore","28800"), "TH":("Asia/Bangkok","25200"),
}
REGION_MCC = {"US":"310260","VN":"45204","GB":"23420","JP":"44020","KR":"45008","IN":"40415","SG":"52505","TH":"52001"}
REGION_IDC = {"US":"useast5","VN":"sg","GB":"eu","JP":"jp","KR":"kr","IN":"sg","SG":"sg","TH":"sg"}

# ── Helpers ────────────────────────────────────────────────────────────────
def getsystem():
    s = platform.system()
    if s.startswith("Win"): return "win" + platform.machine()[-2:]
    if s.startswith("Lin"): return "linux" + platform.machine()[-2:]
    return "osx64"

def get_java():
    win = platform.system().startswith("Win")
    name = "java.exe" if win else "java"
    jh = os.environ.get("JAVA_HOME")
    if jh:
        p = Path(jh) / "bin" / name
        if p.is_file(): return str(p.resolve())
    w = shutil.which("java")
    if w: return str(Path(w).resolve())
    return "java"

def rand_openudid(): return secrets.token_hex(8)

def rand_mac():
    return ":".join(f"{random.randint(0,255):02x}" for _ in range(6))

# ── Device Registration ────────────────────────────────────────────────────
def register_device(java_exe, idx=0):
    sys_plat = getsystem()
    jni = JNI_PATH / sys_plat
    if not jni.exists(): return False, {"error": f"JNI not found: {jni}"}

    now_ms = str(int(time.time() * 1000))
    ud_id = str(random.randint(221480502743165, 821480502743165))
    openudid = rand_openudid()
    mac = rand_mac()
    msg = f"{now_ms} {ud_id} {openudid} {mac}"

    jp = str(jni.resolve())
    cmd = '"{2}" -Djna.library.path="{0}" -Djava.library.path="{0}" -jar unidbg.jar {1}'.format(jp, msg, java_exe)
    try:
        r = subprocess.run(cmd, cwd=str(LIBS_PATH), shell=True, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False, {"error": "Java timed out"}

    out = r.stdout.decode("utf-8", errors="replace")
    err = r.stderr.decode("utf-8", errors="replace")
    m = re.search(r"(?is)hex\s*=\s*([\s\S]*?)\r?\n\s*size\b", f"{out}\n{err}")
    if not m: m = re.search(r"(?is)hex\s*=\s*([0-9a-fA-F\s]+)", f"{out}\n{err}")
    if not m: return False, {"error": "unidbg parse failed", "stderr": out[:1000]}

    try:
        body = binascii.unhexlify(re.sub(r"\s+", "", m.group(1)).encode("ascii"))
    except Exception as e:
        return False, {"error": f"hex decode: {e}"}

    try:
        resp = requests.post(DEVICE_REGISTER_URL, data=body,
            headers={"user-agent":"com.zhiliaoapp.musically/2023105030",
                     "content-type":"application/octet-stream;tt-data=a"}, timeout=30)
        resp.raise_for_status()
        j = resp.json()
    except Exception as e:
        return False, {"error": f"HTTP: {e}"}

    if "device_id" not in j or "install_id" not in j:
        return False, {"error": "Missing IDs", "response": j}

    return True, {"device_id": str(j["device_id"]), "install_id": str(j["install_id"]),
                  "openudid": openudid, "ud_id": ud_id, "mac": mac}

# ── EC Keys ────────────────────────────────────────────────────────────────
def gen_ec_keys():
    k = ECC.generate(curve="P-256")
    return {"private_pem": k.export_key("PEM"),
            "public_pem": k.public_key().export_key("PEM"),
            "tt_ticket_guard_public_key": base64.b64encode(k.public_key().export_key("raw")).decode()}

# ── Profile Builder ────────────────────────────────────────────────────────
def build_profile(dev, keys, region="US", model=None):
    if model is None: model = random.choice(DEVICE_MODELS)
    dt, db, api, osv, res, dpi, abi = model
    tzo, tzn = REGION_TZ.get(region, ("America/New_York","-18000"))
    mcc = REGION_MCC.get(region, "310260")
    idc = REGION_IDC.get(region, "useast5")
    did, iid, ouid = dev["device_id"], dev["install_id"], dev["openudid"]
    now = int(time.time())
    cdid, cludid = str(uuid.uuid4()), str(uuid.uuid4())
    odin = hashlib.sha512(f"{did}:{ouid}:{cdid}:{now}".encode()).hexdigest()[:128]
    cookie = f"store-idc={idc}; store-country-code={region.lower()}; store-country-code-src=did; tt-target-idc={idc}; install_id={iid}; odin_tt={odin}"
    return {
        "_comment": f"Generated — region={region}, device={dt}",
        "meta": {"version":"44.3.15","version_code":"2024403150","manifest_version_code":"2024403150",
                 "update_version_code":"2024403150","ab_version":"44.3.15","build_number":"44.3.15",
                 "sig_hash":"194326e82c84a639a52e5c023116f12a","git_hash":"5ae517f",
                 "sdk_version":"2.5.14.3","sdk_version_code":205140390,"rom":"UP1A.231005.007",
                 "rom_version":f"generic/{dt}/{dt}:{osv}/UP1A.231005.007/UP1A.231005.007:user/release-keys",
                 "build_id":"UP1A.231005.007","release_build":"b2a796d_20260312",
                 "generated_at":now,"generated_date":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "region":region},
        "device": {"device_id":did,"iid":iid,"openudid":ouid,"cdid":cdid,"clientudid":cludid,
                   "google_aid":str(uuid.uuid4()),"device_type":dt,"device_brand":db,
                   "device_manufacturer":db,"os_version":osv,"os_api":api,"resolution":res,
                   "dpi":dpi,"host_abi":abi,"build_fingerprint":"UP1A.231005.007","is_pad":"0"},
        "app": {"app_name":"musical_ly","package":"com.zhiliaoapp.musically","aid":"1233",
                "channel":"googleplay","ssmix":"a","app_type":"normal","support_webview":"1"},
        "network": {"ac":"wifi","ac2":"wifi","mcc_mnc":mcc,"carrier_region":region,
                    "carrier_region_v2":mcc[:3],"sim_region":region.lower(),"carrier":""},
        "locale": {"timezone_name":tzn,"timezone_offset":tzo,"language":"en","locale":"en",
                   "app_language":"en","sys_region":region,"region":region,"op_region":region,"uoo":"0"},
        "user_agent": f"com.zhiliaoapp.musically/2024403150 (Linux; U; Android {osv}; en_US; {dt}; Build/UP1A.231005.007; Cronet/TTNetVersion:80a1e1d9 2026-01-21 QuicVersion:5f252c33 2025-12-30)",
        "passport_headers": {"x-tt-dm-status":"login=0;ct=0;rt=7"},
        "session": {"cookie":cookie,"last_install_time":str(now - random.randint(7*86400,90*86400)),
                    "x_tt_token":"","session_key":""},
        "guard_keys": {"_comment":"EC P-256 key pair for guard signing",
                       "private_pem":keys["private_pem"],"public_pem":keys["public_pem"],
                       "tt_ticket_guard_public_key":keys["tt_ticket_guard_public_key"]},
        "guard_headers": {"tt-ticket-guard-public-key":keys["tt_ticket_guard_public_key"],
                          "tt-ticket-guard-iteration-version":"0","tt-ticket-guard-version":"3",
                          "tt-device-guard-iteration-version":"1","tt-device-guard-client-data":""},
    }

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Batch TikTok Profile Generator")
    ap.add_argument("-n","--count",type=int,default=10)
    ap.add_argument("-r","--region",type=str,default="US")
    ap.add_argument("-o","--output-dir",type=str,default=None)
    ap.add_argument("--java",type=str,default=None)
    ap.add_argument("--delay",type=float,default=0.5)
    a = ap.parse_args()

    java = a.java or get_java()
    out = Path(a.output_dir or SCRIPT_DIR / "generated_profiles")
    out.mkdir(parents=True, exist_ok=True)
    start = len(list(out.glob("profile_*.json"))) + 1

    ok = fail = 0
    for i in range(a.count):
        idx = start + i
        print(f"  [{i+1}/{a.count}] Profile #{idx}...", end=" ", flush=True)
        s, d = register_device(java, idx)
        if not s:
            fail += 1; print(f"FAIL — {d.get('error')}"); continue
        p = build_profile(d, gen_ec_keys(), a.region)
        fn = out / f"profile_{idx:04d}_{d['device_id']}.json"
        fn.write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")
        ok += 1; print(f"OK — device_id={d['device_id']}")
        if a.delay > 0 and i < a.count - 1: time.sleep(a.delay)

    print(f"\n[done] {ok} ok, {fail} fail → {out}")

if __name__ == "__main__":
    main()
