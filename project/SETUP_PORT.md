# MotionForge 2D — Environment Setup

## Backend Port

The backend should run on port **8002** to avoid conflicts with other services.

```bash
cd C:\Users\Admin\MotionForge2D
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

## Frontend

Update `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8002
```

## Why port 8002?

Port 8000 is occupied by another service ("Goha MMO Clone") that cannot be killed (zombie process).
