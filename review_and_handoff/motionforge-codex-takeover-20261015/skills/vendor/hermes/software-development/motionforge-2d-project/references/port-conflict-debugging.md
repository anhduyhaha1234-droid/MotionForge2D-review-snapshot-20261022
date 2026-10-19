# Port Conflict & Zombie Process Debugging

## The Problem

Port 8000 on this Windows machine is permanently occupied by a zombie uvicorn process from another project ("Goha MMO Clone" v6.0). The zombie:
- Shows in `netstat -ano | grep ":8000.*LISTENING"` with PID 17048
- `wmic process where "PID=17048"` returns "No Instance(s Available"
- `cmd.exe /C "taskkill /PID 17048 /F"` says "process not found"
- `cmd.exe /C "taskkill /PID 17048 /F /T"` also fails
- `wmic process where "PID=17048" delete` says "No Instance(s) Available"
- The port remains LISTENING indefinitely

This caused a **405 Method Not Allowed** error when the frontend tried to call `POST /api/projects` — the request hit the wrong FastAPI app ("Goha MMO Clone") which didn't have the MotionForge routes.

## Symptom

User clicks "Bắt đầu" (Start) in the UI → frontend sends `POST /api/projects` → gets `405 {"detail":"Method Not Allowed"}`.

The error message is misleading — it's not a method mismatch, it's a completely different app responding.

## Diagnosis Steps

```bash
# 1. Check who's on port 8000
netstat -ano | grep ":8000.*LISTENING"

# 2. Identify the process
wmic process where "PID=17048" get Name,CommandLine

# 3. If it shows a different app (e.g., "Goha MMO Clone"), it's NOT your backend

# 4. Verify your app works directly
curl -s http://localhost:8000/openapi.json | python -c "import json,sys; print(json.load(sys.stdin).get('info',{}))"
# Expected: {'title': 'MotionForge 2D API', 'version': '0.2.0'}
# Actual: {'title': 'Goha MMO Clone', 'version': '6.0'}
```

## Solution

Use port 8002 instead:

```bash
# 1. Create/update frontend/.env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8002" > frontend/.env.local

# 2. Start backend on port 8002
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# 3. Restart frontend dev server (to pick up .env.local change)
cd frontend && npm run dev

# 4. Verify
curl -s http://localhost:8002/health
# Expected: {"status":"ok","service":"motionforge-2d"}
```

## Prevention

- Always check `curl -s http://localhost:PORT/openapi.json | python -c "import json,sys; print(json.load(sys.stdin).get('info',{}))"` to verify the correct app is responding
- Document the port in SETUP_PORT.md at project root
- `.env.local` is gitignored — must be created after clone
