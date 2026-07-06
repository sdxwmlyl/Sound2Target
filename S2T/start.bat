@echo off
cd /d "%~dp0"

echo ========================================
echo   S2T Starting...
echo ========================================

REM --- Backend ---
echo [1/2] Stopping old backend...
taskkill /fi "WINDOWTITLE eq S2T Backend*" /f 2>nul
timeout /t 1 /nobreak >nul

echo [1/2] Starting backend on :8000...
cd /d "%~dp0backend"
start "S2T Backend" cmd /k "title S2T Backend && python -m uvicorn main:app --host localhost --port 8000"

REM --- Frontend ---
echo [2/2] Stopping old frontend...
taskkill /fi "WINDOWTITLE eq S2T Frontend*" /f 2>nul
timeout /t 2 /nobreak >nul

echo [2/2] Starting frontend on :3000...
cd /d "%~dp0frontend"
call npm run dev

echo.
echo Backend : http://localhost:8000
echo Frontend: http://localhost:3000
pause
