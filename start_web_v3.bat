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

echo [INFO] Starting TV leakage simulator web UI
echo [INFO] Expected URL: http://127.0.0.1:%PORT%
echo [INFO] Health check: http://127.0.0.1:%PORT%/health
echo [INFO] Keep this window open while using the web UI
echo.

"%PY%" run_web.py

endlocal
