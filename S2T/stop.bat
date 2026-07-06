@echo off
chcp 65001 >nul
echo ========================================
echo    S2T 停止脚本
echo ========================================
echo.

echo 正停止后端服务...
taskkill /FI "WINDOWTITLE eq S2T Backend*" /F >nul 2>&1

echo 正停止前端服务...
taskkill /FI "WINDOWTITLE eq S2T Frontend*" /F >nul 2>&1

echo.
echo 所有服务已停止。
echo.
pause