@echo off
echo ============================================
echo   DressGuard WhatsApp Service Setup
echo ============================================
echo.

cd whatsapp-service

echo [1/3] Installing Node.js dependencies...
call npm install

echo.
echo [2/3] Setup complete!
echo.
echo ============================================
echo   How to use:
echo ============================================
echo 1. Run: start-whatsapp.bat
echo 2. Scan QR code with your phone
echo 3. Start DressGuard backend
echo 4. Messages will send from your WhatsApp!
echo.
echo ============================================
pause
