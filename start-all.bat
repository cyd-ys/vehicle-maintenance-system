@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo  Vehicle Maintenance Reservation System
echo  Start backend (8000) + frontend (5173)
echo ============================================
echo.

start "backend-8000" cmd /k "cd /d %~dp0backend && start-backend.bat"
echo [1/2] Backend window opened, waiting 5s for it to come up...
ping -n 6 127.0.0.1 >nul

start "frontend-5173" cmd /k "cd /d %~dp0frontend && start-frontend.bat"
echo [2/2] Frontend window opened.
echo.
echo   Backend : http://127.0.0.1:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo Close those two windows to stop the services.
pause
