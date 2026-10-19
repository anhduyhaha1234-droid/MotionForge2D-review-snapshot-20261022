"""
Proxy Connectivity Test Script
Usage: python test_proxies.py <proxy_file> <target_url>

Proxy file format (one per line):
  host:port:user:pass

Tests each proxy with: TCP connect, SOCKS5, HTTP, and target-specific fetch.
Outputs pass/fail per proxy with timing.
"""

import sys, socket, subprocess, time, re

def test_tcp(host, port, timeout=5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, int(port)))
        s.close()
        return True, 'CONNECTED'
    except Exception as e:
        return False, str(e)[:40]

def test_socks5(proxy, target, timeout=15):
    host, port, user, pw = proxy.split(':')
    auth = f'{user}:{pw}@{host}:{port}'
    cmd = f'curl -s --socks5-hostname "{auth}" --max-time {timeout} -w "CODE:%{{http_code}} SIZE:%{{size_download}}" "{target}" | tail -c 60'
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout+5)
        m = re.search(r'CODE:(\d+) SIZE:(\d+)', r.stdout[-60:])
        if m:
            code, size = int(m.group(1)), int(m.group(2))
            return code == 200 and size > 10000, f'HTTP {code} | {size:,} bytes'
        return False, r.stdout.strip()[:50] or 'no response'
    except Exception as e:
        return False, str(e)[:40]

def test_http(proxy, target, timeout=15):
    host, port, user, pw = proxy.split(':')
    auth = f'{user}:{pw}@{host}:{port}'
    cmd = f'curl -s -x "http://{auth}" --max-time {timeout} -w "CODE:%{{http_code}} SIZE:%{{size_download}}" "{target}" | tail -c 60'
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout+5)
        m = re.search(r'CODE:(\d+) SIZE:(\d+)', r.stdout[-60:])
        if m:
            code, size = int(m.group(1)), int(m.group(2))
            return code == 200 and size > 10000, f'HTTP {code} | {size:,} bytes'
        return False, r.stdout.strip()[:50] or 'no response'
    except Exception as e:
        return False, str(e)[:40]

def main():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <proxy_file> <target_url>')
        sys.exit(1)
    
    proxy_file = sys.argv[1]
    target = sys.argv[2]
    
    with open(proxy_file) as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f'Loaded {len(proxies)} proxies from {proxy_file}')
    print(f'Target: {target}')
    print('=' * 80)
    
    working = []
    for i, proxy in enumerate(proxies):
        host, port, user, pw = proxy.split(':')
        label = f'{host}:{port}'
        
        # Test TCP
        tcp_ok, tcp_msg = test_tcp(host, int(port))
        
        # Test SOCKS5
        s5_ok, s5_msg = test_socks5(proxy, target)
        
        # Test HTTP (optional - only if SOCKS5 fails)
        http_ok, http_msg = (False, 'skipped')
        if not s5_ok:
            http_ok, http_msg = test_http(proxy, target)
        
        ok = s5_ok or http_ok
        if ok:
            working.append(proxy)
            method = 'SOCKS5' if s5_ok else 'HTTP'
            msg = s5_msg if s5_ok else http_msg
        else:
            method = 'FAIL'
            msg = s5_msg
        
        status = '✅' if ok else '❌'
        print(f'  [{i+1:3d}] {status} {label:30s} TCP:{tcp_ok!s:5s} {method:6s} | {msg}')
    
    print('=' * 80)
    print(f'Result: {len(working)}/{len(proxies)} proxies working')
    
    if working:
        out_file = proxy_file.replace('.txt', '_working.txt').replace('.csv', '_working.txt')
        with open(out_file, 'w') as f:
            f.write('\n'.join(working))
        print(f'Saved working proxies to: {out_file}')

if __name__ == '__main__':
    main()
