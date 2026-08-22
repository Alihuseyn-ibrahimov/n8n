@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  === TapAI ===
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
python -m pip install --upgrade pip
echo Paketler qurulur (birinci defe bir az ceke biler)...
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_fail

echo.
echo  Brauzerde ac:  http://127.0.0.1:8088
echo  Dayandirmaq ucun bu pencerede Ctrl+C
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8088 --reload
echo.
pause
exit /b 0

:no_python
echo  [XETA] Python tapilmadi — ona gore de pip islemir.
echo.
echo  Bunu et:
echo   1. https://www.python.org/downloads/  (Python 3.12)
echo   2. Installer-de MUTLEQ isarele:  Add python.exe to PATH
echo   3. Bu PowerShell penceresini bagla, yenisini ac
echo   4. start.bat-i yeniden ise sal
echo.
echo  Ve ya PowerShell-de:
echo     winget install -e --id Python.Python.3.12
echo.
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
