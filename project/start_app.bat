@echo off
chcp 65001 >nul
title MotionForge 2D - Application Launcher
echo ========================================================
echo   MotionForge 2D - Starting Backend & Frontend...
echo ========================================================
echo.

cd /d "c:\Users\Admin\MotionForge2D"
echo [1/3] Starting FastAPI Backend (Port 8888 with --reload)...
start "MotionForge_Backend" /min cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload"

cd /d "c:\Users\Admin\MotionForge2D\frontend"
echo [2/3] Starting Next.js Frontend (Port 3000)...
start "MotionForge_Frontend" /min cmd /c "npm run dev"

echo [3/3] Opening Web UI in Browser...
ping -n 4 127.0.0.1 >nul
start http://localhost:3000

echo.
echo ========================================================
echo   SUCCESS! MotionForge 2D is now running.
echo   - Web UI:  http://localhost:3000
echo   - Backend: http://localhost:8888
echo ========================================================
echo.
