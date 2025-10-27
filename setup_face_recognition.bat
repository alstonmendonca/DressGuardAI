@echo off
echo ========================================
echo DressGuard Face Recognition Setup
echo ========================================
echo.

echo Step 1: Testing Redis connection...
python test_redis.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Redis is not running!
    echo Please start Redis server first: redis-server
    echo.
    pause
    exit /b 1
)

echo.
echo Step 2: Checking database folder...
if not exist "database\" (
    echo Creating database folder...
    mkdir database
    echo Please add person folders with images to database\ folder
    echo Then run sync_faces.py
    pause
    exit /b 0
)

echo.
echo Step 3: Syncing faces to Redis...
echo Do you want to sync faces now? (Y/N)
set /p sync_choice=
if /i "%sync_choice%"=="Y" (
    python sync_faces.py
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Face sync failed!
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo   1. Backend: uvicorn main:app --reload
echo   2. Frontend: cd frontend && npm run dev
echo.
echo To enable logging:
echo   1. Open web interface
echo   2. Click "Start Logging" in Actions panel
echo   3. Violations will be saved to non_compliance_logs\
echo.
pause
