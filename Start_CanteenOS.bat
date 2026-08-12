@echo off
title CanteenOS Boot Sequence
echo ===================================================
echo    Starting CanteenOS ERP System...
echo ===================================================

:: Automatically navigate to the CanteenOS folder
cd /d "%~dp0"

:: Start the Python Backend in the background
echo [1/2] Booting Python FastAPI Backend & SQLite Database...
start "CanteenOS Backend" cmd /c "py -m uvicorn api:app --reload --port 8000"

:: Wait 3 seconds to let the database wake up
timeout /t 3 /nobreak > NUL

:: Start the React Frontend
echo [2/2] Booting React Dashboard...
start "CanteenOS Frontend" cmd /c "npm run dev"

echo.
echo System is live! Check your browser.
pause