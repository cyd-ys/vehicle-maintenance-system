@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo  Init database (create tables + demo data)
echo ============================================
call .venv\Scripts\python.exe -m app.seed --reset
echo.
echo Done. Database: vehicle_maintenance
pause
