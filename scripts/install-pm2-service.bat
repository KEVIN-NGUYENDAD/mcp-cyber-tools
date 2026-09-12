@echo off
REM Install PM2 as Windows Service for auto-start
REM MUST RUN AS ADMINISTRATOR

echo.
echo =========================================
echo PM2 Windows Service Installer
echo =========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo.
    echo Please:
    echo   1. Right-click on Command Prompt
    echo   2. Select "Run as Administrator"
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

REM Install PM2 as Windows Service
echo Installing PM2 as Windows Service...
pm2-windows-service install

if %errorLevel% equ 0 (
    echo.
    echo [SUCCESS] PM2 Windows Service installed!
    echo.
    echo Processes will auto-start on Windows boot:
    echo   - sentinelops-bot
    echo   - sentinelops-daily-brief
    echo.
    echo To verify the service:
    echo   1. Open Services (services.msc)
    echo   2. Look for "pm2-windows-service"
    echo   3. Should show status "Running"
    echo.
    echo To manage the service:
    echo   - Start:  net start "pm2-windows-service"
    echo   - Stop:   net stop "pm2-windows-service"
    echo   - Restart: net stop "pm2-windows-service" ^& net start "pm2-windows-service"
    echo.
    echo To uninstall (if needed):
    echo   pm2-windows-service uninstall
    echo.
) else (
    echo.
    echo [ERROR] Failed to install PM2 Windows Service
    echo Please check the output above for details.
    echo.
)

pause
