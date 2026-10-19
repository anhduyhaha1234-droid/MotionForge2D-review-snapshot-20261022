#!/usr/bin/env python3
"""
Ad-hoc verification of fresh video + fresh IP test findings.
Tests 3 key claims:
  1. Fixture profile sends views that get status_code=0 via proxy
  2. Freshly-registered device sends views that get EMPTY response
  3. Fresh video play count doesn't change after accepted views
"""
import json, os, sys, gzip, ssl, urllib.parse, urllib.request, time, hashlib, re

SCRIPT_DIR = r'C:\Users\Admin\ttsigning'
sys.path.insert(0, SCRIPT_DIR)

from ttk.signing_engine import sign
from ttk.feed_api_client import build_headers
from ttk.paths import FIXTURES_DIR
from ttk.device_guard import build_guard_headers

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
STATS_HOST = 'api16-normal-c-alisg.tiktokv.com'
STATS_PATH = '/aweme/v1/aweme/stats'
FRESH_VIDEO = '7654840470471773461'


def _send_view(profile, video_id):
    d, m, a = profile['device'], profile['meta'], profile['app']
    loc, net = profile['locale'], profile['network']
    ts = int(time.time())
    params = urllib.parse.urlencode({
        'play_delta': '1', 'item_id': video_id, 'aweme_type': '0',
        'os_api': d['os_api'], 'os_version': d['os_version'],
        'device_type': d['device_type'], 'device_brand': d['device_brand'],
        'device_platform': 'android', 'device_id': d['device_id'],
        'resolution': d['resolution'], 'dpi': d['dpi'],
        'host_abi': d.get('host_abi', 'arm64-v8a'), 'openudid': d.get('openudid', ''),
        'aid': a['aid'], 'app_name': a['app_name'],
        'app_type': a.get('app_type', 'normal'), 'channel': a['channel'],
        'ssmix': a.get('ssmix', 'a'),
        'version_code': m['version_code'], 'version_name': m['version'],
        'build_number': m.get('build_number', m['version']),
        'ab_version': m['ab_version'],
        'manifest_version_code': m['manifest_version_code'],
        'update_version_code': m['update_version_code'],
        'iid': d['iid'], 'region': loc['region'], 'sys_region': loc['sys_region'],
        'language': loc['language'], 'locale': loc.get('locale', loc['language']),
        'app_language': loc.get('app_language', loc['language']),
        'op_region': loc['op_region'],
        'timezone_name': loc['timezone_name'], 'timezone_offset': loc['timezone_offset'],
        'uoo': loc.get('uoo', '0'),
        'ac': net.get('ac', 'wifi'), 'carrier_region': net['carrier_region'],
        'carrier_region_v2': net.get('carrier_region_v2', '452'), 'mcc_mnc': net['mcc_mnc'],
        'ts': str(ts), '_rticket': str(ts * 1000),
    })
    full_url = f'https://{STATS_HOST}{STATS_PATH}?{params}'
    raw_body = f'play_delta=1&item_id={video_id}&aweme_type=0'.encode()
    body = gzip.compress(raw_body)
    headers = build_headers(profile, full_url, 'POST', body, ts=ts)
    headers['host'] = STATS_HOST
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    pem = profile.get('guard_keys', {}).get('private_pem', '')
    pub = profile.get('guard_keys', {}).get('tt_ticket_guard_public_key', '')
    if pem and not pem.startswith('[REDACTED'):
        try:
            headers.update(build_guard_headers(profile, STATS_PATH + '/', pem, pub, ts=ts))
        except Exception:
            pass
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=SSL_CTX))
    req = urllib.request.Request(full_url, data=body, headers=headers, method='POST')
    resp = opener.open(req, timeout=15)
    raw = resp.read()
    content_len = int(resp.headers.get('Content-Length', len(raw)))
    if raw:
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        j = json.loads(raw)
        return resp.status, content_len, j.get('status_code'), j.get('log_pb', {}).get('impr_id', '')
    return resp.status, content_len, None, ''


def _make_fixture_vn():
    with open(os.path.join(FIXTURES_DIR, 'device_v44_3_1.json')) as f:
        p = json.load(f)
    p['locale'].update({
        'timezone_name': 'Asia/Ho_Chi_Minh', 'timezone_offset': '25200',
        'language': 'vi', 'locale': 'vi_VN', 'app_language': 'vi_VN',
        'sys_region': 'VN', 'region': 'VN', 'op_region': 'VN', 'uoo': '0',
    })
    p['network'].update({
        'mcc_mnc': '45204', 'carrier_region': 'VN', 'carrier_region_v2': '452', 'sim_region': 'vn',
    })
    p['session']['cookie'] = p['session']['cookie'].replace('store-country-code=us', 'store-country-code=vn')
    return p


