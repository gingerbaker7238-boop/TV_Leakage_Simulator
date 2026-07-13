@echo off
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%_tools\python313\python.exe"

if not exist "%PY%" (
  echo [ERR] embedded python not found: %PY%
  exit /b 1
)

echo [1/3] install/verify pyinstaller ...
"%PY%" -m pip install pyinstaller --user
if errorlevel 1 (
  echo [ERR] pip install failed
  exit /b 1
)

echo [2/3] build leak GUI exe ...
"%PY%" -m PyInstaller --noconfirm --onefile --windowed --name leakage-leakage-simulator-ui "%ROOT%run_gui.py"
if errorlevel 1 (
  echo [ERR] pyinstaller build failed
  exit /b 1
)

if exist "%ROOT%dist\leakage-leakage-simulator-ui.exe" (
  echo [OK] created: %ROOT%dist\leakage-leakage-simulator-ui.exe
) else (
  echo [WARN] output not found. check build log.
)

echo [3/3] done.
