@echo off
echo ============================================
echo   Starting WhatsApp Web Service
echo ============================================
echo.
echo Your WhatsApp will be connected via WhatsApp Web
echo Messages will be sent from YOUR phone number
echo.
echo Starting service...
echo.

cd whatsapp-service
node server.js
