@echo off
chcp 65001 >nul
title S2T

echo ========================================
echo   S2T - Backend + Frontend
echo ========================================
echo.

echo [1/2] Starting Backend (background)...
cd /d d:\projectsound2target\S2T\backend
start "" /MIN D:\QwenPaw\python.exe -m uvicorn main:app --host localhost --port 8000

echo Waiting for backend...
:wait
ping -n 2 127.0.0.1 >nul
netstat -ano | findstr "127.0.0.1:8000" >nul
if %errorlevel% neq 0 goto wait
echo Backend ready.

echo [2/2] Starting Frontend...
cd /d d:\projectsound2target\S2T\frontend
call npm run dev

pause
