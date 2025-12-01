@echo off
echo ============================================
echo   Starting DressGuard System
echo ============================================
echo.
echo This will start:
echo   1. Backend API (FastAPI/uvicorn)
echo   2. WhatsApp Web Service (automatically)
echo.
echo WhatsApp QR code will appear in a separate window
echo Please scan it with your phone to connect
echo.
echo ============================================
echo.

cd /d "%~dp0"

echo Starting DressGuard backend...
uvicorn main:app --reload

pause
