@echo off
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%_tools\python313\python.exe"
if not exist "%PY%" (
  echo [ERR] Python runtime not found: %PY%
  exit /b 1
)
"%PY%" run.py %*
