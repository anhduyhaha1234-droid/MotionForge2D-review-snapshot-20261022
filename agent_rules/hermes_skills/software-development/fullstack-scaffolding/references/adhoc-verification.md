# Ad-Hoc Verification Script Pattern

When a project has no test suite, write a single self-contained Python script that verifies everything end-to-end. Clean it up after it passes.

## Template

```python
#!/usr/bin/env python3
"""Ad-hoc verification for <project>."""
import json, os, sys, subprocess, time, urllib.request

ROOT = r"<project-root>"  # Windows-native path
P = F = 0

def ok(name, condition):
    global P, F
    if condition: P += 1; print(f"  PASS  {name}")
    else: F += 1; print(f"  FAIL  {name}")

# 1. File existence
for rel in ["backend/app/main.py", "frontend/index.html", ...]:
    ok(f"exists: {rel}", os.path.isfile(os.path.join(ROOT, rel)))

# 2. Data defaults
with open(os.path.join(ROOT, "backend/data/settings.json")) as f:
    s = json.load(f)
ok("defaults correct", s == {"key": "expected_value", ...})

# 3. Start backend server
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
    cwd=os.path.join(ROOT, "backend"),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
time.sleep(3)

try:
    def get(path):
        r = urllib.request.urlopen(f"http://127.0.0.1:8001{path}", timeout=5)
        return json.loads(r.read()), r.status

    def post(path, body):
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:8001{path}", data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        r = urllib.request.urlopen(req, timeout=5)
        return json.loads(r.read()), r.status

    # 4. Test each endpoint
    d, code = get("/api/v1/health")
    ok("health: status ok", d.get("status") == "ok")
    ok("health: 200", code == 200)

    d, code = post("/api/v1/settings", {"language": "en"})
    ok("post settings: merge", d.get("language") == "en")

    # SSE: open, check headers, close immediately
    r = urllib.request.urlopen("http://127.0.0.1:8001/api/v1/logs/stream", timeout=3)
    ok("sse: 200", r.status == 200)
    ok("sse: content-type", "text/event-stream" in r.headers.get("Content-Type", ""))
    r.close()

except Exception as e:
    F += 1; print(f"  FAIL  {e}")
finally:
    proc.terminate(); proc.wait(timeout=5)

# 5. Frontend content (string matching, never execute JS)
with open(os.path.join(ROOT, "frontend/index.html")) as f: html = f.read()
ok("html: has viewport", "viewport" in html)

with open(os.path.join(ROOT, "frontend/styles.css")) as f: css = f.read()
ok("css: glassmorphism", "backdrop-filter" in css)

with open(os.path.join(ROOT, "frontend/app.js")) as f: js = f.read()
ok("js: EventSource", "EventSource" in js)

# 6. Restore mutated state
with open(os.path.join(ROOT, "backend/data/settings.json"), "w") as f:
    json.dump({"original": "defaults"}, f, indent=2)

print(f"\nResults: {P} passed, {F} failed")
sys.exit(0 if F == 0 else 1)
```

## Key decisions

| Choice | Reason |
|--------|--------|
| `urllib.request` | Stdlib — no `requests`/`httpx` dependency |
| `subprocess.Popen` | Can start server, test, then `terminate()` in `finally` |
| Non-default port (8001) | Avoids colliding with running dev server |
| `time.sleep(3)` after start | Gives uvicorn time to bind — simple but reliable |
| String matching for frontend | Never execute/parse JS — just verify key strings exist |
| Restore settings at end | POST tests mutate state — leave it clean |

## Alternative: Background server via terminal tool

Instead of `subprocess.Popen` inside the script, start the server externally:

```
terminal: cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
           (background=true, watch_patterns=["Application startup complete"])

# Wait for watch notification, then:
terminal: python $(cygpath -w /path/to/verify.py)

# Clean up:
process: kill
```

This avoids orphan processes and gives better output capture. Use `watch_patterns` (not `notify_on_complete`) for long-lived servers that never exit.

## Pitfalls

- **HTML attr vs JS accessor.** Check `dataset.tab` not `data-tab` in JS files.
- **MSYS paths.** Use `cygpath -w` to convert POSIX paths before passing to Python/Node. `python /c/Users/...` fails silently (resolves to `C:\c\Users\...`).
- **`__pycache__` stale bytecode.** After restoring a `.py` file, clear `<pkg>/__pycache__/` or Python imports the old version.
- **SSE timeout.** SSE endpoints hold connections open. Set short timeout (3s), check status+headers, close.
- **Cleanup.** Delete the script after it passes — it's ad-hoc, not permanent.
