@echo off
setlocal

set "ROOT=%~dp0"
set "PY=%ROOT%_tools\python313\python.exe"
set "PORT=8788"

if not exist "%PY%" (
  echo [ERR] Python runtime not found:
  echo %PY%
  pause
  exit /b 1
)

cd /d "%ROOT%"
set "LEAKAGE_WEB_PORT=%PORT%"

echo [INFO] Starting TV leakage simulator DEV web UI
echo [INFO] URL: http://127.0.0.1:%PORT%
echo [INFO] Auto-restart: ON
echo [INFO] Auto-refresh: ON
echo [INFO] Keep this window open while developing
echo.

"%PY%" run_web_dev.py

endlocal
