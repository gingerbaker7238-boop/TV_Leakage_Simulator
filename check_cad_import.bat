@echo off
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%_tools\python313\python.exe"

if not exist "%PY%" (
  echo [ERR] Embedded python not found: %PY%
  pause
  exit /b 1
)

set "PATH=%ROOT%_tools\python313;%ROOT%_tools\python313\Scripts;%PATH%"
cd /d "%ROOT%"

echo [INFO] Direct CAD import checker
echo [INFO] This runs without the web server.
echo.

"%PY%" check_cad_import.py %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if %EXITCODE% equ 0 (
  echo [OK] Real CAD import succeeded.
) else if %EXITCODE% equ 3 (
  echo [WARN] Synthetic fallback was used. Check import_note above.
) else (
  echo [ERR] Import check failed. Exit code: %EXITCODE%
)
pause
exit /b %EXITCODE%
