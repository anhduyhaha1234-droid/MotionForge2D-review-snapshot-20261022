"""
PPROXY Relay Manager
Start local HTTP proxies that tunnel to authenticated SOCKS5 upstreams.

Usage: python pproxy_relay.py start <proxy_file> [--base-port 18080]
       python pproxy_relay.py test <base_port> <count> <target_url>

Proxy file format (one per line):
  host:port:user:pass

Starts pproxy relays on ports base_port to base_port+count-1.
Each relay converts HTTP proxy -> SOCKS5 with auth.
"""

import subprocess, sys, time, socket, re

def start_relays(proxy_file, base_port=18080):
    """Start pproxy HTTP->SOCKS5 relays. Returns list of (process, local_port)."""
    with open(proxy_file) as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    procs = []
    for i, proxy in enumerate(proxies):
        host, port, user, pw = proxy.split(':')
        local_port = base_port + i
        
        cmd = [sys.executable, '-m', 'pproxy',
               '-l', f'http://0.0.0.0:{local_port}',
               '-r', f'socks5://{host}:{port}#{user}:{pw}']
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        procs.append((proc, local_port))
        time.sleep(0.3)
    
    time.sleep(3)  # Wait for all to start
    return procs

def test_relay(local_port, target_url, timeout=15):
    """Test a single pproxy relay."""
    import requests
    try:
        r = requests.get(target_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            proxies={'http': f'http://127.0.0.1:{local_port}', 'https': f'http://127.0.0.1:{local_port}'},
            timeout=timeout)
        return r.status_code, len(r.text)
    except Exception as e:
        return 0, str(e)[:60]

def cleanup(procs):
    """Terminate all relay processes."""
    for proc, _ in procs:
        try:
            proc.terminate()
        except:
            pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} start <proxy_file> [--base-port 18080]')
        print(f'       {sys.argv[0]} test <base_port> <count> <target_url>')
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'start':
        proxy_file = sys.argv[2]
        base_port = 18080
        if '--base-port' in sys.argv:
            base_port = int(sys.argv[sys.argv.index('--base-port') + 1])
        
        procs = start_relays(proxy_file, base_port)
        print(f'Started {len(procs)} relays on ports {base_port}-{base_port + len(procs) - 1}')
        print('Press Ctrl+C to stop...')
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cleanup(procs)
            print('\nCleaned up')
    
    elif action == 'test':
        base_port = int(sys.argv[2])
        count = int(sys.argv[3])
        target = sys.argv[4]
        
        print(f'Testing {count} relays (ports {base_port}-{base_port+count-1}) -> {target}')
        for i in range(count):
            port = base_port + i
            code, size = test_relay(port, target)
            status = '✅' if code == 200 and isinstance(size, int) and size > 10000 else '❌'
            print(f'  Port {port}: {status} HTTP {code} | {size if isinstance(size, int) else size}')
