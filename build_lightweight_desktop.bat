@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_lightweight_desktop.ps1"
if errorlevel 1 (
  echo.
  echo [ERROR] Lightweight package build failed.
  exit /b 1
)
echo.
echo [OK] Lightweight desktop package is ready under the release folder.
endlocal
