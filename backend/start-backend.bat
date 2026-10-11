@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo  Vehicle Maintenance Reservation - Backend
echo ============================================
if not exist ".venv\Scripts\python.exe" (
  echo [1/2] First run: creating venv and installing deps...
  python -m venv .venv
  call .venv\Scripts\python.exe -m pip install -r requirements.txt
)
echo [2/2] Starting FastAPI on http://127.0.0.1:8000  (docs: /docs)
call .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
