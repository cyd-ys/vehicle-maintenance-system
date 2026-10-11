@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo  Vehicle Maintenance Reservation - Frontend
echo ============================================
if not exist "node_modules" (
  echo [1/2] First run: installing npm dependencies...
  call npm install
)
echo [2/2] Starting Vite dev server on http://localhost:5173
call npm run dev
pause
