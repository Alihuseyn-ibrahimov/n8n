@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  === Melumatci / AI uchun melumat cixarma ===
echo  Qovluq: %CD%
echo.

set "PY_CMD="
where py >nul 2>&1 && py -3 --version >nul 2>&1 && set "PY_CMD=py -3"
if not defined PY_CMD where python >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD where python3 >nul 2>&1 && set "PY_CMD=python3"

if not defined PY_CMD goto :no_python

if not exist ".venv\Scripts\python.exe" (
  echo Virtual muhit yaradilir...
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto :venv_fail
)

call ".venv\Scripts\activate.bat"
python -m pip install -q -r requirements.txt
if errorlevel 1 goto :pip_fail

echo.
echo  Brauzer:   http://127.0.0.1:8090
echo  CLI:       python turbo_scraping.py fixtures\turbo_sehife.html
echo  Dayandirmaq uchun Ctrl+C
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
echo.
pause
exit /b 0

:no_python
echo  [XETA] Python tapilmadi.
echo  https://www.python.org/downloads/  — Installer-de "Add python.exe to PATH"
pause
exit /b 1

:venv_fail
echo  [XETA] Virtual muhit yaradilmadi.
pause
exit /b 1

:pip_fail
echo  [XETA] Paketler qurulmadi.
pause
exit /b 1