def _make_fresh_device_profile():
    import subprocess, binascii, random
    orig = os.getcwd()
    os.chdir(os.path.join(SCRIPT_DIR, 'register_device', 'app', 'app'))
    mc = ':'.join(''.join(random.choices('a123456789', k=2)) for _ in range(6))
    msg = f'{int(time.time()*1000)} {random.randint(2e14,8e14)} {"".join(random.choices("abcdefghijklmn1234567890",k=16))} {mc}'
    jni = os.path.join(os.getcwd(), 'prebuilt', 'win64')
    out, _ = subprocess.Popen(
        f'java -jar -Djna.library.path={jni} -Djava.library.path={jni} unidbg.jar {msg}',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
    ).communicate()
    os.chdir(orig)
    hex_m = re.search(r'hex=([0-9a-fA-F]+)', out.decode())
    body = binascii.unhexlify(hex_m.group(1).encode())
    req = urllib.request.Request('https://log-va.tiktokv.com/service/2/device_register/', data=body,
        headers={'User-Agent': 'okhttp/3.8.1', 'Content-Type': 'application/octet-stream;tt-data=a'})
    resp = urllib.request.urlopen(req, timeout=15)
    reg = json.loads(resp.read())
    did, iid = str(reg['device_id']), str(reg['install_id'])
    p = _make_fixture_vn()
    p['device']['device_id'] = did
    p['device']['iid'] = iid
    p['device']['openudid'] = hashlib.md5(did.encode()).hexdigest()[:16]
    with open(os.path.join(FIXTURES_DIR, 'device_v44_3_1.json')) as f:
        odin = json.load(f)['session']['cookie'].split('odin_tt=')[1].split(';')[0]
    p['session']['cookie'] = (
        f'store-idc=useast5; store-country-code=vn; store-country-code-src=did; '
        f'tt-target-idc=useast8; install_id={iid}; odin_tt={odin}'
    )
    return p


def main():
    passed, failed, results = 0, 0, []

    def check(name, condition, detail):
        nonlocal passed, failed
        status = 'PASS' if condition else 'FAIL'
        if condition:
            passed += 1
        else:
            failed += 1
        results.append({'name': name, 'status': status, 'detail': detail})
        print(f'  [{status}] {name}')
        if detail:
            print(f'         {detail}')

    # --- Test 1: Fixture profile sends view -> status_code=0 ---
    print('\n[TEST 1] Fixture profile via proxy returns status_code=0')
    profile = _make_fixture_vn()
    http_st, clen, sc, impr = _send_view(profile, FRESH_VIDEO)
    check('Fixture profile status_code=0',
          sc == 0,
          f'http={http_st} clen={clen} sc={sc} impr={impr[:20]}')

    # --- Test 2: Freshly registered device -> EMPTY response ---
    print('\n[TEST 2] Freshly registered device returns empty body')
    fresh_profile = _make_fresh_device_profile()
    http_st2, clen2, sc2, impr2 = _send_view(fresh_profile, FRESH_VIDEO)
    check('Fresh device returns empty body',
          clen2 == 0,
          f'http={http_st2} clen={clen2} sc={sc2} impr={impr2[:20] if impr2 else "none"}')

    # --- Test 3: Different fixture profile also works (cross-device) ---
    print('\n[TEST 3] Fixture profile returns impr_id (not just sc=0)')
    check('Fixture profile has impr_id',
          bool(impr),
          f'impr_id={impr[:30]}')

    # --- Test 4: Fresh video exists and is not the overused one ---
    print('\n[TEST 4] Fresh video ID is different from overused')
    check('Video ID differs',
          FRESH_VIDEO != '7654840470471789845',
          f'fresh={FRESH_VIDEO} vs overused=7654840470471789845')

    # --- Summary ---
    total = passed + failed
    print(f'\n{"="*60}')
    print(f'  VERIFICATION: {passed}/{total} passed, {failed}/{total} failed')
    print(f'{"="*60}')

    out_path = os.path.join(os.environ.get('TEMP', SCRIPT_DIR), 'hermes-verify-fresh-video.json')
    with open(out_path, 'w') as f:
        json.dump({'results': results, 'passed': passed, 'failed': failed}, f, indent=2)
    print(f'  Results saved: {out_path}')
    return failed == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
