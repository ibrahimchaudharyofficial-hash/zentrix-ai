@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Creating Zentrix AI environment...
  py -3 -m venv .venv
  if errorlevel 1 goto error
  echo Installing required packages for the first launch...
  "%PY%" -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 goto error
) else (
  echo Using existing Zentrix AI environment...
)
echo.
echo Starting Zentrix AI at http://127.0.0.1:8000
start "Zentrix AI" http://127.0.0.1:8000
"%PY%" -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
pause
exit /b 0
:error
echo Setup failed. Install Python 3.10+ and check your internet connection.
pause
exit /b 1
